"""
Usage statistics model for aggregated data
"""
from sqlalchemy import Column, Date, Integer, BigInteger, ForeignKey, String, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base


class UsageStats(Base):
    """Aggregated statistics per tenant (hourly/daily)"""

    __tablename__ = "usage_stats"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    # Time Period
    date = Column(Date, nullable=False, index=True)
    hour = Column(Integer, nullable=True)  # NULL for daily stats, 0-23 for hourly

    # Request Metrics
    total_requests = Column(BigInteger, nullable=False, default=0)
    successful_requests = Column(BigInteger, nullable=False, default=0)
    failed_requests = Column(BigInteger, nullable=False, default=0)

    # Data Transfer
    total_data_transferred_bytes = Column(BigInteger, nullable=False, default=0)

    # Performance
    avg_response_time_ms = Column(Integer, nullable=True)

    # User Activity
    unique_users = Column(Integer, nullable=False, default=0)

    # Most Used
    most_used_model = Column(String(100), nullable=True)
    peak_hour = Column(Integer, nullable=True)  # For daily stats

    # Relationships
    tenant = relationship("Tenant", back_populates="usage_stats")

    # Composite indexes and constraints
    __table_args__ = (
        Index('ix_usage_stats_tenant_date', 'tenant_id', 'date'),
        Index('ix_usage_stats_tenant_date_hour', 'tenant_id', 'date', 'hour'),
        # Unique constraint to prevent duplicate stats
        Index('uq_usage_stats_tenant_date_hour', 'tenant_id', 'date', 'hour', unique=True),
        # Hour must be 0-23 or NULL
        CheckConstraint('hour IS NULL OR (hour >= 0 AND hour <= 23)', name='check_hour_range'),
    )

    def __repr__(self):
        period = f"{self.date} {self.hour}:00" if self.hour is not None else str(self.date)
        return f"<UsageStats(id={self.id}, tenant_id={self.tenant_id}, period='{period}', requests={self.total_requests})>"
