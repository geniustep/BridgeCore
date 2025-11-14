"""
Field Mapping model for schema transformations
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin


class FieldMapping(Base, TimestampMixin):
    """Field mapping configuration for data transformation"""

    __tablename__ = "field_mappings"

    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(Integer, ForeignKey("systems.id"), nullable=False)

    # Mapping details
    model = Column(String(100), nullable=False, index=True)  # e.g., "res.partner"
    system_version = Column(String(20))  # Target system version

    # Mapping configuration
    mapping_config = Column(JSON, nullable=False)
    """
    Example structure:
    {
        "universal_to_system": {
            "name": "name",
            "phone": "phone",
            "city": "city_id.name"
        },
        "system_to_universal": {
            "name": "name",
            "phone": "phone",
            "city_id.name": "city"
        },
        "transformations": {
            "phone": {"type": "phone_format", "format": "international"}
        }
    }
    """

    # Version migration rules
    version_migration_rules = Column(JSON)
    """
    Example:
    {
        "13.0_to_16.0": {
            "customer": "is_company",
            "phone": {"split_to": ["phone_primary", "phone_secondary"]}
        }
    }
    """

    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(Text)

    # Relationships
    system = relationship("System", back_populates="field_mappings")

    def __repr__(self):
        return f"<FieldMapping(id={self.id}, model='{self.model}', version='{self.system_version}')>"
