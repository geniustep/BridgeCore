"""
Authentication API routes - Flutter Compatible
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.db.session import get_db
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse
)
from app.models.user import User
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
    get_password_hash
)
from app.core.dependencies import get_current_user
from app.core.config import settings
from loguru import logger

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
security = HTTPBearer()


# Flutter-compatible request schemas
class FlutterLoginRequest(BaseModel):
    """Flutter client login request"""
    username: str
    password: str
    database: str


class FlutterTokenResponse(BaseModel):
    """Flutter client token response"""
    access_token: str
    refresh_token: str
    system_id: str
    user: Dict[str, Any]


@router.post("/login", response_model=FlutterTokenResponse, status_code=status.HTTP_200_OK)
async def login(
    request: FlutterLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login endpoint compatible with Flutter client

    This endpoint authenticates users against Odoo and returns JWT tokens
    with system_id and user information in Flutter-expected format.

    Args:
        request: Login request with username, password, and database
        db: Database session

    Returns:
        {
            "access_token": "...",
            "refresh_token": "...",
            "system_id": "odoo-{database}",
            "user": {
                "id": 1,
                "username": "admin",
                "name": "Administrator",
                "company_id": 1,
                "partner_id": 3
            }
        }

    Raises:
        HTTPException: If authentication fails
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

    # Create system_id
    system_id = f"odoo-{database}"

    # Automatically connect to Odoo system using login credentials
    try:
        from app.models.system import System
        
        # Get system service (singleton)
        from app.api.routes.systems import get_system_service
        service = get_system_service(db)
        
        # Check if system exists in database
        query = select(System).where(System.system_id == system_id).where(System.user_id == user.id)
        result = await db.execute(query)
        system = result.scalar_one_or_none()
        
        # Prepare Odoo connection config
        odoo_config = {
            "system_type": "odoo",
            "url": settings.ODOO_URL,
            "database": database,
            "username": username,
            "password": password
        }
        
        # Create or update system in database
        if not system:
            system = System(
                user_id=user.id,
                system_id=system_id,
                system_type="odoo",
                name=f"Odoo {database}",
                description=f"Odoo system connection for {database}",
                connection_config=odoo_config,
                is_active=True
            )
            db.add(system)
        else:
            system.connection_config = odoo_config
            system.is_active = True
        
        await db.commit()
        await db.refresh(system)
        
        # Cache system_id -> db_id mapping
        service._system_id_cache[system_id] = system.id
        
        # Connect to Odoo system
        try:
            adapter = await service.connect_system(
                system_id=system_id,
                system_type="odoo",
                config=odoo_config
            )
            logger.info(f"Auto-connected to Odoo system: {system_id} (connected: {adapter.is_connected})")
        except Exception as e:
            logger.warning(f"Failed to auto-connect to Odoo: {str(e)}")
            # Continue even if connection fails - user can connect manually later
        
    except Exception as e:
        logger.error(f"Error during auto-connection to Odoo: {str(e)}")
        # Continue with login even if auto-connection fails

    # Build user object in Flutter-expected format
    user_data = {
        "id": user.id,
        "username": user.username,
        "name": user.full_name or user.username,
        "company_id": 1,  # TODO: Get from Odoo
        "partner_id": user.id + 2  # Mock partner_id
    }

    logger.info(f"User {user.username} logged in successfully to {system_id}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "system_id": system_id,
        "user": user_data
    }


@router.post("/refresh")
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token (Flutter compatible)

    Expects refresh token in Authorization header: Bearer {refresh_token}

    Args:
        credentials: Bearer token credentials
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
    payload = decode_token(refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Verify token type
    if not verify_token_type(payload, "refresh"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    # Get user
    username: str = payload.get("sub")
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Create new access token
    new_access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )

    logger.info(f"Access token refreshed for user {user.username}")

    return {"access_token": new_access_token}


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout current user (Flutter compatible)

    Note: With JWT, logout is primarily handled client-side by removing tokens.
    This endpoint is for logging purposes and token blacklisting.

    Args:
        credentials: Bearer token credentials
        db: Database session

    Returns:
        {}
    """
    access_token = credentials.credentials

    # Decode token to get user info for logging
    payload = decode_token(access_token)
    if payload:
        username = payload.get("sub")
        logger.info(f"User {username} logged out")

    # TODO: Add token to blacklist in Redis if needed
    # await redis.sadd("token_blacklist", access_token)

    return {}


@router.get("/session")
async def get_session_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current session information (Flutter compatible)

    Args:
        credentials: Bearer token credentials
        db: Database session

    Returns:
        {
            "user": {
                "id": 1,
                "username": "admin",
                "name": "Administrator"
            },
            "session_expires_at": 1234567890
        }
    """
    access_token = credentials.credentials

    # Decode token
    payload = decode_token(access_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    # Verify token type
    if not verify_token_type(payload, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    # Get user
    username: str = payload.get("sub")
    user_id: int = payload.get("user_id")
    exp: int = payload.get("exp")

    query = select(User).where(User.username == username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "name": user.full_name or user.username,
        },
        "session_expires_at": exp,
    }


# Legacy endpoint - kept for backwards compatibility
@router.get("/me", response_model=UserResponse, deprecated=True)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information (DEPRECATED - use /session instead)

    Args:
        current_user: Current authenticated user

    Returns:
        User information
    """
    return current_user
