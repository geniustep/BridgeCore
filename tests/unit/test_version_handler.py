"""
Version Handler tests
"""
import pytest
from app.services.version_handler import VersionHandler


@pytest.mark.asyncio
async def test_version_handler_initialization():
    """Test version handler initialization"""
    handler = VersionHandler()

    assert "odoo" in handler.version_rules
    assert "res.partner" in handler.version_rules["odoo"]


@pytest.mark.asyncio
async def test_migrate_data_odoo_13_to_16():
    """Test data migration from Odoo 13 to 16"""
    handler = VersionHandler()

    # Odoo 13 data with deprecated fields
    v13_data = {
        "name": "Ahmed Ali",
        "customer": True,  # Deprecated in v16
        "phone": "+966501234567"
    }

    migrated_data = await handler.migrate_data(
        data=v13_data,
        system_type="odoo",
        from_version="13.0",
        to_version="16.0",
        model="res.partner"
    )

    # 'customer' should be removed and replaced
    assert "customer" not in migrated_data
    assert migrated_data.get("is_company") == False


@pytest.mark.asyncio
async def test_migrate_data_odoo_16_to_18():
    """Test data migration from Odoo 16 to 18"""
    handler = VersionHandler()

    # Odoo 16 data
    v16_data = {
        "name": "Ahmed Ali",
        "phone": "+966501234567",
        "mobile": "+966509876543"
    }

    migrated_data = await handler.migrate_data(
        data=v16_data,
        system_type="odoo",
        from_version="16.0",
        to_version="18.0",
        model="res.partner"
    )

    # Fields renamed in v18
    assert "phone_primary" in migrated_data
    assert "phone_secondary" in migrated_data
    assert "phone" not in migrated_data
    assert "mobile" not in migrated_data


@pytest.mark.asyncio
async def test_detect_version_differences():
    """Test version difference detection"""
    handler = VersionHandler()

    differences = await handler.detect_version_differences(
        system_type="odoo",
        from_version="16.0",
        to_version="18.0",
        model="res.partner"
    )

    assert differences["has_changes"] is True
    assert len(differences["renamed_fields"]) > 0
