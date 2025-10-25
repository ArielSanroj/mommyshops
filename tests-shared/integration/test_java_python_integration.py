"""
Integration tests for Java-Python communication
Tests the complete flow from Java backend to Python backend
"""

import pytest
import asyncio
import httpx
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
import io
from PIL import Image

# Import the FastAPI app
from backend.main import app

class TestJavaPythonIntegration:
    """Integration tests for Java-Python communication"""
    
    @pytest.fixture
    def python_client(self):
        """FastAPI test client for Python backend"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample test image"""
        img = Image.new('RGB', (200, 100), color='white')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes.getvalue()
    
    @pytest.fixture
    def mock_external_apis(self):
        """Mock external API responses"""
        with patch('backend.services.external_api_service.ExternalApiService') as mock_service:
            mock_service.return_value.query_fda.return_value = {
                "ingredient": "Water",
                "status": "approved",
                "restrictions": []
            }
            mock_service.return_value.query_ewg.return_value = {
                "ingredient": "Water",
                "ewg_score": 1,
                "concerns": []
            }
            mock_service.return_value.query_pubchem.return_value = {
                "ingredient": "Water",
                "cas": "7732-18-5",
                "molecular_weight": 18.015
            }
            yield mock_service
    
    @pytest.fixture
    def mock_ollama_service(self):
        """Mock Ollama service responses"""
        with patch('backend.services.ollama_service.OllamaService') as mock_ollama:
            mock_ollama.return_value.analyze_ingredients.return_value = {
                "analysis": "Safe ingredients for sensitive skin",
                "risk_level": "low",
                "recommendations": "Product is suitable for daily use"
            }
            yield mock_ollama
    
    @pytest.mark.integration
    async def test_java_to_python_image_analysis_flow(self, python_client, sample_image, mock_external_apis, mock_ollama_service):
        """
        Test complete flow: Java calls Python for image analysis
        This simulates what happens when Java backend calls Python
        """
        # Test the Python endpoint that Java calls
        response = python_client.post(
            "/java-integration/analyze-image",
            files={"file": ("test.png", sample_image, "image/png")},
            data={"user_need": "sensitive skin"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure matches Java expectations
        assert "success" in data
        assert "productName" in data
        assert "ingredientsDetails" in data
        assert "avgEcoScore" in data
        assert "suitability" in data
        assert "recommendations" in data
        assert "analysisId" in data
        assert "processingTimeMs" in data
        
        # Verify data types
        assert isinstance(data["success"], bool)
        assert isinstance(data["avgEcoScore"], (int, float))
        assert isinstance(data["ingredientsDetails"], list)
        assert isinstance(data["processingTimeMs"], int)
    
    @pytest.mark.integration
    async def test_python_backend_health_check(self, python_client):
        """Test Python backend health check"""
        response = python_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
    
    @pytest.mark.integration
    async def test_python_ocr_service_integration(self, python_client, sample_image):
        """Test OCR service integration"""
        with patch('backend.services.ocr_service.OCRService.extract_text_from_image') as mock_ocr:
            mock_ocr.return_value = "Water, Glycerin, Sodium Chloride"
            
            response = python_client.post(
                "/java-integration/analyze-image",
                files={"file": ("test.png", sample_image, "image/png")},
                data={"user_need": "general safety"}
            )
            
            assert response.status_code == 200
            mock_ocr.assert_called_once()
    
    @pytest.mark.integration
    async def test_python_external_api_integration(self, python_client, sample_image, mock_external_apis):
        """Test external API integration in Python"""
        response = python_client.post(
            "/java-integration/analyze-image",
            files={"file": ("test.png", sample_image, "image/png")},
            data={"user_need": "acne prone skin"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify external APIs were called
        mock_external_apis.return_value.query_fda.assert_called()
        mock_external_apis.return_value.query_ewg.assert_called()
    
    @pytest.mark.integration
    async def test_python_ollama_integration(self, python_client, sample_image, mock_ollama_service):
        """Test Ollama AI integration in Python"""
        response = python_client.post(
            "/java-integration/analyze-image",
            files={"file": ("test.png", sample_image, "image/png")},
            data={"user_need": "anti-aging"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify Ollama was called
        mock_ollama_service.return_value.analyze_ingredients.assert_called()
    
    @pytest.mark.integration
    async def test_error_handling_python_to_java(self, python_client, sample_image):
        """Test error handling when Python backend fails"""
        with patch('backend.services.ocr_service.OCRService.extract_text_from_image') as mock_ocr:
            mock_ocr.side_effect = Exception("OCR service unavailable")
            
            response = python_client.post(
                "/java-integration/analyze-image",
                files={"file": ("test.png", sample_image, "image/png")},
                data={"user_need": "general safety"}
            )
            
            # Should return error response, not crash
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "error" in data
    
    @pytest.mark.integration
    async def test_rate_limiting_integration(self, python_client, sample_image):
        """Test rate limiting between Java and Python"""
        # Make multiple requests quickly
        responses = []
        for i in range(15):  # Exceed rate limit
            response = python_client.post(
                "/java-integration/analyze-image",
                files={"file": ("test.png", sample_image, "image/png")},
                data={"user_need": "general safety"}
            )
            responses.append(response)
        
        # Some requests should be rate limited
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limited_responses) > 0
    
    @pytest.mark.integration
    async def test_circuit_breaker_simulation(self, python_client, sample_image):
        """Test circuit breaker behavior when Python backend is down"""
        with patch('backend.services.ocr_service.OCRService.extract_text_from_image') as mock_ocr:
            # Simulate Python backend being down
            mock_ocr.side_effect = httpx.ConnectError("Connection failed")
            
            response = python_client.post(
                "/java-integration/analyze-image",
                files={"file": ("test.png", sample_image, "image/png")},
                data={"user_need": "general safety"}
            )
            
            # Should handle gracefully
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
    
    @pytest.mark.integration
    async def test_data_consistency_between_java_python(self, python_client, sample_image):
        """Test that data format is consistent between Java and Python"""
        response = python_client.post(
            "/java-integration/analyze-image",
            files={"file": ("test.png", sample_image, "image/png")},
            data={"user_need": "sensitive skin"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all required fields for Java consumption
        required_fields = [
            "success", "productName", "ingredientsDetails", 
            "avgEcoScore", "suitability", "recommendations",
            "analysisId", "processingTimeMs"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Verify ingredientsDetails structure
        if data["ingredientsDetails"]:
            ingredient = data["ingredientsDetails"][0]
            required_ingredient_fields = [
                "name", "ecoScore", "riskLevel", 
                "benefits", "risksDetailed", "sources"
            ]
            
            for field in required_ingredient_fields:
                assert field in ingredient, f"Missing ingredient field: {field}"
    
    @pytest.mark.integration
    async def test_performance_metrics_integration(self, python_client, sample_image):
        """Test that performance metrics are tracked correctly"""
        response = python_client.post(
            "/java-integration/analyze-image",
            files={"file": ("test.png", sample_image, "image/png")},
            data={"user_need": "general safety"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify processing time is tracked
        assert "processingTimeMs" in data
        assert isinstance(data["processingTimeMs"], int)
        assert data["processingTimeMs"] > 0
        
        # Verify analysis ID is generated
        assert "analysisId" in data
        assert isinstance(data["analysisId"], str)
        assert len(data["analysisId"]) > 0
    
    @pytest.mark.integration
    async def test_concurrent_requests_handling(self, python_client, sample_image):
        """Test handling of concurrent requests from Java to Python"""
        import asyncio
        
        async def make_request():
            response = python_client.post(
                "/java-integration/analyze-image",
                files={"file": ("test.png", sample_image, "image/png")},
                data={"user_need": "general safety"}
            )
            return response
        
        # Make 5 concurrent requests
        tasks = [make_request() for _ in range(5)]
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert "success" in data

