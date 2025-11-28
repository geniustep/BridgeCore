"""
Notification model for push notifications and in-app notifications
"""
from sqlalchemy import Column, String, Boolean, DateTime, Enum, Integer, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from app.db.base import Base, TimestampMixin


class NotificationType(str, enum.Enum):
    """Notification types"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SYSTEM = "system"


class NotificationPriority(str, enum.Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationChannel(str, enum.Enum):
    """Notification delivery channels"""
    IN_APP = "in_app"
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"


class Notification(Base, TimestampMixin):
    """User notifications"""

    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Associations
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("tenant_users.id"), nullable=False, index=True)

    # Notification Content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Type & Priority
    type = Column(Enum(NotificationType), default=NotificationType.INFO, nullable=False)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.NORMAL, nullable=False)
    
    # Delivery
    channels = Column(JSON, default=["in_app"])  # List of NotificationChannel values
    
    # Status
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)
    
    # Action (optional - for clickable notifications)
    action_type = Column(String(50), nullable=True)  # e.g., "navigate", "open_url", "execute"
    action_data = Column(JSON, nullable=True)
    """
    action_data examples:
    
    For navigate:
    {
        "route": "/orders/123",
        "params": {"id": 123}
    }
    
    For open_url:
    {
        "url": "https://example.com/doc"
    }
    
    For execute:
    {
        "method": "refresh_data"
    }
    """

    # Related Entity (optional)
    related_model = Column(String(255), nullable=True)  # e.g., "sale.order"
    related_id = Column(Integer, nullable=True)  # Odoo record ID
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Expiration
    expires_at = Column(DateTime, nullable=True)
    
    # Source
    source = Column(String(100), nullable=True)  # e.g., "trigger", "system", "admin"
    source_id = Column(UUID(as_uuid=True), nullable=True)  # e.g., trigger_id

    # Relationships
    tenant = relationship("Tenant", backref="notifications")
    user = relationship("TenantUser", backref="notifications")

    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, title='{self.title}', is_read={self.is_read})>"


class NotificationPreference(Base, TimestampMixin):
    """User notification preferences"""

    __tablename__ = "notification_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # User Association
    user_id = Column(UUID(as_uuid=True), ForeignKey("tenant_users.id"), nullable=False, unique=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Channel Preferences
    enable_in_app = Column(Boolean, default=True, nullable=False)
    enable_push = Column(Boolean, default=True, nullable=False)
    enable_email = Column(Boolean, default=True, nullable=False)
    enable_sms = Column(Boolean, default=False, nullable=False)

    # Type Preferences (which notification types to receive)
    receive_info = Column(Boolean, default=True, nullable=False)
    receive_success = Column(Boolean, default=True, nullable=False)
    receive_warning = Column(Boolean, default=True, nullable=False)
    receive_error = Column(Boolean, default=True, nullable=False)
    receive_system = Column(Boolean, default=True, nullable=False)

    # Quiet Hours
    quiet_hours_enabled = Column(Boolean, default=False, nullable=False)
    quiet_hours_start = Column(String(5), nullable=True)  # HH:MM format
    quiet_hours_end = Column(String(5), nullable=True)    # HH:MM format
    quiet_hours_timezone = Column(String(50), default="UTC")

    # Email Digest
    email_digest_enabled = Column(Boolean, default=False, nullable=False)
    email_digest_frequency = Column(String(20), default="daily")  # daily, weekly

    # Relationships
    user = relationship("TenantUser", backref="notification_preference")

    def __repr__(self):
        return f"<NotificationPreference(id={self.id}, user_id={self.user_id})>"


class DeviceToken(Base, TimestampMixin):
    """Push notification device tokens"""

    __tablename__ = "device_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # User Association
    user_id = Column(UUID(as_uuid=True), ForeignKey("tenant_users.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Device Info
    device_id = Column(String(255), nullable=False, index=True)
    device_name = Column(String(255), nullable=True)
    device_type = Column(String(50), nullable=False)  # ios, android, web
    
    # Token
    token = Column(Text, nullable=False)
    token_type = Column(String(50), default="fcm")  # fcm, apns, web_push
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    
    # App Info
    app_version = Column(String(50), nullable=True)
    os_version = Column(String(50), nullable=True)

    # Relationships
    user = relationship("TenantUser", backref="device_tokens")

    def __repr__(self):
        return f"<DeviceToken(id={self.id}, user_id={self.user_id}, device_type='{self.device_type}')>"

