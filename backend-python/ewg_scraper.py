"""
EWG Skin Deep Web Scraper
Scrapes ingredient data from EWG's Skin Deep database
"""

import asyncio
import httpx
import re
from bs4 import BeautifulSoup
from typing import Dict, Optional, List
import logging
from urllib.parse import quote_plus
import time

logger = logging.getLogger(__name__)

class EWGScraper:
    def __init__(self):
        self.base_url = "https://www.ewg.org/skindeep"
        self.search_url = f"{self.base_url}/search/"
        self.session = None
        self.rate_limit_delay = 2  # seconds between requests
        
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
    
    async def search_ingredient(self, ingredient_name: str) -> Optional[Dict]:
        """
        Search for an ingredient on EWG Skin Deep and extract data
        """
        try:
            # Search for the ingredient
            search_params = {"search": ingredient_name}
            response = await self.session.get(self.search_url, params=search_params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for ingredient results
            ingredient_links = soup.find_all('a', href=re.compile(r'/ingredients/\d+-'))
            
            if not ingredient_links:
                logger.warning(f"No ingredient results found for: {ingredient_name}")
                return None
                
            # Get the first result (most relevant)
            ingredient_url = ingredient_links[0]['href']
            if not ingredient_url.startswith('http'):
                ingredient_url = f"https://www.ewg.org{ingredient_url}"
            
            # Scrape the ingredient page
            return await self.scrape_ingredient_page(ingredient_url, ingredient_name)
            
        except Exception as e:
            logger.error(f"Error searching for ingredient {ingredient_name}: {e}")
            return None
    
    async def scrape_ingredient_page(self, url: str, ingredient_name: str) -> Optional[Dict]:
        """
        Scrape data from a specific ingredient page
        """
        try:
            await asyncio.sleep(self.rate_limit_delay)  # Rate limiting
            
            response = await self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract score/rating from the squircle image
            score_element = soup.find('img', class_='squircle')
            score = None
            if score_element:
                src = score_element.get('src', '')
                # Extract score from URL like "/skindeep/squircle/show.svg?score=1&score_min=1"
                score_match = re.search(r'score=(\d+)', src)
                if score_match:
                    score = int(score_match.group(1))
            
            # Extract concerns
            concerns = []
            concern_elements = soup.find_all('div', class_='concern') or soup.find_all('li', class_='concern')
            for concern in concern_elements:
                concern_text = concern.get_text().strip()
                if concern_text:
                    concerns.append(concern_text)
            
            # Extract description/summary
            description_element = soup.find('div', class_='description') or soup.find('p', class_='summary')
            description = description_element.get_text().strip() if description_element else ""
            
            # Extract hazard level
            hazard_element = soup.find('div', class_='hazard-level') or soup.find('span', class_='hazard')
            hazard_level = hazard_element.get_text().strip() if hazard_element else "Unknown"
            
            # Convert EWG score (1-10) to eco_score (0-100)
            eco_score = 50.0  # Default
            if score:
                eco_score = max(0, 100 - (score * 10))
            
            # Determine risk level based on score
            risk_level = "desconocido"
            if score:
                if score <= 2:
                    risk_level = "seguro"
                elif score <= 4:
                    risk_level = "riesgo bajo"
                elif score <= 6:
                    risk_level = "riesgo medio"
                elif score <= 8:
                    risk_level = "riesgo alto"
                else:
                    risk_level = "riesgo alto"
            
            result = {
                "eco_score": eco_score,
                "risks_detailed": "; ".join(concerns) if concerns else "No specific concerns found",
                "risk_level": risk_level,
                "sources": "EWG Skin Deep",
                "ewg_score": score,
                "description": description,
                "hazard_level": hazard_level,
                "url": url
            }
            
            logger.info(f"Successfully scraped EWG data for {ingredient_name}: score={score}, eco_score={eco_score}")
            return result
            
        except Exception as e:
            logger.error(f"Error scraping ingredient page {url}: {e}")
            return None
    
    async def get_ingredient_data(self, ingredient_name: str) -> Dict:
        """
        Main method to get ingredient data from EWG
        """
        try:
            result = await self.search_ingredient(ingredient_name)
            
            if result:
                return {
                    "success": True,
                    "data": result,
                    "source": "EWG",
                    "cached": False
                }
            else:
                return {
                    "success": False,
                    "data": {
                        "eco_score": 50.0,
                        "risks_detailed": "No data available",
                        "risk_level": "desconocido",
                        "sources": ""
                    },
                    "error": "Ingredient not found on EWG Skin Deep",
                    "source": "EWG"
                }
                
        except Exception as e:
            logger.error(f"Error getting EWG data for {ingredient_name}: {e}")
            return {
                "success": False,
                "data": {
                    "eco_score": 50.0,
                    "risks_detailed": "No data available",
                    "risk_level": "desconocido",
                    "sources": ""
                },
                "error": str(e),
                "source": "EWG"
            }

# Test function
async def test_ewg_scraper():
    """Test the EWG scraper with a few ingredients"""
    async with EWGScraper() as scraper:
        test_ingredients = ["water", "parabens", "sodium lauryl sulfate"]
        
        for ingredient in test_ingredients:
            print(f"\nTesting ingredient: {ingredient}")
            result = await scraper.get_ingredient_data(ingredient)
            print(f"Success: {result['success']}")
            if result['success']:
                data = result['data']
                print(f"EWG Score: {data.get('ewg_score', 'N/A')}")
                print(f"Eco Score: {data.get('eco_score', 'N/A')}")
                print(f"Risk Level: {data.get('risk_level', 'N/A')}")
                print(f"Concerns: {data.get('risks_detailed', 'N/A')[:100]}...")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(test_ewg_scraper())