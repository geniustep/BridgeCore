"""
Pydantic schemas for tenant users (admin management)
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class TenantUserCreate(BaseModel):
    """Create tenant user request (from admin)"""
    tenant_id: UUID
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(default="user", pattern="^(admin|user)$")
    is_active: bool = Field(default=True)
    odoo_user_id: Optional[int] = None


class TenantUserUpdate(BaseModel):
    """Update tenant user request (from admin)"""
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[str] = Field(None, pattern="^(admin|user)$")
    is_active: Optional[bool] = None
    odoo_user_id: Optional[int] = None


class TenantUserResponse(BaseModel):
    """Tenant user response"""
    id: UUID
    tenant_id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    odoo_user_id: Optional[int]
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

