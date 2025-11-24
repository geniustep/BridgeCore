"""
Offline Sync Module

Complete offline-first synchronization system for BridgeCore
"""

from .schemas import (
    # Push schemas
    OfflinePushRequest,
    LocalChange,
    OfflinePushResponse,
    PushResult,

    # Pull schemas
    OfflinePullRequest,
    OfflinePullResponse,

    # Conflict resolution
    ConflictResolutionRequest,
    ConflictInfo,
    ConflictResolutionResponse,

    # Sync state
    SyncStateResponse,
    SyncStatistics,
)

from .service import OfflineSyncService
from .router import router

__all__ = [
    # Schemas
    "OfflinePushRequest",
    "LocalChange",
    "OfflinePushResponse",
    "PushResult",
    "OfflinePullRequest",
    "OfflinePullResponse",
    "ConflictResolutionRequest",
    "ConflictInfo",
    "ConflictResolutionResponse",
    "SyncStateResponse",
    "SyncStatistics",

    # Service
    "OfflineSyncService",

    # Router
    "router",
]
