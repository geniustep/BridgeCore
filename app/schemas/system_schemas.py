"""
Schemas for multi-system architecture
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class SystemTypeEnum(str, Enum):
    """Supported system types"""
    ODOO = "odoo"
    MOODLE = "moodle"
    SAP = "sap"
    SALESFORCE = "salesforce"
    DYNAMICS = "dynamics"
    CUSTOM = "custom"


class SystemStatusEnum(str, Enum):
    """System status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    TESTING = "testing"


# ============= External System Schemas =============

class ExternalSystemBase(BaseModel):
    """Base external system schema"""
    system_type: SystemTypeEnum
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    version: Optional[str] = None
    status: SystemStatusEnum = SystemStatusEnum.ACTIVE
    is_enabled: bool = True
    default_config: Optional[Dict[str, Any]] = None
    capabilities: Dict[str, Any] = Field(default_factory=dict)


class ExternalSystemCreate(ExternalSystemBase):
    """Schema for creating external system"""
    pass


class ExternalSystemUpdate(BaseModel):
    """Schema for updating external system"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    version: Optional[str] = None
    status: Optional[SystemStatusEnum] = None
    is_enabled: Optional[bool] = None
    default_config: Optional[Dict[str, Any]] = None
    capabilities: Optional[Dict[str, Any]] = None


class ExternalSystemResponse(ExternalSystemBase):
    """Schema for external system response"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============= Tenant System Connection Schemas =============

class TenantSystemBase(BaseModel):
    """Base tenant system connection schema"""
    tenant_id: UUID
    system_id: UUID
    connection_config: Dict[str, Any] = Field(
        ...,
        description="System-specific connection configuration (encrypted)"
    )
    is_active: bool = True
    is_primary: bool = False
    custom_config: Optional[Dict[str, Any]] = None


class TenantSystemCreate(TenantSystemBase):
    """Schema for creating tenant system connection"""

    @validator('connection_config')
    def validate_connection_config(cls, v, values):
        """Validate connection config based on system type"""
        # Basic validation - actual validation should be done by adapter
        if not isinstance(v, dict):
            raise ValueError("connection_config must be a dictionary")
        return v


class TenantSystemUpdate(BaseModel):
    """Schema for updating tenant system connection"""
    connection_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_primary: Optional[bool] = None
    custom_config: Optional[Dict[str, Any]] = None


class TenantSystemResponse(TenantSystemBase):
    """Schema for tenant system response"""
    id: UUID
    last_connection_test: Optional[datetime] = None
    last_successful_connection: Optional[datetime] = None
    connection_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Nested system info
    external_system: Optional[ExternalSystemResponse] = None

    class Config:
        from_attributes = True


class TenantSystemWithDetails(TenantSystemResponse):
    """Extended schema with full system details"""
    pass


# ============= Connection Test Schemas =============

class ConnectionTestRequest(BaseModel):
    """Schema for connection test request"""
    system_type: SystemTypeEnum
    connection_config: Dict[str, Any]


class ConnectionTestResponse(BaseModel):
    """Schema for connection test response"""
    success: bool
    message: str
    system_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    tested_at: datetime = Field(default_factory=datetime.utcnow)


# ============= Odoo-specific Schemas =============

class OdooConnectionConfig(BaseModel):
    """Odoo connection configuration"""
    url: str = Field(..., description="Odoo instance URL")
    database: str = Field(..., description="Odoo database name")
    username: str = Field(..., description="Odoo username")
    password: str = Field(..., description="Odoo password (will be encrypted)")


# ============= Moodle-specific Schemas =============

class MoodleConnectionConfig(BaseModel):
    """Moodle connection configuration"""
    url: str = Field(..., description="Moodle instance URL")
    token: str = Field(..., description="Web Services token (will be encrypted)")
    service: str = Field(default="moodle_mobile_app", description="Moodle service name")


# ============= System List Schemas =============

class SystemListResponse(BaseModel):
    """Response for listing systems"""
    systems: List[ExternalSystemResponse]
    total: int


class TenantSystemListResponse(BaseModel):
    """Response for listing tenant systems"""
    connections: List[TenantSystemResponse]
    total: int


# ============= Helper Schemas =============

class SystemCapabilities(BaseModel):
    """System capabilities"""
    crud: bool = True
    search: bool = True
    webhooks: bool = False
    batch: bool = False
    realtime_sync: bool = False
    # Moodle-specific
    courses: Optional[bool] = None
    users: Optional[bool] = None
    grades: Optional[bool] = None
