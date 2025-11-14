"""
Authentication Pydantic schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any


class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """User update schema"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


class UserResponse(UserBase):
    """User response schema"""
    id: int
    is_active: bool
    is_superuser: bool

    class Config:
        from_attributes = True


class SystemCredentials(BaseModel):
    """System credentials for login"""
    system_type: str = Field(..., description="System type (odoo, sap, salesforce)")
    system_version: Optional[str] = Field(None, description="System version (e.g., '16.0')")
    credentials: Dict[str, Any] = Field(..., description="System-specific credentials")


class LoginRequest(BaseModel):
    """Login request schema"""
    system_credentials: SystemCredentials


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiration in seconds")


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str  # Subject (username)
    user_id: int
    exp: int  # Expiration timestamp
    type: str  # Token type (access or refresh)
