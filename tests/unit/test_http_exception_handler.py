"""
Test HTTPException handler to verify error messages are properly formatted
"""
import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from app.main import app


class TestHTTPExceptionHandler:
    """Test HTTPException handler"""

    def test_http_exception_returns_actual_error_message(self):
        """Test that HTTPException returns the actual error message, not generic one"""
        client = TestClient(app)
        
        # Create a test endpoint that raises HTTPException with specific message
        @app.get("/test-error-handler")
        async def test_error_endpoint():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal error: Connection timeout to Odoo server"
            )
        
        response = client.get("/test-error-handler")
        
        assert response.status_code == 500
        data = response.json()
        
        # Verify the error structure
        assert "error" in data
        assert data["error"]["type"] == "InternalServerError"
        # Verify the actual error message is returned, not generic one
        assert "Connection timeout to Odoo server" in data["error"]["message"]
        assert data["error"]["message"] != "An unexpected error occurred on the server"
        
        # Clean up - remove the test endpoint
        app.routes = [route for route in app.routes if route.path != "/test-error-handler"]

    def test_http_exception_with_different_status_codes(self):
        """Test HTTPException handler with different status codes"""
        client = TestClient(app)
        
        # Test 400 Bad Request
        @app.get("/test-400")
        async def test_400():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid model name provided"
            )
        
        response = client.get("/test-400")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["type"] == "BadRequest"
        assert "Invalid model name provided" in data["error"]["message"]
        
        # Test 403 Forbidden
        @app.get("/test-403")
        async def test_403():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied for search on shuttle.trip"
            )
        
        response = client.get("/test-403")
        assert response.status_code == 403
        data = response.json()
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
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["type"] == "NotFound"
        assert "Odoo model not found" in data["error"]["message"]
        
        # Clean up
        app.routes = [route for route in app.routes if route.path not in ["/test-400", "/test-403", "/test-404"]]

    def test_http_exception_with_dict_detail(self):
        """Test HTTPException handler when detail is a dict"""
        client = TestClient(app)
        
        @app.get("/test-dict-detail")
        async def test_dict_detail():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"message": "Custom error message from dict"}
            )
        
        response = client.get("/test-dict-detail")
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["type"] == "InternalServerError"
        assert "Custom error message from dict" in data["error"]["message"]
        
        # Clean up
        app.routes = [route for route in app.routes if route.path != "/test-dict-detail"]
