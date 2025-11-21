"""
Subscription plan model
"""
from sqlalchemy import Column, String, Integer, Boolean, DECIMAL, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base, TimestampMixin


class Plan(Base, TimestampMixin):
    """Subscription plans for tenants"""

    __tablename__ = "plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), unique=True, nullable=False)  # Free, Basic, Pro, Enterprise
    description = Column(String(500))

    # Limits
    max_requests_per_day = Column(Integer, nullable=False, default=1000)
    max_requests_per_hour = Column(Integer, nullable=False, default=100)
    max_users = Column(Integer, nullable=False, default=5)
    max_storage_gb = Column(Integer, nullable=False, default=1)

    # Features (JSON array of feature names)
    features = Column(JSON, nullable=False, default=list)

    # Pricing
    price_monthly = Column(DECIMAL(10, 2), nullable=False, default=0)
    price_yearly = Column(DECIMAL(10, 2), nullable=False, default=0)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    tenants = relationship("Tenant", back_populates="plan")

    def __repr__(self):
        return f"<Plan(id={self.id}, name='{self.name}', price_monthly={self.price_monthly})>"
