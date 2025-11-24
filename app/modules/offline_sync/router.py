"""
Offline Sync Router

FastAPI endpoints for offline synchronization
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from loguru import logger
from typing import Optional

from app.modules.offline_sync.schemas import (
    # Push
    OfflinePushRequest,
    OfflinePushResponse,

    # Pull
    OfflinePullRequest,
    OfflinePullResponse,

    # Conflict
    ConflictResolutionRequest,
    ConflictResolutionResponse,

    # State
    SyncStateResponse,

    # Full sync
    FullSyncRequest,
    FullSyncResponse,
)

from app.modules.offline_sync.service import OfflineSyncService
from app.core.dependencies import get_current_user
from app.core.rate_limiter import limiter
from app.utils.odoo_client import OdooClient
from app.services.cache_service import CacheService
from app.models.user import User


router = APIRouter(
    prefix="/api/v1/offline-sync",
    tags=["Offline Sync"]
)


# ===== Dependencies =====

async def get_offline_sync_service(
    current_user: User = Depends(get_current_user),
) -> OfflineSyncService:
    """
    Get offline sync service instance

    This uses the user's Odoo connection from their JWT token
    """
    from app.db.session import get_db
    from sqlalchemy.ext.asyncio import AsyncSession
    from fastapi import Depends as FastAPIDepends
    from app.models.system import System
    from sqlalchemy import select

    # Get database session
    async def _get_service():
        async for db in get_db():
            try:
                # Get user's active Odoo system
                query = select(System).where(
                    System.user_id == current_user.id,
                    System.system_type == "odoo",
                    System.is_active == True
                ).order_by(System.updated_at.desc()).limit(1)

                result = await db.execute(query)
                system = result.scalar_one_or_none()

                if not system:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No active Odoo system found. Please connect to Odoo first."
                    )

                # Get or create Odoo client
                from app.api.routes.systems import get_system_service
                service = get_system_service(db)
                system_id = system.system_id

                adapter = service.adapters.get(system_id)
                if not adapter or not adapter.is_connected:
                    config = system.connection_config
                    adapter = await service.connect_system(
                        system_id=system_id,
                        system_type=system.system_type,
                        config=config
                    )

                session_id = getattr(adapter, 'session_id', None)
                if not session_id:
                    # Try to authenticate
                    config = system.connection_config
                    username = config.get("username")
                    password = config.get("password")

                    if username and password:
                        auth_result = await adapter.authenticate(username, password)
                        if auth_result.get("success"):
                            session_id = auth_result.get("session_id")

                if not session_id:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Odoo session not found. Please connect to Odoo first."
                    )

                # Create OdooClient
                from app.core.config import settings
                odoo_client = OdooClient(
                    base_url=settings.ODOO_URL,
                    session_id=session_id,
                    timeout=30,
                    retries=3,
                    backoff=0.5,
                    user_agent="BridgeCore-OfflineSync/1.0"
                )

                # Create cache service
                cache_service = CacheService()

                # Return service
                return OfflineSyncService(
                    odoo_client=odoo_client,
                    cache_service=cache_service,
                )

            finally:
                await db.close()

    return await _get_service()


# ===== PUSH Endpoints =====

@router.post(
    "/push",
    response_model=OfflinePushResponse,
    summary="Push local changes to server",
    description="Upload local offline changes to Odoo server with conflict detection"
)
@limiter.limit("100/minute")
async def push_local_changes(
    request: Request,
    push_request: OfflinePushRequest,
    current_user: User = Depends(get_current_user),
    service: OfflineSyncService = Depends(get_offline_sync_service),
):
    """
    ## Push Local Changes

    Upload changes made offline to the server.

    ### Features:
    - **Batch Processing**: Process multiple changes efficiently
    - **Dependency Resolution**: Automatically handle dependencies between records
    - **Conflict Detection**: Detect and handle conflicts with server data
    - **ID Mapping**: Map local IDs to server IDs

    ### Process:
    1. Sort changes by dependencies
    2. Process in batches
    3. Detect conflicts
    4. Apply conflict resolution strategy
    5. Return results with ID mapping

    ### Conflict Strategies:
    - `server_wins`: Server data takes precedence
    - `client_wins`: Client data overwrites server
    - `manual`: Return conflict for manual resolution
    - `merge`: Merge both versions (requires merged_data)
    - `newest_wins`: Most recent change wins

    ### Rate Limit:
    - 100 requests per minute

    ### Example Request:
    ```json
    {
      "device_id": "iphone-abc123",
      "changes": [
        {
          "local_id": "local_uuid_1",
          "action": "create",
          "model": "sale.order",
          "data": {
            "partner_id": 42,
            "order_line": []
          },
          "local_timestamp": "2025-11-24T10:30:00Z"
        }
      ],
      "conflict_strategy": "server_wins",
      "stop_on_error": false
    }
    ```
    """
    try:
        logger.info(
            f"Offline push: user={current_user.id}, "
            f"device={push_request.device_id}, "
            f"changes={len(push_request.changes)}"
        )

        result = await service.push_changes(
            user_id=current_user.id,
            push_request=push_request,
        )

        return result

    except Exception as e:
        logger.exception(f"Error in push_local_changes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to push changes: {str(e)}"
        )


# ===== PULL Endpoints =====

@router.post(
    "/pull",
    response_model=OfflinePullResponse,
    summary="Pull server changes",
    description="Download new changes from server since last sync"
)
@limiter.limit("200/minute")
async def pull_server_changes(
    request: Request,
    pull_request: OfflinePullRequest,
    current_user: User = Depends(get_current_user),
    service: OfflineSyncService = Depends(get_offline_sync_service),
):
    """
    ## Pull Server Changes

    Download changes from server that occurred since last sync.

    ### Features:
    - **Incremental Sync**: Only fetch new changes
    - **Model Filtering**: Filter by app type or specific models
    - **Priority Filtering**: Filter by change priority
    - **Pagination**: Handle large datasets
    - **Caching**: Fast response with Redis cache

    ### Process:
    1. Get last sync state
    2. Fetch new events from Odoo
    3. Filter by app type/models
    4. Return changes with next sync token

    ### App Types:
    - `sales_app`: sale.order, res.partner, product.product, etc.
    - `delivery_app`: stock.picking, stock.move, etc.
    - `warehouse_app`: stock.picking, stock.quant, etc.
    - `manager_app`: All major models
    - `crm_app`: crm.lead, calendar.event, etc.

    ### Rate Limit:
    - 200 requests per minute

    ### Example Request:
    ```json
    {
      "device_id": "iphone-abc123",
      "app_type": "sales_app",
      "last_event_id": 1250,
      "limit": 100,
      "include_payload": true
    }
    ```
    """
    try:
        logger.info(
            f"Offline pull: user={current_user.id}, "
            f"device={pull_request.device_id}, "
            f"last_event_id={pull_request.last_event_id}"
        )

        result = await service.pull_changes(
            user_id=current_user.id,
            pull_request=pull_request,
        )

        return result

    except Exception as e:
        logger.exception(f"Error in pull_server_changes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pull changes: {str(e)}"
        )


# ===== CONFLICT RESOLUTION Endpoints =====

@router.post(
    "/resolve-conflicts",
    response_model=ConflictResolutionResponse,
    summary="Resolve data conflicts",
    description="Manually or automatically resolve conflicts between local and server data"
)
@limiter.limit("50/minute")
async def resolve_conflicts(
    request: Request,
    resolution_request: ConflictResolutionRequest,
    current_user: User = Depends(get_current_user),
    service: OfflineSyncService = Depends(get_offline_sync_service),
):
    """
    ## Resolve Conflicts

    Resolve conflicts that occurred during push operation.

    ### Conflict Resolution Strategies:
    - **server_wins**: Keep server data, discard local changes
    - **client_wins**: Overwrite server with local data
    - **merge**: Merge both versions (requires merged_data)
    - **newest_wins**: Keep most recently modified version

    ### Process:
    1. Review conflicts from push response
    2. Choose resolution strategy for each
    3. Provide merged data if using merge strategy
    4. Submit resolutions
    5. Server applies resolutions

    ### Rate Limit:
    - 50 requests per minute

    ### Example Request:
    ```json
    {
      "device_id": "iphone-abc123",
      "conflicts": [...],
      "resolutions": [
        {
          "local_id": "local_uuid_1",
          "strategy": "client_wins"
        },
        {
          "local_id": "local_uuid_2",
          "strategy": "merge",
          "merged_data": {
            "name": "Merged Name",
            "email": "merged@example.com"
          }
        }
      ]
    }
    ```
    """
    try:
        logger.info(
            f"Resolve conflicts: user={current_user.id}, "
            f"device={resolution_request.device_id}, "
            f"conflicts={len(resolution_request.resolutions)}"
        )

        result = await service.resolve_conflicts(
            user_id=current_user.id,
            resolution_request=resolution_request,
        )

        return result

    except Exception as e:
        logger.exception(f"Error in resolve_conflicts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve conflicts: {str(e)}"
        )


# ===== SYNC STATE Endpoints =====

@router.get(
    "/state",
    response_model=SyncStateResponse,
    summary="Get sync state",
    description="Get current sync state for a device"
)
@limiter.limit("100/minute")
async def get_sync_state(
    request: Request,
    device_id: str = Query(..., description="Device ID"),
    current_user: User = Depends(get_current_user),
    service: OfflineSyncService = Depends(get_offline_sync_service),
):
    """
    ## Get Sync State

    Retrieve current synchronization state for a device.

    ### Information Returned:
    - Last synced event ID
    - Last sync timestamp
    - Total syncs performed
    - Sync status
    - Pending changes count
    - App type

    ### Rate Limit:
    - 100 requests per minute

    ### Example Response:
    ```json
    {
      "device_id": "iphone-abc123",
      "user_id": 1,
      "last_event_id": 1250,
      "last_sync_time": "2025-11-24T10:30:00Z",
      "next_sync_token": "1_iphone-abc123_1732451400",
      "total_syncs": 150,
      "total_events_synced": 3500,
      "sync_status": "idle",
      "pending_changes": 0,
      "app_type": "sales_app"
    }
    ```
    """
    try:
        result = await service.get_sync_state(
            user_id=current_user.id,
            device_id=device_id,
        )

        return result

    except Exception as e:
        logger.exception(f"Error in get_sync_state: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync state: {str(e)}"
        )


@router.post(
    "/reset",
    summary="Reset sync state",
    description="Reset sync state to force full sync"
)
@limiter.limit("10/hour")
async def reset_sync_state(
    request: Request,
    device_id: str = Query(..., description="Device ID"),
    current_user: User = Depends(get_current_user),
    service: OfflineSyncService = Depends(get_offline_sync_service),
):
    """
    ## Reset Sync State

    Reset synchronization state to force a full sync on next pull.

    ### When to Use:
    - First installation
    - After clearing app data
    - Database corruption
    - Sync errors
    - User requests "Refresh All"

    ### What Happens:
    - last_event_id reset to 0
    - sync_count reset to 0
    - Cache cleared
    - Next pull will fetch all data

    ### Rate Limit:
    - 10 requests per hour (to prevent abuse)

    ### Example Response:
    ```json
    {
      "success": true,
      "message": "Sync state reset successfully",
      "device_id": "iphone-abc123"
    }
    ```
    """
    try:
        result = await service.reset_sync_state(
            user_id=current_user.id,
            device_id=device_id,
        )

        return result

    except Exception as e:
        logger.exception(f"Error in reset_sync_state: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset sync state: {str(e)}"
        )


# ===== HEALTH CHECK =====

@router.get(
    "/health",
    summary="Health check",
    description="Check if offline sync service is operational"
)
async def health_check():
    """
    ## Health Check

    Simple health check endpoint for monitoring.

    ### Returns:
    - Service status
    - Version
    - Available features

    ### No authentication required
    """
    return {
        "status": "healthy",
        "service": "offline-sync",
        "version": "1.0.0",
        "features": [
            "push local changes",
            "pull server changes",
            "conflict resolution",
            "incremental sync",
            "dependency resolution",
            "batch processing",
            "model filtering",
            "priority filtering",
        ]
    }


# ===== STATISTICS Endpoint (Optional) =====

@router.get(
    "/statistics",
    summary="Get sync statistics",
    description="Get detailed sync statistics for a device"
)
@limiter.limit("50/minute")
async def get_sync_statistics(
    request: Request,
    device_id: str = Query(..., description="Device ID"),
    current_user: User = Depends(get_current_user),
):
    """
    ## Get Sync Statistics

    Retrieve detailed statistics about synchronization for a device.

    ### Information Returned:
    - Total syncs
    - Success/failure rates
    - Conflict rates
    - Performance metrics
    - Data volume

    ### Rate Limit:
    - 50 requests per minute
    """
    # TODO: Implement statistics gathering
    return {
        "device_id": device_id,
        "message": "Statistics endpoint coming soon"
    }
