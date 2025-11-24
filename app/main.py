"""
Main FastAPI Application
"""
from fastapi import FastAPI, Request, status
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
    odoo_helpers as admin_odoo_helpers
)
from app.modules.webhook import router as webhook_router_v1
from app.modules.webhook import router_v2 as webhook_router_v2
from app.modules.offline_sync import router as offline_sync_router
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
    ## FastAPI Middleware API

    This API serves as a middleware layer between Flutter applications and external systems (ERP/CRM).

    ### Features

    * 🔐 **Secure Authentication**: JWT-based authentication
    * 🔄 **Data Unification**: Automatic field mapping
    * 🎯 **Multi-System Support**: Odoo, SAP, Salesforce
    * ⚡ **High Performance**: Caching + Connection pooling
    * 📝 **Audit Trail**: Complete operation logging

    ### Quick Start

    1. Get a token from `/auth/login`
    2. Use token in header: `Authorization: Bearer {token}`
    3. Start using the CRUD endpoints

    ### Support

    For help: support@example.com
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

app.add_middleware(UsageTrackingMiddleware)  # Track all tenant requests
app.add_middleware(TenantContextMiddleware)  # Validate tenant context
app.add_middleware(TenantRateLimitMiddleware)  # Enforce rate limits per tenant

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
app.include_router(websocket.router)

# Admin routers (NEW)
app.include_router(admin_auth.router)  # /admin/auth/*
app.include_router(admin_tenants.router)  # /admin/tenants/*
app.include_router(admin_tenant_users.router)  # /admin/tenant-users/*
app.include_router(admin_plans.router)  # /admin/plans/*
app.include_router(admin_analytics.router)  # /admin/analytics/*
app.include_router(admin_logs.router)  # /admin/logs/*
app.include_router(admin_odoo_helpers.router)  # /admin/odoo-helpers/*

# Webhook routers (NEW)
app.include_router(webhook_router_v1.router)  # /api/v1/webhooks/*
app.include_router(webhook_router_v2.router)  # /api/v2/sync/*

# Offline Sync router (NEW)
app.include_router(offline_sync_router)  # /api/v1/offline-sync/*

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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.exception(f"Unhandled exception: {str(exc)}")

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
