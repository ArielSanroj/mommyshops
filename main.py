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
from PIL import Image, ImageEnhance, ImageOps
import io
import os
import logging
import asyncio
from dotenv import load_dotenv
import json
from typing import Dict, List, Optional
import numpy as np
from contextlib import asynccontextmanager
from collections import defaultdict
import shutil
import re
from difflib import SequenceMatcher
from database import Ingredient, get_db, get_ingredient_data, get_all_ingredients
from api_utils_production import fetch_ingredient_data, health_check, get_cache_stats
from llm_utils import enrich_ingredient_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_SIZE", 5 * 1024 * 1024))
MAX_ANALYZED_INGREDIENTS = int(os.getenv("MAX_ANALYZED_INGREDIENTS", 5))
MAX_OCR_INGREDIENTS = int(os.getenv("MAX_OCR_INGREDIENTS", 10))
ALLOWED_USER_NEEDS = {"general safety", "sensitive skin", "pregnancy"}
DEFAULT_USER_NEED = "general safety"
STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that", "ingredients",
    "contains", "may", "contain", "product", "formula", "directions",
    "usage", "warning", "caution"
}


def _normalize_ingredient_key(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9\s-]", " ", value.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


LEXICON_PATH = os.getenv(
    "INGREDIENT_LEXICON_PATH",
    os.path.join(BASE_DIR, "cosmetic_ingredients_lexicon.txt")
)
INGREDIENT_LEXICON: Dict[str, str] = {}
try:
    with open(LEXICON_PATH, "r", encoding="utf-8") as lexicon_file:
        for line in lexicon_file:
            entry = line.strip()
            if not entry:
                continue
            normalized_entry = _normalize_ingredient_key(entry)
            if normalized_entry:
                INGREDIENT_LEXICON[normalized_entry] = entry
    if INGREDIENT_LEXICON:
        logger.info("Ingredient lexicon loaded: %d entries", len(INGREDIENT_LEXICON))
except FileNotFoundError:
    logger.warning("Ingredient lexicon file not found at %s", LEXICON_PATH)

INGREDIENT_LEXICON_INDEX: Dict[str, List[tuple[str, str]]] = defaultdict(list)
for normalized_entry, canonical_entry in INGREDIENT_LEXICON.items():
    if not normalized_entry:
        continue
    first_char = normalized_entry[0]
    INGREDIENT_LEXICON_INDEX[first_char].append((normalized_entry, canonical_entry))


def configure_tesseract() -> bool:
    configured_path = os.getenv("TESSERACT_PATH")
    candidate_paths = [configured_path] if configured_path else []
    candidate_paths.extend([
        "/opt/homebrew/bin/tesseract",
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
    ])

    resolved_path = None
    for path in candidate_paths:
        if path and os.path.isfile(path):
            resolved_path = path
            break

    if not resolved_path:
        resolved_path = shutil.which("tesseract")
        if not resolved_path:
            logger.error("Tesseract executable not found in any known location")
            return False

    try:
        pytesseract.pytesseract.tesseract_cmd = resolved_path
        pytesseract.get_tesseract_version()
        logger.info("Tesseract OCR available at: %s", resolved_path)
        return True
    except Exception as exc:
        logger.error("Tesseract not available: %s", exc)
        return False


TESSERACT_AVAILABLE = configure_tesseract()

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
    """Extract ingredients from image using enhanced OCR with better preprocessing."""
    try:
        logger.info("Starting enhanced image processing...")
        
        if not TESSERACT_AVAILABLE:
            logger.error("Tesseract not available")
            return []
        
        # Load and preprocess image
        image = Image.open(io.BytesIO(image_data))
        logger.info(f"Original image size: {image.size}")
        
        # Enhanced preprocessing for better OCR
        processed_images = []
        
        # 1. Original image
        processed_images.append(("original", image.copy()))
        
        # 2. Grayscale with high contrast
        if image.mode != 'L':
            gray = image.convert('L')
        else:
            gray = image.copy()
        
        # Resize for better OCR (OCR works better on larger images)
        if max(gray.size) < 600:
            scale_factor = 600 / max(gray.size)
            new_size = (int(gray.size[0] * scale_factor), int(gray.size[1] * scale_factor))
            gray = gray.resize(new_size, Image.Resampling.LANCZOS)
            logger.info(f"Resized to: {gray.size}")
        
        # High contrast
        enhancer = ImageEnhance.Contrast(gray)
        high_contrast = enhancer.enhance(2.0)
        processed_images.append(("high_contrast", high_contrast))
        
        # 3. Inverted colors (for dark text on light background)
        inverted = ImageOps.invert(high_contrast)
        processed_images.append(("inverted", inverted))
        
        # 4. Sharpened image
        enhancer = ImageEnhance.Sharpness(high_contrast)
        sharpened = enhancer.enhance(2.0)
        processed_images.append(("sharpened", sharpened))
        
        # 5. Auto contrast
        auto_contrast = ImageOps.autocontrast(high_contrast, cutoff=2)
        processed_images.append(("auto_contrast", auto_contrast))
        
        # Try OCR on multiple processed images with different configurations
        all_ingredients = []
        
        # OCR configurations optimized for ingredient lists
        configs = [
            '--psm 6 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,-()[]/',
            '--psm 3 --oem 3',
            '--psm 4 --oem 3',
            '--psm 8 --oem 3',
            '--psm 6 --oem 1'
        ]
        
        for img_name, processed_img in processed_images:
            logger.info(f"Processing {img_name} image...")
            
            for i, config in enumerate(configs):
                try:
                    logger.info(f"Trying {img_name} with config {i+1}: {config}")
                    
                    ocr_result = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, 
                            lambda: pytesseract.image_to_string(processed_img, lang='eng', config=config)
                        ),
                        timeout=8.0
                    )
                    
                    if ocr_result.strip():
                        logger.info(f"OCR result from {img_name} config {i+1}: {len(ocr_result)} characters")
                        ingredients = extract_ingredients_from_text(ocr_result)
                        if ingredients:
                            all_ingredients.extend(ingredients)
                            logger.info(f"Found {len(ingredients)} ingredients from {img_name} config {i+1}")
                
                except asyncio.TimeoutError:
                    logger.warning(f"OCR {img_name} config {i+1} timed out")
                    continue
                except Exception as e:
                    logger.warning(f"OCR {img_name} config {i+1} failed: {e}")
                    continue
        
        # Clean and deduplicate ingredients
        cleaned_ingredients = clean_and_deduplicate_ingredients(all_ingredients)
        logger.info(f"Final cleaned ingredients: {len(cleaned_ingredients)}")
        
        return cleaned_ingredients[:MAX_OCR_INGREDIENTS]
        
    except Exception as e:
        logger.error(f"Image processing failed: {e}")
        return []

def clean_and_deduplicate_ingredients(ingredients: List[str]) -> List[str]:
    """Clean and deduplicate ingredients, removing corrupted text."""
    cleaned = []
    seen = set()
    
    for ingredient in ingredients:
        if not ingredient or len(ingredient.strip()) < 2:
            continue
            
        # Clean the ingredient
        cleaned_ingredient = clean_ingredient_text(ingredient.strip())
        
        if not cleaned_ingredient or len(cleaned_ingredient) < 2:
            continue
            
        # Skip if it's mostly corrupted characters
        if is_corrupted_text(cleaned_ingredient):
            continue
            
        # Check for duplicates using fuzzy matching
        is_duplicate = False
        for existing in cleaned:
            if SequenceMatcher(None, cleaned_ingredient.lower(), existing.lower()).ratio() > 0.8:
                is_duplicate = True
                break
                
        if not is_duplicate:
            cleaned.append(cleaned_ingredient)
            seen.add(cleaned_ingredient.lower())
    
    return cleaned

def clean_ingredient_text(text: str) -> str:
    """Clean corrupted ingredient text."""
    # Remove common OCR artifacts
    text = re.sub(r'[^\w\s\-.,()\[\]/]', '', text)  # Keep only alphanumeric, spaces, and common punctuation
    text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single space
    text = re.sub(r'^[^a-zA-Z]*', '', text)  # Remove leading non-letters
    text = re.sub(r'[^a-zA-Z]*$', '', text)  # Remove trailing non-letters
    
    # Fix common OCR mistakes
    corrections = {
        r'\b0\b': 'O',  # Zero to O
        r'\b1\b': 'I',  # One to I
        r'\b5\b': 'S',  # Five to S
        r'\b8\b': 'B',  # Eight to B
        r'[|]': 'I',    # Pipe to I
        r'[`\']': '',   # Remove quotes
        r'[{}]': '',    # Remove braces
    }
    
    for pattern, replacement in corrections.items():
        text = re.sub(pattern, replacement, text)
    
    return text.strip()

def is_corrupted_text(text: str) -> bool:
    """Check if text is too corrupted to be useful."""
    if len(text) < 3:
        return True
        
    # Check for too many special characters
    special_chars = sum(1 for c in text if not c.isalnum() and c not in ' -.,()[]/')
    if special_chars > len(text) * 0.3:  # More than 30% special chars
        return True
        
    # Check for too many numbers (ingredients rarely have many numbers)
    numbers = sum(1 for c in text if c.isdigit())
    if numbers > len(text) * 0.4:  # More than 40% numbers
        return True
        
    # Check for repeated characters
    if len(set(text)) < len(text) * 0.5:  # Less than 50% unique characters
        return True

    words = [word for word in re.split(r'\s+', text) if word]
    if not words:
        return True

    if not any(len(re.sub(r'[^A-Za-z]', '', word)) >= 3 for word in words) and not is_likely_ci_code(text):
        return True

    alphabetic_chars = sum(1 for c in text if c.isalpha())
    if alphabetic_chars < 3 and not is_likely_ci_code(text):
        return True
        
    return False


def is_likely_ci_code(text: str) -> bool:
    candidate = re.sub(r'\s+', '', text.upper())
    return bool(re.match(r'^CI\d{5}$', candidate))


def resolve_canonical_ingredient(cleaned_candidate: str) -> Optional[str]:
    normalized_candidate = _normalize_ingredient_key(cleaned_candidate)
    if not normalized_candidate or normalized_candidate in STOPWORDS:
        return None

    canonical = INGREDIENT_LEXICON.get(normalized_candidate)
    if canonical:
        return canonical

    compact_key = normalized_candidate.replace(" ", "")
    canonical = INGREDIENT_LEXICON.get(compact_key)
    if canonical:
        return canonical

    first_char = normalized_candidate[0]
    candidates = INGREDIENT_LEXICON_INDEX.get(first_char, [])
    best_ratio = 0.0
    best_match = None

    for candidate_key, candidate_value in candidates:
        if abs(len(candidate_key) - len(normalized_candidate)) > 6:
            continue
        ratio = SequenceMatcher(None, normalized_candidate, candidate_key).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = candidate_value
        if ratio >= 0.95:
            break

    if best_ratio >= 0.88:
        return best_match

    return None

def extract_ingredients_from_text(text: str) -> List[str]:
    """Extract ingredients from text using enhanced parsing with better cleaning."""
    if not text:
        return []

    # Split by common separators
    segments = re.split(r"[\n,;•·\-|()\[\]]+", text)
    seen = set()
    results: List[str] = []

    for segment in segments:
        candidate = segment.strip()
        if not candidate or len(candidate) < 2:
            continue

        # Skip if it's corrupted text
        if is_corrupted_text(candidate):
            continue

        # Clean the candidate
        cleaned_candidate = clean_ingredient_text(candidate)
        if not cleaned_candidate or len(cleaned_candidate) < 2:
            continue

        canonical = resolve_canonical_ingredient(cleaned_candidate)
        normalized_candidate = _normalize_ingredient_key(canonical or cleaned_candidate)

        value = canonical or cleaned_candidate
        key = canonical.lower() if canonical else normalized_candidate

        # Skip if too short, stopword, or duplicate
        if len(key) <= 2 or key in STOPWORDS or key in seen:
            continue

        seen.add(key)
        results.append(value)

    if results:
        return results

    fallback_matches = re.findall(r"\b[A-Za-z][A-Za-z-]+(?:\s+[A-Za-z][A-Za-z-]+)*\b", text)
    fallback_results = []
    for match in fallback_matches:
        normalized_match = _normalize_ingredient_key(match)
        if len(normalized_match) <= 3 or normalized_match in STOPWORDS or normalized_match in seen:
            continue
        canonical = resolve_canonical_ingredient(match)
        seen.add(normalized_match)
        fallback_results.append(canonical or match.strip())
    return fallback_results

async def analyze_ingredients(ingredients: List[str], user_need: str, db: Session) -> ProductAnalysisResponse:
    """Analyze ingredients and return comprehensive results."""
    try:
        logger.info(f"Analyzing {len(ingredients)} ingredients...")
        
        ingredients_details = []
        ingredient_cache: Dict[str, Optional[dict]] = {}
        total_eco_score = 0
        risk_counts = defaultdict(int, {
            "seguro": 0,
            "riesgo bajo": 0,
            "riesgo medio": 0,
            "riesgo alto": 0,
            "cancerígeno": 0,
            "desconocido": 0
        })
        
        for ingredient in ingredients:
            try:
                # Get ingredient data from database
                normalized_name = ingredient.lower()
                if normalized_name in ingredient_cache:
                    ingredient_data = ingredient_cache[normalized_name]
                else:
                    # Use fetch_ingredient_data which checks local DB first, then external APIs
                    logger.info(f"Fetching data for ingredient: {ingredient}")
                    try:
                        async with httpx.AsyncClient() as client:
                            ingredient_data = await fetch_ingredient_data(ingredient, client)
                        logger.info(f"Fetched data for {ingredient}: {ingredient_data}")
                    except Exception as e:
                        logger.error(f"Error fetching data for {ingredient}: {e}")
                        ingredient_data = None
                    ingredient_cache[normalized_name] = ingredient_data
                
                if ingredient_data and ingredient_data.get('eco_score') is not None:
                    eco_score = ingredient_data.get('eco_score', 50.0)
                    risk_level = ingredient_data.get('risk_level', 'desconocido')
                    benefits = ingredient_data.get('benefits', 'No disponible')
                    risks = ingredient_data.get('risks_detailed', 'No disponible')
                    sources = ingredient_data.get('sources', 'Database')
                    logger.info(f"Using data for {ingredient}: eco_score={eco_score}, risk_level={risk_level}")
                else:
                    # Default data for unknown ingredients
                    logger.warning(f"No data found for ingredient: {ingredient}")
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
        recommendations.append("Excelente puntaje eco-friendly; producto muy sostenible.")
    elif avg_eco_score >= 60:
        recommendations.append("Buen puntaje eco-friendly; producto moderadamente sostenible.")
    else:
        recommendations.append("Puntaje eco-friendly bajo; considera alternativas más sostenibles.")
    
    # Risk-based recommendations
    if risk_counts['cancerígeno'] > 0:
        recommendations.append("Contiene ingredientes cancerígenos; evitar uso prolongado.")
    elif risk_counts['riesgo alto'] > 0:
        recommendations.append("Contiene ingredientes de alto riesgo; usar con precaución.")
    elif risk_counts['riesgo medio'] > 2:
        recommendations.append("Múltiples ingredientes de riesgo medio; monitorear reacciones.")
    
    # User need specific recommendations
    if user_need == "sensitive skin":
        if risk_counts['riesgo alto'] > 0 or risk_counts['riesgo medio'] > 1:
            recommendations.append("No recomendado para piel sensible; busca alternativas más suaves.")
        else:
            recommendations.append("Aparentemente seguro para piel sensible; realiza una prueba de parche.")
    elif user_need == "pregnancy":
        if risk_counts['riesgo alto'] > 0 or risk_counts['cancerígeno'] > 0:
            recommendations.append("No recomendado durante el embarazo; consulta con tu médico.")
        else:
            recommendations.append("Aparentemente seguro durante el embarazo; consulta con tu médico antes de usar.")
    
    return "\n\n".join(recommendations) if recommendations else "Análisis completado. Revisa los ingredientes individuales."


def normalize_user_need(user_need: Optional[str]) -> str:
    if not user_need:
        return DEFAULT_USER_NEED
    normalized = user_need.strip().lower()
    return normalized if normalized in ALLOWED_USER_NEEDS else DEFAULT_USER_NEED

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
        logger.info(f"Starting image analysis for: {file.filename}")
        
        # Validate file
        if not file.content_type or not file.content_type.startswith('image/'):
            logger.warning(f"Invalid file type: {file.content_type}")
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        logger.info("Reading image data...")
        image_data = await file.read()
        if len(image_data) == 0:
            logger.warning("Empty image file received")
            raise HTTPException(status_code=400, detail="Empty image file")
        
        logger.info(f"Image size: {len(image_data)} bytes")
        
        # Limit file size for Railway
        if len(image_data) > MAX_IMAGE_SIZE:
            max_size_mb = round(MAX_IMAGE_SIZE / (1024 * 1024), 2)
            logger.warning(f"Image too large: {len(image_data)} bytes (max: {MAX_IMAGE_SIZE})")
            raise HTTPException(status_code=400, detail=f"Image too large. Maximum size is {max_size_mb}MB.")
        
        # Extract ingredients with timeout
        logger.info("Starting ingredient extraction...")
        try:
            ingredients = await asyncio.wait_for(
                extract_ingredients_from_image(image_data),
                timeout=30.0  # 30 second timeout
            )
        except asyncio.TimeoutError:
            logger.error("Ingredient extraction timed out")
            raise HTTPException(status_code=408, detail="Image processing timed out. Please try with a smaller or clearer image.")
        
        if not ingredients:
            logger.warning("No ingredients detected in image")
            raise HTTPException(status_code=400, detail="No ingredients detected. Try improving image quality or lighting.")
        
        logger.info(f"Found {len(ingredients)} ingredients: {ingredients[:3]}...")
        
        # Limit ingredients for Railway
        if len(ingredients) > MAX_ANALYZED_INGREDIENTS:
            logger.info(
                "Limiting to first %d ingredients (found %d)",
                MAX_ANALYZED_INGREDIENTS,
                len(ingredients)
            )
            ingredients = ingredients[:MAX_ANALYZED_INGREDIENTS]
        
        # Analyze ingredients
        logger.info("Starting ingredient analysis...")
        normalized_need = normalize_user_need(user_need)
        result = await analyze_ingredients(ingredients, normalized_need, db)
        result.product_name = f"Product from Image: {file.filename}"
        
        logger.info("Image analysis completed successfully")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing image: {e}", exc_info=True)
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
        if len(ingredients) > MAX_ANALYZED_INGREDIENTS:
            ingredients = ingredients[:MAX_ANALYZED_INGREDIENTS]
        
        # Analyze ingredients
        normalized_need = normalize_user_need(request.user_need)
        result = await analyze_ingredients(ingredients, normalized_need, db)
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

@app.get("/debug/tesseract")
async def debug_tesseract():
    """Debug Tesseract availability."""
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        return {
            "tesseract_available": True,
            "version": str(version),
            "languages": pytesseract.get_languages()
        }
    except Exception as e:
        return {
            "tesseract_available": False,
            "error": str(e)
        }

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