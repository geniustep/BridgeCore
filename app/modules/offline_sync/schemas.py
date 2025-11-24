"""
Offline Sync Schemas

Pydantic schemas for offline-first synchronization
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
from enum import Enum


# ===== Enums =====

class SyncAction(str, Enum):
    """Sync action types"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    READ = "read"


class ConflictStrategy(str, Enum):
    """Conflict resolution strategies"""
    SERVER_WINS = "server_wins"
    CLIENT_WINS = "client_wins"
    MANUAL = "manual"
    MERGE = "merge"
    NEWEST_WINS = "newest_wins"


class SyncStatus(str, Enum):
    """Sync operation status"""
    SUCCESS = "success"
    FAILED = "failed"
    CONFLICT = "conflict"
    PARTIAL = "partial"
    PENDING = "pending"


# ===== Push Schemas (Upload Local Changes) =====

class LocalChange(BaseModel):
    """Single local change from offline client"""
    local_id: str = Field(..., description="Client-side unique ID (UUID)")
    action: SyncAction = Field(..., description="Action type: create, update, delete")
    model: str = Field(..., description="Odoo model name")
    record_id: Optional[int] = Field(None, description="Server record ID (null for new records)")
    data: Dict[str, Any] = Field(default_factory=dict, description="Record data")
    local_timestamp: str = Field(..., description="ISO datetime when change was made locally")
    fields_changed: Optional[List[str]] = Field(None, description="List of changed fields")
    version: int = Field(1, description="Record version for optimistic locking")

    # Metadata
    priority: int = Field(0, ge=0, le=10, description="Priority (0=lowest, 10=highest)")
    dependencies: Optional[List[str]] = Field(None, description="List of dependent local_ids")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('local_id')
    def validate_local_id(cls, v):
        if not v or len(v) < 3:
            raise ValueError("local_id must be at least 3 characters")
        return v


class OfflinePushRequest(BaseModel):
    """Request to push local changes to server"""
    device_id: str = Field(..., min_length=3, description="Unique device identifier")
    changes: List[LocalChange] = Field(..., description="List of local changes")
    conflict_strategy: ConflictStrategy = Field(
        ConflictStrategy.SERVER_WINS,
        description="Default conflict resolution strategy"
    )
    stop_on_error: bool = Field(
        False,
        description="Stop processing on first error"
    )

    # Batch settings
    batch_size: int = Field(50, ge=1, le=500, description="Batch size for processing")

    # Sync metadata
    last_pull_timestamp: Optional[str] = Field(None, description="Last successful pull timestamp")
    app_version: Optional[str] = Field(None, description="Client app version")

    @validator('changes')
    def validate_changes(cls, v):
        if not v:
            raise ValueError("changes cannot be empty")
        if len(v) > 1000:
            raise ValueError("Too many changes (max 1000 per request)")
        return v


class PushResult(BaseModel):
    """Result of pushing a single change"""
    local_id: str
    status: SyncStatus
    action: SyncAction
    model: str

    # Success case
    server_id: Optional[int] = None
    server_timestamp: Optional[str] = None

    # Error case
    error: Optional[str] = None
    error_code: Optional[str] = None

    # Conflict case
    conflict_info: Optional[Dict[str, Any]] = None

    # Performance
    processing_time_ms: Optional[float] = None


class OfflinePushResponse(BaseModel):
    """Response after pushing local changes"""
    success: bool
    total: int
    succeeded: int
    failed: int
    conflicts: int

    results: List[PushResult]

    # ID mapping (local_id -> server_id)
    id_mapping: Dict[str, int] = Field(default_factory=dict)

    # Next sync token
    next_sync_token: Optional[str] = None

    # Server timestamp
    server_timestamp: str

    # Statistics
    total_processing_time_ms: float
    average_processing_time_ms: float


# ===== Pull Schemas (Download Server Changes) =====

class OfflinePullRequest(BaseModel):
    """Request to pull server changes"""
    device_id: str = Field(..., min_length=3, description="Unique device identifier")
    app_type: str = Field(..., description="App type for model filtering")

    # Sync state
    last_sync_token: Optional[str] = Field(None, description="Last sync token from previous pull")
    last_event_id: Optional[int] = Field(None, description="Last event ID received")

    # Filtering
    models_filter: Optional[List[str]] = Field(None, description="Filter by specific models")
    priority_filter: Optional[List[str]] = Field(None, description="Filter by priority (high, medium, low)")

    # Pagination
    limit: int = Field(100, ge=1, le=500, description="Max events to fetch")
    offset: int = Field(0, ge=0, description="Offset for pagination")

    # Options
    include_payload: bool = Field(True, description="Include full record data")
    include_metadata: bool = Field(False, description="Include sync metadata")


class ServerChange(BaseModel):
    """Single server change"""
    event_id: int
    model: str
    record_id: int
    action: str  # create, write, unlink
    timestamp: str

    # Data
    data: Optional[Dict[str, Any]] = None
    changed_fields: Optional[List[str]] = None

    # Metadata
    priority: Optional[str] = None
    category: Optional[str] = None
    user_id: Optional[int] = None

    # Version info
    version: Optional[int] = None


class OfflinePullResponse(BaseModel):
    """Response with server changes"""
    success: bool
    has_updates: bool
    new_events_count: int

    events: List[ServerChange]

    # Sync state
    next_sync_token: str
    last_event_id: int
    last_sync_time: str

    # Pagination
    has_more: bool
    total_available: Optional[int] = None

    # Server info
    server_timestamp: str
    server_version: Optional[str] = None


# ===== Conflict Resolution Schemas =====

class ConflictInfo(BaseModel):
    """Conflict information"""
    local_id: str
    server_id: int
    model: str

    # Conflicting data
    local_data: Dict[str, Any]
    server_data: Dict[str, Any]

    # Timestamps
    local_timestamp: str
    server_timestamp: str

    # Versions
    local_version: int
    server_version: int

    # Conflicting fields
    conflicting_fields: List[str]

    # Suggested resolution
    suggested_strategy: ConflictStrategy


class ConflictResolutionRequest(BaseModel):
    """Request to resolve conflicts"""
    device_id: str
    conflicts: List[Dict[str, Any]] = Field(..., description="List of conflicts to resolve")

    class ConflictResolution(BaseModel):
        local_id: str
        strategy: ConflictStrategy
        merged_data: Optional[Dict[str, Any]] = None  # For merge strategy

    resolutions: List[ConflictResolution]


class ConflictResolutionResponse(BaseModel):
    """Response after resolving conflicts"""
    success: bool
    resolved: int
    failed: int

    results: List[PushResult]


# ===== Sync State Schemas =====

class SyncStateResponse(BaseModel):
    """Current sync state for a device"""
    device_id: str
    user_id: int

    # Sync state
    last_event_id: int
    last_sync_time: str
    next_sync_token: str

    # Statistics
    total_syncs: int
    total_events_synced: int
    last_push_time: Optional[str] = None
    last_pull_time: Optional[str] = None

    # Status
    sync_status: str  # idle, syncing, error
    pending_changes: int

    # App info
    app_type: str
    app_version: Optional[str] = None


class SyncStatistics(BaseModel):
    """Sync statistics"""
    device_id: str

    # Overall stats
    total_syncs: int
    total_events_synced: int
    total_conflicts: int

    # Success rate
    success_rate: float
    conflict_rate: float

    # Performance
    average_sync_time_ms: float
    average_push_time_ms: float
    average_pull_time_ms: float

    # Last sync
    last_sync_time: str
    last_sync_status: str

    # Data volume
    total_data_uploaded_kb: float
    total_data_downloaded_kb: float


# ===== Full Sync Schema =====

class FullSyncRequest(BaseModel):
    """Request full sync (reset and sync everything)"""
    device_id: str
    app_type: str

    # Options
    clear_local_changes: bool = Field(
        False,
        description="Clear pending local changes before sync"
    )
    include_archived: bool = Field(
        False,
        description="Include archived records"
    )


class FullSyncResponse(BaseModel):
    """Response for full sync"""
    success: bool

    # Stats
    total_records: int
    total_models: int

    # Data by model
    records_by_model: Dict[str, int]

    # Sync state
    next_sync_token: str
    last_event_id: int

    # Timing
    sync_duration_ms: float
    server_timestamp: str


# ===== Batch Sync Schema (Enhanced) =====

class BatchSyncOperation(BaseModel):
    """Single operation in batch sync"""
    operation_id: str = Field(..., description="Client-side operation ID")
    action: SyncAction
    model: str
    record_id: Optional[int] = None
    data: Dict[str, Any] = Field(default_factory=dict)

    # Dependencies
    depends_on: Optional[List[str]] = Field(None, description="List of operation_ids this depends on")


class BatchSyncRequest(BaseModel):
    """Batch sync request with dependency resolution"""
    device_id: str
    operations: List[BatchSyncOperation]

    # Options
    resolve_dependencies: bool = Field(True, description="Automatically resolve dependencies")
    stop_on_error: bool = Field(False)
    conflict_strategy: ConflictStrategy = ConflictStrategy.SERVER_WINS


class BatchSyncResponse(BaseModel):
    """Response for batch sync"""
    success: bool
    total: int
    succeeded: int
    failed: int
    skipped: int  # Due to dependency failures

    results: List[PushResult]

    # Execution order (after dependency resolution)
    execution_order: List[str]

    # ID mapping
    id_mapping: Dict[str, int]


# ===== Health Check Schema =====

class OfflineSyncHealth(BaseModel):
    """Health check for offline sync system"""
    status: str  # healthy, degraded, unhealthy

    # Component status
    database: str
    cache: str
    odoo_connection: str

    # Metrics
    active_devices: int
    pending_syncs: int
    recent_errors: int

    # Performance
    average_response_time_ms: float
    sync_queue_size: int


# ===== Webhook Integration Schemas =====

class WebhookSyncEvent(BaseModel):
    """Webhook event for sync notification"""
    device_id: str
    event_type: Literal["new_changes", "conflict_detected", "sync_required"]

    # Event data
    event_count: int
    models_affected: List[str]
    priority: str

    # Timestamps
    timestamp: str
