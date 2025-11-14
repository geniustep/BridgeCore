"""
Main FastAPI Application
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from loguru import logger

from app.core.config import settings
from app.utils.logger import setup_logging
from app.middleware.logging_middleware import logging_middleware
from app.db.session import init_db, close_db
from app.api.routes import auth, health


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

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging Middleware
app.middleware("http")(logging_middleware)

# Include routers
app.include_router(health.router)
app.include_router(auth.router)


# Exception handlers
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
