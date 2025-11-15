#!/usr/bin/env python3
"""
Integration tests for Flutter client compatibility

Test all endpoints to ensure they match Flutter client expectations.

Run this after starting the server:
    uvicorn app.main:app --reload

Then in another terminal:
    python test_flutter_integration.py
"""

import requests
import json
import sys
from typing import Dict, Any


BASE_URL = "http://localhost:8000"


def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_test(name: str, passed: bool, details: str = ""):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {name}")
    if details:
        print(f"    {details}")


def test_login() -> Dict[str, Any]:
    """Test login endpoint"""
    print_header("Testing Login Endpoint")

    url = f"{BASE_URL}/api/v1/auth/login"
    payload = {
        "username": "admin",
        "password": "admin",
        "database": "testdb"
    }

    try:
        response = requests.post(url, json=payload)
        print(f"\nRequest: POST {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        print(f"Status: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")

        # Validate response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "access_token" in data, "Missing access_token"
        assert "refresh_token" in data, "Missing refresh_token"
        assert "system_id" in data, "Missing system_id"
        assert "user" in data, "Missing user object"

        # Validate user object
        user = data["user"]
        assert "id" in user, "Missing user.id"
        assert "username" in user, "Missing user.username"
        assert "name" in user, "Missing user.name"
        assert "company_id" in user, "Missing user.company_id"
        assert "partner_id" in user, "Missing user.partner_id"

        # Validate system_id format
        assert data["system_id"] == "odoo-testdb", f"Expected 'odoo-testdb', got {data['system_id']}"

        print_test("Login endpoint", True, "All required fields present")
        return data

    except AssertionError as e:
        print_test("Login endpoint", False, str(e))
        sys.exit(1)
    except Exception as e:
        print_test("Login endpoint", False, f"Error: {str(e)}")
        sys.exit(1)


def test_refresh(refresh_token: str):
    """Test refresh token endpoint"""
    print_header("Testing Refresh Token Endpoint")

    url = f"{BASE_URL}/api/v1/auth/refresh"
    headers = {"Authorization": f"Bearer {refresh_token}"}

    try:
        response = requests.post(url, headers=headers)
        print(f"\nRequest: POST {url}")
        print(f"Headers: Authorization: Bearer {refresh_token[:20]}...")
        print(f"Status: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")

        # Validate response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "access_token" in data, "Missing access_token"
        assert isinstance(data["access_token"], str), "access_token should be string"

        print_test("Refresh token endpoint", True, "New access token received")
        return data["access_token"]

    except AssertionError as e:
        print_test("Refresh token endpoint", False, str(e))
        sys.exit(1)
    except Exception as e:
        print_test("Refresh token endpoint", False, f"Error: {str(e)}")
        sys.exit(1)


def test_session(access_token: str):
    """Test session info endpoint"""
    print_header("Testing Session Info Endpoint")

    url = f"{BASE_URL}/api/v1/auth/session"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        response = requests.get(url, headers=headers)
        print(f"\nRequest: GET {url}")
        print(f"Headers: Authorization: Bearer {access_token[:20]}...")
        print(f"Status: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")

        # Validate response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "user" in data, "Missing user object"
        assert "session_expires_at" in data, "Missing session_expires_at"

        # Validate user object
        user = data["user"]
        assert "id" in user, "Missing user.id"
        assert "username" in user, "Missing user.username"
        assert "name" in user, "Missing user.name"

        print_test("Session info endpoint", True, "Session info retrieved")

    except AssertionError as e:
        print_test("Session info endpoint", False, str(e))
        sys.exit(1)
    except Exception as e:
        print_test("Session info endpoint", False, f"Error: {str(e)}")
        sys.exit(1)


def test_odoo_operation(access_token: str, system_id: str):
    """Test Odoo operation endpoint"""
    print_header("Testing Odoo Operation Endpoint")

    url = f"{BASE_URL}/api/v1/systems/{system_id}/odoo/search_read"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "model": "product.product",
        "domain": [],
        "fields": ["id", "name", "display_name"],
        "limit": 10,
        "offset": 0
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"\nRequest: POST {url}")
        print(f"Headers: Authorization: Bearer {access_token[:20]}...")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        print(f"Status: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")

        # Validate response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "result" in data, "Missing result"
        assert isinstance(data["result"], list), "result should be a list"

        print_test("Odoo search_read operation", True, f"Retrieved {len(data['result'])} records")

    except AssertionError as e:
        print_test("Odoo search_read operation", False, str(e))
        sys.exit(1)
    except Exception as e:
        print_test("Odoo search_read operation", False, f"Error: {str(e)}")
        sys.exit(1)


def test_odoo_create(access_token: str, system_id: str):
    """Test Odoo create operation"""
    print_header("Testing Odoo Create Operation")

    url = f"{BASE_URL}/api/v1/systems/{system_id}/odoo/create"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "model": "res.partner",
        "values": {
            "name": "Test Partner",
            "email": "test@example.com"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"\nRequest: POST {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        print(f"Status: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")

        # Validate response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "result" in data, "Missing result"
        assert isinstance(data["result"], int), "result should be an integer (record ID)"

        print_test("Odoo create operation", True, f"Created record with ID {data['result']}")

    except AssertionError as e:
        print_test("Odoo create operation", False, str(e))
        sys.exit(1)
    except Exception as e:
        print_test("Odoo create operation", False, f"Error: {str(e)}")
        sys.exit(1)


def test_logout(access_token: str):
    """Test logout endpoint"""
    print_header("Testing Logout Endpoint")

    url = f"{BASE_URL}/api/v1/auth/logout"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        response = requests.post(url, headers=headers)
        print(f"\nRequest: POST {url}")
        print(f"Headers: Authorization: Bearer {access_token[:20]}...")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        # Validate response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert data == {}, f"Expected empty dict, got {data}"

        print_test("Logout endpoint", True, "Successfully logged out")

    except AssertionError as e:
        print_test("Logout endpoint", False, str(e))
        sys.exit(1)
    except Exception as e:
        print_test("Logout endpoint", False, f"Error: {str(e)}")
        sys.exit(1)


def test_health():
    """Test health endpoint"""
    print_header("Testing Health Endpoint")

    url = f"{BASE_URL}/health"

    try:
        response = requests.get(url)
        print(f"\nRequest: GET {url}")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        print_test("Health endpoint", True, "API is healthy")

    except AssertionError as e:
        print_test("Health endpoint", False, str(e))
        sys.exit(1)
    except Exception as e:
        print_test("Health endpoint", False, f"Error: {str(e)}")
        sys.exit(1)


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  BridgeCore Flutter Integration Tests")
    print("  Testing API compatibility with Flutter client")
    print("=" * 60)

    try:
        # Test health first
        test_health()

        # Test login
        login_data = test_login()
        access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]
        system_id = login_data["system_id"]

        # Test refresh
        new_access_token = test_refresh(refresh_token)

        # Test session with new token
        test_session(new_access_token)

        # Test Odoo operations
        test_odoo_operation(new_access_token, system_id)
        test_odoo_create(new_access_token, system_id)

        # Test logout
        test_logout(new_access_token)

        # All tests passed
        print_header("All Tests Passed! ✅")
        print("\nBridgeCore API is fully compatible with Flutter client.")
        print("You can now integrate the Flutter app with this backend.\n")

        return 0

    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n\nUnexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
