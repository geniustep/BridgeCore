"""
Dependencies for Odoo routes

Provides FastAPI dependencies for authentication and service injection.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Header, Request
from loguru import logger

from app.core.encryption import encryption_service
from app.services.odoo import (
    OdooOperationsService,
    SearchOperations,
    CRUDOperations,
    AdvancedOperations,
    NameOperations,
    ViewOperations,
    WebOperations,
    PermissionOperations,
    UtilityOperations,
    CustomOperations,
)


class OdooServiceFactory:
    """Factory for creating Odoo service instances"""

    @staticmethod
    def create_service(
        service_class,
        odoo_url: str,
        database: str,
        username: str,
        password: str,
        context: Optional[dict] = None
    ):
        """Create an Odoo service instance"""
        return service_class(
            odoo_url=odoo_url,
            database=database,
            username=username,
            password=password,
            context=context or {}
        )


async def get_odoo_credentials(
    request: Request,
    x_odoo_url: Optional[str] = Header(None, alias="X-Odoo-Url"),
    x_odoo_db: Optional[str] = Header(None, alias="X-Odoo-DB"),
    x_odoo_user: Optional[str] = Header(None, alias="X-Odoo-User"),
    x_odoo_password: Optional[str] = Header(None, alias="X-Odoo-Password"),
) -> dict:
    """
    Extract Odoo credentials from request headers or tenant context

    Priority:
    1. Tenant context from JWT token (set by TenantContextMiddleware)
    2. Headers (X-Odoo-Url, X-Odoo-DB, X-Odoo-User, X-Odoo-Password)

    Headers:
        X-Odoo-Url: Odoo instance URL
        X-Odoo-DB: Database name
        X-Odoo-User: Username
        X-Odoo-Password: Password or API key

    Returns credentials dict or raises HTTPException
    """
    # Check if we have tenant context from middleware
    tenant = getattr(request.state, 'tenant', None)
    
    # Enhanced debug logging
    logger.info(f"[ODOO_DEPS] Checking tenant context: tenant={tenant is not None}")
    logger.info(f"[ODOO_DEPS] Request path: {request.url.path}")
    logger.info(f"[ODOO_DEPS] Authorization header present: {request.headers.get('authorization') is not None}")
    
    if hasattr(request.state, 'tenant_id'):
        logger.info(f"[ODOO_DEPS] tenant_id in state: {request.state.tenant_id}")
    else:
        logger.warning(f"[ODOO_DEPS] No tenant_id in request.state - middleware may not have run")

    if tenant:
        # Decrypt Odoo password
        try:
            decrypted_password = encryption_service.decrypt_value(tenant.odoo_password)
        except Exception as e:
            logger.warning(f"Password decryption failed: {str(e)}")
            decrypted_password = tenant.odoo_password

        # Use tenant's Odoo configuration
        return {
            "odoo_url": tenant.odoo_url,
            "database": tenant.odoo_database,
            "username": tenant.odoo_username,
            "password": decrypted_password,
        }

    # Fall back to headers
    logger.debug(f"[ODOO_DEPS] No tenant context, checking headers")
    if not all([x_odoo_url, x_odoo_db, x_odoo_user, x_odoo_password]):
        logger.warning(
            f"[ODOO_DEPS] Missing Odoo credentials. "
            f"Tenant context: {tenant is not None}, "
            f"Headers provided: url={x_odoo_url is not None}, db={x_odoo_db is not None}, "
            f"user={x_odoo_user is not None}, password={x_odoo_password is not None}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Odoo credentials. Either use a tenant JWT token or provide headers: X-Odoo-Url, X-Odoo-DB, X-Odoo-User, X-Odoo-Password"
        )

    return {
        "odoo_url": x_odoo_url,
        "database": x_odoo_db,
        "username": x_odoo_user,
        "password": x_odoo_password,
    }


async def get_search_service(
    credentials: dict = Depends(get_odoo_credentials)
) -> SearchOperations:
    """Get SearchOperations service instance"""
    return SearchOperations(**credentials)


async def get_crud_service(
    credentials: dict = Depends(get_odoo_credentials)
) -> CRUDOperations:
    """Get CRUDOperations service instance"""
    return CRUDOperations(**credentials)


async def get_advanced_service(
    credentials: dict = Depends(get_odoo_credentials)
) -> AdvancedOperations:
    """Get AdvancedOperations service instance"""
    return AdvancedOperations(**credentials)


async def get_name_service(
    credentials: dict = Depends(get_odoo_credentials)
) -> NameOperations:
    """Get NameOperations service instance"""
    return NameOperations(**credentials)


async def get_view_service(
    credentials: dict = Depends(get_odoo_credentials)
) -> ViewOperations:
    """Get ViewOperations service instance"""
    return ViewOperations(**credentials)


async def get_web_service(
    credentials: dict = Depends(get_odoo_credentials)
) -> WebOperations:
    """Get WebOperations service instance"""
    return WebOperations(**credentials)


async def get_permission_service(
    credentials: dict = Depends(get_odoo_credentials)
) -> PermissionOperations:
    """Get PermissionOperations service instance"""
    return PermissionOperations(**credentials)


async def get_utility_service(
    credentials: dict = Depends(get_odoo_credentials)
) -> UtilityOperations:
    """Get UtilityOperations service instance"""
    return UtilityOperations(**credentials)


async def get_custom_service(
    credentials: dict = Depends(get_odoo_credentials)
) -> CustomOperations:
    """Get CustomOperations service instance"""
    return CustomOperations(**credentials)
