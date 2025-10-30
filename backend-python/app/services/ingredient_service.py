"""
Ingredient Service
Hair-focused ingredient analysis with reliable defaults and exact matching
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from .substitute_service import SubstituteService

logger = logging.getLogger(__name__)

CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "ingredient_catalog.json"


class IngredientService:
    """Service for ingredient analysis"""

    def __init__(self, db):
        self.db = db
        self.logger = logger
        self.substitute_service = SubstituteService()
        self.catalog, self.alias_lookup = self._load_catalog()

    @staticmethod
    def _normalize_token(raw_name: str) -> str:
        import re
        t = (raw_name or "").upper().strip()
        t = re.sub(r"\([^)]+\)", "", t)
        t = t.replace("  ", " ").strip().rstrip(".;:")
        return t
    
    async def analyze_ingredients(
        self,
        ingredients: List[str],
        user_id: str,
        user_concerns: Optional[List[str]] = None,
        product_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze a list of ingredients using exact matching against catalog.
        Unknown entries receive neutral defaults; no invented names are added.
        """
        try:
            seen = set()
            cleaned: List[str] = []
            for ing in ingredients:
                norm = self._normalize_token(ing)
                if not norm or norm in seen:
                    continue
                seen.add(norm)
                cleaned.append(norm)

            ingredients_analysis: List[Dict[str, Any]] = []
            for norm in cleaned:
                canonical = self.alias_lookup.get(norm, norm)
                data = self.catalog.get(canonical)
                if data:
                    score = data["score"]
                    safety_level = (
                        "safe" if score >= 80 else "moderate" if score >= 60 else "caution"
                    )
                    substitutes = self.substitute_service.get_substitutes(product_type or "", canonical)
                    first_sub = substitutes[0]["name"] if substitutes else None
                    display_name = data.get("display", canonical.title())

                    ingredients_analysis.append(
                        {
                            "name": display_name,
                            "score": score,
                            "safety_level": safety_level,
                            "description": data["desc"],
                            "ewg_score": data["ewg"],
                            "risk": data["risk"],
                            "eco_friendly": data["eco"],
                            "substitute": first_sub,
                        }
                    )
                else:
                    # Unknown – neutral defaults without inventing new names
                    ingredients_analysis.append(
                        {
                            "name": norm.title(),
                            "score": 80,
                            "safety_level": "safe",
                            "description": "Datos no disponibles",
                            "ewg_score": 3,
                            "risk": "low",
                            "eco_friendly": True,
                            "substitute": None,
                        }
                    )

            if not ingredients_analysis:
                return {
                    "success": False,
                    "ingredients_analysis": [],
                    "overall_score": 0,
                    "recommendations": ["No valid ingredients provided"],
                }

            overall_score = sum(i["score"] for i in ingredients_analysis) / len(ingredients_analysis)

            recommendations: List[str] = []
            if product_type == "hair_conditioner":
                if any(i["name"] in {"DIMETHICONE", "CYCLOMETHICONE", "CYCLOPENTASILOXANE"} for i in ingredients_analysis):
                    recommendations.append("Considerar siliconas de menor acumulación (Amodimethicone)")
                if any(i["name"] in {"CETRIMONIUM CHLORIDE", "POLYQUATERNIUM-10"} for i in ingredients_analysis):
                    recommendations.append("Alternativas catiónicas suaves: BTMS, Guar Hydroxypropyltrimonium Chloride")

            if overall_score >= 80:
                recommendations.append("Producto seguro para uso capilar")
            elif overall_score >= 60:
                recommendations.append("Producto con preocupaciones moderadas")
            else:
                recommendations.append("Producto posiblemente no apto para cueros cabelludos sensibles")

            return {
                "success": True,
                "ingredients_analysis": ingredients_analysis,
                "overall_score": round(overall_score, 2),
                "recommendations": recommendations,
            }
        except Exception as e:
            self.logger.error(f"Ingredient analysis failed: {e}")
            return {
                "success": False,
                "ingredients_analysis": [],
                "overall_score": 0,
                "recommendations": ["Analysis failed"],
            }

    def _load_catalog(self) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, str]]:
        """Load ingredient catalog from JSON, falling back to defaults."""
        catalog = self._default_catalog()
        alias_lookup: Dict[str, str] = {}

        if not CATALOG_PATH.exists():
            logger.warning("Ingredient catalog file not found at %s", CATALOG_PATH)
            return catalog, alias_lookup

        try:
            data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse ingredient catalog: %s", exc)
            return catalog, alias_lookup

        for raw_name, payload in data.items():
            normalized = self._normalize_token(raw_name)
            entry = {
                "display": payload.get("display_name", raw_name),
                "score": payload.get("score", catalog.get(normalized, {}).get("score", 80)),
                "ewg": payload.get("ewg", catalog.get(normalized, {}).get("ewg", 3)),
                "risk": payload.get("risk", catalog.get(normalized, {}).get("risk", "low")),
                "eco": payload.get("eco", catalog.get(normalized, {}).get("eco", True)),
                "desc": payload.get(
                    "description", catalog.get(normalized, {}).get("desc", "Datos no disponibles")
                ),
                "categories": payload.get("categories", []),
            }
            catalog[normalized] = entry

            for alias in payload.get("aliases", []) or []:
                alias_lookup[self._normalize_token(alias)] = normalized

        return catalog, alias_lookup

    def _default_catalog(self) -> Dict[str, Dict[str, Any]]:
        """Minimal built-in catalog used as a fallback."""

        def entry(name: str, score: int, ewg: int, risk: str, eco: bool, desc: str) -> Dict[str, Any]:
            return {
                "display": name.title(),
                "score": score,
                "ewg": ewg,
                "risk": risk,
                "eco": eco,
                "desc": desc,
                "categories": [],
            }

        return {
            "AQUA": entry("Aqua", 95, 1, "none", True, "Water - esencial y completamente seguro"),
            "CETEARYL ALCOHOL": entry(
                "Cetearyl Alcohol", 85, 2, "low", True, "Alcohol graso emulsionante y acondicionador"
            ),
            "CETEARETH-20": entry(
                "Ceteareth-20", 85, 2, "low", True, "Emulsionante no iónico común en acondicionadores"
            ),
            "PEG-100 STEARATE": entry(
                "PEG-100 Stearate", 85, 2, "low", False, "Emulsionante derivado de PEG con bajo riesgo"
            ),
            "CETRIMONIUM CHLORIDE": entry(
                "Cetrimonium Chloride",
                70,
                4,
                "moderate",
                False,
                "Acondicionador catiónico eficaz, posible irritación",
            ),
            "DIMETHICONE": entry(
                "Dimethicone",
                60,
                5,
                "moderate",
                False,
                "Silicona no volátil que puede acumularse con el tiempo",
            ),
            "PARFUM": entry(
                "Parfum", 50, 8, "high", False, "Fragancia genérica que puede contener alérgenos"
            ),
        }
