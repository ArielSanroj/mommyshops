"""
Analysis service
Handles product analysis business logic
"""

from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
import logging
import time
from datetime import datetime

from app.database.models import Product, Ingredient, User
from app.services.ingredient_service import IngredientService
from app.services.ocr_service import OCRService

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
            # Extract and normalize ingredients from text
            ingredients = await self._extract_ingredients_from_text(text)
            
            if not ingredients:
                return {
                    "success": False,
                    "error": "No ingredients found in text"
                }
            
            # Detect product type (simple heuristic)
            product_type = self._detect_product_type(product_name, ingredients)

            # Analyze ingredients
            analysis_result = await self.ingredient_service.analyze_ingredients(
                ingredients=ingredients,
                user_id=user_id,
                user_concerns=[user_need] if user_need else None,
                product_type=product_type
            )
            
            # Persist product if schema supports it; otherwise continue without failing
            product_name_final = product_name or "Unknown Product"
            try:
                product = Product(
                    name=product_name_final,
                    ingredients=ingredients,
                    analysis_data=analysis_result,
                    created_at=datetime.utcnow()
                )
                # user_id may not exist in schema; set if present
                if hasattr(Product, "user_id"):
                    setattr(product, "user_id", user_id)
                self.db.add(product)
                self.db.commit()
                persisted_name = product.name
            except Exception as persist_err:
                logger.warning(f"Skipping DB persist for product due to error: {persist_err}")
                try:
                    self.db.rollback()
                except Exception:
                    pass
                persisted_name = product_name_final

            # Build structured report
            structured_report = self._build_structured_report(
                product_name=product_name_final,
                ingredients_analysis=analysis_result.get("ingredients_analysis", []),
                overall_score=analysis_result.get("overall_score", 0),
                avg_ewg_score=analysis_result.get("avg_ewg_score", 0),
                eco_friendly_percentage=analysis_result.get("eco_friendly_percentage", 0),
                product_type=product_type or "general"
            )

            result = {
                "success": True,
                "product_name": persisted_name,
                "product_type": product_type or "general",
                "ingredients": analysis_result.get("ingredients_analysis", []),
                "avg_eco_score": analysis_result.get("overall_score"),
                "suitability": self._determine_suitability(analysis_result),
                "recommendations": analysis_result.get("recommendations", []),
                "structured_report": structured_report
            }
            if product_type:
                result["product_type"] = product_type
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _extract_ingredients_from_text(self, text: str) -> List[str]:
        """Extract ingredient names by splitting on commas and cleaning."""
        import re
        raw = (text or "").replace("\n", " ")
        parts = [s.strip() for s in raw.split(",") if s.strip()]
        cleaned = []
        seen = set()
        for p in parts:
            t = re.sub(r"\([^)]+\)", "", p).strip().rstrip(".;:")
            if t and t.lower() != "aqua" and t not in seen:
                seen.add(t)
                cleaned.append(t)
        return cleaned

    def _detect_product_type(self, product_name: Optional[str], ingredients: List[str]) -> Optional[str]:
        """Heuristic product type detection (focus: hair conditioner)."""
        pname = (product_name or "").lower()
        if any(k in pname for k in ["acondicionador", "conditioner", "tratamiento capilar"]):
            return "hair_conditioner"
        upper = {i.upper() for i in ingredients}
        hair_markers = {"CETRIMONIUM CHLORIDE", "BEHENTRIMONIUM CHLORIDE", "POLYQUATERNIUM-10"}
        if hair_markers.intersection(upper):
            return "hair_conditioner"
        return None
    
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

    def _build_structured_report(
        self,
        product_name: str,
        ingredients_analysis: List[Dict[str, Any]],
        overall_score: float,
        avg_ewg_score: float,
        eco_friendly_percentage: float,
        product_type: str
    ) -> Dict[str, Any]:
        detected_ingredients = [i.get("name", "-") for i in ingredients_analysis]
        safe = []
        problematic = []
        for i in ingredients_analysis:
            risk = (i.get("risk") or "").lower()
            entry = {
                "ingredient": i.get("name", "-"),
                "ewg_score": i.get("ewg_score"),
                "eco_score": 90 if i.get("eco_friendly") else 40,
                "analysis": i.get("description", ""),
                "substitute": i.get("substitute") or None,
            }
            if risk in ("high", "moderate"):
                problematic.append(entry)
            else:
                safe.append({k: entry[k] for k in ["ingredient", "ewg_score", "eco_score", "analysis"]})

        stats = {
            "total": len(ingredients_analysis),
            "safe_count": len(safe),
            "problematic_count": len(problematic),
            "overall_score": round(float(overall_score or 0), 1),
            "eco_friendly_percentage": round(float(eco_friendly_percentage or 0), 1),
            "avg_ewg_score": round(float(avg_ewg_score or 0), 1),
            "rating": self._determine_suitability({"overall_score": overall_score or 0}),
        }

        return {
            "product_name": product_name,
            "product_type": product_type,
            "detected_ingredients": detected_ingredients,
            "safety": {
                "safe": safe,
                "problematic": problematic,
            },
            "stats": stats,
            "recommendations": [],
        }
    
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
