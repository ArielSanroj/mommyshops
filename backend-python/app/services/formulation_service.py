"""
MommyShops Labs - intelligent formulation service.
Translates detected ingredients + profile context into a proposed formula.
"""

from __future__ import annotations

import copy
import json
import logging
import unicodedata
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "labs_functional_catalog.json"
CLIMATE_MATRIX_PATH = Path(__file__).resolve().parent.parent / "data" / "climate_profiles.json"

DEFAULT_NEEDS = ["hidratacion", "control_grasa", "antiinflamatorio", "anticaspa"]

FUNCTION_LABELS = {
    "hidratacion": "Hidratación profunda",
    "nutricion": "Nutrición vegetal",
    "antioxidante": "Antioxidante",
    "antiinflamatorio": "Antiinflamatorio",
    "barrera": "Refuerzo de barrera",
    "calmante": "Calmante",
    "fortalecimiento": "Fortalecimiento",
    "definicion_rizos": "Definición de rizos",
    "estimulacion": "Estimula folículos",
    "microcirculacion": "Microcirculación",
    "anticaspa": "Control de caspa",
    "antimicrobiano": "Acción antimicrobiana",
    "anticaida": "Control de caída",
    "regulacion_hormonal": "Regulación hormonal",
    "oxigenacion": "Oxigenación",
    "reparacion": "Reparación",
    "refrescante": "Efecto refrescante",
    "defensa_uv": "Defensa UV",
    "control_grasa": "Control de grasa",
    "barrera_cutanea": "Barrera cutánea",
    "nutricion_intensa": "Nutrición intensa",
    "microbioma": "Equilibrio microbioma",
    "definicion": "Definición",
    "oxigenacion_celular": "Oxigenación celular",
    "termoproteccion": "Termoprotección",
    "proteccion_solar": "Protección solar",
}

DEFAULT_FAMILY_WEIGHTS = {
    "humectantes": 1.0,
    "emolientes": 1.0,
    "emolientes_ligeros": 1.0,
    "tensioactivos": 1.0,
    "calmantes": 1.0,
    "prebioticos": 1.0,
    "astringentes": 1.0,
}

INGREDIENT_FAMILY_MAP = {
    "avena": "calmantes",
    "karite": "emolientes",
    "almendra": "emolientes",
    "glicerina": "humectantes",
    "prebioticos": "prebioticos",
    "calendula": "calmantes",
    "beta_glucano": "calmantes",
    "base_surfactante": "tensioactivos",
    "te_verde": "astringentes",
    "hamamelis": "astringentes",
    "aloe": "humectantes",
    "coco_caprylate": "emolientes_ligeros",
    "bisabolol": "calmantes",
    "jojoba": "emolientes",
    "manzanilla": "calmantes"
}

BABY_BASE_BLENDS = {
    "nube_avena": {
        "display_name": "Nube de Avena – Microbiome Edition",
        "persona": "Bebés con piel seca/atópica o climas secos/aire acondicionado",
        "cta": "Pide ahora",
        "ai_mode": "Modo hidratación profunda",
        "base_key": "base_surfactante",
        "base": [
            {"key": "avena", "ingredient": "Avena coloidal orgánica", "percent": 5.0, "role": "Calma eccema"},
            {"key": "karite", "ingredient": "Karité fair-trade", "percent": 8.0, "role": "Sella hidratación"},
            {"key": "almendra", "ingredient": "Leche de almendra dulce", "percent": 4.0, "role": "Nutrición ligera"},
            {"key": "glicerina", "ingredient": "Glicerina vegetal", "percent": 6.0, "role": "Humectante tear-free"},
            {"key": "prebioticos", "ingredient": "Prebióticos (inulina + alfa-glucano)", "percent": 0.4, "role": "Equilibrio microbioma"},
            {"key": "calendula", "ingredient": "Caléndula CO2 + bisabolol", "percent": 0.8, "role": "Reparación"},
            {"key": "beta_glucano", "ingredient": "β-glucano de avena + centella", "percent": 0.6, "role": "Refuerzo barrera"},
            {"key": "base_surfactante", "ingredient": "Base tear-free (Decyl + Coco Glucoside + agua)", "percent": 75.2, "role": "Limpieza suave pH 5.5"},
        ],
    },
    "brisa_te": {
        "display_name": "Brisa de Té Verde – Microbiome Edition",
        "persona": "Piel húmeda/grasosa, climas cálidos o con dermatitis del pañal",
        "cta": "Pide ahora",
        "ai_mode": "Modo anti-humedad",
        "base_key": "base_surfactante",
        "base": [
            {"key": "te_verde", "ingredient": "Infusión de té verde orgánico", "percent": 4.5, "role": "Antioxidante"},
            {"key": "hamamelis", "ingredient": "Hamamelis sin alcohol", "percent": 3.5, "role": "Control humedad"},
            {"key": "aloe", "ingredient": "Aloe vera 99%", "percent": 6.0, "role": "Calma calor"},
            {"key": "coco_caprylate", "ingredient": "Coco-caprylate ligero", "percent": 3.0, "role": "Emoliente seco"},
            {"key": "prebioticos", "ingredient": "Prebióticos (inulina + alfa-glucano)", "percent": 0.4, "role": "Microbioma"},
            {"key": "bisabolol", "ingredient": "Bisabolol + centella", "percent": 0.6, "role": "Antiinflamatorio"},
            {"key": "base_surfactante", "ingredient": "Base micelar (Decyl + Coco Glucoside + Lauryl Glucoside)", "percent": 82.0, "role": "Limpieza fresca"},
        ],
    },
    "equilibrio_calendula": {
        "display_name": "Equilibrio de Caléndula – Microbiome Edition",
        "persona": "Uso diario para piel normal/mixta y transiciones estacionales",
        "cta": "Pide ahora",
        "ai_mode": "Modo balance diario",
        "base_key": "base_surfactante",
        "base": [
            {"key": "calendula", "ingredient": "Caléndula orgánica 3%", "percent": 3.0, "role": "Calma diaria"},
            {"key": "jojoba", "ingredient": "Aceite de jojoba golden", "percent": 4.5, "role": "Balancea sebo"},
            {"key": "manzanilla", "ingredient": "Manzanilla romana", "percent": 2.0, "role": "Relaja y suaviza"},
            {"key": "glicerina", "ingredient": "Glicerina vegetal", "percent": 5.5, "role": "Humectante"},
            {"key": "aloe", "ingredient": "Aloe vera 99%", "percent": 5.0, "role": "Hidratación ligera"},
            {"key": "prebioticos", "ingredient": "Prebióticos (inulina + alfa-glucano)", "percent": 0.4, "role": "Microbioma"},
            {"key": "bisabolol", "ingredient": "Bisabolol + β-glucano", "percent": 0.6, "role": "Barrera"},
            {"key": "base_surfactante", "ingredient": "Base suave (Decyl + Coco Glucoside + agua)", "percent": 79.0, "role": "Limpieza equilibrada"},
        ],
    },
}

def _normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9\s\-&/]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _normalize_need(value: Optional[str]) -> Optional[str]:
    norm = _normalize_text(value)
    return norm or None


def _title_case(value: str) -> str:
    return value[:1].upper() + value[1:] if value else value


@dataclass
class CatalogEntry:
    key: str
    data: Dict[str, Any]

    @property
    def id(self) -> str:
        return self.data.get("id", self.key)

    @property
    def inci(self) -> str:
        return self.data.get("inci_name", self.key.title())


class FormulationService:
    """Core logic for building a MommyShops Labs formula."""

    def __init__(self, catalog_path: Optional[Path] = None):
        self.catalog_path = catalog_path or CATALOG_PATH
        self.catalog, self.synonyms = self._load_catalog()
        self.function_keys = self._collect_function_keys()
        self.climate_matrix = self._load_climate_matrix()
        self.climate_profiles = self.climate_matrix.get("profiles", {})
        self.city_lookup = self._build_city_lookup(self.climate_matrix.get("cities", []))
        self.blend_modulations = self.climate_matrix.get("blend_modulations", {})

    # -----------------------------
    # Public API
    # -----------------------------

    def generate_formula(
        self,
        profile: Optional[Dict[str, Any]],
        detected_ingredients: List[str],
        variant: Optional[str] = None,
        product_name: Optional[str] = None,
        budget: Optional[float] = None,
    ) -> Dict[str, Any]:
        profile_ctx = self._build_profile_context(profile)
        variant_key = self._determine_variant(variant, profile_ctx)

        resolved, unknown = self._resolve_ingredients(detected_ingredients)
        scored_entries = self._score_entries(resolved, profile_ctx)

        if not scored_entries:
            logger.info("No catalog matches from detected list; seeding with variant defaults")
            scored_entries = self._seed_from_catalog(profile_ctx, variant_key)

        coverage = self._aggregate_coverage(scored_entries, profile_ctx)
        gaps = self._find_function_gaps(coverage, profile_ctx)

        additions = self._suggest_additions(
            gaps=gaps,
            profile_ctx=profile_ctx,
            variant_key=variant_key,
            used_ids={entry["record"].id for entry in scored_entries},
        )

        formula_items = self._compose_formula(scored_entries, additions, profile_ctx, variant_key, budget)
        summary = self._build_summary(formula_items, coverage, gaps, profile_ctx, variant_key, product_name)
        original_descriptions = self._describe_originals(scored_entries, profile_ctx)
        substitutions = self._build_substitutions(additions, gaps)

        return {
            "new_formula": [
                {
                    "inci": item["record"].inci,
                    "percent": item["percent"],
                    "reason": item["reason"],
                    "function_tags": item["function_tags"],
                    "source": item["source"],
                }
                for item in formula_items
            ],
            "summary": summary,
            "original_ingredients": original_descriptions,
            "substitutions": substitutions,
            "unknown_ingredients": unknown,
            "mockup": self._build_mockup(summary, formula_items, product_name),
        }

    def generate_baby_formula(self, profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Return an adjusted Mommyshops baby blend tailored to climate and edad."""
        context = self._build_baby_context(profile or {})
        blend_key = self._select_baby_blend(context)
        base = BABY_BASE_BLENDS[blend_key]
        adjusted = self._adjust_blend_for_conditions(blend_key, context)
        reasons = self._compose_blend_reasons(blend_key, context)

        return {
            "blend_key": blend_key,
            "display_name": base["display_name"],
            "persona": base["persona"],
            "cta": base.get("cta", "Pide ahora"),
            "ai_mode": base.get("ai_mode"),
            "adjusted_ingredients": adjusted["ingredients"],
            "adjustments": adjusted["notes"],
            "climate_hint": adjusted["climate_hint"],
            "reasons": reasons,
        }

    def _build_baby_context(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        profile = profile or {}
        climate_ctx = profile.get("climate_context") or {}
        humidity = climate_ctx.get("humidity")
        temperature = climate_ctx.get("temperature_c")
        location_country = profile.get("location_country")
        location_city = profile.get("location_city")
        city_key = self._normalize_location(location_city)
        city_entry = self._lookup_city_entry(location_country, location_city)
        season = (profile.get("season") or "").lower()
        climate_profile_tag = self._resolve_climate_profile(city_entry, season)
        skin_type = (profile.get("skin_type") or "").lower()
        age_group = (profile.get("age_group") or "").lower()
        eczema = (profile.get("eczema_level") or "").lower()
        concern = (profile.get("diaper_dermatitis") or "").lower()

        return {
            "raw": profile,
            "skin_type": skin_type,
            "age_group": age_group,
            "humidity": humidity,
            "temperature": temperature,
            "eczema": eczema,
            "diaper": concern,
            "climate_context": climate_ctx,
            "city_entry": city_entry,
            "climate_profile_tag": climate_profile_tag,
            "season": season,
            "extra_factors": (city_entry or {}).get("extra_factors") or {},
            "city_key": city_key,
        }

    def _lookup_city_entry(self, country: Optional[str], city: Optional[str]) -> Optional[Dict[str, Any]]:
        country_key = self._normalize_location(country)
        city_key = self._normalize_location(city)
        if not country_key or not city_key:
            return None
        return self.city_lookup.get((country_key, city_key))

    def _resolve_climate_profile(self, city_entry: Optional[Dict[str, Any]], season: Optional[str]) -> Optional[str]:
        if not city_entry:
            return None
        overrides = city_entry.get("season_profile_override")
        if season and isinstance(overrides, dict):
            override_tag = overrides.get(season)
            if override_tag and override_tag != "none":
                return override_tag
        if isinstance(overrides, str) and overrides != "none":
            return overrides
        return city_entry.get("climate_profile")

    def _family_weights_for_context(self, blend_key: str, context: Dict[str, Any]) -> Dict[str, float]:
        weights = dict(DEFAULT_FAMILY_WEIGHTS)
        tag = context.get("climate_profile_tag")
        if tag and tag in self.climate_profiles:
            profile_weights = self.climate_profiles[tag].get("family_weights", {})
            for family, multiplier in profile_weights.items():
                base_value = weights.get(family, 1.0)
                weights[family] = round(base_value * float(multiplier), 4)

        weights = self._apply_extra_factors(weights, context.get("extra_factors") or {})
        weights = self._apply_blend_modulation(blend_key, context, weights)

        humidity = context.get("humidity")
        try:
            if humidity is not None:
                humidity_val = float(humidity)
                if humidity_val >= 70:
                    weights["emolientes"] *= 0.85
                    weights["tensioactivos"] *= 1.05
                    weights["astringentes"] *= 1.15
                    weights["prebioticos"] *= 1.15
                elif humidity_val <= 40:
                    weights["humectantes"] *= 1.2
                    weights["emolientes"] *= 1.15
                    weights["tensioactivos"] *= 0.9
                    weights["calmantes"] *= 1.15
        except (TypeError, ValueError):
            pass

        temperature = context.get("temperature")
        try:
            if temperature is not None and float(temperature) >= 28:
                weights["calmantes"] *= 1.1
                weights["astringentes"] *= 1.1
        except (TypeError, ValueError):
            pass

        return weights

    def _apply_extra_factors(self, weights: Dict[str, float], factors: Dict[str, Any]) -> Dict[str, float]:
        adjusted = dict(weights)

        def scale(family: str, factor: float, intensity: float):
            base = adjusted.get(family, 1.0)
            adjusted[family] = round(base * (1 + intensity * factor), 4)

        dermatitis = float(factors.get("dermatitis_risk", 0) or 0)
        if dermatitis:
            scale("calmantes", dermatitis, 0.2)
            scale("prebioticos", dermatitis, 0.15)
            scale("tensioactivos", dermatitis, -0.1)

        sweat = float(factors.get("sweat_risk", 0) or 0)
        if sweat:
            scale("emolientes", sweat, -0.2)
            scale("tensioactivos", sweat, 0.1)
            scale("astringentes", sweat, 0.2)
            scale("prebioticos", sweat, 0.1)

        wind = float(factors.get("wind_irritation", 0) or 0)
        if wind:
            scale("calmantes", wind, 0.15)
            scale("humectantes", wind, 0.1)

        uv = float(factors.get("uv_stress", 0) or 0)
        if uv:
            scale("calmantes", uv, 0.12)
            scale("prebioticos", uv, 0.1)

        barrier = float(factors.get("barrier_damage_risk", 0) or 0)
        if barrier:
            scale("humectantes", barrier, 0.18)
            scale("emolientes", barrier, 0.15)
            scale("calmantes", barrier, 0.12)

        return adjusted

    def _apply_blend_modulation(
        self,
        blend_key: str,
        context: Dict[str, Any],
        weights: Dict[str, float],
    ) -> Dict[str, float]:
        adjusted = dict(weights)
        blend_data = self.blend_modulations.get(blend_key)
        if not blend_data:
            return adjusted

        city_key = context.get("city_key")
        city_mod = blend_data.get(city_key or "")
        if not city_mod:
            return adjusted

        season = self._normalize_season(context.get("season"))
        season_weights = None
        if season and season in city_mod:
            season_weights = city_mod[season]
        elif "all_year" in city_mod:
            season_weights = city_mod["all_year"]

        if not season_weights:
            return adjusted

        for family, multiplier in season_weights.items():
            if family not in adjusted:
                adjusted[family] = 1.0
            adjusted[family] = round(adjusted[family] * float(multiplier), 4)

        return adjusted

    def _normalize_season(self, season: Optional[str]) -> Optional[str]:
        if not season:
            return None
        season = season.strip().lower()
        if "/" in season:
            season = season.split("/")[0].strip()
        mappings = {
            "invierno": "winter",
            "winter": "winter",
            "verano": "summer",
            "summer": "summer",
            "primavera": "spring",
            "spring": "spring",
            "otoño": "autumn",
            "otono": "autumn",
            "autumn": "autumn",
            "fall": "autumn",
        }
        return mappings.get(season, season)

    def _apply_family_weights(
        self, items: List[Dict[str, Any]], weights: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        adjusted = copy.deepcopy(items)
        total = 0.0
        for item in adjusted:
            family = INGREDIENT_FAMILY_MAP.get(item["key"])
            multiplier = weights.get(family, 1.0)
            item["percent"] = round(item["percent"] * multiplier, 4)
            total += item["percent"]

        if total <= 0:
            return adjusted

        normalization = 100.0 / total
        for item in adjusted:
            item["percent"] = round(item["percent"] * normalization, 2)
        return adjusted

    def _select_baby_blend(self, context: Dict[str, Any]) -> str:
        humidity = context.get("humidity")
        skin = context.get("skin_type", "")
        eczema = context.get("eczema", "")
        diaper = context.get("diaper", "")
        city_entry = context.get("city_entry") or {}
        climate_profile_tag = context.get("climate_profile_tag")

        if city_entry and climate_profile_tag != "variable_estaciones":
            primary = city_entry.get("primary_blend")
            if primary:
                return primary

        try:
            humidity_val = float(humidity) if humidity is not None else None
        except (TypeError, ValueError):
            humidity_val = None

        if "seca" in skin or "atop" in skin or eczema in {"alto", "moderado"} or (humidity_val is not None and humidity_val < 45):
            return "nube_avena"

        if (
            "humeda" in skin
            or "gras" in skin
            or diaper in {"si", "true", "alto"}
            or (humidity_val is not None and humidity_val >= 65)
        ):
            return "brisa_te"

        return "equilibrio_calendula"

    def _adjust_blend_for_conditions(self, blend_key: str, context: Dict[str, Any]) -> Dict[str, Any]:
        base = BABY_BASE_BLENDS[blend_key]
        items = copy.deepcopy(base["base"])
        family_weights = self._family_weights_for_context(blend_key, context)
        items = self._apply_family_weights(items, family_weights)
        notes: List[str] = []
        humidity = context.get("humidity")
        temperature = context.get("temperature")
        age_group = context.get("age_group") or ""
        diaper = context.get("diaper") or ""

        def adjust_percent(key: str, delta: float):
            for item in items:
                if item["key"] == key:
                    item["percent"] = round(max(0.1, item["percent"] + delta), 2)
                    return delta
            return 0.0

        base_key = base.get("base_key", "base_surfactante")

        humidity_val = None
        try:
            if humidity is not None:
                humidity_val = float(humidity)
        except (TypeError, ValueError):
            humidity_val = None

        temp_val = None
        try:
            if temperature is not None:
                temp_val = float(temperature)
        except (TypeError, ValueError):
            temp_val = None

        total_delta = 0.0
        if blend_key == "nube_avena" and humidity_val is not None and humidity_val < 45:
            total_delta += adjust_percent("avena", 1.5)
            total_delta += adjust_percent("karite", 1.0)
            notes.append("+ karité y avena por clima seco")
        if blend_key == "brisa_te" and humidity_val is not None and humidity_val >= 70:
            total_delta += adjust_percent("hamamelis", 1.0)
            total_delta += adjust_percent("te_verde", 0.5)
            total_delta -= adjust_percent("coco_caprylate", 0.5)
            notes.append("Activamos modo anti-humedad (más hamamelis)")
        if blend_key == "equilibrio_calendula" and temp_val is not None and temp_val >= 28:
            total_delta += adjust_percent("aloe", 1.0)
            notes.append("Aumentamos aloe por calor alto")
        if "0" in age_group:
            notes.append("Modo recién nacido: mantenemos 0 % fragancia")
        if diaper in {"si", "alto", "true"}:
            notes.append("Refuerzo anti-dermatitis del pañal")

        # Balance base surfactante para mantener 100%
        if abs(total_delta) > 0.01:
            for item in items:
                if item["key"] == base_key:
                    item["percent"] = round(max(0.0, item["percent"] - total_delta), 2)
                    break

        total = sum(item["percent"] for item in items)
        if total != 100.0 and base_key:
            for item in items:
                if item["key"] == base_key:
                    item["percent"] = round(max(0.0, item["percent"] + (100.0 - total)), 2)
                    break

        climate_hint = None
        if humidity_val is not None:
            if humidity_val >= 70:
                climate_hint = "Optimizado para humedad alta"
            elif humidity_val <= 40:
                climate_hint = "Modo clima seco activado"
        if not climate_hint and context.get("climate_profile_tag"):
            profile_meta = self.climate_profiles.get(context["climate_profile_tag"], {})
            if profile_meta.get("label"):
                climate_hint = profile_meta["label"]

        return {"ingredients": items, "notes": notes, "climate_hint": climate_hint}

    def _compose_blend_reasons(self, blend_key: str, context: Dict[str, Any]) -> List[str]:
        reasons: List[str] = []
        skin = context.get("skin_type", "")
        humidity = context.get("humidity")
        diaper = context.get("diaper", "")

        if blend_key == "nube_avena":
            reasons.append("Refuerza barrera con avena coloidal y karité.")
            if "seca" in skin:
                reasons.append("Calma tirantez constante en piel seca/atópica.")
            if humidity is not None:
                reasons.append("IA sube emolientes cuando la humedad cae.")
        elif blend_key == "brisa_te":
            reasons.append("Controla brillo y brotes en clima húmedo.")
            if diaper:
                reasons.append("Hamamelis y aloe protegen zonas con pañal.")
            reasons.append("Espuma micro-micelar tear-free.")
        else:
            reasons.append("Rutina equilibrada para todos los días.")
            reasons.append("Caléndula y jojoba se adaptan a cambios de estación.")
            reasons.append("Prebióticos mantienen microbioma estable.")

        return reasons[:3]

    # -----------------------------
    # Catalog + normalization helpers
    # -----------------------------

    def _load_catalog(self) -> Tuple[Dict[str, CatalogEntry], Dict[str, str]]:
        entries: Dict[str, CatalogEntry] = {}
        synonyms: Dict[str, str] = {}

        raw_data: List[Dict[str, Any]] = []
        if self.catalog_path.exists():
            try:
                parsed = json.loads(self.catalog_path.read_text(encoding="utf-8"))
                if isinstance(parsed, dict):
                    raw_data = list(parsed.values())
                elif isinstance(parsed, list):
                    raw_data = parsed
            except json.JSONDecodeError as exc:
                logger.warning("Invalid labs catalog JSON: %s", exc)

        if not raw_data:
            raw_data = self._fallback_catalog()

        for entry in raw_data:
            inci = entry.get("inci_name")
            key = _normalize_text(inci or entry.get("id") or entry.get("name") or "")
            if not key:
                continue
            catalog_entry = CatalogEntry(key=key, data=entry)
            entries[key] = catalog_entry

            for syn in entry.get("synonyms", []) or []:
                syn_key = _normalize_text(syn)
                if syn_key:
                    synonyms[syn_key] = key

        return entries, synonyms

    def _load_climate_matrix(self) -> Dict[str, Any]:
        if not CLIMATE_MATRIX_PATH.exists():
            logger.warning("Climate matrix file not found at %s", CLIMATE_MATRIX_PATH)
            return {"cities": [], "profiles": {}}
        try:
            return json.loads(CLIMATE_MATRIX_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            logger.warning("Invalid climate matrix JSON: %s", exc)
            return {"cities": [], "profiles": {}}

    def _build_city_lookup(self, cities: List[Dict[str, Any]]) -> Dict[Tuple[str, str], Dict[str, Any]]:
        lookup: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for entry in cities or []:
            country = self._normalize_location(entry.get("country"))
            city = self._normalize_location(entry.get("city"))
            if country and city:
                lookup[(country, city)] = entry
        return lookup

    def _normalize_location(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        value = unicodedata.normalize("NFKD", value)
        value = "".join(ch for ch in value if not unicodedata.combining(ch))
        value = value.strip().lower()
        value = value.replace(".", "")
        return value or None

    def _resolve_ingredients(self, items: List[str]) -> Tuple[List[Dict[str, Any]], List[str]]:
        resolved: List[Dict[str, Any]] = []
        unknown: List[str] = []
        seen_keys: set[str] = set()
        for raw in items or []:
            cleaned = (raw or "").strip()
            if not cleaned:
                continue
            lookup = _normalize_text(cleaned)
            key = self.synonyms.get(lookup, lookup)
            entry = self.catalog.get(key)
            if entry and key not in seen_keys:
                seen_keys.add(key)
                resolved.append(
                    {
                        "input_name": cleaned,
                        "normalized": key,
                        "record": entry,
                    }
                )
            else:
                unknown.append(cleaned)
        return resolved, unknown

    def _build_profile_context(self, profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        profile = profile or {}

        def _clean_list(values: Any) -> List[str]:
            if not values:
                return []
            if isinstance(values, str):
                values = [v.strip() for v in values.split(",")]
            return [v for v in (str(item).strip() for item in values) if v]

        concerns = _clean_list(
            profile.get("concerns")
            or profile.get("skin_concerns")
            or profile.get("hair_concerns")
        )
        goals = _clean_list(profile.get("goals") or profile.get("overall_goals"))

        needs = []
        for raw_need in concerns + goals:
            canonical = self._canonical_need(raw_need)
            if canonical:
                needs.append(canonical)
        if not needs:
            needs = DEFAULT_NEEDS.copy()

        ctx = {
            "skin_type": _normalize_need(profile.get("skin_type")),
            "hair_type": _normalize_need(profile.get("hair_type")),
            "concerns": concerns,
            "goals": goals,
            "needs": needs,
        }
        ctx["is_sensitive"] = any("sensib" in n for n in needs)
        ctx["needs_display"] = {need: self._need_label(need) for need in needs}
        return ctx

    def _collect_function_keys(self) -> set[str]:
        keys = set(FUNCTION_LABELS.keys())
        for entry in self.catalog.values():
            keys.update(entry.data.get("functions", {}).keys())
        return keys

    def _canonical_need(self, value: Optional[str]) -> Optional[str]:
        norm = _normalize_need(value)
        if not norm:
            return None
        candidates = [
            norm,
            norm.replace(" ", "_"),
            norm.replace(" ", ""),
        ]
        # Remove connectors like "_de_" to match catalog keys
        candidates.extend([cand.replace("_de_", "_") for cand in candidates])
        for candidate in candidates:
            if candidate in self.function_keys:
                return candidate
        for candidate in candidates:
            for key in self.function_keys:
                if key and (candidate.startswith(key) or key in candidate):
                    return key
        return norm

    def _need_label(self, need: str) -> str:
        return FUNCTION_LABELS.get(need, _title_case(need.replace("_", " ")))

    def _determine_variant(self, variant: Optional[str], profile_ctx: Dict[str, Any]) -> str:
        if variant:
            normalized = _normalize_text(variant)
        else:
            normalized = ""

        if not normalized and profile_ctx.get("hair_type") in {"rizado", "ondulado"}:
            normalized = "botanical"
        if not normalized:
            normalized = "balanced"
        return normalized

    # -----------------------------
    # Scoring + heuristics
    # -----------------------------

    def _score_entries(self, entries: List[Dict[str, Any]], profile_ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
        scored = []
        for entry in entries:
            record = entry["record"]
            functions = record.data.get("functions", {})
            coverage_map = {
                need: functions.get(need, 0.0)
                for need in profile_ctx["needs"]
            }
            coverage_total = sum(coverage_map.values()) or sum(functions.values()) * 0.3
            compatibility = self._compute_compatibility(record.data, profile_ctx)
            evidence = record.data.get("evidence_level", 0.5)
            total_score = coverage_total * compatibility * (0.6 + evidence * 0.4)
            dominant_need = max(coverage_map, key=lambda k: coverage_map[k]) if coverage_map else None

            scored.append(
                {
                    **entry,
                    "score": round(total_score, 4),
                    "compatibility": round(compatibility, 3),
                    "coverage_map": coverage_map,
                    "dominant_need": dominant_need,
                    "reason": self._build_reason(record, dominant_need, profile_ctx),
                    "source": "detected",
                }
            )
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored

    def _compute_compatibility(self, record: Dict[str, Any], profile_ctx: Dict[str, Any]) -> float:
        compat = 1.0
        risk_flags = [(_normalize_need(flag) or "") for flag in record.get("risk_flags", [])]
        oil_soluble = record.get("compatibilities", {}).get("oil_soluble", False)

        if profile_ctx.get("is_sensitive") and any("irritante" in flag for flag in risk_flags):
            compat -= 0.35
        if profile_ctx.get("skin_type") == "grasa" and oil_soluble:
            compat -= 0.1
        if profile_ctx.get("skin_type") == "seca" and not oil_soluble:
            compat -= 0.05
        if profile_ctx.get("hair_type") == "rizado" and record.get("family") == "botanical":
            compat += 0.05
        return max(0.25, min(1.15, compat))

    def _build_reason(self, record: CatalogEntry, dominant_need: Optional[str], profile_ctx: Dict[str, Any]) -> str:
        label = self._need_label(dominant_need) if dominant_need else "Balance integral"
        family = record.data.get("family", "activo")
        persona = profile_ctx.get("skin_type") or profile_ctx.get("hair_type") or "tu perfil registrado"
        return f"{label} para {persona} con {family.replace('_', ' ')} de Mommyshops."

    def _aggregate_coverage(self, scored_entries: List[Dict[str, Any]], profile_ctx: Dict[str, Any]) -> Dict[str, float]:
        coverage = {need: 0.0 for need in profile_ctx["needs"]}
        for entry in scored_entries:
            for need, score in entry["coverage_map"].items():
                coverage[need] = coverage.get(need, 0.0) + score
        return coverage

    def _find_function_gaps(self, coverage: Dict[str, float], profile_ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
        gaps = []
        for need in profile_ctx["needs"]:
            current = coverage.get(need, 0.0)
            if current < 0.75:
                gaps.append(
                    {
                        "need": need,
                        "required": 0.75,
                        "current": current,
                        "missing": round(0.75 - current, 3),
                        "label": self._need_label(need),
                    }
                )
        return gaps

    def _variant_weight(self, record: CatalogEntry, variant_key: str) -> float:
        family = record.data.get("family", "")
        if variant_key == "botanical":
            return 1.2 if family == "botanical" else 0.8
        if variant_key in {"clinical", "clinico", "clínico"}:
            return 1.2 if family in {"clinical_active", "vitamin", "mineral"} else 0.85
        return 1.0

    def _suggest_additions(
        self,
        gaps: List[Dict[str, Any]],
        profile_ctx: Dict[str, Any],
        variant_key: str,
        used_ids: set[str],
    ) -> List[Dict[str, Any]]:
        additions: List[Dict[str, Any]] = []
        if not gaps:
            return additions

        for gap in gaps:
            candidate = self._best_candidate_for_gap(gap["need"], used_ids, variant_key)
            if not candidate:
                continue
            used_ids.add(candidate.id)
            additions.append(
                {
                    "record": candidate,
                    "score": gap["missing"] * 1.1 + candidate.data.get("evidence_level", 0.5),
                    "dominant_need": gap["need"],
                    "reason": f"Refuerza {gap['label'].lower()} faltante en tu perfil.",
                    "coverage_map": {gap["need"]: candidate.data.get("functions", {}).get(gap["need"], 0.6)},
                    "source": "ai_suggestion",
                    "compatibility": 0.85,
                }
            )
        return additions

    def _best_candidate_for_gap(self, need: str, used_ids: set[str], variant_key: str) -> Optional[CatalogEntry]:
        best_entry = None
        best_score = 0.0
        for entry in self.catalog.values():
            if entry.id in used_ids:
                continue
            func_score = entry.data.get("functions", {}).get(need, 0.0)
            if func_score <= 0:
                continue
            variant_weight = self._variant_weight(entry, variant_key)
            availability = entry.data.get("availability", "stock")
            availability_weight = 0.9 if availability == "stock" else 0.7
            evidence = entry.data.get("evidence_level", 0.5)
            score = func_score * variant_weight * (0.6 + evidence * 0.4) * availability_weight
            if score > best_score:
                best_score = score
                best_entry = entry
        return best_entry

    def _compose_formula(
        self,
        scored_entries: List[Dict[str, Any]],
        additions: List[Dict[str, Any]],
        profile_ctx: Dict[str, Any],
        variant_key: str,
        budget: Optional[float],
    ) -> List[Dict[str, Any]]:
        combined = scored_entries[:3] + additions
        if budget:
            combined = self._respect_budget(combined, budget)

        final_items: List[Dict[str, Any]] = []
        for item in combined:
            record_obj = item.get("record")
            if isinstance(record_obj, CatalogEntry):
                record = record_obj
            elif isinstance(record_obj, dict):
                key = _normalize_text(record_obj.get("inci_name") or record_obj.get("id") or "")
                record = CatalogEntry(key=key or record_obj.get("id", "custom"), data=record_obj)
            else:
                raise ValueError("Invalid record payload for formulation item")
            percent = self._estimate_percentage(record.data, item["score"])
            function_tags = self._top_functions(record.data.get("functions", {}), limit=3)
            final_items.append(
                {
                    **item,
                    "record": record,
                    "percent": percent,
                    "function_tags": function_tags,
                    "reason": item.get("reason") or self._build_reason(record, item.get("dominant_need"), profile_ctx),
                }
            )
        return final_items

    def _respect_budget(self, items: List[Dict[str, Any]], budget: float) -> List[Dict[str, Any]]:
        if not items:
            return items
        estimated = sum(item["record"].data.get("cost", 30.0) for item in items)
        if estimated <= budget:
            return items
        ratio = max(0.4, budget / estimated)
        limited = items[: max(2, int(len(items) * ratio))]
        return limited

    def _estimate_percentage(self, record: Dict[str, Any], score: float) -> float:
        usage = record.get("usage_range") or {}
        minimum = usage.get("min", 0.2)
        maximum = usage.get("max", minimum + 1.0)
        normalized = min(1.0, max(0.2, score))
        percent = minimum + (maximum - minimum) * (normalized / 1.5)
        return round(percent, 2)

    def _top_functions(self, functions: Dict[str, float], limit: int = 3) -> List[str]:
        sorted_funcs = sorted(functions.items(), key=lambda kv: kv[1], reverse=True)
        return [self._need_label(name) for name, _ in sorted_funcs[:limit]]

    def _build_summary(
        self,
        formula_items: List[Dict[str, Any]],
        coverage: Dict[str, float],
        gaps: List[Dict[str, Any]],
        profile_ctx: Dict[str, Any],
        variant_key: str,
        product_name: Optional[str],
    ) -> Dict[str, Any]:
        if formula_items:
            compatibility = sum(item.get("compatibility", 0.85) for item in formula_items) / len(formula_items)
        else:
            compatibility = 0.8
        highlights = [self._need_label(need) for need, score in sorted(coverage.items(), key=lambda kv: kv[1], reverse=True)[:3]]

        profile_hint = "Diseñado para tus necesidades registradas."
        if profile_ctx.get("skin_type") == "grasa":
            profile_hint = "Optimizado para controlar sebo sin irritar."
        elif profile_ctx.get("hair_type") == "rizado":
            profile_hint = "Botánicos inteligentes para rizos definidos y cuero cabelludo sano."

        return {
            "compatibility_score": round(compatibility, 2),
            "highlights": highlights,
            "missing": [gap["label"] for gap in gaps],
            "variant": variant_key,
            "variant_label": self._variant_label(variant_key),
            "profile_hint": profile_hint,
            "product_name": product_name or "Mommyshops Labs Custom Blend",
        }

    def _variant_label(self, variant_key: str) -> str:
        mapping = {
            "botanical": "Botánico",
            "balanced": "Balanceado",
            "clinical": "Clínico suave",
            "clinico": "Clínico suave",
            "clínico": "Clínico suave",
        }
        return mapping.get(variant_key, _title_case(variant_key or "Personalizado"))

    def _describe_originals(self, scored_entries: List[Dict[str, Any]], profile_ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
        described = []
        for entry in scored_entries:
            status = "mantener" if entry["score"] >= 0.5 else "potenciar" if entry["score"] >= 0.3 else "sustituir"
            described.append(
                {
                    "name": entry["input_name"],
                    "status": status,
                    "score": round(entry["score"], 2),
                    "note": entry["reason"],
                }
            )
        return described

    def _build_substitutions(self, additions: List[Dict[str, Any]], gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        substitutions = []
        for addition in additions:
            need = addition.get("dominant_need")
            gap = next((g for g in gaps if g["need"] == need), None)
            substitutions.append(
                {
                    "for": gap["label"] if gap else self._need_label(need or "Balance"),
                    "suggested": addition["record"].inci,
                    "reason": addition["reason"],
                }
            )
        return substitutions

    def _build_mockup(self, summary: Dict[str, Any], formula_items: List[Dict[str, Any]], product_name: Optional[str]) -> Dict[str, Any]:
        hero = [item["record"].inci for item in formula_items[:3]]
        return {
            "title": "Mommyshops Labs",
            "variant": summary.get("variant_label") or summary.get("variant", "balanced"),
            "tagline": f"{summary.get('product_name') or product_name or 'Custom Blend'} — {', '.join(hero[:3])}",
            "hero_ingredients": hero,
            "eta_days": "5-7 días hábiles",
        }

    def _seed_from_catalog(self, profile_ctx: Dict[str, Any], variant_key: str) -> List[Dict[str, Any]]:
        seeds = []
        used_ids: set[str] = set()
        for need in profile_ctx["needs"]:
            candidate = self._best_candidate_for_gap(need, used_ids, variant_key)
            if candidate:
                used_ids.add(candidate.id)
                seeds.append(
                    {
                        "record": candidate,
                        "input_name": candidate.inci,
                        "normalized": candidate.key,
                        "score": candidate.data.get("functions", {}).get(need, 0.7),
                        "compatibility": 0.9,
                        "coverage_map": {need: candidate.data.get("functions", {}).get(need, 0.7)},
                        "dominant_need": need,
                        "reason": f"Activo experto de Mommyshops para {self._need_label(need).lower()}.",
                        "source": "catalog_seed",
                    }
                )
        return seeds

    def _build_subtotals(self, formula_items: List[Dict[str, Any]]) -> Dict[str, float]:
        totals: Dict[str, float] = {}
        for item in formula_items:
            for need, score in item.get("coverage_map", {}).items():
                totals[need] = totals.get(need, 0.0) + score
        return totals

    def _fallback_catalog(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "niacinamide",
                "inci_name": "Niacinamide",
                "functions": {"control_grasa": 0.9, "barrera": 0.8},
                "usage_range": {"min": 2.0, "max": 6.0},
                "compatibilities": {"pH": [5.0, 7.0], "oil_soluble": False},
                "risk_flags": [],
                "evidence_level": 0.85,
                "family": "vitamin",
                "synonyms": ["Nicotinamide"],
                "availability": "stock",
            },
            {
                "id": "camellia_sinensis",
                "inci_name": "Camellia Sinensis Leaf Extract",
                "functions": {"antioxidante": 0.8, "antiinflamatorio": 0.7},
                "usage_range": {"min": 0.2, "max": 2.0},
                "compatibilities": {"pH": [4.5, 7.0], "oil_soluble": False},
                "risk_flags": [],
                "evidence_level": 0.7,
                "family": "botanical",
                "synonyms": ["Green Tea Extract"],
                "availability": "stock",
            },
        ]
