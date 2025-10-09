"""
FastAPI endpoints for enhanced substitution mapping
Integrates with existing MommyShops API structure
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from substitution_api_integration import (
    enhanced_substitute_analysis,
    get_safer_alternatives,
    batch_substitute_analysis,
    enhance_existing_recommendations
)

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class IngredientAnalysisRequest(BaseModel):
    ingredients: List[str] = Field(..., description="List of ingredients to analyze")
    user_conditions: Optional[List[str]] = Field(None, description="User's skin conditions or concerns")
    include_safety_analysis: bool = Field(True, description="Include detailed safety analysis")

class SaferAlternativesRequest(BaseModel):
    ingredients: List[str] = Field(..., description="List of ingredients to find alternatives for")
    user_conditions: Optional[List[str]] = Field(None, description="User's skin conditions or concerns")

class BatchAnalysisRequest(BaseModel):
    ingredient_batches: List[List[str]] = Field(..., description="Multiple batches of ingredients to analyze")
    user_conditions: Optional[List[str]] = Field(None, description="User's skin conditions or concerns")

class SubstitutionCandidate(BaseModel):
    ingredient: str
    similarity_score: float
    safety_improvement: float
    functional_similarity: float
    eco_improvement: float
    risk_reduction: float
    reason: str
    confidence: float
    sources: List[str]

class SubstitutionMapping(BaseModel):
    original: str
    substitutes: List[SubstitutionCandidate]
    safety_justification: str
    functional_equivalence: float
    confidence_score: float
    last_updated: str

class SafetyAnalysis(BaseModel):
    ingredient: str
    safety_score: float
    risk_level: str
    eco_score: float
    is_problematic: bool
    sources: List[str]
    risks_detailed: str
    benefits: str

class AnalysisSummary(BaseModel):
    total_ingredients_analyzed: int
    safe_ingredients: int
    problematic_ingredients: int
    average_safety_score: float
    ingredients_with_substitutes: int
    total_substitute_options: int
    recommendation: str

class EnhancedAnalysisResponse(BaseModel):
    analysis_timestamp: str
    total_ingredients: int
    problematic_ingredients: int
    safety_analysis: List[SafetyAnalysis]
    substitution_mappings: Dict[str, SubstitutionMapping]
    product_recommendations: List[Dict[str, Any]]
    summary: AnalysisSummary

# Create router
router = APIRouter(prefix="/substitution", tags=["Enhanced Substitution"])

@router.post("/analyze", response_model=EnhancedAnalysisResponse)
async def analyze_ingredients_for_substitution(request: IngredientAnalysisRequest):
    """
    Comprehensive ingredient analysis with ML-powered substitution suggestions.
    
    This endpoint analyzes ingredients for safety issues and provides intelligent
    substitution recommendations using machine learning and multiple cosmetic safety standards.
    """
    try:
        logger.info(f"Analyzing {len(request.ingredients)} ingredients for substitutions")
        
        result = await enhanced_substitute_analysis(
            ingredients=request.ingredients,
            user_conditions=request.user_conditions,
            include_safety_analysis=request.include_safety_analysis
        )
        
        return EnhancedAnalysisResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in ingredient analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/alternatives", response_model=List[Dict[str, Any]])
async def get_safer_ingredient_alternatives(request: SaferAlternativesRequest):
    """
    Get safer alternatives for problematic ingredients.
    
    Uses ML-based analysis to find functionally similar but safer ingredients
    based on multiple cosmetic safety standards.
    """
    try:
        logger.info(f"Finding safer alternatives for {len(request.ingredients)} ingredients")
        
        alternatives = await get_safer_alternatives(
            ingredients=request.ingredients,
            user_conditions=request.user_conditions
        )
        
        return alternatives
        
    except Exception as e:
        logger.error(f"Error finding alternatives: {e}")
        raise HTTPException(status_code=500, detail=f"Alternative search failed: {str(e)}")

@router.post("/batch-analyze", response_model=List[EnhancedAnalysisResponse])
async def batch_analyze_ingredients(request: BatchAnalysisRequest):
    """
    Batch analysis of multiple ingredient lists.
    
    Useful for analyzing multiple products or routines simultaneously.
    """
    try:
        logger.info(f"Batch analyzing {len(request.ingredient_batches)} ingredient lists")
        
        results = await batch_substitute_analysis(
            ingredient_batches=request.ingredient_batches,
            user_conditions=request.user_conditions
        )
        
        return [EnhancedAnalysisResponse(**result) for result in results]
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")

@router.post("/enhance-recommendations", response_model=List[Dict[str, Any]])
async def enhance_product_recommendations(
    recommendations: List[Dict[str, Any]],
    user_conditions: Optional[List[str]] = None
):
    """
    Enhance existing product recommendations with substitution analysis.
    
    Takes existing product recommendations and adds substitution analysis
    to help users understand safer alternatives.
    """
    try:
        logger.info(f"Enhancing {len(recommendations)} product recommendations")
        
        enhanced = await enhance_existing_recommendations(
            existing_recommendations=recommendations,
            user_conditions=user_conditions
        )
        
        return enhanced
        
    except Exception as e:
        logger.error(f"Error enhancing recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Enhancement failed: {str(e)}")

@router.get("/health")
async def substitution_health_check():
    """
    Health check for the substitution system.
    
    Verifies that the ML models and safety databases are accessible.
    """
    try:
        # Test with a simple ingredient
        test_result = await enhanced_substitute_analysis(
            ingredients=["glycerin"],
            user_conditions=None
        )
        
        return {
            "status": "healthy",
            "ml_models_loaded": True,
            "safety_databases_accessible": True,
            "test_analysis_successful": True,
            "timestamp": test_result.get("analysis_timestamp")
        }
        
    except Exception as e:
        logger.error(f"Substitution health check failed: {e}")
        return {
            "status": "unhealthy",
            "ml_models_loaded": False,
            "safety_databases_accessible": False,
            "test_analysis_successful": False,
            "error": str(e)
        }

@router.get("/safety-standards")
async def get_supported_safety_standards():
    """
    Get information about supported cosmetic safety standards.
    
    Returns details about the safety standards used in the substitution analysis.
    """
    return {
        "supported_standards": [
            {
                "name": "FDA",
                "description": "Food and Drug Administration",
                "weight": 0.3,
                "focus": "Regulatory approval and safety"
            },
            {
                "name": "EWG",
                "description": "Environmental Working Group",
                "weight": 0.25,
                "focus": "Eco-friendliness and consumer safety"
            },
            {
                "name": "CIR",
                "description": "Cosmetic Ingredient Review",
                "weight": 0.2,
                "focus": "Scientific safety assessment"
            },
            {
                "name": "SCCS",
                "description": "Scientific Committee on Consumer Safety",
                "weight": 0.15,
                "focus": "EU safety evaluation"
            },
            {
                "name": "ICCR",
                "description": "International Cooperation on Cosmetics Regulation",
                "weight": 0.1,
                "focus": "International harmonization"
            }
        ],
        "functional_categories": [
            "emollients", "humectants", "emulsifiers", "preservatives",
            "antioxidants", "surfactants", "fragrance", "colorants"
        ],
        "ml_models": [
            "sentence-transformers (all-MiniLM-L6-v2)",
            "TF-IDF vectorization",
            "cosine similarity matching"
        ]
    }

@router.post("/quick-substitute")
async def quick_substitute_lookup(
    ingredient: str,
    user_conditions: Optional[List[str]] = None,
    max_substitutes: int = 5
):
    """
    Quick substitution lookup for a single ingredient.
    
    Fast lookup for getting substitute recommendations for a single ingredient.
    """
    try:
        logger.info(f"Quick substitute lookup for: {ingredient}")
        
        result = await enhanced_substitute_analysis(
            ingredients=[ingredient],
            user_conditions=user_conditions
        )
        
        # Extract just the substitution data
        substitution_data = result.get("substitution_mappings", {}).get(ingredient)
        
        if not substitution_data:
            return {
                "ingredient": ingredient,
                "substitutes": [],
                "message": "No substitutes found or ingredient is already safe"
            }
        
        # Limit to requested number of substitutes
        limited_substitutes = substitution_data["substitutes"][:max_substitutes]
        
        return {
            "ingredient": ingredient,
            "substitutes": limited_substitutes,
            "safety_justification": substitution_data["safety_justification"],
            "confidence_score": substitution_data["confidence_score"],
            "functional_equivalence": substitution_data["functional_equivalence"]
        }
        
    except Exception as e:
        logger.error(f"Error in quick substitute lookup: {e}")
        raise HTTPException(status_code=500, detail=f"Quick lookup failed: {str(e)}")

# Integration with existing recommendation endpoints
@router.post("/integrate-with-routine-analysis")
async def integrate_with_routine_analysis(
    routine_data: Dict[str, Any],
    user_conditions: Optional[List[str]] = None
):
    """
    Integrate substitution analysis with existing routine analysis.
    
    This endpoint can be called from your existing routine analysis to add
    substitution recommendations to the results.
    """
    try:
        # Extract ingredients from routine data
        ingredients = []
        if "products" in routine_data:
            for product in routine_data["products"]:
                if "ingredients" in product:
                    ingredients.extend(product["ingredients"])
        
        if not ingredients:
            return {
                "message": "No ingredients found in routine data",
                "substitution_analysis": {}
            }
        
        # Get substitution analysis
        substitution_result = await enhanced_substitute_analysis(
            ingredients=ingredients,
            user_conditions=user_conditions
        )
        
        # Return integration-ready data
        return {
            "routine_data": routine_data,
            "substitution_analysis": substitution_result,
            "integration_timestamp": substitution_result["analysis_timestamp"]
        }
        
    except Exception as e:
        logger.error(f"Error integrating with routine analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Integration failed: {str(e)}")

# Export the router for use in main.py
__all__ = ["router"]