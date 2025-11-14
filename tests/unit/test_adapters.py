"""
Adapter tests
"""
import pytest
from app.adapters.odoo_adapter import OdooAdapter


@pytest.mark.asyncio
async def test_odoo_adapter_initialization():
    """Test Odoo adapter initialization"""
    config = {
        "url": "https://demo.odoo.com",
        "database": "demo",
        "username": "admin",
        "password": "admin"
    }

    adapter = OdooAdapter(config)

    assert adapter.url == "https://demo.odoo.com"
    assert adapter.database == "demo"
    assert adapter.is_connected is False


@pytest.mark.asyncio
async def test_field_fallback():
    """Test smart field fallback"""
    config = {
        "url": "https://demo.odoo.com",
        "database": "demo",
        "username": "admin",
        "password": "admin"
    }

    adapter = OdooAdapter(config)

    # Test fallback dictionary
    assert 'phone' in adapter.field_fallbacks
    assert 'mobile' in adapter.field_fallbacks['phone']
    assert 'phone_primary' in adapter.field_fallbacks['phone']


@pytest.mark.asyncio
async def test_apply_field_fallback():
    """Test field fallback application"""
    config = {
        "url": "https://demo.odoo.com",
        "database": "demo",
        "username": "admin",
        "password": "admin"
    }

    adapter = OdooAdapter(config)

    # Test data with missing phone but has mobile
    records = [
        {
            "id": 1,
            "name": "Ahmed",
            "phone": False,  # Missing
            "mobile": "+966501234567"
        }
    ]

    requested_fields = ["name", "phone"]

    result = adapter._apply_field_fallback(records, requested_fields)

    # phone should now have the mobile value
    assert result[0]["phone"] == "+966501234567"
