"""
Unit tests for analysis API routes
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status

class TestAnalysisRoutes:
    """Test analysis API routes functionality"""
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.analysis
    def test_analyze_image_endpoint(self, client, test_image_file):
        """Test image analysis endpoint"""
        with open(test_image_file, "rb") as f:
            response = client.post(
                "/analyze-image",
                files={"file": ("test.jpg", f, "image/jpeg")},
                data={"user_need": "sensitive skin"}
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert "ingredients_details" in data
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.analysis
    def test_analyze_text_endpoint(self, client, test_analysis_request):
        """Test text analysis endpoint"""
        response = client.post("/analyze-text", json=test_analysis_request)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert "ingredients_details" in data
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.analysis
    def test_analyze_text_invalid_data(self, client):
        """Test text analysis with invalid data"""
        response = client.post("/analyze-text", json={})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.analysis
    def test_analyze_text_empty_text(self, client):
        """Test text analysis with empty text"""
        response = client.post("/analyze-text", json={"text": "", "user_need": "general"})
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] == False
        assert "error" in data
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.analysis
    def test_ingredients_analyze_endpoint(self, client):
        """Test ingredients analysis endpoint"""
        request_data = {
            "ingredients": ["Hyaluronic Acid", "Niacinamide"],
            "user_need": "sensitive skin"
        }
        
        response = client.post("/ingredients/analyze", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert "ingredients_details" in data
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.analysis
    def test_ingredients_analyze_empty_list(self, client):
        """Test ingredients analysis with empty list"""
        request_data = {
            "ingredients": [],
            "user_need": "general"
        }
        
        response = client.post("/ingredients/analyze", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] == False
        assert "error" in data
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.analysis
    def test_analyze_image_invalid_file(self, client):
        """Test image analysis with invalid file"""
        response = client.post(
            "/analyze-image",
            files={"file": ("test.txt", b"not an image", "text/plain")},
            data={"user_need": "general"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.analysis
    def test_analyze_image_missing_file(self, client):
        """Test image analysis without file"""
        response = client.post(
            "/analyze-image",
            data={"user_need": "general"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.analysis
    def test_analyze_text_missing_fields(self, client):
        """Test text analysis with missing required fields"""
        response = client.post("/analyze-text", json={"text": "test"})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.analysis
    def test_analyze_text_long_text(self, client):
        """Test text analysis with very long text"""
        long_text = "Aqua, " * 1000  # Very long ingredient list
        
        response = client.post("/analyze-text", json={
            "text": long_text,
            "user_need": "general"
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.analysis
    def test_analyze_text_special_characters(self, client):
        """Test text analysis with special characters"""
        text_with_special_chars = "Aqua, Glycerin, Hyaluronic Acid (1%), Niacinamide 4%"
        
        response = client.post("/analyze-text", json={
            "text": text_with_special_chars,
            "user_need": "general"
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.analysis
    def test_analyze_text_unicode(self, client):
        """Test text analysis with unicode characters"""
        unicode_text = "Aqua, Glicerina, Ácido Hialurónico, Niacinamida"
        
        response = client.post("/analyze-text", json={
            "text": unicode_text,
            "user_need": "general"
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.analysis
    def test_analyze_text_different_user_needs(self, client):
        """Test text analysis with different user needs"""
        text = "Aqua, Glycerin, Hyaluronic Acid, Niacinamide"
        user_needs = ["sensitive skin", "acne-prone", "anti-aging", "general safety"]
        
        for user_need in user_needs:
            response = client.post("/analyze-text", json={
                "text": text,
                "user_need": user_need
            })
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "success" in data
            assert "suitability" in data
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.analysis
    def test_analyze_text_response_structure(self, client, test_analysis_request):
        """Test response structure for text analysis"""
        response = client.post("/analyze-text", json=test_analysis_request)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check required fields
        required_fields = [
            "success", "product_name", "ingredients_details", 
            "avg_eco_score", "suitability", "recommendations"
        ]
        for field in required_fields:
            assert field in data
        
        # Check ingredients_details structure
        if data["ingredients_details"]:
            ingredient = data["ingredients_details"][0]
            ingredient_fields = ["name", "risk_level", "eco_score"]
            for field in ingredient_fields:
                assert field in ingredient
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.analysis
    def test_analyze_image_response_structure(self, client, test_image_file):
        """Test response structure for image analysis"""
        with open(test_image_file, "rb") as f:
            response = client.post(
                "/analyze-image",
                files={"file": ("test.jpg", f, "image/jpeg")},
                data={"user_need": "sensitive skin"}
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check required fields
        required_fields = [
            "success", "product_name", "ingredients_details", 
            "avg_eco_score", "suitability", "recommendations"
        ]
        for field in required_fields:
            assert field in data
        
        # Check processing time
        if "processing_time_ms" in data:
            assert isinstance(data["processing_time_ms"], int)
            assert data["processing_time_ms"] > 0
