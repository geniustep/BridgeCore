"""
Monitoring and Error Tracking

Sentry integration for error tracking
Prometheus metrics for performance monitoring
"""
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
import time
from loguru import logger


# Initialize Sentry
def init_sentry():
    """
    Initialize Sentry SDK for error tracking

    Features:
    - Automatic error capture
    - Performance monitoring
    - Release tracking
    - User context
    """
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                RedisIntegration(),
                LoggingIntegration(
                    level=None,  # Capture all logs
                    event_level=None  # Send errors as events
                )
            ],
            traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
            environment=settings.ENVIRONMENT,
            release=settings.APP_VERSION,
            send_default_pii=False,  # Don't send personally identifiable information
            attach_stacktrace=True,
            before_send=before_send_handler
        )
        logger.info("Sentry initialized successfully")
    else:
        logger.warning("Sentry DSN not configured, error tracking disabled")


def before_send_handler(event, hint):
    """
    Filter events before sending to Sentry

    Args:
        event: Sentry event
        hint: Additional context

    Returns:
        Modified event or None to drop
    """
    # Don't send 404 errors
    if event.get('request', {}).get('status_code') == 404:
        return None

    # Don't send rate limit errors
    if 'RateLimitExceeded' in str(event.get('exception', {}).get('values', [{}])[0].get('type', '')):
        return None

    return event


def capture_exception_with_context(
    exception: Exception,
    user_id: int = None,
    system_id: str = None,
    extra_context: dict = None
):
    """
    Capture exception with additional context

    Args:
        exception: Exception to capture
        user_id: User ID
        system_id: System ID
        extra_context: Additional context data
    """
    with sentry_sdk.push_scope() as scope:
        if user_id:
            scope.set_user({"id": user_id})

        if system_id:
            scope.set_tag("system_id", system_id)

        if extra_context:
            scope.set_context("extra", extra_context)

        sentry_sdk.capture_exception(exception)


# Prometheus Metrics
# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)

# System metrics
active_connections = Gauge(
    'active_connections',
    'Number of active ERP/CRM connections',
    ['system_type']
)

cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['operation']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['operation']
)

# Database metrics
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation']
)

db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['operation', 'status']
)

# Business metrics
api_operations_total = Counter(
    'api_operations_total',
    'Total API operations',
    ['system_type', 'model', 'operation', 'status']
)

api_operation_duration_seconds = Histogram(
    'api_operation_duration_seconds',
    'API operation duration in seconds',
    ['system_type', 'model', 'operation']
)

# Circuit breaker metrics
circuit_breaker_state = Gauge(
    'circuit_breaker_state',
    'Circuit breaker state (0=CLOSED, 1=HALF_OPEN, 2=OPEN)',
    ['system_id']
)

circuit_breaker_failures = Counter(
    'circuit_breaker_failures_total',
    'Total circuit breaker failures',
    ['system_id']
)

# Version migration metrics
version_migrations_total = Counter(
    'version_migrations_total',
    'Total version migrations',
    ['system_type', 'from_version', 'to_version', 'status']
)

version_migration_duration_seconds = Histogram(
    'version_migration_duration_seconds',
    'Version migration duration in seconds',
    ['system_type', 'from_version', 'to_version']
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect Prometheus metrics for HTTP requests
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and collect metrics

        Args:
            request: FastAPI request
            call_next: Next middleware

        Returns:
            Response
        """
        method = request.method
        path = request.url.path

        # Skip metrics endpoint itself
        if path == "/metrics":
            return await call_next(request)

        # Record request start time
        start_time = time.time()

        # Process request
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception as e:
            status = 500
            logger.error(f"Request failed: {e}")
            raise
        finally:
            # Record metrics
            duration = time.time() - start_time

            http_requests_total.labels(
                method=method,
                endpoint=path,
                status=status
            ).inc()

            http_request_duration_seconds.labels(
                method=method,
                endpoint=path
            ).observe(duration)

        return response


async def metrics_endpoint(request: Request):
    """
    Prometheus metrics endpoint

    Returns:
        Metrics in Prometheus format
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# Metric helper functions
def record_cache_hit(operation: str):
    """Record cache hit"""
    cache_hits_total.labels(operation=operation).inc()


def record_cache_miss(operation: str):
    """Record cache miss"""
    cache_misses_total.labels(operation=operation).inc()


def record_db_query(operation: str, duration: float, success: bool):
    """Record database query metrics"""
    status = "success" if success else "error"
    db_queries_total.labels(operation=operation, status=status).inc()
    db_query_duration_seconds.labels(operation=operation).observe(duration)


def record_api_operation(
    system_type: str,
    model: str,
    operation: str,
    duration: float,
    success: bool
):
    """Record API operation metrics"""
    status = "success" if success else "error"
    api_operations_total.labels(
        system_type=system_type,
        model=model,
        operation=operation,
        status=status
    ).inc()
    api_operation_duration_seconds.labels(
        system_type=system_type,
        model=model,
        operation=operation
    ).observe(duration)


def update_circuit_breaker_state(system_id: str, state: str):
    """Update circuit breaker state metric"""
    state_value = {"CLOSED": 0, "HALF_OPEN": 1, "OPEN": 2}.get(state, 0)
    circuit_breaker_state.labels(system_id=system_id).set(state_value)


def record_circuit_breaker_failure(system_id: str):
    """Record circuit breaker failure"""
    circuit_breaker_failures.labels(system_id=system_id).inc()


def record_version_migration(
    system_type: str,
    from_version: str,
    to_version: str,
    duration: float,
    success: bool
):
    """Record version migration metrics"""
    status = "success" if success else "error"
    version_migrations_total.labels(
        system_type=system_type,
        from_version=from_version,
        to_version=to_version,
        status=status
    ).inc()
    version_migration_duration_seconds.labels(
        system_type=system_type,
        from_version=from_version,
        to_version=to_version
    ).observe(duration)


def update_active_connections(system_type: str, count: int):
    """Update active connections gauge"""
    active_connections.labels(system_type=system_type).set(count)
