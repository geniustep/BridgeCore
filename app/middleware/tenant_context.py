"""
Tenant context middleware to extract and validate tenant information
"""
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp
from typing import Callable
from uuid import UUID
import time

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
        # Tiny in-process cache to reduce DB hits under high request volume.
        # Key: tenant_id (str) -> (expires_at_epoch_seconds, tenant_obj)
        self._tenant_cache: dict[str, tuple[float, object]] = {}
        self._tenant_cache_ttl_seconds: int = 30

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
            "/api/v1/auth",  # Auth routes don't need tenant context (including /tenant/login)
            "/auth"    # Legacy auth routes (backward compatibility)
        ]

        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)

        # Extract token
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            # No tenant token, continue (might be admin or public route)
            return await call_next(request)

        token = auth_header.split(" ")[1]
        
        # Log the request path for debugging
        logger.info(f"[TenantContext] Processing request: {request.url.path}")
        
        payload = decode_tenant_token(token)

        if not payload:
            # Not a tenant token (might be admin token)
            # Try to decode without validation to see what's in the token
            try:
                from jose import jwt
                from app.core.config import settings
                unverified_payload = jwt.decode(
                    token, 
                    settings.JWT_SECRET_KEY, 
                    algorithms=[settings.JWT_ALGORITHM],
                    options={"verify_exp": False}
                )
                logger.warning(
                    f"[TenantContext] Token is not a tenant token. "
                    f"user_type={unverified_payload.get('user_type')}, "
                    f"has_tenant_id={unverified_payload.get('tenant_id') is not None}, "
                    f"sub={unverified_payload.get('sub')}"
                )
            except Exception as e:
                logger.warning(f"[TenantContext] Could not decode token for debugging: {str(e)}")
            
            return await call_next(request)
        
        logger.info(f"[TenantContext] Tenant token decoded successfully: user_id={payload.get('sub')}, tenant_id={payload.get('tenant_id')}")

        tenant_id = payload.get("tenant_id")
        user_id = payload.get("sub")

        if not tenant_id:
            # IMPORTANT: Do not raise from BaseHTTPMiddleware; return a response.
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid tenant token (missing tenant_id)"},
            )

        # Validate tenant
        try:
            # Fast path: in-memory cache
            now = time.time()
            cached = self._tenant_cache.get(tenant_id)
            if cached:
                expires_at, cached_tenant = cached
                if expires_at > now:
                    request.state.tenant_id = tenant_id
                    request.state.user_id = user_id
                    request.state.tenant = cached_tenant
                    return await call_next(request)
                else:
                    self._tenant_cache.pop(tenant_id, None)

            async with AsyncSessionLocal() as session:
                tenant_repo = TenantRepository(session)
                tenant = await tenant_repo.get_by_id_uuid(UUID(tenant_id))

                if not tenant:
                    return JSONResponse(
                        status_code=status.HTTP_404_NOT_FOUND,
                        content={"detail": "Tenant not found"},
                    )

                # Check tenant status
                if tenant.status == TenantStatus.SUSPENDED:
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"detail": "Tenant account is suspended. Please contact support."},
                    )

                if tenant.status == TenantStatus.DELETED:
                    return JSONResponse(
                        status_code=status.HTTP_410_GONE,
                        content={"detail": "Tenant account has been deleted"},
                    )

                # Update last active timestamp
                await tenant_repo.update_last_active(UUID(tenant_id))

                # Attach tenant info to request state
                request.state.tenant_id = tenant_id
                request.state.user_id = user_id
                request.state.tenant = tenant

                # Cache tenant briefly to reduce DB hits under load
                self._tenant_cache[tenant_id] = (now + self._tenant_cache_ttl_seconds, tenant)
                
                logger.debug(f"[TenantContext] Tenant context set: tenant_id={tenant_id}, odoo_url={tenant.odoo_url}")

        except Exception as e:
            logger.error(f"Error in tenant context middleware: {str(e)}")
            # Under load, DB connectivity/pool issues can happen.
            # Return a proper JSON response instead of raising inside BaseHTTPMiddleware,
            # which can otherwise surface as plain-text 500.
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"detail": "Failed to validate tenant context. Please retry."},
            )

        # Continue processing request
        response = await call_next(request)
        return response
