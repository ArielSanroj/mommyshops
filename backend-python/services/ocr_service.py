"""
OCR Service for MommyShops API
Handles image text extraction using Tesseract and Google Vision
"""

import logging
import time
from typing import Optional, Dict, Any, List
import pytesseract
from PIL import Image
import io
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..core.config import get_settings

logger = logging.getLogger(__name__)

class OCRService:
    """
    Service for optical character recognition
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    async def extract_text_from_image(self, image_data: bytes) -> Optional[str]:
        """
        Extract text from image using Tesseract OCR
        """
        try:
            # Run OCR in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                self.executor, 
                self._extract_text_sync, 
                image_data
            )
            
            if text and text.strip():
                logger.info(f"OCR extracted {len(text)} characters")
                return text.strip()
            else:
                logger.warning("OCR did not extract any text")
                return None
                
        except Exception as e:
            logger.error(f"Error in OCR extraction: {e}")
            return None
    
    def _extract_text_sync(self, image_data: bytes) -> str:
        """
        Synchronous OCR extraction
        """
        try:
            # Load image from bytes
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(
                image,
                lang='eng+spa',  # English and Spanish
                config='--psm 6'  # Assume uniform block of text
            )
            
            return text
            
        except Exception as e:
            logger.error(f"Error in synchronous OCR: {e}")
            return ""
    
    async def extract_text_with_google_vision(self, image_data: bytes) -> Optional[str]:
        """
        Extract text using Google Vision API (if available)
        """
        try:
            # This would integrate with Google Vision API
            # For now, fallback to Tesseract
            return await self.extract_text_from_image(image_data)
            
        except Exception as e:
            logger.error(f"Error in Google Vision OCR: {e}")
            return None
    
    async def enhance_text_with_ollama(self, text: str) -> Optional[str]:
        """
        Enhance extracted text using Ollama AI
        """
        try:
            # This would integrate with Ollama for text enhancement
            # For now, return original text
            return text
            
        except Exception as e:
            logger.error(f"Error in Ollama text enhancement: {e}")
            return text
    
    async def extract_ingredients_from_text(self, text: str) -> List[str]:
        """
        Extract ingredient list from OCR text
        """
        try:
            # Simple ingredient extraction logic
            # This would be more sophisticated in production
            ingredients = []
            
            # Look for common ingredient patterns
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if line and len(line) > 2:
                    # Check if line contains ingredient-like text
                    if any(keyword in line.lower() for keyword in [
                        'ingredients', 'ingredientes', 'composition', 'composición'
                    ]):
                        # Extract ingredients from this line
                        parts = line.split(',')
                        for part in parts:
                            ingredient = part.strip()
                            if ingredient and len(ingredient) > 2:
                                ingredients.append(ingredient)
            
            logger.info(f"Extracted {len(ingredients)} ingredients from text")
            return ingredients
            
        except Exception as e:
            logger.error(f"Error extracting ingredients: {e}")
            return []
    
    async def get_ocr_confidence(self, image_data: bytes) -> float:
        """
        Get confidence score for OCR extraction
        """
        try:
            # This would calculate confidence based on OCR results
            # For now, return a default value
            return 0.8
            
        except Exception as e:
            logger.error(f"Error calculating OCR confidence: {e}")
            return 0.0

