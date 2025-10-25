"""
Health check routes for MommyShops API
Provides system health and debugging information
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging
import os
import time

from ...core.database import get_db
from ...services.ollama_service import OllamaService
from ...services.ingredient_service import IngredientService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "mommyshops-api",
        "version": "3.0.1"
    }

@router.get("/debug/env")
async def debug_environment() -> Dict[str, Any]:
    """
    Debug environment variables (sanitized)
    """
    env_vars = {}
    for key, value in os.environ.items():
        if key.startswith(('MYSQL', 'POSTGRES', 'REDIS', 'API', 'KEY', 'SECRET', 'TOKEN')):
            env_vars[key] = "***HIDDEN***"
        else:
            env_vars[key] = value
    
    return {
        "environment": env_vars,
        "python_version": os.sys.version,
        "platform": os.name
    }

@router.get("/debug/simple")
async def debug_simple() -> Dict[str, Any]:
    """
    Simple debug information
    """
    return {
        "status": "ok",
        "message": "Simple debug endpoint working",
        "timestamp": time.time()
    }

@router.get("/debug/tesseract")
async def debug_tesseract() -> Dict[str, Any]:
    """
    Debug Tesseract OCR availability
    """
    try:
        import pytesseract
        from PIL import Image
        import io
        
        # Test Tesseract with a simple image
        test_image = Image.new('RGB', (100, 100), color='white')
        test_buffer = io.BytesIO()
        test_image.save(test_buffer, format='PNG')
        test_buffer.seek(0)
        
        # Try to extract text
        text = pytesseract.image_to_string(test_image)
        
        return {
            "status": "available",
            "tesseract_version": pytesseract.get_tesseract_version(),
            "test_result": "success",
            "extracted_text": text.strip()
        }
        
    except Exception as e:
        return {
            "status": "unavailable",
            "error": str(e),
            "tesseract_available": False
        }

@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Detailed health check with component status
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "mommyshops-api",
        "version": "3.0.1",
        "components": {}
    }
    
    # Check database
    try:
        db.execute("SELECT 1")
        health_status["components"]["database"] = {
            "status": "healthy",
            "type": "postgresql"
        }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check Ollama
    try:
        ollama_service = OllamaService()
        ollama_status = await ollama_service.get_status()
        health_status["components"]["ollama"] = {
            "status": "healthy" if ollama_status["available"] else "unhealthy",
            "available": ollama_status["available"],
            "models": ollama_status.get("models", [])
        }
    except Exception as e:
        health_status["components"]["ollama"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check external APIs
    try:
        ingredient_service = IngredientService(db)
        api_status = await ingredient_service.check_external_apis()
        health_status["components"]["external_apis"] = {
            "status": "healthy" if api_status["all_available"] else "degraded",
            "apis": api_status["apis"]
        }
    except Exception as e:
        health_status["components"]["external_apis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    return health_status

