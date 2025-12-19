"""
WebSocket Support for Real-Time Updates

Provides real-time notifications for:
- System connection status changes
- Long-running operation progress
- Audit log events
- Cache invalidation
- Conversations (messages, channels, chatter)
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, status
from typing import Dict, Set, List, Optional
from loguru import logger
import json
import asyncio
from datetime import datetime
from app.core.security import decode_tenant_token


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
        
        # Connection mapping: connection_id -> {websocket, partner_id, subscriptions}
        self.connection_details: Dict[int, Dict] = {}

        # channel -> Set of user_ids subscribed
        self.channel_subscriptions: Dict[str, Set[int]] = {}
        
        # Conversation routing subscriptions: routing_key -> Set of connection_ids
        # routing_key format: "channel:{channel_id}", "thread:{model}:{res_id}", "inbox:{partner_id}"
        self.conversation_subscriptions: Dict[str, Set[int]] = {}

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
    
    async def subscribe_to_conversation_channel(
        self,
        websocket: WebSocket,
        user_id: int,
        partner_id: int,
        channel_id: int
    ):
        """
        Subscribe to a conversation channel for real-time messages
        
        ⚠️ تصحيح: نستخدم connection-based subscriptions + routing keys
        
        Args:
            websocket: WebSocket connection
            user_id: User ID
            partner_id: Partner ID
            channel_id: Channel ID
        """
        connection_id = id(websocket)
        routing_key = f"channel:{channel_id}"
        
        if routing_key not in self.conversation_subscriptions:
            self.conversation_subscriptions[routing_key] = set()
        
        self.conversation_subscriptions[routing_key].add(connection_id)
        
        # Store connection details
        self.connection_details[connection_id] = {
            "websocket": websocket,
            "user_id": user_id,
            "partner_id": partner_id,
            "subscriptions": set([routing_key])
        }
        
        logger.info(f"Connection {connection_id} (user {user_id}, partner {partner_id}) subscribed to channel {channel_id}")
    
    async def unsubscribe_from_conversation_channel(
        self,
        websocket: WebSocket,
        channel_id: int
    ):
        """
        Unsubscribe from a conversation channel
        
        Args:
            websocket: WebSocket connection
            channel_id: Channel ID
        """
        connection_id = id(websocket)
        routing_key = f"channel:{channel_id}"
        
        if routing_key in self.conversation_subscriptions:
            self.conversation_subscriptions[routing_key].discard(connection_id)
        
        if connection_id in self.connection_details:
            self.connection_details[connection_id]["subscriptions"].discard(routing_key)
    
    async def broadcast_to_routing(
        self,
        routing_key: str,
        message: dict
    ):
        """
        Broadcast message to subscribers of a routing key
        
        Routing keys:
        - channel:{channel_id} - Channel messages
        - thread:{model}:{res_id} - Chatter messages
        - inbox:{partner_id} - Personal inbox
        
        Args:
            routing_key: Routing key (e.g., "channel:123")
            message: Message dictionary to broadcast
        """
        if routing_key not in self.conversation_subscriptions:
            return
        
        connection_ids = self.conversation_subscriptions[routing_key].copy()
        dead_connections = set()
        
        for conn_id in connection_ids:
            if conn_id in self.connection_details:
                websocket = self.connection_details[conn_id]["websocket"]
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send to connection {conn_id}: {e}")
                    dead_connections.add(conn_id)
            else:
                dead_connections.add(conn_id)
        
        # Clean up dead connections
        for conn_id in dead_connections:
            if routing_key in self.conversation_subscriptions:
                self.conversation_subscriptions[routing_key].discard(conn_id)
            if conn_id in self.connection_details:
                del self.connection_details[conn_id]

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

    Message Types:
        - subscribe: Subscribe to a channel
        - unsubscribe: Unsubscribe from a channel
        - ping: Heartbeat (responds with pong)
        - subscribe_model: Subscribe to specific record updates
        - unsubscribe_model: Unsubscribe from record updates
        - subscribe_live_tracking: Subscribe to ALL GPS/position updates (ShuttleBee)
        - subscribe_model_channel: Subscribe to ALL events for a model
        - unsubscribe_model_channel: Unsubscribe from model channel
        - request_driver_location: Dispatcher requests driver's current location (on-demand)
        - location_response: Driver responds with current location
        - driver_status_update: Driver updates their status (online, offline, busy)

    Channels:
        - system_status: System connection status changes
        - operations: Long-running operation progress
        - audit: Audit log events
        - cache: Cache invalidation events
        - live_tracking: Real-time GPS/position updates (ShuttleBee)
        - model:{model_name}: All events for a specific model

    Response Format:
        {
            "type": "notification|status|error|pong|webhook_event|model_update|location_response|driver_status",
            "channel": "...",
            "data": {...},
            "timestamp": "2024-01-15T12:00:00"
        }

    ShuttleBee Live Tracking:
        When trip.state == 'ongoing':
            - Driver sends GPS automatically every 10 seconds
            - Data is saved to shuttle.vehicle.position in Odoo
            - Webhook broadcasts to all live_tracking subscribers

        When trip.state != 'ongoing':
            - Driver does NOT send GPS automatically
            - Dispatcher can request location on-demand using request_driver_location
            - Driver responds with current location (not saved to DB)

    Example - Subscribe to live tracking (Flutter/Dart - Dispatcher):
        // Connect to WebSocket
        final ws = WebSocketChannel.connect(
            Uri.parse('ws://bridgecore:8000/api/v1/ws/$userId')
        );

        // Subscribe to live tracking
        ws.sink.add(jsonEncode({
            'type': 'subscribe_live_tracking'
        }));

        // Listen for updates
        ws.stream.listen((message) {
            final data = jsonDecode(message);
            if (data['type'] == 'webhook_event') {
                // Auto update from ongoing trip
                updateDriverPosition(data['data']);
            } else if (data['type'] == 'location_response') {
                // On-demand location response
                updateDriverPosition(data);
            }
        });

    Example - Request driver location (Dispatcher):
        ws.sink.add(jsonEncode({
            'type': 'request_driver_location',
            'driver_id': 5,
            'request_id': 'uuid-here'
        }));

    Example - Respond to location request (Driver):
        ws.sink.add(jsonEncode({
            'type': 'location_response',
            'request_id': 'uuid-here',
            'requester_id': 1,
            'latitude': 33.5731,
            'longitude': -7.5898,
            'speed': 45.0,
            'heading': 180
        }));

    Example - Subscribe to specific model:
        ws.sink.add(jsonEncode({
            'type': 'subscribe_model_channel',
            'model': 'shuttle.vehicle.position'
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

                elif message_type == "subscribe_live_tracking":
                    # Subscribe to live tracking channel for real-time GPS updates
                    # This receives ALL position updates from ShuttleBee
                    await manager.subscribe_to_channel("live_tracking", user_id)
                    await websocket.send_json({
                        "type": "status",
                        "message": "Subscribed to live tracking",
                        "channel": "live_tracking",
                        "models": [
                            "shuttle.vehicle.position",
                            "shuttle.gps.position", 
                            "shuttle.trip"
                        ]
                    })

                elif message_type == "subscribe_model_channel":
                    # Subscribe to ALL events for a specific model
                    # Example: subscribe to all shuttle.vehicle.position creates
                    model = message.get("model")
                    if model:
                        channel = f"model:{model}"
                        await manager.subscribe_to_channel(channel, user_id)
                        await websocket.send_json({
                            "type": "status",
                            "message": f"Subscribed to all {model} events",
                            "channel": channel,
                            "model": model
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "model is required for subscribe_model_channel"
                        })

                elif message_type == "unsubscribe_model_channel":
                    # Unsubscribe from model channel
                    model = message.get("model")
                    if model:
                        channel = f"model:{model}"
                        await manager.unsubscribe_from_channel(channel, user_id)
                        await websocket.send_json({
                            "type": "status",
                            "message": f"Unsubscribed from {model} events",
                            "channel": channel
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "model is required"
                        })

                # ═══════════════════════════════════════════════════════════
                # ShuttleBee Live Tracking Commands
                # ═══════════════════════════════════════════════════════════

                elif message_type == "request_driver_location":
                    # Dispatcher requests driver's current location
                    # Used when trip is NOT ongoing (driver doesn't send automatically)
                    driver_id = message.get("driver_id")
                    request_id = message.get("request_id")
                    
                    if driver_id and request_id:
                        # Check if driver is connected
                        if driver_id in manager.active_connections:
                            # Send request to driver
                            await manager.send_personal_message({
                                "type": "request_location",
                                "request_id": request_id,
                                "requester_id": user_id,
                                "timestamp": datetime.now().isoformat()
                            }, driver_id)
                            
                            await websocket.send_json({
                                "type": "status",
                                "message": f"Location request sent to driver {driver_id}",
                                "request_id": request_id,
                                "driver_id": driver_id
                            })
                        else:
                            await websocket.send_json({
                                "type": "error",
                                "message": f"Driver {driver_id} is not connected",
                                "request_id": request_id,
                                "driver_id": driver_id
                            })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "driver_id and request_id are required"
                        })

                elif message_type == "location_response":
                    # Driver responds with current location
                    # Forward to the dispatcher who requested it
                    request_id = message.get("request_id")
                    requester_id = message.get("requester_id")
                    
                    if requester_id:
                        await manager.send_personal_message({
                            "type": "location_response",
                            "request_id": request_id,
                            "driver_id": user_id,
                            "latitude": message.get("latitude"),
                            "longitude": message.get("longitude"),
                            "speed": message.get("speed"),
                            "heading": message.get("heading"),
                            "accuracy": message.get("accuracy"),
                            "timestamp": message.get("timestamp") or datetime.now().isoformat()
                        }, requester_id)
                        
                        logger.info(f"Location response from driver {user_id} forwarded to {requester_id}")
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "requester_id is required in location_response"
                        })

                elif message_type == "driver_status_update":
                    # Driver updates their status (online, offline, busy, etc.)
                    status = message.get("status")  # online, offline, busy, available
                    vehicle_id = message.get("vehicle_id")
                    
                    if status:
                        # Broadcast to all live_tracking subscribers
                        await manager.broadcast_to_channel("live_tracking", {
                            "type": "driver_status",
                            "driver_id": user_id,
                            "status": status,
                            "vehicle_id": vehicle_id,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        await websocket.send_json({
                            "type": "status",
                            "message": f"Status updated to {status}"
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "status is required"
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


# ===== Conversation WebSocket Endpoints =====

async def authenticate_websocket_token(token: Optional[str]) -> tuple[int, int]:
    """
    Authenticate WebSocket connection via JWT token
    
    ⚠️ تصحيح أمني: authentication عبر token في query/header
    
    Returns:
        (user_id, partner_id) tuple
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token"
        )
    
    payload = decode_tenant_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # For now, we'll get partner_id later from Odoo
    # This is a simplified version - in production you might want to cache partner_id
    user_id = int(user_id_str) if user_id_str.isdigit() else hash(user_id_str) % 1000000
    partner_id = payload.get("partner_id")  # If included in token
    
    return user_id, partner_id or user_id  # Fallback to user_id if partner_id not available


@router.websocket("/ws/conversations")
async def websocket_conversations(
    websocket: WebSocket,
    token: Optional[str] = Query(None)  # ⚠️ تصحيح أمني: auth via token
):
    """
    WebSocket endpoint for real-time conversations
    
    ⚠️ تصحيح أمني مهم:
    1. لا نستخدم user_id في path (security risk)
    2. نستخرج user/partner من JWT token في query
    3. نستخدم connection-based subscriptions
    
    Usage:
        ws://host/ws/conversations?token=<jwt_token>
        
    Messages:
        {"action": "subscribe_channel", "channel_id": 123}
        {"action": "unsubscribe_channel", "channel_id": 123}
    """
    try:
        # Authenticate via token
        user_id, partner_id = await authenticate_websocket_token(token)
        
        await manager.connect(websocket, user_id)
        
        try:
            while True:
                data = await websocket.receive_json()
                action = data.get("action")
                
                if action == "subscribe_channel":
                    channel_id = data.get("channel_id")
                    if channel_id:
                        await manager.subscribe_to_conversation_channel(
                            websocket, user_id, partner_id, channel_id
                        )
                        await websocket.send_json({
                            "status": "subscribed",
                            "channel_id": channel_id
                        })
                
                elif action == "unsubscribe_channel":
                    channel_id = data.get("channel_id")
                    if channel_id:
                        await manager.unsubscribe_from_conversation_channel(
                            websocket, channel_id
                        )
                        await websocket.send_json({
                            "status": "unsubscribed",
                            "channel_id": channel_id
                        })
                
                else:
                    await websocket.send_json({
                        "status": "error",
                        "message": f"Unknown action: {action}"
                    })
                    
        except WebSocketDisconnect:
            manager.disconnect(websocket, user_id)
            logger.info(f"WebSocket disconnected for user {user_id}")
    except HTTPException as e:
        logger.warning(f"WebSocket authentication failed: {e.detail}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
