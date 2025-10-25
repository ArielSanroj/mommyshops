"""
Analysis routes for MommyShops API
Handles product analysis, ingredient analysis, and recommendations
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import time

from ...core.database import get_db
from ...core.security import get_current_user_optional
from ...models.requests import ProductAnalysisRequest, IngredientAnalysisRequest
from ...models.responses import ProductAnalysisResponse, IngredientRecommendationResponse
from ...services.ocr_service import OCRService
from ...services.ingredient_service import IngredientService
from ...services.ml_service import MLService
from ...database import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["Analysis"])

@router.post("/analyze-image", response_model=ProductAnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    user_need: str = Form(default="general safety"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> ProductAnalysisResponse:
    """
    Analyze product image using OCR and AI
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Use OCR service to extract text
        ocr_service = OCRService()
        extracted_text = await ocr_service.extract_text_from_image(file_content)
        
        if not extracted_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract text from image"
            )
        
        # Use ingredient service to analyze ingredients
        ingredient_service = IngredientService(db)
        ingredients_analysis = await ingredient_service.analyze_ingredients(
            extracted_text, user_need
        )
        
        # Use ML service for recommendations
        ml_service = MLService()
        recommendations = await ml_service.generate_recommendations(
            ingredients_analysis, user_need
        )
        
        # Calculate average eco score
        avg_eco_score = sum(ing.eco_score for ing in ingredients_analysis) / len(ingredients_analysis) if ingredients_analysis else 50.0
        
        logger.info(f"Image analysis completed for user: {current_user.email if current_user else 'anonymous'}")
        
        return ProductAnalysisResponse(
            success=True,
            product_name="Product from image",
            ingredients_details=ingredients_analysis,
            avg_eco_score=avg_eco_score,
            suitability="Analysis completed",
            recommendations=recommendations,
            analysis_id=f"img_{int(time.time())}",
            processing_time_ms=0  # This would be calculated
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in image analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/analyze-text", response_model=ProductAnalysisResponse)
async def analyze_text(
    request: ProductAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> ProductAnalysisResponse:
    """
    Analyze product text for ingredients and safety
    """
    try:
        # Use ingredient service to analyze ingredients
        ingredient_service = IngredientService(db)
        ingredients_analysis = await ingredient_service.analyze_ingredients(
            request.text, request.user_need
        )
        
        # Use ML service for recommendations
        ml_service = MLService()
        recommendations = await ml_service.generate_recommendations(
            ingredients_analysis, request.user_need
        )
        
        # Calculate average eco score
        avg_eco_score = sum(ing.eco_score for ing in ingredients_analysis) / len(ingredients_analysis) if ingredients_analysis else 50.0
        
        logger.info(f"Text analysis completed for user: {current_user.email if current_user else 'anonymous'}")
        
        return ProductAnalysisResponse(
            success=True,
            product_name=request.product_name or "Product",
            ingredients_details=ingredients_analysis,
            avg_eco_score=avg_eco_score,
            suitability="Analysis completed",
            recommendations=recommendations,
            analysis_id=f"txt_{int(time.time())}",
            processing_time_ms=0  # This would be calculated
        )
        
    except Exception as e:
        logger.error(f"Error in text analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/ingredients/analyze", response_model=IngredientRecommendationResponse)
async def analyze_ingredients(
    request: IngredientAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> IngredientRecommendationResponse:
    """
    Analyze specific ingredients for safety and recommendations
    """
    try:
        # Use ingredient service to analyze ingredients
        ingredient_service = IngredientService(db)
        ingredients_analysis = await ingredient_service.analyze_ingredients(
            request.ingredients, request.user_need
        )
        
        # Use ML service for recommendations
        ml_service = MLService()
        recommendations = await ml_service.generate_recommendations(
            ingredients_analysis, request.user_need
        )
        
        logger.info(f"Ingredient analysis completed for user: {current_user.email if current_user else 'anonymous'}")
        
        return IngredientRecommendationResponse(
            success=True,
            ingredients_analysis=ingredients_analysis,
            recommendations=recommendations,
            analysis_id=f"ing_{int(time.time())}"
        )
        
    except Exception as e:
        logger.error(f"Error in ingredient analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

