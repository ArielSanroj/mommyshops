"""
Ollama AI integration routes for MommyShops API
Handles AI-powered analysis and recommendations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ...core.database import get_db
from ...core.security import get_current_user_optional
from ...models.requests import OllamaAnalysisRequest, OllamaAlternativesRequest
from ...models.responses import OllamaAnalysisResponse, OllamaAlternativesResponse
from ...services.ollama_service import OllamaService
from ...database import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ollama", tags=["Ollama AI"])

@router.get("/status")
async def get_ollama_status() -> dict:
    """
    Check Ollama service status
    """
    try:
        ollama_service = OllamaService()
        status_info = await ollama_service.get_status()
        
        return {
            "status": "healthy" if status_info["available"] else "unhealthy",
            "available": status_info["available"],
            "models": status_info.get("models", []),
            "version": status_info.get("version", "unknown")
        }
        
    except Exception as e:
        logger.error(f"Error checking Ollama status: {e}")
        return {
            "status": "unhealthy",
            "available": False,
            "error": str(e)
        }

@router.post("/analyze")
async def analyze_with_ollama(
    request: OllamaAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> OllamaAnalysisResponse:
    """
    Analyze ingredients using Ollama AI
    """
    try:
        ollama_service = OllamaService()
        
        # Perform analysis with Ollama
        analysis_result = await ollama_service.analyze_ingredients(
            request.ingredients,
            request.user_conditions,
            request.analysis_type
        )
        
        logger.info(f"Ollama analysis completed for user: {current_user.email if current_user else 'anonymous'}")
        
        return OllamaAnalysisResponse(
            success=True,
            analysis=analysis_result["analysis"],
            confidence=analysis_result["confidence"],
            recommendations=analysis_result["recommendations"],
            processing_time_ms=analysis_result["processing_time_ms"]
        )
        
    except Exception as e:
        logger.error(f"Error in Ollama analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/alternatives")
async def get_alternatives_with_ollama(
    request: OllamaAlternativesRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> OllamaAlternativesResponse:
    """
    Get ingredient alternatives using Ollama AI
    """
    try:
        ollama_service = OllamaService()
        
        # Get alternatives with Ollama
        alternatives_result = await ollama_service.suggest_alternatives(
            request.problematic_ingredients,
            request.user_conditions,
            request.preferences
        )
        
        logger.info(f"Ollama alternatives generated for user: {current_user.email if current_user else 'anonymous'}")
        
        return OllamaAlternativesResponse(
            success=True,
            alternatives=alternatives_result["alternatives"],
            reasoning=alternatives_result["reasoning"],
            confidence=alternatives_result["confidence"],
            processing_time_ms=alternatives_result["processing_time_ms"]
        )
        
    except Exception as e:
        logger.error(f"Error in Ollama alternatives: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/analyze/stream")
async def analyze_with_ollama_stream(
    request: OllamaAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Stream analysis results from Ollama AI
    """
    try:
        ollama_service = OllamaService()
        
        # Stream analysis with Ollama
        async for chunk in ollama_service.analyze_ingredients_stream(
            request.ingredients,
            request.user_conditions,
            request.analysis_type
        ):
            yield chunk
            
    except Exception as e:
        logger.error(f"Error in Ollama streaming analysis: {e}")
        yield {
            "error": "Internal server error",
            "success": False
        }

