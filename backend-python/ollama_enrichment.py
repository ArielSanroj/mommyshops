"""
Utility helpers to derive structured ingredient insights using the Ollama LLM.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from ollama_integration import ollama_integration

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Eres una dermocosmetóloga que evalúa ingredientes cosméticos y responde "
    "SIEMPRE en JSON válido."
)

JSON_TEMPLATE = """Devuelve solo un JSON con la forma:
{
  "ingredient": "<nombre en minusculas>",
  "summary": "Resumen accionable (máximo 240 caracteres)",
  "risks": ["riesgo 1", "riesgo 2"],
  "alternatives": [
    {"name": "Ingrediente o producto", "brand": "Marca opcional", "reason": "Motivo del reemplazo"}
  ]
}
Si no hay datos, deja los campos como cadenas vacías o listas vacías.
"""


def _extract_json(text: str) -> Optional[str]:
    """Find the first JSON object in a block of text."""
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start : end + 1]


async def enrich_ingredient_with_ollama(
    ingredient: str,
    user_conditions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Generate a structured enrichment payload for a single ingredient."""
    if not ingredient or not ollama_integration.is_available():
        return {}

    conditions = ", ".join(user_conditions or []) or "sin condiciones específicas"
    user_prompt = (
        f"Analiza el ingrediente cosmético '{ingredient}'. La persona presenta: {conditions}. "
        f"{JSON_TEMPLATE}"
    )

    try:
        response = await ollama_integration.async_client.chat(
            model=ollama_integration.default_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            stream=False,
        )

        content: str
        if isinstance(response, dict):
            if isinstance(response.get("message"), dict):
                content = response["message"].get("content", "")
            else:
                content = response.get("content", "") or str(response)
        else:
            content = str(response)

        json_blob = _extract_json(content)
        if not json_blob:
            logger.warning("Ollama enrichment did not return JSON for %s", ingredient)
            return {
                "ingredient": ingredient.lower(),
                "summary": content.strip()[:240],
                "risks": [],
                "alternatives": [],
            }

        data = json.loads(json_blob)
        if not isinstance(data, dict):
            return {}

        data.setdefault("ingredient", ingredient.lower())
        data.setdefault("summary", "")
        data.setdefault("risks", [])
        data.setdefault("alternatives", [])
        return data
    except Exception as exc:
        logger.error("Ollama enrichment failed for %s: %s", ingredient, exc)
        return {}


def enrich_ingredient_with_ollama_sync(
    ingredient: str,
    user_conditions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Synchronous helper for scripts."""
    return asyncio.run(enrich_ingredient_with_ollama(ingredient, user_conditions=user_conditions))
