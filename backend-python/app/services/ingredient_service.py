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
        # Remove content inside parentheses (e.g., "Sodium (something)" -> "Sodium")
        t = re.sub(r"\([^)]+\)", "", t)
        # Remove orphan closing parentheses (e.g., "Parabens)" -> "Parabens")
        t = t.rstrip(")")
        # Remove orphan opening parentheses
        t = t.lstrip("(")
        # Clean up multiple spaces and trailing punctuation
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
            processed: List[Tuple[str, str]] = []
            for ing in ingredients:
                original = (ing or "").strip()
                norm = self._normalize_token(original)
                if not norm or norm in seen:
                    continue
                seen.add(norm)
                processed.append((norm, original))

            ingredients_analysis: List[Dict[str, Any]] = []
            for norm, original_name in processed:
                canonical = self.alias_lookup.get(norm, norm)
                data = self.catalog.get(canonical)
                if data:
                    score = data["score"]
                    safety_level = (
                        "safe" if score >= 80 else "moderate" if score >= 60 else "caution"
                    )
                    # First try substitutes from catalog entry, then from substitute service
                    catalog_subs = data.get("substitutes", [])
                    if catalog_subs:
                        # Use substitutes from catalog entry
                        if isinstance(catalog_subs, list):
                            first_sub = catalog_subs[0] if catalog_subs else None
                            all_subs = catalog_subs
                        else:
                            first_sub = str(catalog_subs)
                            all_subs = [first_sub]
                    else:
                        # Fallback to substitute service
                        substitutes = self.substitute_service.get_substitutes(product_type or "", canonical)
                        first_sub = substitutes[0]["name"] if substitutes else None
                        all_subs = [s["name"] for s in substitutes] if substitutes else []
                    
                    display_name = data.get("display", canonical.title())
                    if original_name:
                        display_name = original_name

                    # Format substitute string
                    substitute_str = None
                    if all_subs:
                        if len(all_subs) == 1:
                            substitute_str = all_subs[0]
                        else:
                            substitute_str = ", ".join(all_subs[:3])
                    elif first_sub:
                        substitute_str = first_sub
                    
                    ingredients_analysis.append(
                        {
                            "name": display_name,
                            "score": score,
                            "safety_level": safety_level,
                            "description": data.get("desc") or data.get("description", ""),
                            "ewg_score": data["ewg"],
                            "risk": data["risk"],
                            "eco_friendly": data["eco"],
                            "substitute": substitute_str,
                        }
                    )
                else:
                    # Unknown ingredient - detect if it's a natural plant extract
                    display_name = original_name or norm.title()
                    
                    # Detect natural/plant-based ingredients by keywords (case-insensitive)
                    norm_lower = norm.lower()
                    is_natural_extract = any(keyword in norm_lower for keyword in [
                        "extract", "oil", "juice", "root", "leaf", "flower", "seed", 
                        "fruit", "bark", "stem", "plant", "herb", "botanical", "sinensis",
                        "sativa", "officinalis", "biloba", "gasipaes", "usitatissimum"
                    ])
                    
                    # Natural extracts are generally safer - assign better defaults
                    if is_natural_extract:
                        ingredient_type = "extracto natural" if "extract" in norm_lower else "jugo natural" if "juice" in norm_lower else "aceite natural" if "oil" in norm_lower else "ingrediente natural"
                        description = f"{ingredient_type.capitalize()} de origen vegetal. Generalmente considerado seguro para uso cosmético. Puede proporcionar beneficios antioxidantes y nutritivos para la piel/cabello."
                        ingredients_analysis.append(
                            {
                                "name": display_name,
                                "score": 75,  # Better default for natural extracts
                                "safety_level": "safe",
                                "description": description,
                                "ewg_score": 4,  # Moderate EWG for plant extracts
                                "risk": "low",  # Low risk for natural extracts
                                "eco_friendly": True,
                                "substitute": "Mantener (es un ingrediente natural seguro)",
                            }
                        )
                    else:
                        # Unknown synthetic/chemical ingredient - use conservative defaults
                        ingredients_analysis.append(
                            {
                                "name": display_name,
                                "score": 65,
                                "safety_level": "moderate",
                                "description": "Datos no disponibles; se recomienda verificar fuentes adicionales.",
                                "ewg_score": 6,
                                "risk": "moderate",
                                "eco_friendly": False,
                                "substitute": "Alternativas naturales certificadas (ej. glicerina vegetal, aloe vera orgánico)",
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
                # Include substitutes if present in catalog entry
                "substitutes": payload.get("substitutes", []),
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
