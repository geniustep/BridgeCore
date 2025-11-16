"""
Webhook Router V2 - Smart Sync API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
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
from app.core.rate_limiter import limiter
from starlette.requests import Request


router = APIRouter(
    prefix="/api/v2/sync",
    tags=["smart-sync"]
)


# ===== Dependencies =====

def get_odoo_client(user = Depends(get_current_user)) -> OdooClient:
    """Get Odoo client with user's session"""
    session_id = getattr(user, 'session_id', None) or getattr(user, 'odoo_session_id', None)

    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Odoo session not found. Please login first."
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
