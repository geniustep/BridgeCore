"""
Analytics service for generating statistics and insights
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Dict, Any, List
from datetime import datetime, date, timedelta
from uuid import UUID

from app.repositories.log_repository import UsageLogRepository, UsageStatsRepository
from app.repositories.tenant_repository import TenantRepository
from app.models.usage_log import UsageLog
from app.models.usage_stats import UsageStats
from app.models.tenant import TenantStatus


class AnalyticsService:
    """Service for analytics and statistics"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.usage_repo = UsageLogRepository(session)
        self.stats_repo = UsageStatsRepository(session)
        self.tenant_repo = TenantRepository(session)

    # ========================================================================
    # System-Wide Analytics (Admin)
    # ========================================================================

    async def get_system_overview(self) -> Dict[str, Any]:
        """
        Get system-wide overview statistics

        Returns:
            Dictionary with system metrics
        """
        # Tenant statistics
        total_tenants = await self.tenant_repo.count()
        active_tenants = await self.tenant_repo.count_by_status(TenantStatus.ACTIVE)
        trial_tenants = await self.tenant_repo.count_by_status(TenantStatus.TRIAL)
        suspended_tenants = await self.tenant_repo.count_by_status(TenantStatus.SUSPENDED)

        # Usage statistics (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(hours=24)

        query = select(
            func.count(UsageLog.id).label("total_requests"),
            func.avg(UsageLog.response_time_ms).label("avg_response_time"),
            func.sum(UsageLog.request_size_bytes + UsageLog.response_size_bytes).label("total_data")
        ).where(UsageLog.timestamp >= yesterday)

        result = await self.session.execute(query)
        usage_stats = result.first()

        total_requests = usage_stats.total_requests or 0
        avg_response_time = round(usage_stats.avg_response_time or 0, 2)
        total_data_mb = round((usage_stats.total_data or 0) / (1024 * 1024), 2)

        # Success rate (last 24 hours)
        success_query = select(func.count(UsageLog.id)).where(
            and_(
                UsageLog.timestamp >= yesterday,
                UsageLog.status_code >= 200,
                UsageLog.status_code < 300
            )
        )
        success_result = await self.session.execute(success_query)
        successful_requests = success_result.scalar() or 0

        success_rate = round((successful_requests / total_requests * 100), 2) if total_requests > 0 else 0

        return {
            "tenants": {
                "total": total_tenants,
                "active": active_tenants,
                "trial": trial_tenants,
                "suspended": suspended_tenants
            },
            "usage_24h": {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "success_rate_percent": success_rate,
                "avg_response_time_ms": avg_response_time,
                "total_data_transferred_mb": total_data_mb
            }
        }

    async def get_top_tenants(self, limit: int = 10, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get top tenants by request volume

        Args:
            limit: Number of top tenants to return
            days: Number of days to analyze

        Returns:
            List of top tenants with their usage
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        query = select(
            UsageLog.tenant_id,
            func.count(UsageLog.id).label("request_count"),
            func.avg(UsageLog.response_time_ms).label("avg_response_time")
        ).where(
            UsageLog.timestamp >= start_date
        ).group_by(
            UsageLog.tenant_id
        ).order_by(
            func.count(UsageLog.id).desc()
        ).limit(limit)

        result = await self.session.execute(query)
        top_usage = result.all()

        top_tenants = []
        for row in top_usage:
            tenant = await self.tenant_repo.get_by_id_uuid(row.tenant_id)
            if tenant:
                top_tenants.append({
                    "tenant_id": str(tenant.id),
                    "tenant_name": tenant.name,
                    "tenant_slug": tenant.slug,
                    "request_count": row.request_count,
                    "avg_response_time_ms": round(row.avg_response_time or 0, 2)
                })

        return top_tenants

    # ========================================================================
    # Tenant-Specific Analytics
    # ========================================================================

    async def get_tenant_analytics(
        self,
        tenant_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a tenant

        Args:
            tenant_id: Tenant UUID
            days: Number of days to analyze

        Returns:
            Dictionary with tenant analytics
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Request statistics
        query = select(
            func.count(UsageLog.id).label("total_requests"),
            func.avg(UsageLog.response_time_ms).label("avg_response_time"),
            func.max(UsageLog.response_time_ms).label("max_response_time"),
            func.min(UsageLog.response_time_ms).label("min_response_time"),
            func.sum(UsageLog.request_size_bytes + UsageLog.response_size_bytes).label("total_data"),
            func.count(func.distinct(UsageLog.user_id)).label("unique_users")
        ).where(
            and_(
                UsageLog.tenant_id == tenant_id,
                UsageLog.timestamp >= start_date
            )
        )

        result = await self.session.execute(query)
        stats = result.first()

        # Success/failure breakdown
        success_query = select(func.count(UsageLog.id)).where(
            and_(
                UsageLog.tenant_id == tenant_id,
                UsageLog.timestamp >= start_date,
                UsageLog.status_code >= 200,
                UsageLog.status_code < 300
            )
        )
        success_result = await self.session.execute(success_query)
        successful_requests = success_result.scalar() or 0

        failed_requests = (stats.total_requests or 0) - successful_requests

        # Most used endpoints
        endpoint_query = select(
            UsageLog.endpoint,
            func.count(UsageLog.id).label("count")
        ).where(
            and_(
                UsageLog.tenant_id == tenant_id,
                UsageLog.timestamp >= start_date
            )
        ).group_by(
            UsageLog.endpoint
        ).order_by(
            func.count(UsageLog.id).desc()
        ).limit(5)

        endpoint_result = await self.session.execute(endpoint_query)
        top_endpoints = [
            {"endpoint": row.endpoint, "count": row.count}
            for row in endpoint_result.all()
        ]

        # Most used models
        model_query = select(
            UsageLog.model_name,
            func.count(UsageLog.id).label("count")
        ).where(
            and_(
                UsageLog.tenant_id == tenant_id,
                UsageLog.timestamp >= start_date,
                UsageLog.model_name.isnot(None)
            )
        ).group_by(
            UsageLog.model_name
        ).order_by(
            func.count(UsageLog.id).desc()
        ).limit(5)

        model_result = await self.session.execute(model_query)
        top_models = [
            {"model": row.model_name, "count": row.count}
            for row in model_result.all()
        ]

        return {
            "summary": {
                "total_requests": stats.total_requests or 0,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate_percent": round((successful_requests / stats.total_requests * 100), 2) if stats.total_requests else 0,
                "unique_users": stats.unique_users or 0
            },
            "performance": {
                "avg_response_time_ms": round(stats.avg_response_time or 0, 2),
                "max_response_time_ms": stats.max_response_time or 0,
                "min_response_time_ms": stats.min_response_time or 0
            },
            "data_transfer": {
                "total_bytes": stats.total_data or 0,
                "total_mb": round((stats.total_data or 0) / (1024 * 1024), 2),
                "total_gb": round((stats.total_data or 0) / (1024 * 1024 * 1024), 3)
            },
            "top_endpoints": top_endpoints,
            "top_models": top_models,
            "period_days": days
        }

    async def get_tenant_daily_stats(
        self,
        tenant_id: UUID,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get daily statistics for a tenant

        Args:
            tenant_id: Tenant UUID
            days: Number of days

        Returns:
            List of daily stats
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Try to get from aggregated stats first
        stats = await self.stats_repo.get_tenant_daily_stats(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date
        )

        if stats:
            return [
                {
                    "date": stat.date.isoformat(),
                    "total_requests": stat.total_requests,
                    "successful_requests": stat.successful_requests,
                    "failed_requests": stat.failed_requests,
                    "avg_response_time_ms": stat.avg_response_time_ms,
                    "unique_users": stat.unique_users
                }
                for stat in stats
            ]

        # If no aggregated stats, calculate from raw logs
        query = select(
            func.date(UsageLog.timestamp).label("date"),
            func.count(UsageLog.id).label("total_requests"),
            func.avg(UsageLog.response_time_ms).label("avg_response_time")
        ).where(
            and_(
                UsageLog.tenant_id == tenant_id,
                UsageLog.timestamp >= datetime.combine(start_date, datetime.min.time())
            )
        ).group_by(
            func.date(UsageLog.timestamp)
        ).order_by(
            func.date(UsageLog.timestamp)
        )

        result = await self.session.execute(query)
        daily_stats = [
            {
                "date": row.date.isoformat(),
                "total_requests": row.total_requests,
                "avg_response_time_ms": round(row.avg_response_time or 0, 2)
            }
            for row in result.all()
        ]

        return daily_stats
