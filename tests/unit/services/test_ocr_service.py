"""
Unit tests for OCR service
"""

import pytest
from unittest.mock import Mock, patch
import pytest_asyncio
from backend_python.services.ocr_service import OCRService

class TestOCRService:
    """Test OCR service functionality"""
    
    @pytest.fixture
    def ocr_service(self):
        """Create OCR service instance"""
        return OCRService()
    
    @pytest.mark.unit
    @pytest.mark.ocr
    def test_ocr_service_initialization(self, ocr_service):
        """Test OCR service initialization"""
        assert ocr_service is not None
    
    @pytest.mark.unit
    @pytest.mark.ocr
    @patch('backend_python.services.ocr_service.pytesseract')
    def test_extract_text_success(self, mock_pytesseract, ocr_service):
        """Test successful text extraction"""
        # Mock pytesseract
        mock_pytesseract.image_to_string.return_value = "Aqua, Glycerin, Hyaluronic Acid"
        
        result = ocr_service.extract_text("test_image.jpg")
        
        assert result == "Aqua, Glycerin, Hyaluronic Acid"
        mock_pytesseract.image_to_string.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.ocr
    @patch('backend_python.services.ocr_service.pytesseract')
    def test_extract_text_failure(self, mock_pytesseract, ocr_service):
        """Test text extraction failure"""
        # Mock pytesseract to raise exception
        mock_pytesseract.image_to_string.side_effect = Exception("OCR failed")
        
        result = ocr_service.extract_text("test_image.jpg")
        
        assert result == ""
    
    @pytest.mark.unit
    @pytest.mark.ocr
    @patch('backend_python.services.ocr_service.pytesseract')
    def test_extract_text_with_config(self, mock_pytesseract, ocr_service):
        """Test text extraction with custom config"""
        mock_pytesseract.image_to_string.return_value = "Test text"
        
        result = ocr_service.extract_text("test_image.jpg", config="--psm 6")
        
        assert result == "Test text"
        mock_pytesseract.image_to_string.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.ocr
    @patch('backend_python.services.ocr_service.pytesseract')
    def test_get_confidence_scores(self, mock_pytesseract, ocr_service):
        """Test confidence score extraction"""
        # Mock pytesseract data
        mock_data = {
            'text': 'Aqua, Glycerin',
            'conf': [95, 87]
        }
        mock_pytesseract.image_to_data.return_value = mock_data
        
        result = ocr_service.get_confidence_scores("test_image.jpg")
        
        assert result == mock_data
        mock_pytesseract.image_to_data.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.ocr
    def test_preprocess_image(self, ocr_service):
        """Test image preprocessing"""
        # This would test image preprocessing logic
        # For now, just test that method exists
        assert hasattr(ocr_service, 'preprocess_image')
    
    @pytest.mark.unit
    @pytest.mark.ocr
    def test_validate_image_file(self, ocr_service):
        """Test image file validation"""
        # Test valid image
        assert ocr_service.validate_image_file("test.jpg") == True
        assert ocr_service.validate_image_file("test.png") == True
        assert ocr_service.validate_image_file("test.webp") == True
        
        # Test invalid image
        assert ocr_service.validate_image_file("test.txt") == False
        assert ocr_service.validate_image_file("test.pdf") == False
    
    @pytest.mark.unit
    @pytest.mark.ocr
    def test_extract_ingredients_from_text(self, ocr_service):
        """Test ingredient extraction from text"""
        text = "Aqua, Glycerin, Hyaluronic Acid, Niacinamide"
        
        ingredients = ocr_service.extract_ingredients_from_text(text)
        
        expected = ["Aqua", "Glycerin", "Hyaluronic Acid", "Niacinamide"]
        assert ingredients == expected
    
    @pytest.mark.unit
    @pytest.mark.ocr
    def test_extract_ingredients_empty_text(self, ocr_service):
        """Test ingredient extraction from empty text"""
        text = ""
        
        ingredients = ocr_service.extract_ingredients_from_text(text)
        
        assert ingredients == []
    
    @pytest.mark.unit
    @pytest.mark.ocr
    def test_extract_ingredients_single_ingredient(self, ocr_service):
        """Test ingredient extraction from single ingredient"""
        text = "Aqua"
        
        ingredients = ocr_service.extract_ingredients_from_text(text)
        
        assert ingredients == ["Aqua"]
    
    @pytest.mark.unit
    @pytest.mark.ocr
    def test_extract_ingredients_with_numbers(self, ocr_service):
        """Test ingredient extraction with numbers"""
        text = "Aqua, Glycerin 5%, Hyaluronic Acid 1%, Niacinamide 4%"
        
        ingredients = ocr_service.extract_ingredients_from_text(text)
        
        expected = ["Aqua", "Glycerin", "Hyaluronic Acid", "Niacinamide"]
        assert ingredients == expected
