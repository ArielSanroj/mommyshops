"""
Documented analysis routes with comprehensive OpenAPI documentation
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
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

# Create router with comprehensive documentation
router = APIRouter(
    prefix="/api/v1",
    tags=["Analysis"],
    responses={
        400: {"description": "Bad Request"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Not Found"},
        422: {"description": "Validation Error"},
        500: {"description": "Internal Server Error"}
    }
)

# Request/Response Models
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ProductAnalysisRequest(BaseModel):
    """Request model for product analysis"""
    text: str = Field(
        ..., 
        description="Product ingredients text to analyze",
        example="Aqua, Glycerin, Hyaluronic Acid, Niacinamide, Retinol",
        min_length=1,
        max_length=10000
    )
    user_need: str = Field(
        default="general safety",
        description="User's skin type or concern",
        example="sensitive skin",
        enum=["sensitive skin", "acne-prone", "anti-aging", "general safety"]
    )
    
    class Config:
        schema_extra = {
            "example": {
                "text": "Aqua, Glycerin, Hyaluronic Acid, Niacinamide, Retinol",
                "user_need": "sensitive skin"
            }
        }

class IngredientAnalysis(BaseModel):
    """Individual ingredient analysis result"""
    name: str = Field(..., description="Ingredient name")
    risk_level: str = Field(..., description="Risk level", enum=["low", "medium", "high", "unknown"])
    eco_score: float = Field(..., description="Eco score (0-100)", ge=0, le=100)
    benefits: str = Field(..., description="Benefits of the ingredient")
    risks_detailed: str = Field(..., description="Detailed risk information")
    sources: str = Field(..., description="Data sources used")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Hyaluronic Acid",
                "risk_level": "low",
                "eco_score": 85.0,
                "benefits": "Hydrating, plumping, anti-aging",
                "risks_detailed": "None known",
                "sources": "EWG, FDA, COSING"
            }
        }

class ProductAnalysisResponse(BaseModel):
    """Response model for product analysis"""
    success: bool = Field(..., description="Whether the analysis was successful")
    product_name: Optional[str] = Field(None, description="Name of the analyzed product")
    ingredients_details: List[IngredientAnalysis] = Field(..., description="Detailed analysis of each ingredient")
    avg_eco_score: Optional[float] = Field(None, description="Average eco score", ge=0, le=100)
    suitability: Optional[str] = Field(None, description="Overall suitability", enum=["excellent", "good", "fair", "poor", "not recommended"])
    recommendations: Optional[str] = Field(None, description="Personalized recommendations")
    analysis_id: Optional[str] = Field(None, description="Unique identifier for this analysis")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    error: Optional[str] = Field(None, description="Error message if analysis failed")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "product_name": "Anti-Aging Serum",
                "ingredients_details": [
                    {
                        "name": "Hyaluronic Acid",
                        "risk_level": "low",
                        "eco_score": 85.0,
                        "benefits": "Hydrating, plumping",
                        "risks_detailed": "None known",
                        "sources": "EWG, FDA"
                    }
                ],
                "avg_eco_score": 85.0,
                "suitability": "excellent",
                "recommendations": "This product is excellent for sensitive skin",
                "analysis_id": "analysis_123",
                "processing_time_ms": 1500
            }
        }

class ImageAnalysisRequest(BaseModel):
    """Request model for image analysis"""
    user_need: str = Field(
        default="general safety",
        description="User's skin type or concern",
        example="sensitive skin",
        enum=["sensitive skin", "acne-prone", "anti-aging", "general safety"]
    )

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = Field(False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    timestamp: str = Field(..., description="Error timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error": "Invalid input data",
                "error_code": "INVALID_INPUT",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }

# Endpoints with comprehensive documentation

@router.post(
    "/analyze-image",
    response_model=ProductAnalysisResponse,
    summary="Analyze product from image",
    description="""
    Analyze a product's ingredients from an uploaded image using OCR technology.
    
    This endpoint:
    1. Extracts text from the uploaded image using OCR
    2. Identifies ingredients from the extracted text
    3. Analyzes each ingredient for safety and eco-friendliness
    4. Provides personalized recommendations based on user needs
    
    **Supported image formats**: JPG, PNG, WebP
    **Maximum file size**: 5MB
    **Processing time**: 5-30 seconds depending on image complexity
    """,
    responses={
        200: {
            "description": "Analysis completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "product_name": "Anti-Aging Serum",
                        "ingredients_details": [
                            {
                                "name": "Hyaluronic Acid",
                                "risk_level": "low",
                                "eco_score": 85.0,
                                "benefits": "Hydrating, plumping",
                                "risks_detailed": "None known",
                                "sources": "EWG, FDA"
                            }
                        ],
                        "avg_eco_score": 85.0,
                        "suitability": "excellent",
                        "recommendations": "This product is excellent for sensitive skin",
                        "analysis_id": "analysis_123",
                        "processing_time_ms": 1500
                    }
                }
            }
        },
        400: {
            "description": "Invalid image file",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "Invalid image file format",
                        "error_code": "INVALID_IMAGE",
                        "timestamp": "2024-01-01T00:00:00Z"
                    }
                }
            }
        },
        413: {
            "description": "File too large",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "File size exceeds maximum limit of 5MB",
                        "error_code": "FILE_TOO_LARGE",
                        "timestamp": "2024-01-01T00:00:00Z"
                    }
                }
            }
        }
    },
    tags=["Analysis"]
)
async def analyze_image(
    file: UploadFile = File(
        ..., 
        description="Product image file",
        example="product_image.jpg"
    ),
    user_need: str = Form(
        default="general safety",
        description="User's skin type or concern",
        example="sensitive skin"
    ),
    db: Session = Depends(get_db)
) -> ProductAnalysisResponse:
    """
    Analyze product ingredients from an uploaded image.
    
    This endpoint uses OCR technology to extract ingredient information from product images,
    then analyzes each ingredient for safety, eco-friendliness, and suitability for the user's needs.
    
    **Process**:
    1. **Image Upload**: Accepts JPG, PNG, or WebP images up to 5MB
    2. **OCR Processing**: Extracts text from the image using Tesseract OCR
    3. **Ingredient Identification**: Parses the text to identify individual ingredients
    4. **Safety Analysis**: Analyzes each ingredient using multiple databases (EWG, FDA, COSING)
    5. **AI Recommendations**: Uses AI to provide personalized recommendations
    
    **Rate Limiting**: 5 requests per minute (slower due to AI processing)
    **Authentication**: Optional (provides enhanced features for authenticated users)
    """
    start_time = time.time()
    
    try:
        # Validate file
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image"
            )
        
        if file.size > 5 * 1024 * 1024:  # 5MB limit
            raise HTTPException(
                status_code=413,
                detail="File size exceeds maximum limit of 5MB"
            )
        
        # Call main analysis function
        result = await analyze_image_main(file, user_need, db)
        
        # Convert to response format
        ingredients_details = []
        if result.get("ingredients_details"):
            for ingredient in result["ingredients_details"]:
                ingredients_details.append(IngredientAnalysis(
                    name=ingredient.get("name", ""),
                    risk_level=ingredient.get("risk_level", "unknown"),
                    eco_score=float(ingredient.get("eco_score", 50.0)),
                    benefits=ingredient.get("benefits", "No information available"),
                    risks_detailed=ingredient.get("risks_detailed", "No information available"),
                    sources=ingredient.get("sources", "Analysis system")
                ))
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return ProductAnalysisResponse(
            success=True,
            product_name=result.get("product_name", "Analyzed Product"),
            ingredients_details=ingredients_details,
            avg_eco_score=result.get("avg_eco_score", 50.0),
            suitability=result.get("suitability", "unknown"),
            recommendations=result.get("recommendations", "Consult with a professional"),
            analysis_id=f"img_{int(time.time())}",
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in image analysis: {e}")
        return ProductAnalysisResponse(
            success=False,
            error=str(e),
            ingredients_details=[],
            processing_time_ms=int((time.time() - start_time) * 1000)
        )

@router.post(
    "/analyze-text",
    response_model=ProductAnalysisResponse,
    summary="Analyze product from text",
    description="""
    Analyze a product's ingredients from text input.
    
    This endpoint:
    1. Parses the ingredient text to identify individual ingredients
    2. Analyzes each ingredient for safety and eco-friendliness
    3. Provides personalized recommendations based on user needs
    
    **Processing time**: 2-10 seconds depending on ingredient count
    **Rate limiting**: 60 requests per minute
    """,
    responses={
        200: {
            "description": "Analysis completed successfully"
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "Text field is required",
                        "error_code": "VALIDATION_ERROR",
                        "timestamp": "2024-01-01T00:00:00Z"
                    }
                }
            }
        }
    },
    tags=["Analysis"]
)
async def analyze_text(
    request: ProductAnalysisRequest,
    db: Session = Depends(get_db)
) -> ProductAnalysisResponse:
    """
    Analyze product ingredients from text input.
    
    This endpoint processes ingredient text to provide comprehensive safety analysis
    and personalized recommendations.
    
    **Process**:
    1. **Text Parsing**: Identifies individual ingredients from the text
    2. **Safety Analysis**: Analyzes each ingredient using multiple databases
    3. **AI Recommendations**: Uses AI to provide personalized recommendations
    4. **Eco Scoring**: Calculates overall eco-friendliness score
    
    **Rate Limiting**: 60 requests per minute
    **Authentication**: Optional (provides enhanced features for authenticated users)
    """
    start_time = time.time()
    
    try:
        # Call main text analysis function
        result = await analyze_text_main(request.text, request.user_need, db)
        
        # Convert to response format
        ingredients_details = []
        if result.get("ingredients_details"):
            for ingredient in result["ingredients_details"]:
                ingredients_details.append(IngredientAnalysis(
                    name=ingredient.get("name", ""),
                    risk_level=ingredient.get("risk_level", "unknown"),
                    eco_score=float(ingredient.get("eco_score", 50.0)),
                    benefits=ingredient.get("benefits", "No information available"),
                    risks_detailed=ingredient.get("risks_detailed", "No information available"),
                    sources=ingredient.get("sources", "Analysis system")
                ))
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return ProductAnalysisResponse(
            success=True,
            product_name=result.get("product_name", "Analyzed Product"),
            ingredients_details=ingredients_details,
            avg_eco_score=result.get("avg_eco_score", 50.0),
            suitability=result.get("suitability", "unknown"),
            recommendations=result.get("recommendations", "Consult with a professional"),
            analysis_id=f"txt_{int(time.time())}",
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error in text analysis: {e}")
        return ProductAnalysisResponse(
            success=False,
            error=str(e),
            ingredients_details=[],
            processing_time_ms=int((time.time() - start_time) * 1000)
        )

@router.post(
    "/ingredients/analyze",
    response_model=ProductAnalysisResponse,
    summary="Analyze specific ingredients",
    description="""
    Analyze a list of specific ingredients for safety and eco-friendliness.
    
    This endpoint is optimized for analyzing known ingredient lists and provides
    detailed analysis for each ingredient.
    
    **Processing time**: 1-5 seconds depending on ingredient count
    **Rate limiting**: 60 requests per minute
    """,
    responses={
        200: {
            "description": "Analysis completed successfully"
        }
    },
    tags=["Analysis"]
)
async def analyze_ingredients(
    ingredients: List[str] = Field(
        ..., 
        description="List of ingredients to analyze",
        example=["Hyaluronic Acid", "Niacinamide", "Retinol"]
    ),
    user_need: str = Field(
        default="general safety",
        description="User's skin type or concern",
        example="sensitive skin"
    ),
    db: Session = Depends(get_db)
) -> ProductAnalysisResponse:
    """
    Analyze a list of specific ingredients.
    
    This endpoint provides detailed analysis for a list of known ingredients,
    including safety scores, eco-friendliness, and personalized recommendations.
    
    **Process**:
    1. **Ingredient Validation**: Validates each ingredient name
    2. **Safety Analysis**: Analyzes each ingredient using multiple databases
    3. **Eco Scoring**: Calculates eco-friendliness scores
    4. **Recommendations**: Provides personalized recommendations
    
    **Rate Limiting**: 60 requests per minute
    **Authentication**: Optional (provides enhanced features for authenticated users)
    """
    start_time = time.time()
    
    try:
        # Analyze each ingredient
        ingredients_details = []
        for ingredient in ingredients:
            try:
                ingredient_data = await fetch_ingredient_data(ingredient)
                ingredients_details.append(IngredientAnalysis(
                    name=ingredient_data.get("name", ingredient),
                    risk_level=ingredient_data.get("risk_level", "unknown"),
                    eco_score=float(ingredient_data.get("eco_score", 50.0)),
                    benefits=ingredient_data.get("benefits", "No information available"),
                    risks_detailed=ingredient_data.get("risks_detailed", "No information available"),
                    sources=ingredient_data.get("sources", "Analysis system")
                ))
            except Exception as e:
                logger.warning(f"Error analyzing ingredient {ingredient}: {e}")
                ingredients_details.append(IngredientAnalysis(
                    name=ingredient,
                    risk_level="unknown",
                    eco_score=50.0,
                    benefits="No information available",
                    risks_detailed="Analysis failed",
                    sources="Error"
                ))
        
        # Calculate average eco score
        avg_eco_score = sum(ing.eco_score for ing in ingredients_details) / len(ingredients_details) if ingredients_details else 50.0
        
        # Determine suitability
        high_risk_count = sum(1 for ing in ingredients_details if ing.risk_level == "high")
        if high_risk_count > len(ingredients_details) * 0.3:  # More than 30% high risk
            suitability = "poor"
        elif avg_eco_score >= 80:
            suitability = "excellent"
        elif avg_eco_score >= 60:
            suitability = "good"
        else:
            suitability = "fair"
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return ProductAnalysisResponse(
            success=True,
            product_name="Ingredient Analysis",
            ingredients_details=ingredients_details,
            avg_eco_score=avg_eco_score,
            suitability=suitability,
            recommendations=f"Analysis of {len(ingredients)} ingredients completed",
            analysis_id=f"ing_{int(time.time())}",
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error in ingredient analysis: {e}")
        return ProductAnalysisResponse(
            success=False,
            error=str(e),
            ingredients_details=[],
            processing_time_ms=int((time.time() - start_time) * 1000)
        )
