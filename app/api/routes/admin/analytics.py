"""
Admin analytics routes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from uuid import UUID

from app.db.session import get_db
from app.services.analytics_service import AnalyticsService
from app.api.routes.admin.dependencies import get_current_admin
from app.models.admin import Admin

router = APIRouter(prefix="/admin/analytics", tags=["Admin Analytics"])


@router.get("/overview")
async def get_system_overview(
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Get system-wide overview statistics

    Returns overall system metrics including:
    - Tenant counts by status
    - 24-hour usage statistics
    - Success rates
    - Data transfer volume

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - tenants: Breakdown by status (total, active, trial, suspended)
    - usage_24h: Last 24 hours metrics
    """
    analytics_service = AnalyticsService(db)
    return await analytics_service.get_system_overview()


@router.get("/top-tenants")
async def get_top_tenants(
    limit: int = Query(10, ge=1, le=50),
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
) -> List[Dict[str, Any]]:
    """
    Get top tenants by request volume

    Returns the most active tenants based on request count.

    **Query Parameters:**
    - limit: Number of top tenants to return (1-50, default: 10)
    - days: Number of days to analyze (1-90, default: 7)

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - List of tenants with usage metrics
    """
    analytics_service = AnalyticsService(db)
    return await analytics_service.get_top_tenants(limit=limit, days=days)


@router.get("/tenants/{tenant_id}")
async def get_tenant_analytics(
    tenant_id: UUID,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Get comprehensive analytics for a specific tenant

    **Path Parameters:**
    - tenant_id: Tenant UUID

    **Query Parameters:**
    - days: Number of days to analyze (1-365, default: 30)

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - summary: Request statistics and success rates
    - performance: Response time metrics
    - data_transfer: Data volume metrics
    - top_endpoints: Most used API endpoints
    - top_models: Most used Odoo models
    """
    analytics_service = AnalyticsService(db)
    return await analytics_service.get_tenant_analytics(tenant_id=tenant_id, days=days)


@router.get("/tenants/{tenant_id}/daily")
async def get_tenant_daily_stats(
    tenant_id: UUID,
    days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
) -> List[Dict[str, Any]]:
    """
    Get daily statistics for a tenant

    Returns time-series data showing daily request volumes and performance.

    **Path Parameters:**
    - tenant_id: Tenant UUID

    **Query Parameters:**
    - days: Number of days (1-90, default: 30)

    **Requires:**
    - Valid admin JWT token

    **Returns:**
    - Array of daily statistics with dates, request counts, and response times
    """
    analytics_service = AnalyticsService(db)
    return await analytics_service.get_tenant_daily_stats(tenant_id=tenant_id, days=days)
