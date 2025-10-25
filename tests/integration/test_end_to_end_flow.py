"""
End-to-end integration tests simulating complete user flows
"""

import pytest
import httpx
import asyncio
from unittest.mock import patch, MagicMock
import json
import io
from PIL import Image

class TestEndToEndFlow:
    """End-to-end tests for complete user flows"""
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample test image"""
        img = Image.new('RGB', (200, 100), color='white')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes.getvalue()
    
    @pytest.mark.e2e
    async def test_complete_product_analysis_flow(self, sample_image):
        """
        Test complete flow: User uploads image -> Java -> Python -> Analysis -> Response
        This simulates the real user journey
        """
        # Mock external services
        with patch('backend.services.external_api_service.ExternalApiService') as mock_apis, \
             patch('backend.services.ollama_service.OllamaService') as mock_ollama, \
             patch('backend.services.ocr_service.OCRService') as mock_ocr:
            
            # Configure mocks
            mock_ocr.return_value.extract_text_from_image.return_value = "Water, Glycerin, Sodium Chloride"
            mock_apis.return_value.query_fda.return_value = {"status": "approved"}
            mock_apis.return_value.query_ewg.return_value = {"ewg_score": 2}
            mock_ollama.return_value.analyze_ingredients.return_value = {
                "analysis": "Safe for sensitive skin",
                "risk_level": "low"
            }
            
            # Simulate Java backend calling Python
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/java-integration/analyze-image",
                    files={"file": ("product.jpg", sample_image, "image/jpeg")},
                    data={"user_need": "sensitive skin"}
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Verify complete analysis response
                assert data["success"] is True
                assert "productName" in data
                assert "ingredientsDetails" in data
                assert "avgEcoScore" in data
                assert "suitability" in data
                assert "recommendations" in data
                
                # Verify external services were called
                mock_ocr.return_value.extract_text_from_image.assert_called()
                mock_apis.return_value.query_fda.assert_called()
                mock_apis.return_value.query_ewg.assert_called()
                mock_ollama.return_value.analyze_ingredients.assert_called()
    
    @pytest.mark.e2e
    async def test_user_registration_and_analysis_flow(self, sample_image):
        """
        Test complete user flow: Registration -> Login -> Analysis
        """
        async with httpx.AsyncClient() as client:
            # Step 1: User registration
            register_data = {
                "email": "test@example.com",
                "password": "SecurePass123!",
                "full_name": "Test User"
            }
            
            with patch('backend.core.database.get_db') as mock_db:
                # Mock database operations
                mock_db.return_value.add.return_value = None
                mock_db.return_value.commit.return_value = None
                mock_db.return_value.refresh.return_value = None
                
                register_response = await client.post(
                    "http://localhost:8000/auth/register",
                    json=register_data
                )
                
                # Should succeed (or fail gracefully if user exists)
                assert register_response.status_code in [200, 201, 409]
            
            # Step 2: User login
            login_data = {
                "email": "test@example.com",
                "password": "SecurePass123!"
            }
            
            with patch('backend.core.security.verify_password') as mock_verify:
                mock_verify.return_value = True
                
                login_response = await client.post(
                    "http://localhost:8000/auth/token",
                    data=login_data
                )
                
                # Should get JWT token
                assert login_response.status_code == 200
                token_data = login_response.json()
                assert "access_token" in token_data
                token = token_data["access_token"]
            
            # Step 3: Authenticated analysis
            headers = {"Authorization": f"Bearer {token}"}
            
            with patch('backend.services.ocr_service.OCRService') as mock_ocr:
                mock_ocr.return_value.extract_text_from_image.return_value = "Water, Glycerin"
                
                analysis_response = await client.post(
                    "http://localhost:8000/analyze-text",
                    headers=headers,
                    json={
                        "text": "Water, Glycerin, Sodium Chloride",
                        "user_need": "sensitive skin"
                    }
                )
                
                assert analysis_response.status_code == 200
                data = analysis_response.json()
                assert "success" in data
    
    @pytest.mark.e2e
    async def test_error_recovery_flow(self, sample_image):
        """
        Test error recovery: Service fails -> Fallback -> Success
        """
        async with httpx.AsyncClient() as client:
            # First request fails
            with patch('backend.services.ocr_service.OCRService.extract_text_from_image') as mock_ocr:
                mock_ocr.side_effect = Exception("OCR service down")
                
                response1 = await client.post(
                    "http://localhost:8000/java-integration/analyze-image",
                    files={"file": ("test.png", sample_image, "image/png")},
                    data={"user_need": "general safety"}
                )
                
                # Should handle error gracefully
                assert response1.status_code == 200
                data1 = response1.json()
                assert data1["success"] is False
                assert "error" in data1
            
            # Second request succeeds (service recovered)
            with patch('backend.services.ocr_service.OCRService.extract_text_from_image') as mock_ocr:
                mock_ocr.return_value = "Water, Glycerin"
                
                response2 = await client.post(
                    "http://localhost:8000/java-integration/analyze-image",
                    files={"file": ("test.png", sample_image, "image/png")},
                    data={"user_need": "general safety"}
                )
                
                # Should succeed
                assert response2.status_code == 200
                data2 = response2.json()
                assert data2["success"] is True
    
    @pytest.mark.e2e
    async def test_performance_under_load(self, sample_image):
        """
        Test system performance under load
        """
        async def make_request():
            async with httpx.AsyncClient() as client:
                return await client.post(
                    "http://localhost:8000/java-integration/analyze-image",
                    files={"file": ("test.png", sample_image, "image/png")},
                    data={"user_need": "general safety"}
                )
        
        # Make 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successful responses
        successful = [r for r in responses if not isinstance(r, Exception) and r.status_code == 200]
        rate_limited = [r for r in responses if not isinstance(r, Exception) and r.status_code == 429]
        
        # Should have some successful and some rate limited
        assert len(successful) > 0
        assert len(rate_limited) > 0  # Rate limiting should kick in
    
    @pytest.mark.e2e
    async def test_data_consistency_across_services(self, sample_image):
        """
        Test that data remains consistent across Java and Python services
        """
        async with httpx.AsyncClient() as client:
            # Make request to Python backend
            response = await client.post(
                "http://localhost:8000/java-integration/analyze-image",
                files={"file": ("test.png", sample_image, "image/png")},
                data={"user_need": "sensitive skin"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify data structure is consistent
            assert isinstance(data["success"], bool)
            assert isinstance(data["avgEcoScore"], (int, float))
            assert 0 <= data["avgEcoScore"] <= 100
            assert isinstance(data["ingredientsDetails"], list)
            assert isinstance(data["processingTimeMs"], int)
            assert data["processingTimeMs"] > 0
            
            # Verify ingredients structure
            for ingredient in data["ingredientsDetails"]:
                assert "name" in ingredient
                assert "ecoScore" in ingredient
                assert "riskLevel" in ingredient
                assert isinstance(ingredient["ecoScore"], (int, float))
                assert ingredient["riskLevel"] in ["low", "moderate", "high"]
    
    @pytest.mark.e2e
    async def test_security_flow(self, sample_image):
        """
        Test security measures in the flow
        """
        async with httpx.AsyncClient() as client:
            # Test with malicious file
            malicious_content = b"<?php system($_GET['cmd']); ?>"
            
            response = await client.post(
                "http://localhost:8000/java-integration/analyze-image",
                files={"file": ("malicious.php", malicious_content, "application/x-php")},
                data={"user_need": "general safety"}
            )
            
            # Should reject malicious file
            assert response.status_code == 400
            
            # Test with oversized file
            oversized_content = b"x" * (6 * 1024 * 1024)  # 6MB
            
            response = await client.post(
                "http://localhost:8000/java-integration/analyze-image",
                files={"file": ("large.jpg", oversized_content, "image/jpeg")},
                data={"user_need": "general safety"}
            )
            
            # Should reject oversized file
            assert response.status_code == 413

