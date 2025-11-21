"""
Tenant user model - users within each tenant
"""
from sqlalchemy import Column, String, Boolean, DateTime, Enum, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from app.db.base import Base, TimestampMixin


class TenantUserRole(str, enum.Enum):
    """Tenant user roles"""
    ADMIN = "admin"
    USER = "user"


class TenantUser(Base, TimestampMixin):
    """Users within each tenant (company)"""

    __tablename__ = "tenant_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # User Info
    email = Column(String(255), nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(TenantUserRole), default=TenantUserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Odoo Integration
    odoo_user_id = Column(Integer, nullable=True)

    # Metadata
    last_login = Column(DateTime, nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    usage_logs = relationship("UsageLog", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TenantUser(id={self.id}, email='{self.email}', tenant_id={self.tenant_id})>"
