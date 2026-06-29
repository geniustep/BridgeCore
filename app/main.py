"""
Main FastAPI Application
"""
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from loguru import logger

from app.core.config import settings
from app.utils.logger import setup_logging
from app.middleware.logging_middleware import logging_middleware
from app.db.session import init_db, close_db
from app.api.routes import auth, health, systems, batch, barcode, files, websocket, odoo
from app.api.routes.odoo import router as odoo_operations_router
from app.api.routes.admin import (
    auth as admin_auth,
    tenants as admin_tenants,
    tenant_users as admin_tenant_users,
    plans as admin_plans,
    analytics as admin_analytics,
    logs as admin_logs,
    odoo_helpers as admin_odoo_helpers,
    systems as admin_systems,
    alerts as admin_alerts,
    ip_blocks as admin_ip_blocks
)
from app.modules.webhook import router as webhook_router_v1
from app.modules.webhook import router_v2 as webhook_router_v2
from app.modules.offline_sync import router as offline_sync_router
from app.modules.odoo_sync import router as odoo_sync_router
from app.modules.conversation import router as conversation_router
from app.api.routes.moodle.main import router as moodle_router
from app.api.routes.triggers import router as triggers_router
from app.api.routes.notifications import router as notifications_router
from app.core.rate_limiter import limiter, _rate_limit_exceeded_handler
from app.core.monitoring import (
    init_sentry,
    PrometheusMiddleware,
    metrics_endpoint
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events

    Startup:
    - Setup logging
    - Initialize database

    Shutdown:
    - Close database connections
    """
    # Startup
    logger.info("Starting application...")
    setup_logging()

    # Initialize Sentry
    init_sentry()

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    ## BridgeCore Multi-System Middleware API

    This API serves as a middleware layer between Flutter applications and multiple external systems (ERP/CRM/LMS).

    ### Features

    * 🔐 **Secure Authentication**: JWT-based authentication
    * 🔄 **Data Unification**: Automatic field mapping
    * 🎯 **Multi-System Support**: Odoo ERP, Moodle LMS, SAP, Salesforce
    * ⚡ **High Performance**: Caching + Connection pooling
    * 📝 **Audit Trail**: Complete operation logging
    * 🏢 **Multi-Tenancy**: Isolated tenant data and connections

    ### Supported Systems

    * **Odoo ERP**: Complete CRUD operations, 26 endpoints
    * **Moodle LMS**: Course, user, and enrolment management
    * **SAP ERP**: Coming soon
    * **Salesforce CRM**: Coming soon

    ### Quick Start

    1. Get a token from `/api/v1/auth/tenant/login`
    2. Use token in header: `Authorization: Bearer {token}`
    3. Start using the system-specific endpoints

    ### Support

    For help: support@bridgecore.com
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiter state
app.state.limiter = limiter

# Logging Middleware (first to execute - added last)
app.middleware("http")(logging_middleware)

# Admin Panel Middleware (Phase 2)
from app.middleware.usage_tracking import UsageTrackingMiddleware
from app.middleware.tenant_context import TenantContextMiddleware
from app.middleware.tenant_rate_limit import TenantRateLimitMiddleware
from app.middleware.ip_block_middleware import IPBlockMiddleware

app.add_middleware(UsageTrackingMiddleware)  # Track all tenant requests
app.add_middleware(TenantContextMiddleware)  # Validate tenant context
app.add_middleware(TenantRateLimitMiddleware)  # Enforce rate limits per tenant
app.add_middleware(IPBlockMiddleware)  # Block banned IPs (NEW)

# Prometheus Middleware
app.add_middleware(PrometheusMiddleware)

# Gzip Compression Middleware - Reduce response size by 70-90%
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS Middleware (last to execute - added first, handles OPTIONS requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(odoo.router)  # Legacy Odoo operations endpoint
app.include_router(odoo_operations_router, prefix="/api/v1")  # New 26 Odoo operations
app.include_router(systems.router)
app.include_router(batch.router)
app.include_router(barcode.router)
app.include_router(files.router)
app.include_router(websocket.router, prefix="/api/v1")

# Admin routers (NEW) - with /api prefix for clear separation from frontend routes
app.include_router(admin_auth.router, prefix="/api")  # /api/admin/auth/*
app.include_router(admin_tenants.router, prefix="/api")  # /api/admin/tenants/*
app.include_router(admin_tenant_users.router, prefix="/api")  # /api/admin/tenant-users/*
app.include_router(admin_plans.router, prefix="/api")  # /api/admin/plans/*
app.include_router(admin_analytics.router, prefix="/api")  # /api/admin/analytics/*
app.include_router(admin_logs.router, prefix="/api")  # /api/admin/logs/*
app.include_router(admin_odoo_helpers.router, prefix="/api")  # /api/admin/odoo-helpers/*
app.include_router(admin_systems.router, prefix="/api")  # /api/admin/systems/*
app.include_router(admin_alerts.router, prefix="/api")  # /api/admin/alerts/*
app.include_router(admin_ip_blocks.router, prefix="/api")  # /api/admin/ip-blocks/*

# Webhook routers (NEW)
app.include_router(webhook_router_v1.router)  # /api/v1/webhooks/*
app.include_router(webhook_router_v2.router)  # /api/v2/sync/*

# Offline Sync router (NEW)
app.include_router(offline_sync_router)  # /api/v1/offline-sync/*

# Odoo Sync router (Direct integration with auto-webhook-odoo)
app.include_router(odoo_sync_router)  # /api/v1/odoo-sync/*

# Moodle router (NEW)
app.include_router(moodle_router, prefix="/api/v1")  # /api/v1/moodle/*

# Triggers & Notifications routers (NEW)
app.include_router(triggers_router)  # /api/v1/triggers/*
app.include_router(notifications_router)  # /api/v1/notifications/*

# Conversation router (NEW)
app.include_router(conversation_router, prefix="/api/v1")  # /api/v1/conversations/*

# Add metrics endpoint
app.add_api_route("/metrics", metrics_endpoint, methods=["GET"], tags=["Monitoring"])


# Exception handlers
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors"""
    logger.warning(f"Rate limit exceeded: {request.client.host}")

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": {
                "type": "RateLimitExceeded",
                "message": "Too many requests. Please try again later.",
                "request_id": request.state.request_id if hasattr(request.state, "request_id") else None
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.error(f"Validation error: {exc.errors()}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "ValidationError",
                "message": "Invalid request data",
                "details": exc.errors(),
                "request_id": request.state.request_id if hasattr(request.state, "request_id") else None
            }
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper error formatting"""
    logger.error(
        f"HTTPException: {exc.status_code} - {exc.detail}\n"
        f"   Path: {request.url.path}\n"
        f"   Method: {request.method}\n"
        f"   Client IP: {request.client.host if request.client else 'unknown'}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method
        }
    )

    error_message = exc.detail
    if isinstance(exc.detail, dict):
        error_message = exc.detail.get("message", str(exc.detail))
    elif isinstance(exc.detail, str):
        error_message = exc.detail

    error_type_map = {
        400: "BadRequest",
        401: "Unauthorized",
        403: "Forbidden",
        404: "NotFound",
        409: "Conflict",
        422: "ValidationError",
        429: "RateLimitExceeded",
        500: "InternalServerError",
        503: "ServiceUnavailable"
    }
    error_type = error_type_map.get(exc.status_code, "HttpError")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": error_type,
                "message": error_message,
                "request_id": request.state.request_id if hasattr(request.state, "request_id") else None
            }
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    if isinstance(exc, HTTPException):
        raise exc
    
    logger.exception(
        f"Unhandled exception: {str(exc)}\n"
        f"   Path: {request.url.path}\n"
        f"   Method: {request.method}\n"
        f"   Client IP: {request.client.host if request.client else 'unknown'}"
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "InternalServerError",
                "message": "An unexpected error occurred on the server",
                "request_id": request.state.request_id if hasattr(request.state, "request_id") else None
            }
        }
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to FastAPI Middleware API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
