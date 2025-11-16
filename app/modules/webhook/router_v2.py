"""
Webhook Router V2 - Smart Sync API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.modules.webhook.service import WebhookService
from app.modules.webhook.schemas import (
    SyncRequest,
    SyncResponse,
    SyncStatsResponse
)
from app.services.cache_service import CacheService
from app.utils.odoo_client import OdooClient, OdooError
from app.core.config import settings
from app.core.dependencies import get_current_user, get_cache_service
from app.db.session import get_db
from app.core.rate_limiter import limiter
from starlette.requests import Request


router = APIRouter(
    prefix="/api/v2/sync",
    tags=["smart-sync"]
)


# ===== Dependencies =====

async def get_odoo_client(
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> OdooClient:
    """Get Odoo client with user's session"""
    from app.models.system import System
    from sqlalchemy import select
    from app.api.routes.systems import get_system_service
    
    # Get user's active Odoo system (prefer most recently updated)
    query = select(System).where(
        System.user_id == user.id,
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
    
    # Get SystemService and check if adapter is connected
    service = get_system_service(db)
    system_id = system.system_id
    
    # Check if adapter exists and is connected
    adapter = service.adapters.get(system_id)
    if not adapter or not adapter.is_connected:
        # Try to reconnect using stored config
        try:
            config = system.connection_config
            adapter = await service.connect_system(
                system_id=system_id,
                system_type=system.system_type,
                config=config
            )
        except Exception as e:
            logger.error(f"Failed to connect to Odoo: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to connect to Odoo: {str(e)}"
            )
    
    # Get session_id from adapter
    session_id = getattr(adapter, 'session_id', None)
    
    # If no session_id, try to authenticate
    if not session_id:
        logger.warning(f"No session_id found for {system_id}, attempting to authenticate...")
        try:
            config = system.connection_config
            username = config.get("username")
            password = config.get("password")
            
            if username and password:
                auth_result = await adapter.authenticate(username, password)
                if auth_result.get("success"):
                    session_id = auth_result.get("session_id")
                    logger.info(f"Successfully authenticated and obtained session_id for {system_id}")
                else:
                    logger.error(f"Authentication failed: {auth_result.get('error')}")
            else:
                logger.error(f"No credentials found in config for {system_id}")
        except Exception as e:
            logger.error(f"Error during authentication: {str(e)}")
    
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Odoo session not found. Please connect to Odoo first via /systems/{system_id}/connect"
        )

    return OdooClient(
        base_url=settings.ODOO_URL,
        session_id=session_id,
        timeout=15,
        retries=2,
        backoff=0.3,
        user_agent="BridgeCore-SmartSync/2.0"
    )


async def get_webhook_service(
    odoo_client: OdooClient = Depends(get_odoo_client),
    cache_service: CacheService = Depends(get_cache_service)
) -> WebhookService:
    """Get webhook service instance"""
    return WebhookService(odoo_client, cache_service)


# ===== Routes =====

@router.post(
    "/pull",
    response_model=SyncResponse,
    summary="Smart sync pull",
    description="Pull only new changes since last sync for this user/device"
)
@limiter.limit("200/minute")
async def sync_pull(
    request: Request,
    sync_request: SyncRequest,
    service: WebhookService = Depends(get_webhook_service)
):
    """
    Smart sync - pulls only what the user needs based on their last sync state

    This endpoint:
    - Tracks sync state per user/device
    - Returns only NEW events since last sync
    - Filters by app type (sales_app, delivery_app, etc.)
    - Updates sync state automatically

    Rate limited to 200 requests/minute per user
    """

    try:
        logger.info(
            f"Smart sync pull: user={sync_request.user_id}, "
            f"device={sync_request.device_id}, app={sync_request.app_type}"
        )

        result = await service.smart_sync(sync_request)
        return result

    except OdooError as e:
        logger.error(f"Odoo error in sync_pull: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Odoo error: {str(e)}"
        )
    except ValueError as e:
        logger.error(f"Validation error in sync_pull: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error in sync_pull: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(e)}"
        )


@router.get(
    "/state",
    response_model=SyncStatsResponse,
    summary="Get sync state",
    description="Get current sync state for a user/device"
)
@limiter.limit("100/minute")
async def get_sync_state(
    request: Request,
    user_id: int = Query(..., description="User ID"),
    device_id: str = Query(..., description="Device ID"),
    service: WebhookService = Depends(get_webhook_service)
):
    """
    Get current sync state for a user/device

    Returns information about:
    - Last synced event ID
    - Last sync timestamp
    - Total sync count
    - Sync status

    Rate limited to 100 requests/minute per user
    """

    try:
        result = await service.get_sync_state(user_id, device_id)
        return result

    except ValueError as e:
        logger.error(f"Sync state not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except OdooError as e:
        logger.error(f"Odoo error in get_sync_state: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Odoo error: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Error in get_sync_state: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(e)}"
        )


@router.post(
    "/reset",
    summary="Reset sync state",
    description="Reset sync state for a user/device (useful for troubleshooting)"
)
@limiter.limit("10/hour")
async def reset_sync_state(
    request: Request,
    user_id: int = Query(..., description="User ID"),
    device_id: str = Query(..., description="Device ID"),
    service: WebhookService = Depends(get_webhook_service)
):
    """
    Reset sync state for a user/device

    This will:
    - Reset last_event_id to 0
    - Reset sync_count to 0
    - Force full sync on next pull

    Use this for troubleshooting sync issues.

    Rate limited to 10 requests/hour per user
    """

    try:
        result = await service.reset_sync_state(user_id, device_id)
        return result

    except ValueError as e:
        logger.error(f"Sync state not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except OdooError as e:
        logger.error(f"Odoo error in reset_sync_state: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Odoo error: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Error in reset_sync_state: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(e)}"
        )


@router.get(
    "/health",
    summary="Smart sync health check",
    description="Check if smart sync service is operational"
)
async def smart_sync_health():
    """Health check endpoint for smart sync service"""
    return {
        "status": "healthy",
        "service": "smart-sync",
        "version": "2.0.0",
        "features": [
            "multi-user sync",
            "per-device tracking",
            "app-type filtering",
            "incremental sync"
        ]
    }
