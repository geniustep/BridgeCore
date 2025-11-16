"""
WebSocket Support for Real-Time Updates

Provides real-time notifications for:
- System connection status changes
- Long-running operation progress
- Audit log events
- Cache invalidation
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set, List
from loguru import logger
import json
import asyncio
from datetime import datetime


router = APIRouter()


class ConnectionManager:
    """
    Manage WebSocket connections

    Features:
    - User-based connection tracking
    - Broadcast to all connections
    - Broadcast to specific user
    - Channel-based subscriptions
    - Odoo model subscriptions for real-time updates
    """

    def __init__(self):
        # user_id -> Set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}

        # channel -> Set of user_ids subscribed
        self.channel_subscriptions: Dict[str, Set[int]] = {}

        # Odoo model subscriptions: "system:model:id" -> Set of user_ids
        self.model_subscriptions: Dict[str, Set[int]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """
        Accept new WebSocket connection

        Args:
            websocket: WebSocket instance
            user_id: User ID
        """
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected for user {user_id}")

    def disconnect(self, websocket: WebSocket, user_id: int):
        """
        Remove WebSocket connection

        Args:
            websocket: WebSocket instance
            user_id: User ID
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)

            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        logger.info(f"WebSocket disconnected for user {user_id}")

    async def send_personal_message(self, message: dict, user_id: int):
        """
        Send message to specific user

        Args:
            message: Message dictionary
            user_id: Target user ID
        """
        if user_id in self.active_connections:
            dead_connections = set()

            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send message to user {user_id}: {e}")
                    dead_connections.add(connection)

            # Clean up dead connections
            for connection in dead_connections:
                self.active_connections[user_id].discard(connection)

    async def broadcast(self, message: dict):
        """
        Broadcast message to all connected users

        Args:
            message: Message dictionary
        """
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)

    async def subscribe_to_channel(self, channel: str, user_id: int):
        """
        Subscribe user to channel

        Args:
            channel: Channel name
            user_id: User ID
        """
        if channel not in self.channel_subscriptions:
            self.channel_subscriptions[channel] = set()

        self.channel_subscriptions[channel].add(user_id)
        logger.info(f"User {user_id} subscribed to channel {channel}")

    async def unsubscribe_from_channel(self, channel: str, user_id: int):
        """
        Unsubscribe user from channel

        Args:
            channel: Channel name
            user_id: User ID
        """
        if channel in self.channel_subscriptions:
            self.channel_subscriptions[channel].discard(user_id)
            logger.info(f"User {user_id} unsubscribed from channel {channel}")

    async def broadcast_to_channel(self, channel: str, message: dict):
        """
        Broadcast message to all users subscribed to channel

        Args:
            channel: Channel name
            message: Message dictionary
        """
        if channel in self.channel_subscriptions:
            for user_id in self.channel_subscriptions[channel]:
                await self.send_personal_message(message, user_id)

    async def subscribe_to_model(
        self,
        user_id: int,
        system_id: str,
        model: str,
        record_ids: List[int]
    ):
        """
        Subscribe user to Odoo model updates

        Args:
            user_id: User ID
            system_id: System identifier
            model: Odoo model name
            record_ids: List of record IDs to subscribe to
        """
        for record_id in record_ids:
            subscription_key = f"{system_id}:{model}:{record_id}"

            if subscription_key not in self.model_subscriptions:
                self.model_subscriptions[subscription_key] = set()

            self.model_subscriptions[subscription_key].add(user_id)

        logger.info(
            f"User {user_id} subscribed to {system_id}:{model} "
            f"records: {record_ids}"
        )

    async def unsubscribe_from_model(
        self,
        user_id: int,
        system_id: str,
        model: str,
        record_ids: List[int]
    ):
        """
        Unsubscribe user from Odoo model updates

        Args:
            user_id: User ID
            system_id: System identifier
            model: Odoo model name
            record_ids: List of record IDs to unsubscribe from
        """
        for record_id in record_ids:
            subscription_key = f"{system_id}:{model}:{record_id}"

            if subscription_key in self.model_subscriptions:
                self.model_subscriptions[subscription_key].discard(user_id)

                # Clean up empty subscriptions
                if not self.model_subscriptions[subscription_key]:
                    del self.model_subscriptions[subscription_key]

        logger.info(
            f"User {user_id} unsubscribed from {system_id}:{model} "
            f"records: {record_ids}"
        )

    async def broadcast_model_update(
        self,
        system_id: str,
        model: str,
        record_id: int,
        operation: str,
        data: dict
    ):
        """
        Broadcast Odoo model update to subscribed users

        Args:
            system_id: System identifier
            model: Odoo model name
            record_id: Record ID
            operation: Operation type (create, write, unlink)
            data: Update data
        """
        subscription_key = f"{system_id}:{model}:{record_id}"

        if subscription_key in self.model_subscriptions:
            message = {
                "type": "model_update",
                "system_id": system_id,
                "model": model,
                "record_id": record_id,
                "operation": operation,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }

            for user_id in self.model_subscriptions[subscription_key]:
                await self.send_personal_message(message, user_id)

            logger.debug(
                f"Broadcast {operation} on {model}:{record_id} "
                f"to {len(self.model_subscriptions[subscription_key])} users"
            )

    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(conns) for conns in self.active_connections.values())


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """
    WebSocket endpoint for real-time updates

    Args:
        websocket: WebSocket instance
        user_id: User ID

    Message Format:
        {
            "type": "subscribe|unsubscribe|ping|message",
            "channel": "system_status|operations|audit",
            "data": {...}
        }

    Response Format:
        {
            "type": "notification|status|error|pong",
            "channel": "...",
            "data": {...},
            "timestamp": "2024-01-15T12:00:00"
        }

    Example:
        # JavaScript client
        const ws = new WebSocket('ws://localhost:8000/api/v1/ws/123');

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Received:', data);
        };

        // Subscribe to channel
        ws.send(JSON.stringify({
            type: 'subscribe',
            channel: 'system_status'
        }));
    """
    await manager.connect(websocket, user_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                message_type = message.get("type")

                if message_type == "subscribe":
                    channel = message.get("channel")
                    if channel:
                        await manager.subscribe_to_channel(channel, user_id)
                        await websocket.send_json({
                            "type": "status",
                            "message": f"Subscribed to {channel}",
                            "channel": channel
                        })

                elif message_type == "unsubscribe":
                    channel = message.get("channel")
                    if channel:
                        await manager.unsubscribe_from_channel(channel, user_id)
                        await websocket.send_json({
                            "type": "status",
                            "message": f"Unsubscribed from {channel}",
                            "channel": channel
                        })

                elif message_type == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    })

                elif message_type == "subscribe_model":
                    # Subscribe to Odoo model updates
                    system_id = message.get("system_id")
                    model = message.get("model")
                    record_ids = message.get("record_ids", [])

                    if system_id and model and record_ids:
                        await manager.subscribe_to_model(
                            user_id=user_id,
                            system_id=system_id,
                            model=model,
                            record_ids=record_ids
                        )
                        await websocket.send_json({
                            "type": "status",
                            "message": f"Subscribed to {model} records: {record_ids}",
                            "system_id": system_id,
                            "model": model,
                            "record_ids": record_ids
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "system_id, model, and record_ids are required"
                        })

                elif message_type == "unsubscribe_model":
                    # Unsubscribe from Odoo model updates
                    system_id = message.get("system_id")
                    model = message.get("model")
                    record_ids = message.get("record_ids", [])

                    if system_id and model and record_ids:
                        await manager.unsubscribe_from_model(
                            user_id=user_id,
                            system_id=system_id,
                            model=model,
                            record_ids=record_ids
                        )
                        await websocket.send_json({
                            "type": "status",
                            "message": f"Unsubscribed from {model} records: {record_ids}",
                            "system_id": system_id,
                            "model": model,
                            "record_ids": record_ids
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "system_id, model, and record_ids are required"
                        })

                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"WebSocket disconnected for user {user_id}")


# Helper functions for sending notifications

async def notify_system_status(
    user_id: int,
    system_id: str,
    status: str,
    message: str = None
):
    """
    Notify user about system status change

    Args:
        user_id: User ID
        system_id: System ID
        status: Status (connected, disconnected, error)
        message: Optional message
    """
    await manager.broadcast_to_channel("system_status", {
        "type": "notification",
        "channel": "system_status",
        "data": {
            "system_id": system_id,
            "status": status,
            "message": message
        }
    })


async def notify_operation_progress(
    user_id: int,
    operation_id: str,
    progress: int,
    status: str,
    message: str = None
):
    """
    Notify user about operation progress

    Args:
        user_id: User ID
        operation_id: Operation ID
        progress: Progress percentage (0-100)
        status: Status (running, completed, failed)
        message: Optional message
    """
    await manager.send_personal_message({
        "type": "notification",
        "channel": "operations",
        "data": {
            "operation_id": operation_id,
            "progress": progress,
            "status": status,
            "message": message
        }
    }, user_id)


async def notify_audit_event(
    user_id: int,
    action: str,
    model: str,
    record_id: str,
    status: str
):
    """
    Notify user about audit event

    Args:
        user_id: User ID
        action: Action performed
        model: Model name
        record_id: Record ID
        status: Status
    """
    await manager.send_personal_message({
        "type": "notification",
        "channel": "audit",
        "data": {
            "action": action,
            "model": model,
            "record_id": record_id,
            "status": status
        }
    }, user_id)


async def notify_cache_invalidation(channel: str, keys: list):
    """
    Notify about cache invalidation

    Args:
        channel: Channel name
        keys: Cache keys invalidated
    """
    await manager.broadcast_to_channel("cache", {
        "type": "notification",
        "channel": "cache",
        "data": {
            "event": "invalidation",
            "keys": keys
        }
    })


@router.get("/ws/stats")
async def websocket_stats():
    """
    Get WebSocket connection statistics

    Returns:
        Connection statistics
    """
    return {
        "active_connections": manager.get_connection_count(),
        "active_users": len(manager.active_connections),
        "channels": {
            channel: len(users)
            for channel, users in manager.channel_subscriptions.items()
        }
    }


# ===== Critical Events Support (for Smart Sync) =====

async def notify_critical_event(
    user_id: int,
    event_type: str,
    model: str,
    record_id: int,
    data: dict,
    priority: str = "high"
):
    """
    Send critical event notification to user via WebSocket

    This is used for high-priority events that need immediate attention,
    such as:
    - Urgent sale orders
    - Critical stock movements
    - Important customer updates

    Args:
        user_id: User ID to notify
        event_type: Event type (create, write, unlink)
        model: Odoo model name
        record_id: Record ID
        data: Event data/payload
        priority: Event priority (high, medium, low)
    """
    message = {
        "type": "critical_event",
        "channel": "critical_events",
        "priority": priority,
        "event": {
            "event_type": event_type,
            "model": model,
            "record_id": record_id,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    }

    await manager.send_personal_message(message, user_id)
    logger.info(
        f"Sent critical {event_type} event for {model}:{record_id} "
        f"to user {user_id}"
    )


async def broadcast_urgent_update(
    model: str,
    record_id: int,
    event_type: str,
    data: dict,
    affected_users: List[int] = None
):
    """
    Broadcast urgent update to multiple users

    Used when a critical change affects multiple users and they need
    to be notified immediately.

    Args:
        model: Odoo model name
        record_id: Record ID
        event_type: Event type
        data: Event data
        affected_users: Optional list of specific user IDs to notify.
                       If None, broadcasts to all connected users.
    """
    message = {
        "type": "urgent_update",
        "channel": "urgent_updates",
        "event": {
            "model": model,
            "record_id": record_id,
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    }

    if affected_users:
        for user_id in affected_users:
            await manager.send_personal_message(message, user_id)
    else:
        await manager.broadcast(message)

    logger.info(
        f"Broadcast urgent {event_type} for {model}:{record_id} "
        f"to {len(affected_users) if affected_users else 'all'} users"
    )


async def notify_sync_event(
    user_id: int,
    event_id: int,
    model: str,
    record_id: int,
    event_type: str,
    app_type: str = None
):
    """
    Notify user about new sync event

    This is called when a new webhook event is created that affects
    the user's app. The client can then trigger a sync pull.

    Args:
        user_id: User ID
        event_id: Webhook event ID
        model: Odoo model name
        record_id: Record ID
        event_type: Event type (create/write/unlink)
        app_type: Optional app type filter
    """
    message = {
        "type": "sync_event",
        "channel": "sync_events",
        "event": {
            "id": event_id,
            "model": model,
            "record_id": record_id,
            "event_type": event_type,
            "app_type": app_type,
            "timestamp": datetime.now().isoformat()
        },
        "action": "trigger_sync"  # Hint for client to call /api/v2/sync/pull
    }

    await manager.send_personal_message(message, user_id)
    logger.debug(f"Notified user {user_id} about sync event {event_id}")


# ===== Redis PubSub Integration (Optional) =====

try:
    import redis.asyncio as redis
    from app.core.config import settings

    # Redis client for pub/sub
    redis_pubsub_client = None

    async def init_redis_pubsub():
        """Initialize Redis PubSub for distributed WebSocket events"""
        global redis_pubsub_client

        try:
            redis_pubsub_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Redis PubSub initialized for WebSocket events")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis PubSub: {e}")
            redis_pubsub_client = None

    async def publish_event_to_redis(channel: str, event: dict):
        """
        Publish event to Redis channel for distributed handling

        This allows multiple BridgeCore instances to share WebSocket events.

        Args:
            channel: Redis channel name
            event: Event data to publish
        """
        if redis_pubsub_client:
            try:
                await redis_pubsub_client.publish(
                    channel,
                    json.dumps(event)
                )
                logger.debug(f"Published event to Redis channel: {channel}")
            except Exception as e:
                logger.error(f"Failed to publish to Redis: {e}")

    async def subscribe_to_redis_events():
        """
        Subscribe to Redis events and forward to WebSocket clients

        This should be run as a background task.
        """
        if not redis_pubsub_client:
            logger.warning("Redis PubSub not available")
            return

        pubsub = redis_pubsub_client.pubsub()

        try:
            # Subscribe to channels
            await pubsub.subscribe(
                "critical_events",
                "urgent_updates",
                "sync_events"
            )

            logger.info("Subscribed to Redis event channels")

            # Listen for messages
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        event_data = json.loads(message["data"])
                        channel = message["channel"]

                        # Forward to appropriate users based on channel
                        if channel == "critical_events":
                            user_id = event_data.get("user_id")
                            if user_id:
                                await manager.send_personal_message(
                                    event_data,
                                    user_id
                                )

                        elif channel == "urgent_updates":
                            await manager.broadcast(event_data)

                        elif channel == "sync_events":
                            user_id = event_data.get("user_id")
                            if user_id:
                                await manager.send_personal_message(
                                    event_data,
                                    user_id
                                )

                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")

        except Exception as e:
            logger.error(f"Redis subscription error: {e}")
        finally:
            await pubsub.unsubscribe()
            await pubsub.close()

except ImportError:
    logger.warning("redis.asyncio not available, skipping PubSub features")
    redis_pubsub_client = None

    async def init_redis_pubsub():
        pass

    async def publish_event_to_redis(channel: str, event: dict):
        pass

    async def subscribe_to_redis_events():
        pass
