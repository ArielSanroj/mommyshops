"""
Pydantic schemas for Mommyshops Labs formulation endpoint.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, validator


class FormulationProfile(BaseModel):
    skin_type: Optional[str] = Field(None, description="Tipo de piel (seca, grasa, sensible, etc.)")
    hair_type: Optional[str] = Field(None, description="Tipo de cabello principal")
    concerns: List[str] = Field(default_factory=list, description="Necesidades clave declaradas por la persona usuaria")
    goals: List[str] = Field(default_factory=list, description="Resultados deseados al usar el producto")
    skin_concerns: List[str] = Field(default_factory=list)
    hair_concerns: List[str] = Field(default_factory=list)
    overall_goals: List[str] = Field(default_factory=list)

    @validator("*", pre=True)
    def _sanitize(cls, value):
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                return None
            return cleaned
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return value


class FormulaIngredient(BaseModel):
    inci: str
    percent: float
    reason: str
    function_tags: List[str] = Field(default_factory=list)
    source: str


class FormulationSummary(BaseModel):
    compatibility_score: float
    highlights: List[str] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)
    variant: str
    variant_label: Optional[str] = None
    profile_hint: Optional[str] = None
    product_name: Optional[str] = None


class FormulateRequest(BaseModel):
    profile: Optional[FormulationProfile] = None
    ingredients_detected: List[str] = Field(default_factory=list, description="Ingredientes identificados por el front/análisis")
    variant: Optional[str] = Field(
        default=None,
        description="botanical | clinical | balanced",
    )
    product_name: Optional[str] = Field(default=None, max_length=200)
    budget: Optional[float] = Field(default=None, ge=0)

    @validator("ingredients_detected", pre=True)
    def _ensure_list(cls, value):
        if isinstance(value, str):
            return [value]
        return value or []


class FormulationOriginalIngredient(BaseModel):
    name: str
    status: str
    score: float
    note: Optional[str] = None


class FormulationSubstitution(BaseModel):
    for_: str = Field(..., alias="for")
    suggested: str
    reason: Optional[str] = None

    class Config:
        allow_population_by_field_name = True


class MockupPayload(BaseModel):
    title: str
    variant: str
    tagline: str
    hero_ingredients: List[str]
    eta_days: Optional[str] = None


class FormulateResponse(BaseModel):
    new_formula: List[FormulaIngredient]
    summary: FormulationSummary
    original_ingredients: List[FormulationOriginalIngredient] = Field(default_factory=list)
    substitutions: List[FormulationSubstitution] = Field(default_factory=list)
    unknown_ingredients: List[str] = Field(default_factory=list)
    mockup: Optional[MockupPayload] = None
