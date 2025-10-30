"""
Analysis router
Handles product analysis, ingredient analysis, and recommendations
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import Optional, List
import logging
import time

from app.dependencies import get_database, optional_auth, require_auth
from app.database.models import User, Product, Ingredient
from app.services.analysis_service import AnalysisService
from app.services.ocr_service import OCRService
from app.services.ingredient_service import IngredientService
from pydantic import BaseModel, Field, validator
from typing import Optional, List
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])

# Pydantic models
class AnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000, description="Text to analyze")
    product_name: Optional[str] = Field(None, max_length=200, description="Product name for category detection")
    user_need: Optional[str] = Field(None, max_length=500, description="User's specific needs")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    
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
        result = await analysis_service.analyze_text(
            text=request.text,
            user_id=user_id,
            user_need=request.user_need,
            notes=request.notes,
            product_name=request.product_name
        )
        
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
        
        # Analyze extracted text
        analysis_service = AnalysisService(db)
        user_id = current_user.id if current_user else "dev-user"
        result = await analysis_service.analyze_text(
            text=extracted_text,
            user_id=user_id,
            user_need=user_need,
            notes=notes,
            product_name=product_name
        )
        
        processing_time = time.time() - start_time
        
        logger.info(
            f"Image analysis completed for user {current_user.id if current_user else 'dev-user'} in {processing_time:.2f}s"
        )
        
        return AnalysisResponse(
            success=result.get("success", False),
            product_name=result.get("product_name"),
            ingredients=result.get("ingredients", []),
            avg_eco_score=result.get("avg_eco_score"),
            suitability=result.get("suitability"),
            recommendations=result.get("recommendations", []),
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
