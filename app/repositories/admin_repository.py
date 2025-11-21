"""
Admin repository for admin user data access
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.repositories.base_repository import BaseRepository
from app.models.admin import Admin
from uuid import UUID


class AdminRepository(BaseRepository[Admin]):
    """Repository for admin user operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(Admin, session)

    async def get_by_email(self, email: str) -> Optional[Admin]:
        """
        Get admin by email

        Args:
            email: Admin email address

        Returns:
            Admin instance or None
        """
        query = select(Admin).where(Admin.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id_uuid(self, admin_id: UUID) -> Optional[Admin]:
        """
        Get admin by UUID

        Args:
            admin_id: Admin UUID

        Returns:
            Admin instance or None
        """
        query = select(Admin).where(Admin.id == admin_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def is_email_taken(self, email: str, exclude_id: Optional[UUID] = None) -> bool:
        """
        Check if email is already taken

        Args:
            email: Email to check
            exclude_id: Optional admin ID to exclude from check (for updates)

        Returns:
            True if email is taken, False otherwise
        """
        query = select(Admin).where(Admin.email == email)
        if exclude_id:
            query = query.where(Admin.id != exclude_id)

        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
