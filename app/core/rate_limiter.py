"""
Rate Limiting with SlowAPI

Protect API from abuse and overload
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import settings


# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"] if settings.RATE_LIMIT_ENABLED else [],
    storage_uri=settings.REDIS_URL,
    strategy="fixed-window"
)

# Rate limit presets for different endpoint types
RATE_LIMITS = {
    "auth": "10/minute",          # Login attempts
    "read": "100/minute",         # Read operations
    "write": "50/minute",         # Create/Update operations
    "delete": "20/minute",        # Delete operations
    "batch": "10/minute",         # Batch operations
    "file": "30/minute",          # File operations
    "report": "20/minute",        # Report generation
    # Odoo Operations Rate Limits
    "odoo_search": "100/minute",      # Search operations (lightweight)
    "odoo_read": "80/minute",         # Read operations
    "odoo_create": "30/minute",        # Create operations (more expensive)
    "odoo_write": "40/minute",        # Update operations
    "odoo_delete": "20/minute",       # Delete operations
    "odoo_advanced": "50/minute",     # Advanced operations (onchange, read_group)
    "odoo_name": "100/minute",        # Name operations (lightweight)
    "odoo_view": "60/minute",         # View operations
    "odoo_web": "50/minute",         # Web operations
    "odoo_permission": "100/minute",  # Permission checks (lightweight)
    "odoo_utility": "80/minute",       # Utility operations
    "odoo_method": "30/minute",       # Custom method calls (can be expensive)
}


def get_rate_limit(operation_type: str) -> str:
    """
    Get rate limit for operation type

    Args:
        operation_type: Type of operation

    Returns:
        Rate limit string
    """
    return RATE_LIMITS.get(operation_type, "60/minute")
