"""
Tenant (company) model for multi-tenancy
"""
from sqlalchemy import Column, String, Boolean, DateTime, Enum, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from app.db.base import Base, TimestampMixin


class TenantStatus(str, enum.Enum):
    """Tenant status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    DELETED = "deleted"


class Tenant(Base, TimestampMixin):
    """Companies/clients using BridgeCore"""

    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Basic Info
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(String(1000))
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50))

    # Odoo Connection
    odoo_url = Column(String(500), nullable=False)
    odoo_database = Column(String(255), nullable=False)
    odoo_version = Column(String(50))
    odoo_username = Column(String(255), nullable=False)
    odoo_password = Column(String(500), nullable=False)  # Should be encrypted

    # Status & Subscription
    status = Column(Enum(TenantStatus), default=TenantStatus.TRIAL, nullable=False, index=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    trial_ends_at = Column(DateTime, nullable=True)
    subscription_ends_at = Column(DateTime, nullable=True)

    # Rate Limits (override plan defaults if set)
    max_requests_per_day = Column(Integer, nullable=True)
    max_requests_per_hour = Column(Integer, nullable=True)
    max_users = Column(Integer, nullable=False, default=5)  # Maximum number of users allowed

    # Allowed Features
    allowed_models = Column(JSON, nullable=False, default=list)  # Empty = all models
    allowed_features = Column(JSON, nullable=False, default=list)  # Empty = all features

    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("admins.id"), nullable=True)
    last_active_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    plan = relationship("Plan", back_populates="tenants")
    users = relationship("TenantUser", back_populates="tenant", cascade="all, delete-orphan")
    usage_logs = relationship("UsageLog", back_populates="tenant", cascade="all, delete-orphan")
    error_logs = relationship("ErrorLog", back_populates="tenant", cascade="all, delete-orphan")
    usage_stats = relationship("UsageStats", back_populates="tenant", cascade="all, delete-orphan")
    audit_logs = relationship("AdminAuditLog", back_populates="target_tenant")

    def __repr__(self):
        return f"<Tenant(id={self.id}, name='{self.name}', slug='{self.slug}', status='{self.status}')>"
