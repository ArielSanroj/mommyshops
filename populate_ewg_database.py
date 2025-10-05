"""
EWG Database Population Script
Comprehensive script to populate the database with EWG Skin Deep ingredient data
"""

import asyncio
import httpx
import logging
import json
import os
import re
import time
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
from database import SessionLocal, Ingredient, engine, Base
from ewg_scraper import EWGScraper
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EWGDatabasePopulator:
    def __init__(self):
        self.base_url = "https://www.ewg.org/skindeep"
        self.session = None
        self.rate_limit_delay = 3  # seconds between requests
        self.batch_size = 50
        self.max_ingredients = 5000  # Limit to prevent overwhelming
        
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
    
    async def get_ingredient_categories(self) -> List[Dict]:
        """Get all ingredient categories from EWG"""
        try:
            response = await self.session.get(f"{self.base_url}/ingredients/")
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            categories = []
            
            # Look for category links
            category_links = soup.find_all('a', href=re.compile(r'/ingredients/[a-z-]+'))
            
            for link in category_links:
                category_name = link.get_text().strip()
                category_url = urljoin(self.base_url, link['href'])
                categories.append({
                    'name': category_name,
                    'url': category_url
                })
            
            logger.info(f"Found {len(categories)} ingredient categories")
            return categories
            
        except Exception as e:
            logger.error(f"Error getting ingredient categories: {e}")
            return []
    
    async def get_ingredients_from_category(self, category_url: str) -> List[str]:
        """Get all ingredients from a specific category"""
        try:
            await asyncio.sleep(self.rate_limit_delay)
            
            response = await self.session.get(category_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            ingredients = []
            
            # Look for ingredient links
            ingredient_links = soup.find_all('a', href=re.compile(r'/ingredients/\d+-'))
            
            for link in ingredient_links:
                ingredient_name = link.get_text().strip()
                if ingredient_name and len(ingredient_name) > 2:
                    ingredients.append(ingredient_name)
            
            logger.info(f"Found {len(ingredients)} ingredients in category")
            return ingredients
            
        except Exception as e:
            logger.error(f"Error getting ingredients from category {category_url}: {e}")
            return []
    
    async def get_all_ingredients_from_ewg(self) -> List[str]:
        """Get comprehensive list of ingredients from EWG"""
        all_ingredients = set()
        
        # Get categories first
        categories = await self.get_ingredient_categories()
        
        # Add some common ingredient categories manually
        common_categories = [
            "preservatives", "fragrances", "emulsifiers", "surfactants", 
            "moisturizers", "antioxidants", "vitamins", "acids", "oils",
            "waxes", "polymers", "colorants", "sunscreens"
        ]
        
        for category in common_categories:
            category_url = f"{self.base_url}/ingredients/{category}/"
            ingredients = await self.get_ingredients_from_category(category_url)
            all_ingredients.update(ingredients)
            
            if len(all_ingredients) >= self.max_ingredients:
                break
        
        # Also get ingredients from the main categories
        for category in categories[:10]:  # Limit to first 10 categories
            ingredients = await self.get_ingredients_from_category(category['url'])
            all_ingredients.update(ingredients)
            
            if len(all_ingredients) >= self.max_ingredients:
                break
        
        # Add some common ingredients manually
        common_ingredients = [
            "water", "aqua", "glycerin", "glycerol", "hyaluronic acid", "sodium hyaluronate",
            "retinol", "vitamin c", "ascorbic acid", "niacinamide", "salicylic acid",
            "glycolic acid", "lactic acid", "alpha hydroxy acid", "beta hydroxy acid",
            "ceramides", "peptides", "collagen", "elastin", "squalane", "squalene",
            "jojoba oil", "argan oil", "coconut oil", "olive oil", "sunflower oil",
            "shea butter", "cocoa butter", "beeswax", "lanolin", "dimethicone",
            "cyclomethicone", "silicone", "parabens", "methylparaben", "propylparaben",
            "butylparaben", "ethylparaben", "phenoxyethanol", "benzyl alcohol",
            "sodium lauryl sulfate", "sodium laureth sulfate", "cocamidopropyl betaine",
            "cocamidopropyl hydroxysultaine", "decyl glucoside", "lauryl glucoside",
            "sorbitan oleate", "polysorbate 20", "polysorbate 80", "lecithin",
            "tocopherol", "vitamin e", "ascorbyl palmitate", "retinyl palmitate",
            "coenzyme q10", "ubiquinone", "ferulic acid", "resveratrol",
            "green tea extract", "aloe vera", "chamomile extract", "calendula extract",
            "rosehip oil", "evening primrose oil", "borage oil", "flaxseed oil",
            "vitamin a", "vitamin b3", "vitamin b5", "panthenol", "pro-vitamin b5",
            "vitamin d", "vitamin k", "biotin", "folic acid", "zinc oxide",
            "titanium dioxide", "avobenzone", "octinoxate", "oxybenzone",
            "homosalate", "octisalate", "octocrylene", "zinc oxide", "titanium dioxide"
        ]
        
        all_ingredients.update(common_ingredients)
        
        logger.info(f"Total unique ingredients found: {len(all_ingredients)}")
        return list(all_ingredients)[:self.max_ingredients]
    
    async def populate_database_with_ewg_data(self):
        """Populate database with EWG data"""
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Get all ingredients from EWG
        ingredients_list = await self.get_all_ingredients_from_ewg()
        
        logger.info(f"Starting to populate database with {len(ingredients_list)} ingredients")
        
        # Process ingredients in batches
        db = SessionLocal()
        try:
            existing_ingredients = {ing.name.lower() for ing in db.query(Ingredient).all()}
            logger.info(f"Found {len(existing_ingredients)} existing ingredients in database")
            
            processed = 0
            added = 0
            updated = 0
            
            for i in range(0, len(ingredients_list), self.batch_size):
                batch = ingredients_list[i:i + self.batch_size]
                logger.info(f"Processing batch {i//self.batch_size + 1}/{(len(ingredients_list) + self.batch_size - 1)//self.batch_size}")
                
                # Process batch concurrently
                tasks = []
                for ingredient_name in batch:
                    if ingredient_name.lower() not in existing_ingredients:
                        task = self.process_ingredient(ingredient_name, db)
                        tasks.append(task)
                
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in results:
                        if isinstance(result, Exception):
                            logger.error(f"Error processing ingredient: {result}")
                        else:
                            if result:
                                added += 1
                            processed += 1
                
                # Commit batch
                db.commit()
                logger.info(f"Batch committed. Added: {added}, Processed: {processed}")
                
                # Rate limiting between batches
                await asyncio.sleep(5)
            
            logger.info(f"Database population complete! Added: {added}, Processed: {processed}")
            
        except Exception as e:
            logger.error(f"Error populating database: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def process_ingredient(self, ingredient_name: str, db) -> bool:
        """Process a single ingredient and add to database"""
        try:
            # Use EWG scraper to get data
            async with EWGScraper() as scraper:
                result = await scraper.get_ingredient_data(ingredient_name)
                
                if result["success"]:
                    data = result["data"]
                    
                    # Check if ingredient already exists
                    existing = db.query(Ingredient).filter(
                        Ingredient.name.ilike(ingredient_name)
                    ).first()
                    
                    if existing:
                        # Update existing ingredient
                        existing.eco_score = data.get("eco_score", existing.eco_score)
                        existing.risk_level = data.get("risk_level", existing.risk_level)
                        existing.benefits = data.get("benefits", existing.benefits)
                        existing.risks_detailed = data.get("risks_detailed", existing.risks_detailed)
                        existing.sources = data.get("sources", existing.sources)
                        logger.info(f"Updated ingredient: {ingredient_name}")
                        return True
                    else:
                        # Add new ingredient
                        ingredient = Ingredient(
                            name=ingredient_name,
                            eco_score=data.get("eco_score", 50.0),
                            risk_level=data.get("risk_level", "desconocido"),
                            benefits=data.get("benefits", ""),
                            risks_detailed=data.get("risks_detailed", ""),
                            sources=data.get("sources", "EWG Skin Deep")
                        )
                        db.add(ingredient)
                        logger.info(f"Added ingredient: {ingredient_name}")
                        return True
                else:
                    logger.warning(f"Failed to get data for {ingredient_name}: {result.get('error', 'Unknown error')}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error processing ingredient {ingredient_name}: {e}")
            return False

async def main():
    """Main function to populate database with EWG data"""
    logger.info("Starting EWG database population...")
    
    async with EWGDatabasePopulator() as populator:
        await populator.populate_database_with_ewg_data()
    
    logger.info("EWG database population completed!")

if __name__ == "__main__":
    asyncio.run(main())