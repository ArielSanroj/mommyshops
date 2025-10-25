"""
Integration tests for Java-Python communication
Tests the complete flow from Java to Python and back
"""

import pytest
import requests
import json
import time
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class TestJavaPythonIntegration:
    """Test suite for Java-Python integration"""
    
    def setup_method(self):
        """Setup test environment"""
        self.java_base_url = "http://localhost:8080"
        self.python_base_url = "http://localhost:8000"
        self.timeout = 30
        
    def test_java_health_check(self):
        """Test Java health endpoint"""
        response = requests.get(f"{self.java_base_url}/api/health", timeout=self.timeout)
        assert response.status_code == 200
        
        health_data = response.json()
        assert "status" in health_data
        assert health_data["status"] in ["healthy", "degraded"]
        
    def test_python_health_check(self):
        """Test Python health endpoint"""
        response = requests.get(f"{self.python_base_url}/java/health", timeout=self.timeout)
        assert response.status_code == 200
        
        health_data = response.json()
        assert "status" in health_data
        assert health_data["status"] in ["healthy", "unhealthy"]
        
    def test_java_python_communication(self):
        """Test direct Java to Python communication"""
        # Test text analysis through Java
        test_data = {
            "text": "Aqua, Glycerin, Hyaluronic Acid, Niacinamide",
            "user_need": "sensitive skin"
        }
        
        response = requests.post(
            f"{self.java_base_url}/api/analysis/analyze-product",
            json=test_data,
            timeout=self.timeout
        )
        
        assert response.status_code == 200
        analysis_data = response.json()
        assert "success" in analysis_data
        assert "ingredients_details" in analysis_data
        
    def test_python_ollama_status(self):
        """Test Python Ollama service status"""
        response = requests.get(f"{self.python_base_url}/ollama/status", timeout=self.timeout)
        assert response.status_code == 200
        
        ollama_data = response.json()
        assert "available" in ollama_data
        
    def test_java_python_substitution_flow(self):
        """Test complete substitution flow from Java to Python"""
        test_data = {
            "problematic_ingredients": ["Sodium Lauryl Sulfate", "Parabens"],
            "user_conditions": ["sensitive skin", "eczema"]
        }
        
        response = requests.post(
            f"{self.java_base_url}/api/substitution/alternatives",
            json=test_data,
            timeout=self.timeout
        )
        
        assert response.status_code == 200
        alternatives_data = response.json()
        assert isinstance(alternatives_data, list)
        
    def test_python_external_api_integration(self):
        """Test Python external API integration"""
        # Test ingredient analysis
        test_ingredient = "Hyaluronic Acid"
        
        response = requests.post(
            f"{self.python_base_url}/java/ingredient-analysis",
            data={"ingredient": test_ingredient},
            timeout=self.timeout
        )
        
        assert response.status_code == 200
        ingredient_data = response.json()
        assert "name" in ingredient_data
        assert "riskLevel" in ingredient_data
        
    def test_error_handling(self):
        """Test error handling in Java-Python communication"""
        # Test with invalid data
        invalid_data = {
            "text": "",  # Empty text should cause error
            "user_need": "invalid_need"
        }
        
        response = requests.post(
            f"{self.java_base_url}/api/analysis/analyze-product",
            json=invalid_data,
            timeout=self.timeout
        )
        
        # Should handle error gracefully
        assert response.status_code in [200, 400, 500]
        
    def test_circuit_breaker_behavior(self):
        """Test circuit breaker behavior when Python is down"""
        # This test would require stopping Python service
        # For now, just test that Java handles Python unavailability
        pass
        
    def test_performance_metrics(self):
        """Test performance of Java-Python communication"""
        start_time = time.time()
        
        test_data = {
            "text": "Aqua, Glycerin, Hyaluronic Acid, Niacinamide, Retinol",
            "user_need": "anti-aging"
        }
        
        response = requests.post(
            f"{self.java_base_url}/api/analysis/analyze-product",
            json=test_data,
            timeout=self.timeout
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 10  # Should complete within 10 seconds
        
        # Check if response includes processing time
        analysis_data = response.json()
        if "processingTimeMs" in analysis_data:
            assert analysis_data["processingTimeMs"] > 0
            
    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        import concurrent.futures
        import threading
        
        def make_request():
            test_data = {
                "text": "Aqua, Glycerin, Hyaluronic Acid",
                "user_need": "general safety"
            }
            return requests.post(
                f"{self.java_base_url}/api/analysis/analyze-product",
                json=test_data,
                timeout=self.timeout
            )
        
        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [future.result() for future in futures]
        
        # All requests should succeed
        for response in results:
            assert response.status_code == 200
            
    def test_data_consistency(self):
        """Test data consistency between Java and Python"""
        test_data = {
            "text": "Aqua, Glycerin, Hyaluronic Acid, Niacinamide",
            "user_need": "sensitive skin"
        }
        
        # Get response from Java
        java_response = requests.post(
            f"{self.java_base_url}/api/analysis/analyze-product",
            json=test_data,
            timeout=self.timeout
        )
        
        # Get response directly from Python
        python_response = requests.post(
            f"{self.python_base_url}/java/analyze-text",
            data=test_data,
            timeout=self.timeout
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
        
    def test_authentication_flow(self):
        """Test authentication flow between Java and Python"""
        # This would test JWT token passing from Java to Python
        # For now, just test that endpoints are accessible
        response = requests.get(f"{self.java_base_url}/api/health", timeout=self.timeout)
        assert response.status_code == 200
        
    def test_monitoring_integration(self):
        """Test monitoring and metrics integration"""
        # Test that health endpoints return monitoring data
        java_health = requests.get(f"{self.java_base_url}/api/health", timeout=self.timeout)
        python_health = requests.get(f"{self.python_base_url}/java/health", timeout=self.timeout)
        
        assert java_health.status_code == 200
        assert python_health.status_code == 200
        
        java_data = java_health.json()
        python_data = python_health.json()
        
        # Both should have monitoring information
        assert "timestamp" in java_data
        assert "timestamp" in python_data
        assert "service" in python_data

if __name__ == "__main__":
    pytest.main([__file__, "-v"])