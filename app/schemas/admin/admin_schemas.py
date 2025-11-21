"""
Pydantic schemas for admin users
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class AdminLogin(BaseModel):
    """Admin login request"""
    email: EmailStr
    password: str


class AdminCreate(BaseModel):
    """Create admin request"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(default="admin", pattern="^(super_admin|admin|support)$")


class AdminUpdate(BaseModel):
    """Update admin request"""
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[str] = Field(None, pattern="^(super_admin|admin|support)$")
    is_active: Optional[bool] = None


class AdminResponse(BaseModel):
    """Admin response"""
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdminLoginResponse(BaseModel):
    """Admin login response"""
    admin: dict
    token: str
    token_type: str = "bearer"
