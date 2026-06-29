"""
Rate limiting middleware per tenant based on subscription plan
With Smart Throttling and Alert Integration
"""
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Callable, Optional
from datetime import datetime, timedelta
from uuid import UUID
import redis.asyncio as redis
import asyncio

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
        """Check if tenant has exceeded rate limits with smart throttling"""
        redis_client = await self.get_redis_client()

        # Get tenant limits (from request state if available, otherwise use defaults)
        hourly_limit = settings.DEFAULT_TENANT_RATE_LIMIT_PER_HOUR
        daily_limit = settings.DEFAULT_TENANT_RATE_LIMIT_PER_DAY
        tenant_name = "Unknown"

        # If tenant info is attached to request state, use its limits
        if hasattr(request.state, "tenant"):
            tenant = request.state.tenant
            tenant_name = getattr(tenant, 'name', 'Unknown')
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
        warning_key = f"rate_limit:warning:{tenant_id}:{now.strftime('%Y%m%d%H')}"

        # Get current counts
        hourly_count = int(await redis_client.get(hour_key) or 0)
        daily_count = int(await redis_client.get(day_key) or 0)

        # Calculate usage percentages
        hourly_percentage = (hourly_count / hourly_limit) * 100 if hourly_limit > 0 else 0
        daily_percentage = (daily_count / daily_limit) * 100 if daily_limit > 0 else 0

        # Smart Throttling: Add delay when approaching limits (80-100%)
        delay_ms = 0
        if hourly_percentage >= 90 or daily_percentage >= 90:
            delay_ms = 500  # 500ms delay
        elif hourly_percentage >= 80 or daily_percentage >= 80:
            delay_ms = 200  # 200ms delay
        
        if delay_ms > 0:
            await asyncio.sleep(delay_ms / 1000)
            # Add warning header
            request.state.rate_limit_throttled = True
            request.state.rate_limit_delay_ms = delay_ms

        # Check and create warning alerts at 80% threshold (once per hour)
        warning_sent = await redis_client.get(warning_key)
        if not warning_sent and (hourly_percentage >= 80 or daily_percentage >= 80):
            # Mark warning as sent for this hour
            await redis_client.set(warning_key, "1", ex=3600)
            
            # Fire async task to create alert (non-blocking)
            asyncio.create_task(
                self._create_rate_limit_warning(
                    tenant_id=tenant_id,
                    tenant_name=tenant_name,
                    hourly_count=hourly_count,
                    hourly_limit=hourly_limit,
                    daily_count=daily_count,
                    daily_limit=daily_limit
                )
            )

        # Check hourly limit exceeded
        if hourly_count >= hourly_limit:
            # Record IP violation for potential auto-blocking
            client_ip = self._get_client_ip(request)
            if client_ip:
                asyncio.create_task(
                    self._record_rate_limit_violation(tenant_id, client_ip, request)
                )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Hourly rate limit exceeded ({hourly_limit} requests/hour). Your request was throttled. Please try again later.",
                headers={
                    "Retry-After": "3600",
                    "X-RateLimit-Limit": str(hourly_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int((now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)).timestamp()))
                }
            )

        # Check daily limit exceeded
        if daily_count >= daily_limit:
            client_ip = self._get_client_ip(request)
            if client_ip:
                asyncio.create_task(
                    self._record_rate_limit_violation(tenant_id, client_ip, request)
                )
            
            seconds_until_reset = 86400 - (now.hour * 3600 + now.minute * 60 + now.second)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily rate limit exceeded ({daily_limit} requests/day). Please try again tomorrow.",
                headers={
                    "Retry-After": str(seconds_until_reset),
                    "X-RateLimit-Limit": str(daily_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int((now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)).timestamp()))
                }
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

        # Add rate limit info to response headers
        request.state.rate_limit_hourly_remaining = hourly_limit - hourly_count - 1
        request.state.rate_limit_daily_remaining = daily_limit - daily_count - 1
        request.state.rate_limit_hourly_limit = hourly_limit
        request.state.rate_limit_daily_limit = daily_limit

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        if request.client:
            return request.client.host
        return ""

    async def _create_rate_limit_warning(
        self,
        tenant_id: str,
        tenant_name: str,
        hourly_count: int,
        hourly_limit: int,
        daily_count: int,
        daily_limit: int
    ):
        """Create rate limit warning alert (non-blocking)"""
        try:
            from app.db.session import AsyncSessionLocal
            from app.services.alert_service import AlertService
            
            async with AsyncSessionLocal() as session:
                alert_service = AlertService(session)
                
                # Check which limit is being approached
                hourly_pct = (hourly_count / hourly_limit) * 100 if hourly_limit else 0
                daily_pct = (daily_count / daily_limit) * 100 if daily_limit else 0
                
                if hourly_pct >= 80:
                    await alert_service.check_rate_limit_and_alert(
                        tenant_id=UUID(tenant_id),
                        tenant_name=tenant_name,
                        current_count=hourly_count,
                        limit=hourly_limit,
                        limit_type="hourly"
                    )
                
                if daily_pct >= 80:
                    await alert_service.check_rate_limit_and_alert(
                        tenant_id=UUID(tenant_id),
                        tenant_name=tenant_name,
                        current_count=daily_count,
                        limit=daily_limit,
                        limit_type="daily"
                    )
        except Exception as e:
            logger.error(f"Failed to create rate limit alert: {str(e)}")

    async def _record_rate_limit_violation(
        self,
        tenant_id: str,
        ip_address: str,
        request: Request
    ):
        """Record rate limit violation for potential IP blocking"""
        try:
            from app.db.session import AsyncSessionLocal
            from app.services.ip_block_service import IPBlockService
            
            async with AsyncSessionLocal() as session:
                ip_block_service = IPBlockService(session)
                await ip_block_service.record_violation(
                    ip_address=ip_address,
                    violation_type="rate_limit",
                    tenant_id=UUID(tenant_id),
                    user_agent=request.headers.get("user-agent"),
                    request_details={
                        "path": request.url.path,
                        "method": request.method
                    }
                )
        except Exception as e:
            logger.error(f"Failed to record rate limit violation: {str(e)}")
