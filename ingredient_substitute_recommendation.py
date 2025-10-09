"""Ingredient analysis and substitution helpers for recommendation workflows."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import httpx

from api_utils_production import fetch_ingredient_data
from database import canonicalize_ingredients
from product_catalog_service import product_catalog_service


SAFE_RISK_LEVELS = {"", "seguro", "riesgo bajo"}
ECO_FRIENDLY_THRESHOLD = 70.0
DEFAULT_SUBSTITUTE_MESSAGE = "alternativa natural (ej. aloe vera, glicerina vegetal)"


DEFAULT_SUBSTITUTE_MAP = {
    "paraben": "extracto de romero",
    "parabeno": "extracto de romero",
    "parabenos": "extracto de romero",
    "phthalate": "chamomile extract",
    "ftalato": "extracto de manzanilla",
    "sodium lauryl sulfate": "cocamidopropyl betaine",
    "sodium laureth sulfate": "decyl glucoside",
    "formaldehyde": "fermentos naturales",
    "formaldehido": "fermentos naturales",
    "triclosan": "aceite de árbol de té",
    "triclocarban": "aceite de árbol de té",
}


logger = logging.getLogger(__name__)


@dataclass
class IngredientAssessment:
    name: str
    risk_level: str
    eco_score: Optional[float]
    eco_status: str
    risks_detailed: Optional[str]
    sources: Optional[str]
    is_risky: bool

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "risk_level": self.risk_level,
            "eco_score": self.eco_score,
            "eco_status": self.eco_status,
            "risks_detailed": self.risks_detailed,
            "sources": self.sources,
            "is_risky": self.is_risky,
        }


async def _fetch_analysis(name: str, client: httpx.AsyncClient) -> IngredientAssessment:
    try:
        payload = await fetch_ingredient_data(name, client)
    except Exception as exc:  # pragma: no cover - network resilience
        return IngredientAssessment(
            name=name,
            risk_level="desconocido",
            eco_score=None,
            eco_status="desconocido",
            risks_detailed=str(exc),
            sources=None,
            is_risky=True,
        )

    risk_level = str(payload.get("risk_level", "desconocido") or "desconocido").lower()
    eco_score = payload.get("eco_score")
    eco_status = "eco-friendly"
    if eco_score is None or eco_score < ECO_FRIENDLY_THRESHOLD:
        eco_status = "needs attention"

    is_risky = risk_level not in SAFE_RISK_LEVELS or eco_status != "eco-friendly"
    risks_detailed = payload.get("risks_detailed") or None
    sources = payload.get("sources") or None

    return IngredientAssessment(
        name=name,
        risk_level=risk_level,
        eco_score=eco_score,
        eco_status=eco_status,
        risks_detailed=risks_detailed,
        sources=sources,
        is_risky=is_risky,
    )


async def analyze_ingredients(ingredients: Sequence[str]) -> List[IngredientAssessment]:
    cleaned = [item.strip() for item in ingredients if isinstance(item, str) and item.strip()]
    if not cleaned:
        return []

    canonical = canonicalize_ingredients(cleaned)
    # Preserve order with fallbacks if canonicalization fails
    targets = canonical or [item.lower() for item in cleaned]

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [_fetch_analysis(name, client) for name in targets]
        results = await asyncio.gather(*tasks)

    # Deduplicate while preserving input order
    seen: set[str] = set()
    assessments: List[IngredientAssessment] = []
    for assessment in results:
        key = assessment.name.lower()
        if key in seen:
            continue
        seen.add(key)
        assessments.append(assessment)
    return assessments


def find_substitutes(risky_ingredients: Iterable[str]) -> List[Dict[str, str]]:
    substitutes: List[Dict[str, str]] = []
    for ingredient in risky_ingredients:
        key = ingredient.lower()
        substitute = DEFAULT_SUBSTITUTE_MAP.get(key, DEFAULT_SUBSTITUTE_MESSAGE)
        substitutes.append({"original": ingredient, "substitute": substitute})
    return substitutes


def _split_ingredients(assessments: Sequence[IngredientAssessment]) -> Tuple[List[str], List[str]]:
    safe: List[str] = []
    risky: List[str] = []
    for item in assessments:
        if item.is_risky:
            risky.append(item.name)
        else:
            safe.append(item.name)
    return safe, risky


async def recommend_products(
    assessments: Sequence[IngredientAssessment],
    recommender,
    *,
    user_conditions: Optional[Sequence[str]] = None,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    safe_ingredients, risky_ingredients = _split_ingredients(assessments)

    # Ensure we have at least some query terms for the recommender
    query_ingredients = safe_ingredients or risky_ingredients
    if not query_ingredients:
        return []

    catalog_updated = False
    candidate_products: List[Dict[str, Any]] = []

    try:
        catalog_updated, candidate_products = await product_catalog_service.ensure_catalog(
            query_ingredients,
            user_conditions=user_conditions,
            max_products=max(top_k * 4, 12),
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("Product catalog expansion failed: %s", exc)

    loop = asyncio.get_event_loop()
    if catalog_updated:
        await loop.run_in_executor(None, recommender.rebuild)
    else:
        await loop.run_in_executor(None, recommender.ensure_loaded)

    suggestions = recommender.suggest_substitutes(
        ingredients=query_ingredients,
        excluded_ingredients=risky_ingredients,
        target_product_name=None,
        user_conditions=list(user_conditions or []),
        top_k=top_k,
    )

    formatted: List[Dict[str, Any]] = []
    for suggestion in suggestions:
        formatted.append(
            {
                "product_id": suggestion.get("product_id"),
                "name": suggestion.get("name"),
                "brand": suggestion.get("brand"),
                "eco_score": suggestion.get("eco_score"),
                "risk_level": suggestion.get("risk_level"),
                "reason": suggestion.get("reason"),
                "similarity": suggestion.get("similarity"),
                "category": suggestion.get("category"),
                "rating_average": suggestion.get("rating_average"),
                "rating_count": int(suggestion.get("rating_count", 0) or 0),
            }
        )

    if formatted:
        return formatted

    fallback: List[Dict[str, Any]] = []
    for candidate in candidate_products:
        entry = {
            "product_id": candidate.get("product_id"),
            "name": candidate.get("name"),
            "brand": candidate.get("brand"),
            "eco_score": candidate.get("eco_score"),
            "risk_level": candidate.get("risk_level"),
            "reason": candidate.get("reason") or "Coincidencia externa",
            "similarity": round(float(candidate.get("match_score", 0.0)), 4),
            "category": candidate.get("category"),
            "rating_average": candidate.get("rating_average"),
            "rating_count": int(candidate.get("rating_count", 0) or 0),
        }
        fallback.append(entry)
        if len(fallback) >= top_k:
            break

    return fallback


async def generate_recommendations(
    ingredients: Sequence[str],
    recommender,
    *,
    user_conditions: Optional[Sequence[str]] = None,
    top_k: int = 3,
) -> Dict[str, List[Dict[str, Any]]]:
    assessments = await analyze_ingredients(ingredients)

    substitutes = find_substitutes(
        [item.name for item in assessments if item.is_risky]
    )

    recommendations = await recommend_products(
        assessments,
        recommender,
        user_conditions=user_conditions,
        top_k=top_k,
    )

    return {
        "analysis": [item.as_dict() for item in assessments],
        "substitutes": substitutes,
        "recommendations": recommendations,
    }


__all__ = [
    "IngredientAssessment",
    "analyze_ingredients",
    "find_substitutes",
    "recommend_products",
    "generate_recommendations",
]
