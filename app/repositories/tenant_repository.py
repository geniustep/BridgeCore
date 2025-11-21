"""
Tenant repository for tenant data access
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from datetime import datetime
from app.repositories.base_repository import BaseRepository
from app.models.tenant import Tenant, TenantStatus
from uuid import UUID


class TenantRepository(BaseRepository[Tenant]):
    """Repository for tenant operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(Tenant, session)

    async def get_by_slug(self, slug: str) -> Optional[Tenant]:
        """
        Get tenant by slug

        Args:
            slug: Tenant slug

        Returns:
            Tenant instance or None
        """
        query = select(Tenant).where(Tenant.slug == slug)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id_uuid(self, tenant_id: UUID) -> Optional[Tenant]:
        """
        Get tenant by UUID

        Args:
            tenant_id: Tenant UUID

        Returns:
            Tenant instance or None
        """
        query = select(Tenant).where(Tenant.id == tenant_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def is_slug_taken(self, slug: str, exclude_id: Optional[UUID] = None) -> bool:
        """
        Check if slug is already taken

        Args:
            slug: Slug to check
            exclude_id: Optional tenant ID to exclude from check (for updates)

        Returns:
            True if slug is taken, False otherwise
        """
        query = select(Tenant).where(Tenant.slug == slug)
        if exclude_id:
            query = query.where(Tenant.id != exclude_id)

        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_active_tenants(self, skip: int = 0, limit: int = 100) -> List[Tenant]:
        """
        Get all active tenants

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active tenants
        """
        query = (
            select(Tenant)
            .where(Tenant.status == TenantStatus.ACTIVE)
            .order_by(Tenant.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_by_status(self, status: TenantStatus) -> int:
        """
        Count tenants by status

        Args:
            status: Tenant status

        Returns:
            Number of tenants with given status
        """
        query = select(func.count()).select_from(Tenant).where(Tenant.status == status)
        result = await self.session.execute(query)
        return result.scalar()

    async def update_last_active(self, tenant_id: UUID) -> None:
        """
        Update tenant's last active timestamp

        Args:
            tenant_id: Tenant UUID
        """
        query = select(Tenant).where(Tenant.id == tenant_id)
        result = await self.session.execute(query)
        tenant = result.scalar_one_or_none()

        if tenant:
            tenant.last_active_at = datetime.utcnow()
            await self.session.commit()
