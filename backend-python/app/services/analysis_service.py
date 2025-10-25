"""
Analysis service
Handles product analysis business logic
"""

from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
import logging
import time
from datetime import datetime

from database import Product, Ingredient, User
from services.ingredient_service import IngredientService
from services.ocr_service import OCRService

logger = logging.getLogger(__name__)

class AnalysisService:
    """Service for product analysis operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ingredient_service = IngredientService(db)
        self.ocr_service = OCRService()
    
    async def analyze_text(
        self,
        text: str,
        user_id: str,
        user_need: Optional[str] = None,
        notes: Optional[str] = None,
        product_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze text for ingredients and provide recommendations"""
        try:
            # Extract ingredients from text
            ingredients = await self._extract_ingredients_from_text(text)
            
            if not ingredients:
                return {
                    "success": False,
                    "error": "No ingredients found in text"
                }
            
            # Analyze ingredients
            analysis_result = await self.ingredient_service.analyze_ingredients(
                ingredients=ingredients,
                user_id=user_id,
                user_concerns=[user_need] if user_need else None
            )
            
            # Create product record
            product = Product(
                name=product_name or "Unknown Product",
                ingredients=ingredients,
                user_id=user_id,
                analysis_data=analysis_result,
                created_at=datetime.utcnow()
            )
            
            self.db.add(product)
            self.db.commit()
            
            return {
                "success": True,
                "product_name": product.name,
                "ingredients": analysis_result.get("ingredients_analysis", []),
                "avg_eco_score": analysis_result.get("overall_score"),
                "suitability": self._determine_suitability(analysis_result),
                "recommendations": analysis_result.get("recommendations", [])
            }
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _extract_ingredients_from_text(self, text: str) -> List[str]:
        """Extract ingredient names from text"""
        # Simple ingredient extraction (can be enhanced with ML)
        import re
        
        # Common ingredient patterns
        ingredient_patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Capitalized words
            r'\b[a-z]+(?:\s+[a-z]+)*\b'  # Lowercase words
        ]
        
        ingredients = []
        for pattern in ingredient_patterns:
            matches = re.findall(pattern, text)
            ingredients.extend(matches)
        
        # Filter out common non-ingredient words
        common_words = {'water', 'aqua', 'and', 'or', 'the', 'of', 'in', 'on', 'at', 'to', 'for'}
        ingredients = [ing for ing in ingredients if ing.lower() not in common_words]
        
        return list(set(ingredients))  # Remove duplicates
    
    def _determine_suitability(self, analysis_result: Dict[str, Any]) -> str:
        """Determine product suitability based on analysis"""
        overall_score = analysis_result.get("overall_score", 0)
        
        if overall_score >= 80:
            return "excellent"
        elif overall_score >= 60:
            return "good"
        elif overall_score >= 40:
            return "moderate"
        else:
            return "poor"
    
    async def get_user_analysis_history(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get user's analysis history"""
        try:
            products = self.db.query(Product).filter(
                Product.user_id == user_id
            ).order_by(Product.created_at.desc()).offset(offset).limit(limit).all()
            
            return [
                {
                    "id": str(product.id),
                    "name": product.name,
                    "ingredients": product.ingredients,
                    "created_at": product.created_at,
                    "analysis_data": product.analysis_data
                }
                for product in products
            ]
            
        except Exception as e:
            logger.error(f"Failed to get analysis history: {e}")
            return []
