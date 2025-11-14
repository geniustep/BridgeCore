"""
Field Mapping Service tests
"""
import pytest
from app.services.field_mapping_service import FieldMappingService


@pytest.mark.asyncio
async def test_field_mapping_initialization():
    """Test field mapping service initialization"""
    service = FieldMappingService()

    assert "odoo_16" in service.mappings
    assert "res.partner" in service.mappings["odoo_16"]


@pytest.mark.asyncio
async def test_transform_to_universal():
    """Test transformation from system-specific to universal schema"""
    service = FieldMappingService()

    odoo_data = {
        "id": 1,
        "name": "Ahmed Ali",
        "email": "ahmed@example.com",
        "phone": "+966501234567",
        "mobile": "+966509876543"
    }

    universal_data = await service.transform_to_universal(
        data=odoo_data,
        system_type="odoo",
        system_version="16.0",
        model="res.partner"
    )

    assert universal_data["name"] == "Ahmed Ali"
    assert universal_data["email"] == "ahmed@example.com"
    assert universal_data["phone"] == "+966501234567"


@pytest.mark.asyncio
async def test_transform_to_system():
    """Test transformation from universal to system-specific schema"""
    service = FieldMappingService()

    universal_data = {
        "name": "Ahmed Ali",
        "email": "ahmed@example.com",
        "phone": "+966501234567"
    }

    odoo_data = await service.transform_to_system(
        data=universal_data,
        system_type="odoo",
        system_version="16.0",
        model="res.partner"
    )

    assert odoo_data["name"] == "Ahmed Ali"
    assert odoo_data["email"] == "ahmed@example.com"
    assert odoo_data["phone"] == "+966501234567"


@pytest.mark.asyncio
async def test_smart_fallback():
    """Test smart field fallback"""
    service = FieldMappingService()

    # Data with alternative field
    data = {
        "id": 1,
        "name": False,  # Missing
        "display_name": "Ahmed Ali",  # Fallback
        "email": "ahmed@example.com"
    }

    # Apply fallback for 'name' field
    fallback_value = service._apply_fallback(data, "name")

    assert fallback_value == "Ahmed Ali"
