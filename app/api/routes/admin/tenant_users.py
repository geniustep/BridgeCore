"""
Admin tenant user management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.schemas.admin import (
    TenantUserCreate,
    TenantUserUpdate,
    TenantUserResponse
)
from app.api.routes.admin.dependencies import get_current_admin
from app.models.admin import Admin
from app.models.tenant_user import TenantUser
from app.models.tenant import Tenant
from app.core.security import get_password_hash

router = APIRouter(prefix="/admin/tenant-users", tags=["Admin Tenant User Management"])


@router.get("", response_model=List[TenantUserResponse])
async def list_tenant_users(
    tenant_id: UUID = Query(..., description="Tenant ID to filter users"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    List all users for a specific tenant

    **Query Parameters:**
    - tenant_id: Tenant UUID (required)
    - skip: Number of records to skip (default: 0)
    - limit: Maximum records to return (default: 100, max: 500)

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - List of tenant users
    """
    # Verify tenant exists
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Get users
    result = await db.execute(
        select(TenantUser)
        .where(TenantUser.tenant_id == tenant_id)
        .offset(skip)
        .limit(limit)
        .order_by(TenantUser.created_at.desc())
    )
    users = result.scalars().all()

    return users


@router.get("/{user_id}", response_model=TenantUserResponse)
async def get_tenant_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Get tenant user by ID

    **Path Parameters:**
    - user_id: User UUID

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - Tenant user details

    **Errors:**
    - 404: User not found
    """
    result = await db.execute(
        select(TenantUser).where(TenantUser.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.post("", response_model=TenantUserResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant_user(
    user_data: TenantUserCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Create a new tenant user

    **Request Body:**
    - tenant_id: Tenant UUID
    - email: User email
    - password: User password (min 8 characters)
    - full_name: User full name
    - role: User role (admin or user)
    - is_active: Whether user is active
    - odoo_user_id: Optional Odoo user ID

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - Created tenant user

    **Errors:**
    - 400: Email already exists for this tenant
    - 404: Tenant not found
    """
    # Verify tenant exists
    result = await db.execute(
        select(Tenant).where(Tenant.id == user_data.tenant_id)
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Check if email already exists for this tenant
    result = await db.execute(
        select(TenantUser).where(
            TenantUser.tenant_id == user_data.tenant_id,
            TenantUser.email == user_data.email
        )
    )
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists for this tenant"
        )

    # Create user
    user = TenantUser(
        tenant_id=user_data.tenant_id,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        is_active=user_data.is_active,
        odoo_user_id=user_data.odoo_user_id
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.put("/{user_id}", response_model=TenantUserResponse)
async def update_tenant_user(
    user_id: UUID,
    user_data: TenantUserUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Update tenant user

    **Path Parameters:**
    - user_id: User UUID

    **Request Body:**
    - Any fields from TenantUserUpdate schema (all optional)
    - password: If provided, will be hashed and updated

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - Updated tenant user

    **Errors:**
    - 400: Email already exists for another user in this tenant
    - 404: User not found
    """
    # Get user
    result = await db.execute(
        select(TenantUser).where(TenantUser.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check email uniqueness if updating email
    if user_data.email and user_data.email != user.email:
        result = await db.execute(
            select(TenantUser).where(
                TenantUser.tenant_id == user.tenant_id,
                TenantUser.email == user_data.email,
                TenantUser.id != user_id
            )
        )
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists for another user in this tenant"
            )

    # Update fields
    update_data = user_data.dict(exclude_unset=True)
    
    # Hash password if provided
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    for key, value in update_data.items():
        if hasattr(user, key):
            setattr(user, key, value)

    await db.commit()
    await db.refresh(user)

    return user


@router.delete("/{user_id}")
async def delete_tenant_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Delete a tenant user

    **Path Parameters:**
    - user_id: User UUID

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - Success message

    **Errors:**
    - 404: User not found
    """
    # Get user
    result = await db.execute(
        select(TenantUser).where(TenantUser.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    await db.delete(user)
    await db.commit()

    return {"message": "User deleted successfully"}

