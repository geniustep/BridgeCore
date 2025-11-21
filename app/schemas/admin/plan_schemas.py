"""
Pydantic schemas for subscription plans
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class PlanCreate(BaseModel):
    """Create plan request"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    max_requests_per_day: int = Field(default=1000, ge=0)
    max_requests_per_hour: int = Field(default=100, ge=0)
    max_users: int = Field(default=5, ge=1)
    max_storage_gb: int = Field(default=1, ge=0)
    features: List[str] = Field(default_factory=list)
    price_monthly: Decimal = Field(default=Decimal("0.00"), ge=0)
    price_yearly: Decimal = Field(default=Decimal("0.00"), ge=0)
    is_active: bool = Field(default=True)


class PlanUpdate(BaseModel):
    """Update plan request"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    max_requests_per_day: Optional[int] = Field(None, ge=0)
    max_requests_per_hour: Optional[int] = Field(None, ge=0)
    max_users: Optional[int] = Field(None, ge=1)
    max_storage_gb: Optional[int] = Field(None, ge=0)
    features: Optional[List[str]] = None
    price_monthly: Optional[Decimal] = Field(None, ge=0)
    price_yearly: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


class PlanResponse(BaseModel):
    """Plan response"""
    id: UUID
    name: str
    description: Optional[str]
    max_requests_per_day: int
    max_requests_per_hour: int
    max_users: int
    max_storage_gb: int
    features: List[str]
    price_monthly: Decimal
    price_yearly: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
