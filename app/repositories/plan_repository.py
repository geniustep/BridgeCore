"""
Plan repository for subscription plan data access
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from app.repositories.base_repository import BaseRepository
from app.models.plan import Plan
from uuid import UUID


class PlanRepository(BaseRepository[Plan]):
    """Repository for plan operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(Plan, session)

    async def get_by_name(self, name: str) -> Optional[Plan]:
        """
        Get plan by name

        Args:
            name: Plan name

        Returns:
            Plan instance or None
        """
        query = select(Plan).where(Plan.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id_uuid(self, plan_id: UUID) -> Optional[Plan]:
        """
        Get plan by UUID

        Args:
            plan_id: Plan UUID

        Returns:
            Plan instance or None
        """
        query = select(Plan).where(Plan.id == plan_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_active_plans(self) -> List[Plan]:
        """
        Get all active plans

        Returns:
            List of active plans
        """
        query = select(Plan).where(Plan.is_active == True).order_by(Plan.price_monthly)
        result = await self.session.execute(query)
        return result.scalars().all()
