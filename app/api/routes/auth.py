"""
Authentication API routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
    verify_token_type
)
from app.core.dependencies import get_current_user
from app.core.config import settings
from loguru import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with system credentials

    This endpoint authenticates users against external systems (Odoo, SAP, etc.)
    and returns JWT tokens for subsequent API calls.

    Args:
        request: Login request with system credentials
        db: Database session

    Returns:
        Access and refresh tokens

    Raises:
        HTTPException: If authentication fails
    """
    system_type = request.system_credentials.system_type
    credentials = request.system_credentials.credentials

    # For demo purposes, we'll create a simple authentication
    # In production, this would verify against the actual external system

    # Example: For Odoo
    if system_type == "odoo":
        username = credentials.get("username")
        password = credentials.get("password")

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
            from app.core.security import get_password_hash
            user = User(
                username=username,
                email=f"{username}@example.com",
                hashed_password=get_password_hash(password),
                full_name=username,
                is_active=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

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

        logger.info(f"User {user.username} logged in successfully")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported system type: {system_type}"
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token

    Args:
        request: Refresh token request
        db: Database session

    Returns:
        New access and refresh tokens

    Raises:
        HTTPException: If refresh token is invalid
    """
    # Decode refresh token
    payload = decode_token(request.refresh_token)
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

    # Create new tokens
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )
    new_refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.id}
    )

    logger.info(f"Tokens refreshed for user {user.username}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout current user

    Note: With JWT, logout is primarily handled client-side by removing tokens.
    This endpoint is for logging purposes.

    Args:
        current_user: Current authenticated user

    Returns:
        Success message
    """
    logger.info(f"User {current_user.username} logged out")

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information

    Args:
        current_user: Current authenticated user

    Returns:
        User information
    """
    return current_user
