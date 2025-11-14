"""
System API routes for CRUD operations

All endpoints for interacting with external systems
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Any, Dict
from loguru import logger

from app.db.session import get_db
from app.core.dependencies import get_current_user, get_client_ip, get_user_agent
from app.models.user import User
from app.schemas.system import (
    CRUDRequest,
    CRUDResponse,
    MetadataResponse
)
from app.services.system_service import SystemService
from app.services.cache_service import CacheService
from app.services.audit_service import AuditService
from app.repositories.audit_repository import AuditRepository
from app.core.config import settings

router = APIRouter(prefix="/systems", tags=["Systems"])

# Initialize services
cache_service = CacheService(settings.REDIS_URL)
audit_repo = None  # Will be initialized with DB session
system_service = None  # Will be initialized with dependencies


def get_system_service(db: AsyncSession = Depends(get_db)) -> SystemService:
    """Get system service instance"""
    audit_repo = AuditRepository(db)
    audit_service = AuditService(audit_repo)
    return SystemService(cache_service, audit_service)


@router.post("/{system_id}/create", response_model=CRUDResponse)
async def create_record(
    system_id: str,
    model: str = Query(..., description="Model name (e.g., res.partner)"),
    data: Dict[str, Any] = ...,
    use_universal_schema: bool = Query(False, description="Use universal schema"),
    system_version: Optional[str] = Query(None, description="System version"),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    service: SystemService = Depends(get_system_service)
):
    """
    Create a new record in external system

    Args:
        system_id: System identifier
        model: Model/entity name
        data: Record data
        use_universal_schema: Transform from universal schema
        system_version: System version for mapping

    Returns:
        Creation result with record ID

    Example:
        ```json
        POST /systems/odoo-prod/create?model=res.partner
        {
            "name": "Ahmed Ali",
            "email": "ahmed@example.com",
            "phone": "+966501234567"
        }
        ```
    """
    try:
        result = await service.create_record(
            user_id=current_user.id,
            system_id=system_id,
            model=model,
            data=data,
            use_universal_schema=use_universal_schema,
            system_version=system_version,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )

        return CRUDResponse(
            success=True,
            data=result,
            message=f"Record created successfully"
        )

    except Exception as e:
        logger.error(f"Create record error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{system_id}/read", response_model=List[Dict[str, Any]])
async def read_records(
    system_id: str,
    model: str = Query(..., description="Model name"),
    domain: Optional[str] = Query(None, description="Search domain as JSON string"),
    fields: Optional[str] = Query(None, description="Comma-separated field names"),
    limit: int = Query(80, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    order: Optional[str] = Query(None, description="Sort order"),
    use_universal_schema: bool = Query(False),
    system_version: Optional[str] = Query(None),
    use_cache: bool = Query(True),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    service: SystemService = Depends(get_system_service)
):
    """
    Read/search records from external system

    Args:
        system_id: System identifier
        model: Model/entity name
        domain: Search filters (JSON array)
        fields: Fields to return
        limit: Maximum records
        offset: Records to skip
        order: Sort order
        use_universal_schema: Transform to universal schema
        system_version: System version for mapping
        use_cache: Use caching

    Returns:
        List of records

    Example:
        ```
        GET /systems/odoo-prod/read?model=res.partner&fields=name,email,phone&limit=10
        ```
    """
    try:
        # Parse domain if provided
        import json
        domain_list = json.loads(domain) if domain else None

        # Parse fields
        fields_list = fields.split(",") if fields else None

        records = await service.read_records(
            user_id=current_user.id,
            system_id=system_id,
            model=model,
            domain=domain_list,
            fields=fields_list,
            limit=limit,
            offset=offset,
            order=order,
            use_universal_schema=use_universal_schema,
            system_version=system_version,
            use_cache=use_cache,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )

        return records

    except Exception as e:
        logger.error(f"Read records error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{system_id}/update/{record_id}", response_model=CRUDResponse)
async def update_record(
    system_id: str,
    record_id: int,
    model: str = Query(..., description="Model name"),
    data: Dict[str, Any] = ...,
    use_universal_schema: bool = Query(False),
    system_version: Optional[str] = Query(None),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    service: SystemService = Depends(get_system_service)
):
    """
    Update an existing record in external system

    Args:
        system_id: System identifier
        record_id: Record ID to update
        model: Model/entity name
        data: Updated data
        use_universal_schema: Transform from universal schema
        system_version: System version for mapping

    Returns:
        Update result

    Example:
        ```json
        PUT /systems/odoo-prod/update/42?model=res.partner
        {
            "phone": "+966502222222"
        }
        ```
    """
    try:
        result = await service.update_record(
            user_id=current_user.id,
            system_id=system_id,
            model=model,
            record_id=record_id,
            data=data,
            use_universal_schema=use_universal_schema,
            system_version=system_version,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )

        return CRUDResponse(
            success=True,
            data=result,
            message="Record updated successfully"
        )

    except Exception as e:
        logger.error(f"Update record error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{system_id}/delete/{record_id}", response_model=CRUDResponse)
async def delete_record(
    system_id: str,
    record_id: int,
    model: str = Query(..., description="Model name"),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    service: SystemService = Depends(get_system_service)
):
    """
    Delete a record from external system

    Args:
        system_id: System identifier
        record_id: Record ID to delete
        model: Model/entity name

    Returns:
        Deletion result

    Example:
        ```
        DELETE /systems/odoo-prod/delete/42?model=res.partner
        ```
    """
    try:
        result = await service.delete_record(
            user_id=current_user.id,
            system_id=system_id,
            model=model,
            record_id=record_id,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )

        return CRUDResponse(
            success=True,
            data=result,
            message="Record deleted successfully"
        )

    except Exception as e:
        logger.error(f"Delete record error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{system_id}/metadata", response_model=Dict[str, Any])
async def get_metadata(
    system_id: str,
    model: str = Query(..., description="Model name"),
    use_cache: bool = Query(True),
    current_user: User = Depends(get_current_user),
    service: SystemService = Depends(get_system_service)
):
    """
    Get metadata/schema information for a model

    Args:
        system_id: System identifier
        model: Model/entity name
        use_cache: Use caching

    Returns:
        Model metadata (fields, types, relations, etc.)

    Example:
        ```
        GET /systems/odoo-prod/metadata?model=res.partner
        ```
    """
    try:
        metadata = await service.get_metadata(
            system_id=system_id,
            model=model,
            use_cache=use_cache
        )

        return metadata

    except Exception as e:
        logger.error(f"Get metadata error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{system_id}/connect")
async def connect_system(
    system_id: str,
    config: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    service: SystemService = Depends(get_system_service)
):
    """
    Connect to external system

    Args:
        system_id: System identifier
        config: Connection configuration

    Returns:
        Connection result

    Example:
        ```json
        POST /systems/odoo-prod/connect
        {
            "url": "https://demo.odoo.com",
            "database": "demo",
            "username": "admin",
            "password": "admin"
        }
        ```
    """
    try:
        system_type = config.get("system_type", "odoo")
        adapter = await service.connect_system(
            system_id=system_id,
            system_type=system_type,
            config=config
        )

        return {
            "success": True,
            "message": f"Connected to {system_id}",
            "is_connected": adapter.is_connected
        }

    except Exception as e:
        logger.error(f"Connect system error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{system_id}/disconnect")
async def disconnect_system(
    system_id: str,
    current_user: User = Depends(get_current_user),
    service: SystemService = Depends(get_system_service)
):
    """
    Disconnect from external system

    Args:
        system_id: System identifier

    Returns:
        Disconnection result
    """
    try:
        success = await service.disconnect_system(system_id)

        return {
            "success": success,
            "message": f"Disconnected from {system_id}" if success else "System not found"
        }

    except Exception as e:
        logger.error(f"Disconnect system error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
