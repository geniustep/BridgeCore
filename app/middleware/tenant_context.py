"""
Tenant context middleware to extract and validate tenant information
"""
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Callable
from uuid import UUID

from app.core.security import decode_tenant_token
from app.db.session import AsyncSessionLocal
from app.repositories.tenant_repository import TenantRepository
from app.models.tenant import TenantStatus
from loguru import logger


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract tenant context from JWT and attach to request state

    Also validates:
    - Tenant exists
    - Tenant is active
    - Updates last_active_at timestamp
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip tenant validation for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Skip tenant validation for public routes
        public_paths = [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/admin",  # Admin routes don't need tenant context
            "/auth"    # Auth routes don't need tenant context
        ]

        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)

        # Extract token
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            # No tenant token, continue (might be admin or public route)
            return await call_next(request)

        token = auth_header.split(" ")[1]
        payload = decode_tenant_token(token)

        if not payload:
            # Not a tenant token (might be admin token)
            return await call_next(request)

        tenant_id = payload.get("tenant_id")
        user_id = payload.get("sub")

        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid tenant token"
            )

        # Validate tenant
        try:
            async with AsyncSessionLocal() as session:
                tenant_repo = TenantRepository(session)
                tenant = await tenant_repo.get_by_id_uuid(UUID(tenant_id))

                if not tenant:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Tenant not found"
                    )

                # Check tenant status
                if tenant.status == TenantStatus.SUSPENDED:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Tenant account is suspended. Please contact support."
                    )

                if tenant.status == TenantStatus.DELETED:
                    raise HTTPException(
                        status_code=status.HTTP_410_GONE,
                        detail="Tenant account has been deleted"
                    )

                # Update last active timestamp
                await tenant_repo.update_last_active(UUID(tenant_id))

                # Attach tenant info to request state
                request.state.tenant_id = tenant_id
                request.state.user_id = user_id
                request.state.tenant = tenant

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in tenant context middleware: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to validate tenant context"
            )

        # Continue processing request
        response = await call_next(request)
        return response
