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
import asyncio

from app.core.security import decode_tenant_token
from app.db.session import AsyncSessionLocal
from app.repositories.tenant_repository import TenantRepository
from app.models.tenant import TenantStatus
from loguru import logger
from datetime import datetime


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

            # Retry logic for database operations
            max_retries = 3
            last_exception = None
            tenant = None
            
            for attempt in range(max_retries):
                try:
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

                        # Attach tenant info to request state BEFORE update (so request can proceed even if update fails)
                        request.state.tenant_id = tenant_id
                        request.state.user_id = user_id
                        request.state.tenant = tenant

                        # Cache tenant briefly to reduce DB hits under load
                        self._tenant_cache[tenant_id] = (now + self._tenant_cache_ttl_seconds, tenant)
                        
                        logger.debug(f"[TenantContext] Tenant context set: tenant_id={tenant_id}, odoo_url={getattr(tenant, 'odoo_url', 'N/A')}")
                        
                        # Update last active timestamp (non-blocking, don't fail if this errors)
                        # Do this AFTER setting request state so request can proceed
                        try:
                            tenant.last_active_at = datetime.utcnow()
                            await session.commit()
                        except Exception as update_error:
                            logger.warning(
                                f"Failed to update last_active_at for tenant {tenant_id}: {str(update_error)}"
                            )
                            # Rollback and continue - request state is already set
                            try:
                                await session.rollback()
                            except:
                                pass
                        
                        # Success - break retry loop
                        break
                        
                except Exception as db_error:
                    last_exception = db_error
                    
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Database error in tenant context (attempt {attempt + 1}/{max_retries}): {str(db_error)}",
                            exc_info=True
                        )
                        await asyncio.sleep(0.1 * (attempt + 1))  # Exponential backoff
                    else:
                        # If we have a cached tenant, use it as fallback
                        if tenant_id in self._tenant_cache:
                            cached_expires, cached_tenant = self._tenant_cache[tenant_id]
                            if cached_expires > time.time():
                                logger.warning(f"Using cached tenant {tenant_id} due to DB error")
                                request.state.tenant_id = tenant_id
                                request.state.user_id = user_id
                                request.state.tenant = cached_tenant
                                break
                        raise

        except ValueError as ve:
            # Invalid UUID format
            logger.error(f"Invalid tenant_id format: {tenant_id}, error: {str(ve)}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid tenant ID format"},
            )
        except Exception as e:
            error_details = {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "path": request.url.path,
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
            logger.error(
                f"Error in tenant context middleware: {str(e)}",
                exc_info=True,
                extra=error_details
            )
            
            # Log more details for debugging
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
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
