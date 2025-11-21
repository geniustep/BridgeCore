"""
Admin tenant management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID

from app.db.session import get_db
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
