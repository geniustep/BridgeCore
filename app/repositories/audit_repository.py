"""
Audit Log Repository
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timedelta
from app.models.audit_log import AuditLog
from app.repositories.base_repository import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    """Repository for audit log operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(AuditLog, session)

    async def get_by_user(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """Get audit logs for a specific user"""
        query = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_system(
        self,
        system_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for a specific system with optional date range"""
        query = (
            select(self.model)
            .where(self.model.system_id == system_id)
        )

        if start_date:
            query = query.where(self.model.timestamp >= start_date)
        if end_date:
            query = query.where(self.model.timestamp <= end_date)

        query = query.order_by(self.model.timestamp.desc()).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_failed_operations(
        self,
        system_id: Optional[int] = None,
        hours: int = 24
    ) -> List[AuditLog]:
        """Get failed operations within the last N hours"""
        time_threshold = datetime.utcnow() - timedelta(hours=hours)

        query = (
            select(self.model)
            .where(self.model.status == "error")
            .where(self.model.timestamp >= time_threshold)
        )

        if system_id:
            query = query.where(self.model.system_id == system_id)

        query = query.order_by(self.model.timestamp.desc())

        result = await self.session.execute(query)
        return result.scalars().all()
