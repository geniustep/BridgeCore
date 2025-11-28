"""
Trigger model for automation system
"""
from sqlalchemy import Column, String, Boolean, DateTime, Enum, Integer, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from app.db.base import Base, TimestampMixin


class TriggerEvent(str, enum.Enum):
    """Trigger event types"""
    ON_CREATE = "on_create"
    ON_UPDATE = "on_update"
    ON_DELETE = "on_delete"
    ON_WORKFLOW = "on_workflow"
    SCHEDULED = "scheduled"
    MANUAL = "manual"


class TriggerActionType(str, enum.Enum):
    """Trigger action types"""
    WEBHOOK = "webhook"
    EMAIL = "email"
    NOTIFICATION = "notification"
    ODOO_METHOD = "odoo_method"
    CUSTOM_CODE = "custom_code"


class TriggerStatus(str, enum.Enum):
    """Trigger status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class Trigger(Base, TimestampMixin):
    """Automation triggers for Odoo events"""

    __tablename__ = "triggers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Basic Info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Tenant Association
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Trigger Configuration
    model = Column(String(255), nullable=False, index=True)  # Odoo model name
    event = Column(Enum(TriggerEvent), nullable=False, index=True)
    
    # Condition (domain filter as JSON)
    condition = Column(JSON, nullable=True, default=list)  # Odoo domain format
    
    # Action Configuration
    action_type = Column(Enum(TriggerActionType), nullable=False)
    action_config = Column(JSON, nullable=False, default=dict)
    """
    action_config examples:
    
    For WEBHOOK:
    {
        "url": "https://api.example.com/webhook",
        "method": "POST",
        "headers": {"Authorization": "Bearer xxx"},
        "payload_template": "{{record}}"
    }
    
    For EMAIL:
    {
        "to": ["admin@example.com"],
        "subject": "New record created: {{record.name}}",
        "body_template": "Record details: {{record}}"
    }
    
    For NOTIFICATION:
    {
        "user_ids": [1, 2, 3],
        "title": "New record",
        "message": "{{record.name}} has been created"
    }
    
    For ODOO_METHOD:
    {
        "method": "action_confirm",
        "args": [],
        "kwargs": {}
    }
    """

    # Scheduling (for SCHEDULED events)
    schedule_cron = Column(String(100), nullable=True)  # Cron expression
    schedule_timezone = Column(String(50), default="UTC")
    next_run_at = Column(DateTime, nullable=True)
    last_run_at = Column(DateTime, nullable=True)

    # Status & Metrics
    status = Column(Enum(TriggerStatus), default=TriggerStatus.ACTIVE, nullable=False, index=True)
    is_enabled = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=10, nullable=False)  # Lower = higher priority
    
    # Execution Metrics
    execution_count = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)
    last_error_at = Column(DateTime, nullable=True)

    # Rate Limiting
    max_executions_per_hour = Column(Integer, default=100)
    current_hour_executions = Column(Integer, default=0)

    # Relationships
    tenant = relationship("Tenant", backref="triggers")
    executions = relationship("TriggerExecution", back_populates="trigger", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Trigger(id={self.id}, name='{self.name}', model='{self.model}', event='{self.event}')>"


class TriggerExecution(Base, TimestampMixin):
    """Trigger execution history"""

    __tablename__ = "trigger_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    trigger_id = Column(UUID(as_uuid=True), ForeignKey("triggers.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Execution Details
    record_id = Column(Integer, nullable=True)  # Odoo record ID
    record_data = Column(JSON, nullable=True)  # Snapshot of record data
    
    # Result
    success = Column(Boolean, nullable=False)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timing
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)

    # Relationships
    trigger = relationship("Trigger", back_populates="executions")

    def __repr__(self):
        return f"<TriggerExecution(id={self.id}, trigger_id={self.trigger_id}, success={self.success})>"

