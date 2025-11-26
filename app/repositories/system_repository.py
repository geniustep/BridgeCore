"""
Repository for ExternalSystem and TenantSystem management
"""
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from uuid import UUID
from loguru import logger

from app.models.external_system import ExternalSystem, TenantSystem, SystemType, SystemStatus
from app.repositories.base_repository import BaseRepository


class ExternalSystemRepository(BaseRepository[ExternalSystem]):
    """Repository for managing external systems (Odoo, Moodle, SAP, etc.)"""

    def __init__(self, session: AsyncSession):
        super().__init__(ExternalSystem, session)

    async def get_by_type(self, system_type: SystemType) -> Optional[ExternalSystem]:
        """Get system by type"""
        query = select(ExternalSystem).where(
            ExternalSystem.system_type == system_type
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_enabled_systems(self) -> List[ExternalSystem]:
        """Get all enabled systems"""
        query = select(ExternalSystem).where(
            and_(
                ExternalSystem.is_enabled == True,
                ExternalSystem.status == SystemStatus.ACTIVE
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all_systems(self) -> List[ExternalSystem]:
        """Get all systems"""
        query = select(ExternalSystem)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class TenantSystemRepository(BaseRepository[TenantSystem]):
    """Repository for managing tenant-system connections"""

    def __init__(self, session: AsyncSession):
        super().__init__(TenantSystem, session)

    async def get_by_tenant(
        self,
        tenant_id: UUID,
        active_only: bool = True
    ) -> List[TenantSystem]:
        """
        Get all systems connected to a tenant

        Args:
            tenant_id: Tenant ID
            active_only: Only return active connections

        Returns:
            List of tenant system connections
        """
        conditions = [TenantSystem.tenant_id == tenant_id]

        if active_only:
            conditions.append(TenantSystem.is_active == True)

        query = select(TenantSystem).where(
            and_(*conditions)
        ).options(
            selectinload(TenantSystem.external_system)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_tenant_and_type(
        self,
        tenant_id: UUID,
        system_type: SystemType
    ) -> Optional[TenantSystem]:
        """
        Get specific system connection for a tenant

        Args:
            tenant_id: Tenant ID
            system_type: System type (odoo, moodle, etc.)

        Returns:
            TenantSystem connection or None
        """
        query = select(TenantSystem).join(
            ExternalSystem
        ).where(
            and_(
                TenantSystem.tenant_id == tenant_id,
                ExternalSystem.system_type == system_type
            )
        ).options(
            selectinload(TenantSystem.external_system)
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_primary_system(
        self,
        tenant_id: UUID
    ) -> Optional[TenantSystem]:
        """Get primary system for a tenant"""
        query = select(TenantSystem).where(
            and_(
                TenantSystem.tenant_id == tenant_id,
                TenantSystem.is_primary == True,
                TenantSystem.is_active == True
            )
        ).options(
            selectinload(TenantSystem.external_system)
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def set_primary(
        self,
        tenant_id: UUID,
        system_id: UUID
    ) -> bool:
        """
        Set a system as primary for a tenant (unsets others)

        Args:
            tenant_id: Tenant ID
            system_id: System ID to set as primary

        Returns:
            True if successful
        """
        # Unset all primary flags for this tenant
        query_unset = select(TenantSystem).where(
            TenantSystem.tenant_id == tenant_id
        )
        result = await self.session.execute(query_unset)
        connections = result.scalars().all()

        for conn in connections:
            conn.is_primary = False

        # Set the new primary
        query_set = select(TenantSystem).where(
            and_(
                TenantSystem.tenant_id == tenant_id,
                TenantSystem.system_id == system_id
            )
        )
        result = await self.session.execute(query_set)
        connection = result.scalar_one_or_none()

        if connection:
            connection.is_primary = True
            await self.session.commit()
            return True

        return False

    async def check_exists(
        self,
        tenant_id: UUID,
        system_id: UUID
    ) -> bool:
        """Check if connection already exists"""
        query = select(TenantSystem).where(
            and_(
                TenantSystem.tenant_id == tenant_id,
                TenantSystem.system_id == system_id
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def update_connection_status(
        self,
        connection_id: UUID,
        success: bool,
        error_message: Optional[str] = None
    ) -> None:
        """Update connection test results"""
        from datetime import datetime

        connection = await self.get_by_id(connection_id)
        if connection:
            connection.last_connection_test = datetime.utcnow()
            if success:
                connection.last_successful_connection = datetime.utcnow()
                connection.connection_error = None
            else:
                connection.connection_error = error_message

            await self.session.commit()

    async def get_by_system_type(
        self,
        system_type: SystemType,
        active_only: bool = True
    ) -> List[TenantSystem]:
        """Get all tenant connections for a specific system type"""
        conditions = [ExternalSystem.system_type == system_type]

        if active_only:
            conditions.append(TenantSystem.is_active == True)

        query = select(TenantSystem).join(
            ExternalSystem
        ).where(
            and_(*conditions)
        ).options(
            selectinload(TenantSystem.external_system),
            selectinload(TenantSystem.tenant)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())
