"""
Webhook Module - Real-time change tracking from Odoo

This module provides:
- Webhook event handling and querying
- Smart multi-user sync
- Real-time notifications via WebSocket
- GraphQL API for flexible queries
"""

from app.modules.webhook.service import WebhookService
from app.modules.webhook.schemas import (
    WebhookEventOut,
    EventsResponse,
    SyncRequest,
    SyncResponse
)

__all__ = [
    "WebhookService",
    "WebhookEventOut",
    "EventsResponse",
    "SyncRequest",
    "SyncResponse"
]
