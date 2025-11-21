"""
Usage log model for tracking API requests
"""
from sqlalchemy import Column, String, Integer, DateTime, BigInteger, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.db.base import Base


class UsageLog(Base):
    """Track all API requests per tenant"""

    __tablename__ = "usage_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("tenant_users.id"), nullable=True, index=True)

    # Request Info
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    endpoint = Column(String(500), nullable=False)
    method = Column(String(10), nullable=False)  # GET, POST, PUT, DELETE
    model_name = Column(String(100), nullable=True, index=True)

    # Performance Metrics
    request_size_bytes = Column(BigInteger, nullable=True)
    response_size_bytes = Column(BigInteger, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    status_code = Column(Integer, nullable=False, index=True)

    # Client Info
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="usage_logs")
    user = relationship("TenantUser", back_populates="usage_logs")

    # Composite indexes for common queries
    __table_args__ = (
        Index('ix_usage_logs_tenant_timestamp', 'tenant_id', 'timestamp'),
        Index('ix_usage_logs_tenant_status', 'tenant_id', 'status_code'),
        Index('ix_usage_logs_tenant_model', 'tenant_id', 'model_name'),
    )

    def __repr__(self):
        return f"<UsageLog(id={self.id}, tenant_id={self.tenant_id}, endpoint='{self.endpoint}', status={self.status_code})>"
