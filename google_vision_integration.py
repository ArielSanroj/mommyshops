"""
Google Cloud Vision Integration for MommyShops
Enhanced OCR for cosmetic ingredient extraction using Google Vision API
"""

import os
import base64
import logging
import asyncio
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import httpx

load_dotenv()
logger = logging.getLogger(__name__)

class GoogleVisionOCR:
    """Google Cloud Vision OCR integration for cosmetic ingredient extraction."""
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_VISION_API_KEY')
        self.base_url = "https://vision.googleapis.com/v1/images:annotate"
        
        if not self.api_key:
            logger.warning("GOOGLE_VISION_API_KEY not found in environment variables")
    
    async def extract_text_from_image(self, image_data: bytes) -> List[str]:
        """
        Extract text from image using Google Cloud Vision API
        
        Args:
            image_data: Image bytes
            
        Returns:
            List of extracted text lines
        """
        if not self.api_key:
            logger.error("Google Vision API key not configured")
            return []
        
        try:
            logger.info("Starting Google Vision OCR extraction...")
            
            # Convert image to base64
            img_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare request
            request_data = {
                "requests": [
                    {
                        "image": {
                            "content": img_base64
                        },
                        "features": [
                            {
                                "type": "TEXT_DETECTION",
                                "maxResults": 50
                            }
                        ]
                    }
                ]
            }
            
            url = f"{self.base_url}?key={self.api_key}"
            headers = {
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=request_data, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if 'responses' in result and result['responses']:
                        text_annotations = result['responses'][0].get('textAnnotations', [])
                        
                        if text_annotations:
                            # Get the full text description
                            full_text = text_annotations[0].get('description', '')
                            logger.info(f"Google Vision extracted {len(full_text)} characters")
                            
                            # Split into lines and clean
                            lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                            
                            # Extract ingredients from the text
                            ingredients = self._extract_ingredients_from_text(lines)
                            
                            logger.info(f"Extracted {len(ingredients)} ingredients using Google Vision")
                            return ingredients
                        else:
                            logger.warning("No text detected by Google Vision")
                            return []
                    else:
                        logger.warning("Empty response from Google Vision API")
                        return []
                else:
                    logger.error(f"Google Vision API error {response.status_code}: {response.text[:200]}")
                    return []
                    
        except Exception as e:
            logger.error(f"Google Vision OCR failed: {e}")
            return []
    
    def _extract_ingredients_from_text(self, text_lines: List[str]) -> List[str]:
        """
        Extract cosmetic ingredients from text lines
        
        Args:
            text_lines: List of text lines from OCR
            
        Returns:
            List of extracted ingredients
        """
        ingredients = []
        
        # Common cosmetic ingredient patterns
        ingredient_indicators = [
            'ingredients:', 'ingredientes:', 'composition:', 'composición:',
            'active ingredients:', 'ingredientes activos:', 'contains:',
            'may contain:', 'puede contener:'
        ]
        
        # Find the ingredients section
        ingredients_section = []
        found_section = False
        
        for line in text_lines:
            line_lower = line.lower()
            
            # Check if this line indicates start of ingredients
            if any(indicator in line_lower for indicator in ingredient_indicators):
                found_section = True
                # Extract ingredients from this line too
                ingredients_section.append(line)
                continue
            
            # If we're in the ingredients section
            if found_section:
                # Stop if we hit common non-ingredient sections
                stop_indicators = [
                    'directions:', 'instrucciones:', 'warnings:', 'advertencias:',
                    'net weight:', 'peso neto:', 'made in:', 'hecho en:',
                    'expires:', 'vence:', 'batch:', 'lote:'
                ]
                
                if any(indicator in line_lower for indicator in stop_indicators):
                    break
                
                ingredients_section.append(line)
        
        # If no specific section found, use all text
        if not ingredients_section:
            ingredients_section = text_lines
        
        # Extract individual ingredients
        for line in ingredients_section:
            # Split by common separators
            potential_ingredients = []
            
            # Split by comma, semicolon, or newline
            for separator in [',', ';', '\n']:
                if separator in line:
                    potential_ingredients.extend([ing.strip() for ing in line.split(separator)])
                    break
            else:
                # If no separator found, use the whole line
                potential_ingredients.append(line.strip())
            
            # Clean and validate ingredients
            for ingredient in potential_ingredients:
                ingredient = ingredient.strip()
                
                # Skip empty or very short ingredients
                if len(ingredient) < 2:
                    continue
                
                # Skip common non-ingredient words
                skip_words = [
                    'ingredients', 'ingredientes', 'composition', 'composición',
                    'active', 'activos', 'contains', 'contiene', 'may contain',
                    'puede contener', 'water', 'aqua', 'eau'
                ]
                
                if ingredient.lower() in skip_words:
                    continue
                
                # Skip ingredients that are too long (likely not individual ingredients)
                if len(ingredient) > 100:
                    continue
                
                # Skip ingredients that look like instructions
                instruction_words = ['apply', 'aplicar', 'use', 'usar', 'avoid', 'evitar']
                if any(word in ingredient.lower() for word in instruction_words):
                    continue
                
                ingredients.append(ingredient)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_ingredients = []
        for ingredient in ingredients:
            if ingredient.lower() not in seen:
                seen.add(ingredient.lower())
                unique_ingredients.append(ingredient)
        
        return unique_ingredients[:50]  # Limit to 50 ingredients
    
    async def analyze_ingredient_safety(self, ingredients: List[str], user_conditions: List[str] = None) -> Dict[str, Any]:
        """
        Analyze ingredient safety using Google Vision API (placeholder for future enhancement)
        
        Args:
            ingredients: List of ingredients to analyze
            user_conditions: User's skin conditions
            
        Returns:
            Analysis results
        """
        # This is a placeholder for future enhancement
        # For now, return basic analysis
        analysis = {
            "total_ingredients": len(ingredients),
            "ingredients": ingredients,
            "safety_notes": [],
            "recommendations": []
        }
        
        # Basic safety analysis
        known_sensitive_ingredients = [
            'sodium lauryl sulfate', 'sls', 'parabens', 'formaldehyde',
            'sulfates', 'fragrance', 'perfume', 'alcohol', 'retinol'
        ]
        
        for ingredient in ingredients:
            ingredient_lower = ingredient.lower()
            for sensitive in known_sensitive_ingredients:
                if sensitive in ingredient_lower:
                    analysis["safety_notes"].append(f"⚠️ {ingredient} may cause sensitivity")
        
        if not analysis["safety_notes"]:
            analysis["safety_notes"].append("✅ No obviously problematic ingredients detected")
        
        return analysis

# Global instance
google_vision_ocr = GoogleVisionOCR()

async def extract_ingredients_with_google_vision(image_data: bytes) -> List[str]:
    """
    Convenience function to extract ingredients using Google Vision
    
    Args:
        image_data: Image bytes
        
    Returns:
        List of extracted ingredients
    """
    return await google_vision_ocr.extract_text_from_image(image_data)

async def analyze_ingredients_with_google_vision(ingredients: List[str], user_conditions: List[str] = None) -> Dict[str, Any]:
    """
    Convenience function to analyze ingredients using Google Vision
    
    Args:
        ingredients: List of ingredients
        user_conditions: User's skin conditions
        
    Returns:
        Analysis results
    """
    return await google_vision_ocr.analyze_ingredient_safety(ingredients, user_conditions)