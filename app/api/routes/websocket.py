"""
WebSocket Support for Real-Time Updates

Provides real-time notifications for:
- System connection status changes
- Long-running operation progress
- Audit log events
- Cache invalidation
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
from loguru import logger
import json
import asyncio


router = APIRouter()


class ConnectionManager:
    """
    Manage WebSocket connections

    Features:
    - User-based connection tracking
    - Broadcast to all connections
    - Broadcast to specific user
    - Channel-based subscriptions
    """

    def __init__(self):
        # user_id -> Set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}

        # channel -> Set of user_ids subscribed
        self.channel_subscriptions: Dict[str, Set[int]] = {}

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
