"""
SCCS (Scientific Committee on Consumer Safety) Web Scraper
Scrapes ingredient safety data from EU SCCS opinions
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

class SCCSScraper:
    def __init__(self):
        self.base_url = "https://health.ec.europa.eu"
        self.search_url = f"{self.base_url}/search/site"
        self.opinions_url = f"{self.base_url}/scientific-committees/scientific-committee-consumer-safety-sccs/sccs-opinions_en"
        self.session = None
        self.rate_limit_delay = 3  # seconds between requests
        self.cache_file = "sccs_cache.json"
        self.cache = self._load_cache()
        
    def _load_cache(self) -> Dict:
        """Load cached SCCS data"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load SCCS cache: {e}")
        return {}
    
    def _save_cache(self):
        """Save SCCS data to cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save SCCS cache: {e}")
        
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
        Search for an ingredient in SCCS opinions
        """
        # Check cache first
        cache_key = ingredient_name.lower()
        if cache_key in self.cache:
            logger.info(f"Using cached SCCS data for {ingredient_name}")
            return self.cache[cache_key]
        
        try:
            # Search for the ingredient in SCCS opinions
            search_term = f"{ingredient_name} SCCS"
            search_params = {"query": search_term}
            response = await self.session.get(self.search_url, params=search_params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for search results
            results = soup.find_all('div', class_='search-result') or soup.find_all('article', class_='result')
            
            if not results:
                # Try alternative selectors
                results = soup.find_all('a', href=re.compile(r'opinion|sccs'))
            
            if not results:
                logger.warning(f"No SCCS results found for: {ingredient_name}")
                return None
                
            # Get the first result (most relevant)
            result_link = results[0]
            if result_link.name == 'a':
                opinion_url = result_link['href']
            else:
                link_element = result_link.find('a', href=re.compile(r'opinion|sccs'))
                if link_element:
                    opinion_url = link_element['href']
                else:
                    return None
            
            if not opinion_url.startswith('http'):
                opinion_url = f"{self.base_url}{opinion_url}"
            
            # Scrape the opinion page
            return await self.scrape_opinion_page(opinion_url, ingredient_name)
            
        except Exception as e:
            logger.error(f"Error searching SCCS for ingredient {ingredient_name}: {e}")
            return None
    
    async def scrape_opinion_page(self, url: str, ingredient_name: str) -> Optional[Dict]:
        """
        Scrape data from an SCCS opinion page
        """
        try:
            await asyncio.sleep(self.rate_limit_delay)  # Rate limiting
            
            response = await self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract opinion conclusion
            conclusion_element = soup.find('div', class_='conclusion') or soup.find('section', class_='opinion-conclusion')
            conclusion = ""
            if conclusion_element:
                conclusion = conclusion_element.get_text().strip()
            else:
                # Look for conclusion in text
                conclusion_text = soup.get_text()
                conclusion_match = re.search(r'(safe.*?use|not safe|insufficient data|no.*?concern)', conclusion_text, re.IGNORECASE)
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
                if re.search(r'uv filter', function_text, re.IGNORECASE):
                    functions.append("UV filter")
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
            
            # Extract specific concerns
            concerns_element = soup.find('div', class_='concerns') or soup.find('section', class_='safety-concerns')
            concerns = ""
            if concerns_element:
                concerns = concerns_element.get_text().strip()
            else:
                # Look for common concerns
                concerns_text = soup.get_text()
                concern_list = []
                if re.search(r'irritation', concerns_text, re.IGNORECASE):
                    concern_list.append("Skin irritation")
                if re.search(r'allergen', concerns_text, re.IGNORECASE):
                    concern_list.append("Allergenic potential")
                if re.search(r'reproductive', concerns_text, re.IGNORECASE):
                    concern_list.append("Reproductive toxicity")
                if re.search(r'carcinogen', concerns_text, re.IGNORECASE):
                    concern_list.append("Carcinogenic potential")
                concerns = ", ".join(concern_list) if concern_list else "No specific concerns identified"
            
            # Determine risk level based on conclusion
            risk_level = "desconocido"
            if conclusion:
                conclusion_lower = conclusion.lower()
                if "safe" in conclusion_lower and "not" not in conclusion_lower:
                    risk_level = "seguro"
                elif "insufficient data" in conclusion_lower or "limited data" in conclusion_lower:
                    risk_level = "riesgo bajo"
                elif "not safe" in conclusion_lower or "unsafe" in conclusion_lower:
                    risk_level = "riesgo alto"
                else:
                    risk_level = "riesgo bajo"
            
            # Create detailed risks
            risks_detailed = conclusion
            if concentration:
                risks_detailed += f" (Concentration limit: {concentration})"
            if concerns:
                risks_detailed += f" (Concerns: {concerns})"
            
            result = {
                "benefits": function or "Cosmetic ingredient",
                "risks_detailed": risks_detailed or "No specific safety data available",
                "risk_level": risk_level,
                "sources": "SCCS",
                "concentration_limit": concentration,
                "concerns": concerns,
                "url": url
            }
            
            # Cache the result
            self.cache[ingredient_name.lower()] = result
            
            logger.info(f"Successfully scraped SCCS data for {ingredient_name}: {risk_level}")
            return result
            
        except Exception as e:
            logger.error(f"Error scraping SCCS opinion page {url}: {e}")
            return None
    
    async def get_ingredient_data(self, ingredient_name: str) -> Dict:
        """
        Main method to get ingredient data from SCCS
        """
        try:
            result = await self.search_ingredient(ingredient_name)
            
            if result:
                return {
                    "success": True,
                    "data": result,
                    "source": "SCCS",
                    "cached": False
                }
            else:
                return {
                    "success": False,
                    "data": {
                        "benefits": "No data available",
                        "risks_detailed": "No SCCS data found",
                        "risk_level": "desconocido",
                        "sources": ""
                    },
                    "error": "Ingredient not found in SCCS opinions",
                    "source": "SCCS"
                }
                
        except Exception as e:
            logger.error(f"Error getting SCCS data for {ingredient_name}: {e}")
            return {
                "success": False,
                "data": {
                    "benefits": "No data available",
                    "risks_detailed": "No SCCS data found",
                    "risk_level": "desconocido",
                    "sources": ""
                },
                "error": str(e),
                "source": "SCCS"
            }

# Test function
async def test_sccs_scraper():
    """Test the SCCS scraper with a few ingredients"""
    async with SCCSScraper() as scraper:
        test_ingredients = ["retinol", "parabens", "sodium lauryl sulfate", "water"]
        
        for ingredient in test_ingredients:
            print(f"\nTesting SCCS ingredient: {ingredient}")
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
    asyncio.run(test_sccs_scraper())