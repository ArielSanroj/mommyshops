"""
Ingredient Service for MommyShops API
Handles ingredient analysis, safety assessment, and external API integration
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import asyncio

from ..core.config import get_settings
from ..database import Ingredient
from .external_api_service import ExternalAPIService

logger = logging.getLogger(__name__)

class IngredientService:
    """
    Service for ingredient analysis and safety assessment
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.external_api_service = ExternalAPIService()
    
    async def analyze_ingredients(self, text: str, user_need: str) -> List[Dict[str, Any]]:
        """
        Analyze ingredients from text for safety
        """
        try:
            # Extract ingredients from text
            ingredients = await self._extract_ingredients_from_text(text)
            
            if not ingredients:
                logger.warning("No ingredients found in text")
                return []
            
            # Analyze each ingredient
            analysis_results = []
            for ingredient in ingredients:
                analysis = await self._analyze_single_ingredient(ingredient, user_need)
                if analysis:
                    analysis_results.append(analysis)
            
            logger.info(f"Analyzed {len(analysis_results)} ingredients")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing ingredients: {e}")
            return []
    
    async def _extract_ingredients_from_text(self, text: str) -> List[str]:
        """
        Extract ingredient names from text
        """
        try:
            ingredients = []
            
            # Simple extraction logic
            # This would be more sophisticated in production
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if line and len(line) > 2:
                    # Check if line contains ingredients
                    if any(keyword in line.lower() for keyword in [
                        'ingredients', 'ingredientes', 'composition', 'composición'
                    ]):
                        # Split by common separators
                        parts = line.split(',')
                        for part in parts:
                            ingredient = part.strip()
                            if ingredient and len(ingredient) > 2:
                                ingredients.append(ingredient)
            
            return ingredients
            
        except Exception as e:
            logger.error(f"Error extracting ingredients: {e}")
            return []
    
    async def _analyze_single_ingredient(self, ingredient_name: str, user_need: str) -> Optional[Dict[str, Any]]:
        """
        Analyze a single ingredient for safety and properties
        """
        try:
            # Check if ingredient exists in database
            db_ingredient = self.db.query(Ingredient).filter(
                Ingredient.name.ilike(f"%{ingredient_name}%")
            ).first()
            
            if db_ingredient:
                # Use existing data
                return {
                    "name": db_ingredient.name,
                    "risk_level": db_ingredient.risk_level,
                    "eco_score": db_ingredient.eco_score,
                    "benefits": db_ingredient.benefits,
                    "risks_detailed": db_ingredient.risks_detailed,
                    "sources": db_ingredient.sources
                }
            
            # Fetch data from external APIs
            external_data = await self.external_api_service.fetch_ingredient_data(
                ingredient_name, user_need
            )
            
            if external_data:
                # Save to database for future use
                new_ingredient = Ingredient(
                    name=ingredient_name,
                    risk_level=external_data.get("risk_level", "desconocido"),
                    eco_score=external_data.get("eco_score", 50.0),
                    benefits=external_data.get("benefits", "No disponible"),
                    risks_detailed=external_data.get("risks_detailed", "No disponible"),
                    sources=external_data.get("sources", "External APIs")
                )
                
                self.db.add(new_ingredient)
                self.db.commit()
                
                return {
                    "name": new_ingredient.name,
                    "risk_level": new_ingredient.risk_level,
                    "eco_score": new_ingredient.eco_score,
                    "benefits": new_ingredient.benefits,
                    "risks_detailed": new_ingredient.risks_detailed,
                    "sources": new_ingredient.sources
                }
            
            # Return default analysis if no data found
            return {
                "name": ingredient_name,
                "risk_level": "desconocido",
                "eco_score": 50.0,
                "benefits": "No disponible",
                "risks_detailed": "No se encontró información",
                "sources": "No disponible"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing ingredient {ingredient_name}: {e}")
            return None
    
    async def get_ingredient_safety_score(self, ingredient_name: str) -> float:
        """
        Get safety score for an ingredient (0-100)
        """
        try:
            analysis = await self._analyze_single_ingredient(ingredient_name, "safety")
            if analysis:
                # Convert risk level to numeric score
                risk_scores = {
                    "seguro": 90.0,
                    "riesgo bajo": 70.0,
                    "riesgo medio": 50.0,
                    "riesgo alto": 30.0,
                    "cancerígeno": 10.0,
                    "desconocido": 50.0
                }
                return risk_scores.get(analysis["risk_level"], 50.0)
            
            return 50.0  # Default score
            
        except Exception as e:
            logger.error(f"Error getting safety score for {ingredient_name}: {e}")
            return 50.0
    
    async def get_ingredient_eco_score(self, ingredient_name: str) -> float:
        """
        Get eco-friendliness score for an ingredient (0-100)
        """
        try:
            analysis = await self._analyze_single_ingredient(ingredient_name, "eco")
            if analysis:
                return analysis["eco_score"]
            
            return 50.0  # Default score
            
        except Exception as e:
            logger.error(f"Error getting eco score for {ingredient_name}: {e}")
            return 50.0
    
    async def check_external_apis(self) -> Dict[str, Any]:
        """
        Check status of external APIs
        """
        try:
            return await self.external_api_service.health_check()
            
        except Exception as e:
            logger.error(f"Error checking external APIs: {e}")
            return {
                "all_available": False,
                "apis": {},
                "error": str(e)
            }
    
    async def get_ingredient_alternatives(self, ingredient_name: str) -> List[str]:
        """
        Get alternative ingredients for a given ingredient
        """
        try:
            # This would use ML or external APIs to find alternatives
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error getting alternatives for {ingredient_name}: {e}")
            return []

