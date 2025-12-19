#!/usr/bin/env python3
"""
Simple test to verify HTTPException handler works
Run: python3 simple_test.py
"""
import json
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

# Import app after setting up environment if needed
try:
    from app.main import app
except Exception as e:
    print(f"Error importing app: {e}")
    print("Make sure you're in the correct directory and dependencies are installed")
    exit(1)

def main():
    print("=" * 70)
    print("Testing HTTPException Handler")
    print("=" * 70)
    
    client = TestClient(app)
    
    # Test 1: Simulate the search_read error scenario
    print("\n[Test 1] Testing 500 Internal Server Error with actual message...")
    print("-" * 70)
    
    @app.get("/test-500-error")
    async def test_500():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error: Connection timeout to Odoo server"
        )
    
    try:
        response = client.get("/test-500-error")
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        # Verify
        assert response.status_code == 500
        assert "error" in data
        assert data["error"]["type"] == "InternalServerError"
        assert "Connection timeout" in data["error"]["message"]
        assert data["error"]["message"] != "An unexpected error occurred on the server"
        
        print("✅ PASSED: Actual error message is returned")
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    # Test 2: Test different status codes
    print("\n[Test 2] Testing different HTTP status codes...")
    print("-" * 70)
    
    test_cases = [
        (400, "BadRequest", "Invalid model name: test.model"),
        (403, "Forbidden", "Permission denied for search on shuttle.trip"),
        (404, "NotFound", "Odoo model not found: invalid.model"),
        (503, "ServiceUnavailable", "Odoo connection error: Server unavailable"),
    ]
    
    for status_code, expected_type, error_message in test_cases:
        @app.get(f"/test-{status_code}")
        async def test_endpoint(code=status_code, msg=error_message):
            raise HTTPException(status_code=code, detail=msg)
        
        try:
            response = client.get(f"/test-{status_code}")
            data = response.json()
            
            assert response.status_code == status_code
            assert data["error"]["type"] == expected_type
            assert error_message in data["error"]["message"]
            
            print(f"✅ {status_code} {expected_type}: {data['error']['message'][:50]}...")
            
        except Exception as e:
            print(f"❌ FAILED for {status_code}: {e}")
            return False
    
    # Clean up
    app.routes = [route for route in app.routes 
                  if not route.path.startswith("/test-")]
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    print("\nThe HTTPException handler is working correctly.")
    print("Frontend will now receive actual error messages.")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
