"""
Universal Audit Module - Auto-discovery and monitoring for all Odoo models

This module provides:
- Automatic discovery of all Odoo models
- Model classification by importance
- Multiple detection strategies
- Real-time change monitoring
"""

from app.modules.universal_audit.detector import UniversalAuditDetector
from app.modules.universal_audit.auto_discovery import ModelDiscovery
from app.modules.universal_audit.classifier import ModelClassifier

__all__ = [
    "UniversalAuditDetector",
    "ModelDiscovery",
    "ModelClassifier"
]
