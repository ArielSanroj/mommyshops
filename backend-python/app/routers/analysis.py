"""
Analysis router
Handles product analysis, ingredient analysis, and recommendations
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import logging
import time
import json
import re

from app.dependencies import get_database, optional_auth, require_auth
from app.database.models import User, Product, Ingredient
from app.services.analysis_service import AnalysisService
from app.services.ocr_service import OCRService
from app.services.ingredient_service import IngredientService
logger = logging.getLogger(__name__)

try:
    from app.services.ollama_service import OllamaService
except ImportError as import_error:  # pragma: no cover
    logger.warning("OllamaService import failed (%s). Using stub implementation.", import_error)

    class OllamaService:  # type: ignore
        available = False
        model = "disabled"
        base_url = "http://localhost:11434"

        async def enhance_text_with_ollama(self, text: str) -> str:
            return text

        async def analyze_ingredients(self, ingredients: List[str], user_conditions: List[str], analysis_type: str) -> Dict[str, Any]:
            return {
                "analysis": "",
                "confidence": 0.0,
                "recommendations": "",
                "processing_time_ms": 0,
            }

        async def analyze_ingredients_structured(self, ingredients: List[str], user_conditions: List[str], profile_context: Dict[str, Any]) -> Dict[str, Any]:
            return {"items": [], "success": False}

from app.schemas.profile import UserProfileCreate
from pydantic import BaseModel, Field, validator


def _user_profile_dict(user: Optional[User]) -> Dict[str, Any]:
    if not user:
        return {}
    return {
        "skin_type": user.skin_face,
        "hair_type": user.hair_type,
        "face_shape": getattr(user, "face_shape", None),
        "skin_concerns": user.goals_face or [],
        "hair_concerns": user.goals_hair or [],
        "overall_goals": user.conditions or [],
        "climate": getattr(user, "climate", None),
        "location_country": getattr(user, "country", None),
        "location_city": getattr(user, "city", None),
        "water_hardness": getattr(user, "water_hardness", None),
        "ultra_sensitive": getattr(user, "ultra_sensitive", None),
        "age_group": getattr(user, "age_group", None),
        "eczema_level": getattr(user, "eczema_level", None),
        "diaper_dermatitis": getattr(user, "diaper_dermatitis", None),
        "fragrance_preferences": getattr(user, "fragrance_preferences", None),
        "microbiome_preference": getattr(user, "microbiome_preference", None),
    }


def _merge_profiles(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    list_keys = {"skin_concerns", "hair_concerns", "overall_goals"}
    for key, value in override.items():
        if not value and value not in (0, False):
            continue
        if key in list_keys:
            if isinstance(value, list) and value:
                merged[key] = value
        else:
            merged[key] = value
    for key in list_keys:
        if not merged.get(key):
            merged.pop(key, None)
    return {k: v for k, v in merged.items() if v is not None and v != []}


router = APIRouter(prefix="/analysis", tags=["analysis"])

CLIMATE_PRESETS = [
    {
        "country": "Colombia",
        "city": "Bogotá",
        "emoji": "🏔️",
        "humidity": 35,
        "temperature_c": 18,
        "condition": "Clima seco + altitud",
        "ia_adjustment": "+20% avena y karité",
        "compatibility_hint": "Necesitas fórmulas más nutritivas (Nube de Avena)."
    },
    {
        "country": "Colombia",
        "city": "Cartagena",
        "emoji": "🌴",
        "humidity": 78,
        "temperature_c": 30,
        "condition": "Clima cálido + humedad alta",
        "ia_adjustment": "Reducimos emolientes y subimos té verde/hamamelis",
        "compatibility_hint": "Ideal activar Brisa de Té Verde para controlar humedad."
    },
    {
        "country": "México",
        "city": "CDMX",
        "emoji": "🌤️",
        "humidity": 45,
        "temperature_c": 22,
        "condition": "Clima templado + altura",
        "ia_adjustment": "Balanceamos avena/caléndula según temporada",
        "compatibility_hint": "Equilibrio de Caléndula funciona perfecto todo el año."
    },
    {
        "country": "Argentina",
        "city": "Buenos Aires",
        "emoji": "🌦️",
        "humidity": 60,
        "temperature_c": 20,
        "condition": "Clima templado con humedad media",
        "ia_adjustment": "Ajustamos jojoba/caléndula en transición estacional",
        "compatibility_hint": "Equilibrio Caléndula mantiene la piel suave a diario."
    },
    {
        "country": "Estados Unidos",
        "city": "Miami",
        "emoji": "☀️",
        "humidity": 75,
        "temperature_c": 32,
        "condition": "Clima tropical húmedo",
        "ia_adjustment": "Activamos modo anti-humedad (hamamelis + aloe)",
        "compatibility_hint": "Brisa de Té Verde previene dermatitis por calor."
    }
]


def _normalize_location_value(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    normalized = (
        value.strip()
        .lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )
    return normalized or None


CLIMATE_LOOKUP = {
    (_normalize_location_value(entry["country"]), _normalize_location_value(entry["city"])): entry
    for entry in CLIMATE_PRESETS
}


class ClimateResponse(BaseModel):
    country: str
    city: str
    emoji: str
    humidity: float
    temperature_c: float
    condition: str
    ia_adjustment: str
    compatibility_hint: str
    source: str = "mommyshops_preset"


@router.get("/climate", response_model=ClimateResponse)
async def get_climate_profile(
    country: str = Query(..., min_length=2, description="Country name"),
    city: str = Query(..., min_length=2, description="City name"),
):
    """
    Retrieve climate profile for a given city/country combination.
    """
    country_key = _normalize_location_value(country)
    city_key = _normalize_location_value(city)
    if not country_key or not city_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="País y ciudad son requeridos")
    context = CLIMATE_LOOKUP.get((country_key, city_key))
    if not context:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No tenemos datos climáticos para esa ubicación")
    return context


class AnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000, description="Text to analyze")
    product_name: Optional[str] = Field(None, max_length=200, description="Product name for category detection")
    user_need: Optional[str] = Field(None, max_length=500, description="User's specific needs")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    profile: Optional[UserProfileCreate] = Field(None, description="Inline personalization profile")
    
    @validator('text')
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError('Text cannot be empty')
        # Remove potentially harmful content
        v = re.sub(r'<script.*?</script>', '', v, flags=re.IGNORECASE | re.DOTALL)
        v = re.sub(r'<[^>]+>', '', v)  # Remove HTML tags
        return v.strip()
    
    @validator('user_need', 'notes')
    def validate_optional_fields(cls, v):
        if v is not None:
            # Remove potentially harmful content
            v = re.sub(r'<script.*?</script>', '', v, flags=re.IGNORECASE | re.DOTALL)
            v = re.sub(r'<[^>]+>', '', v)  # Remove HTML tags
            return v.strip()
        return v

class AnalysisResponse(BaseModel):
    success: bool
    product_name: Optional[str] = None
    product_type: Optional[str] = None
    ingredients: List[dict] = []
    avg_eco_score: Optional[float] = None
    suitability: Optional[str] = None
    recommendations: List[str] = []
    structured_report: Optional[dict] = None
    detailed_report: Optional[str] = None
    profile: Optional[dict] = None
    analysis_summary: Optional[dict] = None
    intelligent_formula: Optional[dict] = None
    baby_report: Optional[dict] = None
    processing_time: float

class IngredientAnalysisRequest(BaseModel):
    ingredients: List[str] = Field(..., min_items=1, max_items=50, description="List of ingredients to analyze")
    user_concerns: Optional[List[str]] = Field(None, max_items=10, description="User's specific concerns")
    
    @validator('ingredients')
    def validate_ingredients(cls, v):
        if not v:
            raise ValueError('At least one ingredient is required')
        
        # Validate each ingredient
        validated_ingredients = []
        for ingredient in v:
            if not ingredient or not ingredient.strip():
                continue
            # Sanitize ingredient name
            ingredient = re.sub(r'<[^>]+>', '', ingredient.strip())
            if ingredient and len(ingredient) <= 200:  # Reasonable length limit
                validated_ingredients.append(ingredient)
        
        if not validated_ingredients:
            raise ValueError('No valid ingredients provided')
        
        return validated_ingredients
    
    @validator('user_concerns')
    def validate_user_concerns(cls, v):
        if v is not None:
            validated_concerns = []
            for concern in v:
                if concern and concern.strip():
                    # Sanitize concern
                    concern = re.sub(r'<[^>]+>', '', concern.strip())
                    if concern and len(concern) <= 100:
                        validated_concerns.append(concern)
            return validated_concerns
        return v

class IngredientAnalysisResponse(BaseModel):
    success: bool
    ingredients_analysis: List[dict] = []
    overall_score: Optional[float] = None
    recommendations: List[str] = []
    processing_time: float

@router.post("/text", response_model=AnalysisResponse)
async def analyze_text(
    request: AnalysisRequest,
    current_user: Optional[User] = Depends(optional_auth),
    db: Session = Depends(get_database)
):
    """Analyze text for ingredients and provide analysis"""
    start_time = time.time()
    
    try:
        analysis_service = AnalysisService(db)
        user_id = current_user.id if current_user else "dev-user"

        incoming_profile = request.profile.dict(exclude_unset=True, exclude_none=True) if request.profile else {}
        stored_profile = _user_profile_dict(current_user)
        merged_profile = _merge_profiles(stored_profile, incoming_profile)

        effective_user_need = request.user_need
        if not effective_user_need:
            goals = merged_profile.get("overall_goals")
            if goals:
                effective_user_need = ", ".join(goals)
            elif merged_profile.get("skin_concerns"):
                effective_user_need = ", ".join(merged_profile["skin_concerns"])
            elif merged_profile.get("hair_concerns"):
                effective_user_need = ", ".join(merged_profile["hair_concerns"])
        
        # Skip Ollama text pre-processing to speed up analysis
        # The main analysis will handle ingredient extraction
        enhanced_text = request.text
        
        result = await analysis_service.analyze_text(
            text=enhanced_text,
            user_id=user_id,
            user_need=effective_user_need,
            notes=request.notes,
            product_name=request.product_name,
            profile=merged_profile
        )
        
        # Skip secondary Ollama enhancement to avoid double processing
        # The main analysis already uses Ollama if available
        
        processing_time = time.time() - start_time
        
        logger.info(
            f"Text analysis completed for user {current_user.id if current_user else 'dev-user'} in {processing_time:.2f}s"
        )
        
        return AnalysisResponse(
            success=result.get("success", False),
            product_name=result.get("product_name"),
            product_type=result.get("product_type"),
            ingredients=result.get("ingredients", []),
            avg_eco_score=result.get("avg_eco_score"),
            suitability=result.get("suitability"),
            recommendations=result.get("recommendations", []),
            structured_report=result.get("structured_report"),
            detailed_report=result.get("detailed_report"),
            profile=result.get("profile"),
            analysis_summary=result.get("analysis_summary"),
            intelligent_formula=result.get("intelligent_formula"),
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Text analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Text analysis failed"
        )

@router.post("/image", response_model=AnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    product_name: Optional[str] = Form(None),
    user_need: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    profile: Optional[str] = Form(None),
    current_user: Optional[User] = Depends(optional_auth),
    db: Session = Depends(get_database)
):
    """Analyze image for ingredients using OCR"""
    start_time = time.time()
    
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Validate file size (5MB limit)
        MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File too large. Maximum size is 5MB"
            )
        
        # Validate file extension
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        file_extension = None
        if file.filename:
            file_extension = '.' + file.filename.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
                )
        
        # Read file content
        file_content = await file.read()
        
        # Validate file content size
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File too large. Maximum size is 5MB"
            )
        
        # Use OCR service to extract text
        ocr_service = OCRService()
        extracted_text = await ocr_service.extract_text_from_image(file_content)
        
        if not extracted_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract text from image"
            )
        
        # Skip Ollama OCR enhancement to speed up analysis
        # The main analysis will handle ingredient extraction
        enhanced_text = extracted_text
        
        # Analyze extracted text
        analysis_service = AnalysisService(db)
        user_id = current_user.id if current_user else "dev-user"
        incoming_profile: Dict[str, Any] = {}
        if profile:
            try:
                profile_dict = json.loads(profile)
                incoming_profile = UserProfileCreate(**profile_dict).dict(exclude_unset=True, exclude_none=True)
            except Exception as exc:
                logger.warning(f"Failed to parse profile payload from form: {exc}")
        stored_profile = _user_profile_dict(current_user)
        merged_profile = _merge_profiles(stored_profile, incoming_profile)

        effective_user_need = user_need
        if not effective_user_need:
            goals = merged_profile.get("overall_goals")
            if goals:
                effective_user_need = ", ".join(goals)
            elif merged_profile.get("skin_concerns"):
                effective_user_need = ", ".join(merged_profile["skin_concerns"])
            elif merged_profile.get("hair_concerns"):
                effective_user_need = ", ".join(merged_profile["hair_concerns"])

        result = await analysis_service.analyze_text(
            text=enhanced_text,
            user_id=user_id,
            user_need=effective_user_need,
            notes=notes,
            product_name=product_name,
            profile=merged_profile
        )
        
        # Skip secondary Ollama enhancement to avoid double processing
        # The main analysis already uses Ollama if available
        
        processing_time = time.time() - start_time
        
        logger.info(
            f"Image analysis completed for user {current_user.id if current_user else 'dev-user'} in {processing_time:.2f}s"
        )
        
        return AnalysisResponse(
            success=result.get("success", False),
            product_name=result.get("product_name"),
            product_type=result.get("product_type"),
            ingredients=result.get("ingredients", []),
            avg_eco_score=result.get("avg_eco_score"),
            suitability=result.get("suitability"),
            recommendations=result.get("recommendations", []),
            structured_report=result.get("structured_report"),
            detailed_report=result.get("detailed_report"),
            profile=result.get("profile"),
            analysis_summary=result.get("analysis_summary"),
            intelligent_formula=result.get("intelligent_formula"),
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image analysis failed"
        )

@router.post("/ingredients", response_model=IngredientAnalysisResponse)
async def analyze_ingredients(
    request: IngredientAnalysisRequest,
    current_user: Optional[User] = Depends(optional_auth),
    db: Session = Depends(get_database)
):
    """Analyze specific ingredients"""
    start_time = time.time()
    
    try:
        ingredient_service = IngredientService(db)
        user_id = current_user.id if current_user else "dev-user"
        result = await ingredient_service.analyze_ingredients(
            ingredients=request.ingredients,
            user_id=user_id,
            user_concerns=request.user_concerns
        )
        
        processing_time = time.time() - start_time
        
        logger.info(f"Ingredient analysis completed for user {current_user.id} in {processing_time:.2f}s")
        
        return IngredientAnalysisResponse(
            success=result.get("success", False),
            ingredients_analysis=result.get("ingredients_analysis", []),
            overall_score=result.get("overall_score"),
            recommendations=result.get("recommendations", []),
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Ingredient analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ingredient analysis failed"
        )

@router.get("/history")
async def get_analysis_history(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_database)
):
    """Get user's analysis history"""
    try:
        analysis_service = AnalysisService(db)
        history = await analysis_service.get_user_analysis_history(
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        
        return {
            "success": True,
            "history": history,
            "total": len(history)
        }
        
    except Exception as e:
        logger.error(f"Failed to get analysis history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analysis history"
        )
