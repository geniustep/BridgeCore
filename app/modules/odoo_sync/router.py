# -*- coding: utf-8 -*-
"""
Odoo Sync Router - REST API endpoints for Odoo sync operations

Provides endpoints for:
- Pulling events from Odoo
- Acknowledging processed events
- Managing user sync states
- Health checks and statistics
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List
from loguru import logger
from datetime import datetime

from app.modules.odoo_sync.service import OdooSyncService
from app.modules.odoo_sync.schemas import (
    OdooPullRequest,
    OdooPullResponse,
    OdooAckRequest,
    OdooAckResponse,
    SyncStateRequest,
    SyncStateUpdateRequest,
    SyncStateGetResponse,
    SyncStatisticsResponse,
    OdooHealthResponse,
    OdooStatsResponse,
    AppType,
    Priority
)
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.services.cache_service import CacheService, get_cache_service
from app.core.rate_limiter import limiter
from starlette.requests import Request


router = APIRouter(
    prefix="/api/v1/odoo-sync",
    tags=["odoo-sync"]
)


# ================================================================
# Dependencies
# ================================================================

def get_odoo_sync_service(
    cache_service: CacheService = Depends(get_cache_service)
) -> OdooSyncService:
    """Get Odoo Sync Service instance"""
    return OdooSyncService(
        odoo_url=settings.ODOO_URL,
        api_key=settings.ODOO_WEBHOOK_API_KEY,
        cache_service=cache_service
    )


# ================================================================
# Pull Events
# ================================================================

@router.post(
    "/pull",
    response_model=OdooPullResponse,
    summary="Pull events from Odoo",
    description="Pull webhook events from Odoo's update.webhook table"
)
@limiter.limit("60/minute")
async def pull_events(
    request: Request,
    pull_request: OdooPullRequest,
    user = Depends(get_current_user),
    service: OdooSyncService = Depends(get_odoo_sync_service)
):
    """
    Pull events from Odoo's update.webhook table
    
    This endpoint connects to auto-webhook-odoo and pulls events
    that haven't been processed yet.
    
    - **last_event_id**: Start pulling from this ID (exclusive)
    - **limit**: Maximum events to pull (1-1000)
    - **models**: Filter by specific models
    - **priority**: Filter by priority (high/medium/low)
    - **app_type**: Auto-filter models by app type
    """
    try:
        logger.info(f"User {user.id} pulling events from Odoo")
        
        result = await service.pull_events(
            last_event_id=pull_request.last_event_id,
            limit=pull_request.limit,
            models=pull_request.models,
            priority=pull_request.priority,
            app_type=pull_request.app_type
        )
        
        return result
        
    except ConnectionError as e:
        logger.error(f"Connection error pulling from Odoo: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to Odoo: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Error pulling events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/pull",
    response_model=OdooPullResponse,
    summary="Pull events from Odoo (GET)",
    description="Pull webhook events using query parameters"
)
@limiter.limit("60/minute")
async def pull_events_get(
    request: Request,
    last_event_id: int = Query(0, description="Last event ID pulled"),
    limit: int = Query(100, ge=1, le=1000, description="Max events"),
    models: Optional[str] = Query(None, description="Comma-separated model names"),
    priority: Optional[Priority] = Query(None, description="Priority filter"),
    app_type: Optional[AppType] = Query(None, description="App type for model filtering"),
    user = Depends(get_current_user),
    service: OdooSyncService = Depends(get_odoo_sync_service)
):
    """Pull events using GET with query parameters"""
    try:
        models_list = [m.strip() for m in models.split(",")] if models else None
        
        result = await service.pull_events(
            last_event_id=last_event_id,
            limit=limit,
            models=models_list,
            priority=priority.value if priority else None,
            app_type=app_type.value if app_type else None
        )
        
        return result
        
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to Odoo: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Error pulling events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ================================================================
# Acknowledge Events
# ================================================================

@router.post(
    "/ack",
    response_model=OdooAckResponse,
    summary="Acknowledge events",
    description="Mark events as processed in Odoo"
)
@limiter.limit("60/minute")
async def acknowledge_events(
    request: Request,
    ack_request: OdooAckRequest,
    user = Depends(get_current_user),
    service: OdooSyncService = Depends(get_odoo_sync_service)
):
    """
    Acknowledge events as processed
    
    Call this after successfully processing events to mark them
    as processed in Odoo's update.webhook table.
    """
    try:
        logger.info(f"User {user.id} acknowledging {len(ack_request.event_ids)} events")
        
        result = await service.acknowledge_events(ack_request.event_ids)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.message
            )
        
        return result
        
    except HTTPException:
        raise
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to Odoo: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Error acknowledging events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ================================================================
# Sync State Management
# ================================================================

@router.post(
    "/sync-state",
    response_model=SyncStateGetResponse,
    summary="Get or create sync state",
    description="Get existing sync state or create new one for user/device"
)
@limiter.limit("30/minute")
async def get_or_create_sync_state(
    request: Request,
    state_request: SyncStateRequest,
    user = Depends(get_current_user),
    service: OdooSyncService = Depends(get_odoo_sync_service)
):
    """
    Get or create sync state for a user/device
    
    Returns the current sync state including last_event_id which
    should be used for pulling new events.
    """
    try:
        sync_state = await service.get_sync_state(
            user_id=state_request.user_id,
            device_id=state_request.device_id,
            app_type=state_request.app_type
        )
        
        if not sync_state:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get or create sync state"
            )
        
        return SyncStateGetResponse(
            success=True,
            sync_state=sync_state,
            timestamp=datetime.now()
        )
        
    except HTTPException:
        raise
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to Odoo: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Error getting sync state: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/sync-state/update",
    response_model=SyncStateGetResponse,
    summary="Update sync state",
    description="Update sync state after pulling events"
)
@limiter.limit("60/minute")
async def update_sync_state(
    request: Request,
    update_request: SyncStateUpdateRequest,
    user = Depends(get_current_user),
    service: OdooSyncService = Depends(get_odoo_sync_service)
):
    """
    Update sync state after pulling events
    
    Call this after successfully processing pulled events to
    update the last_event_id and sync statistics.
    """
    try:
        sync_state = await service.update_sync_state(
            user_id=update_request.user_id,
            device_id=update_request.device_id,
            last_event_id=update_request.last_event_id,
            events_synced=update_request.events_synced
        )
        
        if not sync_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sync state not found"
            )
        
        return SyncStateGetResponse(
            success=True,
            sync_state=sync_state,
            timestamp=datetime.now()
        )
        
    except HTTPException:
        raise
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to Odoo: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Error updating sync state: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/sync-state/stats",
    response_model=SyncStatisticsResponse,
    summary="Get sync statistics",
    description="Get sync statistics for a user"
)
@limiter.limit("30/minute")
async def get_sync_statistics(
    request: Request,
    user_id: int = Query(..., description="User ID"),
    device_id: Optional[str] = Query(None, description="Device ID filter"),
    app_type: Optional[str] = Query(None, description="App type filter"),
    user = Depends(get_current_user),
    service: OdooSyncService = Depends(get_odoo_sync_service)
):
    """Get sync statistics for a user"""
    try:
        result = await service.get_sync_statistics(
            user_id=user_id,
            device_id=device_id,
            app_type=app_type
        )
        
        return result
        
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to Odoo: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Error getting sync statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ================================================================
# Smart Pull (Convenience Endpoint)
# ================================================================

@router.post(
    "/smart-pull",
    summary="Smart pull with auto sync state",
    description="Pull events with automatic sync state management"
)
@limiter.limit("30/minute")
async def smart_pull(
    request: Request,
    user_id: int = Query(..., description="User ID"),
    device_id: str = Query(..., min_length=3, description="Device ID"),
    app_type: AppType = Query(AppType.MOBILE_APP, description="App type"),
    limit: int = Query(100, ge=1, le=1000, description="Max events"),
    auto_ack: bool = Query(True, description="Auto-acknowledge events"),
    user = Depends(get_current_user),
    service: OdooSyncService = Depends(get_odoo_sync_service)
):
    """
    Smart pull: Get sync state → Pull events → Update state
    
    This is a convenience endpoint that:
    1. Gets the user's sync state to find last_event_id
    2. Pulls new events since last_event_id
    3. Optionally acknowledges the events
    4. Updates the sync state
    
    Use this for simple sync workflows.
    """
    try:
        result = await service.smart_pull(
            user_id=user_id,
            device_id=device_id,
            app_type=app_type.value,
            limit=limit,
            auto_ack=auto_ack
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Smart pull failed")
            )
        
        return result
        
    except HTTPException:
        raise
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to Odoo: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Error in smart pull: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ================================================================
# Health & Statistics
# ================================================================

@router.get(
    "/health",
    response_model=OdooHealthResponse,
    summary="Health check",
    description="Check Odoo webhook API health"
)
async def health_check(
    service: OdooSyncService = Depends(get_odoo_sync_service)
):
    """
    Check Odoo webhook API health
    
    Returns connection status, pending events count, and version info.
    This endpoint does not require authentication.
    """
    try:
        return await service.health_check()
    except Exception as e:
        logger.exception(f"Health check failed: {e}")
        return OdooHealthResponse(
            status="error",
            odoo_connected=False,
            pending_events=0,
            timestamp=datetime.now()
        )


@router.get(
    "/stats",
    response_model=OdooStatsResponse,
    summary="Get statistics",
    description="Get webhook statistics from Odoo"
)
@limiter.limit("10/minute")
async def get_statistics(
    request: Request,
    days: int = Query(7, ge=1, le=90, description="Days to look back"),
    user = Depends(get_current_user),
    service: OdooSyncService = Depends(get_odoo_sync_service)
):
    """Get webhook statistics from Odoo"""
    try:
        return await service.get_statistics(days=days)
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to Odoo: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Error getting statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

