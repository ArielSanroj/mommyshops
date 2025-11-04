"""
Pydantic schemas for the personalized product builder.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SubstituteSelection(BaseModel):
    original: str = Field(..., description="Nombre del ingrediente original problemático")
    selected: str = Field(..., description="Ingrediente sustituto elegido")
    reason: Optional[str] = Field(None, description="Motivo o beneficio del sustituto")


class CustomProductCreate(BaseModel):
    base_product_name: str = Field(..., max_length=255)
    safe_ingredients: List[str] = Field(default_factory=list)
    substitutions: List[SubstituteSelection] = Field(default_factory=list)
    profile: Optional[dict] = Field(default=None, description="Instantánea del perfil del usuario")
    labs_formula: List[dict] = Field(default_factory=list, description="Respuesta estructurada de Mommyshops Labs")
    labs_summary: Optional[dict] = Field(default=None, description="Resumen del blend generado por Labs")
    labs_mockup: Optional[dict] = Field(default=None, description="Información visual/mockup del producto")


class CustomProductResponse(BaseModel):
    id: int
    base_product_name: str
    safe_ingredients: List[str]
    substitutions: List[dict]  # Changed from SubstituteSelection to dict for JSON storage
    profile_snapshot: Optional[dict]
    labs_formula: List[dict] = Field(default_factory=list)
    labs_summary: Optional[dict]
    labs_mockup: Optional[dict]
    price: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2
