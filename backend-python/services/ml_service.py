"""
ML Service for MommyShops API
Handles machine learning recommendations and analysis
"""

import logging
from typing import List, Dict, Any, Optional
import asyncio

from ..core.config import get_settings

logger = logging.getLogger(__name__)

class MLService:
    """
    Service for machine learning recommendations
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.model_loaded = False
    
    async def generate_recommendations(self, ingredients_analysis: List[Dict[str, Any]], user_need: str) -> str:
        """
        Generate recommendations based on ingredient analysis
        """
        try:
            if not ingredients_analysis:
                return "No se encontraron ingredientes para analizar."
            
            # Analyze risk levels
            high_risk_count = sum(1 for ing in ingredients_analysis if ing.get("risk_level") in ["riesgo alto", "cancerígeno"])
            medium_risk_count = sum(1 for ing in ingredients_analysis if ing.get("risk_level") == "riesgo medio")
            safe_count = sum(1 for ing in ingredients_analysis if ing.get("risk_level") == "seguro")
            
            # Generate recommendations based on analysis
            recommendations = []
            
            if high_risk_count > 0:
                recommendations.append(f"⚠️ Se encontraron {high_risk_count} ingredientes de alto riesgo. Se recomienda evitar este producto.")
            
            if medium_risk_count > 0:
                recommendations.append(f"⚠️ Se encontraron {medium_risk_count} ingredientes de riesgo medio. Use con precaución.")
            
            if safe_count > 0:
                recommendations.append(f"✅ Se encontraron {safe_count} ingredientes seguros.")
            
            # Add specific recommendations based on user need
            if user_need.lower() in ["pregnancy", "embarazo"]:
                recommendations.append("🤰 Para mujeres embarazadas, evite ingredientes como retinoides, ácido salicílico y parabenos.")
            
            if user_need.lower() in ["sensitive skin", "piel sensible"]:
                recommendations.append("🌿 Para piel sensible, evite fragancias, alcohol y sulfatos.")
            
            if user_need.lower() in ["children", "niños"]:
                recommendations.append("👶 Para niños, use productos con ingredientes suaves y naturales.")
            
            # Add general safety recommendations
            recommendations.append("🔍 Siempre consulte con un dermatólogo antes de usar productos nuevos.")
            recommendations.append("📋 Lea las etiquetas y evite ingredientes que causen alergias.")
            
            return "\n".join(recommendations)
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return "Error al generar recomendaciones. Consulte con un profesional."
    
    async def calculate_product_safety_score(self, ingredients_analysis: List[Dict[str, Any]]) -> float:
        """
        Calculate overall product safety score (0-100)
        """
        try:
            if not ingredients_analysis:
                return 50.0  # Default score
            
            # Calculate weighted average based on risk levels
            total_score = 0
            weight_sum = 0
            
            for ingredient in ingredients_analysis:
                risk_level = ingredient.get("risk_level", "desconocido")
                eco_score = ingredient.get("eco_score", 50.0)
                
                # Risk level weights
                risk_weights = {
                    "seguro": 1.0,
                    "riesgo bajo": 0.8,
                    "riesgo medio": 0.6,
                    "riesgo alto": 0.3,
                    "cancerígeno": 0.1,
                    "desconocido": 0.5
                }
                
                weight = risk_weights.get(risk_level, 0.5)
                total_score += eco_score * weight
                weight_sum += weight
            
            if weight_sum > 0:
                return total_score / weight_sum
            else:
                return 50.0
                
        except Exception as e:
            logger.error(f"Error calculating safety score: {e}")
            return 50.0
    
    async def get_ingredient_substitutes(self, problematic_ingredients: List[str]) -> Dict[str, List[str]]:
        """
        Get substitute ingredients for problematic ones
        """
        try:
            substitutes = {}
            
            # Simple substitution logic
            # This would be more sophisticated in production
            substitution_map = {
                "sodium lauryl sulfate": ["coco-glucoside", "decyl glucoside", "lauryl glucoside"],
                "sodium laureth sulfate": ["coco-glucoside", "decyl glucoside", "lauryl glucoside"],
                "parabens": ["potassium sorbate", "sodium benzoate", "phenoxyethanol"],
                "phthalates": ["natural fragrances", "essential oils"],
                "formaldehyde": ["natural preservatives", "vitamin E", "rosemary extract"],
                "triclosan": ["natural antimicrobials", "tea tree oil", "eucalyptus oil"]
            }
            
            for ingredient in problematic_ingredients:
                ingredient_lower = ingredient.lower()
                found_substitutes = []
                
                for key, values in substitution_map.items():
                    if key in ingredient_lower:
                        found_substitutes.extend(values)
                
                if found_substitutes:
                    substitutes[ingredient] = found_substitutes
            
            return substitutes
            
        except Exception as e:
            logger.error(f"Error getting substitutes: {e}")
            return {}
    
    async def analyze_user_preferences(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze user preferences for personalized recommendations
        """
        try:
            preferences = {
                "skin_type": user_profile.get("skin_type", "normal"),
                "allergies": user_profile.get("allergies", []),
                "pregnancy_status": user_profile.get("pregnancy_status", "not_pregnant"),
                "age_group": user_profile.get("age_group", "adult")
            }
            
            # Generate personalized recommendations
            recommendations = []
            
            if preferences["skin_type"] == "sensitive":
                recommendations.append("Use productos sin fragancias ni alcohol")
            
            if preferences["pregnancy_status"] == "pregnant":
                recommendations.append("Evite retinoides, ácido salicílico y parabenos")
            
            if preferences["age_group"] == "child":
                recommendations.append("Use productos suaves y naturales")
            
            return {
                "preferences": preferences,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error analyzing user preferences: {e}")
            return {
                "preferences": {},
                "recommendations": []
            }
    
    async def rebuild_model(self, model_type: str = "recommendation") -> bool:
        """
        Rebuild ML model
        """
        try:
            # This would rebuild the ML model
            # For now, just log the request
            logger.info(f"Rebuilding {model_type} model")
            return True
            
        except Exception as e:
            logger.error(f"Error rebuilding model: {e}")
            return False

