# -*- coding: utf-8 -*-
"""
Odoo Sync Schemas - Pydantic models for Odoo sync operations
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class AppType(str, Enum):
    """Application types for sync filtering"""
    SALES_APP = "sales_app"
    DELIVERY_APP = "delivery_app"
    WAREHOUSE_APP = "warehouse_app"
    MANAGER_APP = "manager_app"
    MOBILE_APP = "mobile_app"


class Priority(str, Enum):
    """Event priority levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============================================================
# Request Schemas
# ============================================================

class OdooPullRequest(BaseModel):
    """Request to pull events from Odoo"""
    last_event_id: int = Field(default=0, description="Last event ID pulled")
    limit: int = Field(default=100, ge=1, le=1000, description="Max events to pull")
    models: Optional[List[str]] = Field(default=None, description="Filter by models")
    priority: Optional[Priority] = Field(default=None, description="Filter by priority")
    user_id: Optional[int] = Field(default=None, description="User ID for sync state")
    device_id: Optional[str] = Field(default=None, description="Device ID for sync state")
    app_type: Optional[AppType] = Field(default=None, description="App type for model filtering")

    class Config:
        use_enum_values = True


class OdooAckRequest(BaseModel):
    """Request to acknowledge processed events"""
    event_ids: List[int] = Field(..., min_items=1, description="Event IDs to acknowledge")


class SyncStateRequest(BaseModel):
    """Request to get or create sync state"""
    user_id: int = Field(..., description="User ID")
    device_id: str = Field(..., min_length=3, max_length=255, description="Device ID")
    app_type: AppType = Field(default=AppType.MOBILE_APP, description="App type")
    device_info: Optional[str] = Field(default=None, description="Device info")
    app_version: Optional[str] = Field(default=None, description="App version")

    class Config:
        use_enum_values = True


class SyncStateUpdateRequest(BaseModel):
    """Request to update sync state after pulling"""
    user_id: int = Field(..., description="User ID")
    device_id: str = Field(..., min_length=3, description="Device ID")
    last_event_id: int = Field(..., ge=0, description="Last event ID synced")
    events_synced: int = Field(default=0, ge=0, description="Number of events synced")


# ============================================================
# Response Schemas
# ============================================================

class OdooEvent(BaseModel):
    """Single event from Odoo update.webhook"""
    id: int
    model: str
    record_id: int
    event: str  # create, write, unlink
    timestamp: Optional[datetime] = None
    payload: Optional[Dict[str, Any]] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None


class OdooPullResponse(BaseModel):
    """Response from pulling Odoo events"""
    success: bool = True
    events: List[OdooEvent] = []
    last_id: int = 0
    has_more: bool = False
    count: int = 0
    timestamp: datetime = Field(default_factory=datetime.now)


class OdooAckResponse(BaseModel):
    """Response from acknowledging events"""
    success: bool = True
    processed_count: int = 0
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)


class SyncStateResponse(BaseModel):
    """Sync state for a user/device"""
    id: int
    user_id: int
    device_id: str
    app_type: str
    last_event_id: int = 0
    last_sync_time: Optional[datetime] = None
    sync_count: int = 0
    total_events_synced: int = 0
    is_active: bool = True
    device_info: Optional[str] = None
    app_version: Optional[str] = None


class SyncStateGetResponse(BaseModel):
    """Response for getting sync state"""
    success: bool = True
    sync_state: SyncStateResponse
    timestamp: datetime = Field(default_factory=datetime.now)


class SyncStatisticsDevice(BaseModel):
    """Device sync statistics"""
    device_id: str
    app_type: str
    last_sync_time: Optional[datetime] = None
    sync_count: int = 0
    total_events_synced: int = 0
    is_active: bool = True


class SyncStatisticsResponse(BaseModel):
    """Sync statistics response"""
    success: bool = True
    stats: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class OdooHealthResponse(BaseModel):
    """Odoo sync health check response"""
    status: str = "healthy"
    odoo_connected: bool = True
    pending_events: int = 0
    last_pull_time: Optional[datetime] = None
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.now)


class ModelByPriority(BaseModel):
    """Model statistics by priority"""
    model: str
    count: int
    processed: Optional[int] = None
    pending: Optional[int] = None


class OdooStatsResponse(BaseModel):
    """Statistics response from Odoo"""
    success: bool = True
    stats: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)

