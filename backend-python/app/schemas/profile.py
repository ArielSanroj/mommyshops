"""
Pydantic schemas for user personalization profile.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class UserProfileBase(BaseModel):
    skin_type: Optional[str] = Field(None, description="Tipo de piel facial predominante")
    hair_type: Optional[str] = Field(None, description="Tipo de cabello")
    face_shape: Optional[str] = Field(None, description="Tipo de rostro")
    skin_concerns: List[str] = Field(default_factory=list, description="Necesidades o preocupaciones de piel")
    hair_concerns: List[str] = Field(default_factory=list, description="Necesidades o preocupaciones de cabello")
    overall_goals: List[str] = Field(default_factory=list, description="Objetivos generales de belleza/bienestar")
    climate: Optional[str] = Field(None, description="Código de clima seleccionado (ej. clima_humedo_calor)")
    location_country: Optional[str] = Field(None, description="País reportado por la mamá")
    location_city: Optional[str] = Field(None, description="Ciudad reportada por la mamá")
    climate_context: Optional[Dict[str, Any]] = Field(None, description="Datos de humedad/temperatura obtenidos por IA")
    water_hardness: Optional[str] = Field(None, description="Nivel de dureza del agua en el hogar")
    ultra_sensitive: Optional[bool] = Field(None, description="Bandera para modo ultra sensitive")
    age_group: Optional[str] = Field(None, description="Edad del bebé (ej. 0_3m, 3_12m)")
    eczema_level: Optional[str] = Field(None, description="Nivel de eccema reportado")
    diaper_dermatitis: Optional[str] = Field(None, description="Estado de dermatitis del pañal")
    fragrance_preferences: Optional[str] = Field(None, description="Preferencias de fragancia (ej. sin fragancia)")
    microbiome_preference: Optional[str] = Field(None, description="Preferencia para activaciones microbiome-friendly")

    @validator(
        "skin_type",
        "hair_type",
        "face_shape",
        "climate",
        "location_country",
        "location_city",
        "water_hardness",
        "age_group",
        "eczema_level",
        "diaper_dermatitis",
        "fragrance_preferences",
        "microbiome_preference",
        pre=True,
    )
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
