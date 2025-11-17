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
    ModelCount,
    RetryResponse,
    DeadLetterQueueStats,
    EventStatistics,
    WebhookConfigOut
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
            # Fetch from Odoo (OdooClient is sync, but we're in async context)
            # Run in thread pool to avoid blocking
            import asyncio
            loop = asyncio.get_event_loop()
            rows = await loop.run_in_executor(
                None,
                lambda: self.odoo.search_read(
                    "update.webhook",
                    domain=domain,
                    fields=["id", "model", "record_id", "event", "timestamp"],
                    limit=limit,
                    offset=offset,
                    order="timestamp desc"
                )
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

            # Get sync state (run sync call in executor)
            import asyncio
            loop = asyncio.get_event_loop()
            sync_state = await loop.run_in_executor(
                None,
                lambda: self.odoo.call_kw(
                    "user.sync.state",
                    "get_or_create_state",
                    [
                        sync_request.user_id,
                        sync_request.device_id,
                        sync_request.app_type
                    ]
                )
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

            # Fetch new events (OdooClient is sync, run in executor)
            import asyncio
            loop = asyncio.get_event_loop()
            events = await loop.run_in_executor(
                None,
                lambda: self.odoo.search_read(
                    "update.webhook",
                    domain=domain,
                    fields=["id", "model", "record_id", "event", "timestamp"],
                    limit=sync_request.limit,
                    order="id asc"  # Oldest first for proper sync
                )
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

            await loop.run_in_executor(
                None,
                lambda: self.odoo.call_kw(
                    "user.sync.state",
                    "write",
                    [[sync_state["id"]], {
                        "last_event_id": new_last_event_id,
                        "last_sync_time": datetime.utcnow().isoformat(),
                        "sync_count": sync_state.get("sync_count", 0) + 1
                    }]
                )
            )

            # Mark events as synced by this user (optional, for analytics)
            for event in events:
                try:
                    await loop.run_in_executor(
                        None,
                        lambda e=event: self.odoo.call_kw(
                            "update.webhook",
                            "mark_as_synced_by_user",
                            [[e["id"]], sync_request.user_id]
                        )
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
            import asyncio
            loop = asyncio.get_event_loop()
            states = await loop.run_in_executor(
                None,
                lambda: self.odoo.search_read(
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
            import asyncio
            loop = asyncio.get_event_loop()
            states = await loop.run_in_executor(
                None,
                lambda: self.odoo.search(
                    "user.sync.state",
                    domain=[
                        ("user_id", "=", user_id),
                        ("device_id", "=", device_id)
                    ]
                )
            )

            if not states:
                raise ValueError("Sync state not found")

            await loop.run_in_executor(
                None,
                lambda: self.odoo.write("user.sync.state", states, {
                    "last_event_id": 0,
                    "sync_count": 0
                })
            )

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
            import asyncio
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None,
                lambda: self.odoo.get_updates_summary(limit=limit, since=since)
            )

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
            import asyncio
            loop = asyncio.get_event_loop()
            deleted = await loop.run_in_executor(
                None,
                lambda: self.odoo.cleanup_updates(before=before)
            )
            logger.info(f"Cleaned up {deleted} webhook events")
            return deleted

        except OdooError as e:
            logger.error(f"Odoo error during cleanup: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            raise

    # ===== New Methods for Enhanced Features =====

    async def get_events_enhanced(
        self,
        model_name: Optional[str] = None,
        record_id: Optional[int] = None,
        event: Optional[str] = None,
        since: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[WebhookEventOut]:
        """
        Get webhook events with enhanced filtering including new fields

        Args:
            model_name: Filter by model name
            record_id: Filter by record ID
            event: Filter by event type
            since: Filter by timestamp
            priority: Filter by priority (high/medium/low)
            category: Filter by category (business/system/notification/custom)
            status: Filter by status (pending/processing/sent/failed/dead)
            limit: Max number of events
            offset: Pagination offset

        Returns:
            List of webhook events with full details
        """

        # Build cache key with new filters
        cache_key = f"webhook:events:v2:{model_name}:{record_id}:{event}:{since}:{priority}:{category}:{status}:{limit}:{offset}"

        # Try cache
        try:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for enhanced events query")
                return [WebhookEventOut(**event) for event in cached]
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")

        # Build domain
        domain = []
        if model_name:
            domain.append(["model", "=", model_name])
        if record_id is not None:
            domain.append(["record_id", "=", record_id])
        if event:
            domain.append(["event", "=", event])
        if since:
            domain.append(["timestamp", ">=", since])
        if priority:
            domain.append(["priority", "=", priority])
        if category:
            domain.append(["category", "=", category])
        if status:
            domain.append(["status", "=", status])

        # Extended fields list
        fields = [
            "id", "model", "record_id", "event", "timestamp",
            "priority", "category", "status",
            "retry_count", "max_retries", "next_retry_at",
            "error_message", "error_type", "error_code",
            "changed_fields", "payload",
            "subscriber_id", "template_id", "config_id",
            "sent_at", "response_code", "processing_time",
            "is_archived"
        ]

        try:
            rows = self.odoo.search_read(
                "webhook.event",  # Updated model name
                domain=domain,
                fields=fields,
                limit=limit,
                offset=offset,
                order="timestamp desc"
            )

            events = [
                WebhookEventOut(
                    id=r["id"],
                    model=r.get("model", ""),
                    record_id=r.get("record_id", 0),
                    event=r.get("event", "manual"),
                    occurred_at=r.get("timestamp", ""),
                    priority=r.get("priority", "medium"),
                    category=r.get("category", "business"),
                    status=r.get("status", "pending"),
                    retry_count=r.get("retry_count", 0),
                    max_retries=r.get("max_retries", 5),
                    next_retry_at=r.get("next_retry_at"),
                    error_message=r.get("error_message"),
                    error_type=r.get("error_type"),
                    error_code=r.get("error_code"),
                    changed_fields=r.get("changed_fields"),
                    payload=r.get("payload"),
                    subscriber_id=r.get("subscriber_id"),
                    template_id=r.get("template_id"),
                    config_id=r.get("config_id"),
                    sent_at=r.get("sent_at"),
                    response_code=r.get("response_code"),
                    processing_time=r.get("processing_time"),
                    is_archived=r.get("is_archived", False)
                )
                for r in rows
            ]

            # Cache for 30 seconds (shorter TTL for detailed data)
            try:
                await self.cache.set(
                    cache_key,
                    [event.dict() for event in events],
                    ttl=30
                )
            except Exception as e:
                logger.warning(f"Cache storage failed: {e}")

            logger.info(f"Retrieved {len(events)} enhanced webhook events")
            return events

        except OdooError as e:
            logger.error(f"Odoo error while fetching enhanced events: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while fetching enhanced events: {e}")
            raise

    async def retry_event(
        self,
        event_id: int,
        force: bool = False
    ) -> RetryResponse:
        """
        Retry a failed webhook event

        Args:
            event_id: Event ID to retry
            force: Force retry even if max_retries reached

        Returns:
            RetryResponse with operation result
        """

        try:
            # Call Odoo method to retry
            result = self.odoo.call_kw(
                "webhook.event",
                "retry_event",
                [[event_id]],
                {"force": force}
            )

            return RetryResponse(
                success=result.get("success", False),
                event_id=event_id,
                message=result.get("message", ""),
                new_status=result.get("new_status", "unknown")
            )

        except OdooError as e:
            logger.error(f"Odoo error retrying event {event_id}: {e}")
            return RetryResponse(
                success=False,
                event_id=event_id,
                message=f"Error: {str(e)}",
                new_status="failed"
            )
        except Exception as e:
            logger.error(f"Error retrying event {event_id}: {e}")
            return RetryResponse(
                success=False,
                event_id=event_id,
                message=f"Unexpected error: {str(e)}",
                new_status="failed"
            )

    async def bulk_retry_events(
        self,
        event_ids: List[int],
        force: bool = False
    ) -> List[RetryResponse]:
        """
        Retry multiple failed events

        Args:
            event_ids: List of event IDs to retry
            force: Force retry even if max_retries reached

        Returns:
            List of RetryResponse for each event
        """

        results = []
        for event_id in event_ids:
            result = await self.retry_event(event_id, force)
            results.append(result)

        logger.info(f"Bulk retry completed: {len(results)} events processed")
        return results

    async def get_dead_letter_queue_stats(self) -> DeadLetterQueueStats:
        """
        Get statistics about dead letter queue

        Returns:
            DeadLetterQueueStats with summary information
        """

        try:
            # Get dead letter events
            dead_events = self.odoo.search_read(
                "webhook.event",
                domain=[["status", "=", "dead"]],
                fields=["id", "model", "timestamp"],
                limit=10000
            )

            # Count by model
            model_counts = {}
            for event in dead_events:
                model = event.get("model", "unknown")
                model_counts[model] = model_counts.get(model, 0) + 1

            # Get oldest and newest
            timestamps = [e.get("timestamp") for e in dead_events if e.get("timestamp")]
            oldest = min(timestamps) if timestamps else None
            newest = max(timestamps) if timestamps else None

            return DeadLetterQueueStats(
                total_events=len(dead_events),
                by_model=[
                    ModelCount(model=model, count=count)
                    for model, count in model_counts.items()
                ],
                oldest_event=oldest,
                newest_event=newest
            )

        except OdooError as e:
            logger.error(f"Odoo error getting dead letter stats: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting dead letter stats: {e}")
            raise

    async def get_event_statistics(
        self,
        since: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> EventStatistics:
        """
        Get comprehensive event statistics

        Args:
            since: Get stats since this timestamp
            model_name: Filter by specific model

        Returns:
            EventStatistics with detailed metrics
        """

        try:
            domain = []
            if since:
                domain.append(["timestamp", ">=", since])
            if model_name:
                domain.append(["model", "=", model_name])

            # Get all events matching criteria
            events = self.odoo.search_read(
                "webhook.event",
                domain=domain,
                fields=["status", "priority", "category", "model", "processing_time"],
                limit=10000
            )

            # Calculate stats
            total = len(events)
            by_status = {}
            by_priority = {}
            by_category = {}
            model_counts = {}
            processing_times = []

            for event in events:
                status = event.get("status", "unknown")
                priority = event.get("priority", "unknown")
                category = event.get("category", "unknown")
                model = event.get("model", "unknown")
                proc_time = event.get("processing_time")

                by_status[status] = by_status.get(status, 0) + 1
                by_priority[priority] = by_priority.get(priority, 0) + 1
                by_category[category] = by_category.get(category, 0) + 1
                model_counts[model] = model_counts.get(model, 0) + 1

                if proc_time:
                    processing_times.append(proc_time)

            # Calculate success rate
            sent_count = by_status.get("sent", 0)
            success_rate = (sent_count / total * 100) if total > 0 else 0.0

            # Calculate average processing time
            avg_processing_time = (
                sum(processing_times) / len(processing_times)
                if processing_times else 0.0
            )

            return EventStatistics(
                total_events=total,
                by_status=by_status,
                by_priority=by_priority,
                by_category=by_category,
                by_model=[
                    ModelCount(model=model, count=count)
                    for model, count in sorted(
                        model_counts.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:10]  # Top 10 models
                ],
                success_rate=success_rate,
                average_processing_time=avg_processing_time
            )

        except OdooError as e:
            logger.error(f"Odoo error getting statistics: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            raise

    async def get_webhook_configs(self) -> List[WebhookConfigOut]:
        """
        Get all webhook configurations

        Returns:
            List of webhook configurations
        """

        try:
            configs = self.odoo.search_read(
                "webhook.config",
                domain=[["active", "=", True]],
                fields=[
                    "id", "name", "model_name", "enabled",
                    "priority", "category", "events",
                    "batch_enabled", "batch_size"
                ],
                limit=1000
            )

            return [
                WebhookConfigOut(
                    id=c["id"],
                    name=c.get("name", ""),
                    model_name=c.get("model_name", ""),
                    enabled=c.get("enabled", False),
                    priority=c.get("priority", "medium"),
                    category=c.get("category", "business"),
                    events=c.get("events", []),
                    batch_enabled=c.get("batch_enabled", False),
                    batch_size=c.get("batch_size")
                )
                for c in configs
            ]

        except OdooError as e:
            logger.error(f"Odoo error getting configs: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting configs: {e}")
            raise

    # ===== Push Webhook Methods =====

    async def receive_webhook(
        self,
        payload: dict
    ) -> Dict[str, Any]:
        """
        Receive webhook event from Odoo (Push-based)

        This method receives webhook events pushed from auto-webhook-odoo
        and processes them immediately.

        Args:
            payload: Webhook payload from Odoo

        Returns:
            Dict with processing result
        """
        try:
            # Extract event data
            model = payload.get("model")
            record_id = payload.get("record_id")
            event_type = payload.get("event")
            priority = payload.get("priority", "medium")
            timestamp = payload.get("timestamp") or payload.get("_webhook_metadata", {}).get("timestamp")
            
            logger.info(
                f"Received webhook push: {model}:{record_id} ({event_type}), "
                f"priority={priority}"
            )

            # Validate required fields
            if not model or record_id is None or not event_type:
                raise ValueError("Missing required fields: model, record_id, or event")

            # Extract event ID if available
            event_metadata = payload.get("_webhook_metadata", {})
            odoo_event_id = event_metadata.get("event_id") or payload.get("event_id")
            
            # Note: auto-webhook-odoo already stores the event in update.webhook
            # We don't need to do anything here - the event is already available for Pull-based access
            # This Push endpoint is just for real-time notification of critical events

            # Process critical events immediately
            if priority == "high":
                logger.info(f"Processing high-priority event: {model}:{record_id}")
                # Here you can add immediate processing logic:
                # - Send notifications
                # - Update cache
                # - Trigger WebSocket broadcast
                # - etc.

            # Return success response
            return {
                "success": True,
                "message": "Webhook received and processed",
                "event_id": odoo_event_id,
                "processed_at": datetime.utcnow().isoformat(),
                "model": model,
                "record_id": record_id,
                "event": event_type,
                "priority": priority
            }

        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            raise
