"""
Trigger API routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID

from app.db.session import get_db
from app.core.security import decode_tenant_token
from app.services.trigger_service import TriggerService
from app.models.trigger import TriggerEvent, TriggerStatus
from app.schemas.trigger_schemas import (
    TriggerCreate,
    TriggerUpdate,
    TriggerToggle,
    TriggerExecuteManual,
    TriggerResponse,
    TriggerListResponse,
    TriggerExecutionListResponse,
    TriggerStatsResponse,
    ManualExecutionResult,
)
from loguru import logger

router = APIRouter(prefix="/api/v1/triggers", tags=["Triggers"])
security = HTTPBearer()


async def get_tenant_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Extract tenant and user info from JWT token"""
    token = credentials.credentials
    payload = decode_tenant_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return {
        "user_id": UUID(payload.get("sub")),
        "tenant_id": UUID(payload.get("tenant_id")),
        "email": payload.get("email"),
        "role": payload.get("role")
    }


# ============================================================================
# Trigger CRUD
# ============================================================================

@router.post("/create", response_model=TriggerResponse)
async def create_trigger(
    body: TriggerCreate,
    auth: dict = Depends(get_tenant_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new automation trigger

    Triggers allow you to automate actions when Odoo events occur.

    **Event Types:**
    - `on_create`: When a record is created
    - `on_update`: When a record is updated
    - `on_delete`: When a record is deleted
    - `on_workflow`: When a workflow state changes
    - `scheduled`: Run on a schedule (cron)
    - `manual`: Execute manually via API

    **Action Types:**
    - `webhook`: Call an external URL
    - `email`: Send an email
    - `notification`: Create in-app notification
    - `odoo_method`: Call an Odoo method
    """
    service = TriggerService(db)
    trigger = await service.create_trigger(auth["tenant_id"], body)
    return TriggerResponse.model_validate(trigger)


@router.get("/list", response_model=TriggerListResponse)
async def list_triggers(
    model: Optional[str] = Query(None, description="Filter by Odoo model"),
    event: Optional[TriggerEvent] = Query(None, description="Filter by event type"),
    status: Optional[TriggerStatus] = Query(None, description="Filter by status"),
    is_enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    auth: dict = Depends(get_tenant_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    List all triggers for the tenant
    """
    service = TriggerService(db)
    triggers, total = await service.list_triggers(
        tenant_id=auth["tenant_id"],
        model=model,
        event=event,
        status=status,
        is_enabled=is_enabled,
        skip=skip,
        limit=limit
    )

    return TriggerListResponse(
        triggers=[TriggerResponse.model_validate(t) for t in triggers],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{trigger_id}", response_model=TriggerResponse)
async def get_trigger(
    trigger_id: UUID,
    auth: dict = Depends(get_tenant_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get trigger details by ID
    """
    service = TriggerService(db)
    trigger = await service.get_trigger(trigger_id, auth["tenant_id"])

    if not trigger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trigger not found"
        )

    return TriggerResponse.model_validate(trigger)


@router.put("/{trigger_id}", response_model=TriggerResponse)
async def update_trigger(
    trigger_id: UUID,
    body: TriggerUpdate,
    auth: dict = Depends(get_tenant_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing trigger
    """
    service = TriggerService(db)
    trigger = await service.update_trigger(trigger_id, auth["tenant_id"], body)

    if not trigger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trigger not found"
        )

    return TriggerResponse.model_validate(trigger)


@router.delete("/{trigger_id}")
async def delete_trigger(
    trigger_id: UUID,
    auth: dict = Depends(get_tenant_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a trigger
    """
    service = TriggerService(db)
    success = await service.delete_trigger(trigger_id, auth["tenant_id"])

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trigger not found"
        )

    return {"success": True, "message": "Trigger deleted successfully"}


@router.post("/{trigger_id}/toggle", response_model=TriggerResponse)
async def toggle_trigger(
    trigger_id: UUID,
    body: TriggerToggle,
    auth: dict = Depends(get_tenant_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Enable or disable a trigger
    """
    service = TriggerService(db)
    trigger = await service.toggle_trigger(trigger_id, auth["tenant_id"], body.is_enabled)

    if not trigger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trigger not found"
        )

    return TriggerResponse.model_validate(trigger)


# ============================================================================
# Trigger Execution
# ============================================================================

@router.post("/{trigger_id}/execute", response_model=ManualExecutionResult)
async def execute_trigger(
    trigger_id: UUID,
    body: TriggerExecuteManual,
    auth: dict = Depends(get_tenant_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually execute a trigger

    Use this to test triggers or execute them on demand.

    **Parameters:**
    - `record_ids`: Optional list of specific record IDs to process
    - `test_mode`: If true, validates but doesn't actually execute actions
    """
    service = TriggerService(db)

    try:
        executions = await service.execute_manual(
            trigger_id=trigger_id,
            tenant_id=auth["tenant_id"],
            record_ids=body.record_ids,
            test_mode=body.test_mode
        )

        return ManualExecutionResult(
            success=True,
            message=f"Executed trigger {'in test mode' if body.test_mode else 'successfully'}",
            executed_count=len(executions),
            results=[
                {
                    "execution_id": str(e.id),
                    "success": e.success,
                    "result": e.result,
                    "error": e.error_message
                }
                for e in executions
            ]
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{trigger_id}/history", response_model=TriggerExecutionListResponse)
async def get_trigger_history(
    trigger_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    auth: dict = Depends(get_tenant_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get trigger execution history
    """
    service = TriggerService(db)

    # Verify trigger exists
    trigger = await service.get_trigger(trigger_id, auth["tenant_id"])
    if not trigger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trigger not found"
        )

    executions, total = await service.get_execution_history(
        trigger_id=trigger_id,
        tenant_id=auth["tenant_id"],
        skip=skip,
        limit=limit
    )

    from app.schemas.trigger_schemas import TriggerExecutionResponse
    return TriggerExecutionListResponse(
        executions=[TriggerExecutionResponse.model_validate(e) for e in executions],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{trigger_id}/stats", response_model=TriggerStatsResponse)
async def get_trigger_stats(
    trigger_id: UUID,
    auth: dict = Depends(get_tenant_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get trigger execution statistics
    """
    service = TriggerService(db)
    stats = await service.get_trigger_stats(trigger_id, auth["tenant_id"])

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trigger not found"
        )

    return TriggerStatsResponse(**stats)

