"""
Pydantic schemas for webhook module
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


# ===== Webhook Event Schemas =====

class WebhookEventOut(BaseModel):
    """Webhook event output schema - Enhanced with new Odoo fields"""
    id: int
    model: str
    record_id: int
    event: Literal["create", "write", "unlink", "manual"]
    occurred_at: str  # ISO datetime string (timestamp field)

    # New fields from enhanced Odoo module
    priority: Optional[Literal["high", "medium", "low"]] = "medium"
    category: Optional[Literal["business", "system", "notification", "custom"]] = "business"
    status: Optional[Literal["pending", "processing", "sent", "failed", "dead"]] = "pending"

    retry_count: Optional[int] = 0
    max_retries: Optional[int] = 5
    next_retry_at: Optional[str] = None

    error_message: Optional[str] = None
    error_type: Optional[str] = None
    error_code: Optional[int] = None

    changed_fields: Optional[List[str]] = None
    payload: Optional[dict] = None

    subscriber_id: Optional[int] = None
    template_id: Optional[int] = None
    config_id: Optional[int] = None

    sent_at: Optional[str] = None
    response_code: Optional[int] = None
    processing_time: Optional[float] = None

    is_archived: Optional[bool] = False

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
    """Filter for GraphQL queries - Enhanced"""
    model: Optional[str] = None
    record_id: Optional[int] = None
    event: Optional[str] = None
    since: Optional[datetime] = None
    until: Optional[datetime] = None

    # New filters
    priority: Optional[Literal["high", "medium", "low"]] = None
    category: Optional[Literal["business", "system", "notification", "custom"]] = None
    status: Optional[Literal["pending", "processing", "sent", "failed", "dead"]] = None


# ===== Retry & Dead Letter Queue Schemas =====

class RetryEventRequest(BaseModel):
    """Request to retry failed event"""
    event_id: int
    force: bool = False  # Force retry even if max_retries reached


class BulkRetryRequest(BaseModel):
    """Request to retry multiple events"""
    event_ids: List[int]
    force: bool = False


class RetryResponse(BaseModel):
    """Response for retry operation"""
    success: bool
    event_id: int
    message: str
    new_status: str


class DeadLetterQueueStats(BaseModel):
    """Dead letter queue statistics"""
    total_events: int
    by_model: List[ModelCount]
    oldest_event: Optional[str] = None
    newest_event: Optional[str] = None


# ===== Webhook Config Schemas =====

class WebhookConfigOut(BaseModel):
    """Webhook configuration output"""
    id: int
    name: str
    model_name: str
    enabled: bool
    priority: Literal["high", "medium", "low"]
    category: Literal["business", "system", "notification", "custom"]
    events: List[str]
    batch_enabled: bool
    batch_size: Optional[int] = None


class WebhookSubscriberOut(BaseModel):
    """Webhook subscriber output"""
    id: int
    name: str
    endpoint_url: str
    enabled: bool
    auth_type: Literal["none", "basic", "bearer", "api_key"]
    timeout: int
    verify_ssl: bool
    success_rate: Optional[float] = None
    last_success_at: Optional[str] = None
    last_failure_at: Optional[str] = None


# ===== Statistics & Analytics Schemas =====

class EventStatistics(BaseModel):
    """Event statistics"""
    total_events: int
    by_status: dict
    by_priority: dict
    by_category: dict
    by_model: List[ModelCount]
    success_rate: float
    average_processing_time: float


class PerformanceMetrics(BaseModel):
    """Performance metrics"""
    events_per_second: float
    average_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate: float
