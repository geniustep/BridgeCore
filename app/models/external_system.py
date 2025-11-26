"""
External System models for multi-system architecture
Supports Odoo, Moodle, SAP, Salesforce, etc.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Enum, JSON, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from app.db.base import Base, TimestampMixin


class SystemType(str, enum.Enum):
    """Supported external system types"""
    ODOO = "odoo"
    MOODLE = "moodle"
    SAP = "sap"
    SALESFORCE = "salesforce"
    DYNAMICS = "dynamics"
    CUSTOM = "custom"


class SystemStatus(str, enum.Enum):
    """External system connection status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    TESTING = "testing"


class ExternalSystem(Base, TimestampMixin):
    """
    External system configuration (Odoo, Moodle, SAP, etc.)
    This is a catalog of available system types and their global settings
    """
    __tablename__ = "external_systems"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # System Info
    system_type = Column(Enum(SystemType), nullable=False, index=True)
    name = Column(String(255), nullable=False)  # e.g., "Moodle LMS", "Odoo ERP"
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=True)  # e.g., "4.1", "17.0"

    # Status
    status = Column(Enum(SystemStatus), default=SystemStatus.ACTIVE, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)

    # Global Configuration (optional defaults)
    default_config = Column(JSON, nullable=True, default=dict)

    # Capabilities (what this system supports)
    capabilities = Column(JSON, nullable=False, default=dict)
    # Example: {"crud": true, "search": true, "webhooks": false}

    # Relationships
    tenant_connections = relationship("TenantSystem", back_populates="external_system", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ExternalSystem(id={self.id}, type='{self.system_type}', name='{self.name}')>"


class TenantSystem(Base, TimestampMixin):
    """
    Many-to-Many relationship between Tenants and External Systems
    Each tenant can connect to multiple systems with their own credentials
    """
    __tablename__ = "tenant_systems"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Foreign Keys
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    system_id = Column(UUID(as_uuid=True), ForeignKey("external_systems.id", ondelete="CASCADE"), nullable=False, index=True)

    # Connection Details (encrypted)
    connection_config = Column(JSON, nullable=False)
    # Example for Odoo:
    # {
    #   "url": "https://example.odoo.com",
    #   "database": "production",
    #   "username": "api_user",
    #   "password": "encrypted_password"
    # }
    # Example for Moodle:
    # {
    #   "url": "https://lms.example.com",
    #   "token": "encrypted_token"
    # }

    # Status & Settings
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_primary = Column(Boolean, default=False, nullable=False)  # Primary system for this tenant

    # Connection Health
    last_connection_test = Column(DateTime, nullable=True)
    last_successful_connection = Column(DateTime, nullable=True)
    connection_error = Column(Text, nullable=True)

    # Custom Settings per tenant
    custom_config = Column(JSON, nullable=True, default=dict)
    # Example: {"sync_interval": 300, "allowed_models": ["course", "user"]}

    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("admins.id"), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="connected_systems")
    external_system = relationship("ExternalSystem", back_populates="tenant_connections")

    def __repr__(self):
        return f"<TenantSystem(id={self.id}, tenant_id={self.tenant_id}, system_id={self.system_id}, active={self.is_active})>"
