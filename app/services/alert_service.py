"""
Alert service for creating and managing system alerts
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import redis.asyncio as redis

from app.models.alert import Alert, AlertType, AlertSeverity, AlertStatus
from app.models.tenant import Tenant
from app.core.config import settings
from loguru import logger


class AlertService:
    """Service for managing system alerts"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.redis_client = None

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
    # Alert Creation
    # ========================================================================

    async def create_alert(
        self,
        alert_type: AlertType,
        title: str,
        message: str,
        tenant_id: Optional[UUID] = None,
        severity: AlertSeverity = AlertSeverity.WARNING,
        details: Optional[Dict[str, Any]] = None,
        threshold_value: Optional[int] = None,
        current_value: Optional[int] = None,
        auto_resolve: bool = False,
        expires_in_hours: Optional[int] = None
    ) -> Alert:
        """
        Create a new alert
        
        Args:
            alert_type: Type of alert
            title: Alert title
            message: Alert message
            tenant_id: Associated tenant (optional)
            severity: Alert severity level
            details: Additional context data
            threshold_value: The limit/threshold that was reached
            current_value: The actual value
            auto_resolve: Whether to auto-resolve the alert
            expires_in_hours: Hours until alert expires
            
        Returns:
            Created alert
        """
        # Check for duplicate active alerts
        existing = await self._check_duplicate_alert(alert_type, tenant_id)
        if existing:
            # Update existing alert instead
            existing.current_value = current_value
            existing.details = details
            existing.message = message
            await self.session.commit()
            return existing

        alert = Alert(
            alert_type=alert_type,
            title=title,
            message=message,
            tenant_id=tenant_id,
            severity=severity,
            details=details,
            threshold_value=threshold_value,
            current_value=current_value,
            auto_resolve=auto_resolve,
            expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours) if expires_in_hours else None
        )

        self.session.add(alert)
        await self.session.commit()
        await self.session.refresh(alert)

        logger.warning(f"Alert created: {alert_type.value} - {title} (Tenant: {tenant_id})")

        return alert

    async def _check_duplicate_alert(
        self, 
        alert_type: AlertType, 
        tenant_id: Optional[UUID]
    ) -> Optional[Alert]:
        """Check for existing active alert of same type"""
        query = select(Alert).where(
            and_(
                Alert.alert_type == alert_type,
                Alert.status == AlertStatus.ACTIVE,
                Alert.tenant_id == tenant_id if tenant_id else Alert.tenant_id.is_(None)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    # ========================================================================
    # Rate Limit Alerts
    # ========================================================================

    async def check_rate_limit_and_alert(
        self,
        tenant_id: UUID,
        tenant_name: str,
        current_count: int,
        limit: int,
        limit_type: str = "hourly"  # hourly or daily
    ) -> Optional[Alert]:
        """
        Check rate limit usage and create alerts if needed
        
        Args:
            tenant_id: Tenant UUID
            tenant_name: Tenant name for message
            current_count: Current request count
            limit: Maximum allowed requests
            limit_type: Type of limit (hourly/daily)
            
        Returns:
            Created alert if threshold exceeded, None otherwise
        """
        percentage = (current_count / limit) * 100 if limit > 0 else 0

        # 80% warning threshold
        if 80 <= percentage < 100:
            return await self.create_alert(
                alert_type=AlertType.RATE_LIMIT_WARNING,
                title=f"Rate Limit Warning - {tenant_name}",
                message=f"Tenant '{tenant_name}' has used {percentage:.1f}% of their {limit_type} rate limit ({current_count:,}/{limit:,} requests)",
                tenant_id=tenant_id,
                severity=AlertSeverity.WARNING,
                details={
                    "limit_type": limit_type,
                    "percentage": round(percentage, 1)
                },
                threshold_value=limit,
                current_value=current_count,
                auto_resolve=True,
                expires_in_hours=1 if limit_type == "hourly" else 24
            )

        # 100% exceeded
        elif percentage >= 100:
            return await self.create_alert(
                alert_type=AlertType.RATE_LIMIT_EXCEEDED,
                title=f"Rate Limit Exceeded - {tenant_name}",
                message=f"Tenant '{tenant_name}' has exceeded their {limit_type} rate limit ({current_count:,}/{limit:,} requests)",
                tenant_id=tenant_id,
                severity=AlertSeverity.ERROR,
                details={
                    "limit_type": limit_type,
                    "percentage": round(percentage, 1)
                },
                threshold_value=limit,
                current_value=current_count,
                expires_in_hours=1 if limit_type == "hourly" else 24
            )

        return None

    # ========================================================================
    # Error Rate Alerts
    # ========================================================================

    async def check_error_rate_and_alert(
        self,
        tenant_id: UUID,
        tenant_name: str,
        error_count: int,
        total_requests: int,
        threshold_percent: float = 10.0
    ) -> Optional[Alert]:
        """
        Check error rate and create alert if too high
        
        Args:
            tenant_id: Tenant UUID
            tenant_name: Tenant name
            error_count: Number of errors
            total_requests: Total requests
            threshold_percent: Error rate threshold (default 10%)
            
        Returns:
            Created alert if threshold exceeded
        """
        if total_requests == 0:
            return None

        error_rate = (error_count / total_requests) * 100

        if error_rate >= threshold_percent:
            severity = AlertSeverity.ERROR if error_rate >= 20 else AlertSeverity.WARNING
            
            return await self.create_alert(
                alert_type=AlertType.HIGH_ERROR_RATE,
                title=f"High Error Rate - {tenant_name}",
                message=f"Tenant '{tenant_name}' has an error rate of {error_rate:.1f}% ({error_count:,} errors in {total_requests:,} requests)",
                tenant_id=tenant_id,
                severity=severity,
                details={
                    "error_rate": round(error_rate, 1),
                    "threshold": threshold_percent
                },
                threshold_value=int(threshold_percent),
                current_value=int(error_rate),
                expires_in_hours=1
            )

        return None

    # ========================================================================
    # Response Time Alerts
    # ========================================================================

    async def check_response_time_and_alert(
        self,
        tenant_id: UUID,
        tenant_name: str,
        avg_response_time_ms: float,
        threshold_ms: int = 2000
    ) -> Optional[Alert]:
        """
        Check response time and create alert if too slow
        
        Args:
            tenant_id: Tenant UUID
            tenant_name: Tenant name
            avg_response_time_ms: Average response time in ms
            threshold_ms: Threshold in milliseconds
            
        Returns:
            Created alert if threshold exceeded
        """
        if avg_response_time_ms >= threshold_ms:
            severity = AlertSeverity.ERROR if avg_response_time_ms >= 5000 else AlertSeverity.WARNING
            
            return await self.create_alert(
                alert_type=AlertType.SLOW_RESPONSE,
                title=f"Slow Response Time - {tenant_name}",
                message=f"Tenant '{tenant_name}' has an average response time of {avg_response_time_ms:.0f}ms (threshold: {threshold_ms}ms)",
                tenant_id=tenant_id,
                severity=severity,
                details={
                    "avg_response_time_ms": round(avg_response_time_ms),
                    "threshold_ms": threshold_ms
                },
                threshold_value=threshold_ms,
                current_value=int(avg_response_time_ms),
                auto_resolve=True,
                expires_in_hours=1
            )

        return None

    # ========================================================================
    # Alert Management
    # ========================================================================

    async def get_alerts(
        self,
        tenant_id: Optional[UUID] = None,
        status: Optional[AlertStatus] = None,
        severity: Optional[AlertSeverity] = None,
        alert_type: Optional[AlertType] = None,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False
    ) -> List[Alert]:
        """Get alerts with filters"""
        query = select(Alert)
        
        conditions = []
        
        if tenant_id:
            conditions.append(Alert.tenant_id == tenant_id)
        if status:
            conditions.append(Alert.status == status)
        if severity:
            conditions.append(Alert.severity == severity)
        if alert_type:
            conditions.append(Alert.alert_type == alert_type)
        if active_only:
            conditions.append(Alert.status == AlertStatus.ACTIVE)
            
        if conditions:
            query = query.where(and_(*conditions))
            
        query = query.order_by(Alert.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active_alerts_count(self) -> Dict[str, int]:
        """Get count of active alerts by severity"""
        query = select(
            Alert.severity,
            func.count(Alert.id).label('count')
        ).where(
            Alert.status == AlertStatus.ACTIVE
        ).group_by(Alert.severity)
        
        result = await self.session.execute(query)
        
        counts = {
            "critical": 0,
            "error": 0,
            "warning": 0,
            "info": 0,
            "total": 0
        }
        
        for row in result.all():
            counts[row.severity.value] = row.count
            counts["total"] += row.count
            
        return counts

    async def acknowledge_alert(
        self,
        alert_id: int,
        admin_id: UUID
    ) -> Optional[Alert]:
        """Acknowledge an alert"""
        query = select(Alert).where(Alert.id == alert_id)
        result = await self.session.execute(query)
        alert = result.scalar_one_or_none()
        
        if not alert:
            return None
            
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = admin_id
        
        await self.session.commit()
        await self.session.refresh(alert)
        
        return alert

    async def resolve_alert(
        self,
        alert_id: int,
        admin_id: UUID
    ) -> Optional[Alert]:
        """Resolve an alert"""
        query = select(Alert).where(Alert.id == alert_id)
        result = await self.session.execute(query)
        alert = result.scalar_one_or_none()
        
        if not alert:
            return None
            
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = admin_id
        
        await self.session.commit()
        await self.session.refresh(alert)
        
        return alert

    async def dismiss_alert(
        self,
        alert_id: int,
        admin_id: UUID
    ) -> Optional[Alert]:
        """Dismiss an alert"""
        query = select(Alert).where(Alert.id == alert_id)
        result = await self.session.execute(query)
        alert = result.scalar_one_or_none()
        
        if not alert:
            return None
            
        alert.status = AlertStatus.DISMISSED
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = admin_id
        
        await self.session.commit()
        await self.session.refresh(alert)
        
        return alert

    async def bulk_dismiss_alerts(
        self,
        alert_ids: List[int],
        admin_id: UUID
    ) -> int:
        """Bulk dismiss alerts"""
        stmt = update(Alert).where(
            Alert.id.in_(alert_ids)
        ).values(
            status=AlertStatus.DISMISSED,
            resolved_at=datetime.utcnow(),
            resolved_by=admin_id
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount

    async def cleanup_expired_alerts(self) -> int:
        """Clean up expired auto-resolve alerts"""
        now = datetime.utcnow()
        
        stmt = update(Alert).where(
            and_(
                Alert.auto_resolve == True,
                Alert.expires_at <= now,
                Alert.status == AlertStatus.ACTIVE
            )
        ).values(
            status=AlertStatus.RESOLVED,
            resolved_at=now
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount

