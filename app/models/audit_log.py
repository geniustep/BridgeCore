"""
Audit Log model for tracking all operations
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class AuditLog(Base):
    """Audit trail for all system operations"""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    system_id = Column(Integer, ForeignKey("systems.id"), index=True)

    # Operation details
    action = Column(String(50), nullable=False, index=True)  # create, read, update, delete
    model = Column(String(100), index=True)  # e.g., "res.partner"
    record_id = Column(String(50))  # ID of the record in external system

    # Request/Response data
    request_data = Column(JSON)
    response_data = Column(JSON)

    # Status
    status = Column(String(20), nullable=False, index=True)  # success, error
    error_message = Column(Text)

    # Metadata
    ip_address = Column(String(45))
    user_agent = Column(Text)
    duration_ms = Column(Integer)  # Request duration in milliseconds
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")
    system = relationship("System", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', status='{self.status}')>"
