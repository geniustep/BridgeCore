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
    CleanupResponse,
    RetryEventRequest,
    BulkRetryRequest,
    RetryResponse,
    DeadLetterQueueStats,
    EventStatistics,
    WebhookConfigOut
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
        "version": "2.0.0",  # Updated version
        "features": [
            "enhanced_filtering",
            "retry_mechanism",
            "dead_letter_queue",
            "statistics",
            "priority_support"
        ]
    }


# ===== New Enhanced Endpoints =====

@router.get(
    "/events/enhanced",
    response_model=EventsResponse,
    summary="List webhook events with enhanced filtering",
    description="Get webhook events with priority, category, status filtering"
)
@limiter.limit("200/minute")
async def list_events_enhanced(
    request: Request,
    model_name: Optional[str] = Query(None, description="Filter by model name"),
    record_id: Optional[int] = Query(None, description="Filter by specific record id"),
    event: Optional[str] = Query(None, description="create|write|unlink|manual"),
    since: Optional[str] = Query(None, description="ISO datetime to filter timestamp >= since"),
    priority: Optional[str] = Query(None, description="high|medium|low"),
    category: Optional[str] = Query(None, description="business|system|notification|custom"),
    status: Optional[str] = Query(None, description="pending|processing|sent|failed|dead"),
    limit: int = Query(100, ge=1, le=1000, description="Max events to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    service: WebhookService = Depends(get_webhook_service)
):
    """
    List webhook events with enhanced filtering

    Rate limited to 200 requests/minute per user
    """

    try:
        events = await service.get_events_enhanced(
            model_name=model_name,
            record_id=record_id,
            event=event,
            since=since,
            priority=priority,
            category=category,
            status=status,
            limit=limit,
            offset=offset
        )

        return EventsResponse(
            count=len(events),
            data=events
        )

    except OdooError as e:
        logger.error(f"Odoo error in list_events_enhanced: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Odoo error: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Error in list_events_enhanced: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(e)}"
        )


@router.post(
    "/retry",
    response_model=RetryResponse,
    summary="Retry failed event",
    description="Retry a single failed webhook event"
)
@limiter.limit("50/minute")
async def retry_event(
    request: Request,
    retry_request: RetryEventRequest,
    service: WebhookService = Depends(get_webhook_service)
):
    """
    Retry a failed webhook event

    Rate limited to 50 requests/minute per user
    """

    try:
        result = await service.retry_event(
            event_id=retry_request.event_id,
            force=retry_request.force
        )
        return result

    except Exception as e:
        logger.exception(f"Error in retry_event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(e)}"
        )


@router.post(
    "/retry/bulk",
    response_model=List[RetryResponse],
    summary="Bulk retry failed events",
    description="Retry multiple failed webhook events"
)
@limiter.limit("10/minute")
async def bulk_retry_events(
    request: Request,
    bulk_request: BulkRetryRequest,
    service: WebhookService = Depends(get_webhook_service)
):
    """
    Bulk retry failed webhook events

    Rate limited to 10 requests/minute per user
    Max 100 events per request
    """

    if len(bulk_request.event_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 events can be retried at once"
        )

    try:
        results = await service.bulk_retry_events(
            event_ids=bulk_request.event_ids,
            force=bulk_request.force
        )
        return results

    except Exception as e:
        logger.exception(f"Error in bulk_retry_events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(e)}"
        )


@router.get(
    "/dead-letter/stats",
    response_model=DeadLetterQueueStats,
    summary="Dead letter queue statistics",
    description="Get statistics about events in dead letter queue"
)
@limiter.limit("30/minute")
async def get_dead_letter_stats(
    request: Request,
    service: WebhookService = Depends(get_webhook_service)
):
    """
    Get dead letter queue statistics

    Rate limited to 30 requests/minute per user
    """

    try:
        stats = await service.get_dead_letter_queue_stats()
        return stats

    except OdooError as e:
        logger.error(f"Odoo error in get_dead_letter_stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Odoo error: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Error in get_dead_letter_stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(e)}"
        )


@router.get(
    "/statistics",
    response_model=EventStatistics,
    summary="Event statistics",
    description="Get comprehensive webhook event statistics"
)
@limiter.limit("20/minute")
async def get_statistics(
    request: Request,
    since: Optional[str] = Query(None, description="Get stats since this timestamp"),
    model_name: Optional[str] = Query(None, description="Filter by model"),
    service: WebhookService = Depends(get_webhook_service)
):
    """
    Get comprehensive event statistics

    Rate limited to 20 requests/minute per user
    """

    try:
        stats = await service.get_event_statistics(
            since=since,
            model_name=model_name
        )
        return stats

    except OdooError as e:
        logger.error(f"Odoo error in get_statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Odoo error: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Error in get_statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(e)}"
        )


@router.get(
    "/configs",
    response_model=List[WebhookConfigOut],
    summary="Get webhook configurations",
    description="Get all active webhook configurations"
)
@limiter.limit("30/minute")
async def get_webhook_configs(
    request: Request,
    service: WebhookService = Depends(get_webhook_service)
):
    """
    Get all active webhook configurations

    Rate limited to 30 requests/minute per user
    """

    try:
        configs = await service.get_webhook_configs()
        return configs

    except OdooError as e:
        logger.error(f"Odoo error in get_webhook_configs: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Odoo error: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Error in get_webhook_configs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(e)}"
        )
