"""
Endpoints específicos para integración con Java Spring Boot
Estos endpoints están optimizados para comunicación Java-Python
"""

from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging
import time
from datetime import datetime

# Import existing services
from main import (
    analyze_image as analyze_image_main,
    analyze_text as analyze_text_main,
    get_current_user_optional,
    get_db
)
from database import SessionLocal
from api_utils_production import fetch_ingredient_data
from ollama_integration import (
    analyze_ingredients_with_ollama,
    suggest_alternatives_with_ollama
)

logger = logging.getLogger(__name__)

# Create router for Java integration
java_router = APIRouter(prefix="/java", tags=["Java Integration"])

# Response models optimized for Java
class JavaIngredientAnalysis:
    def __init__(self, name: str, risk_level: str, eco_score: float, 
                 benefits: str, risks_detailed: str, sources: str):
        self.name = name
        self.riskLevel = risk_level
        self.ecoScore = eco_score
        self.benefits = benefits
        self.risksDetailed = risks_detailed
        self.sources = sources
        self.function = ""
        self.origin = ""
        self.concerns = []
        self.isNatural = None
        self.casNumber = ""
        self.inciName = name

class JavaProductAnalysisResponse:
    def __init__(self, success: bool, error: str = None, product_name: str = None,
                 ingredients_details: List[JavaIngredientAnalysis] = None,
                 avg_eco_score: float = None, suitability: str = None,
                 recommendations: str = None, analysis_id: str = None,
                 processing_time_ms: int = None):
        self.success = success
        self.error = error
        self.productName = product_name
        self.ingredientsDetails = ingredients_details or []
        self.avgEcoScore = avg_eco_score
        self.suitability = suitability
        self.recommendations = recommendations
        self.analysisId = analysis_id
        self.processingTimeMs = processing_time_ms

@java_router.post("/analyze-image")
async def java_analyze_image(
    file: UploadFile = File(...),
    user_need: str = Form(default="general safety"),
    db: Session = Depends(get_db)
) -> JavaProductAnalysisResponse:
    """
    Endpoint optimizado para Java - Análisis de imagen
    """
    start_time = time.time()
    
    try:
        # Call main analysis function
        result = await analyze_image_main(file, user_need, db)
        
        # Convert to Java-optimized format
        ingredients_details = []
        if result.get("ingredients_details"):
            for ingredient in result["ingredients_details"]:
                java_ingredient = JavaIngredientAnalysis(
                    name=ingredient.get("name", ""),
                    risk_level=ingredient.get("risk_level", "desconocido"),
                    eco_score=float(ingredient.get("eco_score", 50.0)),
                    benefits=ingredient.get("benefits", "No disponible"),
                    risks_detailed=ingredient.get("risks_detailed", "No disponible"),
                    sources=ingredient.get("sources", "Python Backend")
                )
                ingredients_details.append(java_ingredient)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return JavaProductAnalysisResponse(
            success=True,
            product_name=result.get("product_name", "Producto analizado"),
            ingredients_details=ingredients_details,
            avg_eco_score=result.get("avg_eco_score", 50.0),
            suitability=result.get("suitability", "Análisis completado"),
            recommendations=result.get("recommendations", "Consulta con un profesional"),
            analysis_id=f"java_{int(time.time())}",
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error in Java image analysis: {e}")
        return JavaProductAnalysisResponse(
            success=False,
            error=str(e),
            processing_time_ms=int((time.time() - start_time) * 1000)
        )

@java_router.post("/analyze-text")
async def java_analyze_text(
    text: str = Form(...),
    user_need: str = Form(default="general safety"),
    db: Session = Depends(get_db)
) -> JavaProductAnalysisResponse:
    """
    Endpoint optimizado para Java - Análisis de texto
    """
    start_time = time.time()
    
    try:
        # Call main text analysis function
        result = await analyze_text_main(text, user_need, db)
        
        # Convert to Java-optimized format
        ingredients_details = []
        if result.get("ingredients_details"):
            for ingredient in result["ingredients_details"]:
                java_ingredient = JavaIngredientAnalysis(
                    name=ingredient.get("name", ""),
                    risk_level=ingredient.get("risk_level", "desconocido"),
                    eco_score=float(ingredient.get("eco_score", 50.0)),
                    benefits=ingredient.get("benefits", "No disponible"),
                    risks_detailed=ingredient.get("risks_detailed", "No disponible"),
                    sources=ingredient.get("sources", "Python Backend")
                )
                ingredients_details.append(java_ingredient)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return JavaProductAnalysisResponse(
            success=True,
            product_name=result.get("product_name", "Producto analizado"),
            ingredients_details=ingredients_details,
            avg_eco_score=result.get("avg_eco_score", 50.0),
            suitability=result.get("suitability", "Análisis completado"),
            recommendations=result.get("recommendations", "Consulta con un profesional"),
            analysis_id=f"java_{int(time.time())}",
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error in Java text analysis: {e}")
        return JavaProductAnalysisResponse(
            success=False,
            error=str(e),
            processing_time_ms=int((time.time() - start_time) * 1000)
        )

@java_router.post("/ingredient-analysis")
async def java_ingredient_analysis(
    ingredient: str = Form(...),
    db: Session = Depends(get_db)
) -> JavaIngredientAnalysis:
    """
    Endpoint optimizado para Java - Análisis de ingrediente individual
    """
    try:
        # Get ingredient data from external APIs
        ingredient_data = await fetch_ingredient_data(ingredient, None)
        
        return JavaIngredientAnalysis(
            name=ingredient_data.get("name", ingredient),
            risk_level=ingredient_data.get("risk_level", "desconocido"),
            eco_score=float(ingredient_data.get("eco_score", 50.0)),
            benefits=ingredient_data.get("benefits", "No disponible"),
            risks_detailed=ingredient_data.get("risks_detailed", "No disponible"),
            sources=ingredient_data.get("sources", "Python Backend")
        )
        
    except Exception as e:
        logger.error(f"Error in Java ingredient analysis: {e}")
        return JavaIngredientAnalysis(
            name=ingredient,
            risk_level="desconocido",
            eco_score=50.0,
            benefits="No disponible",
            risks_detailed=f"Error: {str(e)}",
            sources="Error"
        )

@java_router.post("/alternatives")
async def java_get_alternatives(
    problematic_ingredients: List[str] = Form(...),
    user_conditions: List[str] = Form(default=[]),
    db: Session = Depends(get_db)
) -> List[str]:
    """
    Endpoint optimizado para Java - Obtener alternativas con Ollama
    """
    try:
        # Use Ollama to suggest alternatives
        alternatives_result = await suggest_alternatives_with_ollama(
            problematic_ingredients, user_conditions
        )
        
        if alternatives_result.success:
            # Parse alternatives from Ollama response
            alternatives = []
            content = alternatives_result.content or ""
            
            # Simple parsing - in production, use more sophisticated parsing
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('*'):
                    # Clean up the line
                    clean_line = line.replace('•', '').replace('-', '').strip()
                    if clean_line and len(clean_line) > 2:
                        alternatives.append(clean_line)
            
            return alternatives[:5]  # Return top 5 alternatives
        else:
            return ["Servicio no disponible temporalmente"]
            
    except Exception as e:
        logger.error(f"Error in Java alternatives: {e}")
        return ["Error al obtener alternativas"]

@java_router.get("/health")
async def java_health_check() -> Dict[str, Any]:
    """
    Health check optimizado para Java
    """
    try:
        # Check basic services
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "python-backend",
            "version": "3.0.1",
            "components": {
                "database": "healthy",
                "ollama": "checking",
                "external_apis": "checking"
            }
        }
        
        # Check Ollama availability
        try:
            from ollama_integration import ollama_integration
            if ollama_integration.is_available():
                health_status["components"]["ollama"] = "healthy"
            else:
                health_status["components"]["ollama"] = "unhealthy"
        except Exception:
            health_status["components"]["ollama"] = "unavailable"
        
        # Check external APIs
        try:
            from api_utils_production import health_check
            api_health = await health_check()
            health_status["components"]["external_apis"] = "healthy" if api_health else "degraded"
        except Exception:
            health_status["components"]["external_apis"] = "unavailable"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error in Java health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "service": "python-backend"
        }

# Include the router in main app
# This will be added to main.py

