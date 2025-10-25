"""
Response models for MommyShops API
Pydantic models for API response formatting
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class AuthRegisterResponse(BaseModel):
    success: bool
    message: str
    user_id: str
    email: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class AuthenticatedUser(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool

class ProductAnalysisResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    product_name: Optional[str] = None
    ingredients_details: List[Dict[str, Any]] = Field(default=[])
    avg_eco_score: Optional[float] = None
    suitability: Optional[str] = None
    recommendations: Optional[str] = None
    analysis_id: Optional[str] = None
    processing_time_ms: Optional[int] = None

class IngredientRecommendationResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    ingredients_analysis: List[Dict[str, Any]] = Field(default=[])
    recommendations: Optional[str] = None
    analysis_id: Optional[str] = None

class OllamaAnalysisResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    analysis: Optional[str] = None
    confidence: Optional[float] = None
    recommendations: Optional[str] = None
    processing_time_ms: Optional[int] = None

class OllamaAlternativesResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    alternatives: List[str] = Field(default=[])
    reasoning: Optional[str] = None
    confidence: Optional[float] = None
    processing_time_ms: Optional[int] = None

class RoutineAnalysisResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    analysis: Optional[str] = None
    recommendations: Optional[str] = None
    risk_flags: List[str] = Field(default=[])
    analysis_id: Optional[str] = None

class UserRecommendationsResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    recommendations: List[Dict[str, Any]] = Field(default=[])
    total_count: int = 0

class RecommendationRatingResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    rating_id: Optional[str] = None
    message: Optional[str] = None

class FirebaseRegisterResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    user_id: Optional[str] = None
    message: Optional[str] = None

class FirebaseLoginResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    user_id: Optional[str] = None
    message: Optional[str] = None

class FirebaseUserProfile(BaseModel):
    uid: str
    email: str
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class FirebaseRefreshTokenResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    new_token: Optional[str] = None
    expires_in: Optional[int] = None

class MLRebuildResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    model_id: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: float
    service: str
    version: str
    components: Optional[Dict[str, Any]] = None

class DebugResponse(BaseModel):
    status: str
    message: str
    timestamp: float
    data: Optional[Dict[str, Any]] = None

