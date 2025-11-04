"""
Pydantic schemas for user personalization profile.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class UserProfileBase(BaseModel):
    skin_type: Optional[str] = Field(None, description="Tipo de piel facial predominante")
    hair_type: Optional[str] = Field(None, description="Tipo de cabello")
    face_shape: Optional[str] = Field(None, description="Tipo de rostro")
    skin_concerns: List[str] = Field(default_factory=list, description="Necesidades o preocupaciones de piel")
    hair_concerns: List[str] = Field(default_factory=list, description="Necesidades o preocupaciones de cabello")
    overall_goals: List[str] = Field(default_factory=list, description="Objetivos generales de belleza/bienestar")

    @validator("skin_type", "hair_type", "face_shape", pre=True)
    def _normalize_string(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @validator("skin_concerns", "hair_concerns", "overall_goals", pre=True)
    def _normalize_list(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            # Support comma-separated strings coming from legacy clients
            return [item.strip() for item in value.split(",") if item.strip()]
        return [str(item).strip() for item in value if str(item).strip()]


class UserProfileCreate(UserProfileBase):
    """Payload to create or update a user profile."""


class UserProfileResponse(UserProfileBase):
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Pydantic v2
