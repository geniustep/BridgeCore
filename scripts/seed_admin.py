#!/usr/bin/env python3
"""
Seed script to create initial admin user and default plans
Run this after running migrations
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import uuid

from app.core.config import settings
from app.models.admin import Admin, AdminRole
from app.models.plan import Plan
from app.core.security import get_password_hash


async def create_default_admin():
    """Create default super admin user"""
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if admin already exists
        from sqlalchemy import select
        result = await session.execute(
            select(Admin).where(Admin.email == "admin@bridgecore.local")
        )
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print("❌ Admin user already exists!")
            return

        # Create admin
        admin = Admin(
            id=uuid.uuid4(),
            email="admin@bridgecore.local",
            hashed_password=get_password_hash("admin123"),  # Change in production!
            full_name="Super Admin",
            role=AdminRole.SUPER_ADMIN,
            is_active=True
        )

        session.add(admin)
        await session.commit()
        print(f"✅ Created admin user:")
        print(f"   Email: admin@bridgecore.local")
        print(f"   Password: admin123")
        print(f"   ⚠️  IMPORTANT: Change this password in production!")


async def create_default_plans():
    """Create default subscription plans"""
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if plans already exist
        from sqlalchemy import select
        result = await session.execute(select(Plan))
        existing_plans = result.scalars().all()

        if existing_plans:
            print("❌ Plans already exist!")
            return

        # Define default plans
        plans = [
            {
                "name": "Free",
                "description": "Free tier for testing",
                "max_requests_per_day": 1000,
                "max_requests_per_hour": 100,
                "max_users": 2,
                "max_storage_gb": 1,
                "features": ["basic_odoo_access", "api_access"],
                "price_monthly": 0,
                "price_yearly": 0,
                "is_active": True
            },
            {
                "name": "Basic",
                "description": "Basic plan for small teams",
                "max_requests_per_day": 5000,
                "max_requests_per_hour": 500,
                "max_users": 5,
                "max_storage_gb": 5,
                "features": ["basic_odoo_access", "api_access", "email_support", "file_upload"],
                "price_monthly": 49.99,
                "price_yearly": 499.00,
                "is_active": True
            },
            {
                "name": "Pro",
                "description": "Professional plan for growing businesses",
                "max_requests_per_day": 20000,
                "max_requests_per_hour": 2000,
                "max_users": 20,
                "max_storage_gb": 20,
                "features": [
                    "basic_odoo_access",
                    "api_access",
                    "email_support",
                    "file_upload",
                    "batch_operations",
                    "webhooks",
                    "priority_support"
                ],
                "price_monthly": 149.99,
                "price_yearly": 1499.00,
                "is_active": True
            },
            {
                "name": "Enterprise",
                "description": "Enterprise plan with unlimited access",
                "max_requests_per_day": 100000,
                "max_requests_per_hour": 10000,
                "max_users": 100,
                "max_storage_gb": 100,
                "features": [
                    "basic_odoo_access",
                    "api_access",
                    "email_support",
                    "file_upload",
                    "batch_operations",
                    "webhooks",
                    "priority_support",
                    "custom_integrations",
                    "dedicated_support",
                    "sla"
                ],
                "price_monthly": 499.99,
                "price_yearly": 4999.00,
                "is_active": True
            }
        ]

        # Create plans
        for plan_data in plans:
            plan = Plan(
                id=uuid.uuid4(),
                **plan_data
            )
            session.add(plan)

        await session.commit()
        print("✅ Created 4 default plans:")
        for plan_data in plans:
            print(f"   - {plan_data['name']}: ${plan_data['price_monthly']}/month")


async def main():
    """Run all seed functions"""
    print("=" * 60)
    print("BridgeCore - Database Seeding")
    print("=" * 60)
    print()

    print("Creating default admin user...")
    await create_default_admin()
    print()

    print("Creating default subscription plans...")
    await create_default_plans()
    print()

    print("=" * 60)
    print("Seeding completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
