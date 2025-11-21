"""
Admin user model for platform management
"""
from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from app.db.base import Base, TimestampMixin


class AdminRole(str, enum.Enum):
    """Admin roles"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    SUPPORT = "support"


class Admin(Base, TimestampMixin):
    """Admin users who manage the BridgeCore platform"""

    __tablename__ = "admins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(AdminRole), default=AdminRole.ADMIN, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    audit_logs = relationship("AdminAuditLog", back_populates="admin", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Admin(id={self.id}, email='{self.email}', role='{self.role}')>"
