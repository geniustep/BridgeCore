"""
Rate limiting middleware per tenant based on subscription plan
"""
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Callable
from datetime import datetime, timedelta
from uuid import UUID
import redis.asyncio as redis

from app.core.config import settings
from app.core.security import decode_tenant_token
from loguru import logger


class TenantRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware per tenant

    Enforces:
    - Hourly rate limits
    - Daily rate limits
    Based on tenant's subscription plan
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.redis_client = None

    async def get_redis_client(self):
        """Get or create Redis client"""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return self.redis_client

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Skip rate limiting for certain paths
        skip_paths = ["/health", "/metrics", "/docs", "/redoc", "/openapi.json", "/admin", "/api/v1/auth"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)

        # Extract tenant info from token
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return await call_next(request)

        token = auth_header.split(" ")[1]
        payload = decode_tenant_token(token)

        if not payload:
            # Not a tenant token
            return await call_next(request)

        tenant_id = payload.get("tenant_id")
        if not tenant_id:
            return await call_next(request)

        # Check rate limits
        try:
            await self._check_rate_limits(tenant_id, request)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in rate limit middleware: {str(e)}")
            # Don't block request if rate limiting fails
            pass

        # Continue processing request
        response = await call_next(request)
        return response

    async def _check_rate_limits(self, tenant_id: str, request: Request):
        """Check if tenant has exceeded rate limits"""
        redis_client = await self.get_redis_client()

        # Get tenant limits (from request state if available, otherwise use defaults)
        hourly_limit = settings.DEFAULT_TENANT_RATE_LIMIT_PER_HOUR
        daily_limit = settings.DEFAULT_TENANT_RATE_LIMIT_PER_DAY

        # If tenant info is attached to request state, use its limits
        if hasattr(request.state, "tenant"):
            tenant = request.state.tenant
            if tenant.max_requests_per_hour:
                hourly_limit = tenant.max_requests_per_hour
            elif tenant.plan:
                hourly_limit = tenant.plan.max_requests_per_hour

            if tenant.max_requests_per_day:
                daily_limit = tenant.max_requests_per_day
            elif tenant.plan:
                daily_limit = tenant.plan.max_requests_per_day

        # Keys for Redis
        now = datetime.utcnow()
        hour_key = f"rate_limit:tenant:{tenant_id}:hour:{now.strftime('%Y%m%d%H')}"
        day_key = f"rate_limit:tenant:{tenant_id}:day:{now.strftime('%Y%m%d')}"

        # Check hourly limit
        hourly_count = await redis_client.get(hour_key)
        if hourly_count and int(hourly_count) >= hourly_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Hourly rate limit exceeded ({hourly_limit} requests/hour)",
                headers={"Retry-After": "3600"}
            )

        # Check daily limit
        daily_count = await redis_client.get(day_key)
        if daily_count and int(daily_count) >= daily_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily rate limit exceeded ({daily_limit} requests/day)",
                headers={"Retry-After": str(86400 - (now.hour * 3600 + now.minute * 60 + now.second))}
            )

        # Increment counters
        pipe = redis_client.pipeline()

        # Hourly counter
        pipe.incr(hour_key)
        pipe.expire(hour_key, 3600)  # Expire after 1 hour

        # Daily counter
        pipe.incr(day_key)
        pipe.expire(day_key, 86400)  # Expire after 1 day

        await pipe.execute()

        # Add rate limit info to response headers (will be added by the response)
        request.state.rate_limit_hourly_remaining = hourly_limit - (int(hourly_count) if hourly_count else 0) - 1
        request.state.rate_limit_daily_remaining = daily_limit - (int(daily_count) if daily_count else 0) - 1
