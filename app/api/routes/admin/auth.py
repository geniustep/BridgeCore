"""
Admin authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.admin import AdminLogin, AdminLoginResponse, AdminResponse
from app.services.admin_service import AdminService
from app.api.routes.admin.dependencies import get_current_admin
from app.models.admin import Admin

router = APIRouter(prefix="/admin/auth", tags=["Admin Authentication"])


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(
    credentials: AdminLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Admin login endpoint

    Authenticates an admin user and returns a JWT token.

    **Request Body:**
    - email: Admin email address
    - password: Admin password

    **Returns:**
    - admin: Admin user data
    - token: JWT access token
    - token_type: "bearer"

    **Errors:**
    - 401: Invalid credentials
    - 403: Account deactivated
    """
    admin_service = AdminService(db)

    result = await admin_service.authenticate(
        email=credentials.email,
        password=credentials.password
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    return AdminLoginResponse(**result)


@router.get("/me", response_model=AdminResponse)
async def get_current_admin_info(
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Get current admin user information

    Returns the currently authenticated admin's profile.

    **Requires:**
    - Valid JWT token in Authorization header

    **Returns:**
    - Admin user data

    **Errors:**
    - 401: Invalid or expired token
    - 403: Account deactivated
    - 404: Admin not found
    """
    return current_admin


@router.post("/logout")
async def admin_logout():
    """
    Admin logout endpoint

    Since we're using stateless JWT tokens, logout is handled client-side
    by removing the token. This endpoint exists for consistency.

    **Returns:**
    - Success message

    **Note:**
    For actual token revocation, implement a token blacklist using Redis.
    """
    return {"message": "Logged out successfully"}
