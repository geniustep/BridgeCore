"""
Webhook Router - REST API endpoints (v1)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from loguru import logger

from app.modules.webhook.service import WebhookService
from app.modules.webhook.schemas import (
    EventsResponse,
    WebhookEventOut,
    CheckUpdatesOut,
    CleanupResponse
)
from app.services.cache_service import CacheService
from app.utils.odoo_client import OdooClient, OdooError
from app.core.config import settings
from app.core.dependencies import get_current_user, get_cache_service
from app.core.rate_limiter import limiter
from starlette.requests import Request


router = APIRouter(
    prefix="/api/v1/webhooks",
    tags=["webhooks"]
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
        user_agent="BridgeCore-Webhook/1.0"
    )


async def get_webhook_service(
    odoo_client: OdooClient = Depends(get_odoo_client),
    cache_service: CacheService = Depends(get_cache_service)
) -> WebhookService:
    """Get webhook service instance"""
    return WebhookService(odoo_client, cache_service)


# ===== Routes =====

@router.get(
    "/events",
    response_model=EventsResponse,
    summary="List webhook events",
    description="Get webhook events with optional filtering by model, record, event type, and timestamp"
)
@limiter.limit("100/minute")
async def list_events(
    request: Request,
    model_name: Optional[str] = Query(None, description="Filter by model name"),
    record_id: Optional[int] = Query(None, description="Filter by specific record id"),
    event: Optional[str] = Query(None, description="create|write|unlink|manual"),
    since: Optional[str] = Query(None, description="ISO datetime to filter timestamp >= since"),
    limit: int = Query(100, ge=1, le=1000, description="Max events to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    service: WebhookService = Depends(get_webhook_service)
):
    """
    List webhook events with filtering and pagination

    Rate limited to 100 requests/minute per user
    """

    try:
        events = await service.get_events(
            model_name=model_name,
            record_id=record_id,
            event=event,
            since=since,
            limit=limit,
            offset=offset
        )

        return EventsResponse(
            count=len(events),
            data=events
        )

    except OdooError as e:
        logger.error(f"Odoo error in list_events: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Odoo error: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Error in list_events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(e)}"
        )


@router.get(
    "/check-updates",
    response_model=CheckUpdatesOut,
    summary="Check for updates",
    description="Get a lightweight summary of updates since a timestamp"
)
@limiter.limit("50/minute")
async def check_updates(
    request: Request,
    since: Optional[str] = Query(None, description="ISO datetime: return updates >= since"),
    limit: int = Query(200, ge=1, le=1000, description="Max events to check"),
    service: WebhookService = Depends(get_webhook_service)
):
    """
    Returns a lightweight summary of webhook updates

    Rate limited to 50 requests/minute per user
    """

    try:
        result = await service.check_updates(since=since, limit=limit)
        return result

    except OdooError as e:
        logger.error(f"Odoo error in check_updates: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Odoo error: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Error in check_updates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(e)}"
        )


@router.delete(
    "/cleanup",
    response_model=CleanupResponse,
    summary="Cleanup old events",
    description="Delete webhook events older than a given timestamp"
)
@limiter.limit("10/hour")
async def cleanup_events(
    request: Request,
    before: Optional[str] = Query(None, description="Delete events occurred_at <= before (ISO datetime)"),
    service: WebhookService = Depends(get_webhook_service)
):
    """
    Cleanup old webhook events

    Rate limited to 10 requests/hour per user
    Requires admin privileges
    """

    try:
        deleted = await service.cleanup_events(before=before)

        return CleanupResponse(
            ok=True,
            deleted=deleted,
            message=f"Successfully deleted {deleted} events"
        )

    except OdooError as e:
        logger.error(f"Odoo error in cleanup_events: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Odoo error: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Error in cleanup_events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(e)}"
        )


@router.get(
    "/health",
    summary="Webhook service health check",
    description="Check if webhook service is operational"
)
async def webhook_health():
    """Health check endpoint for webhook service"""
    return {
        "status": "healthy",
        "service": "webhook",
        "version": "1.0.0"
    }
