"""
Request models for MommyShops API
Pydantic models for API request validation
"""

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

class AuthRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=100)

class AuthLoginRequest(BaseModel):
    email: EmailStr
    password: str

class ProductAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=10000)
    product_name: Optional[str] = Field(None, max_length=200)
    user_need: str = Field(default="general safety", max_length=200)

class IngredientAnalysisRequest(BaseModel):
    ingredients: str = Field(..., min_length=5, max_length=5000)
    user_need: str = Field(default="general safety", max_length=200)

class OllamaAnalysisRequest(BaseModel):
    ingredients: List[str] = Field(..., min_items=1, max_items=50)
    user_conditions: List[str] = Field(default=[], max_items=20)
    analysis_type: str = Field(default="safety", max_length=50)

class OllamaAlternativesRequest(BaseModel):
    problematic_ingredients: List[str] = Field(..., min_items=1, max_items=20)
    user_conditions: List[str] = Field(default=[], max_items=20)
    preferences: Optional[Dict[str, Any]] = Field(default=None)

class RoutineAnalysisRequest(BaseModel):
    user_id: str
    routine_type: str = Field(default="daily", max_length=50)
    products: List[Dict[str, Any]] = Field(..., min_items=1, max_items=20)

class RecommendationRatingRequest(BaseModel):
    recommendation_id: str
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = Field(None, max_length=500)

class FirebaseRegisterRequest(BaseModel):
    firebase_uid: str = Field(..., min_length=10, max_length=100)
    email: EmailStr
    display_name: Optional[str] = Field(None, max_length=100)
    photo_url: Optional[str] = Field(None, max_length=500)

class FirebaseLoginRequest(BaseModel):
    firebase_uid: str = Field(..., min_length=10, max_length=100)
    email: EmailStr

class FirebaseUserUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(None, max_length=100)
    photo_url: Optional[str] = Field(None, max_length=500)
    preferences: Optional[Dict[str, Any]] = Field(default=None)

class MLRebuildRequest(BaseModel):
    force_rebuild: bool = Field(default=False)
    model_type: str = Field(default="recommendation", max_length=50)
    parameters: Optional[Dict[str, Any]] = Field(default=None)

