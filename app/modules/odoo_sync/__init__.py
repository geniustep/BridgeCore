# -*- coding: utf-8 -*-
"""
Odoo Sync Module

This module provides direct integration with auto-webhook-odoo for pulling
events from Odoo's update.webhook table and managing user sync states.
"""

from app.modules.odoo_sync.service import OdooSyncService
from app.modules.odoo_sync.router import router

__all__ = ["OdooSyncService", "router"]

