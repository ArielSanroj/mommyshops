"""
Ingredient Service
Hair-focused ingredient analysis with reliable defaults and exact matching
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

from .substitute_service import SubstituteService

logger = logging.getLogger(__name__)

BABY_RISK_WEIGHTS = {
    "good": 6,
    "ok": 0,
    "caution": -12,
    "bad": -25,
}

FLAG_LABELS = {
    "piel_atopica": "Puede detonar dermatitis atópica o eccema activo.",
    "piel_muy_reactiva": "Puede causar ardor en piel ultra sensible.",
    "dermatitis_panal": "No recomendado si hay dermatitis del pañal.",
    "bebes_menores_3m": "No apto para recién nacidos (0-3 meses).",
    "bebes_menores_6m": "Evitar en bebés menores de 6 meses.",
    "piel_muy_seca": "Puede dejar sensación tirante en piel muy seca.",
    "piel_muy_grasa": "Puede ocluir en piel o clima muy graso/húmedo.",
    "clima_humedo_caliente": "Se vuelve pesado en climas cálidos y húmedos.",
    "clima_seco": "No aporta suficiente humectación en clima seco.",
    "agua_muy_dura": "Puede reaccionar con agua dura y resecar.",
    "fragrance_free": "Tu perfil evita fragancias para reducir brotes.",
    "microbiome": "Puede alterar el microbioma del bebé.",
    "uso_diario": "Restringir para uso diario en bebés sensibles.",
    "formulas_con_sulfatos": "Evitar combinar con sulfatos fuertes.",
}

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
        profile: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Analyze a list of ingredients using exact matching against catalog.
        Unknown entries receive neutral defaults; no invented names are added.
        """
        try:
            seen = set()
            profile_flags = self._build_profile_flags(profile)
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

                    entry_payload = {
                        "name": display_name,
                        "score": score,
                        "safety_level": safety_level,
                        "description": data.get("desc") or data.get("description", ""),
                        "ewg_score": data["ewg"],
                        "risk": data["risk"],
                        "eco_friendly": data["eco"],
                        "substitute": substitute_str,
                        "catalog_entry": {
                            "score": data["score"],
                            "ewg": data["ewg"],
                            "risk": data["risk"],
                            "eco": data["eco"],
                            "description": data.get("desc"),
                            "baby": data.get("baby"),
                            "categories": data.get("categories", []),
                        },
                    }
                    ingredients_analysis.append(
                        self._apply_baby_annotations(entry_payload, data, profile_flags)
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
                        entry_payload = {
                            "name": display_name,
                            "score": 75,
                            "safety_level": "safe",
                            "description": description,
                            "ewg_score": 4,
                            "risk": "low",
                            "eco_friendly": True,
                            "substitute": "Mantener (es un ingrediente natural seguro)",
                        }
                        ingredients_analysis.append(
                            self._apply_baby_annotations(entry_payload, None, profile_flags)
                        )
                    else:
                        # Unknown synthetic/chemical ingredient - use conservative defaults
                        entry_payload = {
                            "name": display_name,
                            "score": 65,
                            "safety_level": "moderate",
                            "description": "Datos no disponibles; se recomienda verificar fuentes adicionales.",
                            "ewg_score": 6,
                            "risk": "moderate",
                            "eco_friendly": False,
                            "substitute": "Alternativas naturales certificadas (ej. glicerina vegetal, aloe vera orgánico)",
                        }
                        ingredients_analysis.append(
                            self._apply_baby_annotations(entry_payload, None, profile_flags)
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
                "baby": payload.get("baby"),
                "aliases": payload.get("aliases", []),
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

    def enrich_with_baby_metadata(
        self,
        payload: Dict[str, Any],
        profile: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Public helper to add baby metadata to an ingredient payload."""
        profile_flags = self._build_profile_flags(profile)
        catalog_entry = None
        norm = self._normalize_token(payload.get("name", "")) if payload.get("name") else None
        if norm:
            catalog_entry = self.catalog.get(norm)
        if not catalog_entry and payload.get("catalog_entry"):
            catalog_entry = payload["catalog_entry"]
        return self._apply_baby_annotations(payload, catalog_entry, profile_flags)

    def get_profile_flags(self, profile: Optional[Dict[str, Any]]) -> Set[str]:
        return self._build_profile_flags(profile)

    # ------------------------------------------------------------------
    # Baby-specific helpers
    # ------------------------------------------------------------------

    def _apply_baby_annotations(
        self,
        payload: Dict[str, Any],
        catalog_entry: Optional[Dict[str, Any]],
        profile_flags: Set[str],
    ) -> Dict[str, Any]:
        profile_flags = profile_flags or set()
        catalog_entry = catalog_entry or {}
        baby_meta = (catalog_entry or {}).get("baby") or {}
        baby_risk = (baby_meta.get("risk") or "").lower() or None
        baby_summary = baby_meta.get("summary")
        avoid_in = {
            self._normalize_flag(flag) for flag in (baby_meta.get("avoid_in") or []) if flag
        }
        avoid_in.discard(None)
        baby_flags = [
            flag
            for flag in (
                self._normalize_flag(flag) for flag in (baby_meta.get("flags") or [])
            )
            if flag
        ]

        avoid_matches = sorted(flag for flag in avoid_in if flag in profile_flags)
        triggered_flags = sorted(flag for flag in baby_flags if flag in profile_flags)

        base_score = payload.get("compatibility_score", payload.get("score", 70))
        compat_score = base_score + BABY_RISK_WEIGHTS.get(baby_risk, 0)
        compat_score -= 7 * len(avoid_matches)
        compat_score -= 5 * len(triggered_flags)
        compat_score = max(0, min(100, round(compat_score)))

        benefits = list(payload.get("benefits") or [])
        warnings = list(payload.get("warnings") or [])

        if baby_summary:
            if baby_risk in {"good", "ok"}:
                if baby_summary not in benefits:
                    benefits.append(baby_summary)
            elif baby_risk in {"caution", "bad"}:
                if baby_summary not in warnings:
                    warnings.append(baby_summary)

        if avoid_matches:
            for flag in avoid_matches:
                msg = self._flag_message(flag)
                if msg and msg not in warnings:
                    warnings.append(msg)

        payload.update(
            {
                "compatibility_score": compat_score,
                "baby_risk": baby_risk,
                "baby_summary": baby_summary,
                "baby_avoid_in": sorted(flag for flag in avoid_in if flag),
                "baby_flags": baby_flags,
                "baby_flags_triggered": triggered_flags,
                "avoid_reasons": [self._flag_message(flag) for flag in avoid_matches],
                "benefits": benefits,
                "warnings": warnings,
            }
        )

        if catalog_entry and "catalog_entry" not in payload:
            payload["catalog_entry"] = {
                "score": catalog_entry.get("score"),
                "ewg": catalog_entry.get("ewg"),
                "risk": catalog_entry.get("risk"),
                "eco": catalog_entry.get("eco"),
                "description": catalog_entry.get("desc"),
                "baby": catalog_entry.get("baby"),
                "categories": catalog_entry.get("categories"),
            }
        return payload

    def _build_profile_flags(self, profile: Optional[Dict[str, Any]]) -> Set[str]:
        flags: Set[str] = set()
        if not profile:
            return flags

        def add(value: Optional[str]):
            norm = self._normalize_flag(value)
            if norm:
                flags.add(norm)

        skin = (profile.get("skin_type") or "").lower()
        if "seca" in skin:
            add("piel_muy_seca")
        if "atop" in skin:
            add("piel_atopica")
        if "humeda" in skin or "grasa" in skin:
            add("piel_muy_grasa")

        age_group = (profile.get("age_group") or "").lower()
        if age_group:
            if "0" in age_group or "reci" in age_group:
                add("bebes_menores_3m")
                add("bebes_menores_6m")
            elif "3" in age_group or "12" in age_group:
                add("bebes_menores_12m")

        if profile.get("ultra_sensitive"):
            add("piel_muy_reactiva")

        eczema_level = (profile.get("eczema_level") or "").lower()
        if eczema_level and eczema_level not in {"none", "baja"}:
            add("piel_atopica")

        diaper = profile.get("diaper_dermatitis")
        if diaper and str(diaper).lower() not in {"no", "false", "0"}:
            add("dermatitis_panal")

        fragrance_pref = (profile.get("fragrance_preferences") or "").lower()
        if "sin" in fragrance_pref or "free" in fragrance_pref:
            add("fragrance_free")

        if profile.get("microbiome_preference"):
            add("microbiome")

        water = (profile.get("water_hardness") or "").lower()
        if "dura" in water:
            add("agua_muy_dura")

        climate_code = self._normalize_flag(profile.get("climate"))
        if climate_code:
            add(climate_code)

        climate_ctx = profile.get("climate_context") or {}
        humidity = climate_ctx.get("humidity")
        if humidity is not None:
            try:
                humidity = float(humidity)
                if humidity >= 70:
                    add("clima_humedo_caliente")
                elif humidity <= 40:
                    add("clima_seco")
            except (TypeError, ValueError):
                pass

        temperature = climate_ctx.get("temperature_c")
        if temperature is not None:
            try:
                temperature = float(temperature)
                if temperature >= 28:
                    add("clima_humedo_caliente")
            except (TypeError, ValueError):
                pass

        return flags

    def _normalize_flag(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        import re

        normalized = (
            str(value)
            .strip()
            .lower()
            .replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u")
        )
        normalized = normalized.replace("/", "_").replace("-", "_").replace(" ", "_")
        normalized = re.sub(r"__+", "_", normalized)
        normalized = normalized.strip("_")
        return normalized or None

    def _flag_message(self, flag: Optional[str]) -> str:
        if not flag:
            return ""
        return FLAG_LABELS.get(flag, flag.replace("_", " ").capitalize())
