"""
Pydantic schemas for webhook module
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


# ===== Webhook Event Schemas =====

class WebhookEventOut(BaseModel):
    """Webhook event output schema"""
    id: int
    model: str
    record_id: int
    event: Literal["create", "write", "unlink", "manual"]
    occurred_at: str  # ISO datetime string

    class Config:
        from_attributes = True


class EventsResponse(BaseModel):
    """Response for events listing"""
    status: str = "success"
    count: int
    data: List[WebhookEventOut]


# ===== Smart Sync Schemas =====

class SyncRequest(BaseModel):
    """Smart sync request from mobile app"""
    user_id: int = Field(..., description="Odoo user ID")
    device_id: str = Field(..., min_length=1, max_length=255, description="Unique device identifier")
    app_type: str = Field(..., description="App type: sales_app, delivery_app, manager_app, etc.")
    models_filter: Optional[List[str]] = Field(None, description="Optional: filter by specific models")
    limit: int = Field(100, ge=1, le=500, description="Max events to fetch")


class EventData(BaseModel):
    """Event data in sync response"""
    id: int
    model: str
    record_id: int
    event: str
    timestamp: str


class SyncResponse(BaseModel):
    """Smart sync response"""
    status: str = "success"
    has_updates: bool
    new_events_count: int
    events: List[EventData]
    next_sync_token: str
    last_sync_time: str


class SyncStatsResponse(BaseModel):
    """Sync state statistics"""
    user_id: int
    device_id: str
    last_event_id: int
    last_sync_time: str
    sync_count: int
    is_active: bool


# ===== Update Summary Schemas =====

class ModelCount(BaseModel):
    """Model change count"""
    model: str
    count: int


class CheckUpdatesOut(BaseModel):
    """Check updates response"""
    has_update: bool
    last_update_at: Optional[str] = None
    summary: List[ModelCount]


# ===== Cleanup Schema =====

class CleanupResponse(BaseModel):
    """Cleanup operation response"""
    ok: bool
    deleted: int
    message: Optional[str] = None


# ===== WebSocket Message Schemas =====

class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    type: Literal["event", "sync_update", "error", "ping", "pong"]
    data: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WebSocketAuth(BaseModel):
    """WebSocket authentication"""
    token: str
    user_id: Optional[int] = None
    subscribe_to: Optional[List[str]] = None  # List of models to subscribe


# ===== GraphQL Input Types =====

class WebhookEventFilter(BaseModel):
    """Filter for GraphQL queries"""
    model: Optional[str] = None
    record_id: Optional[int] = None
    event: Optional[str] = None
    since: Optional[datetime] = None
    until: Optional[datetime] = None
