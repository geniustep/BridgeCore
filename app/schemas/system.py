"""
System operation Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class SystemBase(BaseModel):
    """Base system schema"""
    system_id: str = Field(..., description="Unique system identifier")
    system_type: str = Field(..., description="System type (odoo, sap, etc.)")
    system_version: Optional[str] = Field(None, description="System version")
    name: str = Field(..., description="System display name")
    description: Optional[str] = None
    is_active: bool = True


class SystemCreate(SystemBase):
    """System creation schema"""
    connection_config: Dict[str, Any] = Field(..., description="Connection configuration")


class SystemUpdate(BaseModel):
    """System update schema"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    connection_config: Optional[Dict[str, Any]] = None


class SystemResponse(SystemBase):
    """System response schema"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CRUDRequest(BaseModel):
    """Generic CRUD request schema"""
    model: str = Field(..., description="Model/entity name")
    data: Optional[Dict[str, Any]] = Field(None, description="Data for create/update")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filters for read")
    fields: Optional[List[str]] = Field(None, description="Fields to return")
    limit: Optional[int] = Field(100, ge=1, le=1000)
    offset: Optional[int] = Field(0, ge=0)


class CRUDResponse(BaseModel):
    """Generic CRUD response schema"""
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    record_count: Optional[int] = None


class MetadataResponse(BaseModel):
    """System metadata response"""
    model: str
    fields: Dict[str, Any]
    relations: Optional[Dict[str, Any]] = None


class AuditLogResponse(BaseModel):
    """Audit log response schema"""
    id: int
    user_id: int
    system_id: Optional[int]
    action: str
    model: Optional[str]
    record_id: Optional[str]
    status: str
    timestamp: datetime
    duration_ms: Optional[int]
    error_message: Optional[str] = None

    class Config:
        from_attributes = True
