"""
Admin IP block management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from app.db.session import get_db
from app.api.routes.admin.dependencies import get_current_admin
from app.models.admin import Admin
from app.models.ip_block import BlockReason
from app.services.ip_block_service import IPBlockService
from loguru import logger

router = APIRouter(prefix="/admin/ip-blocks", tags=["Admin IP Blocks"])


# Request/Response schemas
class IPBlockCreate(BaseModel):
    ip_address: str
    reason: str  # rate_limit_abuse, brute_force, suspicious_activity, security_threat, manual_block, spam
    description: Optional[str] = None
    tenant_id: Optional[UUID] = None
    duration_hours: Optional[int] = 24
    is_permanent: bool = False


class IPBlockResponse(BaseModel):
    id: int
    ip_address: str
    ip_range: Optional[str]
    reason: str
    description: Optional[str]
    tenant_id: Optional[UUID]
    is_permanent: bool
    blocked_at: datetime
    expires_at: Optional[datetime]
    violation_count: int
    last_violation_at: Optional[datetime]
    blocked_by: Optional[UUID]
    is_active: bool
    unblocked_at: Optional[datetime]
    unblocked_by: Optional[UUID]
    unblock_reason: Optional[str]
    user_agent: Optional[str]

    class Config:
        from_attributes = True


class IPBlockStats(BaseModel):
    active_blocks: int
    by_reason: dict
    blocked_last_24h: int


class UnblockRequest(BaseModel):
    reason: Optional[str] = None


@router.get("", response_model=List[IPBlockResponse])
async def get_blocked_ips(
    tenant_id: Optional[UUID] = Query(None),
    reason: Optional[str] = Query(None),
    active_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Get list of blocked IPs
    
    **Query Parameters:**
    - tenant_id: Filter by tenant
    - reason: Filter by block reason
    - active_only: Only show active blocks (default: true)
    - skip: Pagination offset
    - limit: Maximum results
    
    **Returns:**
    - List of IP blocks
    """
    ip_block_service = IPBlockService(db)
    
    blocks = await ip_block_service.get_blocked_ips(
        tenant_id=tenant_id,
        reason=BlockReason(reason) if reason else None,
        active_only=active_only,
        skip=skip,
        limit=limit
    )
    
    return blocks


@router.get("/stats", response_model=IPBlockStats)
async def get_block_statistics(
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Get IP block statistics
    
    **Returns:**
    - Statistics about blocked IPs
    """
    ip_block_service = IPBlockService(db)
    stats = await ip_block_service.get_block_statistics()
    return IPBlockStats(**stats)


@router.get("/check/{ip_address}")
async def check_ip_status(
    ip_address: str,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Check if an IP is blocked
    
    **Path Parameters:**
    - ip_address: IP to check
    
    **Returns:**
    - Block status and details
    """
    ip_block_service = IPBlockService(db)
    
    is_blocked = await ip_block_service.is_ip_blocked(ip_address)
    block_info = await ip_block_service.get_block_info(ip_address) if is_blocked else None
    
    return {
        "ip_address": ip_address,
        "is_blocked": is_blocked,
        "block_info": IPBlockResponse.from_orm(block_info) if block_info else None
    }


@router.post("", response_model=IPBlockResponse, status_code=status.HTTP_201_CREATED)
async def block_ip(
    block_data: IPBlockCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Block an IP address
    
    **Request Body:**
    - ip_address: IP to block
    - reason: Block reason
    - description: Optional description
    - tenant_id: Associated tenant
    - duration_hours: Block duration (default 24)
    - is_permanent: Whether block is permanent
    
    **Returns:**
    - Created IP block
    """
    ip_block_service = IPBlockService(db)
    
    try:
        reason = BlockReason(block_data.reason)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid reason. Valid values: {[r.value for r in BlockReason]}"
        )
    
    block = await ip_block_service.block_ip(
        ip_address=block_data.ip_address,
        reason=reason,
        description=block_data.description,
        tenant_id=block_data.tenant_id,
        blocked_by=current_admin.id,
        duration_hours=block_data.duration_hours,
        is_permanent=block_data.is_permanent
    )
    
    logger.info(f"Admin {current_admin.email} blocked IP {block_data.ip_address}: {reason.value}")
    
    return block


@router.post("/{ip_address}/unblock")
async def unblock_ip(
    ip_address: str,
    unblock_data: UnblockRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Unblock an IP address
    
    **Path Parameters:**
    - ip_address: IP to unblock
    
    **Request Body:**
    - reason: Optional reason for unblocking
    
    **Returns:**
    - Success message
    """
    ip_block_service = IPBlockService(db)
    
    block = await ip_block_service.unblock_ip(
        ip_address=ip_address,
        unblocked_by=current_admin.id,
        reason=unblock_data.reason
    )
    
    if not block:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active block found for this IP"
        )
    
    logger.info(f"Admin {current_admin.email} unblocked IP {ip_address}")
    
    return {"message": f"IP {ip_address} unblocked successfully"}


@router.delete("/{block_id}")
async def delete_block(
    block_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Delete a block record (admin only)
    
    **Path Parameters:**
    - block_id: Block ID to delete
    
    **Returns:**
    - Success message
    """
    from sqlalchemy import select, delete
    from app.models.ip_block import IPBlock
    
    # Check if block exists
    query = select(IPBlock).where(IPBlock.id == block_id)
    result = await db.execute(query)
    block = result.scalar_one_or_none()
    
    if not block:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Block not found"
        )
    
    # Delete block
    await db.delete(block)
    await db.commit()
    
    # Clear cache
    ip_block_service = IPBlockService(db)
    redis_client = await ip_block_service.get_redis_client()
    await redis_client.delete(f"blocked_ip:{block.ip_address}")
    
    logger.info(f"Admin {current_admin.email} deleted block {block_id} for IP {block.ip_address}")
    
    return {"message": "Block deleted successfully"}


@router.post("/cleanup-expired")
async def cleanup_expired_blocks(
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Clean up expired temporary blocks
    
    **Returns:**
    - Count of cleaned up blocks
    """
    ip_block_service = IPBlockService(db)
    count = await ip_block_service.cleanup_expired_blocks()
    
    return {"message": f"Cleaned up {count} expired blocks", "count": count}

