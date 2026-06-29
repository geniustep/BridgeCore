"""
Admin alerts management routes
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
from app.models.alert import AlertType, AlertSeverity, AlertStatus
from app.services.alert_service import AlertService
from loguru import logger

router = APIRouter(prefix="/admin/alerts", tags=["Admin Alerts"])


# Response schemas
class AlertResponse(BaseModel):
    id: int
    tenant_id: Optional[UUID]
    alert_type: str
    severity: str
    status: str
    title: str
    message: str
    details: Optional[dict]
    threshold_value: Optional[int]
    current_value: Optional[int]
    created_at: datetime
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[UUID]
    resolved_at: Optional[datetime]
    resolved_by: Optional[UUID]
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class AlertCountResponse(BaseModel):
    critical: int
    error: int
    warning: int
    info: int
    total: int


class BulkDismissRequest(BaseModel):
    alert_ids: List[int]


@router.get("", response_model=List[AlertResponse])
async def get_alerts(
    tenant_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None, regex="^(active|acknowledged|resolved|dismissed)$"),
    severity: Optional[str] = Query(None, regex="^(info|warning|error|critical)$"),
    alert_type: Optional[str] = Query(None),
    active_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Get alerts with filters
    
    **Query Parameters:**
    - tenant_id: Filter by tenant
    - status: Filter by status (active, acknowledged, resolved, dismissed)
    - severity: Filter by severity (info, warning, error, critical)
    - alert_type: Filter by type
    - active_only: Only show active alerts
    - skip: Pagination offset
    - limit: Maximum results
    
    **Returns:**
    - List of alerts
    """
    alert_service = AlertService(db)
    
    alerts = await alert_service.get_alerts(
        tenant_id=tenant_id,
        status=AlertStatus(status) if status else None,
        severity=AlertSeverity(severity) if severity else None,
        alert_type=AlertType(alert_type) if alert_type else None,
        active_only=active_only,
        skip=skip,
        limit=limit
    )
    
    return alerts


@router.get("/count", response_model=AlertCountResponse)
async def get_alert_counts(
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Get count of active alerts by severity
    
    **Returns:**
    - Counts by severity and total
    """
    alert_service = AlertService(db)
    counts = await alert_service.get_active_alerts_count()
    return AlertCountResponse(**counts)


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Acknowledge an alert
    
    **Path Parameters:**
    - alert_id: Alert ID
    
    **Returns:**
    - Success message
    """
    alert_service = AlertService(db)
    alert = await alert_service.acknowledge_alert(alert_id, current_admin.id)
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    return {"message": "Alert acknowledged", "alert_id": alert_id}


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Resolve an alert
    
    **Path Parameters:**
    - alert_id: Alert ID
    
    **Returns:**
    - Success message
    """
    alert_service = AlertService(db)
    alert = await alert_service.resolve_alert(alert_id, current_admin.id)
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    return {"message": "Alert resolved", "alert_id": alert_id}


@router.post("/{alert_id}/dismiss")
async def dismiss_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Dismiss an alert
    
    **Path Parameters:**
    - alert_id: Alert ID
    
    **Returns:**
    - Success message
    """
    alert_service = AlertService(db)
    alert = await alert_service.dismiss_alert(alert_id, current_admin.id)
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    return {"message": "Alert dismissed", "alert_id": alert_id}


@router.post("/bulk-dismiss")
async def bulk_dismiss_alerts(
    request: BulkDismissRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Bulk dismiss multiple alerts
    
    **Request Body:**
    - alert_ids: List of alert IDs to dismiss
    
    **Returns:**
    - Count of dismissed alerts
    """
    alert_service = AlertService(db)
    count = await alert_service.bulk_dismiss_alerts(
        request.alert_ids,
        current_admin.id
    )
    
    return {"message": f"Dismissed {count} alerts", "count": count}


@router.post("/cleanup-expired")
async def cleanup_expired_alerts(
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Clean up expired auto-resolve alerts
    
    **Returns:**
    - Count of cleaned up alerts
    """
    alert_service = AlertService(db)
    count = await alert_service.cleanup_expired_alerts()
    
    return {"message": f"Cleaned up {count} expired alerts", "count": count}

