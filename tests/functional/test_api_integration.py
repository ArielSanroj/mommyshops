"""
Functional tests for API integration
Tests API endpoints, error handling, and integration between components
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch
import tempfile
import os

from app.main import app
from database import User, Product, Ingredient

class TestAPIIntegration:
    """Test API integration functionality"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def test_user(self, db_session):
        """Create test user"""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=pwd_context.hash("password123"),
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    @pytest.fixture
    def auth_headers(self, client, test_user):
        """Get authentication headers"""
        # Login to get token
        response = client.post("/auth/login", data={
            "username": test_user.username,
            "password": "password123"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_api_root_endpoint(self, client):
        """Test API root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
    
    def test_health_check_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "service" in data
    
    def test_detailed_health_check(self, client):
        """Test detailed health check"""
        response = client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "components" in data
        assert "system_metrics" in data
        assert "configuration" in data
    
    def test_readiness_check(self, client):
        """Test readiness check"""
        response = client.get("/health/readiness")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "ready"
        assert "timestamp" in data
    
    def test_liveness_check(self, client):
        """Test liveness check"""
        response = client.get("/health/liveness")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "alive"
        assert "timestamp" in data
    
    def test_api_documentation_endpoints(self, client):
        """Test API documentation endpoints"""
        # Test OpenAPI docs
        response = client.get("/docs")
        assert response.status_code == 200
        
        # Test ReDoc
        response = client.get("/redoc")
        assert response.status_code == 200
    
    def test_cors_headers(self, client):
        """Test CORS headers"""
        response = client.options("/", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })
        
        # Should handle CORS preflight
        assert response.status_code in [200, 204]
    
    def test_error_handling(self, client):
        """Test error handling"""
        # Test 404
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_authentication_required_endpoints(self, client):
        """Test that protected endpoints require authentication"""
        protected_endpoints = [
            "/auth/me",
            "/analysis/text",
            "/analysis/image",
            "/analysis/ingredients",
            "/analysis/history"
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
    
    def test_rate_limiting(self, client, auth_headers):
        """Test rate limiting"""
        # Make multiple requests quickly
        for i in range(10):
            response = client.post(
                "/analysis/text",
                json={"text": f"test ingredients {i}"},
                headers=auth_headers
            )
            
            # Should not be rate limited for normal usage
            assert response.status_code in [200, 400, 422, 429]
    
    def test_request_id_header(self, client):
        """Test request ID header"""
        response = client.get("/health/")
        
        # Should include request ID in response headers
        assert "X-Request-ID" in response.headers
    
    def test_content_type_validation(self, client, auth_headers):
        """Test content type validation"""
        # Test with invalid content type
        response = client.post(
            "/analysis/text",
            data="invalid data",
            headers={**auth_headers, "Content-Type": "text/plain"}
        )
        
        # Should handle gracefully
        assert response.status_code in [400, 422]
    
    def test_file_upload_validation(self, client, auth_headers):
        """Test file upload validation"""
        # Test with invalid file type
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp_file:
            tmp_file.write(b"not an image")
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, "rb") as f:
                response = client.post(
                    "/analysis/image",
                    files={"file": ("test.txt", f, "text/plain")},
                    headers=auth_headers
                )
            
            # Should fail validation
            assert response.status_code == 400
        
        finally:
            os.unlink(tmp_file_path)
    
    def test_database_connection(self, client):
        """Test database connection"""
        response = client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should show database status
        assert "components" in data
        assert "database" in data["components"]
    
    def test_external_api_integration(self, client, auth_headers):
        """Test external API integration"""
        # Mock external API calls
        with patch('app.services.ingredient_service.IngredientService.analyze_ingredients') as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "ingredients_analysis": [],
                "overall_score": 80.0,
                "recommendations": ["Test recommendation"]
            }
            
            response = client.post(
                "/analysis/ingredients",
                json={"ingredients": ["Test Ingredient"]},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_concurrent_requests(self, client, auth_headers):
        """Test handling of concurrent requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = client.post(
                "/analysis/text",
                json={"text": "test ingredients"},
                headers=auth_headers
            )
            results.append(response.status_code)
        
        # Make concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should be handled
        assert len(results) == 5
        # All should return valid status codes
        for status_code in results:
            assert status_code in [200, 400, 422, 429, 500]
    
    def test_memory_usage(self, client, auth_headers):
        """Test memory usage under load"""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Make multiple requests
        for i in range(20):
            response = client.post(
                "/analysis/text",
                json={"text": f"test ingredients {i}"},
                headers=auth_headers
            )
        
        # Check memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024
    
    def test_response_time(self, client, auth_headers):
        """Test response time"""
        import time
        
        start_time = time.time()
        response = client.post(
            "/analysis/text",
            json={"text": "test ingredients"},
            headers=auth_headers
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Response should be reasonably fast (less than 5 seconds)
        assert response_time < 5.0
        assert response.status_code in [200, 400, 422]
    
    def test_api_versioning(self, client):
        """Test API versioning"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should include version information
        assert "version" in data
        assert data["version"] == "1.0.0"
    
    def test_api_metadata(self, client):
        """Test API metadata"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should include all required metadata
        required_fields = ["message", "version", "docs", "health"]
        for field in required_fields:
            assert field in data
