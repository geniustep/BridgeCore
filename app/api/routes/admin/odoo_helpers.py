"""
Odoo Helper Endpoints for Admin Panel
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from uuid import UUID
from loguru import logger

from app.db.session import get_db
from app.api.routes.admin.dependencies import get_current_admin
from app.models.admin import Admin
from app.repositories.tenant_repository import TenantRepository
from app.adapters.odoo_adapter import OdooAdapter
from app.core.encryption import encryption_service

router = APIRouter(prefix="/admin/odoo-helpers", tags=["Admin Odoo Helpers"])


@router.get("/companies/{tenant_id}")
async def get_odoo_companies(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Get list of companies from Odoo for a specific tenant
    
    Args:
        tenant_id: Tenant UUID
        
    Returns:
        List of companies with id and name
    """
    tenant_repo = TenantRepository(db)
    tenant = await tenant_repo.get_by_id_uuid(tenant_id)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    try:
        # Decrypt password
        try:
            decrypted_password = encryption_service.decrypt_value(tenant.odoo_password)
        except Exception:
            decrypted_password = tenant.odoo_password
        
        # Create adapter
        adapter = OdooAdapter({
            "url": tenant.odoo_url,
            "database": tenant.odoo_database,
            "username": tenant.odoo_username,
            "password": decrypted_password,
            "system_version": tenant.odoo_version
        })
        
        # Authenticate
        auth_result = await adapter.authenticate(tenant.odoo_username, decrypted_password)
        
        if not auth_result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to authenticate with Odoo"
            )
        
        # Get companies
        companies = await adapter.search_read(
            model="res.company",
            domain=[],
            fields=["name"],
            limit=100
        )
        
        await adapter.disconnect()
        
        return {
            "success": True,
            "companies": [
                {
                    "id": company["id"],
                    "name": company["name"]
                }
                for company in companies
            ]
        }
        
    except Exception as e:
        logger.error(f"Error fetching companies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching companies: {str(e)}"
        )


@router.get("/users/{tenant_id}")
async def get_odoo_users(
    tenant_id: UUID,
    company_id: int = Query(..., description="Odoo company ID"),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Get list of users from Odoo for a specific tenant and company
    
    Args:
        tenant_id: Tenant UUID
        company_id: Odoo company ID
        
    Returns:
        List of users with id, name, login, email
    """
    tenant_repo = TenantRepository(db)
    tenant = await tenant_repo.get_by_id_uuid(tenant_id)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    try:
        # Decrypt password
        try:
            decrypted_password = encryption_service.decrypt_value(tenant.odoo_password)
        except Exception:
            decrypted_password = tenant.odoo_password
        
        # Create adapter
        adapter = OdooAdapter({
            "url": tenant.odoo_url,
            "database": tenant.odoo_database,
            "username": tenant.odoo_username,
            "password": decrypted_password,
            "system_version": tenant.odoo_version
        })
        
        # Authenticate
        auth_result = await adapter.authenticate(tenant.odoo_username, decrypted_password)
        
        if not auth_result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to authenticate with Odoo"
            )
        
        # Get users for the company
        users = await adapter.search_read(
            model="res.users",
            domain=[["company_id", "=", company_id], ["active", "=", True]],
            fields=["name", "login", "email", "company_id"],
            limit=500
        )
        
        await adapter.disconnect()
        
        return {
            "success": True,
            "users": [
                {
                    "id": user["id"],
                    "name": user["name"],
                    "login": user.get("login", ""),
                    "email": user.get("email", ""),
                    "company_id": user.get("company_id", [None, ""])[0] if isinstance(user.get("company_id"), list) else user.get("company_id")
                }
                for user in users
            ]
        }
        
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching users: {str(e)}"
        )

