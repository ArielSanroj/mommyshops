"""
Services package for MommyShops application
"""

from .analysis_service import AnalysisService
from .ocr_service import OCRService
from .ingredient_service import IngredientService
try:
    from .ollama_service import OllamaService  # pragma: no cover
except Exception:  # pragma: no cover - optional dependency
    OllamaService = None  # type: ignore

from .formulation_service import FormulationService

__all__ = [
    "AnalysisService",
    "OCRService", 
    "IngredientService",
    "OllamaService",
    "FormulationService",
]
