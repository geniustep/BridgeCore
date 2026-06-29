"""
IP blocking middleware to prevent blocked IPs from accessing the API
"""
from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp
from typing import Callable
import redis.asyncio as redis

from app.core.config import settings
from loguru import logger


class IPBlockMiddleware(BaseHTTPMiddleware):
    """
    Middleware to block requests from blocked IP addresses
    
    Checks Redis cache for blocked IPs for fast lookup.
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

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip for health checks and public paths
        skip_paths = ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)

        # Get client IP
        client_ip = self._get_client_ip(request)
        
        if not client_ip:
            return await call_next(request)

        # Check if IP is blocked
        try:
            redis_client = await self.get_redis_client()
            is_blocked = await redis_client.get(f"blocked_ip:{client_ip}")
            
            if is_blocked == "1":
                logger.warning(f"Blocked IP attempted access: {client_ip} - {request.url.path}")
                
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "error": {
                            "type": "IPBlocked",
                            "message": "Your IP address has been blocked due to suspicious activity. Please contact support if you believe this is an error.",
                            "ip_address": client_ip
                        }
                    }
                )
        except Exception as e:
            # Don't block if Redis is unavailable
            logger.error(f"Error checking IP block status: {str(e)}")

        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, handling proxies"""
        # Check X-Forwarded-For header (common with proxies/load balancers)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Get the first IP (original client)
            return forwarded_for.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        
        # Fall back to direct connection IP
        if request.client:
            return request.client.host
        
        return ""

