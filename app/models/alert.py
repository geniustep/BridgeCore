"""
Alert model for system notifications and monitoring alerts
"""
from sqlalchemy import Column, String, DateTime, Boolean, Enum, Text, ForeignKey, Index, BigInteger, Integer
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime
from app.db.base import Base


class AlertType(str, enum.Enum):
    """Alert types"""
    RATE_LIMIT_WARNING = "rate_limit_warning"      # 80% of limit reached
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"    # Limit exceeded
    HIGH_ERROR_RATE = "high_error_rate"            # Error rate > threshold
    SLOW_RESPONSE = "slow_response"                # Response time > threshold
    SUSPICIOUS_IP = "suspicious_ip"                # Suspicious activity from IP
    TENANT_SUSPENDED = "tenant_suspended"          # Tenant was suspended
    CONNECTION_FAILED = "connection_failed"        # Odoo connection failed
    SECURITY_THREAT = "security_threat"            # Security issue detected


class AlertSeverity(str, enum.Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    """Alert status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class Alert(Base):
    """System alerts for monitoring and notifications"""

    __tablename__ = "alerts"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)
    
    # Alert details
    alert_type = Column(Enum(AlertType), nullable=False, index=True)
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.WARNING, nullable=False, index=True)
    status = Column(Enum(AlertStatus), default=AlertStatus.ACTIVE, nullable=False, index=True)
    
    # Content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)  # Additional context data
    
    # Thresholds that triggered the alert
    threshold_value = Column(Integer, nullable=True)  # The limit/threshold
    current_value = Column(Integer, nullable=True)    # The actual value
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey("admins.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("admins.id"), nullable=True)
    
    # Auto-dismiss settings
    auto_resolve = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", backref="alerts")

    # Indexes
    __table_args__ = (
        Index('ix_alerts_tenant_type', 'tenant_id', 'alert_type'),
        Index('ix_alerts_status_severity', 'status', 'severity'),
        Index('ix_alerts_active', 'status', 'created_at'),
    )

    def __repr__(self):
        return f"<Alert(id={self.id}, type='{self.alert_type}', severity='{self.severity}', status='{self.status}')>"

