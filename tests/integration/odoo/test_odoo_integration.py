"""
Integration tests for Odoo operations with real Odoo instance

These tests require:
1. A running Odoo instance (can be demo.odoo.com or local)
2. Valid Odoo credentials
3. Environment variables set:
   - ODOO_URL
   - ODOO_DATABASE
   - ODOO_USERNAME
   - ODOO_PASSWORD

To run these tests:
    pytest tests/integration/odoo/test_odoo_integration.py -v

To skip integration tests (if Odoo not available):
    pytest tests/integration/odoo/test_odoo_integration.py -v -m "not integration"
"""
import pytest
import os
from typing import Optional

from app.services.odoo import (
    CRUDOperations,
    SearchOperations,
    AdvancedOperations,
    NameOperations,
    ViewOperations,
    UtilityOperations,
)


# Skip all integration tests if Odoo credentials not provided
pytestmark = pytest.mark.skipif(
    not all([
        os.getenv("ODOO_URL"),
        os.getenv("ODOO_DATABASE"),
        os.getenv("ODOO_USERNAME"),
        os.getenv("ODOO_PASSWORD"),
    ]),
    reason="Odoo credentials not provided. Set ODOO_URL, ODOO_DATABASE, ODOO_USERNAME, ODOO_PASSWORD"
)


@pytest.fixture
def odoo_credentials():
    """Get Odoo credentials from environment"""
    return {
        "odoo_url": os.getenv("ODOO_URL", "https://demo.odoo.com"),
        "database": os.getenv("ODOO_DATABASE", "demo"),
        "username": os.getenv("ODOO_USERNAME", "admin"),
        "password": os.getenv("ODOO_PASSWORD", "admin"),
    }


@pytest.fixture
async def crud_service(odoo_credentials):
    """Create CRUD service and authenticate"""
    service = CRUDOperations(**odoo_credentials)
    await service.authenticate()
    yield service
    await service.close()


@pytest.fixture
async def search_service(odoo_credentials):
    """Create Search service and authenticate"""
    service = SearchOperations(**odoo_credentials)
    await service.authenticate()
    yield service
    await service.close()


@pytest.fixture
async def utility_service(odoo_credentials):
    """Create Utility service and authenticate"""
    service = UtilityOperations(**odoo_credentials)
    await service.authenticate()
    yield service
    await service.close()


class TestCRUDIntegration:
    """Integration tests for CRUD operations"""

    @pytest.mark.asyncio
    async def test_create_and_read_partner(self, crud_service):
        """Test creating and reading a partner"""
        # Create a test partner
        partner_id = await crud_service.create(
            model="res.partner",
            values={
                "name": "Test Partner Integration",
                "email": "test.integration@example.com",
                "is_company": False,
            }
        )
        
        assert partner_id is not None
        assert isinstance(partner_id, int)
        
        # Read the created partner
        partners = await crud_service.read(
            model="res.partner",
            ids=[partner_id],
            fields=["name", "email", "is_company"]
        )
        
        assert len(partners) == 1
        assert partners[0]["id"] == partner_id
        assert partners[0]["name"] == "Test Partner Integration"
        assert partners[0]["email"] == "test.integration@example.com"
        
        # Cleanup: Delete the test partner
        await crud_service.unlink(model="res.partner", ids=[partner_id])

    @pytest.mark.asyncio
    async def test_update_partner(self, crud_service):
        """Test updating a partner"""
        # Create a test partner
        partner_id = await crud_service.create(
            model="res.partner",
            values={
                "name": "Original Name",
                "email": "original@example.com",
            }
        )
        
        # Update the partner
        success = await crud_service.write(
            model="res.partner",
            ids=[partner_id],
            values={
                "name": "Updated Name",
                "phone": "+1234567890",
            }
        )
        
        assert success is True
        
        # Verify the update
        partners = await crud_service.read(
            model="res.partner",
            ids=[partner_id],
            fields=["name", "email", "phone"]
        )
        
        assert partners[0]["name"] == "Updated Name"
        assert partners[0]["phone"] == "+1234567890"
        
        # Cleanup
        await crud_service.unlink(model="res.partner", ids=[partner_id])


class TestSearchIntegration:
    """Integration tests for Search operations"""

    @pytest.mark.asyncio
    async def test_search_companies(self, search_service):
        """Test searching for companies"""
        # Search for companies
        ids = await search_service.search(
            model="res.partner",
            domain=[["is_company", "=", True]],
            limit=10
        )
        
        assert isinstance(ids, list)
        assert len(ids) <= 10
        
        # If we have results, verify we can read them
        if ids:
            partners = await search_service.search_read(
                model="res.partner",
                domain=[["id", "in", ids[:5]]],
                fields=["name", "is_company"],
                limit=5
            )
            
            assert len(partners) <= 5
            for partner in partners:
                assert partner.get("is_company") is True

    @pytest.mark.asyncio
    async def test_search_count(self, search_service):
        """Test counting search results"""
        count = await search_service.search_count(
            model="res.partner",
            domain=[["is_company", "=", True]]
        )
        
        assert isinstance(count, int)
        assert count >= 0


class TestUtilityIntegration:
    """Integration tests for Utility operations"""

    @pytest.mark.asyncio
    async def test_fields_get(self, utility_service):
        """Test getting field definitions"""
        fields = await utility_service.fields_get(
            model="res.partner",
            fields=["name", "email", "phone"]
        )
        
        assert isinstance(fields, dict)
        assert "name" in fields
        assert "email" in fields
        assert "phone" in fields
        
        # Verify field structure
        name_field = fields["name"]
        assert "string" in name_field
        assert "type" in name_field

    @pytest.mark.asyncio
    async def test_default_get(self, utility_service):
        """Test getting default values"""
        defaults = await utility_service.default_get(
            model="res.partner",
            fields=["name", "email", "is_company"]
        )
        
        assert isinstance(defaults, dict)
        # Defaults may be empty, but structure should be correct

    @pytest.mark.asyncio
    async def test_get_metadata(self, utility_service):
        """Test getting record metadata"""
        # First, get a partner ID
        search_service = SearchOperations(
            odoo_url=utility_service.odoo_url,
            database=utility_service.database,
            username=utility_service.username,
            password=utility_service.password,
        )
        await search_service.authenticate()
        
        ids = await search_service.search(
            model="res.partner",
            domain=[],
            limit=1
        )
        await search_service.close()
        
        if ids:
            metadata = await utility_service.get_metadata(
                model="res.partner",
                ids=ids[:1]
            )
            
            assert isinstance(metadata, list)
            if metadata:
                assert "id" in metadata[0]
                assert "create_uid" in metadata[0] or "write_uid" in metadata[0]


class TestAdvancedIntegration:
    """Integration tests for Advanced operations"""

    @pytest.mark.asyncio
    async def test_onchange(self, odoo_credentials):
        """Test onchange operation"""
        service = AdvancedOperations(**odoo_credentials)
        await service.authenticate()
        
        try:
            result = await service.onchange(
                model="res.partner",
                values={"is_company": True},
                field_name="is_company",
                field_onchange={"is_company": "1"}
            )
            
            # Onchange may return empty dict or field updates
            assert isinstance(result, dict)
        finally:
            await service.close()

    @pytest.mark.asyncio
    async def test_read_group(self, odoo_credentials):
        """Test read_group operation"""
        service = AdvancedOperations(**odoo_credentials)
        await service.authenticate()
        
        try:
            groups = await service.read_group(
                model="res.partner",
                domain=[],
                fields=["name"],
                groupby=["is_company"],
                limit=10
            )
            
            assert isinstance(groups, list)
            # Each group should have __count and grouping field
            if groups:
                assert "__count" in groups[0] or "is_company" in groups[0]
        finally:
            await service.close()


class TestNameOperationsIntegration:
    """Integration tests for Name operations"""

    @pytest.mark.asyncio
    async def test_name_search(self, odoo_credentials):
        """Test name_search operation"""
        service = NameOperations(**odoo_credentials)
        await service.authenticate()
        
        try:
            results = await service.name_search(
                model="res.partner",
                name="",
                limit=10
            )
            
            assert isinstance(results, list)
            # Results are tuples of (id, name)
            if results:
                assert isinstance(results[0], (list, tuple))
                assert len(results[0]) >= 2
        finally:
            await service.close()

    @pytest.mark.asyncio
    async def test_name_get(self, odoo_credentials):
        """Test name_get operation"""
        service = NameOperations(**odoo_credentials)
        await service.authenticate()
        
        try:
            # First get a partner ID
            search_service = SearchOperations(**odoo_credentials)
            await search_service.authenticate()
            ids = await search_service.search(
                model="res.partner",
                domain=[],
                limit=1
            )
            await search_service.close()
            
            if ids:
                names = await service.name_get(
                    model="res.partner",
                    ids=ids[:1]
                )
                
                assert isinstance(names, list)
                if names:
                    assert isinstance(names[0], (list, tuple))
                    assert len(names[0]) >= 2
        finally:
            await service.close()

