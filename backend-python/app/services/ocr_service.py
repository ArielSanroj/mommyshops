"""
OCR Service
Handles text extraction from images
"""

import pytesseract
from PIL import Image
import logging
import io
from typing import Optional

logger = logging.getLogger(__name__)

class OCRService:
    """Service for OCR text extraction"""
    
    def __init__(self):
        self.logger = logger
    
    async def extract_text_from_image(self, image_content: bytes) -> Optional[str]:
        """Extract text from image content"""
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_content))
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(image)
            
            self.logger.info(f"OCR extracted {len(text)} characters")
            return text.strip() if text else None
            
        except Exception as e:
            self.logger.error(f"OCR extraction failed: {e}")
            return None
