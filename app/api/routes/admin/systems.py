"""
Admin API for managing external systems and tenant connections
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID
from loguru import logger
from datetime import datetime

from app.schemas.system_schemas import (
    ExternalSystemResponse,
    TenantSystemCreate,
    TenantSystemUpdate,
    TenantSystemResponse,
    ConnectionTestRequest,
    ConnectionTestResponse,
    SystemTypeEnum,
    OdooConnectionConfig,
    MoodleConnectionConfig
)
from app.repositories.system_repository import ExternalSystemRepository, TenantSystemRepository
from app.repositories.tenant_repository import TenantRepository
from app.api.routes.admin.dependencies import get_current_admin
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters import OdooAdapter, MoodleAdapter
from app.core.encryption import encrypt_data, decrypt_data

router = APIRouter()


# ============= External Systems Management =============

@router.get("/systems", response_model=List[ExternalSystemResponse])
async def list_systems(
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    List all available external systems (Odoo, Moodle, SAP, etc.)

    Args:
        enabled_only: Only return enabled systems
    """
    repo = ExternalSystemRepository(db)

    if enabled_only:
        systems = await repo.get_enabled_systems()
    else:
        systems = await repo.get_all_systems()

    return systems


@router.get("/systems/{system_id}", response_model=ExternalSystemResponse)
async def get_system(
    system_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get external system by ID"""
    repo = ExternalSystemRepository(db)
    system = await repo.get(system_id)

    if not system:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="System not found"
        )

    return system


# ============= Tenant System Connections =============

@router.get("/tenants/{tenant_id}/systems", response_model=List[TenantSystemResponse])
async def list_tenant_systems(
    tenant_id: UUID,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    List all systems connected to a tenant

    Args:
        tenant_id: Tenant ID
        active_only: Only return active connections
    """
    # Verify tenant exists
    tenant_repo = TenantRepository(db)
    tenant = await tenant_repo.get(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Get tenant systems
    repo = TenantSystemRepository(db)
    connections = await repo.get_by_tenant(tenant_id, active_only)

    return connections


@router.post("/tenants/{tenant_id}/systems", response_model=TenantSystemResponse, status_code=status.HTTP_201_CREATED)
async def add_tenant_system(
    tenant_id: UUID,
    connection: TenantSystemCreate,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Add a new system connection to a tenant

    Args:
        tenant_id: Tenant ID
        connection: Connection details
    """
    # Verify tenant exists
    tenant_repo = TenantRepository(db)
    tenant = await tenant_repo.get(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Verify system exists
    system_repo = ExternalSystemRepository(db)
    system = await system_repo.get(connection.system_id)
    if not system:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="System not found"
        )

    # Check if connection already exists
    conn_repo = TenantSystemRepository(db)
    exists = await conn_repo.check_exists(tenant_id, connection.system_id)
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Connection already exists"
        )

    # Encrypt sensitive data in connection_config
    encrypted_config = encrypt_data(connection.connection_config)

    # Create connection
    new_connection = await conn_repo.create({
        "tenant_id": tenant_id,
        "system_id": connection.system_id,
        "connection_config": encrypted_config,
        "is_active": connection.is_active,
        "is_primary": connection.is_primary,
        "custom_config": connection.custom_config,
        "created_by": current_admin.id
    })

    return new_connection


@router.put("/tenants/{tenant_id}/systems/{connection_id}", response_model=TenantSystemResponse)
async def update_tenant_system(
    tenant_id: UUID,
    connection_id: UUID,
    connection: TenantSystemUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Update tenant system connection"""
    repo = TenantSystemRepository(db)
    existing = await repo.get(connection_id)

    if not existing or existing.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )

    # Prepare update data
    update_data = connection.dict(exclude_unset=True)

    # Encrypt connection_config if provided
    if "connection_config" in update_data:
        update_data["connection_config"] = encrypt_data(update_data["connection_config"])

    # Update
    updated = await repo.update(connection_id, update_data)
    return updated


@router.delete("/tenants/{tenant_id}/systems/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant_system(
    tenant_id: UUID,
    connection_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Delete tenant system connection"""
    repo = TenantSystemRepository(db)
    existing = await repo.get(connection_id)

    if not existing or existing.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )

    await repo.delete(connection_id)
    return None


@router.post("/tenants/{tenant_id}/systems/{connection_id}/set-primary", response_model=dict)
async def set_primary_system(
    tenant_id: UUID,
    connection_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Set a system as primary for the tenant"""
    repo = TenantSystemRepository(db)
    existing = await repo.get(connection_id)

    if not existing or existing.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )

    success = await repo.set_primary(tenant_id, existing.system_id)

    if success:
        return {"success": True, "message": "Primary system updated"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to set primary system"
        )


# ============= Connection Testing =============

@router.post("/test-connection", response_model=ConnectionTestResponse)
async def test_connection(
    request: ConnectionTestRequest,
    current_admin = Depends(get_current_admin)
):
    """
    Test connection to external system

    This endpoint tests connectivity without saving the connection
    """
    try:
        adapter = None
        system_info = None

        if request.system_type == SystemTypeEnum.ODOO:
            # Test Odoo connection
            adapter = OdooAdapter(request.connection_config)
            connected = await adapter.connect()

            if connected:
                # Try to authenticate
                auth_result = await adapter.authenticate(
                    request.connection_config.get("username"),
                    request.connection_config.get("password")
                )
                if auth_result.get("uid"):
                    system_info = {
                        "type": "odoo",
                        "uid": auth_result.get("uid"),
                        "database": request.connection_config.get("database"),
                        "url": request.connection_config.get("url")
                    }
                else:
                    raise Exception("Authentication failed")

        elif request.system_type == SystemTypeEnum.MOODLE:
            # Test Moodle connection
            adapter = MoodleAdapter(request.connection_config)
            connected = await adapter.connect()

            if connected:
                site_info = await adapter.get_metadata("site")
                system_info = {
                    "type": "moodle",
                    "sitename": site_info.get("sitename"),
                    "version": site_info.get("version"),
                    "url": request.connection_config.get("url")
                }

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"System type {request.system_type} not yet supported for testing"
            )

        # Cleanup
        if adapter:
            await adapter.disconnect()

        return ConnectionTestResponse(
            success=True,
            message="Connection successful",
            system_info=system_info,
            tested_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        return ConnectionTestResponse(
            success=False,
            message="Connection failed",
            error=str(e),
            tested_at=datetime.utcnow()
        )


@router.post("/tenants/{tenant_id}/systems/{connection_id}/test", response_model=ConnectionTestResponse)
async def test_existing_connection(
    tenant_id: UUID,
    connection_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Test an existing tenant system connection"""
    repo = TenantSystemRepository(db)
    connection = await repo.get(connection_id)

    if not connection or connection.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )

    # Decrypt connection config
    decrypted_config = decrypt_data(connection.connection_config)

    # Test connection
    test_request = ConnectionTestRequest(
        system_type=connection.external_system.system_type,
        connection_config=decrypted_config
    )

    result = await test_connection(test_request, current_admin)

    # Update connection status
    await repo.update_connection_status(
        connection_id,
        result.success,
        result.error
    )

    return result
