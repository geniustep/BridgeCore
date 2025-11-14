"""
System model for external system connections
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin


class System(Base, TimestampMixin):
    """External system configuration (Odoo, SAP, Salesforce, etc.)"""

    __tablename__ = "systems"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    system_id = Column(String(50), unique=True, index=True, nullable=False)  # e.g., "odoo-prod"
    system_type = Column(String(50), nullable=False)  # e.g., "odoo", "sap", "salesforce"
    system_version = Column(String(20))  # e.g., "16.0", "18.0"
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)

    # Connection details (encrypted)
    connection_config = Column(JSON, nullable=False)  # Store encrypted credentials

    # Relationships
    user = relationship("User", back_populates="systems")
    field_mappings = relationship("FieldMapping", back_populates="system", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="system", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<System(id={self.id}, system_id='{self.system_id}', type='{self.system_type}')>"
