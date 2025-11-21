"""
Tenant User Repository
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tenant_user import TenantUser


class TenantUserRepository:
    """Repository for tenant user operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: UUID) -> Optional[TenantUser]:
        """Get tenant user by ID"""
        query = select(TenantUser).where(TenantUser.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[TenantUser]:
        """Get tenant user by email"""
        query = select(TenantUser).where(TenantUser.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_tenant_id(self, tenant_id: UUID) -> List[TenantUser]:
        """Get all users for a tenant"""
        query = select(TenantUser).where(TenantUser.tenant_id == tenant_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create(self, user: TenantUser) -> TenantUser:
        """Create new tenant user"""
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update(self, user: TenantUser) -> TenantUser:
        """Update tenant user"""
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete(self, user_id: UUID) -> bool:
        """Delete tenant user"""
        user = await self.get_by_id(user_id)
        if user:
            await self.session.delete(user)
            await self.session.commit()
            return True
        return False