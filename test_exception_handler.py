"""
Simple test script to verify HTTPException handler works correctly
"""
import sys
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from app.main import app

def test_http_exception_handler():
    """Test that HTTPException handler returns actual error messages"""
    client = TestClient(app)
    
    # Create a test endpoint that simulates the search_read error
    @app.get("/test-search-read-error")
    async def test_search_read_error():
        # Simulate the error that occurs in search_read endpoint
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error: Connection timeout to Odoo server"
        )
    
    print("Testing HTTPException handler...")
    print("=" * 60)
    
    # Test the endpoint
    response = client.get("/test-search-read-error")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response JSON: {response.json()}")
    print("=" * 60)
    
    data = response.json()
    
    # Verify the error structure
    assert response.status_code == 500, f"Expected 500, got {response.status_code}"
    assert "error" in data, "Response should contain 'error' key"
    assert data["error"]["type"] == "InternalServerError", f"Expected InternalServerError, got {data['error']['type']}"
    
    # Verify the actual error message is returned, not generic one
    error_message = data["error"]["message"]
    assert "Connection timeout to Odoo server" in error_message, \
        f"Expected actual error message, got: {error_message}"
    assert error_message != "An unexpected error occurred on the server", \
        "Should not return generic error message"
    
    print("✅ Test PASSED: HTTPException handler returns actual error message")
    print(f"   Error message: {error_message}")
    
    # Test with different error types
    print("\n" + "=" * 60)
    print("Testing different error types...")
    print("=" * 60)
    
    # Test 400 Bad Request
    @app.get("/test-400")
    async def test_400():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid model name: shuttle.trip"
        )
    
    response = client.get("/test-400")
    data = response.json()
    print(f"400 Error - Type: {data['error']['type']}, Message: {data['error']['message']}")
    assert data["error"]["type"] == "BadRequest"
    assert "Invalid model name" in data["error"]["message"]
    
    # Test 403 Forbidden
    @app.get("/test-403")
    async def test_403():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied for search on shuttle.trip"
        )
    
    response = client.get("/test-403")
    data = response.json()
    print(f"403 Error - Type: {data['error']['type']}, Message: {data['error']['message']}")
    assert data["error"]["type"] == "Forbidden"
    assert "Permission denied" in data["error"]["message"]
    
    # Test 404 Not Found
    @app.get("/test-404")
    async def test_404():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Odoo model not found: invalid.model"
        )
    
    response = client.get("/test-404")
    data = response.json()
    print(f"404 Error - Type: {data['error']['type']}, Message: {data['error']['message']}")
    assert data["error"]["type"] == "NotFound"
    assert "Odoo model not found" in data["error"]["message"]
    
    print("\n✅ All tests PASSED!")
    print("=" * 60)
    print("The HTTPException handler is working correctly!")
    print("Frontend will now receive actual error messages instead of generic ones.")
    
    # Clean up test routes
    app.routes = [route for route in app.routes 
                  if route.path not in ["/test-search-read-error", "/test-400", "/test-403", "/test-404"]]

if __name__ == "__main__":
    try:
        test_http_exception_handler()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error running test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
