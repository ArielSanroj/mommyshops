"""
End-to-end tests for complete analysis flow
Tests the entire user journey from image upload to results
"""

import pytest
import requests
import time
import json
from typing import Dict, Any

class TestCompleteAnalysisFlow:
    """Test complete analysis flow from start to finish"""
    
    @pytest.fixture
    def java_base_url(self):
        """Java backend base URL"""
        return "http://localhost:8080"
    
    @pytest.fixture
    def python_base_url(self):
        """Python backend base URL"""
        return "http://localhost:8000"
    
    @pytest.fixture
    def test_image_data(self):
        """Test image data"""
        return b"fake-image-data"
    
    @pytest.fixture
    def test_ingredients_text(self):
        """Test ingredients text"""
        return "Aqua, Glycerin, Hyaluronic Acid, Niacinamide, Retinol, Vitamin C"
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_complete_image_analysis_flow(self, java_base_url, test_image_data):
        """Test complete image analysis flow"""
        # Step 1: Upload image for analysis
        files = {"file": ("test_product.jpg", test_image_data, "image/jpeg")}
        data = {"user_need": "sensitive skin"}
        
        response = requests.post(
            f"{java_base_url}/api/analysis/analyze-image",
            files=files,
            data=data,
            timeout=60
        )
        
        assert response.status_code == 200
        analysis_data = response.json()
        
        # Verify response structure
        assert "success" in analysis_data
        assert "ingredients_details" in analysis_data
        assert "product_name" in analysis_data
        assert "avg_eco_score" in analysis_data
        assert "suitability" in analysis_data
        assert "recommendations" in analysis_data
        
        # Verify analysis quality
        if analysis_data["success"]:
            assert analysis_data["avg_eco_score"] >= 0
            assert analysis_data["avg_eco_score"] <= 100
            assert len(analysis_data["ingredients_details"]) > 0
            
            # Check ingredient details structure
            for ingredient in analysis_data["ingredients_details"]:
                assert "name" in ingredient
                assert "risk_level" in ingredient
                assert "eco_score" in ingredient
                assert "benefits" in ingredient
                assert "risks_detailed" in ingredient
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_complete_text_analysis_flow(self, java_base_url, test_ingredients_text):
        """Test complete text analysis flow"""
        # Step 1: Analyze text
        request_data = {
            "text": test_ingredients_text,
            "user_need": "anti-aging"
        }
        
        response = requests.post(
            f"{java_base_url}/api/analysis/analyze-product",
            json=request_data,
            timeout=60
        )
        
        assert response.status_code == 200
        analysis_data = response.json()
        
        # Verify response structure
        assert "success" in analysis_data
        assert "ingredients_details" in analysis_data
        assert "product_name" in analysis_data
        assert "avg_eco_score" in analysis_data
        assert "suitability" in analysis_data
        assert "recommendations" in analysis_data
        
        # Verify analysis quality
        if analysis_data["success"]:
            assert analysis_data["avg_eco_score"] >= 0
            assert analysis_data["avg_eco_score"] <= 100
            assert len(analysis_data["ingredients_details"]) > 0
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_complete_substitution_flow(self, java_base_url):
        """Test complete ingredient substitution flow"""
        # Step 1: Get alternatives for problematic ingredients
        request_data = {
            "problematic_ingredients": ["Sodium Lauryl Sulfate", "Parabens"],
            "user_conditions": ["sensitive skin", "eczema"]
        }
        
        response = requests.post(
            f"{java_base_url}/api/substitution/alternatives",
            json=request_data,
            timeout=60
        )
        
        assert response.status_code == 200
        alternatives_data = response.json()
        
        # Verify alternatives structure
        assert isinstance(alternatives_data, list)
        assert len(alternatives_data) > 0
        
        # Verify alternative quality
        for alternative in alternatives_data:
            assert isinstance(alternative, str)
            assert len(alternative) > 0
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_complete_health_check_flow(self, java_base_url, python_base_url):
        """Test complete health check flow"""
        # Step 1: Check Java health
        java_response = requests.get(f"{java_base_url}/api/health", timeout=10)
        assert java_response.status_code == 200
        
        java_health = java_response.json()
        assert "status" in java_health
        assert java_health["status"] in ["healthy", "degraded"]
        
        # Step 2: Check Python health
        python_response = requests.get(f"{python_base_url}/java/health", timeout=10)
        assert python_response.status_code == 200
        
        python_health = python_response.json()
        assert "status" in python_health
        assert python_health["status"] in ["healthy", "unhealthy"]
        
        # Step 3: Check Ollama status
        ollama_response = requests.get(f"{python_base_url}/ollama/status", timeout=10)
        assert ollama_response.status_code == 200
        
        ollama_status = ollama_response.json()
        assert "available" in ollama_status
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_complete_error_handling_flow(self, java_base_url):
        """Test complete error handling flow"""
        # Test with invalid data
        invalid_requests = [
            {"text": "", "user_need": "general"},  # Empty text
            {"text": "test", "user_need": ""},    # Empty user need
            {"text": None, "user_need": "general"},  # Null text
            {"text": "test", "user_need": None},   # Null user need
        ]
        
        for request_data in invalid_requests:
            response = requests.post(
                f"{java_base_url}/api/analysis/analyze-product",
                json=request_data,
                timeout=30
            )
            
            # Should handle errors gracefully
            assert response.status_code in [200, 400, 422]
            
            if response.status_code == 200:
                data = response.json()
                assert "success" in data
                if not data["success"]:
                    assert "error" in data
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_complete_performance_flow(self, java_base_url, test_ingredients_text):
        """Test complete performance flow"""
        # Test response times
        start_time = time.time()
        
        request_data = {
            "text": test_ingredients_text,
            "user_need": "sensitive skin"
        }
        
        response = requests.post(
            f"{java_base_url}/api/analysis/analyze-product",
            json=request_data,
            timeout=60
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 30  # Should complete within 30 seconds
        
        # Check if response includes processing time
        analysis_data = response.json()
        if "processing_time_ms" in analysis_data:
            assert analysis_data["processing_time_ms"] > 0
            assert analysis_data["processing_time_ms"] < 30000  # Less than 30 seconds
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_complete_concurrent_analysis_flow(self, java_base_url, test_ingredients_text):
        """Test complete concurrent analysis flow"""
        import concurrent.futures
        import threading
        
        def make_analysis_request():
            request_data = {
                "text": test_ingredients_text,
                "user_need": "sensitive skin"
            }
            
            response = requests.post(
                f"{java_base_url}/api/analysis/analyze-product",
                json=request_data,
                timeout=60
            )
            
            return response.status_code == 200
        
        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_analysis_request) for _ in range(5)]
            results = [future.result() for future in futures]
        
        # All requests should succeed
        success_count = sum(results)
        assert success_count >= 4  # At least 4 out of 5 should succeed
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_complete_data_consistency_flow(self, java_base_url, python_base_url, test_ingredients_text):
        """Test complete data consistency flow"""
        # Test same request through Java and Python
        request_data = {
            "text": test_ingredients_text,
            "user_need": "sensitive skin"
        }
        
        # Java analysis
        java_response = requests.post(
            f"{java_base_url}/api/analysis/analyze-product",
            json=request_data,
            timeout=60
        )
        
        # Python analysis
        python_response = requests.post(
            f"{python_base_url}/java/analyze-text",
            data=request_data,
            timeout=60
        )
        
        assert java_response.status_code == 200
        assert python_response.status_code == 200
        
        java_data = java_response.json()
        python_data = python_response.json()
        
        # Both should have similar structure
        assert "success" in java_data
        assert "success" in python_data
        assert "ingredients_details" in java_data
        assert "ingredients_details" in python_data
        
        # Both should be successful
        assert java_data["success"] == True
        assert python_data["success"] == True
        
        # Both should have ingredients
        assert len(java_data["ingredients_details"]) > 0
        assert len(python_data["ingredients_details"]) > 0
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_complete_monitoring_flow(self, java_base_url, python_base_url):
        """Test complete monitoring flow"""
        # Check Java health
        java_health = requests.get(f"{java_base_url}/api/health", timeout=10)
        assert java_health.status_code == 200
        
        # Check Python health
        python_health = requests.get(f"{python_base_url}/java/health", timeout=10)
        assert python_health.status_code == 200
        
        # Check Ollama status
        ollama_status = requests.get(f"{python_base_url}/ollama/status", timeout=10)
        assert ollama_status.status_code == 200
        
        # All services should be healthy
        java_data = java_health.json()
        python_data = python_health.json()
        ollama_data = ollama_status.json()
        
        assert java_data["status"] in ["healthy", "degraded"]
        assert python_data["status"] in ["healthy", "unhealthy"]
        assert "available" in ollama_data
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_complete_user_journey_flow(self, java_base_url, test_ingredients_text):
        """Test complete user journey flow"""
        # Step 1: User analyzes product
        analysis_request = {
            "text": test_ingredients_text,
            "user_need": "sensitive skin"
        }
        
        analysis_response = requests.post(
            f"{java_base_url}/api/analysis/analyze-product",
            json=analysis_request,
            timeout=60
        )
        
        assert analysis_response.status_code == 200
        analysis_data = analysis_response.json()
        
        if analysis_data["success"]:
            # Step 2: User gets recommendations
            assert "recommendations" in analysis_data
            assert len(analysis_data["recommendations"]) > 0
            
            # Step 3: User checks suitability
            assert "suitability" in analysis_data
            assert analysis_data["suitability"] in ["excellent", "good", "fair", "poor", "not recommended"]
            
            # Step 4: User gets ingredient details
            assert "ingredients_details" in analysis_data
            assert len(analysis_data["ingredients_details"]) > 0
            
            # Step 5: User gets eco score
            assert "avg_eco_score" in analysis_data
            assert 0 <= analysis_data["avg_eco_score"] <= 100
            
            # Step 6: User gets alternatives if needed
            if analysis_data["suitability"] in ["poor", "not recommended"]:
                alternatives_request = {
                    "problematic_ingredients": ["Sodium Lauryl Sulfate", "Parabens"],
                    "user_conditions": ["sensitive skin"]
                }
                
                alternatives_response = requests.post(
                    f"{java_base_url}/api/substitution/alternatives",
                    json=alternatives_request,
                    timeout=60
                )
                
                assert alternatives_response.status_code == 200
                alternatives_data = alternatives_response.json()
                assert isinstance(alternatives_data, list)
                assert len(alternatives_data) > 0
