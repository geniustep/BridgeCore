"""
Admin authentication dependencies
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.core.security import decode_admin_token
from app.services.admin_service import AdminService
from app.models.admin import Admin, AdminRole

security = HTTPBearer()


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Admin:
    """
    Get current admin from JWT token

    Args:
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        Current admin user

    Raises:
        HTTPException: If token is invalid or admin not found
    """
    token = credentials.credentials

    # Decode token
    payload = decode_admin_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    # Get admin from database
    admin_id = payload.get("sub")
    if not admin_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    admin_service = AdminService(db)
    admin = await admin_service.get_admin(UUID(admin_id))

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is deactivated"
        )

    return admin


async def get_current_super_admin(
    current_admin: Admin = Depends(get_current_admin)
) -> Admin:
    """
    Ensure current admin has super_admin role

    Args:
        current_admin: Current admin user

    Returns:
        Current admin user if super admin

    Raises:
        HTTPException: If admin is not a super admin
    """
    if current_admin.role != AdminRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin privileges required"
        )

    return current_admin


def require_admin_role(*allowed_roles: AdminRole):
    """
    Dependency factory to require specific admin roles

    Args:
        *allowed_roles: Allowed admin roles

    Returns:
        Dependency function

    Example:
        @router.get("/", dependencies=[Depends(require_admin_role(AdminRole.SUPER_ADMIN, AdminRole.ADMIN))])
    """
    async def check_role(current_admin: Admin = Depends(get_current_admin)) -> Admin:
        if current_admin.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {', '.join([r.value for r in allowed_roles])}"
            )
        return current_admin

    return check_role
