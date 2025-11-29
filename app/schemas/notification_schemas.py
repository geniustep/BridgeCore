"""
Notification schemas for API validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum


class NotificationTypeEnum(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SYSTEM = "system"


class NotificationPriorityEnum(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationChannelEnum(str, Enum):
    IN_APP = "in_app"
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"


# ============================================================================
# Request Schemas
# ============================================================================

class NotificationCreate(BaseModel):
    """Create a new notification (admin/system use)"""
    user_id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    type: NotificationTypeEnum = NotificationTypeEnum.INFO
    priority: NotificationPriorityEnum = NotificationPriorityEnum.NORMAL
    channels: List[NotificationChannelEnum] = [NotificationChannelEnum.IN_APP]
    action_type: Optional[str] = None
    action_data: Optional[Dict[str, Any]] = None
    related_model: Optional[str] = None
    related_id: Optional[int] = None
    extra_data: Optional[Dict[str, Any]] = None  # Renamed from metadata to avoid SQLAlchemy conflict
    expires_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "New Order Received",
                "message": "Order SO123 has been received and is awaiting confirmation",
                "type": "info",
                "priority": "normal",
                "channels": ["in_app", "push"],
                "action_type": "navigate",
                "action_data": {"route": "/orders/123"},
                "related_model": "sale.order",
                "related_id": 123
            }
        }


class NotificationBulkCreate(BaseModel):
    """Create notifications for multiple users"""
    user_ids: List[UUID]
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    type: NotificationTypeEnum = NotificationTypeEnum.INFO
    priority: NotificationPriorityEnum = NotificationPriorityEnum.NORMAL
    channels: List[NotificationChannelEnum] = [NotificationChannelEnum.IN_APP]
    action_type: Optional[str] = None
    action_data: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None


class NotificationMarkRead(BaseModel):
    """Mark notifications as read"""
    notification_ids: List[UUID]


class NotificationPreferenceUpdate(BaseModel):
    """Update notification preferences"""
    enable_in_app: Optional[bool] = None
    enable_push: Optional[bool] = None
    enable_email: Optional[bool] = None
    enable_sms: Optional[bool] = None
    receive_info: Optional[bool] = None
    receive_success: Optional[bool] = None
    receive_warning: Optional[bool] = None
    receive_error: Optional[bool] = None
    receive_system: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_timezone: Optional[str] = None
    email_digest_enabled: Optional[bool] = None
    email_digest_frequency: Optional[str] = Field(None, pattern=r"^(daily|weekly)$")


class DeviceTokenRegister(BaseModel):
    """Register a device for push notifications"""
    device_id: str = Field(..., min_length=1, max_length=255)
    device_name: Optional[str] = Field(None, max_length=255)
    device_type: str = Field(..., pattern=r"^(ios|android|web)$")
    token: str = Field(..., min_length=1)
    token_type: str = Field(default="fcm", pattern=r"^(fcm|apns|web_push)$")
    app_version: Optional[str] = None
    os_version: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "device-abc-123",
                "device_name": "iPhone 15 Pro",
                "device_type": "ios",
                "token": "fcm-token-here...",
                "token_type": "fcm",
                "app_version": "2.1.0",
                "os_version": "17.0"
            }
        }


class DeviceTokenUnregister(BaseModel):
    """Unregister a device"""
    device_id: str


# ============================================================================
# Response Schemas
# ============================================================================

class NotificationResponse(BaseModel):
    """Notification response"""
    id: UUID
    tenant_id: UUID
    user_id: UUID
    title: str
    message: str
    type: NotificationTypeEnum
    priority: NotificationPriorityEnum
    channels: List[str]
    is_read: bool
    read_at: Optional[datetime]
    action_type: Optional[str]
    action_data: Optional[Dict[str, Any]]
    related_model: Optional[str]
    related_id: Optional[int]
    extra_data: Optional[Dict[str, Any]]  # Renamed from metadata to avoid SQLAlchemy conflict
    expires_at: Optional[datetime]
    source: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """List of notifications response"""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    skip: int
    limit: int


class NotificationPreferenceResponse(BaseModel):
    """Notification preferences response"""
    id: UUID
    user_id: UUID
    enable_in_app: bool
    enable_push: bool
    enable_email: bool
    enable_sms: bool
    receive_info: bool
    receive_success: bool
    receive_warning: bool
    receive_error: bool
    receive_system: bool
    quiet_hours_enabled: bool
    quiet_hours_start: Optional[str]
    quiet_hours_end: Optional[str]
    quiet_hours_timezone: str
    email_digest_enabled: bool
    email_digest_frequency: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class DeviceTokenResponse(BaseModel):
    """Device token response"""
    id: UUID
    device_id: str
    device_name: Optional[str]
    device_type: str
    token_type: str
    is_active: bool
    last_used_at: Optional[datetime]
    app_version: Optional[str]
    os_version: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DeviceTokenListResponse(BaseModel):
    """List of device tokens response"""
    devices: List[DeviceTokenResponse]
    total: int


class NotificationStatsResponse(BaseModel):
    """Notification statistics"""
    total_notifications: int
    unread_count: int
    read_count: int
    notifications_today: int
    notifications_this_week: int
    by_type: Dict[str, int]
    by_priority: Dict[str, int]


class BulkNotificationResult(BaseModel):
    """Result of bulk notification creation"""
    success: bool
    created_count: int
    failed_count: int
    notification_ids: List[UUID]

