"""
Webhook Service - Business logic for webhook operations
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger

from app.utils.odoo_client import OdooClient, OdooError
from app.services.cache_service import CacheService
from app.modules.webhook.schemas import (
    WebhookEventOut,
    EventData,
    SyncRequest,
    SyncResponse,
    SyncStatsResponse,
    CheckUpdatesOut,
    ModelCount
)


# App type to models mapping
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


class WebhookService:
    """Core webhook business logic"""

    def __init__(
        self,
        odoo_client: OdooClient,
        cache_service: CacheService
    ):
        self.odoo = odoo_client
        self.cache = cache_service

    async def get_events(
        self,
        model_name: Optional[str] = None,
        record_id: Optional[int] = None,
        event: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[WebhookEventOut]:
        """
        Get webhook events with filtering and caching

        Args:
            model_name: Filter by model name
            record_id: Filter by record ID
            event: Filter by event type (create/write/unlink)
            since: Filter by timestamp (ISO datetime string)
            limit: Max number of events to return
            offset: Offset for pagination

        Returns:
            List of webhook events
        """

        # Build cache key
        cache_key = f"webhook:events:{model_name}:{record_id}:{event}:{since}:{limit}:{offset}"

        # Try cache first
        try:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for events query: {cache_key}")
                return [WebhookEventOut(**event) for event in cached]
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")

        # Build domain for Odoo query
        domain = []
        if model_name:
            domain.append(["model", "=", model_name])
        if record_id is not None:
            domain.append(["record_id", "=", record_id])
        if event:
            domain.append(["event", "=", event])
        if since:
            domain.append(["timestamp", ">=", since])

        try:
            # Fetch from Odoo
            rows = self.odoo.search_read(
                "update.webhook",
                domain=domain,
                fields=["id", "model", "record_id", "event", "timestamp"],
                limit=limit,
                offset=offset,
                order="timestamp desc"
            )

            # Transform to Pydantic models
            events = [
                WebhookEventOut(
                    id=r["id"],
                    model=r.get("model", ""),
                    record_id=r.get("record_id", 0),
                    event=r.get("event", "manual"),
                    occurred_at=r.get("timestamp", "")
                )
                for r in rows
            ]

            # Cache for 60 seconds
            try:
                await self.cache.set(
                    cache_key,
                    [event.dict() for event in events],
                    ttl=60
                )
            except Exception as e:
                logger.warning(f"Cache storage failed: {e}")

            logger.info(f"Retrieved {len(events)} webhook events")
            return events

        except OdooError as e:
            logger.error(f"Odoo error while fetching events: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while fetching events: {e}")
            raise

    async def smart_sync(
        self,
        sync_request: SyncRequest
    ) -> SyncResponse:
        """
        Smart sync for multi-user apps
        Returns only new events since last sync for this user/device

        Args:
            sync_request: Sync request with user_id, device_id, app_type

        Returns:
            SyncResponse with new events and updated sync token
        """

        try:
            # Get or create sync state for this user/device
            logger.debug(
                f"Smart sync for user={sync_request.user_id}, "
                f"device={sync_request.device_id}, app={sync_request.app_type}"
            )

            sync_state = self.odoo.call_kw(
                "user.sync.state",
                "get_or_create_state",
                [
                    sync_request.user_id,
                    sync_request.device_id,
                    sync_request.app_type
                ]
            )

            last_event_id = sync_state.get("last_event_id", 0)
            last_sync_time = sync_state.get("last_sync_time", "")

            # Build domain for new events
            domain = [
                ("id", ">", last_event_id),
                ("is_archived", "=", False)
            ]

            # Filter by app type models
            app_models = APP_TYPE_MODELS.get(sync_request.app_type, [])
            if app_models:
                domain.append(("model", "in", app_models))

            # Additional user-defined filter
            if sync_request.models_filter:
                domain.append(("model", "in", sync_request.models_filter))

            # Fetch new events
            events = self.odoo.search_read(
                "update.webhook",
                domain=domain,
                fields=["id", "model", "record_id", "event", "timestamp"],
                limit=sync_request.limit,
                order="id asc"  # Oldest first for proper sync
            )

            if not events:
                logger.info(f"No new events for user {sync_request.user_id}")
                return SyncResponse(
                    has_updates=False,
                    new_events_count=0,
                    events=[],
                    next_sync_token=str(last_event_id),
                    last_sync_time=last_sync_time
                )

            # Update user sync state
            new_last_event_id = events[-1]["id"]

            self.odoo.call_kw(
                "user.sync.state",
                "write",
                [[sync_state["id"]], {
                    "last_event_id": new_last_event_id,
                    "last_sync_time": datetime.utcnow().isoformat(),
                    "sync_count": sync_state.get("sync_count", 0) + 1
                }]
            )

            # Mark events as synced by this user (optional, for analytics)
            for event in events:
                try:
                    self.odoo.call_kw(
                        "update.webhook",
                        "mark_as_synced_by_user",
                        [[event["id"]], sync_request.user_id]
                    )
                except Exception as e:
                    # Non-critical, just log
                    logger.warning(
                        f"Could not mark event {event['id']} as synced: {e}"
                    )

            # Transform events
            event_data = [
                EventData(
                    id=e["id"],
                    model=e.get("model", ""),
                    record_id=e.get("record_id", 0),
                    event=e.get("event", ""),
                    timestamp=e.get("timestamp", "")
                )
                for e in events
            ]

            logger.info(
                f"Smart sync complete: {len(events)} new events for user {sync_request.user_id}"
            )

            return SyncResponse(
                has_updates=True,
                new_events_count=len(events),
                events=event_data,
                next_sync_token=str(new_last_event_id),
                last_sync_time=last_sync_time
            )

        except OdooError as e:
            logger.error(f"Odoo error during smart sync: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during smart sync: {e}")
            raise

    async def get_sync_state(
        self,
        user_id: int,
        device_id: str
    ) -> SyncStatsResponse:
        """Get current sync state for a user/device"""

        try:
            states = self.odoo.search_read(
                "user.sync.state",
                domain=[
                    ("user_id", "=", user_id),
                    ("device_id", "=", device_id)
                ],
                fields=[
                    "user_id", "device_id", "last_event_id",
                    "last_sync_time", "sync_count", "is_active"
                ],
                limit=1
            )

            if not states:
                raise ValueError("Sync state not found")

            state = states[0]
            return SyncStatsResponse(
                user_id=state.get("user_id")[0] if isinstance(state.get("user_id"), list) else state.get("user_id"),
                device_id=state.get("device_id", ""),
                last_event_id=state.get("last_event_id", 0),
                last_sync_time=state.get("last_sync_time", ""),
                sync_count=state.get("sync_count", 0),
                is_active=state.get("is_active", False)
            )

        except OdooError as e:
            logger.error(f"Odoo error getting sync state: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting sync state: {e}")
            raise

    async def reset_sync_state(
        self,
        user_id: int,
        device_id: str
    ) -> Dict[str, str]:
        """Reset sync state for a user/device"""

        try:
            states = self.odoo.search(
                "user.sync.state",
                domain=[
                    ("user_id", "=", user_id),
                    ("device_id", "=", device_id)
                ]
            )

            if not states:
                raise ValueError("Sync state not found")

            self.odoo.write("user.sync.state", states, {
                "last_event_id": 0,
                "sync_count": 0
            })

            logger.info(f"Reset sync state for user {user_id}, device {device_id}")
            return {"status": "success", "message": "Sync state reset successfully"}

        except OdooError as e:
            logger.error(f"Odoo error resetting sync state: {e}")
            raise
        except Exception as e:
            logger.error(f"Error resetting sync state: {e}")
            raise

    async def check_updates(
        self,
        since: Optional[str] = None,
        limit: int = 200
    ) -> CheckUpdatesOut:
        """
        Check for updates since a timestamp
        Returns lightweight summary grouped by model
        """

        try:
            data = self.odoo.get_updates_summary(limit=limit, since=since)

            last_at = data.get("last_update_at")
            summary = [ModelCount(**s) for s in data.get("summary", [])]

            return CheckUpdatesOut(
                has_update=bool(summary),
                last_update_at=last_at,
                summary=summary
            )

        except OdooError as e:
            logger.error(f"Odoo error checking updates: {e}")
            raise
        except Exception as e:
            logger.error(f"Error checking updates: {e}")
            raise

    async def cleanup_events(
        self,
        before: Optional[str] = None
    ) -> int:
        """
        Cleanup webhook events older than a given timestamp

        Args:
            before: ISO datetime string - delete events before this time

        Returns:
            Number of deleted events
        """

        try:
            deleted = self.odoo.cleanup_updates(before=before)
            logger.info(f"Cleaned up {deleted} webhook events")
            return deleted

        except OdooError as e:
            logger.error(f"Odoo error during cleanup: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            raise
