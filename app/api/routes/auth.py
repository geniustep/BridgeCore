"""
Authentication API routes - Tenant & Admin Support

This file supports both:
1. Tenant users (for Flutter apps)
2. Admin users (for Admin Dashboard)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse
)
from app.models.user import User
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_user import TenantUser
from app.repositories.tenant_repository import TenantRepository
from app.repositories.tenant_user_repository import TenantUserRepository
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
    get_password_hash,
    create_tenant_token,
    create_tenant_refresh_token,
    decode_tenant_token
)
from app.core.dependencies import get_current_user
from app.core.config import settings
from loguru import logger

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
security = HTTPBearer()


# ============================================================================
# Tenant User Authentication (for Flutter apps)
# ============================================================================

class TenantLoginRequest(BaseModel):
    """Tenant user login request"""
    email: EmailStr
    password: str


class TenantTokenResponse(BaseModel):
    """Tenant user token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]
    tenant: Dict[str, Any]


@router.post("/tenant/login", response_model=TenantTokenResponse)
async def tenant_login(
    request: TenantLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login endpoint for tenant users (Flutter apps)

    This endpoint authenticates tenant users and returns JWT tokens
    with tenant_id embedded. The tenant's Odoo credentials are NOT
    returned - they are fetched automatically when making API calls.

    Flow:
    1. User provides email + password
    2. System finds user and their tenant
    3. Validates tenant status (must be active)
    4. Returns JWT with tenant_id
    5. All future API calls use this JWT
    6. Middleware extracts tenant_id and fetches Odoo credentials

    Args:
        request: Login request with email and password
        db: Database session

    Returns:
        {
            "access_token": "...",
            "refresh_token": "...",
            "token_type": "bearer",
            "expires_in": 1800,
            "user": {
                "id": "uuid",
                "email": "user@company.com",
                "full_name": "User Name",
                "role": "user"
            },
            "tenant": {
                "id": "uuid",
                "name": "Company A",
                "slug": "company-a",
                "status": "active"
            }
        }

    Raises:
        HTTPException: If authentication fails or tenant is not active
    """
    email = request.email
    password = request.password

    logger.info(f"Tenant login attempt for email: {email}")

    try:
        # Get tenant user repository
        tenant_user_repo = TenantUserRepository(db)
        tenant_repo = TenantRepository(db)

        # Find user by email
        query = select(TenantUser).where(TenantUser.email == email)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"Tenant user not found: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Verify password
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Invalid password for tenant user: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Inactive tenant user attempted login: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive. Please contact administrator."
            )

        # Get tenant
        tenant = await tenant_repo.get_by_id_uuid(user.tenant_id)

        if not tenant:
            logger.error(f"Tenant not found for user: {email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Tenant configuration error. Please contact support."
            )

        # ✅ Check tenant status
        if tenant.status == TenantStatus.SUSPENDED:
            logger.warning(f"Suspended tenant login attempt: {tenant.name}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant account is suspended. Please contact support."
            )

        if tenant.status == TenantStatus.DELETED:
            logger.warning(f"Deleted tenant login attempt: {tenant.name}")
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Tenant account has been deleted."
            )

        if tenant.status == TenantStatus.TRIAL:
            # Check if trial expired
            if tenant.trial_ends_at and tenant.trial_ends_at < datetime.utcnow():
                logger.warning(f"Expired trial tenant login attempt: {tenant.name}")
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="Trial period has expired. Please upgrade your account."
                )

        # Create JWT tokens with tenant_id
        access_token = create_tenant_token(
            user_id=str(user.id),
            tenant_id=str(tenant.id),
            email=user.email,
            role=user.role
        )

        refresh_token = create_tenant_refresh_token(
            user_id=str(user.id),
            tenant_id=str(tenant.id)
        )

        # Update last login
        user.last_login = datetime.utcnow()
        await db.commit()

        # Update tenant last active
        await tenant_repo.update_last_active(tenant.id)

        logger.info(
            f"Tenant user logged in successfully: {email} "
            f"(Tenant: {tenant.name})"
        )

        # Build response
        return TenantTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user={
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "odoo_user_id": user.odoo_user_id
            },
            tenant={
                "id": str(tenant.id),
                "name": tenant.name,
                "slug": tenant.slug,
                "status": tenant.status.value
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tenant login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )


@router.post("/tenant/refresh")
async def tenant_refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token for tenant user

    Args:
        credentials: Bearer refresh token
        db: Database session

    Returns:
        {
            "access_token": "new_token_here"
        }

    Raises:
        HTTPException: If refresh token is invalid
    """
    refresh_token = credentials.credentials

    # Decode refresh token
    payload = decode_tenant_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Verify token type
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")

    # Get user
    tenant_user_repo = TenantUserRepository(db)
    user = await tenant_user_repo.get_by_id(UUID(user_id))

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Get tenant
    tenant_repo = TenantRepository(db)
    tenant = await tenant_repo.get_by_id_uuid(UUID(tenant_id))

    if not tenant or tenant.status != TenantStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant is not active"
        )

    # Create new access token
    new_access_token = create_tenant_token(
        user_id=str(user.id),
        tenant_id=str(tenant.id),
        email=user.email,
        role=user.role
    )

    logger.info(f"Access token refreshed for tenant user: {user.email}")

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.get("/tenant/me")
async def get_tenant_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current tenant user information

    Args:
        credentials: Bearer access token
        db: Database session

    Returns:
        Current user and tenant information
    """
    access_token = credentials.credentials

    # Decode token
    payload = decode_tenant_token(access_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")

    # Get user
    tenant_user_repo = TenantUserRepository(db)
    user = await tenant_user_repo.get_by_id(UUID(user_id))

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Get tenant
    tenant_repo = TenantRepository(db)
    tenant = await tenant_repo.get_by_id_uuid(UUID(tenant_id))

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "odoo_user_id": user.odoo_user_id,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None
        },
        "tenant": {
            "id": str(tenant.id),
            "name": tenant.name,
            "slug": tenant.slug,
            "status": tenant.status.value,
            "odoo_url": tenant.odoo_url,
            "odoo_database": tenant.odoo_database
        }
    }


@router.post("/tenant/logout")
async def tenant_logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Logout tenant user

    Note: With JWT, logout is primarily handled client-side.
    This endpoint is for logging purposes.

    Args:
        credentials: Bearer access token

    Returns:
        Success message
    """
    access_token = credentials.credentials

    # Decode token to get user info for logging
    payload = decode_tenant_token(access_token)
    if payload:
        email = payload.get("email")
        logger.info(f"Tenant user logged out: {email}")

    # TODO: Add token to blacklist in Redis if needed
    # await redis.sadd("token_blacklist", access_token)

    return {"message": "Logged out successfully"}


# ============================================================================
# Legacy/Admin Authentication (keep for backward compatibility)
# ============================================================================

class FlutterLoginRequest(BaseModel):
    """Flutter client login request (legacy)"""
    username: str
    password: str
    database: str


@router.post("/login", deprecated=True)
async def legacy_login(
    request: FlutterLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Legacy login endpoint (DEPRECATED)
    
    Use /tenant/login instead for new implementations.
    
    This endpoint is kept for backward compatibility with existing Flutter apps.
    """
    username = request.username
    password = request.password
    database = request.database

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Try to find existing user or create a temporary one
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    # For demo: create user if doesn't exist
    if not user:
        user = User(
            username=username,
            email=f"{username}@{database}.com",
            hashed_password=get_password_hash(password),
            full_name=f"{username.capitalize()}",
            is_active=True,
            is_superuser=False
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"Created new user: {username}")

    # Verify password
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    # Create tokens
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.id}
    )

    system_id = f"odoo-{database}"

    user_data = {
        "id": user.id,
        "username": user.username,
        "name": user.full_name or user.username,
        "company_id": 1,
        "partner_id": user.id + 2
    }

    logger.info(f"User {user.username} logged in successfully (legacy)")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "system_id": system_id,
        "user": user_data
    }


@router.post("/refresh", deprecated=True)
async def legacy_refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Legacy refresh endpoint (DEPRECATED)
    
    Use /tenant/refresh instead.
    """
    refresh_token = credentials.credentials

    payload = decode_token(refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    if not verify_token_type(payload, "refresh"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    username: str = payload.get("sub")
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    new_access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )

    return {"access_token": new_access_token}


@router.post("/logout", deprecated=True)
async def legacy_logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Legacy logout endpoint (DEPRECATED)"""
    access_token = credentials.credentials

    payload = decode_token(access_token)
    if payload:
        username = payload.get("sub")
        logger.info(f"User {username} logged out (legacy)")

    return {}


@router.get("/me", response_model=UserResponse, deprecated=True)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information (DEPRECATED - legacy endpoint)
    
    Use /tenant/me for tenant users
    """
    return current_user