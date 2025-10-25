"""
CIR (Cosmetic Ingredient Review) Web Scraper
Scrapes ingredient safety data from CIR database
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

class CIRScraper:
    def __init__(self):
        self.base_url = "https://cir-reports.cir-safety.org"
        self.search_url = f"{self.base_url}/search"
        self.session = None
        self.rate_limit_delay = 2  # seconds between requests
        self.cache_file = "cir_cache.json"
        self.cache = self._load_cache()
        
    def _load_cache(self) -> Dict:
        """Load cached CIR data"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load CIR cache: {e}")
        return {}
    
    def _save_cache(self):
        """Save CIR data to cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save CIR cache: {e}")
        
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
        Search for an ingredient in CIR database
        """
        # Check cache first
        cache_key = ingredient_name.lower()
        if cache_key in self.cache:
            logger.info(f"Using cached CIR data for {ingredient_name}")
            return self.cache[cache_key]
        
        try:
            # Search for the ingredient
            search_params = {"q": ingredient_name}
            response = await self.session.get(self.search_url, params=search_params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for search results
            results = soup.find_all('div', class_='search-result') or soup.find_all('article', class_='result')
            
            if not results:
                # Try alternative selectors
                results = soup.find_all('a', href=re.compile(r'/report/'))
            
            if not results:
                logger.warning(f"No CIR results found for: {ingredient_name}")
                return None
                
            # Get the first result (most relevant)
            result_link = results[0]
            if result_link.name == 'a':
                report_url = result_link['href']
            else:
                link_element = result_link.find('a', href=re.compile(r'/report/'))
                if link_element:
                    report_url = link_element['href']
                else:
                    return None
            
            if not report_url.startswith('http'):
                report_url = f"{self.base_url}{report_url}"
            
            # Scrape the report page
            return await self.scrape_report_page(report_url, ingredient_name)
            
        except Exception as e:
            logger.error(f"Error searching CIR for ingredient {ingredient_name}: {e}")
            return None
    
    async def scrape_report_page(self, url: str, ingredient_name: str) -> Optional[Dict]:
        """
        Scrape data from a CIR report page
        """
        try:
            await asyncio.sleep(self.rate_limit_delay)  # Rate limiting
            
            response = await self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract safety conclusion
            conclusion_element = soup.find('div', class_='conclusion') or soup.find('section', class_='safety-conclusion')
            conclusion = ""
            if conclusion_element:
                conclusion = conclusion_element.get_text().strip()
            else:
                # Look for conclusion in text
                conclusion_text = soup.get_text()
                conclusion_match = re.search(r'(safe.*?as used|insufficient data|not safe)', conclusion_text, re.IGNORECASE)
                if conclusion_match:
                    conclusion = conclusion_match.group(1)
            
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
                function = ", ".join(functions) if functions else "Cosmetic ingredient"
            
            # Extract concentration limits
            concentration_element = soup.find('div', class_='concentration') or soup.find('span', class_='limit')
            concentration = ""
            if concentration_element:
                concentration = concentration_element.get_text().strip()
            else:
                # Look for concentration patterns
                concentration_text = soup.get_text()
                conc_match = re.search(r'(\d+\.?\d*%|\d+\.?\d*\s*ppm)', concentration_text)
                if conc_match:
                    concentration = conc_match.group(1)
            
            # Determine risk level based on conclusion
            risk_level = "desconocido"
            if conclusion:
                conclusion_lower = conclusion.lower()
                if "safe as used" in conclusion_lower or "safe" in conclusion_lower:
                    risk_level = "seguro"
                elif "insufficient data" in conclusion_lower:
                    risk_level = "riesgo bajo"
                elif "not safe" in conclusion_lower or "unsafe" in conclusion_lower:
                    risk_level = "riesgo alto"
                else:
                    risk_level = "riesgo bajo"
            
            # Create detailed risks
            risks_detailed = conclusion
            if concentration:
                risks_detailed += f" (Concentration limit: {concentration})"
            
            result = {
                "benefits": function or "Cosmetic ingredient",
                "risks_detailed": risks_detailed or "No specific safety data available",
                "risk_level": risk_level,
                "sources": "CIR",
                "concentration_limit": concentration,
                "url": url
            }
            
            # Cache the result
            self.cache[ingredient_name.lower()] = result
            
            logger.info(f"Successfully scraped CIR data for {ingredient_name}: {risk_level}")
            return result
            
        except Exception as e:
            logger.error(f"Error scraping CIR report page {url}: {e}")
            return None
    
    async def get_ingredient_data(self, ingredient_name: str) -> Dict:
        """
        Main method to get ingredient data from CIR
        """
        try:
            result = await self.search_ingredient(ingredient_name)
            
            if result:
                return {
                    "success": True,
                    "data": result,
                    "source": "CIR",
                    "cached": False
                }
            else:
                return {
                    "success": False,
                    "data": {
                        "benefits": "No data available",
                        "risks_detailed": "No CIR data found",
                        "risk_level": "desconocido",
                        "sources": ""
                    },
                    "error": "Ingredient not found in CIR database",
                    "source": "CIR"
                }
                
        except Exception as e:
            logger.error(f"Error getting CIR data for {ingredient_name}: {e}")
            return {
                "success": False,
                "data": {
                    "benefits": "No data available",
                    "risks_detailed": "No CIR data found",
                    "risk_level": "desconocido",
                    "sources": ""
                },
                "error": str(e),
                "source": "CIR"
            }

# Test function
async def test_cir_scraper():
    """Test the CIR scraper with a few ingredients"""
    async with CIRScraper() as scraper:
        test_ingredients = ["retinol", "parabens", "sodium lauryl sulfate", "water"]
        
        for ingredient in test_ingredients:
            print(f"\nTesting CIR ingredient: {ingredient}")
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
    asyncio.run(test_cir_scraper())