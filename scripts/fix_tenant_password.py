#!/usr/bin/env python3
"""
Fix tenant password - decrypt hash or update to plain text
Run this to fix passwords that were stored as hash instead of encrypted/plain text
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import uuid

from app.core.config import settings
from app.models.tenant import Tenant
from app.core.encryption import encryption_service

async def fix_tenant_password():
    """Fix tenant password - update to encrypted plain text"""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Get tenant
        result = await session.execute(
            select(Tenant).where(Tenant.slug == "enterprise" or Tenant.name.ilike("%enterprise%"))
        )
        tenants = result.scalars().all()
        
        if not tenants:
            print("❌ No tenant found")
            return
        
        for tenant in tenants:
            print(f"\n📋 Tenant: {tenant.name} ({tenant.slug})")
            print(f"   Current password (first 50 chars): {tenant.odoo_password[:50]}...")
            
            # Check if password is a hash (starts with $2b$)
            if tenant.odoo_password.startswith("$2b$"):
                print("   ⚠️  Password is stored as hash (bcrypt)")
                print("   💡 You need to update the password manually in the Admin Dashboard")
                print("   💡 Or provide the original password here to encrypt it")
                
                # For now, we'll need to update it manually
                # The user should update the password in the Admin Dashboard
                print(f"   ✅ Please update the password in Admin Dashboard to: ,,07Genius")
            else:
                # Try to decrypt (might be encrypted)
                try:
                    decrypted = encryption_service.decrypt_value(tenant.odoo_password)
                    print(f"   ✅ Password is encrypted, decrypted value: {decrypted[:10]}...")
                except:
                    print(f"   ✅ Password appears to be plain text or already encrypted")
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_tenant_password())

