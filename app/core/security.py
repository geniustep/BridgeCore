"""
Security utilities for authentication and authorization
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token

    Args:
        data: Data to encode in token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token

    Example:
        token = create_access_token(
            data={"sub": user.username, "user_id": user.id}
        )
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token

    Args:
        data: Data to encode in token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify a JWT token

    Args:
        token: JWT token to decode

    Returns:
        Decoded token payload or None if invalid

    Raises:
        JWTError: If token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def verify_token_type(payload: Dict[str, Any], expected_type: str) -> bool:
    """
    Verify token type (access or refresh)

    Args:
        payload: Decoded token payload
        expected_type: Expected token type ('access' or 'refresh')

    Returns:
        True if token type matches, False otherwise
    """
    token_type = payload.get("type")
    return token_type == expected_type


# ============================================================================
# Admin JWT Token Functions
# ============================================================================

def create_admin_token(
    admin_id: str,
    email: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token for admin users

    Args:
        admin_id: Admin user ID (UUID)
        email: Admin email
        role: Admin role (super_admin, admin, support)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token for admin

    Example:
        token = create_admin_token(
            admin_id=str(admin.id),
            email=admin.email,
            role=admin.role
        )
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ADMIN_TOKEN_EXPIRE_MINUTES
        )

    payload = {
        "sub": admin_id,
        "email": email,
        "role": role,
        "user_type": "admin",
        "type": "access",
        "exp": expire
    }

    encoded_jwt = jwt.encode(
        payload,
        settings.ADMIN_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_admin_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify an admin JWT token

    Args:
        token: Admin JWT token to decode

    Returns:
        Decoded token payload or None if invalid

    Example:
        payload = decode_admin_token(token)
        if payload and payload.get("user_type") == "admin":
            admin_id = payload.get("sub")
    """
    try:
        payload = jwt.decode(
            token,
            settings.ADMIN_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Verify it's an admin token
        if payload.get("user_type") != "admin":
            return None

        return payload
    except JWTError:
        return None


# ============================================================================
# Tenant User JWT Token Functions
# ============================================================================

def create_tenant_token(
    user_id: str,
    tenant_id: str,
    email: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token for tenant users

    Args:
        user_id: Tenant user ID (UUID)
        tenant_id: Tenant ID (UUID)
        email: User email
        role: User role (admin, user)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token for tenant user

    Example:
        token = create_tenant_token(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            email=user.email,
            role=user.role
        )
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "email": email,
        "role": role,
        "user_type": "tenant",
        "type": "access",
        "exp": expire
    }

    encoded_jwt = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_tenant_refresh_token(
    user_id: str,
    tenant_id: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token for tenant users

    Args:
        user_id: Tenant user ID (UUID)
        tenant_id: Tenant ID (UUID)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT refresh token for tenant user
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "user_type": "tenant",
        "type": "refresh",
        "exp": expire
    }

    encoded_jwt = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_tenant_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify a tenant user JWT token

    Args:
        token: Tenant user JWT token to decode

    Returns:
        Decoded token payload or None if invalid

    Example:
        payload = decode_tenant_token(token)
        if payload:
            user_id = payload.get("sub")
            tenant_id = payload.get("tenant_id")
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Verify it's a tenant token
        if payload.get("user_type") != "tenant":
            return None

        return payload
    except JWTError:
        return None


# ============================================================================
# Utility Functions
# ============================================================================

def get_token_type(token: str) -> Optional[str]:
    """
    Get the user type from a token without full validation

    Args:
        token: JWT token

    Returns:
        "admin" or "tenant" or None if invalid
    """
    try:
        # Decode without verification to peek at user_type
        unverified_payload = jwt.get_unverified_claims(token)
        return unverified_payload.get("user_type")
    except:
        return None
