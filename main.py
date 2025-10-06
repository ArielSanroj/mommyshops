"""
MommyShops - Clean and Optimized Cosmetic Ingredient Analysis System
Streamlined version for Railway deployment with minimal dependencies
"""

from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import httpx
import pytesseract
from PIL import Image, ImageEnhance
import io
import os
import logging
import asyncio
from dotenv import load_dotenv
import json
from typing import Dict, List, Optional
import numpy as np
from contextlib import asynccontextmanager
import re
from database import Ingredient, get_db, get_ingredient_data, get_all_ingredients
from api_utils_production import fetch_ingredient_data, health_check, get_cache_stats
from llm_utils import enrich_ingredient_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check Tesseract availability
TESSERACT_AVAILABLE = True
try:
    tesseract_path = os.getenv("TESSERACT_PATH", "/opt/homebrew/bin/tesseract")
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    pytesseract.get_tesseract_version()
    logger.info(f"✅ Tesseract OCR available at: {tesseract_path}")
except Exception as e:
    TESSERACT_AVAILABLE = False
    logger.error(f"❌ Tesseract not available: {e}")

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Configure connection limits on startup and cleanup on shutdown."""
    # Startup
    try:
        import httpx
        httpx._config.DEFAULT_LIMITS = httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
            keepalive_expiry=30.0
        )
        logger.info("Connection limits configured successfully")
    except Exception as e:
        logger.error(f"Error configuring connection limits: {e}")
    
    yield
    
    # Shutdown
    logger.info("Application shutting down")

# FastAPI app
app = FastAPI(
    title="MommyShops - Cosmetic Ingredient Analysis",
    description="Professional cosmetic ingredient safety analysis",
    version="3.0.0",
    lifespan=lifespan
)

# Pydantic models
class AnalyzeUrlRequest(BaseModel):
    url: str = Field(..., description="URL of the product page")
    user_need: str = Field(default="general safety", description="User's skin need")

class AnalyzeTextRequest(BaseModel):
    text: str = Field(..., description="Text containing ingredients")
    user_need: str = Field(default="general safety", description="User's skin need")

class IngredientAnalysisResponse(BaseModel):
    name: str
    eco_score: float
    risk_level: str
    benefits: str
    risks_detailed: str
    sources: str

class ProductAnalysisResponse(BaseModel):
    product_name: str
    ingredients_details: List[IngredientAnalysisResponse]
    avg_eco_score: float
    suitability: str
    recommendations: str

# Core functions
async def extract_ingredients_from_image(image_data: bytes) -> List[str]:
    """Extract ingredients from image using OCR."""
    try:
        logger.info("Starting image processing...")
        
        if not TESSERACT_AVAILABLE:
            logger.error("Tesseract not available")
            return []
        
        # Load and preprocess image
        image = Image.open(io.BytesIO(image_data))
        logger.info(f"Original image size: {image.size}")
        
        # Simple preprocessing
        if image.mode != 'L':
            image = image.convert('L')
            logger.info("Converted to grayscale")
        
        # Resize if too small
        if max(image.size) < 300:
            scale_factor = 300 / max(image.size)
            new_size = (int(image.size[0] * scale_factor), int(image.size[1] * scale_factor))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            logger.info(f"Resized to: {image.size}")
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        logger.info("Enhanced contrast")
        
        # OCR configurations
        configs = [
            '--psm 6 --oem 3',
            '--psm 3 --oem 3',
            '--psm 4 --oem 3',
            '--psm 8 --oem 3',
            '--psm 6 --oem 1'
        ]
        
        best_ingredients = []
        best_text = ""
        
        for i, config in enumerate(configs):
            try:
                logger.info(f"Trying OCR config {i+1}: {config}")
                
                ocr_result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, 
                        lambda: pytesseract.image_to_string(image, lang='eng', config=config)
                    ),
                    timeout=5.0
                )
                
                if len(ocr_result) > len(best_text):
                    best_text = ocr_result
                    logger.info(f"Better text found with config {i+1}")
                
                ingredients = extract_ingredients_from_text(ocr_result)
                if len(ingredients) > len(best_ingredients):
                    best_ingredients = ingredients
                    logger.info(f"Found {len(ingredients)} ingredients with config {i+1}")
                
            except asyncio.TimeoutError:
                logger.warning(f"OCR config {i+1} timed out")
                continue
            except Exception as e:
                logger.warning(f"OCR config {i+1} failed: {e}")
                continue
        
        logger.info(f"Final ingredients found: {len(best_ingredients)}")
        return best_ingredients[:10]  # Limit to 10 ingredients
        
    except Exception as e:
        logger.error(f"Image processing failed: {e}")
        return []

def extract_ingredients_from_text(text: str) -> List[str]:
    """Extract ingredients from text using simple patterns."""
    if not text:
        return []
    
    # Common patterns for cosmetic ingredients
    patterns = [
        r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b',  # Capitalized words
        r'\b[a-z]+(?:\s+[a-z]+)*\b',  # Lowercase words
        r'\b[A-Z]+(?:\s+[A-Z]+)*\b',  # All caps words
    ]
    
    ingredients = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if (len(match) > 3 and 
                match.lower() not in ['the', 'and', 'for', 'with', 'from', 'this', 'that', 
                                    'ingredients', 'contains', 'may', 'contain', 'product', 
                                    'formula', 'directions', 'usage', 'warning', 'caution']):
                ingredients.append(match.strip())
    
    return list(set(ingredients))

async def analyze_ingredients(ingredients: List[str], user_need: str, db: Session) -> ProductAnalysisResponse:
    """Analyze ingredients and return comprehensive results."""
    try:
        logger.info(f"Analyzing {len(ingredients)} ingredients...")
        
        ingredients_details = []
        total_eco_score = 0
        risk_counts = {"seguro": 0, "riesgo bajo": 0, "riesgo medio": 0, "riesgo alto": 0, "cancerígeno": 0, "desconocido": 0}
        
        for ingredient in ingredients:
            try:
                # Get ingredient data from database
                ingredient_data = get_ingredient_data(ingredient, db)
                
                if ingredient_data:
                    eco_score = ingredient_data.get('eco_score', 50.0)
                    risk_level = ingredient_data.get('risk_level', 'desconocido')
                    benefits = ingredient_data.get('benefits', 'No disponible')
                    risks = ingredient_data.get('risks_detailed', 'No disponible')
                    sources = ingredient_data.get('sources', 'Database')
                else:
                    # Default data for unknown ingredients
                    eco_score = 50.0
                    risk_level = 'desconocido'
                    benefits = 'Datos no disponibles'
                    risks = 'Datos insuficientes para evaluación'
                    sources = 'Análisis básico'
                
                ingredients_details.append(IngredientAnalysisResponse(
                    name=ingredient,
                    eco_score=eco_score,
                    risk_level=risk_level,
                    benefits=benefits,
                    risks_detailed=risks,
                    sources=sources
                ))
                
                total_eco_score += eco_score
                risk_counts[risk_level] += 1
                
            except Exception as e:
                logger.warning(f"Error analyzing ingredient {ingredient}: {e}")
                # Add default data for failed ingredients
                ingredients_details.append(IngredientAnalysisResponse(
                    name=ingredient,
                    eco_score=50.0,
                    risk_level='desconocido',
                    benefits='Error en análisis',
                    risks_detailed='No se pudo analizar',
                    sources='Error'
                ))
                total_eco_score += 50.0
                risk_counts['desconocido'] += 1
        
        # Calculate average eco score
        avg_eco_score = total_eco_score / len(ingredients) if ingredients else 50.0
        
        # Determine suitability
        if risk_counts['cancerígeno'] > 0 or risk_counts['riesgo alto'] > 2:
            suitability = "No"
        elif risk_counts['riesgo alto'] > 0 or risk_counts['riesgo medio'] > 3:
            suitability = "Evaluar"
        else:
            suitability = "Sí"
        
        # Generate recommendations
        recommendations = generate_recommendations(ingredients_details, user_need, avg_eco_score, risk_counts)
        
        return ProductAnalysisResponse(
            product_name="Product Analysis",
            ingredients_details=ingredients_details,
            avg_eco_score=round(avg_eco_score, 1),
            suitability=suitability,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Error in ingredient analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

def generate_recommendations(ingredients: List[IngredientAnalysisResponse], user_need: str, avg_eco_score: float, risk_counts: Dict) -> str:
    """Generate personalized recommendations."""
    recommendations = []
    
    # Eco score recommendations
    if avg_eco_score >= 80:
        recommendations.append("🌱 Excelente puntaje eco-friendly. Producto muy sostenible.")
    elif avg_eco_score >= 60:
        recommendations.append("🌿 Buen puntaje eco-friendly. Producto moderadamente sostenible.")
    else:
        recommendations.append("⚠️ Puntaje eco-friendly bajo. Considera alternativas más sostenibles.")
    
    # Risk-based recommendations
    if risk_counts['cancerígeno'] > 0:
        recommendations.append("🚫 Contiene ingredientes cancerígenos. Evitar uso prolongado.")
    elif risk_counts['riesgo alto'] > 0:
        recommendations.append("🔴 Contiene ingredientes de alto riesgo. Usar con precaución.")
    elif risk_counts['riesgo medio'] > 2:
        recommendations.append("🟠 Múltiples ingredientes de riesgo medio. Monitorear reacciones.")
    
    # User need specific recommendations
    if user_need == "sensitive skin":
        if risk_counts['riesgo alto'] > 0 or risk_counts['riesgo medio'] > 1:
            recommendations.append("👤 No recomendado para piel sensible. Busca alternativas más suaves.")
        else:
            recommendations.append("👤 Aparentemente seguro para piel sensible, pero haz una prueba de parche.")
    elif user_need == "pregnancy":
        if risk_counts['riesgo alto'] > 0 or risk_counts['cancerígeno'] > 0:
            recommendations.append("🤰 No recomendado durante el embarazo. Consulta con tu médico.")
        else:
            recommendations.append("🤰 Aparentemente seguro, pero consulta con tu médico antes de usar.")
    
    return "\n\n".join(recommendations) if recommendations else "Análisis completado. Revisa los ingredientes individuales."

# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "MommyShops API is running", "version": "3.0.0"}

@app.post("/analyze-image", response_model=ProductAnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    user_need: str = Form(default="general safety"),
    db: Session = Depends(get_db)
):
    """Analyze cosmetic product from image."""
    try:
        logger.info(f"Analyzing image: {file.filename}")
        
        # Validate file
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await file.read()
        if len(image_data) == 0:
            raise HTTPException(status_code=400, detail="Empty image file")
        
        # Limit file size for Railway
        max_size = 5 * 1024 * 1024  # 5MB
        if len(image_data) > max_size:
            raise HTTPException(status_code=400, detail="Image too large. Maximum size is 5MB.")
        
        # Extract ingredients
        ingredients = await extract_ingredients_from_image(image_data)
        if not ingredients:
            raise HTTPException(status_code=400, detail="No ingredients detected. Try improving image quality or lighting.")
        
        # Limit ingredients for Railway
        if len(ingredients) > 5:
            logger.info(f"Limiting to first 5 ingredients (found {len(ingredients)})")
            ingredients = ingredients[:5]
        
        # Analyze ingredients
        result = await analyze_ingredients(ingredients, user_need, db)
        result.product_name = f"Product from Image: {file.filename}"
        
        logger.info("Image analysis completed successfully")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing image: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/analyze-text", response_model=ProductAnalysisResponse)
async def analyze_text(request: AnalyzeTextRequest, db: Session = Depends(get_db)):
    """Analyze ingredients from text."""
    try:
        logger.info("Analyzing text input")
        
        # Extract ingredients from text
        ingredients = extract_ingredients_from_text(request.text)
        if not ingredients:
            raise HTTPException(status_code=400, detail="No ingredients found in text")
        
        # Limit ingredients
        if len(ingredients) > 5:
            ingredients = ingredients[:5]
        
        # Analyze ingredients
        result = await analyze_ingredients(ingredients, request.user_need, db)
        result.product_name = "Text Analysis"
        
        logger.info("Text analysis completed successfully")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing text: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health():
    """Health check for all APIs."""
    try:
        health_status = await health_check()
        return {
            "status": "healthy",
            "timestamp": health_status.get("timestamp"),
            "apis": health_status.get("apis", {}),
            "cache_stats": health_status.get("cache_stats", {})
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {"status": "unhealthy", "error": str(e)}

@app.get("/ingredients")
async def get_all_ingredients(db: Session = Depends(get_db)):
    """Get all ingredients from database."""
    try:
        ingredients = get_all_ingredients(db)
        return {"ingredients": ingredients, "count": len(ingredients)}
    except Exception as e:
        logger.error(f"Error getting ingredients: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Run the application
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)