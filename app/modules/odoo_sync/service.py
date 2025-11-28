# -*- coding: utf-8 -*-
"""
Odoo Sync Service - Direct integration with auto-webhook-odoo

This service provides:
1. Pull events from Odoo's update.webhook table
2. Acknowledge processed events
3. Manage user sync states
4. Health checks and statistics
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger
import httpx

from app.core.config import settings
from app.services.cache_service import CacheService
from app.modules.odoo_sync.schemas import (
    OdooEvent,
    OdooPullResponse,
    OdooAckResponse,
    SyncStateResponse,
    SyncStatisticsResponse,
    OdooHealthResponse,
    OdooStatsResponse,
    Priority,
    AppType
)


# App type to models mapping (same as in webhook service)
APP_TYPE_MODELS = {
    "sales_app": [
        "sale.order",
        "sale.order.line",
        "res.partner",
        "product.template",
        "product.product",
        "product.category",
    ],
    "delivery_app": [
        "stock.picking",
        "stock.move",
        "stock.move.line",
        "res.partner",
    ],
    "warehouse_app": [
        "stock.picking",
        "stock.move",
        "stock.move.line",
        "stock.quant",
        "product.product",
        "stock.location",
    ],
    "manager_app": [
        "sale.order",
        "purchase.order",
        "account.move",
        "res.partner",
        "hr.expense",
        "project.project",
    ],
    "mobile_app": [
        "sale.order",
        "res.partner",
        "product.template",
        "product.product",
    ],
}


class OdooSyncService:
    """
    Service for syncing with Odoo's auto-webhook-odoo module
    
    This service connects directly to Odoo's webhook API to:
    - Pull events from update.webhook
    - Mark events as processed
    - Manage user/device sync states
    """

    def __init__(
        self,
        odoo_url: str,
        api_key: str,
        cache_service: Optional[CacheService] = None,
        timeout: int = 30
    ):
        """
        Initialize Odoo Sync Service
        
        Args:
            odoo_url: Base URL for Odoo (e.g., https://odoo.example.com)
            api_key: API key for authentication with auto-webhook-odoo
            cache_service: Optional cache service for caching
            timeout: HTTP request timeout in seconds
        """
        self.odoo_url = odoo_url.rstrip('/')
        self.api_key = api_key
        self.cache = cache_service
        self.timeout = timeout
        self._last_pull_time: Optional[datetime] = None
        
        # HTTP client with default headers
        self._headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Odoo webhook API
        
        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint (e.g., /api/webhooks/pull)
            params: Query parameters
            json_data: JSON body data
            
        Returns:
            Response JSON data
        """
        url = f"{self.odoo_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self._headers,
                    params=params,
                    json=json_data
                )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException as e:
            logger.error(f"Timeout connecting to Odoo: {url}")
            raise ConnectionError(f"Timeout connecting to Odoo: {e}")
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Odoo: {e.response.status_code} - {e.response.text}")
            raise ConnectionError(f"HTTP error from Odoo: {e.response.status_code}")
            
        except Exception as e:
            logger.error(f"Error connecting to Odoo: {e}")
            raise ConnectionError(f"Error connecting to Odoo: {e}")

    # ================================================================
    # Pull Events
    # ================================================================

    async def pull_events(
        self,
        last_event_id: int = 0,
        limit: int = 100,
        models: Optional[List[str]] = None,
        priority: Optional[str] = None,
        app_type: Optional[str] = None
    ) -> OdooPullResponse:
        """
        Pull events from Odoo's update.webhook table
        
        Args:
            last_event_id: Last event ID that was pulled
            limit: Maximum number of events to return
            models: List of model names to filter
            priority: Priority filter (high/medium/low)
            app_type: App type for automatic model filtering
            
        Returns:
            OdooPullResponse with events and metadata
        """
        try:
            # If app_type provided, use its models
            if app_type and not models:
                models = APP_TYPE_MODELS.get(app_type, [])
            
            # Build request body
            request_data = {
                "last_event_id": last_event_id,
                "limit": min(limit, 1000)
            }
            
            if models:
                request_data["models"] = models
            if priority:
                request_data["priority"] = priority
            
            logger.info(f"Pulling events from Odoo: last_id={last_event_id}, limit={limit}")
            
            # Make request to Odoo
            result = await self._make_request(
                method="POST",
                endpoint="/api/webhooks/pull",
                json_data=request_data
            )
            
            self._last_pull_time = datetime.now()
            
            # Parse events
            events = []
            for event_data in result.get("events", []):
                events.append(OdooEvent(
                    id=event_data["id"],
                    model=event_data["model"],
                    record_id=event_data["record_id"],
                    event=event_data["event"],
                    timestamp=datetime.fromisoformat(event_data["timestamp"]) if event_data.get("timestamp") else None,
                    payload=event_data.get("payload"),
                    priority=event_data.get("priority"),
                    category=event_data.get("category"),
                    user_id=event_data.get("user_id"),
                    user_name=event_data.get("user_name")
                ))
            
            logger.info(f"Pulled {len(events)} events from Odoo, has_more={result.get('has_more')}")
            
            return OdooPullResponse(
                success=True,
                events=events,
                last_id=result.get("last_id", last_event_id),
                has_more=result.get("has_more", False),
                count=len(events),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to pull events from Odoo: {e}")
            return OdooPullResponse(
                success=False,
                events=[],
                last_id=last_event_id,
                has_more=False,
                count=0,
                timestamp=datetime.now()
            )

    # ================================================================
    # Acknowledge Events
    # ================================================================

    async def acknowledge_events(self, event_ids: List[int]) -> OdooAckResponse:
        """
        Mark events as processed in Odoo
        
        Args:
            event_ids: List of event IDs to mark as processed
            
        Returns:
            OdooAckResponse with result
        """
        try:
            if not event_ids:
                return OdooAckResponse(
                    success=True,
                    processed_count=0,
                    message="No events to acknowledge"
                )
            
            logger.info(f"Acknowledging {len(event_ids)} events in Odoo")
            
            result = await self._make_request(
                method="POST",
                endpoint="/api/webhooks/mark-processed",
                json_data={"event_ids": event_ids}
            )
            
            return OdooAckResponse(
                success=result.get("success", True),
                processed_count=result.get("processed_count", len(event_ids)),
                message=result.get("message", f"{len(event_ids)} events acknowledged"),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to acknowledge events in Odoo: {e}")
            return OdooAckResponse(
                success=False,
                processed_count=0,
                message=str(e),
                timestamp=datetime.now()
            )

    # ================================================================
    # Sync State Management
    # ================================================================

    async def get_sync_state(
        self,
        user_id: int,
        device_id: str,
        app_type: str = "mobile_app"
    ) -> Optional[SyncStateResponse]:
        """
        Get or create sync state for a user/device
        
        Args:
            user_id: User ID
            device_id: Device unique identifier
            app_type: Application type
            
        Returns:
            SyncStateResponse or None if failed
        """
        try:
            logger.info(f"Getting sync state: user={user_id}, device={device_id}")
            
            result = await self._make_request(
                method="POST",
                endpoint="/api/webhooks/sync-state",
                json_data={
                    "user_id": user_id,
                    "device_id": device_id,
                    "app_type": app_type
                }
            )
            
            sync_state = result.get("sync_state", {})
            
            return SyncStateResponse(
                id=sync_state.get("id", 0),
                user_id=sync_state.get("user_id", user_id),
                device_id=sync_state.get("device_id", device_id),
                app_type=sync_state.get("app_type", app_type),
                last_event_id=sync_state.get("last_event_id", 0),
                last_sync_time=datetime.fromisoformat(sync_state["last_sync_time"]) if sync_state.get("last_sync_time") else None,
                sync_count=sync_state.get("sync_count", 0),
                total_events_synced=sync_state.get("total_events_synced", 0),
                is_active=sync_state.get("is_active", True)
            )
            
        except Exception as e:
            logger.error(f"Failed to get sync state from Odoo: {e}")
            return None

    async def update_sync_state(
        self,
        user_id: int,
        device_id: str,
        last_event_id: int,
        events_synced: int = 0
    ) -> Optional[SyncStateResponse]:
        """
        Update sync state after pulling events
        
        Args:
            user_id: User ID
            device_id: Device unique identifier
            last_event_id: Last event ID synced
            events_synced: Number of events synced
            
        Returns:
            Updated SyncStateResponse or None if failed
        """
        try:
            logger.info(
                f"Updating sync state: user={user_id}, device={device_id}, "
                f"last_event={last_event_id}, synced={events_synced}"
            )
            
            result = await self._make_request(
                method="POST",
                endpoint="/api/webhooks/sync-state/update",
                json_data={
                    "user_id": user_id,
                    "device_id": device_id,
                    "last_event_id": last_event_id,
                    "events_synced": events_synced
                }
            )
            
            sync_state = result.get("sync_state", {})
            
            return SyncStateResponse(
                id=sync_state.get("id", 0),
                user_id=sync_state.get("user_id", user_id),
                device_id=sync_state.get("device_id", device_id),
                app_type=sync_state.get("app_type", "mobile_app"),
                last_event_id=sync_state.get("last_event_id", last_event_id),
                last_sync_time=datetime.fromisoformat(sync_state["last_sync_time"]) if sync_state.get("last_sync_time") else None,
                sync_count=sync_state.get("sync_count", 0),
                total_events_synced=sync_state.get("total_events_synced", 0),
                is_active=sync_state.get("is_active", True)
            )
            
        except Exception as e:
            logger.error(f"Failed to update sync state in Odoo: {e}")
            return None

    async def get_sync_statistics(
        self,
        user_id: int,
        device_id: Optional[str] = None,
        app_type: Optional[str] = None
    ) -> SyncStatisticsResponse:
        """
        Get sync statistics for a user
        
        Args:
            user_id: User ID
            device_id: Optional device ID filter
            app_type: Optional app type filter
            
        Returns:
            SyncStatisticsResponse with stats
        """
        try:
            params = {"user_id": str(user_id)}
            if device_id:
                params["device_id"] = device_id
            if app_type:
                params["app_type"] = app_type
            
            result = await self._make_request(
                method="GET",
                endpoint="/api/webhooks/sync-state/stats",
                params=params
            )
            
            return SyncStatisticsResponse(
                success=result.get("success", True),
                stats=result.get("stats", {}),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to get sync statistics from Odoo: {e}")
            return SyncStatisticsResponse(
                success=False,
                stats={"error": str(e)},
                timestamp=datetime.now()
            )

    # ================================================================
    # Health & Statistics
    # ================================================================

    async def health_check(self) -> OdooHealthResponse:
        """
        Check Odoo webhook API health
        
        Returns:
            OdooHealthResponse with health status
        """
        try:
            result = await self._make_request(
                method="GET",
                endpoint="/api/webhooks/health"
            )
            
            return OdooHealthResponse(
                status=result.get("status", "healthy"),
                odoo_connected=True,
                pending_events=result.get("pending_events", 0),
                last_pull_time=self._last_pull_time,
                version=result.get("version", "2.0.0"),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Odoo health check failed: {e}")
            return OdooHealthResponse(
                status="unhealthy",
                odoo_connected=False,
                pending_events=0,
                last_pull_time=self._last_pull_time,
                version="unknown",
                timestamp=datetime.now()
            )

    async def get_statistics(self, days: int = 7) -> OdooStatsResponse:
        """
        Get webhook statistics from Odoo
        
        Args:
            days: Number of days to look back
            
        Returns:
            OdooStatsResponse with statistics
        """
        try:
            result = await self._make_request(
                method="GET",
                endpoint="/api/webhooks/stats",
                params={"days": str(days)}
            )
            
            return OdooStatsResponse(
                success=result.get("success", True),
                stats=result.get("stats", {}),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to get statistics from Odoo: {e}")
            return OdooStatsResponse(
                success=False,
                stats={"error": str(e)},
                timestamp=datetime.now()
            )

    # ================================================================
    # Combined Operations
    # ================================================================

    async def smart_pull(
        self,
        user_id: int,
        device_id: str,
        app_type: str = "mobile_app",
        limit: int = 100,
        auto_ack: bool = True
    ) -> Dict[str, Any]:
        """
        Smart pull: Get sync state, pull new events, update state
        
        This is a convenience method that:
        1. Gets the user's sync state to find last_event_id
        2. Pulls new events since last_event_id
        3. Optionally acknowledges the events
        4. Updates the sync state
        
        Args:
            user_id: User ID
            device_id: Device ID
            app_type: Application type
            limit: Max events to pull
            auto_ack: Whether to auto-acknowledge events
            
        Returns:
            Dict with events and sync state
        """
        try:
            # Step 1: Get sync state
            sync_state = await self.get_sync_state(user_id, device_id, app_type)
            last_event_id = sync_state.last_event_id if sync_state else 0
            
            # Step 2: Pull events
            pull_result = await self.pull_events(
                last_event_id=last_event_id,
                limit=limit,
                app_type=app_type
            )
            
            if not pull_result.success or pull_result.count == 0:
                return {
                    "success": pull_result.success,
                    "events": [],
                    "count": 0,
                    "has_more": False,
                    "sync_state": sync_state.dict() if sync_state else None
                }
            
            # Step 3: Acknowledge events
            if auto_ack and pull_result.events:
                event_ids = [e.id for e in pull_result.events]
                await self.acknowledge_events(event_ids)
            
            # Step 4: Update sync state
            new_sync_state = await self.update_sync_state(
                user_id=user_id,
                device_id=device_id,
                last_event_id=pull_result.last_id,
                events_synced=pull_result.count
            )
            
            return {
                "success": True,
                "events": [e.dict() for e in pull_result.events],
                "count": pull_result.count,
                "has_more": pull_result.has_more,
                "last_id": pull_result.last_id,
                "sync_state": new_sync_state.dict() if new_sync_state else None
            }
            
        except Exception as e:
            logger.error(f"Smart pull failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "events": [],
                "count": 0
            }

