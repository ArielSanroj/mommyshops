"""
INCI Beauty Database Scraper
Comprehensive scraper for INCI Beauty database with authentication support
"""

import asyncio
import httpx
import logging
import json
import os
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

@dataclass
class INCIBeautyIngredient:
    """Standardized INCI Beauty ingredient data."""
    name: str
    inci_name: str
    cas_number: Optional[str] = None
    eco_score: Optional[float] = None
    risk_level: Optional[str] = None
    benefits: Optional[str] = None
    risks_detailed: Optional[str] = None
    function: Optional[str] = None
    origin: Optional[str] = None
    concerns: Optional[str] = None
    restrictions: Optional[str] = None
    sources: str = "INCI Beauty Database"

class INCIBeautyDatabaseScraper:
    def __init__(self):
        self.base_url = "https://open.incibeauty.com"
        self.api_url = "https://api.incibeauty.com"
        self.username = os.getenv("INCI_BEAUTY_USERNAME")
        self.password = os.getenv("INCI_BEAUTY_PASSWORD")
        self.api_key = os.getenv("INCI_BEAUTY_API_KEY")
        self.session = None
        self.rate_limit_delay = 2  # seconds between requests
        
    async def __aenter__(self):
        headers = {
            'User-Agent': 'Mommyshops/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        self.session = httpx.AsyncClient(
            timeout=60.0,
            headers=headers,
            follow_redirects=True
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    async def authenticate(self) -> bool:
        """Authenticate with INCI Beauty if credentials are provided."""
        if not self.username or not self.password:
            logger.warning("INCI Beauty credentials not provided")
            return False
        
        try:
            login_data = {
                "username": self.username,
                "password": self.password
            }
            
            response = await self.session.post(
                f"{self.base_url}/login",
                json=login_data
            )
            
            if response.status_code == 200:
                logger.info("Successfully authenticated with INCI Beauty")
                return True
            else:
                logger.warning(f"Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    async def scrape_database_page(self, page_url: str) -> List[INCIBeautyIngredient]:
        """Scrape a specific database page."""
        try:
            await asyncio.sleep(self.rate_limit_delay)
            
            response = await self.session.get(page_url)
            
            if response.status_code == 200:
                return self._parse_database_page(response.text, page_url)
            elif response.status_code == 302:
                logger.warning(f"Redirected from {page_url} - authentication may be required")
                return []
            else:
                logger.warning(f"Failed to access {page_url}: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error scraping {page_url}: {e}")
            return []
    
    def _parse_database_page(self, html_content: str, page_url: str) -> List[INCIBeautyIngredient]:
        """Parse HTML content from a database page."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            ingredients = []
            
            # Look for ingredient data in various formats
            # Method 1: Look for tables with ingredient data
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:  # Skip header
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        ingredient = self._extract_ingredient_from_row(cells)
                        if ingredient:
                            ingredients.append(ingredient)
            
            # Method 2: Look for ingredient cards or divs
            ingredient_cards = soup.find_all(['div', 'section'], class_=re.compile(r'ingredient|card|item', re.I))
            for card in ingredient_cards:
                ingredient = self._extract_ingredient_from_card(card)
                if ingredient:
                    ingredients.append(ingredient)
            
            # Method 3: Look for JSON data in scripts
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'ingredient' in script.string.lower():
                    json_ingredients = self._extract_ingredients_from_script(script.string)
                    ingredients.extend(json_ingredients)
            
            logger.info(f"Extracted {len(ingredients)} ingredients from {page_url}")
            return ingredients
            
        except Exception as e:
            logger.error(f"Error parsing database page: {e}")
            return []
    
    def _extract_ingredient_from_row(self, cells: List) -> Optional[INCIBeautyIngredient]:
        """Extract ingredient data from a table row."""
        try:
            if len(cells) < 2:
                return None
            
            name = cells[0].get_text().strip()
            if not name or len(name) < 2:
                return None
            
            # Extract additional data from other cells
            inci_name = name
            cas_number = None
            eco_score = None
            function = None
            
            for i, cell in enumerate(cells[1:], 1):
                text = cell.get_text().strip()
                if not text:
                    continue
                
                # Try to identify CAS numbers
                if re.match(r'^\d+-\d+-\d+$', text):
                    cas_number = text
                # Try to identify scores
                elif re.match(r'^\d+(\.\d+)?$', text) and '.' in text:
                    try:
                        eco_score = float(text)
                    except ValueError:
                        pass
                # Try to identify functions
                elif any(word in text.lower() for word in ['emulsifier', 'surfactant', 'preservative', 'moisturizer']):
                    function = text
            
            return INCIBeautyIngredient(
                name=name,
                inci_name=inci_name,
                cas_number=cas_number,
                eco_score=eco_score,
                function=function
            )
            
        except Exception as e:
            logger.error(f"Error extracting ingredient from row: {e}")
            return None
    
    def _extract_ingredient_from_card(self, card) -> Optional[INCIBeautyIngredient]:
        """Extract ingredient data from a card element."""
        try:
            # Look for name/title
            name_element = card.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b'])
            if not name_element:
                name_element = card.find(class_=re.compile(r'title|name|heading', re.I))
            
            if not name_element:
                return None
            
            name = name_element.get_text().strip()
            if not name or len(name) < 2:
                return None
            
            # Look for additional data
            text_content = card.get_text()
            
            # Extract CAS number
            cas_match = re.search(r'CAS[:\s]*(\d+-\d+-\d+)', text_content, re.I)
            cas_number = cas_match.group(1) if cas_match else None
            
            # Extract score
            score_match = re.search(r'score[:\s]*(\d+(?:\.\d+)?)', text_content, re.I)
            eco_score = float(score_match.group(1)) if score_match else None
            
            # Extract function
            function_match = re.search(r'function[:\s]*([^\\n]+)', text_content, re.I)
            function = function_match.group(1).strip() if function_match else None
            
            return INCIBeautyIngredient(
                name=name,
                inci_name=name,
                cas_number=cas_number,
                eco_score=eco_score,
                function=function
            )
            
        except Exception as e:
            logger.error(f"Error extracting ingredient from card: {e}")
            return None
    
    def _extract_ingredients_from_script(self, script_content: str) -> List[INCIBeautyIngredient]:
        """Extract ingredients from JavaScript content."""
        try:
            ingredients = []
            
            # Look for JSON arrays or objects
            json_matches = re.findall(r'\\[\\{[^\\]]+\\}\\]', script_content)
            for match in json_matches:
                try:
                    data = json.loads(match)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and 'name' in item:
                                ingredient = INCIBeautyIngredient(
                                    name=item.get('name', ''),
                                    inci_name=item.get('inci_name', item.get('name', '')),
                                    cas_number=item.get('cas_number'),
                                    eco_score=item.get('eco_score'),
                                    function=item.get('function')
                                )
                                ingredients.append(ingredient)
                except json.JSONDecodeError:
                    continue
            
            return ingredients
            
        except Exception as e:
            logger.error(f"Error extracting ingredients from script: {e}")
            return []
    
    async def scrape_full_database(self, max_pages: int = 100) -> List[INCIBeautyIngredient]:
        """Scrape the full INCI Beauty database."""
        try:
            logger.info("Starting full database scrape")
            
            # Authenticate if credentials are available
            if self.username and self.password:
                await self.authenticate()
            
            all_ingredients = []
            
            # Try different database endpoints
            database_urls = [
                f"{self.base_url}/database",
                f"{self.base_url}/database/38500",
                f"{self.base_url}/ingredients",
                f"{self.base_url}/api/ingredients",
                f"{self.api_url}/ingredients"
            ]
            
            for url in database_urls:
                try:
                    logger.info(f"Trying database URL: {url}")
                    ingredients = await self.scrape_database_page(url)
                    if ingredients:
                        all_ingredients.extend(ingredients)
                        logger.info(f"Found {len(ingredients)} ingredients at {url}")
                        break
                except Exception as e:
                    logger.warning(f"Failed to scrape {url}: {e}")
                    continue
            
            # If no ingredients found, try pagination
            if not all_ingredients:
                logger.info("Trying pagination approach")
                for page in range(1, max_pages + 1):
                    page_url = f"{self.base_url}/database?page={page}"
                    ingredients = await self.scrape_database_page(page_url)
                    if not ingredients:
                        break
                    all_ingredients.extend(ingredients)
                    logger.info(f"Page {page}: {len(ingredients)} ingredients")
            
            logger.info(f"Total ingredients scraped: {len(all_ingredients)}")
            return all_ingredients
            
        except Exception as e:
            logger.error(f"Error scraping full database: {e}")
            return []
    
    def convert_to_database_format(self, ingredients: List[INCIBeautyIngredient]) -> Dict[str, Dict]:
        """Convert scraped ingredients to database.py format."""
        database_format = {}
        
        for ingredient in ingredients:
            # Determine risk level based on eco score
            if ingredient.eco_score is not None:
                if ingredient.eco_score >= 80:
                    risk_level = "seguro"
                elif ingredient.eco_score >= 60:
                    risk_level = "riesgo bajo"
                elif ingredient.eco_score >= 40:
                    risk_level = "riesgo medio"
                else:
                    risk_level = "riesgo alto"
            else:
                risk_level = "desconocido"
            
            # Create database entry
            key = ingredient.name.lower().replace(' ', '_')
            database_format[key] = {
                "eco_score": ingredient.eco_score or 50.0,
                "risk_level": risk_level,
                "benefits": ingredient.function or ingredient.benefits or "No disponible",
                "risks_detailed": ingredient.concerns or ingredient.risks_detailed or "No disponible",
                "sources": f"INCI Beauty Database{f' + {ingredient.sources}' if ingredient.sources != 'INCI Beauty Database' else ''}"
            }
            
            # Add additional data if available
            if ingredient.cas_number:
                database_format[key]["cas_number"] = ingredient.cas_number
            if ingredient.origin:
                database_format[key]["origin"] = ingredient.origin
            if ingredient.restrictions:
                database_format[key]["restrictions"] = ingredient.restrictions
        
        return database_format

# Test function
async def test_inci_beauty_scraper():
    """Test the INCI Beauty database scraper."""
    async with INCIBeautyDatabaseScraper() as scraper:
        print("🧪 Testing INCI Beauty Database Scraper")
        print("=" * 50)
        
        # Try to scrape the database
        ingredients = await scraper.scrape_full_database(max_pages=5)
        
        if ingredients:
            print(f"✅ Successfully scraped {len(ingredients)} ingredients")
            
            # Show sample ingredients
            print("\\nSample ingredients:")
            for i, ingredient in enumerate(ingredients[:5]):
                print(f"  {i+1}. {ingredient.name}")
                print(f"     INCI: {ingredient.inci_name}")
                print(f"     CAS: {ingredient.cas_number or 'N/A'}")
                print(f"     Score: {ingredient.eco_score or 'N/A'}")
                print(f"     Function: {ingredient.function or 'N/A'}")
                print()
            
            # Convert to database format
            db_format = scraper.convert_to_database_format(ingredients)
            print(f"📊 Converted to database format: {len(db_format)} entries")
            
        else:
            print("❌ No ingredients found")
            print("💡 This may be due to:")
            print("   - Authentication required")
            print("   - Different page structure")
            print("   - Rate limiting")
            print("   - API key needed")

if __name__ == "__main__":
    asyncio.run(test_inci_beauty_scraper())