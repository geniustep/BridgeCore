"""
Models package - exports all database models
"""
from app.models.user import User
from app.models.system import System
from app.models.audit_log import AuditLog
from app.models.field_mapping import FieldMapping

# Admin Panel Models
from app.models.admin import Admin, AdminRole
from app.models.plan import Plan
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_user import TenantUser, TenantUserRole
from app.models.usage_log import UsageLog
from app.models.error_log import ErrorLog, ErrorSeverity
from app.models.usage_stats import UsageStats
from app.models.admin_audit_log import AdminAuditLog

# Multi-System Support (NEW)
from app.models.external_system import ExternalSystem, TenantSystem, SystemType, SystemStatus

__all__ = [
    # Original models
    "User",
    "System",
    "AuditLog",
    "FieldMapping",
    # Admin panel models
    "Admin",
    "AdminRole",
    "Plan",
    "Tenant",
    "TenantStatus",
    "TenantUser",
    "TenantUserRole",
    "UsageLog",
    "ErrorLog",
    "ErrorSeverity",
    "UsageStats",
    "AdminAuditLog",
    # Multi-System Support
    "ExternalSystem",
    "TenantSystem",
    "SystemType",
    "SystemStatus",
]
