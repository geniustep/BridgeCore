"""
Odoo Operations Services Module

This module provides a comprehensive set of services for interacting with Odoo ERP
through JSON-RPC API. It supports all 26 Odoo API operations.

Services:
    - OdooOperationsService: Base class for all Odoo operations
    - SearchOperations: search, search_read, search_count
    - CRUDOperations: create, read, write, unlink, copy
    - AdvancedOperations: onchange, read_group, default_get
    - NameOperations: name_search, name_get, name_create
    - ViewOperations: fields_get, fields_view_get, load_views, get_views
    - WebOperations: web_save, web_read, web_search_read
    - PermissionOperations: check_access_rights
    - UtilityOperations: exists, copy
    - CustomOperations: call_method, action_*, button_*
"""

from .base import OdooOperationsService
from .search_ops import SearchOperations
from .crud_ops import CRUDOperations
from .advanced_ops import AdvancedOperations
from .name_ops import NameOperations
from .view_ops import ViewOperations
from .web_ops import WebOperations
from .permission_ops import PermissionOperations
from .utility_ops import UtilityOperations
from .custom_ops import CustomOperations

__all__ = [
    "OdooOperationsService",
    "SearchOperations",
    "CRUDOperations",
    "AdvancedOperations",
    "NameOperations",
    "ViewOperations",
    "WebOperations",
    "PermissionOperations",
    "UtilityOperations",
    "CustomOperations",
]
