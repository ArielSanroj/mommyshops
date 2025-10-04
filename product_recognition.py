"""
Enhanced Product Recognition System for MommyShops
Handles product photos (not just ingredient labels) by detecting brands, product names,
and looking up ingredients from databases and APIs.
"""

import asyncio
import io
import re
import logging
from typing import List, Dict, Optional, Tuple
from PIL import Image
import pytesseract
import httpx
from bs4 import BeautifulSoup
import json
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ProductInfo:
    """Product information extracted from image or API"""
    brand: Optional[str] = None
    product_name: Optional[str] = None
    product_type: Optional[str] = None  # shampoo, cream, etc.
    ingredients: List[str] = None
    confidence: float = 0.0
    source: str = "unknown"  # ocr, api, llm

class ProductRecognitionEngine:
    """Enhanced product recognition system"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.nvidia_api_key = os.getenv("NVIDIA_API_KEY")
        
        # Known cosmetic brands for better recognition
        self.known_brands = [
            "l'oreal", "maybelline", "revlon", "covergirl", "neutrogena", "olay",
            "dove", "nivea", "vaseline", "johnson", "johnson's", "avon", "mary kay",
            "clinique", "estee lauder", "lancome", "chanel", "dior", "ysl",
            "mac", "urban decay", "too faced", "fenty", "glossier", "rare beauty",
            "cerave", "la roche posay", "vichy", "eucerin", "aveeno", "cetaphil",
            "isdin", "sesderma", "martiderm", "endocare", "helena rubinstein",
            "biotherm", "kiehl's", "fresh", "origins", "clinique", "shiseido",
            "sk-ii", "laneige", "innisfree", "the ordinary", "paula's choice"
        ]
        
        # Product type keywords
        self.product_types = [
            "shampoo", "conditioner", "cream", "lotion", "serum", "cleanser",
            "toner", "moisturizer", "sunscreen", "foundation", "concealer",
            "lipstick", "mascara", "eyeshadow", "blush", "bronzer", "primer",
            "mask", "scrub", "exfoliant", "gel", "oil", "balm", "stick"
        ]
    
    async def analyze_product_image(self, image_data: bytes) -> ProductInfo:
        """
        Main function to analyze product images and extract ingredient information
        """
        try:
            logger.info("Starting enhanced product recognition...")
            
            # Step 1: Extract text from image (brand, product name)
            product_info = await self._extract_product_info_from_image(image_data)
            
            # Step 2: If we have brand/product info, try to find ingredients from APIs
            if product_info.brand or product_info.product_name:
                logger.info(f"Found product info: {product_info.brand} - {product_info.product_name}")
                
                # Try multiple sources for ingredient lookup
                ingredients = await self._lookup_ingredients_from_sources(product_info)
                
                if ingredients:
                    product_info.ingredients = ingredients
                    product_info.source = "api_lookup"
                    logger.info(f"Found {len(ingredients)} ingredients from API lookup")
                else:
                    # Fallback to LLM analysis
                    logger.info("No ingredients found from APIs, trying LLM analysis...")
                    ingredients = await self._extract_ingredients_with_llm(image_data, product_info)
                    if ingredients:
                        product_info.ingredients = ingredients
                        product_info.source = "llm_analysis"
            
            # Step 3: Always try OCR as a backup and compare results
            logger.info("Trying OCR extraction as backup...")
            ocr_ingredients = await self._extract_ingredients_with_ocr(image_data)
            
            if ocr_ingredients:
                # Check if OCR found better ingredients (more cosmetic-specific)
                cosmetic_keywords = ['water', 'glycerin', 'alcohol', 'acid', 'sodium', 'citric', 'phenoxyethanol', 'betaine']
                ocr_cosmetic_count = sum(1 for ing in ocr_ingredients if any(keyword in ing.lower() for keyword in cosmetic_keywords))
                
                if ocr_cosmetic_count > 0:
                    logger.info(f"OCR found {ocr_cosmetic_count} cosmetic ingredients, using OCR results")
                    product_info.ingredients = ocr_ingredients
                    product_info.source = "ocr_extraction"
                elif not product_info.ingredients:
                    # Use OCR as fallback if no other ingredients found
                    product_info.ingredients = ocr_ingredients
                    product_info.source = "ocr_fallback"
            
            return product_info
            
        except Exception as e:
            logger.error(f"Error in product recognition: {e}")
            return ProductInfo()
    
    async def _extract_product_info_from_image(self, image_data: bytes) -> ProductInfo:
        """Extract brand and product name from image using OCR"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Use OCR to extract text
            text = pytesseract.image_to_string(image, lang='eng+spa')
            logger.info(f"OCR extracted text: {text[:200]}...")
            
            # Parse brand and product name
            brand, product_name, product_type = self._parse_product_info(text)
            
            return ProductInfo(
                brand=brand,
                product_name=product_name,
                product_type=product_type,
                confidence=0.8 if brand else 0.3
            )
            
        except Exception as e:
            logger.error(f"Error extracting product info: {e}")
            return ProductInfo()
    
    def _parse_product_info(self, text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse brand, product name, and product type from OCR text"""
        text_lower = text.lower()
        
        # Find brand
        brand = None
        for known_brand in self.known_brands:
            if known_brand in text_lower:
                brand = known_brand.title()
                break
        
        # Find product type
        product_type = None
        for ptype in self.product_types:
            if ptype in text_lower:
                product_type = ptype
                break
        
        # Extract product name (usually the largest text or first line)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        product_name = None
        
        if lines:
            # Look for lines that might be product names
            for line in lines:
                if len(line) > 5 and len(line) < 50:  # Reasonable length for product name
                    if not any(word in line.lower() for word in ['ingredients', 'directions', 'warning', 'caution']):
                        product_name = line
                        break
        
        return brand, product_name, product_type
    
    async def _lookup_ingredients_from_sources(self, product_info: ProductInfo) -> List[str]:
        """Look up ingredients from various sources"""
        ingredients = []
        
        # Try multiple lookup strategies
        lookup_methods = [
            self._lookup_from_incidecoder,
            self._lookup_from_cosdna,
            self._lookup_from_ewg,
            self._lookup_from_brand_website,
            self._lookup_from_google_search
        ]
        
        for method in lookup_methods:
            try:
                result = await method(product_info)
                if result:
                    ingredients.extend(result)
                    logger.info(f"Found {len(result)} ingredients from {method.__name__}")
                    break  # Use first successful result
            except Exception as e:
                logger.warning(f"Lookup method {method.__name__} failed: {e}")
                continue
        
        return list(set(ingredients))  # Remove duplicates
    
    async def _lookup_from_incidecoder(self, product_info: ProductInfo) -> List[str]:
        """Look up ingredients from INCI Decoder"""
        if not product_info.brand or not product_info.product_name:
            return []
        
        try:
            # Search INCI Decoder
            search_query = f"{product_info.brand} {product_info.product_name}"
            url = f"https://incidecoder.com/search?query={search_query}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for ingredient lists
                    ingredients = []
                    ingredient_elements = soup.find_all(['div', 'span'], class_=re.compile(r'ingredient'))
                    
                    for element in ingredient_elements:
                        text = element.get_text().strip()
                        if text and len(text) > 3:
                            ingredients.append(text)
                    
                    return ingredients
                    
        except Exception as e:
            logger.warning(f"INCI Decoder lookup failed: {e}")
        
        return []
    
    async def _lookup_from_cosdna(self, product_info: ProductInfo) -> List[str]:
        """Look up ingredients from COSDNA"""
        if not product_info.brand or not product_info.product_name:
            return []
        
        try:
            # Search COSDNA
            search_query = f"{product_info.brand} {product_info.product_name}"
            url = f"https://www.cosdna.com/eng/search.php?q={search_query}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for ingredient lists
                    ingredients = []
                    tables = soup.find_all('table')
                    
                    for table in tables:
                        rows = table.find_all('tr')
                        for row in rows:
                            cells = row.find_all('td')
                            if len(cells) >= 2:
                                ingredient = cells[0].get_text().strip()
                                if ingredient and len(ingredient) > 3:
                                    ingredients.append(ingredient)
                    
                    return ingredients
                    
        except Exception as e:
            logger.warning(f"COSDNA lookup failed: {e}")
        
        return []
    
    async def _lookup_from_ewg(self, product_info: ProductInfo) -> List[str]:
        """Look up ingredients from EWG Skin Deep"""
        if not product_info.brand or not product_info.product_name:
            return []
        
        try:
            # Search EWG Skin Deep
            search_query = f"{product_info.brand} {product_info.product_name}"
            url = f"https://www.ewg.org/skindeep/search/?query={search_query}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for ingredient lists
                    ingredients = []
                    ingredient_sections = soup.find_all(['div', 'section'], class_=re.compile(r'ingredient'))
                    
                    for section in ingredient_sections:
                        text = section.get_text()
                        # Extract ingredients from text
                        ingredient_matches = re.findall(r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b', text)
                        ingredients.extend(ingredient_matches)
                    
                    return ingredients
                    
        except Exception as e:
            logger.warning(f"EWG lookup failed: {e}")
        
        return []
    
    async def _lookup_from_brand_website(self, product_info: ProductInfo) -> List[str]:
        """Look up ingredients from brand's official website"""
        if not product_info.brand:
            return []
        
        try:
            # Try to find the brand's website
            brand_websites = {
                "l'oreal": "https://www.loreal.com",
                "maybelline": "https://www.maybelline.com",
                "neutrogena": "https://www.neutrogena.com",
                "dove": "https://www.dove.com",
                "nivea": "https://www.nivea.com",
                "cerave": "https://www.cerave.com",
                "isdin": "https://www.isdin.com"
            }
            
            website = brand_websites.get(product_info.brand.lower())
            if not website:
                return []
            
            # Search for the product on the brand website
            search_url = f"{website}/search?q={product_info.product_name}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(search_url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for ingredient information
                    ingredients = []
                    ingredient_elements = soup.find_all(['div', 'span'], string=re.compile(r'ingredients?', re.I))
                    
                    for element in ingredient_elements:
                        parent = element.parent
                        if parent:
                            text = parent.get_text()
                            # Extract ingredients from text
                            ingredient_matches = re.findall(r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b', text)
                            ingredients.extend(ingredient_matches)
                    
                    return ingredients
                    
        except Exception as e:
            logger.warning(f"Brand website lookup failed: {e}")
        
        return []
    
    async def _lookup_from_google_search(self, product_info: ProductInfo) -> List[str]:
        """Look up ingredients using Google search"""
        if not product_info.brand or not product_info.product_name:
            return []
        
        try:
            # Search for ingredients using Google
            search_query = f'"{product_info.brand}" "{product_info.product_name}" ingredients list'
            
            # Use a simple web search (you might want to use Google Custom Search API)
            url = f"https://www.google.com/search?q={search_query}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract text from search results
                    text = soup.get_text()
                    
                    # Look for ingredient patterns - more specific to cosmetic ingredients
                    ingredients = []
                    
                    # Known cosmetic ingredient patterns
                    cosmetic_patterns = [
                        r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*(?:\s*/\s*[A-Z0-9-]+)*\b',
                        r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
                    ]
                    
                    # Filter out common non-ingredient words
                    exclude_words = {
                        'google', 'search', 'results', 'website', 'page', 'click', 'here', 'more',
                        'ingredients', 'list', 'contains', 'may', 'contain', 'product', 'formula',
                        'directions', 'usage', 'warning', 'caution', 'keep', 'away', 'children',
                        'if', 'you', 'have', 'questions', 'contact', 'customer', 'service'
                    }
                    
                    for pattern in cosmetic_patterns:
                        matches = re.findall(pattern, text)
                        for match in matches:
                            match_lower = match.lower()
                            # Filter out common words and very short matches
                            if (len(match) > 3 and 
                                match_lower not in exclude_words and
                                not match_lower.isdigit() and
                                not any(word in match_lower for word in ['http', 'www', 'com', 'org'])):
                                ingredients.append(match)
                    
                    # Remove duplicates and limit results
                    unique_ingredients = list(dict.fromkeys(ingredients))  # Preserve order while removing duplicates
                    return unique_ingredients[:15]  # Limit to first 15 matches
                    
        except Exception as e:
            logger.warning(f"Google search lookup failed: {e}")
        
        return []
    
    async def _extract_ingredients_with_llm(self, image_data: bytes, product_info: ProductInfo) -> List[str]:
        """Use LLM to analyze the image and extract ingredients"""
        try:
            if not self.openai_api_key:
                logger.warning("OpenAI API key not available for LLM analysis")
                return []
            
            # Convert image to base64
            import base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            # Create prompt for LLM
            prompt = f"""
            Analyze this cosmetic product image and extract the ingredient list.
            
            Product Information:
            - Brand: {product_info.brand or 'Unknown'}
            - Product Name: {product_info.product_name or 'Unknown'}
            - Product Type: {product_info.product_type or 'Unknown'}
            
            Please identify and list all cosmetic ingredients visible in the image.
            Return only a comma-separated list of ingredient names in INCI format.
            If you cannot see ingredients clearly, return "No ingredients visible".
            """
            
            # Use OpenAI Vision API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4-vision-preview",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{image_b64}"
                                        }
                                    }
                                ]
                            }
                        ],
                        "max_tokens": 500
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content']
                    
                    if "No ingredients visible" in content:
                        return []
                    
                    # Parse ingredients from response
                    ingredients = [ing.strip() for ing in content.split(',') if ing.strip()]
                    return ingredients
                    
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
        
        return []
    
    async def _extract_ingredients_with_ocr(self, image_data: bytes) -> List[str]:
        """Fallback to traditional OCR for ingredient extraction"""
        try:
            # Import the existing OCR function
            from main import extract_ingredients_from_image
            ingredients = await extract_ingredients_from_image(image_data)
            
            # If OCR found ingredients, return them
            if ingredients:
                logger.info(f"OCR fallback found {len(ingredients)} ingredients")
                return ingredients
            
            # If OCR didn't find ingredients, try simple text extraction
            logger.info("OCR didn't find ingredients, trying simple text extraction...")
            image = Image.open(io.BytesIO(image_data))
            text = pytesseract.image_to_string(image, lang='eng+spa')
            
            # Look for ingredient patterns in the text
            ingredients = []
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                if 'ingredients' in line.lower() or any(word in line.lower() for word in ['water', 'glycerin', 'alcohol', 'acid', 'sodium', 'citric']):
                    # This line might contain ingredients
                    # Split by common separators
                    potential_ingredients = re.split(r'[,;]', line)
                    for ing in potential_ingredients:
                        ing = ing.strip()
                        # Better filtering for cosmetic ingredients
                        if (len(ing) > 3 and 
                            not ing.lower() in ['ingredients', 'list', 'contains', 'directions', 'usage'] and
                            not ing.endswith(':') and  # Remove labels like "INGREDIENTS:"
                            any(char.isalpha() for char in ing)):  # Must contain letters
                            ingredients.append(ing)
            
            logger.info(f"Simple text extraction found {len(ingredients)} ingredients: {ingredients}")
            return ingredients
            
        except Exception as e:
            logger.error(f"OCR fallback failed: {e}")
            return []

# Global instance
product_recognizer = ProductRecognitionEngine()