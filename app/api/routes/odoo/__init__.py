"""
Odoo API Routes Module

This module provides FastAPI routes for all 26 Odoo operations.

Routes are organized into logical groups:
- /api/v1/odoo/search - Search operations
- /api/v1/odoo/crud - CRUD operations
- /api/v1/odoo/advanced - Advanced operations (onchange, read_group, etc.)
- /api/v1/odoo/names - Name operations
- /api/v1/odoo/views - View and field metadata operations
- /api/v1/odoo/web - Web-optimized operations
- /api/v1/odoo/permissions - Permission operations
- /api/v1/odoo/utility - Utility operations
- /api/v1/odoo/methods - Custom method operations
"""

from fastapi import APIRouter

from .search import router as search_router
from .crud import router as crud_router
from .advanced import router as advanced_router
from .names import router as names_router
from .views import router as views_router
from .web import router as web_router
from .permissions import router as permissions_router
from .utility import router as utility_router
from .methods import router as methods_router

# Main router for all Odoo operations
router = APIRouter(prefix="/odoo", tags=["Odoo Operations"])

# Include all sub-routers
router.include_router(search_router, tags=["Search Operations"])
router.include_router(crud_router, tags=["CRUD Operations"])
router.include_router(advanced_router, tags=["Advanced Operations"])
router.include_router(names_router, tags=["Name Operations"])
router.include_router(views_router, tags=["View Operations"])
router.include_router(web_router, tags=["Web Operations"])
router.include_router(permissions_router, tags=["Permission Operations"])
router.include_router(utility_router, tags=["Utility Operations"])
router.include_router(methods_router, tags=["Custom Methods"])

__all__ = ["router"]
