"""
Functional tests for analysis flow
Tests the complete analysis workflow from input to results
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch
import tempfile
import os

from app.main import app
from app.dependencies import get_database
from database import User, Product, Ingredient
from core.config import get_settings

class TestAnalysisFlow:
    """Test complete analysis workflow"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def test_user(self, db_session):
        """Create test user"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
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
            "password": "testpassword"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_complete_text_analysis_flow(self, client, auth_headers):
        """Test complete text analysis workflow"""
        # Test data
        analysis_data = {
            "text": "Aqua, Glycerin, Hyaluronic Acid, Niacinamide, Retinol",
            "user_need": "anti-aging",
            "notes": "Looking for effective anti-aging ingredients"
        }
        
        # Mock external services
        with patch('app.services.analysis_service.AnalysisService._extract_ingredients_from_text') as mock_extract:
            with patch('app.services.ingredient_service.IngredientService.analyze_ingredients') as mock_analyze:
                # Setup mocks
                mock_extract.return_value = ["Aqua", "Glycerin", "Hyaluronic Acid", "Niacinamide", "Retinol"]
                mock_analyze.return_value = {
                    "success": True,
                    "ingredients_analysis": [
                        {
                            "name": "Hyaluronic Acid",
                            "risk_level": "low",
                            "eco_score": 85.0,
                            "benefits": "Hydrating",
                            "risks": "None known"
                        },
                        {
                            "name": "Retinol",
                            "risk_level": "medium",
                            "eco_score": 70.0,
                            "benefits": "Anti-aging",
                            "risks": "May cause irritation"
                        }
                    ],
                    "overall_score": 77.5,
                    "recommendations": [
                        "Product has good anti-aging ingredients",
                        "Consider patch testing for Retinol sensitivity"
                    ]
                }
                
                # Perform analysis
                response = client.post(
                    "/analysis/text",
                    json=analysis_data,
                    headers=auth_headers
                )
                
                # Assertions
                assert response.status_code == 200
                data = response.json()
                
                assert data["success"] is True
                assert data["product_name"] is not None
                assert len(data["ingredients"]) == 2
                assert data["avg_eco_score"] == 77.5
                assert data["suitability"] in ["excellent", "good", "moderate", "poor"]
                assert len(data["recommendations"]) > 0
                assert data["processing_time"] > 0
    
    def test_complete_image_analysis_flow(self, client, auth_headers):
        """Test complete image analysis workflow"""
        # Create test image
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
            tmp_file.write(b"fake_image_data")
            tmp_file_path = tmp_file.name
        
        try:
            # Mock OCR service
            with patch('app.services.ocr_service.OCRService.extract_text_from_image') as mock_ocr:
                with patch('app.services.analysis_service.AnalysisService._extract_ingredients_from_text') as mock_extract:
                    with patch('app.services.ingredient_service.IngredientService.analyze_ingredients') as mock_analyze:
                        # Setup mocks
                        mock_ocr.return_value = "Aqua, Glycerin, Hyaluronic Acid, Niacinamide"
                        mock_extract.return_value = ["Aqua", "Glycerin", "Hyaluronic Acid", "Niacinamide"]
                        mock_analyze.return_value = {
                            "success": True,
                            "ingredients_analysis": [
                                {
                                    "name": "Hyaluronic Acid",
                                    "risk_level": "low",
                                    "eco_score": 85.0,
                                    "benefits": "Hydrating",
                                    "risks": "None known"
                                }
                            ],
                            "overall_score": 85.0,
                            "recommendations": ["Product has excellent hydrating ingredients"]
                        }
                        
                        # Perform image analysis
                        with open(tmp_file_path, "rb") as f:
                            response = client.post(
                                "/analysis/image",
                                files={"file": ("test.jpg", f, "image/jpeg")},
                                data={
                                    "product_name": "Test Product",
                                    "user_need": "hydration"
                                },
                                headers=auth_headers
                            )
                        
                        # Assertions
                        assert response.status_code == 200
                        data = response.json()
                        
                        assert data["success"] is True
                        assert data["product_name"] == "Test Product"
                        assert len(data["ingredients"]) == 1
                        assert data["avg_eco_score"] == 85.0
                        assert data["suitability"] == "excellent"
                        assert len(data["recommendations"]) > 0
        
        finally:
            # Cleanup
            os.unlink(tmp_file_path)
    
    def test_ingredient_analysis_flow(self, client, auth_headers):
        """Test ingredient analysis workflow"""
        # Test data
        analysis_data = {
            "ingredients": ["Hyaluronic Acid", "Retinol", "Vitamin C"],
            "user_concerns": ["sensitive skin", "anti-aging"]
        }
        
        # Mock ingredient service
        with patch('app.services.ingredient_service.IngredientService.analyze_ingredients') as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "ingredients_analysis": [
                    {
                        "name": "Hyaluronic Acid",
                        "risk_level": "low",
                        "eco_score": 85.0,
                        "benefits": "Hydrating",
                        "risks": "None known"
                    },
                    {
                        "name": "Retinol",
                        "risk_level": "medium",
                        "eco_score": 70.0,
                        "benefits": "Anti-aging",
                        "risks": "May cause irritation"
                    },
                    {
                        "name": "Vitamin C",
                        "risk_level": "low",
                        "eco_score": 90.0,
                        "benefits": "Antioxidant",
                        "risks": "May cause photosensitivity"
                    }
                ],
                "overall_score": 81.7,
                "recommendations": [
                    "Great combination for anti-aging",
                    "Use sunscreen with Vitamin C",
                    "Start with low concentration Retinol"
                ]
            }
            
            # Perform ingredient analysis
            response = client.post(
                "/analysis/ingredients",
                json=analysis_data,
                headers=auth_headers
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert len(data["ingredients_analysis"]) == 3
            assert data["overall_score"] == 81.7
            assert len(data["recommendations"]) == 3
            assert data["processing_time"] > 0
    
    def test_analysis_history_flow(self, client, auth_headers, test_user, db_session):
        """Test analysis history retrieval"""
        # Create test products
        products = [
            Product(
                name="Product 1",
                ingredients=["Ingredient 1", "Ingredient 2"],
                user_id=test_user.id,
                analysis_data={"score": 80}
            ),
            Product(
                name="Product 2", 
                ingredients=["Ingredient 3", "Ingredient 4"],
                user_id=test_user.id,
                analysis_data={"score": 90}
            )
        ]
        
        for product in products:
            db_session.add(product)
        db_session.commit()
        
        # Get analysis history
        response = client.get(
            "/analysis/history",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert len(data["history"]) == 2
        assert data["total"] == 2
        
        # Check product data
        product_names = [item["name"] for item in data["history"]]
        assert "Product 1" in product_names
        assert "Product 2" in product_names
    
    def test_analysis_error_handling(self, client, auth_headers):
        """Test analysis error handling"""
        # Test with invalid data
        response = client.post(
            "/analysis/text",
            json={"text": ""},  # Empty text
            headers=auth_headers
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]
    
    def test_analysis_without_authentication(self, client):
        """Test analysis without authentication"""
        response = client.post(
            "/analysis/text",
            json={"text": "test ingredients"}
        )
        
        # Should require authentication
        assert response.status_code == 401
    
    def test_analysis_rate_limiting(self, client, auth_headers):
        """Test analysis rate limiting"""
        # Make multiple requests quickly
        for i in range(5):
            response = client.post(
                "/analysis/text",
                json={"text": f"test ingredients {i}"},
                headers=auth_headers
            )
            
            # Should not be rate limited for normal usage
            assert response.status_code in [200, 400, 422]
    
    def test_analysis_with_mock_services(self, client, auth_headers):
        """Test analysis with mocked external services"""
        # Mock all external services
        with patch('app.services.ocr_service.OCRService') as mock_ocr:
            with patch('app.services.ingredient_service.IngredientService') as mock_ingredient:
                with patch('app.services.analysis_service.AnalysisService') as mock_analysis:
                    # Setup mocks
                    mock_ocr.return_value.extract_text_from_image.return_value = "test ingredients"
                    mock_ingredient.return_value.analyze_ingredients.return_value = {
                        "success": True,
                        "ingredients_analysis": [],
                        "overall_score": 80.0,
                        "recommendations": ["Test recommendation"]
                    }
                    mock_analysis.return_value.analyze_text.return_value = {
                        "success": True,
                        "product_name": "Test Product",
                        "ingredients": [],
                        "avg_eco_score": 80.0,
                        "suitability": "good",
                        "recommendations": ["Test recommendation"]
                    }
                    
                    # Test text analysis
                    response = client.post(
                        "/analysis/text",
                        json={"text": "test ingredients"},
                        headers=auth_headers
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
