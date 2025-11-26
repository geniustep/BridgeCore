"""
Adapters package for external systems
"""
from app.adapters.base_adapter import BaseAdapter
from app.adapters.odoo_adapter import OdooAdapter
from app.adapters.moodle_adapter import MoodleAdapter

__all__ = [
    "BaseAdapter",
    "OdooAdapter",
    "MoodleAdapter",
]
