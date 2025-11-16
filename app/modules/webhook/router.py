"""
Webhook Router - REST API endpoints (v1)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
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
from app.db.session import get_db
from app.core.rate_limiter import limiter
from starlette.requests import Request


router = APIRouter(
    prefix="/api/v1/webhooks",
    tags=["webhooks"]
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
            detail=f"No active Odoo system found for user {user.id}. Please connect to Odoo first via /systems/odoo-{user.username}/connect"
        )
    
    # Get SystemService and check if adapter is connected
    service = get_system_service(db)
    system_id = system.system_id
    
    logger.debug(f"Getting Odoo client for system_id: {system_id}, user_id: {user.id}")
    
    # Check if adapter exists and is connected
    adapter = service.adapters.get(system_id)
    if not adapter or not adapter.is_connected:
        # Try to reconnect using stored config
        logger.info(f"Adapter not found or not connected for {system_id}, attempting to reconnect...")
        try:
            config = system.connection_config.copy() if system.connection_config else {}
            # Ensure URL is correct - remove /odoo if present (Odoo is at root)
            base_url = config.get("url", settings.ODOO_URL)
            if base_url:
                # Remove /odoo suffix if present
                if base_url.endswith("/odoo") or base_url.endswith("/odoo/"):
                    config["url"] = base_url.rstrip('/').replace('/odoo', '').rstrip('/')
                    logger.info(f"Fixed Odoo URL: {config['url']}")
                else:
                    config["url"] = base_url.rstrip('/')
            else:
                # Use default from settings
                default_url = settings.ODOO_URL.rstrip('/').replace('/odoo', '').rstrip('/')
                config["url"] = default_url
            
            adapter = await service.connect_system(
                system_id=system_id,
                system_type=system.system_type,
                config=config
            )
            logger.info(f"Successfully reconnected to {system_id}")
        except Exception as e:
            logger.error(f"Failed to reconnect to Odoo {system_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to connect to Odoo: {str(e)}. Please try connecting manually via /systems/{system_id}/connect"
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
                    error_msg = auth_result.get("error", "Unknown error")
                    logger.error(f"Authentication failed for {system_id}: {error_msg}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"Odoo authentication failed: {error_msg}. Please check credentials and try connecting via /systems/{system_id}/connect"
                    )
            else:
                logger.error(f"No credentials found in config for {system_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No credentials stored for system {system_id}. Please connect via /systems/{system_id}/connect"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during authentication: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Authentication error: {str(e)}. Please try connecting via /systems/{system_id}/connect"
            )
    
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Odoo session not found for system {system_id}. Please connect to Odoo first via /systems/{system_id}/connect"
        )

    logger.debug(f"Using session_id: {session_id[:20]}... for system {system_id}")

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
