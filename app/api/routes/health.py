"""
Health check API routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db
from datetime import datetime
from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT
    }


@router.get("/health/db")
async def database_health_check(db: AsyncSession = Depends(get_db)):
    """
    Database health check endpoint

    Args:
        db: Database session

    Returns:
        Database health status
    """
    try:
        # Execute simple query
        result = await db.execute(text("SELECT 1"))
        result.scalar_one()

        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/health/redis")
async def redis_health_check():
    """
    Redis health check endpoint

    Returns:
        Redis health status
    """
    try:
        from app.services.cache_service import CacheService

        cache = CacheService(settings.REDIS_URL)

        # Test Redis connection
        test_key = "health_check"
        await cache.set(test_key, "ok", ttl=10)
        value = await cache.get(test_key)
        await cache.delete(test_key)

        await cache.close()

        if value == "ok":
            return {
                "status": "healthy",
                "redis": "connected",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "status": "unhealthy",
                "redis": "connection_error",
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "redis": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
