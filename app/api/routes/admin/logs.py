"""
Admin logs routes for viewing usage and error logs
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from app.db.session import get_db
from app.services.logging_service import LoggingService
from app.api.routes.admin.dependencies import get_current_admin
from app.models.admin import Admin
from app.models.error_log import ErrorSeverity
from pydantic import BaseModel


# Response schemas
class UsageLogResponse(BaseModel):
    """Usage log response"""
    id: int
    tenant_id: UUID
    user_id: Optional[UUID]
    timestamp: datetime
    endpoint: str
    method: str
    model_name: Optional[str]
    request_size_bytes: Optional[int]
    response_size_bytes: Optional[int]
    response_time_ms: Optional[int]
    status_code: int
    ip_address: Optional[str]

    class Config:
        from_attributes = True


class ErrorLogResponse(BaseModel):
    """Error log response"""
    id: int
    tenant_id: UUID
    timestamp: datetime
    error_type: str
    error_message: str
    stack_trace: Optional[str]
    endpoint: Optional[str]
    method: Optional[str]
    severity: str
    is_resolved: bool
    resolved_at: Optional[datetime]
    resolved_by: Optional[UUID]
    resolution_notes: Optional[str]

    class Config:
        from_attributes = True


class ResolveErrorRequest(BaseModel):
    """Request to resolve an error"""
    resolution_notes: Optional[str] = None


router = APIRouter(prefix="/admin/logs", tags=["Admin Logs"])


@router.get("/usage", response_model=List[UsageLogResponse])
async def get_usage_logs(
    tenant_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    method: Optional[str] = Query(None, regex="^(GET|POST|PUT|DELETE|PATCH)$"),
    status_code: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Get usage logs with filters

    Returns API request logs with optional filtering.

    **Query Parameters:**
    - tenant_id: Filter by tenant (optional)
    - skip: Number of records to skip (default: 0)
    - limit: Maximum records to return (1-500, default: 100)
    - start_date: Filter from this date (ISO format)
    - end_date: Filter until this date (ISO format)
    - method: Filter by HTTP method (GET, POST, PUT, DELETE, PATCH)
    - status_code: Filter by status code

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - List of usage logs
    """
    logging_service = LoggingService(db)
    logs = await logging_service.get_usage_logs(
        tenant_id=tenant_id,
        skip=skip,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        method=method,
        status_code=status_code
    )
    return logs


@router.get("/usage/summary")
async def get_usage_summary(
    tenant_id: UUID,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Get usage statistics summary for a tenant

    **Query Parameters:**
    - tenant_id: Tenant UUID (required)
    - days: Number of days to analyze (1-365, default: 30)

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - Usage statistics summary
    """
    logging_service = LoggingService(db)
    return await logging_service.get_usage_stats_summary(tenant_id=tenant_id, days=days)


@router.get("/errors", response_model=List[ErrorLogResponse])
async def get_error_logs(
    tenant_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    severity: Optional[str] = Query(None, regex="^(low|medium|high|critical)$"),
    unresolved_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Get error logs with filters

    **Query Parameters:**
    - tenant_id: Filter by tenant (optional)
    - skip: Number of records to skip (default: 0)
    - limit: Maximum records to return (1-500, default: 100)
    - severity: Filter by severity (low, medium, high, critical)
    - unresolved_only: Only show unresolved errors (default: false)

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - List of error logs
    """
    logging_service = LoggingService(db)

    severity_enum = ErrorSeverity(severity) if severity else None

    logs = await logging_service.get_error_logs(
        tenant_id=tenant_id,
        skip=skip,
        limit=limit,
        severity=severity_enum,
        unresolved_only=unresolved_only
    )
    return logs


@router.get("/errors/summary")
async def get_error_summary(
    tenant_id: UUID,
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Get error summary for a tenant

    **Query Parameters:**
    - tenant_id: Tenant UUID (required)
    - days: Number of days to analyze (1-90, default: 7)

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - Error statistics summary
    """
    logging_service = LoggingService(db)
    return await logging_service.get_error_summary(tenant_id=tenant_id, days=days)


@router.post("/errors/{error_id}/resolve")
async def resolve_error(
    error_id: int,
    resolve_data: ResolveErrorRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Mark an error as resolved

    **Path Parameters:**
    - error_id: Error log ID

    **Request Body:**
    - resolution_notes: Optional notes about the resolution

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - Success message

    **Errors:**
    - 404: Error not found
    """
    logging_service = LoggingService(db)

    error = await logging_service.resolve_error(
        error_id=error_id,
        resolved_by=current_admin.id,
        resolution_notes=resolve_data.resolution_notes
    )

    if not error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Error log not found"
        )

    return {"message": "Error marked as resolved"}
