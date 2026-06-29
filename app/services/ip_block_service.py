"""
IP Block service for managing blocked IPs
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import redis.asyncio as redis

from app.models.ip_block import IPBlock, BlockReason
from app.models.alert import AlertType, AlertSeverity
from app.services.alert_service import AlertService
from app.core.config import settings
from loguru import logger


class IPBlockService:
    """Service for managing IP blocks"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.redis_client = None
        self.alert_service = AlertService(session)
        
        # Thresholds for auto-blocking
        self.RATE_LIMIT_VIOLATIONS_THRESHOLD = 5  # Block after 5 rate limit violations
        self.FAILED_LOGIN_THRESHOLD = 10          # Block after 10 failed logins
        self.SUSPICIOUS_REQUESTS_THRESHOLD = 20   # Block after 20 suspicious requests

    async def get_redis_client(self):
        """Get or create Redis client"""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return self.redis_client

    # ========================================================================
    # IP Checking
    # ========================================================================

    async def is_ip_blocked(self, ip_address: str) -> bool:
        """
        Check if an IP address is blocked
        
        Args:
            ip_address: IP address to check
            
        Returns:
            True if IP is blocked
        """
        # First check Redis cache for fast lookup
        redis_client = await self.get_redis_client()
        cached = await redis_client.get(f"blocked_ip:{ip_address}")
        
        if cached:
            return cached == "1"

        # Check database
        query = select(IPBlock).where(
            and_(
                IPBlock.ip_address == ip_address,
                IPBlock.is_active == True,
                or_(
                    IPBlock.expires_at.is_(None),  # Permanent
                    IPBlock.expires_at > datetime.utcnow()  # Not expired
                )
            )
        )
        
        result = await self.session.execute(query)
        block = result.scalar_one_or_none()
        
        # Cache the result
        is_blocked = block is not None
        await redis_client.set(
            f"blocked_ip:{ip_address}",
            "1" if is_blocked else "0",
            ex=300  # Cache for 5 minutes
        )
        
        return is_blocked

    async def get_block_info(self, ip_address: str) -> Optional[IPBlock]:
        """Get block information for an IP"""
        query = select(IPBlock).where(
            and_(
                IPBlock.ip_address == ip_address,
                IPBlock.is_active == True
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    # ========================================================================
    # IP Blocking
    # ========================================================================

    async def block_ip(
        self,
        ip_address: str,
        reason: BlockReason,
        description: Optional[str] = None,
        tenant_id: Optional[UUID] = None,
        blocked_by: Optional[UUID] = None,
        duration_hours: Optional[int] = 24,
        is_permanent: bool = False,
        user_agent: Optional[str] = None,
        request_details: Optional[Dict[str, Any]] = None
    ) -> IPBlock:
        """
        Block an IP address
        
        Args:
            ip_address: IP to block
            reason: Reason for blocking
            description: Additional description
            tenant_id: Associated tenant
            blocked_by: Admin who blocked the IP
            duration_hours: Block duration in hours (default 24)
            is_permanent: Whether the block is permanent
            user_agent: User agent that triggered the block
            request_details: Details of the triggering request
            
        Returns:
            Created IP block
        """
        # Check if IP is already blocked
        existing = await self.get_block_info(ip_address)
        
        if existing:
            # Update existing block
            existing.violation_count += 1
            existing.last_violation_at = datetime.utcnow()
            existing.reason = reason
            existing.description = description
            
            # Extend block duration if violations continue
            if not existing.is_permanent and existing.violation_count >= 3:
                existing.is_permanent = True
                existing.expires_at = None
                logger.warning(f"IP {ip_address} permanently blocked due to repeated violations")
            elif not existing.is_permanent and duration_hours:
                existing.expires_at = datetime.utcnow() + timedelta(hours=duration_hours * existing.violation_count)
                
            await self.session.commit()
            await self.session.refresh(existing)
            
            # Invalidate cache
            redis_client = await self.get_redis_client()
            await redis_client.delete(f"blocked_ip:{ip_address}")
            
            return existing

        # Create new block
        block = IPBlock(
            ip_address=ip_address,
            reason=reason,
            description=description,
            tenant_id=tenant_id,
            blocked_by=blocked_by,
            is_permanent=is_permanent,
            expires_at=None if is_permanent else (datetime.utcnow() + timedelta(hours=duration_hours) if duration_hours else None),
            user_agent=user_agent,
            request_details=request_details,
            violation_count=1
        )

        self.session.add(block)
        await self.session.commit()
        await self.session.refresh(block)

        # Cache the block
        redis_client = await self.get_redis_client()
        await redis_client.set(
            f"blocked_ip:{ip_address}",
            "1",
            ex=duration_hours * 3600 if duration_hours and not is_permanent else None
        )

        logger.warning(f"IP {ip_address} blocked: {reason.value} - {description}")

        return block

    async def unblock_ip(
        self,
        ip_address: str,
        unblocked_by: UUID,
        reason: Optional[str] = None
    ) -> Optional[IPBlock]:
        """
        Unblock an IP address
        
        Args:
            ip_address: IP to unblock
            unblocked_by: Admin who unblocked
            reason: Reason for unblocking
            
        Returns:
            Updated IP block or None
        """
        block = await self.get_block_info(ip_address)
        
        if not block:
            return None
            
        block.is_active = False
        block.unblocked_at = datetime.utcnow()
        block.unblocked_by = unblocked_by
        block.unblock_reason = reason
        
        await self.session.commit()
        await self.session.refresh(block)

        # Invalidate cache
        redis_client = await self.get_redis_client()
        await redis_client.delete(f"blocked_ip:{ip_address}")

        logger.info(f"IP {ip_address} unblocked by admin")

        return block

    # ========================================================================
    # Violation Tracking
    # ========================================================================

    async def record_violation(
        self,
        ip_address: str,
        violation_type: str,
        tenant_id: Optional[UUID] = None,
        user_agent: Optional[str] = None,
        request_details: Optional[Dict[str, Any]] = None
    ) -> Optional[IPBlock]:
        """
        Record a violation for an IP and auto-block if threshold reached
        
        Args:
            ip_address: IP that violated
            violation_type: Type of violation (rate_limit, login_failed, suspicious)
            tenant_id: Associated tenant
            user_agent: User agent
            request_details: Request details
            
        Returns:
            IP block if threshold reached
        """
        redis_client = await self.get_redis_client()
        
        # Track violations in Redis
        key = f"ip_violations:{ip_address}:{violation_type}"
        count = await redis_client.incr(key)
        await redis_client.expire(key, 3600)  # 1 hour window
        
        # Determine threshold based on violation type
        thresholds = {
            "rate_limit": self.RATE_LIMIT_VIOLATIONS_THRESHOLD,
            "login_failed": self.FAILED_LOGIN_THRESHOLD,
            "suspicious": self.SUSPICIOUS_REQUESTS_THRESHOLD
        }
        
        threshold = thresholds.get(violation_type, 10)
        
        # Auto-block if threshold reached
        if count >= threshold:
            reason_map = {
                "rate_limit": BlockReason.RATE_LIMIT_ABUSE,
                "login_failed": BlockReason.BRUTE_FORCE,
                "suspicious": BlockReason.SUSPICIOUS_ACTIVITY
            }
            
            reason = reason_map.get(violation_type, BlockReason.SUSPICIOUS_ACTIVITY)
            
            # Create alert
            await self.alert_service.create_alert(
                alert_type=AlertType.SUSPICIOUS_IP,
                title=f"IP Auto-Blocked: {ip_address}",
                message=f"IP {ip_address} was automatically blocked after {count} {violation_type} violations",
                tenant_id=tenant_id,
                severity=AlertSeverity.WARNING,
                details={
                    "ip_address": ip_address,
                    "violation_type": violation_type,
                    "violation_count": count,
                    "user_agent": user_agent
                }
            )
            
            return await self.block_ip(
                ip_address=ip_address,
                reason=reason,
                description=f"Auto-blocked after {count} {violation_type} violations in 1 hour",
                tenant_id=tenant_id,
                duration_hours=24,
                user_agent=user_agent,
                request_details=request_details
            )
        
        return None

    # ========================================================================
    # Block Management
    # ========================================================================

    async def get_blocked_ips(
        self,
        tenant_id: Optional[UUID] = None,
        reason: Optional[BlockReason] = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[IPBlock]:
        """Get list of blocked IPs"""
        query = select(IPBlock)
        
        conditions = []
        
        if tenant_id:
            conditions.append(IPBlock.tenant_id == tenant_id)
        if reason:
            conditions.append(IPBlock.reason == reason)
        if active_only:
            conditions.append(IPBlock.is_active == True)
            
        if conditions:
            query = query.where(and_(*conditions))
            
        query = query.order_by(IPBlock.blocked_at.desc()).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_block_statistics(self) -> Dict[str, Any]:
        """Get block statistics"""
        # Total active blocks
        active_query = select(func.count(IPBlock.id)).where(IPBlock.is_active == True)
        active_result = await self.session.execute(active_query)
        active_count = active_result.scalar() or 0
        
        # Blocks by reason
        reason_query = select(
            IPBlock.reason,
            func.count(IPBlock.id).label('count')
        ).where(
            IPBlock.is_active == True
        ).group_by(IPBlock.reason)
        
        reason_result = await self.session.execute(reason_query)
        
        by_reason = {}
        for row in reason_result.all():
            by_reason[row.reason.value] = row.count
        
        # Blocks in last 24 hours
        yesterday = datetime.utcnow() - timedelta(hours=24)
        recent_query = select(func.count(IPBlock.id)).where(
            IPBlock.blocked_at >= yesterday
        )
        recent_result = await self.session.execute(recent_query)
        recent_count = recent_result.scalar() or 0
        
        return {
            "active_blocks": active_count,
            "by_reason": by_reason,
            "blocked_last_24h": recent_count
        }

    async def cleanup_expired_blocks(self) -> int:
        """Clean up expired temporary blocks"""
        now = datetime.utcnow()
        
        query = select(IPBlock).where(
            and_(
                IPBlock.is_active == True,
                IPBlock.is_permanent == False,
                IPBlock.expires_at <= now
            )
        )
        
        result = await self.session.execute(query)
        expired_blocks = result.scalars().all()
        
        redis_client = await self.get_redis_client()
        
        for block in expired_blocks:
            block.is_active = False
            await redis_client.delete(f"blocked_ip:{block.ip_address}")
        
        await self.session.commit()
        
        return len(expired_blocks)

