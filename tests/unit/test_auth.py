"""
Authentication tests
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test successful login"""
    response = await client.post(
        "/auth/login",
        json={
            "system_credentials": {
                "system_type": "odoo",
                "credentials": {
                    "url": "https://demo.odoo.com",
                    "database": "demo",
                    "username": "admin",
                    "password": "admin"
                }
            }
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Test login with invalid credentials"""
    response = await client.post(
        "/auth/login",
        json={
            "system_credentials": {
                "system_type": "odoo",
                "credentials": {
                    "url": "https://demo.odoo.com",
                    "database": "demo",
                    "username": "wrong",
                    "password": "wrong"
                }
            }
        }
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, auth_headers: dict):
    """Test getting current user info"""
    response = await client.get("/auth/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "username" in data
    assert "email" in data


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(client: AsyncClient):
    """Test accessing protected endpoint without token"""
    response = await client.get("/auth/me")

    assert response.status_code == 403  # No credentials provided
