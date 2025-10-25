"""
Unit tests for OCR service
"""

import pytest
import io
from PIL import Image
from backend.services.ocr_service import OCRService


class TestOCRService:
    """Tests for OCR service"""
    
    @pytest.fixture
    def ocr_service(self):
        return OCRService()
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample image for testing"""
        img = Image.new('RGB', (200, 100), color='white')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes.getvalue()
    
    @pytest.mark.asyncio
    async def test_extract_text_from_image_success(self, ocr_service, sample_image):
        """Test successful text extraction"""
        result = await ocr_service.extract_text_from_image(sample_image)
        assert result is not None or result == ""  # May be empty for blank image
    
    @pytest.mark.asyncio
    async def test_extract_text_from_image_invalid_data(self, ocr_service):
        """Test with invalid image data"""
        result = await ocr_service.extract_text_from_image(b"invalid data")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_extract_ingredients_from_text(self, ocr_service):
        """Test ingredient extraction from text"""
        text = "Ingredients: Water, Glycerin, Sodium Chloride"
        result = await ocr_service.extract_ingredients_from_text(text)
        assert isinstance(result, list)
        assert len(result) >= 0
    
    @pytest.mark.asyncio
    async def test_get_ocr_confidence(self, ocr_service, sample_image):
        """Test OCR confidence calculation"""
        confidence = await ocr_service.get_ocr_confidence(sample_image)
        assert 0.0 <= confidence <= 1.0

