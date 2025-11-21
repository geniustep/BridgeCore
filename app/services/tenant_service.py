"""
Tenant service for tenant business logic
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
import httpx

from app.repositories.tenant_repository import TenantRepository
from app.repositories.plan_repository import PlanRepository
from app.models.tenant import Tenant, TenantStatus
from app.core.security import get_password_hash
from fastapi import HTTPException, status


class TenantService:
    """Service for tenant operations"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.tenant_repo = TenantRepository(session)
        self.plan_repo = PlanRepository(session)

    async def create_tenant(
        self,
        name: str,
        slug: str,
        contact_email: str,
        odoo_url: str,
        odoo_database: str,
        odoo_username: str,
        odoo_password: str,
        plan_id: UUID,
        created_by: Optional[UUID] = None,
        **kwargs
    ) -> Tenant:
        """
        Create a new tenant

        Args:
            name: Tenant name
            slug: Unique slug
            contact_email: Contact email
            odoo_url: Odoo instance URL
            odoo_database: Odoo database name
            odoo_username: Odoo username
            odoo_password: Odoo password (will be encrypted)
            plan_id: Subscription plan ID
            created_by: Admin ID who created the tenant
            **kwargs: Additional optional fields

        Returns:
            Created tenant instance

        Raises:
            HTTPException: If slug is taken or plan doesn't exist
        """
        # Check if slug is taken
        if await self.tenant_repo.is_slug_taken(slug):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Slug already taken"
            )

        # Verify plan exists
        plan = await self.plan_repo.get_by_id_uuid(plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found"
            )

        # Create tenant
        tenant = Tenant(
            name=name,
            slug=slug,
            contact_email=contact_email,
            odoo_url=odoo_url,
            odoo_database=odoo_database,
            odoo_username=odoo_username,
            odoo_password=get_password_hash(odoo_password),  # Encrypt password
            plan_id=plan_id,
            status=TenantStatus.TRIAL,
            created_by=created_by,
            **kwargs
        )

        return await self.tenant_repo.create(tenant)

    async def get_tenant(self, tenant_id: UUID) -> Optional[Tenant]:
        """
        Get tenant by ID

        Args:
            tenant_id: Tenant UUID

        Returns:
            Tenant instance or None
        """
        return await self.tenant_repo.get_by_id_uuid(tenant_id)

    async def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """
        Get tenant by slug

        Args:
            slug: Tenant slug

        Returns:
            Tenant instance or None
        """
        return await self.tenant_repo.get_by_slug(slug)

    async def list_tenants(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TenantStatus] = None
    ) -> List[Tenant]:
        """
        List tenants with pagination and optional status filter

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Optional status filter

        Returns:
            List of tenants
        """
        filters = {"status": status} if status else None
        return await self.tenant_repo.get_multi(
            skip=skip,
            limit=limit,
            filters=filters,
            order_by="-created_at"
        )

    async def update_tenant(
        self,
        tenant_id: UUID,
        data: Dict[str, Any]
    ) -> Optional[Tenant]:
        """
        Update tenant

        Args:
            tenant_id: Tenant UUID
            data: Dictionary of fields to update

        Returns:
            Updated tenant instance or None

        Raises:
            HTTPException: If slug is already taken by another tenant
        """
        tenant = await self.tenant_repo.get_by_id_uuid(tenant_id)
        if not tenant:
            return None

        # Check slug uniqueness if updating slug
        if "slug" in data and data["slug"] != tenant.slug:
            if await self.tenant_repo.is_slug_taken(data["slug"], exclude_id=tenant_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Slug already taken"
                )

        # Encrypt password if updating
        if "odoo_password" in data:
            data["odoo_password"] = get_password_hash(data["odoo_password"])

        # Update fields
        for key, value in data.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)

        await self.session.commit()
        await self.session.refresh(tenant)
        return tenant

    async def suspend_tenant(self, tenant_id: UUID) -> bool:
        """
        Suspend tenant

        Args:
            tenant_id: Tenant UUID

        Returns:
            True if suspended, False if tenant not found
        """
        tenant = await self.tenant_repo.get_by_id_uuid(tenant_id)
        if not tenant:
            return False

        tenant.status = TenantStatus.SUSPENDED
        await self.session.commit()
        return True

    async def activate_tenant(self, tenant_id: UUID) -> bool:
        """
        Activate tenant

        Args:
            tenant_id: Tenant UUID

        Returns:
            True if activated, False if tenant not found
        """
        tenant = await self.tenant_repo.get_by_id_uuid(tenant_id)
        if not tenant:
            return False

        tenant.status = TenantStatus.ACTIVE
        await self.session.commit()
        return True

    async def delete_tenant(self, tenant_id: UUID) -> bool:
        """
        Soft delete tenant

        Args:
            tenant_id: Tenant UUID

        Returns:
            True if deleted, False if tenant not found
        """
        tenant = await self.tenant_repo.get_by_id_uuid(tenant_id)
        if not tenant:
            return False

        tenant.status = TenantStatus.DELETED
        tenant.deleted_at = datetime.utcnow()
        await self.session.commit()
        return True

    async def test_odoo_connection(self, tenant_id: UUID) -> Dict[str, Any]:
        """
        Test Odoo connection for a tenant

        Args:
            tenant_id: Tenant UUID

        Returns:
            Dictionary with connection test results

        Raises:
            HTTPException: If tenant not found
        """
        tenant = await self.tenant_repo.get_by_id_uuid(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )

        try:
            # Test connection by calling Odoo's version endpoint
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{tenant.odoo_url}/web/database/selector")

                if response.status_code == 200:
                    return {
                        "success": True,
                        "message": "Odoo instance is reachable",
                        "url": tenant.odoo_url
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Odoo instance returned status code {response.status_code}",
                        "url": tenant.odoo_url
                    }

        except httpx.TimeoutException:
            return {
                "success": False,
                "message": "Connection timeout",
                "url": tenant.odoo_url
            }
        except httpx.RequestError as e:
            return {
                "success": False,
                "message": f"Connection error: {str(e)}",
                "url": tenant.odoo_url
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)}",
                "url": tenant.odoo_url
            }

    async def get_tenant_statistics(self) -> Dict[str, Any]:
        """
        Get overall tenant statistics

        Returns:
            Dictionary with tenant statistics
        """
        total = await self.tenant_repo.count()
        active = await self.tenant_repo.count_by_status(TenantStatus.ACTIVE)
        suspended = await self.tenant_repo.count_by_status(TenantStatus.SUSPENDED)
        trial = await self.tenant_repo.count_by_status(TenantStatus.TRIAL)
        deleted = await self.tenant_repo.count_by_status(TenantStatus.DELETED)

        return {
            "total": total,
            "active": active,
            "suspended": suspended,
            "trial": trial,
            "deleted": deleted
        }
