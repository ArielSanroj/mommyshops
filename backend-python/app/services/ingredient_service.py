"""
Ingredient Service
Handles ingredient analysis and safety scoring
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class IngredientService:
    """Service for ingredient analysis"""
    
    def __init__(self, db):
        self.db = db
        self.logger = logger
    
    async def analyze_ingredients(self, ingredients: List[str], user_id: str, user_concerns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyze a list of ingredients"""
        try:
            ingredients_analysis = []
            
            for ingredient in ingredients:
                # Basic analysis for each ingredient
                analysis = {
                    "name": ingredient,
                    "score": 85,  # Default safe score
                    "safety_level": "safe",
                    "description": f"Analysis for {ingredient}",
                    "concerns": []
                }
                
                # Check for potentially harmful ingredients
                harmful_ingredients = ["METHYLPARABEN", "PROPYLPARABEN", "FRAGRANCE", "PARFUM"]
                if ingredient.upper() in harmful_ingredients:
                    analysis["score"] = 60
                    analysis["safety_level"] = "moderate"
                    analysis["concerns"] = ["May cause skin irritation"]
                
                ingredients_analysis.append(analysis)
            
            # Calculate overall score
            overall_score = sum(ing["score"] for ing in ingredients_analysis) / len(ingredients_analysis)
            
            # Generate recommendations
            recommendations = []
            if overall_score >= 80:
                recommendations.append("Product appears safe for most skin types")
            elif overall_score >= 60:
                recommendations.append("Product has moderate safety concerns")
            else:
                recommendations.append("Product may not be suitable for sensitive skin")
            
            return {
                "success": True,
                "ingredients_analysis": ingredients_analysis,
                "overall_score": overall_score,
                "recommendations": recommendations
            }
            
        except Exception as e:
            self.logger.error(f"Ingredient analysis failed: {e}")
            return {
                "success": False,
                "ingredients_analysis": [],
                "overall_score": 0,
                "recommendations": ["Analysis failed"]
            }
