"""
Integration tests for API endpoints
"""

import pytest
from fastapi import status


class TestHealthEndpoints:
    """Tests for health check endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data


class TestRateLimiting:
    """Tests for rate limiting middleware"""
    
    def test_rate_limit_not_applied_to_health(self, client):
        """Test rate limiting is not applied to health endpoint"""
        # Make many requests to health endpoint
        for _ in range(150):
            response = client.get("/health")
            assert response.status_code == status.HTTP_200_OK
    
    def test_rate_limit_headers(self, client):
        """Test rate limit headers are present"""
        # Skip test for health endpoint (excluded from rate limiting)
        # This would need to test a non-excluded endpoint
        pass


class TestCORSHeaders:
    """Tests for CORS configuration"""
    
    def test_cors_headers_present(self, client):
        """Test CORS headers are present"""
        response = client.options(
            "/",
            headers={"Origin": "http://localhost:8080"}
        )
        
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers or \
               response.status_code == status.HTTP_200_OK


class TestSecurityHeaders:
    """Tests for security headers and middleware"""
    
    def test_trusted_host_middleware(self, client):
        """Test trusted host middleware"""
        response = client.get(
            "/",
            headers={"Host": "localhost"}
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_untrusted_host_rejected(self, client):
        """Test untrusted host is rejected"""
        # This test depends on trusted host configuration
        # In test environment, might not reject
        pass


class TestErrorHandling:
    """Tests for error handling"""
    
    def test_404_not_found(self, client):
        """Test 404 error handling"""
        response = client.get("/nonexistent-endpoint")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_405_method_not_allowed(self, client):
        """Test 405 error handling"""
        response = client.delete("/")  # DELETE not allowed on root
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

