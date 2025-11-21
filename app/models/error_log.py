"""
Error log model for tracking errors
"""
from sqlalchemy import Column, String, DateTime, Boolean, Enum, Text, ForeignKey, Index, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime
from app.db.base import Base


class ErrorSeverity(str, enum.Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorLog(Base):
    """Track errors per tenant"""

    __tablename__ = "error_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Error Info
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    error_type = Column(String(255), nullable=False, index=True)
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)

    # Request Context
    endpoint = Column(String(500), nullable=True)
    method = Column(String(10), nullable=True)
    request_data = Column(JSON, nullable=True)

    # Severity & Resolution
    severity = Column(Enum(ErrorSeverity), default=ErrorSeverity.MEDIUM, nullable=False, index=True)
    is_resolved = Column(Boolean, default=False, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("admins.id"), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="error_logs")

    # Composite indexes
    __table_args__ = (
        Index('ix_error_logs_tenant_timestamp', 'tenant_id', 'timestamp'),
        Index('ix_error_logs_tenant_severity', 'tenant_id', 'severity'),
        Index('ix_error_logs_unresolved', 'tenant_id', 'is_resolved'),
    )

    def __repr__(self):
        return f"<ErrorLog(id={self.id}, tenant_id={self.tenant_id}, error_type='{self.error_type}', severity='{self.severity}')>"
