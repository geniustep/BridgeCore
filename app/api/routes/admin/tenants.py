"""
Admin tenant management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import redis.asyncio as redis
from pydantic import BaseModel

from app.db.session import get_db
from app.core.config import settings
from app.schemas.admin import (
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    TenantConnectionTest
)
from app.services.tenant_service import TenantService
from app.api.routes.admin.dependencies import get_current_admin
from app.models.admin import Admin
from app.models.tenant import TenantStatus
from loguru import logger

router = APIRouter(prefix="/admin/tenants", tags=["Admin Tenant Management"])


@router.get("", response_model=List[TenantResponse])
async def list_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = Query(None, regex="^(active|suspended|trial|deleted)$"),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    List all tenants with pagination

    **Query Parameters:**
    - skip: Number of records to skip (default: 0)
    - limit: Maximum records to return (default: 100, max: 500)
    - status: Filter by status (active, suspended, trial, deleted)

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - List of tenants
    """
    tenant_service = TenantService(db)

    tenant_status = TenantStatus(status) if status else None

    tenants = await tenant_service.list_tenants(
        skip=skip,
        limit=limit,
        status=tenant_status
    )

    return tenants


@router.get("/statistics")
async def get_tenant_statistics(
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Get tenant statistics

    Returns overall tenant statistics (counts by status).

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - total: Total number of tenants
    - active: Number of active tenants
    - suspended: Number of suspended tenants
    - trial: Number of trial tenants
    - deleted: Number of deleted tenants
    """
    tenant_service = TenantService(db)
    return await tenant_service.get_tenant_statistics()


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Get tenant details by ID

    **Path Parameters:**
    - tenant_id: Tenant UUID

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - Tenant details

    **Errors:**
    - 404: Tenant not found
    """
    tenant_service = TenantService(db)
    tenant = await tenant_service.get_tenant(tenant_id)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    return tenant


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Create a new tenant

    **Request Body:**
    - name: Tenant name
    - slug: Unique identifier (lowercase, alphanumeric, hyphens only)
    - contact_email: Contact email
    - odoo_url: Odoo instance URL
    - odoo_database: Odoo database name
    - odoo_username: Odoo username
    - odoo_password: Odoo password
    - plan_id: Subscription plan ID
    - ... (see TenantCreate schema for all fields)

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - Created tenant

    **Errors:**
    - 400: Slug already taken or invalid data
    - 404: Plan not found
    """
    tenant_service = TenantService(db)

    tenant = await tenant_service.create_tenant(
        **tenant_data.dict(),
        created_by=current_admin.id
    )

    return tenant


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    tenant_data: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Update tenant

    **Path Parameters:**
    - tenant_id: Tenant UUID

    **Request Body:**
    - Any fields from TenantUpdate schema (all optional)

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - Updated tenant

    **Errors:**
    - 400: Slug already taken
    - 404: Tenant not found
    """
    tenant_service = TenantService(db)

    # Only include non-None values
    update_data = tenant_data.dict(exclude_unset=True)

    tenant = await tenant_service.update_tenant(tenant_id, update_data)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    return tenant


@router.post("/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Suspend a tenant

    Suspends tenant access to the system.

    **Path Parameters:**
    - tenant_id: Tenant UUID

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - Success message

    **Errors:**
    - 404: Tenant not found
    """
    tenant_service = TenantService(db)
    success = await tenant_service.suspend_tenant(tenant_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    return {"message": "Tenant suspended successfully"}


@router.post("/{tenant_id}/activate")
async def activate_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Activate a tenant

    Activates a suspended or trial tenant.

    **Path Parameters:**
    - tenant_id: Tenant UUID

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - Success message

    **Errors:**
    - 404: Tenant not found
    """
    tenant_service = TenantService(db)
    success = await tenant_service.activate_tenant(tenant_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    return {"message": "Tenant activated successfully"}


@router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Delete a tenant (soft delete)

    Marks tenant as deleted (soft delete).

    **Path Parameters:**
    - tenant_id: Tenant UUID

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - Success message

    **Errors:**
    - 404: Tenant not found
    """
    tenant_service = TenantService(db)
    success = await tenant_service.delete_tenant(tenant_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    return {"message": "Tenant deleted successfully"}


@router.post("/{tenant_id}/test-connection", response_model=TenantConnectionTest)
async def test_tenant_connection(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Test Odoo connection for a tenant

    Tests if the tenant's Odoo instance is reachable.

    **Path Parameters:**
    - tenant_id: Tenant UUID

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - success: Whether connection was successful
    - message: Connection test result message
    - url: Odoo URL tested

    **Errors:**
    - 404: Tenant not found
    """
    tenant_service = TenantService(db)
    result = await tenant_service.test_odoo_connection(tenant_id)
    return result


class RateLimitStatus(BaseModel):
    """Rate limit status response"""
    hourly_count: int
    hourly_limit: int
    hourly_remaining: int
    daily_count: int
    daily_limit: int
    daily_remaining: int
    hourly_key: str
    daily_key: str


@router.get("/{tenant_id}/rate-limit", response_model=RateLimitStatus)
async def get_rate_limit_status(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Get current rate limit status for a tenant

    **Path Parameters:**
    - tenant_id: Tenant UUID

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - Current rate limit counts and limits
    """
    tenant_service = TenantService(db)
    tenant = await tenant_service.get_tenant(tenant_id)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Get limits
    hourly_limit = tenant.max_requests_per_hour or settings.DEFAULT_TENANT_RATE_LIMIT_PER_HOUR
    daily_limit = tenant.max_requests_per_day or settings.DEFAULT_TENANT_RATE_LIMIT_PER_DAY

    # Connect to Redis
    redis_client = await redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )

    try:
        # Get current keys
        now = datetime.utcnow()
        hour_key = f"rate_limit:tenant:{tenant_id}:hour:{now.strftime('%Y%m%d%H')}"
        day_key = f"rate_limit:tenant:{tenant_id}:day:{now.strftime('%Y%m%d')}"

        # Get counts
        hourly_count = int(await redis_client.get(hour_key) or 0)
        daily_count = int(await redis_client.get(day_key) or 0)

        return RateLimitStatus(
            hourly_count=hourly_count,
            hourly_limit=hourly_limit,
            hourly_remaining=max(0, hourly_limit - hourly_count),
            daily_count=daily_count,
            daily_limit=daily_limit,
            daily_remaining=max(0, daily_limit - daily_count),
            hourly_key=hour_key,
            daily_key=day_key
        )
    finally:
        await redis_client.close()


@router.post("/{tenant_id}/rate-limit/reset")
async def reset_rate_limit(
    tenant_id: UUID,
    reset_type: str = Query("all", regex="^(daily|hourly|all)$"),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Reset rate limit counters for a tenant

    **Path Parameters:**
    - tenant_id: Tenant UUID

    **Query Parameters:**
    - reset_type: Type of reset (daily, hourly, or all) - default: all

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - Message confirming reset
    """
    tenant_service = TenantService(db)
    tenant = await tenant_service.get_tenant(tenant_id)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Connect to Redis
    redis_client = await redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )

    try:
        now = datetime.utcnow()
        deleted_keys = []

        if reset_type in ["daily", "all"]:
            day_key = f"rate_limit:tenant:{tenant_id}:day:{now.strftime('%Y%m%d')}"
            result = await redis_client.delete(day_key)
            if result:
                deleted_keys.append(day_key)
                logger.info(f"Deleted daily rate limit key: {day_key}")

        if reset_type in ["hourly", "all"]:
            hour_key = f"rate_limit:tenant:{tenant_id}:hour:{now.strftime('%Y%m%d%H')}"
            result = await redis_client.delete(hour_key)
            if result:
                deleted_keys.append(hour_key)
                logger.info(f"Deleted hourly rate limit key: {hour_key}")

        if reset_type == "all":
            # Delete all keys for this tenant
            pattern = f"rate_limit:tenant:{tenant_id}:*"
            keys = await redis_client.keys(pattern)
            if keys:
                deleted = await redis_client.delete(*keys)
                deleted_keys.extend(keys)
                logger.info(f"Deleted {deleted} rate limit keys for tenant {tenant_id}")

        return {
            "message": f"Rate limit reset successful",
            "reset_type": reset_type,
            "deleted_keys": len(deleted_keys),
            "keys": deleted_keys
        }
    finally:
        await redis_client.close()
