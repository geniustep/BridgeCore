"""
IP Block model for blocking suspicious or malicious IPs
"""
from sqlalchemy import Column, String, DateTime, Boolean, Enum, Text, ForeignKey, Index, BigInteger, Integer
from sqlalchemy.dialects.postgresql import UUID, JSON, INET
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime
from app.db.base import Base


class BlockReason(str, enum.Enum):
    """Reasons for blocking an IP"""
    RATE_LIMIT_ABUSE = "rate_limit_abuse"          # Too many rate limit violations
    BRUTE_FORCE = "brute_force"                    # Failed login attempts
    SUSPICIOUS_ACTIVITY = "suspicious_activity"    # Unusual request patterns
    SECURITY_THREAT = "security_threat"            # Security scanning/attacks
    MANUAL_BLOCK = "manual_block"                  # Manually blocked by admin
    SPAM = "spam"                                  # Spam/abuse detected


class IPBlock(Base):
    """Blocked IP addresses"""

    __tablename__ = "ip_blocks"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    
    # IP Information
    ip_address = Column(String(45), nullable=False, index=True)  # IPv6 compatible
    ip_range = Column(String(50), nullable=True)  # CIDR notation for range blocks
    
    # Block details
    reason = Column(Enum(BlockReason), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Associated tenant (if applicable)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)
    
    # Block settings
    is_permanent = Column(Boolean, default=False)
    blocked_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)  # Null = permanent
    
    # Auto-block tracking
    violation_count = Column(Integer, default=1)
    last_violation_at = Column(DateTime, default=datetime.utcnow)
    
    # Admin who created the block
    blocked_by = Column(UUID(as_uuid=True), ForeignKey("admins.id"), nullable=True)
    
    # Unblock info
    is_active = Column(Boolean, default=True, index=True)
    unblocked_at = Column(DateTime, nullable=True)
    unblocked_by = Column(UUID(as_uuid=True), ForeignKey("admins.id"), nullable=True)
    unblock_reason = Column(Text, nullable=True)
    
    # Additional context
    user_agent = Column(String(500), nullable=True)
    request_details = Column(JSON, nullable=True)  # Last request that triggered block
    
    # Relationships
    tenant = relationship("Tenant", backref="blocked_ips")

    # Indexes
    __table_args__ = (
        Index('ix_ip_blocks_active_ip', 'is_active', 'ip_address'),
        Index('ix_ip_blocks_expires', 'is_active', 'expires_at'),
    )

    def __repr__(self):
        return f"<IPBlock(id={self.id}, ip='{self.ip_address}', reason='{self.reason}', active={self.is_active})>"

    @property
    def is_expired(self) -> bool:
        """Check if the block has expired"""
        if self.is_permanent or self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

