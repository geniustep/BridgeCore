"""
Pytest fixtures for Odoo operation tests
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.odoo import (
    OdooOperationsService,
    SearchOperations,
    CRUDOperations,
    AdvancedOperations,
    NameOperations,
    ViewOperations,
    WebOperations,
    PermissionOperations,
    UtilityOperations,
    CustomOperations,
)


# Test Odoo credentials
TEST_ODOO_URL = "https://demo.odoo.com"
TEST_ODOO_DB = "demo"
TEST_ODOO_USER = "admin"
TEST_ODOO_PASS = "admin"


@pytest.fixture
def odoo_credentials():
    """Return test Odoo credentials"""
    return {
        "odoo_url": TEST_ODOO_URL,
        "database": TEST_ODOO_DB,
        "username": TEST_ODOO_USER,
        "password": TEST_ODOO_PASS,
    }


@pytest.fixture
def mock_execute_kw():
    """Mock _execute_kw method"""
    async def _mock(*args, **kwargs):
        return []
    return AsyncMock(side_effect=_mock)


@pytest.fixture
def search_service(odoo_credentials):
    """Create SearchOperations service"""
    return SearchOperations(**odoo_credentials)


@pytest.fixture
def crud_service(odoo_credentials):
    """Create CRUDOperations service"""
    return CRUDOperations(**odoo_credentials)


@pytest.fixture
def advanced_service(odoo_credentials):
    """Create AdvancedOperations service"""
    return AdvancedOperations(**odoo_credentials)


@pytest.fixture
def name_service(odoo_credentials):
    """Create NameOperations service"""
    return NameOperations(**odoo_credentials)


@pytest.fixture
def view_service(odoo_credentials):
    """Create ViewOperations service"""
    return ViewOperations(**odoo_credentials)


@pytest.fixture
def web_service(odoo_credentials):
    """Create WebOperations service"""
    return WebOperations(**odoo_credentials)


@pytest.fixture
def permission_service(odoo_credentials):
    """Create PermissionOperations service"""
    return PermissionOperations(**odoo_credentials)


@pytest.fixture
def utility_service(odoo_credentials):
    """Create UtilityOperations service"""
    return UtilityOperations(**odoo_credentials)


@pytest.fixture
def custom_service(odoo_credentials):
    """Create CustomOperations service"""
    return CustomOperations(**odoo_credentials)


@pytest.fixture
def mock_http_client():
    """Mock httpx AsyncClient"""
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        yield mock_instance


def create_json_response(data, status_code=200):
    """Helper to create mock JSON response"""
    response = MagicMock()
    response.status_code = status_code
    response.headers = {"content-type": "application/json"}
    response.json.return_value = {"jsonrpc": "2.0", "result": data}
    response.raise_for_status = MagicMock()
    return response


def create_error_response(error_message, error_code=None):
    """Helper to create mock error response"""
    response = MagicMock()
    response.status_code = 200
    response.headers = {"content-type": "application/json"}
    response.json.return_value = {
        "jsonrpc": "2.0",
        "error": {
            "code": error_code,
            "message": error_message,
            "data": {}
        }
    }
    response.raise_for_status = MagicMock()
    return response
