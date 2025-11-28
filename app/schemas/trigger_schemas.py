"""
Trigger schemas for API validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum


class TriggerEventEnum(str, Enum):
    ON_CREATE = "on_create"
    ON_UPDATE = "on_update"
    ON_DELETE = "on_delete"
    ON_WORKFLOW = "on_workflow"
    SCHEDULED = "scheduled"
    MANUAL = "manual"


class TriggerActionTypeEnum(str, Enum):
    WEBHOOK = "webhook"
    EMAIL = "email"
    NOTIFICATION = "notification"
    ODOO_METHOD = "odoo_method"
    CUSTOM_CODE = "custom_code"


class TriggerStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


# ============================================================================
# Request Schemas
# ============================================================================

class TriggerCreate(BaseModel):
    """Create a new trigger"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    model: str = Field(..., min_length=1, max_length=255, description="Odoo model name")
    event: TriggerEventEnum
    condition: Optional[List[Any]] = Field(default=[], description="Odoo domain filter")
    action_type: TriggerActionTypeEnum
    action_config: Dict[str, Any] = Field(..., description="Action configuration")
    schedule_cron: Optional[str] = Field(None, description="Cron expression for scheduled triggers")
    schedule_timezone: Optional[str] = "UTC"
    is_enabled: bool = True
    priority: int = Field(default=10, ge=1, le=100)
    max_executions_per_hour: int = Field(default=100, ge=1, le=10000)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Notify on New Sale Order",
                "description": "Send notification when a new sale order is created",
                "model": "sale.order",
                "event": "on_create",
                "condition": [["state", "=", "draft"]],
                "action_type": "notification",
                "action_config": {
                    "title": "New Sale Order",
                    "message": "Sale order {{record.name}} has been created"
                },
                "is_enabled": True,
                "priority": 10
            }
        }


class TriggerUpdate(BaseModel):
    """Update an existing trigger"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    model: Optional[str] = Field(None, min_length=1, max_length=255)
    event: Optional[TriggerEventEnum] = None
    condition: Optional[List[Any]] = None
    action_type: Optional[TriggerActionTypeEnum] = None
    action_config: Optional[Dict[str, Any]] = None
    schedule_cron: Optional[str] = None
    schedule_timezone: Optional[str] = None
    is_enabled: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=100)
    max_executions_per_hour: Optional[int] = Field(None, ge=1, le=10000)


class TriggerToggle(BaseModel):
    """Toggle trigger enabled status"""
    is_enabled: bool


class TriggerExecuteManual(BaseModel):
    """Manually execute a trigger"""
    record_ids: Optional[List[int]] = Field(None, description="Specific record IDs to process")
    test_mode: bool = Field(default=False, description="Execute without actually performing actions")


# ============================================================================
# Response Schemas
# ============================================================================

class TriggerResponse(BaseModel):
    """Trigger response"""
    id: UUID
    name: str
    description: Optional[str]
    tenant_id: UUID
    model: str
    event: TriggerEventEnum
    condition: List[Any]
    action_type: TriggerActionTypeEnum
    action_config: Dict[str, Any]
    schedule_cron: Optional[str]
    schedule_timezone: str
    next_run_at: Optional[datetime]
    last_run_at: Optional[datetime]
    status: TriggerStatusEnum
    is_enabled: bool
    priority: int
    execution_count: int
    success_count: int
    failure_count: int
    last_error: Optional[str]
    last_error_at: Optional[datetime]
    max_executions_per_hour: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class TriggerListResponse(BaseModel):
    """List of triggers response"""
    triggers: List[TriggerResponse]
    total: int
    skip: int
    limit: int


class TriggerExecutionResponse(BaseModel):
    """Trigger execution response"""
    id: UUID
    trigger_id: UUID
    tenant_id: UUID
    record_id: Optional[int]
    record_data: Optional[Dict[str, Any]]
    success: bool
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class TriggerExecutionListResponse(BaseModel):
    """List of trigger executions response"""
    executions: List[TriggerExecutionResponse]
    total: int
    skip: int
    limit: int


class TriggerStatsResponse(BaseModel):
    """Trigger statistics response"""
    trigger_id: UUID
    name: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    avg_duration_ms: Optional[float]
    last_execution: Optional[datetime]
    executions_today: int
    executions_this_week: int


class ManualExecutionResult(BaseModel):
    """Result of manual trigger execution"""
    success: bool
    message: str
    executed_count: int
    results: List[Dict[str, Any]]

