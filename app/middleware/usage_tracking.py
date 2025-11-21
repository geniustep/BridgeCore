"""
Usage tracking middleware for logging API requests per tenant
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from datetime import datetime
from typing import Callable
import time

from app.models.usage_log import UsageLog
from app.models.error_log import ErrorLog, ErrorSeverity
from app.db.session import AsyncSessionLocal
from app.core.security import decode_tenant_token
from loguru import logger


class UsageTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track all API requests per tenant

    Logs:
    - Endpoint accessed
    - HTTP method
    - Response time
    - Request/response size
    - Status code
    - User agent and IP
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip tracking for health checks, metrics, and admin routes
        skip_paths = ["/health", "/metrics", "/docs", "/redoc", "/openapi.json", "/admin"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)

        # Extract tenant info from token
        tenant_id = None
        user_id = None

        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = decode_tenant_token(token)
            if payload:
                tenant_id = payload.get("tenant_id")
                user_id = payload.get("sub")

        # Only track requests with tenant context
        if not tenant_id:
            return await call_next(request)

        # Measure request time
        start_time = time.time()

        # Get request size
        request_size = 0
        if request.headers.get("content-length"):
            try:
                request_size = int(request.headers.get("content-length"))
            except ValueError:
                request_size = 0

        # Process request
        response = await call_next(request)

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Get response size
        response_size = 0
        if hasattr(response, "headers") and response.headers.get("content-length"):
            try:
                response_size = int(response.headers.get("content-length"))
            except ValueError:
                response_size = 0

        # Extract model name from path if present
        model_name = None
        path_parts = request.url.path.split("/")
        if "systems" in path_parts:
            # Try to find model name in query params or path
            model_name = request.query_params.get("model")

        # Log usage asynchronously
        try:
            await self._log_usage(
                tenant_id=tenant_id,
                user_id=user_id,
                endpoint=request.url.path,
                method=request.method,
                model_name=model_name,
                request_size_bytes=request_size,
                response_size_bytes=response_size,
                response_time_ms=response_time_ms,
                status_code=response.status_code,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception as e:
            logger.error(f"Failed to log usage: {str(e)}")

        return response

    async def _log_usage(
        self,
        tenant_id: str,
        user_id: str,
        endpoint: str,
        method: str,
        model_name: str,
        request_size_bytes: int,
        response_size_bytes: int,
        response_time_ms: int,
        status_code: int,
        ip_address: str,
        user_agent: str
    ):
        """Log usage to database"""
        from uuid import UUID

        async with AsyncSessionLocal() as session:
            usage_log = UsageLog(
                tenant_id=UUID(tenant_id),
                user_id=UUID(user_id) if user_id else None,
                timestamp=datetime.utcnow(),
                endpoint=endpoint,
                method=method,
                model_name=model_name,
                request_size_bytes=request_size_bytes,
                response_size_bytes=response_size_bytes,
                response_time_ms=response_time_ms,
                status_code=status_code,
                ip_address=ip_address,
                user_agent=user_agent
            )

            session.add(usage_log)
            await session.commit()
