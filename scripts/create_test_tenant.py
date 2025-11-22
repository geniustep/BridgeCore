#!/usr/bin/env python3
"""Create test tenant and user for testing"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import uuid
from datetime import datetime, timedelta

from app.core.config import settings
from app.models.admin import Admin, AdminRole
from app.models.plan import Plan
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_user import TenantUser, TenantUserRole
from app.core.security import get_password_hash


async def create_test_data():
    """Create test tenant and user"""
    # Use the docker database URL
    db_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/middleware_db"
    
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("🔍 Checking existing data...")
        
        # Check if admin exists
        result = await session.execute(
            select(Admin).where(Admin.email == "admin@bridgecore.com")
        )
        admin = result.scalar_one_or_none()
        
        if not admin:
            print("❌ Admin not found. Creating admin first...")
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
            await session.refresh(admin)
            print("✅ Created admin: admin@bridgecore.com")
        else:
            print(f"✅ Admin exists: {admin.email}")
        
        # Check if plan exists
        result = await session.execute(
            select(Plan).where(Plan.slug == "free")
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            print("❌ Free plan not found. Creating plan...")
            plan = Plan(
                id=uuid.uuid4(),
                name="Free Plan",
                slug="free",
                description="Free tier for testing",
                price=0.0,
                billing_period="monthly",
                max_requests_per_day=1000,
                max_requests_per_hour=100,
                max_users=5,
                allowed_features=["odoo", "webhooks"],
                is_active=True
            )
            session.add(plan)
            await session.commit()
            await session.refresh(plan)
            print("✅ Created free plan")
        else:
            print(f"✅ Plan exists: {plan.name}")
        
        # Check if tenant exists
        result = await session.execute(
            select(Tenant).where(Tenant.slug == "done-company")
        )
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            print("❌ Tenant not found. Creating tenant...")
            tenant = Tenant(
                id=uuid.uuid4(),
                name="Done Company",
                slug="done-company",
                description="Test company for development",
                contact_email="contact@done.com",
                contact_phone="+212600000000",
                odoo_url="https://odoo.geniura.com",
                odoo_database="done",
                odoo_version="16.0",
                odoo_username="admin",
                odoo_password="admin",  # Should be encrypted in production
                status=TenantStatus.ACTIVE,
                plan_id=plan.id,
                created_by=admin.id,
                trial_ends_at=datetime.utcnow() + timedelta(days=30),
                allowed_models=[],  # Empty = all models allowed
                allowed_features=[]  # Empty = all features allowed
            )
            session.add(tenant)
            await session.commit()
            await session.refresh(tenant)
            print(f"✅ Created tenant: {tenant.name} (slug: {tenant.slug})")
        else:
            print(f"✅ Tenant exists: {tenant.name}")
        
        # Check if user exists
        result = await session.execute(
            select(TenantUser).where(TenantUser.email == "user@done.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ User not found. Creating user...")
            user = TenantUser(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                email="user@done.com",
                hashed_password=get_password_hash("done123"),
                full_name="Test User",
                role=TenantUserRole.ADMIN,
                is_active=True,
                odoo_user_id=2  # Typically admin user in Odoo
            )
            session.add(user)
            await session.commit()
            print(f"✅ Created user: {user.email}")
        else:
            # Update password to be sure
            user.hashed_password = get_password_hash("done123")
            await session.commit()
            print(f"✅ User exists: {user.email} (password updated)")
        
        print("\n" + "="*60)
        print("✅ TEST DATA READY!")
        print("="*60)
        print(f"\n📋 Login Credentials:")
        print(f"   Email:    user@done.com")
        print(f"   Password: done123")
        print(f"\n🏢 Tenant Info:")
        print(f"   Name:     {tenant.name}")
        print(f"   Slug:     {tenant.slug}")
        print(f"   Status:   {tenant.status.value}")
        print(f"\n🔗 Test Command:")
        print(f'   curl -X POST "https://bridgecore.geniura.com/api/v1/auth/tenant/login" \\')
        print(f'     -H "Content-Type: application/json" \\')
        print(f'     -d \'{{"email": "user@done.com", "password": "done123"}}\'')
        print()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_test_data())

