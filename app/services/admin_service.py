"""
Admin service for admin user business logic
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from app.repositories.admin_repository import AdminRepository
from app.models.admin import Admin, AdminRole
from app.core.security import get_password_hash, verify_password, create_admin_token
from fastapi import HTTPException, status


class AdminService:
    """Service for admin user operations"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.admin_repo = AdminRepository(session)

    async def authenticate(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate admin user

        Args:
            email: Admin email
            password: Plain text password

        Returns:
            Dictionary with admin data and token, or None if authentication fails
        """
        from loguru import logger
        
        logger.info(f"[AUTH SERVICE] Authenticating user: {email}")
        
        admin = await self.admin_repo.get_by_email(email)

        if not admin:
            logger.warning(f"[AUTH SERVICE] Admin not found: {email}")
            return None

        logger.debug(f"[AUTH SERVICE] Admin found: {admin.email}, ID: {admin.id}, Active: {admin.is_active}")
        
        password_valid = verify_password(password, admin.hashed_password)
        logger.debug(f"[AUTH SERVICE] Password verification result: {password_valid}")
        
        if not password_valid:
            logger.warning(f"[AUTH SERVICE] Invalid password for: {email}")
            return None

        if not admin.is_active:
            logger.warning(f"[AUTH SERVICE] Account deactivated: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin account is deactivated"
            )

        # Update last login
        admin.last_login = datetime.utcnow()
        await self.session.commit()

        # Create token
        token = create_admin_token(
            admin_id=str(admin.id),
            email=admin.email,
            role=admin.role.value
        )

        logger.info(f"[AUTH SERVICE] Authentication successful: {email}")

        return {
            "admin": {
                "id": str(admin.id),
                "email": admin.email,
                "full_name": admin.full_name,
                "role": admin.role.value,
                "is_active": admin.is_active,
                "last_login": admin.last_login.isoformat() if admin.last_login else None
            },
            "token": token
        }

    async def create_admin(
        self,
        email: str,
        password: str,
        full_name: str,
        role: AdminRole = AdminRole.ADMIN
    ) -> Admin:
        """
        Create a new admin user

        Args:
            email: Admin email
            password: Plain text password
            full_name: Admin full name
            role: Admin role (default: ADMIN)

        Returns:
            Created admin instance

        Raises:
            HTTPException: If email is already taken
        """
        # Check if email exists
        if await self.admin_repo.is_email_taken(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create admin
        admin = Admin(
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role=role,
            is_active=True
        )

        return await self.admin_repo.create(admin)

    async def get_admin(self, admin_id: UUID) -> Optional[Admin]:
        """
        Get admin by ID

        Args:
            admin_id: Admin UUID

        Returns:
            Admin instance or None
        """
        return await self.admin_repo.get_by_id_uuid(admin_id)

    async def get_admin_by_email(self, email: str) -> Optional[Admin]:
        """
        Get admin by email

        Args:
            email: Admin email

        Returns:
            Admin instance or None
        """
        return await self.admin_repo.get_by_email(email)

    async def list_admins(self, skip: int = 0, limit: int = 100) -> List[Admin]:
        """
        List all admins with pagination

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of admins
        """
        return await self.admin_repo.get_multi(skip=skip, limit=limit, order_by="-created_at")

    async def update_admin(
        self,
        admin_id: UUID,
        data: Dict[str, Any]
    ) -> Optional[Admin]:
        """
        Update admin user

        Args:
            admin_id: Admin UUID
            data: Dictionary of fields to update

        Returns:
            Updated admin instance or None

        Raises:
            HTTPException: If email is already taken by another admin
        """
        admin = await self.admin_repo.get_by_id_uuid(admin_id)
        if not admin:
            return None

        # Check email uniqueness if updating email
        if "email" in data and data["email"] != admin.email:
            if await self.admin_repo.is_email_taken(data["email"], exclude_id=admin_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

        # Hash password if updating
        if "password" in data:
            data["hashed_password"] = get_password_hash(data.pop("password"))

        # Update fields
        for key, value in data.items():
            if hasattr(admin, key):
                setattr(admin, key, value)

        await self.session.commit()
        await self.session.refresh(admin)
        return admin

    async def deactivate_admin(self, admin_id: UUID) -> bool:
        """
        Deactivate admin account

        Args:
            admin_id: Admin UUID

        Returns:
            True if deactivated, False if admin not found
        """
        admin = await self.admin_repo.get_by_id_uuid(admin_id)
        if not admin:
            return False

        admin.is_active = False
        await self.session.commit()
        return True

    async def activate_admin(self, admin_id: UUID) -> bool:
        """
        Activate admin account

        Args:
            admin_id: Admin UUID

        Returns:
            True if activated, False if admin not found
        """
        admin = await self.admin_repo.get_by_id_uuid(admin_id)
        if not admin:
            return False

        admin.is_active = True
        await self.session.commit()
        return True
