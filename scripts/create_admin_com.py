#!/usr/bin/env python3
"""Create admin user with admin@bridgecore.com"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import uuid

from app.core.config import settings
from app.models.admin import Admin, AdminRole
from app.core.security import get_password_hash


async def create_admin():
    """Create admin user with admin@bridgecore.com"""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if admin already exists
        result = await session.execute(
            select(Admin).where(Admin.email == "admin@bridgecore.com")
        )
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print("✅ Admin user already exists: admin@bridgecore.com")
            # Update password to be sure
            existing_admin.hashed_password = get_password_hash("admin123")
            await session.commit()
            print("✅ Password updated to: admin123")
            return

        # Create admin
        admin = Admin(
            id=uuid.uuid4(),
            email="admin@bridgecore.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Super Admin",
            role=AdminRole.SUPER_ADMIN,
            is_active=True
        )

        session.add(admin)
        await session.commit()
        print("✅ Created admin user:")
        print("   Email: admin@bridgecore.com")
        print("   Password: admin123")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_admin())

