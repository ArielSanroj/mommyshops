"""
High-level Ollama client integrated with the FastAPI app layer.
"""

import logging
import json
import re
import time
from typing import List, Dict, Any, Optional, AsyncGenerator

import httpx

from core.config import get_settings

logger = logging.getLogger(__name__)


class OllamaService:
    """
    Service wrapper around the Ollama HTTP API with structured output helpers.
    """

    def __init__(self):
        settings = get_settings()
        self.base_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = getattr(settings, "OLLAMA_MODEL", "llama3.2:1b")
        self.vision_model = getattr(settings, "OLLAMA_VISION_MODEL", "llava")
        # Aggressive timeout: max 15 seconds for all Ollama requests
        configured_timeout = getattr(settings, "OLLAMA_TIMEOUT", 15)
        self.timeout = min(15, max(5, configured_timeout))
        self.available = False
        self.available_models: List[str] = []
        self._check_availability()

    def _check_availability(self) -> None:
        """
        Detect Ollama availability and transparently fall back to any
        installed model if the configured one is missing.
        """
        try:
            import httpx
            with httpx.Client(timeout=2.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
        except Exception as exc:
            logger.warning(f"Ollama not available at {self.base_url}: {exc}")
            self.available = False
            self.available_models = []
            return

        if response.status_code != 200:
            self.available = False
            self.available_models = []
            logger.warning(f"Ollama service returned status {response.status_code}")
            return

        data = response.json()
        models = [
            (model or {}).get("name", "").strip()
            for model in data.get("models", [])
        ]
        self.available_models = [m for m in models if m]

        if not self.available_models:
            self.available = False
            logger.warning("Ollama responded without any models – check installation.")
            return

        selected_model = self._pick_available_model(self.available_models)
        if selected_model != self.model:
            logger.warning(
                "Configured Ollama model '%s' is unavailable. Using '%s' instead.",
                self.model,
                selected_model,
            )
            self.model = selected_model

        self.available = True
        logger.info(
            "Ollama service available at %s (models: %s)",
            self.base_url,
            ", ".join(self.available_models),
        )

    def _pick_available_model(self, candidates: List[str]) -> str:
        """
        Return the first installed model that matches the preferred order.
        """
        preferred_order = [
            self.model,
            "llama3.2:1b",
            "tinyllama:1.1b",
            "llama3.2:latest",
            "llama3:latest",
            "llama3.1",
            "llama3",
        ]
        for name in preferred_order:
            if name and name in candidates:
                return name
        return candidates[0]

    async def analyze_ingredients_structured(
        self,
        ingredients: List[str],
        user_conditions: Optional[List[str]] = None,
        profile_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Request a strict JSON analysis for each ingredient.
        """
        if not self.available:
            return {"items": [], "raw": "", "error": "Ollama service not available"}

        prompt = self._create_structured_prompt(
            ingredients,
            user_conditions or [],
            profile_context or {},
        )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                    },
                )
            except httpx.RequestError as e:
                error = f"Ollama connection error: {str(e)}"
                logger.error(error)
                return {"items": [], "raw": "", "error": error}

        if response.status_code != 200:
            error_msg = response.text if hasattr(response, 'text') else f"Status {response.status_code}"
            error = f"Ollama API error: {response.status_code} - {error_msg[:200]}"
            logger.error(error)
            # If 404, the model might not exist - try to list available models
            if response.status_code == 404:
                try:
                    async with httpx.AsyncClient(timeout=5.0) as check_client:
                        models_resp = await check_client.get(f"{self.base_url}/api/tags")
                        if models_resp.status_code == 200:
                            models_data = models_resp.json()
                            available = [m.get("name", "") for m in models_data.get("models", [])]
                            logger.warning(f"Model '{self.model}' not found. Available models: {', '.join(available[:5])}")
                except:
                    pass
            return {"items": [], "raw": "", "error": error}

        data = response.json()
        raw_response = data.get("response", "")
        
        # Log raw response for debugging (first 500 chars)
        logger.info(f"Ollama raw response (first 500 chars): {raw_response[:500]}")
        
        parsed = self._extract_json_payload(raw_response)

        if not isinstance(parsed, list):
            logger.error(f"Structured Ollama response is not a JSON array. Raw response (first 500): {raw_response[:500]}")
            logger.error(f"Parsed type: {type(parsed)}, value: {str(parsed)[:200]}")
            return {"items": [], "raw": raw_response, "error": "invalid_payload"}

        normalized: List[Dict[str, Any]] = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            name = (item.get("name") or item.get("ingredient") or "").strip()
            if not name:
                continue

            normalized.append(
                {
                    "name": name,
                    "score": self._safe_number(item.get("safety_score"), default=70, scale=100),
                    "ewg_score": self._safe_number(item.get("ewg_score"), default=5, scale=10),
                    "risk": self._normalize_risk(item.get("risk")),
                    "eco_friendly": bool(item.get("eco_friendly", False)),
                    "description": item.get("analysis") or item.get("description") or "",
                    "substitutes": item.get("substitutes") or item.get("alternatives") or [],
                }
            )

        return {"items": normalized, "raw": raw_response}

    async def analyze_ingredients(
        self, ingredients: List[str], user_conditions: List[str], analysis_type: str
    ) -> Dict[str, Any]:
        """
        Legacy free-form analysis used for complementary insights.
        """
        if not self.available:
            return {
                "analysis": "Ollama service not available",
                "confidence": 0.0,
                "recommendations": "",
                "processing_time_ms": 0,
            }

        prompt = self._create_analysis_prompt(ingredients, user_conditions, analysis_type)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
            )

        if response.status_code != 200:
            error = f"Ollama API error: {response.status_code}"
            logger.error(error)
            return {
                "analysis": error,
                "confidence": 0.0,
                "recommendations": "",
                "processing_time_ms": 0,
            }

        data = response.json()
        analysis = data.get("response", "")
        return {
            "analysis": analysis,
            "confidence": 0.8,
            "recommendations": self._extract_recommendations(analysis),
            "processing_time_ms": int(time.time() * 1000),
        }

    async def analyze_ingredients_stream(
        self, ingredients: List[str], user_conditions: List[str], analysis_type: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Simple streaming proxy (not heavily used in the current flow).
        """
        if not self.available:
            yield {"error": "Ollama service not available", "success": False}
            return

        prompt = self._create_analysis_prompt(ingredients, user_conditions, analysis_type)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": True},
            ) as response:
                if response.status_code != 200:
                    yield {"error": f"HTTP {response.status_code}", "success": False}
                    return

                async for line in response.aiter_lines():
                    payload = (line or "").strip()
                    if not payload:
                        continue
                    if payload.startswith("data: "):
                        payload = payload[6:]
                    yield {"data": payload, "success": True}

    # ------------------------------------------------------------------
    # Prompt builders and post-processing helpers
    # ------------------------------------------------------------------

    def _create_structured_prompt(
        self,
        ingredients: List[str],
        user_conditions: List[str],
        profile_context: Dict[str, Any],
    ) -> str:
        conditions = ", ".join(user_conditions) if user_conditions else "general"
        ingredient_lines = "\n".join(f"- {ing}" for ing in ingredients)
        profile_lines = []
        if profile_context:
            if profile_context.get("skin_type"):
                profile_lines.append(f"Tipo de piel: {profile_context['skin_type']}")
            if profile_context.get("hair_type"):
                profile_lines.append(f"Tipo de cabello: {profile_context['hair_type']}")
            if profile_context.get("face_shape"):
                profile_lines.append(f"Tipo de rostro: {profile_context['face_shape']}")
            if profile_context.get("skin_concerns"):
                profile_lines.append(
                    "Preocupaciones de piel: " + ", ".join(profile_context["skin_concerns"])
                )
            if profile_context.get("hair_concerns"):
                profile_lines.append(
                    "Preocupaciones de cabello: " + ", ".join(profile_context["hair_concerns"])
                )
            if profile_context.get("overall_goals"):
                profile_lines.append(
                    "Objetivos generales: " + ", ".join(profile_context["overall_goals"])
                )
        profile_block = "\n".join(profile_lines) if profile_lines else "Sin información adicional."
        return f"""Eres un experto en ingredientes cosméticos que evalúa la seguridad y proporciona alternativas.

INSTRUCCIONES:
- Responde ÚNICAMENTE con un array JSON válido, sin texto adicional antes o después
- Analiza cada ingrediente listado y proporciona información detallada
- Para extractos botánicos naturales, proporciona análisis basado en evidencia científica
- Incluye sustitutos específicos y relevantes, no genéricos

FORMATO REQUERIDO (array JSON):
[
  {{
    "name": "nombre exacto del ingrediente",
    "safety_score": 75,
    "ewg_score": 3,
    "risk": "low",
    "eco_friendly": true,
    "analysis": "Descripción corta del ingrediente, sus beneficios y consideraciones de seguridad en español",
    "substitutes": ["Sustituto 1", "Sustituto 2", "Sustituto 3"]
  }}
]

Perfil del usuario:
{profile_block}

Condiciones/Necesidades: {', '.join(conditions) if conditions else 'General'}

Ingredientes a analizar:
{ingredient_lines}

RESPONDE SOLO CON EL ARRAY JSON, SIN EXPLICACIONES ADICIONALES:"""

    def _create_analysis_prompt(self, ingredients: List[str], user_conditions: List[str], analysis_type: str) -> str:
        return f"""
Analiza los siguientes ingredientes cosméticos para {analysis_type}:

Ingredientes: {', '.join(ingredients)}
Condiciones del usuario: {', '.join(user_conditions) if user_conditions else 'General'}

Proporciona:
1. Análisis de seguridad de cada ingrediente
2. Nivel de riesgo (seguro, riesgo bajo, riesgo medio, riesgo alto, cancerígeno)
3. Beneficios y preocupaciones
4. Recomendaciones específicas
5. Puntuación de seguridad general (0-100)

Responde en español, sé claro y profesional.
"""

    @staticmethod
    def _extract_json_payload(raw_text: str) -> Any:
        try:
            cleaned = raw_text.strip()
            if cleaned.startswith("["):
                return json.loads(cleaned)
            match = re.search(r"(\[.*\])", cleaned, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to parse structured Ollama output: %s", exc)
        return []

    @staticmethod
    def _safe_number(value: Any, default: int, scale: int) -> int:
        try:
            number = float(value)
            if number < 0:
                return 0
            if number > scale:
                return scale
            return int(round(number))
        except Exception:
            return default

    @staticmethod
    def _normalize_risk(value: Any) -> str:
        if not value:
            return "moderate"
        text = str(value).strip().lower()
        if any(k in text for k in ("critical", "alto", "high", "severo")):
            return "high"
        if "moder" in text:
            return "moderate"
        if any(k in text for k in ("low", "bajo", "seguro", "safe")):
            return "low"
        return "moderate"

    @staticmethod
    def _extract_recommendations(analysis: str) -> str:
        try:
            lines = analysis.splitlines()
            findings = [
                line.strip()
                for line in lines
                if any(keyword in line.lower() for keyword in ("recomend", "sugerenc", "consejo"))
            ]
            return "\n".join(findings) if findings else ""
        except Exception as exc:  # pragma: no cover
            logger.error("Error extracting recommendations: %s", exc)
            return ""
