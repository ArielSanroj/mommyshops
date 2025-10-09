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

from database import canonicalize_ingredients
from ollama_integration import (
    ollama_integration, 
    analyze_ingredients_with_ollama,
    enhance_ocr_text_with_ollama,
    analyze_ingredient_safety_with_ollama
)

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
            
            if product_info.ingredients:
                product_info.ingredients = canonicalize_ingredients(product_info.ingredients)
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
        
        return canonicalize_ingredients(ingredients)
    
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
            # Try Ollama first if available
            if ollama_integration.is_available():
                logger.info("Trying Ollama for LLM analysis...")
                try:
                    # Convert image to base64
                    import base64
                    image_b64 = base64.b64encode(image_data).decode('utf-8')
                    
                    # Create prompt for Ollama
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
                    
                    # Use Ollama for analysis
                    ollama_result = await ollama_integration.analyze_ingredients([prompt])
                    if ollama_result.success and ollama_result.content:
                        if "No ingredients visible" not in ollama_result.content:
                            # Parse ingredients from response
                            ingredients = [ing.strip() for ing in ollama_result.content.split(',') if ing.strip()]
                            if ingredients:
                                logger.info(f"Ollama LLM extracted {len(ingredients)} ingredients")
                                return canonicalize_ingredients(ingredients)
                except Exception as e:
                    logger.warning(f"Ollama LLM analysis failed: {e}")
            
            # Fallback to OpenAI if available
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
                    return canonicalize_ingredients(ingredients)
                    
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
        
        return []
    
    def _extract_ingredients_from_text(self, text: str) -> List[str]:
        """Extract ingredients from text using pattern matching"""
        ingredients = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Skip common non-ingredient words
            skip_words = [
                'ingredients', 'ingrediente', 'ingredientes', 'ingredient',
                'analysis', 'assessment', 'safety', 'benefits', 'risks',
                'recommendations', 'alternatives', 'substitutes'
            ]
            
            line_lower = line.lower()
            if any(skip_word in line_lower for skip_word in skip_words):
                continue
            
            # Look for ingredient patterns
            if any(pattern in line_lower for pattern in [
                'acid', 'alcohol', 'oil', 'extract', 'vitamin', 'sodium',
                'glycerin', 'paraben', 'sulfate', 'oxide', 'ester',
                'cetyl', 'stearyl', 'myristyl', 'palmitate', 'stearate',
                'helianthus', 'hexanediol', 'cera', 'beeswax', 'polyglyceryl',
                'aqua', 'water', 'eau', 'butylene', 'propylene', 'glycol',
                'acrylate', 'copolymer', 'distearate', 'hydroxyethyl'
            ]):
                # Clean up the ingredient name
                ingredient = line.strip()
                # Remove common prefixes/suffixes
                ingredient = ingredient.replace('*', '').replace('•', '').replace('-', ' ').strip()
                # Remove numbers at the beginning (like "1. ", "2. ", etc.)
                if ingredient and ingredient[0].isdigit() and len(ingredient) > 2:
                    ingredient = ingredient.split('.', 1)[1].strip() if '.' in ingredient else ingredient[1:].strip()
                
                if ingredient and len(ingredient) > 2:
                    ingredients.append(ingredient)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_ingredients = []
        for ingredient in ingredients:
            if ingredient.lower() not in seen:
                seen.add(ingredient.lower())
                unique_ingredients.append(ingredient)
        
        return unique_ingredients
    
    async def _enhance_ocr_with_ollama(self, ocr_text: str) -> Optional[str]:
        """Enhance OCR text using Ollama for better ingredient extraction"""
        if not ollama_integration.is_available():
            return None
        
        try:
            ollama_result = await enhance_ocr_text_with_ollama(ocr_text)
            if ollama_result.success and ollama_result.content:
                logger.info("OCR text enhanced with Ollama")
                return ollama_result.content
            else:
                logger.warning(f"Ollama OCR enhancement failed: {ollama_result.error}")
                return None
        except Exception as e:
            logger.error(f"Error enhancing OCR with Ollama: {e}")
            return None
    
    async def _analyze_ingredients_with_ollama(self, ingredients: List[str], skin_type: str = "normal") -> Optional[Dict[str, Any]]:
        """Analyze ingredients using Ollama for detailed safety assessment"""
        if not ollama_integration.is_available():
            return None
        
        try:
            ollama_result = await analyze_ingredient_safety_with_ollama(ingredients, skin_type)
            if ollama_result.success and ollama_result.content:
                logger.info("Ingredient safety analysis completed with Ollama")
                return {
                    'content': ollama_result.content,
                    'model': ollama_result.model,
                    'skin_type': skin_type
                }
            else:
                logger.warning(f"Ollama safety analysis failed: {ollama_result.error}")
                return None
        except Exception as e:
            logger.error(f"Error analyzing ingredients with Ollama: {e}")
            return None
    
    async def _extract_ingredients_with_ocr(self, image_data: bytes) -> List[str]:
        """Fallback to traditional OCR for ingredient extraction"""
        try:
            # Import the existing OCR function
            from main import extract_ingredients_from_image
            ingredients = await extract_ingredients_from_image(image_data)
            
            # If OCR found ingredients, return them
            if ingredients:
                logger.info(f"OCR fallback found {len(ingredients)} ingredients")
                return canonicalize_ingredients(ingredients)
            
            # If OCR didn't find ingredients, try simple text extraction
            logger.info("OCR didn't find ingredients, trying simple text extraction...")
            image = Image.open(io.BytesIO(image_data))
            text = pytesseract.image_to_string(image, lang='eng+spa')
            
            # Try Ollama to improve OCR text if available
            if ollama_integration.is_available() and text.strip():
                try:
                    logger.info("Using Ollama to improve OCR text...")
                    enhanced_text = await self._enhance_ocr_with_ollama(text)
                    if enhanced_text:
                        # Parse ingredients from improved text
                        improved_ingredients = self._extract_ingredients_from_text(enhanced_text)
                        if improved_ingredients:
                            logger.info(f"Ollama improved OCR found {len(improved_ingredients)} ingredients")
                            return canonicalize_ingredients(improved_ingredients)
                except Exception as e:
                    logger.warning(f"Ollama OCR improvement failed: {e}")
            
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
            return canonicalize_ingredients(ingredients)
            
        except Exception as e:
            logger.error(f"OCR fallback failed: {e}")
            return []
    
    async def get_comprehensive_analysis(self, image_data: bytes, skin_type: str = "normal") -> Dict[str, Any]:
        """
        Get comprehensive product analysis combining all available methods with Ollama enhancement
        
        Args:
            image_data: Product image data
            skin_type: User's skin type for personalized analysis
            
        Returns:
            Comprehensive analysis results
        """
        try:
            logger.info("Starting comprehensive product analysis...")
            
            # Step 1: Extract basic product information
            product_info = await self.recognize_product(image_data)
            
            # Step 2: Extract ingredients using all available methods
            ingredients = []
            
            # Try OCR with Ollama enhancement
            if product_info.ingredients:
                ingredients = product_info.ingredients
                logger.info(f"Found {len(ingredients)} ingredients from product recognition")
            else:
                # Fallback to direct OCR
                ingredients = await self._extract_ingredients_with_ocr(image_data)
                logger.info(f"Found {len(ingredients)} ingredients from OCR")
            
            # Step 3: Enhance with Ollama analysis if available
            ollama_analysis = None
            if ingredients and ollama_integration.is_available():
                try:
                    ollama_analysis = await self._analyze_ingredients_with_ollama(ingredients, skin_type)
                    if ollama_analysis:
                        logger.info("Ollama safety analysis completed")
                except Exception as e:
                    logger.warning(f"Ollama analysis failed: {e}")
            
            # Step 4: Compile comprehensive results
            results = {
                'product_info': {
                    'brand': product_info.brand,
                    'product_name': product_info.product_name,
                    'product_type': product_info.product_type,
                    'confidence': product_info.confidence,
                    'source': product_info.source
                },
                'ingredients': {
                    'list': ingredients,
                    'count': len(ingredients),
                    'canonicalized': canonicalize_ingredients(ingredients)
                },
                'ollama_analysis': ollama_analysis,
                'analysis_metadata': {
                    'skin_type': skin_type,
                    'ollama_available': ollama_integration.is_available(),
                    'timestamp': asyncio.get_event_loop().time()
                }
            }
            
            logger.info(f"Comprehensive analysis completed: {len(ingredients)} ingredients, Ollama: {ollama_analysis is not None}")
            return results
            
        except Exception as e:
            logger.error(f"Comprehensive analysis failed: {e}")
            return {
                'error': str(e),
                'product_info': None,
                'ingredients': {'list': [], 'count': 0, 'canonicalized': []},
                'ollama_analysis': None,
                'analysis_metadata': {
                    'skin_type': skin_type,
                    'ollama_available': False,
                    'timestamp': asyncio.get_event_loop().time()
                }
            }

# Global instance
product_recognizer = ProductRecognitionEngine()