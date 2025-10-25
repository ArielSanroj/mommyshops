"""
ICCR (International Cooperation on Cosmetics Regulation) Web Scraper
Scrapes ingredient safety data from ICCR documents and guidelines
"""

import asyncio
import httpx
import re
from bs4 import BeautifulSoup
from typing import Dict, Optional, List
import logging
from urllib.parse import quote_plus
import time
import json
import os

logger = logging.getLogger(__name__)

class ICCRScraper:
    def __init__(self):
        self.base_url = "https://www.iccr-cosmetics.org"
        self.search_url = f"{self.base_url}/search"
        self.documents_url = f"{self.base_url}/topics-documents"
        self.session = None
        self.rate_limit_delay = 3  # seconds between requests
        self.cache_file = "iccr_cache.json"
        self.cache = self._load_cache()
        
    def _load_cache(self) -> Dict:
        """Load cached ICCR data"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load ICCR cache: {e}")
        return {}
    
    def _save_cache(self):
        """Save ICCR data to cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save ICCR cache: {e}")
        
    async def __aenter__(self):
        self.session = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
        self._save_cache()
    
    async def search_ingredient(self, ingredient_name: str) -> Optional[Dict]:
        """
        Search for an ingredient in ICCR documents
        """
        # Check cache first
        cache_key = ingredient_name.lower()
        if cache_key in self.cache:
            logger.info(f"Using cached ICCR data for {ingredient_name}")
            return self.cache[cache_key]
        
        try:
            # Search for the ingredient in ICCR documents
            search_params = {"q": ingredient_name}
            response = await self.session.get(self.search_url, params=search_params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for search results
            results = soup.find_all('div', class_='search-result') or soup.find_all('article', class_='result')
            
            if not results:
                # Try alternative selectors
                results = soup.find_all('a', href=re.compile(r'document|report|guideline'))
            
            if not results:
                logger.warning(f"No ICCR results found for: {ingredient_name}")
                return None
                
            # Get the first result (most relevant)
            result_link = results[0]
            if result_link.name == 'a':
                document_url = result_link['href']
            else:
                link_element = result_link.find('a', href=re.compile(r'document|report|guideline'))
                if link_element:
                    document_url = link_element['href']
                else:
                    return None
            
            if not document_url.startswith('http'):
                document_url = f"{self.base_url}{document_url}"
            
            # Scrape the document page
            return await self.scrape_document_page(document_url, ingredient_name)
            
        except Exception as e:
            logger.error(f"Error searching ICCR for ingredient {ingredient_name}: {e}")
            return None
    
    async def scrape_document_page(self, url: str, ingredient_name: str) -> Optional[Dict]:
        """
        Scrape data from an ICCR document page
        """
        try:
            await asyncio.sleep(self.rate_limit_delay)  # Rate limiting
            
            response = await self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract document summary/guidance
            summary_element = soup.find('div', class_='summary') or soup.find('section', class_='document-summary')
            summary = ""
            if summary_element:
                summary = summary_element.get_text().strip()
            else:
                # Look for guidance in text
                summary_text = soup.get_text()
                guidance_match = re.search(r'(harmonized.*?guidance|global.*?standard|recommended.*?limit)', summary_text, re.IGNORECASE)
                if guidance_match:
                    summary = guidance_match.group(1)
            
            # Extract function/benefits
            function_element = soup.find('div', class_='function') or soup.find('section', class_='ingredient-function')
            function = ""
            if function_element:
                function = function_element.get_text().strip()
            else:
                # Look for common cosmetic functions
                function_text = soup.get_text()
                functions = []
                if re.search(r'skin conditioning', function_text, re.IGNORECASE):
                    functions.append("Skin conditioning")
                if re.search(r'anti-aging', function_text, re.IGNORECASE):
                    functions.append("Anti-aging")
                if re.search(r'emollient', function_text, re.IGNORECASE):
                    functions.append("Emollient")
                if re.search(r'preservative', function_text, re.IGNORECASE):
                    functions.append("Preservative")
                if re.search(r'uv filter', function_text, re.IGNORECASE):
                    functions.append("UV filter")
                function = ", ".join(functions) if functions else "Cosmetic ingredient"
            
            # Extract harmonized limits
            limit_element = soup.find('div', class_='limit') or soup.find('span', class_='concentration')
            limit = ""
            if limit_element:
                limit = limit_element.get_text().strip()
            else:
                # Look for limit patterns
                limit_text = soup.get_text()
                limit_match = re.search(r'(\d+\.?\d*%|\d+\.?\d*\s*ppm)', limit_text)
                if limit_match:
                    limit = limit_match.group(1)
            
            # Extract regulatory status
            status_element = soup.find('div', class_='status') or soup.find('section', class_='regulatory-status')
            status = ""
            if status_element:
                status = status_element.get_text().strip()
            else:
                # Look for regulatory status
                status_text = soup.get_text()
                if re.search(r'approved|authorized', status_text, re.IGNORECASE):
                    status = "Approved for cosmetic use"
                elif re.search(r'restricted', status_text, re.IGNORECASE):
                    status = "Restricted use"
                elif re.search(r'prohibited', status_text, re.IGNORECASE):
                    status = "Prohibited"
                else:
                    status = "Under review"
            
            # Determine risk level based on status and guidance
            risk_level = "desconocido"
            if status:
                status_lower = status.lower()
                if "approved" in status_lower or "authorized" in status_lower:
                    risk_level = "seguro"
                elif "restricted" in status_lower:
                    risk_level = "riesgo bajo"
                elif "prohibited" in status_lower:
                    risk_level = "riesgo alto"
                else:
                    risk_level = "riesgo bajo"
            
            # Create detailed risks
            risks_detailed = summary or status
            if limit:
                risks_detailed += f" (Harmonized limit: {limit})"
            
            result = {
                "benefits": function or "Cosmetic ingredient",
                "risks_detailed": risks_detailed or "No specific regulatory guidance available",
                "risk_level": risk_level,
                "sources": "ICCR",
                "harmonized_limit": limit,
                "regulatory_status": status,
                "url": url
            }
            
            # Cache the result
            self.cache[ingredient_name.lower()] = result
            
            logger.info(f"Successfully scraped ICCR data for {ingredient_name}: {risk_level}")
            return result
            
        except Exception as e:
            logger.error(f"Error scraping ICCR document page {url}: {e}")
            return None
    
    async def get_ingredient_data(self, ingredient_name: str) -> Dict:
        """
        Main method to get ingredient data from ICCR
        """
        try:
            result = await self.search_ingredient(ingredient_name)
            
            if result:
                return {
                    "success": True,
                    "data": result,
                    "source": "ICCR",
                    "cached": False
                }
            else:
                return {
                    "success": False,
                    "data": {
                        "benefits": "No data available",
                        "risks_detailed": "No ICCR data found",
                        "risk_level": "desconocido",
                        "sources": ""
                    },
                    "error": "Ingredient not found in ICCR documents",
                    "source": "ICCR"
                }
                
        except Exception as e:
            logger.error(f"Error getting ICCR data for {ingredient_name}: {e}")
            return {
                "success": False,
                "data": {
                    "benefits": "No data available",
                    "risks_detailed": "No ICCR data found",
                    "risk_level": "desconocido",
                    "sources": ""
                },
                "error": str(e),
                "source": "ICCR"
            }

# Test function
async def test_iccr_scraper():
    """Test the ICCR scraper with a few ingredients"""
    async with ICCRScraper() as scraper:
        test_ingredients = ["retinol", "parabens", "sodium lauryl sulfate", "water"]
        
        for ingredient in test_ingredients:
            print(f"\nTesting ICCR ingredient: {ingredient}")
            result = await scraper.get_ingredient_data(ingredient)
            print(f"Success: {result['success']}")
            if result['success']:
                data = result['data']
                print(f"Benefits: {data.get('benefits', 'N/A')}")
                print(f"Risk Level: {data.get('risk_level', 'N/A')}")
                print(f"Risks: {data.get('risks_detailed', 'N/A')[:100]}...")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(test_iccr_scraper())