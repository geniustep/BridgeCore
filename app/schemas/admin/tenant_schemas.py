"""
Pydantic schemas for tenants
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
import re


class TenantCreate(BaseModel):
    """Create tenant request"""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=3, max_length=100, pattern="^[a-z0-9-]+$")
    description: Optional[str] = Field(None, max_length=1000)
    contact_email: EmailStr
    contact_phone: Optional[str] = Field(None, max_length=50)

    # Odoo Connection
    odoo_url: str = Field(..., pattern="^https?://")
    odoo_database: str = Field(..., min_length=1, max_length=255)
    odoo_version: Optional[str] = Field(None, max_length=50)
    odoo_username: str = Field(..., min_length=1, max_length=255)
    odoo_password: str = Field(..., min_length=1)

    # Subscription
    plan_id: UUID

    # Optional overrides
    max_requests_per_day: Optional[int] = Field(None, ge=0)
    max_requests_per_hour: Optional[int] = Field(None, ge=0)
    max_users: int = Field(5, ge=1, le=1000, description="Maximum number of users allowed")
    allowed_models: Optional[List[str]] = Field(default_factory=list)
    allowed_features: Optional[List[str]] = Field(default_factory=list)

    # Trial settings
    trial_ends_at: Optional[datetime] = None
    subscription_ends_at: Optional[datetime] = None

    @validator('slug')
    def validate_slug(cls, v):
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v


class TenantUpdate(BaseModel):
    """Update tenant request"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=3, max_length=100, pattern="^[a-z0-9-]+$")
    description: Optional[str] = Field(None, max_length=1000)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=50)

    # Odoo Connection
    odoo_url: Optional[str] = Field(None, pattern="^https?://")
    odoo_database: Optional[str] = Field(None, min_length=1, max_length=255)
    odoo_version: Optional[str] = Field(None, max_length=50)
    odoo_username: Optional[str] = Field(None, min_length=1, max_length=255)
    odoo_password: Optional[str] = Field(None, min_length=1)

    # Subscription
    plan_id: Optional[UUID] = None
    status: Optional[str] = Field(None, pattern="^(active|suspended|trial|deleted)$")

    # Limits
    max_requests_per_day: Optional[int] = Field(None, ge=0)
    max_requests_per_hour: Optional[int] = Field(None, ge=0)
    max_users: Optional[int] = Field(None, ge=1, le=1000)
    allowed_models: Optional[List[str]] = None
    allowed_features: Optional[List[str]] = None

    # Dates
    trial_ends_at: Optional[datetime] = None
    subscription_ends_at: Optional[datetime] = None


class TenantResponse(BaseModel):
    """Tenant response"""
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    contact_email: str
    contact_phone: Optional[str]

    # Odoo Connection (excluding password)
    odoo_url: str
    odoo_database: str
    odoo_version: Optional[str]
    odoo_username: str

    # Status & Subscription
    status: str
    plan_id: UUID
    trial_ends_at: Optional[datetime]
    subscription_ends_at: Optional[datetime]

    # Limits
    max_requests_per_day: Optional[int]
    max_requests_per_hour: Optional[int]
    max_users: int
    allowed_models: List[str]
    allowed_features: List[str]

    # Metadata
    created_by: Optional[UUID]
    last_active_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TenantListResponse(BaseModel):
    """Paginated tenant list response"""
    total: int
    tenants: List[TenantResponse]
    skip: int
    limit: int


class TenantConnectionTest(BaseModel):
    """Tenant Odoo connection test result"""
    success: bool
    message: str
    url: str
    database: Optional[str] = None
    version: Optional[str] = None
    user_info: Optional[dict] = None
    details: Optional[dict] = None
