"""
Admin audit log model for tracking admin actions
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.db.base import Base


class AdminAuditLog(Base):
    """Audit trail for admin actions"""

    __tablename__ = "admin_audit_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    admin_id = Column(UUID(as_uuid=True), ForeignKey("admins.id"), nullable=False, index=True)

    # Action Info
    action = Column(String(100), nullable=False, index=True)  # create_tenant, suspend_tenant, etc
    target_tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)
    details = Column(JSON, nullable=True)  # Additional action details

    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Relationships
    admin = relationship("Admin", back_populates="audit_logs")
    target_tenant = relationship("Tenant", back_populates="audit_logs")

    # Composite indexes
    __table_args__ = (
        Index('ix_admin_audit_logs_admin_timestamp', 'admin_id', 'timestamp'),
        Index('ix_admin_audit_logs_tenant_timestamp', 'target_tenant_id', 'timestamp'),
        Index('ix_admin_audit_logs_action', 'action', 'timestamp'),
    )

    def __repr__(self):
        return f"<AdminAuditLog(id={self.id}, admin_id={self.admin_id}, action='{self.action}', timestamp={self.timestamp})>"
