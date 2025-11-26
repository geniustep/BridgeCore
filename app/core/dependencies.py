"""
FastAPI dependencies
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
from app.db.session import get_db
from app.core.security import decode_token, verify_token_type
from app.models.user import User
from app.models.tenant_user import TenantUser
from app.models.external_system import SystemType
from sqlalchemy import select
from sqlalchemy.orm import selectinload

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token

    Args:
        credentials: HTTP bearer token
        db: Database session

    Returns:
        Current user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials

    # Decode token
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token type
    if not verify_token_type(payload, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    query = select(User).where(User.username == username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user

    Args:
        current_user: Current user from get_current_user

    Returns:
        Current active user

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current superuser

    Args:
        current_user: Current user from get_current_user

    Returns:
        Current superuser

    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough privileges"
        )
    return current_user


def get_client_ip(request) -> str:
    """
    Get client IP address from request

    Args:
        request: FastAPI request

    Returns:
        Client IP address
    """
    if request.client:
        return request.client.host
    return "unknown"


def get_user_agent(request) -> str:
    """
    Get user agent from request

    Args:
        request: FastAPI request

    Returns:
        User agent string
    """
    return request.headers.get("user-agent", "unknown")


async def get_cache_service():
    """
    Get cache service instance

    Returns:
        CacheService instance
    """
    from app.services.cache_service import CacheService
    from app.core.config import settings
    return CacheService(redis_url=settings.REDIS_URL)


# ============= Tenant User Dependencies =============

async def get_current_tenant_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> TenantUser:
    """
    Get current authenticated tenant user from JWT token

    Args:
        credentials: HTTP bearer token
        db: Database session

    Returns:
        Current tenant user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials

    # Decode token
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user ID from token
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get tenant user from database
    query = select(TenantUser).where(
        TenantUser.id == UUID(user_id)
    ).options(
        selectinload(TenantUser.tenant)
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


# ============= System Adapter Dependencies =============

async def get_moodle_adapter(
    current_user: TenantUser = Depends(get_current_tenant_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get Moodle adapter for current tenant

    Args:
        current_user: Current tenant user
        db: Database session

    Returns:
        MoodleAdapter instance

    Raises:
        HTTPException: If Moodle is not configured for tenant
    """
    from app.repositories.system_repository import TenantSystemRepository
    from app.adapters.moodle_adapter import MoodleAdapter
    from app.core.encryption import decrypt_data

    # Get Moodle connection for this tenant
    repo = TenantSystemRepository(db)
    connection = await repo.get_by_tenant_and_type(
        current_user.tenant_id,
        SystemType.MOODLE
    )

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Moodle is not configured for this tenant"
        )

    if not connection.is_active:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Moodle connection is inactive"
        )

    # Decrypt connection config
    config = decrypt_data(connection.connection_config)

    # Create and return adapter
    adapter = MoodleAdapter(config)
    await adapter.connect()

    return adapter


async def get_odoo_adapter(
    current_user: TenantUser = Depends(get_current_tenant_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get Odoo adapter for current tenant

    Args:
        current_user: Current tenant user
        db: Database session

    Returns:
        OdooAdapter instance

    Raises:
        HTTPException: If Odoo is not configured for tenant
    """
    from app.repositories.system_repository import TenantSystemRepository
    from app.adapters.odoo_adapter import OdooAdapter
    from app.core.encryption import decrypt_data

    # Try to get from new multi-system architecture first
    repo = TenantSystemRepository(db)
    connection = await repo.get_by_tenant_and_type(
        current_user.tenant_id,
        SystemType.ODOO
    )

    if connection:
        # Use new multi-system config
        if not connection.is_active:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Odoo connection is inactive"
            )

        config = decrypt_data(connection.connection_config)
    else:
        # Fallback to legacy Odoo fields in tenant (backward compatibility)
        tenant = current_user.tenant

        if not tenant.odoo_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Odoo is not configured for this tenant"
            )

        config = {
            "url": tenant.odoo_url,
            "database": tenant.odoo_database,
            "username": tenant.odoo_username,
            "password": tenant.odoo_password
        }

    # Create and return adapter
    adapter = OdooAdapter(config)
    await adapter.connect()

    return adapter
