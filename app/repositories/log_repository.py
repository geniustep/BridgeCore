"""
Log repositories for usage and error logs
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from app.repositories.base_repository import BaseRepository
from app.models.usage_log import UsageLog
from app.models.error_log import ErrorLog, ErrorSeverity
from app.models.usage_stats import UsageStats
from uuid import UUID


class UsageLogRepository(BaseRepository[UsageLog]):
    """Repository for usage log operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(UsageLog, session)

    async def get_tenant_logs(
        self,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[UsageLog]:
        """
        Get usage logs for a tenant with optional date filtering

        Args:
            tenant_id: Tenant UUID
            skip: Number of records to skip
            limit: Maximum number of records to return
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of usage logs
        """
        query = select(UsageLog).where(UsageLog.tenant_id == tenant_id)

        if start_date:
            query = query.where(UsageLog.timestamp >= start_date)
        if end_date:
            query = query.where(UsageLog.timestamp <= end_date)

        query = query.order_by(UsageLog.timestamp.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_tenant_requests(
        self,
        tenant_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """
        Count total requests for a tenant in a time period

        Args:
            tenant_id: Tenant UUID
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Number of requests
        """
        query = select(func.count()).select_from(UsageLog).where(UsageLog.tenant_id == tenant_id)

        if start_date:
            query = query.where(UsageLog.timestamp >= start_date)
        if end_date:
            query = query.where(UsageLog.timestamp <= end_date)

        result = await self.session.execute(query)
        return result.scalar()


class ErrorLogRepository(BaseRepository[ErrorLog]):
    """Repository for error log operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(ErrorLog, session)

    async def get_tenant_errors(
        self,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 100,
        severity: Optional[ErrorSeverity] = None,
        unresolved_only: bool = False
    ) -> List[ErrorLog]:
        """
        Get error logs for a tenant with filtering

        Args:
            tenant_id: Tenant UUID
            skip: Number of records to skip
            limit: Maximum number of records to return
            severity: Optional severity filter
            unresolved_only: If True, only return unresolved errors

        Returns:
            List of error logs
        """
        query = select(ErrorLog).where(ErrorLog.tenant_id == tenant_id)

        if severity:
            query = query.where(ErrorLog.severity == severity)
        if unresolved_only:
            query = query.where(ErrorLog.is_resolved == False)

        query = query.order_by(ErrorLog.timestamp.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_unresolved_errors(self, tenant_id: UUID) -> int:
        """
        Count unresolved errors for a tenant

        Args:
            tenant_id: Tenant UUID

        Returns:
            Number of unresolved errors
        """
        query = (
            select(func.count())
            .select_from(ErrorLog)
            .where(and_(ErrorLog.tenant_id == tenant_id, ErrorLog.is_resolved == False))
        )
        result = await self.session.execute(query)
        return result.scalar()


class UsageStatsRepository(BaseRepository[UsageStats]):
    """Repository for usage statistics operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(UsageStats, session)

    async def get_tenant_daily_stats(
        self,
        tenant_id: UUID,
        start_date: date,
        end_date: date
    ) -> List[UsageStats]:
        """
        Get daily statistics for a tenant

        Args:
            tenant_id: Tenant UUID
            start_date: Start date
            end_date: End date

        Returns:
            List of daily usage stats
        """
        query = (
            select(UsageStats)
            .where(
                and_(
                    UsageStats.tenant_id == tenant_id,
                    UsageStats.hour.is_(None),  # Daily stats have hour = NULL
                    UsageStats.date >= start_date,
                    UsageStats.date <= end_date
                )
            )
            .order_by(UsageStats.date)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_tenant_hourly_stats(
        self,
        tenant_id: UUID,
        date: date
    ) -> List[UsageStats]:
        """
        Get hourly statistics for a tenant on a specific date

        Args:
            tenant_id: Tenant UUID
            date: Date to get hourly stats for

        Returns:
            List of hourly usage stats
        """
        query = (
            select(UsageStats)
            .where(
                and_(
                    UsageStats.tenant_id == tenant_id,
                    UsageStats.hour.isnot(None),  # Hourly stats have hour set
                    UsageStats.date == date
                )
            )
            .order_by(UsageStats.hour)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
