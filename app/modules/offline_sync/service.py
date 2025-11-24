"""
Offline Sync Service

Business logic for offline-first synchronization
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
import time

from app.modules.offline_sync.schemas import (
    # Push
    OfflinePushRequest,
    OfflinePushResponse,
    LocalChange,
    PushResult,
    SyncAction,
    SyncStatus,

    # Pull
    OfflinePullRequest,
    OfflinePullResponse,
    ServerChange,

    # Conflict
    ConflictResolutionRequest,
    ConflictResolutionResponse,
    ConflictStrategy,
    ConflictInfo,

    # State
    SyncStateResponse,
    SyncStatistics,

    # Full sync
    FullSyncRequest,
    FullSyncResponse,

    # Batch
    BatchSyncRequest,
    BatchSyncResponse,
)

from app.utils.odoo_client import OdooClient, OdooError
from app.services.cache_service import CacheService
from app.modules.webhook.service import WebhookService


class OfflineSyncService:
    """
    Offline Sync Service

    Handles all offline synchronization operations:
    - Push: Upload local changes to server
    - Pull: Download server changes
    - Conflict Resolution: Resolve data conflicts
    - State Management: Track sync state
    """

    # App type model mappings
    APP_TYPE_MODELS = {
        "sales_app": [
            "sale.order",
            "sale.order.line",
            "res.partner",
            "product.template",
            "product.product",
            "product.category",
            "account.move",
            "account.payment",
        ],
        "delivery_app": [
            "stock.picking",
            "stock.move",
            "stock.move.line",
            "stock.location",
            "res.partner",
            "product.product",
        ],
        "warehouse_app": [
            "stock.picking",
            "stock.move",
            "stock.quant",
            "stock.inventory",
            "product.product",
            "stock.location",
            "stock.warehouse",
        ],
        "manager_app": [
            "sale.order",
            "purchase.order",
            "account.move",
            "hr.expense",
            "project.project",
            "project.task",
            "res.partner",
        ],
        "crm_app": [
            "crm.lead",
            "crm.stage",
            "res.partner",
            "calendar.event",
            "mail.activity",
        ],
    }

    def __init__(
        self,
        odoo_client: OdooClient,
        cache_service: CacheService,
        webhook_service: Optional[WebhookService] = None
    ):
        self.odoo = odoo_client
        self.cache = cache_service
        self.webhook_service = webhook_service

    # ==================== PUSH (Upload Local Changes) ====================

    async def push_changes(
        self,
        user_id: int,
        push_request: OfflinePushRequest
    ) -> OfflinePushResponse:
        """
        Push local changes to server

        Process:
        1. Validate and sort changes by dependencies
        2. Execute changes in batches
        3. Detect and handle conflicts
        4. Return results with ID mapping
        """
        start_time = time.time()
        results: List[PushResult] = []
        id_mapping: Dict[str, int] = {}

        try:
            # Sort changes by dependencies
            sorted_changes = self._sort_by_dependencies(push_request.changes)

            # Process in batches
            batch_size = push_request.batch_size
            for i in range(0, len(sorted_changes), batch_size):
                batch = sorted_changes[i:i + batch_size]

                batch_results = await self._process_batch(
                    user_id=user_id,
                    batch=batch,
                    conflict_strategy=push_request.conflict_strategy,
                    id_mapping=id_mapping,
                )

                results.extend(batch_results)

                # Stop on error if requested
                if push_request.stop_on_error:
                    if any(r.status == SyncStatus.FAILED for r in batch_results):
                        logger.warning(f"Stopping push due to error (stop_on_error=True)")
                        break

            # Calculate statistics
            succeeded = sum(1 for r in results if r.status == SyncStatus.SUCCESS)
            failed = sum(1 for r in results if r.status == SyncStatus.FAILED)
            conflicts = sum(1 for r in results if r.status == SyncStatus.CONFLICT)

            total_time = (time.time() - start_time) * 1000  # ms
            avg_time = total_time / len(results) if results else 0

            # Get next sync token
            next_sync_token = await self._generate_sync_token(
                user_id, push_request.device_id
            )

            return OfflinePushResponse(
                success=failed == 0,
                total=len(results),
                succeeded=succeeded,
                failed=failed,
                conflicts=conflicts,
                results=results,
                id_mapping=id_mapping,
                next_sync_token=next_sync_token,
                server_timestamp=datetime.utcnow().isoformat(),
                total_processing_time_ms=total_time,
                average_processing_time_ms=avg_time,
            )

        except Exception as e:
            logger.exception(f"Error in push_changes: {e}")
            raise

    async def _process_batch(
        self,
        user_id: int,
        batch: List[LocalChange],
        conflict_strategy: ConflictStrategy,
        id_mapping: Dict[str, int],
    ) -> List[PushResult]:
        """Process a batch of changes"""
        results = []

        for change in batch:
            start_time = time.time()

            try:
                result = await self._process_single_change(
                    user_id=user_id,
                    change=change,
                    conflict_strategy=conflict_strategy,
                    id_mapping=id_mapping,
                )

                # Add processing time
                processing_time = (time.time() - start_time) * 1000
                result.processing_time_ms = processing_time

                results.append(result)

            except Exception as e:
                logger.error(f"Error processing change {change.local_id}: {e}")
                results.append(
                    PushResult(
                        local_id=change.local_id,
                        status=SyncStatus.FAILED,
                        action=change.action,
                        model=change.model,
                        error=str(e),
                        error_code="PROCESSING_ERROR",
                    )
                )

        return results

    async def _process_single_change(
        self,
        user_id: int,
        change: LocalChange,
        conflict_strategy: ConflictStrategy,
        id_mapping: Dict[str, int],
    ) -> PushResult:
        """Process a single change"""

        # Replace local IDs in data with server IDs
        data = self._replace_local_ids(change.data, id_mapping)

        try:
            if change.action == SyncAction.CREATE:
                return await self._handle_create(change, data)

            elif change.action == SyncAction.UPDATE:
                return await self._handle_update(
                    change, data, conflict_strategy
                )

            elif change.action == SyncAction.DELETE:
                return await self._handle_delete(change)

            else:
                raise ValueError(f"Unsupported action: {change.action}")

        except OdooError as e:
            return PushResult(
                local_id=change.local_id,
                status=SyncStatus.FAILED,
                action=change.action,
                model=change.model,
                error=str(e),
                error_code="ODOO_ERROR",
            )

    async def _handle_create(
        self, change: LocalChange, data: Dict[str, Any]
    ) -> PushResult:
        """Handle create action"""
        loop = asyncio.get_event_loop()

        # Call Odoo create
        server_id = await loop.run_in_executor(
            None,
            self.odoo.create,
            change.model,
            data,
        )

        return PushResult(
            local_id=change.local_id,
            status=SyncStatus.SUCCESS,
            action=change.action,
            model=change.model,
            server_id=server_id,
            server_timestamp=datetime.utcnow().isoformat(),
        )

    async def _handle_update(
        self,
        change: LocalChange,
        data: Dict[str, Any],
        conflict_strategy: ConflictStrategy,
    ) -> PushResult:
        """Handle update action with conflict detection"""
        loop = asyncio.get_event_loop()

        if not change.record_id:
            return PushResult(
                local_id=change.local_id,
                status=SyncStatus.FAILED,
                action=change.action,
                model=change.model,
                error="record_id is required for update",
                error_code="MISSING_RECORD_ID",
            )

        # Check for conflicts
        conflict_detected = False
        if change.version and change.version > 1:
            # Read current server version
            server_record = await loop.run_in_executor(
                None,
                self.odoo.read,
                change.model,
                [change.record_id],
                ["write_date", "__last_update"],
            )

            if server_record:
                # Check if server record was updated after local change
                server_write_date = server_record[0].get("write_date") or server_record[0].get("__last_update")
                if server_write_date:
                    local_time = datetime.fromisoformat(change.local_timestamp.replace('Z', '+00:00'))
                    server_time = datetime.fromisoformat(server_write_date.replace('Z', '+00:00')) if isinstance(server_write_date, str) else server_write_date

                    if server_time > local_time:
                        conflict_detected = True

        if conflict_detected:
            # Handle conflict based on strategy
            if conflict_strategy == ConflictStrategy.SERVER_WINS:
                # Skip update, server wins
                return PushResult(
                    local_id=change.local_id,
                    status=SyncStatus.CONFLICT,
                    action=change.action,
                    model=change.model,
                    server_id=change.record_id,
                    error="Conflict detected - server wins",
                    conflict_info={
                        "strategy": "server_wins",
                        "resolution": "skipped",
                    },
                )

            elif conflict_strategy == ConflictStrategy.CLIENT_WINS:
                # Continue with update
                pass

            elif conflict_strategy == ConflictStrategy.MANUAL:
                # Return conflict for manual resolution
                return PushResult(
                    local_id=change.local_id,
                    status=SyncStatus.CONFLICT,
                    action=change.action,
                    model=change.model,
                    server_id=change.record_id,
                    conflict_info={
                        "strategy": "manual",
                        "requires_resolution": True,
                    },
                )

        # Execute update
        success = await loop.run_in_executor(
            None,
            self.odoo.write,
            change.model,
            [change.record_id],
            data,
        )

        return PushResult(
            local_id=change.local_id,
            status=SyncStatus.SUCCESS if success else SyncStatus.FAILED,
            action=change.action,
            model=change.model,
            server_id=change.record_id,
            server_timestamp=datetime.utcnow().isoformat(),
        )

    async def _handle_delete(self, change: LocalChange) -> PushResult:
        """Handle delete action"""
        loop = asyncio.get_event_loop()

        if not change.record_id:
            return PushResult(
                local_id=change.local_id,
                status=SyncStatus.FAILED,
                action=change.action,
                model=change.model,
                error="record_id is required for delete",
                error_code="MISSING_RECORD_ID",
            )

        # Call Odoo unlink
        success = await loop.run_in_executor(
            None,
            self.odoo.unlink,
            change.model,
            [change.record_id],
        )

        return PushResult(
            local_id=change.local_id,
            status=SyncStatus.SUCCESS if success else SyncStatus.FAILED,
            action=change.action,
            model=change.model,
            server_id=change.record_id,
            server_timestamp=datetime.utcnow().isoformat(),
        )

    # ==================== PULL (Download Server Changes) ====================

    async def pull_changes(
        self,
        user_id: int,
        pull_request: OfflinePullRequest,
    ) -> OfflinePullResponse:
        """
        Pull server changes

        Returns only new changes since last sync
        """
        try:
            # Get app type models
            models_filter = pull_request.models_filter
            if not models_filter:
                models_filter = self.APP_TYPE_MODELS.get(
                    pull_request.app_type, []
                )

            # Get last event ID from sync state or request
            last_event_id = pull_request.last_event_id or 0

            # Check cache first
            cache_key = f"offline_sync:pull:{user_id}:{pull_request.device_id}:{last_event_id}"
            cached_response = await self.cache.get(cache_key)

            if cached_response:
                logger.debug(f"Cache hit for pull request: {cache_key}")
                return OfflinePullResponse(**cached_response)

            # Fetch events from Odoo
            loop = asyncio.get_event_loop()

            domain = [
                ("id", ">", last_event_id),
            ]

            if models_filter:
                domain.append(("model", "in", models_filter))

            if pull_request.priority_filter:
                domain.append(("priority", "in", pull_request.priority_filter))

            # Get events
            events_data = await loop.run_in_executor(
                None,
                self.odoo.search_read,
                "update.webhook",
                domain,
                ["id", "model", "record_id", "event", "timestamp", "payload", "changed_fields", "priority", "category"],
                pull_request.limit,
                pull_request.offset,
                "id ASC",
            )

            # Transform to ServerChange objects
            events = []
            for event_data in events_data:
                events.append(
                    ServerChange(
                        event_id=event_data["id"],
                        model=event_data["model"],
                        record_id=event_data["record_id"],
                        action=event_data["event"],
                        timestamp=event_data.get("timestamp", ""),
                        data=event_data.get("payload") if pull_request.include_payload else None,
                        changed_fields=event_data.get("changed_fields"),
                        priority=event_data.get("priority"),
                        category=event_data.get("category"),
                    )
                )

            # Calculate next state
            new_last_event_id = events[-1].event_id if events else last_event_id
            next_sync_token = await self._generate_sync_token(
                user_id, pull_request.device_id
            )

            # Check if more events available
            total_count = await loop.run_in_executor(
                None,
                self.odoo.search_count,
                "update.webhook",
                domain,
            )

            has_more = (pull_request.offset + len(events)) < total_count

            response = OfflinePullResponse(
                success=True,
                has_updates=len(events) > 0,
                new_events_count=len(events),
                events=events,
                next_sync_token=next_sync_token,
                last_event_id=new_last_event_id,
                last_sync_time=datetime.utcnow().isoformat(),
                has_more=has_more,
                total_available=total_count,
                server_timestamp=datetime.utcnow().isoformat(),
            )

            # Cache for 60 seconds
            await self.cache.set(cache_key, response.dict(), ttl=60)

            return response

        except Exception as e:
            logger.exception(f"Error in pull_changes: {e}")
            raise

    # ==================== CONFLICT RESOLUTION ====================

    async def resolve_conflicts(
        self,
        user_id: int,
        resolution_request: ConflictResolutionRequest,
    ) -> ConflictResolutionResponse:
        """
        Resolve conflicts manually or automatically
        """
        results = []

        for resolution in resolution_request.resolutions:
            try:
                # Get conflict details
                conflict = next(
                    (c for c in resolution_request.conflicts if c["local_id"] == resolution.local_id),
                    None
                )

                if not conflict:
                    results.append(
                        PushResult(
                            local_id=resolution.local_id,
                            status=SyncStatus.FAILED,
                            action=SyncAction.UPDATE,
                            model="",
                            error="Conflict not found",
                        )
                    )
                    continue

                # Apply resolution strategy
                if resolution.strategy == ConflictStrategy.SERVER_WINS:
                    # No action needed, server data prevails
                    results.append(
                        PushResult(
                            local_id=resolution.local_id,
                            status=SyncStatus.SUCCESS,
                            action=SyncAction.UPDATE,
                            model=conflict["model"],
                            server_id=conflict["server_id"],
                        )
                    )

                elif resolution.strategy == ConflictStrategy.CLIENT_WINS:
                    # Update server with client data
                    loop = asyncio.get_event_loop()
                    success = await loop.run_in_executor(
                        None,
                        self.odoo.write,
                        conflict["model"],
                        [conflict["server_id"]],
                        conflict["local_data"],
                    )

                    results.append(
                        PushResult(
                            local_id=resolution.local_id,
                            status=SyncStatus.SUCCESS if success else SyncStatus.FAILED,
                            action=SyncAction.UPDATE,
                            model=conflict["model"],
                            server_id=conflict["server_id"],
                        )
                    )

                elif resolution.strategy == ConflictStrategy.MERGE:
                    # Use merged data
                    if not resolution.merged_data:
                        raise ValueError("merged_data required for merge strategy")

                    loop = asyncio.get_event_loop()
                    success = await loop.run_in_executor(
                        None,
                        self.odoo.write,
                        conflict["model"],
                        [conflict["server_id"]],
                        resolution.merged_data,
                    )

                    results.append(
                        PushResult(
                            local_id=resolution.local_id,
                            status=SyncStatus.SUCCESS if success else SyncStatus.FAILED,
                            action=SyncAction.UPDATE,
                            model=conflict["model"],
                            server_id=conflict["server_id"],
                        )
                    )

            except Exception as e:
                logger.error(f"Error resolving conflict {resolution.local_id}: {e}")
                results.append(
                    PushResult(
                        local_id=resolution.local_id,
                        status=SyncStatus.FAILED,
                        action=SyncAction.UPDATE,
                        model="",
                        error=str(e),
                    )
                )

        resolved = sum(1 for r in results if r.status == SyncStatus.SUCCESS)
        failed = sum(1 for r in results if r.status == SyncStatus.FAILED)

        return ConflictResolutionResponse(
            success=failed == 0,
            resolved=resolved,
            failed=failed,
            results=results,
        )

    # ==================== SYNC STATE ====================

    async def get_sync_state(
        self, user_id: int, device_id: str
    ) -> SyncStateResponse:
        """Get current sync state for device"""
        try:
            loop = asyncio.get_event_loop()

            # Get sync state from Odoo
            sync_states = await loop.run_in_executor(
                None,
                self.odoo.search_read,
                "user.sync.state",
                [("user_id", "=", user_id), ("device_id", "=", device_id)],
                ["last_event_id", "last_sync_time", "sync_count", "app_type", "is_active"],
                1,
            )

            if not sync_states:
                # Create new sync state
                state_id = await loop.run_in_executor(
                    None,
                    self.odoo.create,
                    "user.sync.state",
                    {
                        "user_id": user_id,
                        "device_id": device_id,
                        "app_type": "general",
                        "last_event_id": 0,
                        "sync_count": 0,
                    },
                )

                return SyncStateResponse(
                    device_id=device_id,
                    user_id=user_id,
                    last_event_id=0,
                    last_sync_time=datetime.utcnow().isoformat(),
                    next_sync_token="0",
                    total_syncs=0,
                    total_events_synced=0,
                    sync_status="idle",
                    pending_changes=0,
                    app_type="general",
                )

            state = sync_states[0]

            return SyncStateResponse(
                device_id=device_id,
                user_id=user_id,
                last_event_id=state["last_event_id"],
                last_sync_time=state.get("last_sync_time", datetime.utcnow().isoformat()),
                next_sync_token=str(state["last_event_id"]),
                total_syncs=state["sync_count"],
                total_events_synced=state["last_event_id"],
                sync_status="idle",
                pending_changes=0,
                app_type=state.get("app_type", "general"),
            )

        except Exception as e:
            logger.exception(f"Error getting sync state: {e}")
            raise

    async def reset_sync_state(
        self, user_id: int, device_id: str
    ) -> Dict[str, Any]:
        """Reset sync state (force full sync)"""
        try:
            loop = asyncio.get_event_loop()

            # Find and reset sync state
            sync_states = await loop.run_in_executor(
                None,
                self.odoo.search,
                "user.sync.state",
                [("user_id", "=", user_id), ("device_id", "=", device_id)],
            )

            if sync_states:
                await loop.run_in_executor(
                    None,
                    self.odoo.write,
                    "user.sync.state",
                    sync_states,
                    {"last_event_id": 0, "sync_count": 0},
                )

            # Clear cache
            cache_pattern = f"offline_sync:*:{user_id}:{device_id}:*"
            await self.cache.delete_pattern(cache_pattern)

            return {
                "success": True,
                "message": "Sync state reset successfully",
                "device_id": device_id,
            }

        except Exception as e:
            logger.exception(f"Error resetting sync state: {e}")
            raise

    # ==================== UTILITY METHODS ====================

    def _sort_by_dependencies(
        self, changes: List[LocalChange]
    ) -> List[LocalChange]:
        """Sort changes by dependencies (topological sort)"""
        # Simple implementation: process creates first, then updates, then deletes
        creates = [c for c in changes if c.action == SyncAction.CREATE]
        updates = [c for c in changes if c.action == SyncAction.UPDATE]
        deletes = [c for c in changes if c.action == SyncAction.DELETE]

        # TODO: Implement proper dependency resolution based on dependencies field

        return creates + updates + deletes

    def _replace_local_ids(
        self, data: Dict[str, Any], id_mapping: Dict[str, int]
    ) -> Dict[str, Any]:
        """Replace local IDs in data with server IDs"""
        result = {}

        for key, value in data.items():
            if isinstance(value, str) and value.startswith("local_"):
                # This is a local ID reference
                if value in id_mapping:
                    result[key] = id_mapping[value]
                else:
                    result[key] = value  # Keep as is if not found
            elif isinstance(value, dict):
                result[key] = self._replace_local_ids(value, id_mapping)
            elif isinstance(value, list):
                result[key] = [
                    self._replace_local_ids(item, id_mapping)
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                result[key] = value

        return result

    async def _generate_sync_token(
        self, user_id: int, device_id: str
    ) -> str:
        """Generate next sync token"""
        # Simple implementation: use timestamp
        return f"{user_id}_{device_id}_{int(time.time())}"
