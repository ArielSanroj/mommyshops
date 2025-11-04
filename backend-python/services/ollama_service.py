"""
Ollama Service for MommyShops API
Handles AI-powered analysis using Ollama
"""

import logging
import time
from typing import List, Dict, Any, Optional, AsyncGenerator
import asyncio
import httpx
import json
import re

from app.core.config import get_settings

logger = logging.getLogger(__name__)

class OllamaService:
    """
    Service for Ollama AI integration
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = getattr(self.settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = getattr(self.settings, 'OLLAMA_MODEL', 'llama3.1')
        self.vision_model = getattr(self.settings, 'OLLAMA_VISION_MODEL', 'llava')
        self.timeout = getattr(self.settings, 'OLLAMA_TIMEOUT', 120)
        self.available = False
        self._check_availability()
    
    def _check_availability(self):
        """
        Check if Ollama service is available
        """
        try:
            # This would check if Ollama is running
            # For now, assume it's available
            self.available = True
        except Exception as e:
            logger.error(f"Ollama not available: {e}")
            self.available = False
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get Ollama service status
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                
                if response.status_code == 200:
                    data = response.json()
                    models = [model["name"] for model in data.get("models", [])]
                    
                    return {
                        "available": True,
                        "models": models,
                        "version": "unknown",
                        "base_url": self.base_url
                    }
                else:
                    return {
                        "available": False,
                        "models": [],
                        "version": "unknown",
                        "error": f"HTTP {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"Error checking Ollama status: {e}")
            return {
                "available": False,
                "models": [],
                "version": "unknown",
                "error": str(e)
            }
    
    async def analyze_ingredients_structured(
        self,
        ingredients: List[str],
        user_conditions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Request structured JSON analysis for each ingredient.
        """
        try:
            if not self.available:
                raise Exception("Ollama service not available")
            
            prompt = self._create_structured_prompt(ingredients, user_conditions or [])
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code}")
            
            data = response.json()
            raw_response = data.get("response", "")
            parsed = self._extract_json_payload(raw_response)
            
            if not isinstance(parsed, list):
                raise ValueError("Structured response is not a JSON array")
            
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
            
            if not normalized:
                raise ValueError("Structured response contained no valid ingredients")
            
            return {
                "items": normalized,
                "raw": raw_response
            }
        except Exception as exc:
            logger.error(f"Ollama structured ingredient analysis failed: {exc}")
            return {
                "items": [],
                "raw": "",
                "error": str(exc)
            }
    
    async def analyze_ingredients(self, ingredients: List[str], user_conditions: List[str], analysis_type: str) -> Dict[str, Any]:
        """
        Analyze ingredients using Ollama AI
        """
        try:
            if not self.available:
                raise Exception("Ollama service not available")
            
            # Create prompt for analysis
            prompt = self._create_analysis_prompt(ingredients, user_conditions, analysis_type)
            
            # Call Ollama API
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    analysis = data.get("response", "")
                    
                    return {
                        "analysis": analysis,
                        "confidence": 0.8,  # This would be calculated
                        "recommendations": self._extract_recommendations(analysis),
                        "processing_time_ms": int(time.time() * 1000)
                    }
                else:
                    raise Exception(f"Ollama API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error in Ollama analysis: {e}")
            return {
                "analysis": f"Error: {str(e)}",
                "confidence": 0.0,
                "recommendations": "No disponible",
                "processing_time_ms": 0
            }
    
    async def suggest_alternatives(self, problematic_ingredients: List[str], user_conditions: List[str], preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Suggest ingredient alternatives using Ollama AI
        """
        try:
            if not self.available:
                raise Exception("Ollama service not available")
            
            # Create prompt for alternatives
            prompt = self._create_alternatives_prompt(problematic_ingredients, user_conditions, preferences)
            
            # Call Ollama API
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get("response", "")
                    
                    return {
                        "alternatives": self._extract_alternatives(response_text),
                        "reasoning": self._extract_reasoning(response_text),
                        "confidence": 0.8,
                        "processing_time_ms": int(time.time() * 1000)
                    }
                else:
                    raise Exception(f"Ollama API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error in Ollama alternatives: {e}")
            return {
                "alternatives": [],
                "reasoning": f"Error: {str(e)}",
                "confidence": 0.0,
                "processing_time_ms": 0
            }
    
    async def analyze_ingredients_stream(self, ingredients: List[str], user_conditions: List[str], analysis_type: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream analysis results from Ollama AI
        """
        try:
            if not self.available:
                yield {"error": "Ollama service not available", "success": False}
                return
            
            # Create prompt for analysis
            prompt = self._create_analysis_prompt(ingredients, user_conditions, analysis_type)
            
            # Stream from Ollama API
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": True
                    }
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line.strip():
                                try:
                                    data = line.strip()
                                    if data.startswith("data: "):
                                        data = data[6:]
                                    if data:
                                        yield {"data": data, "success": True}
                                except Exception as e:
                                    yield {"error": str(e), "success": False}
                    else:
                        yield {"error": f"HTTP {response.status_code}", "success": False}
                        
        except Exception as e:
            logger.error(f"Error in Ollama streaming: {e}")
            yield {"error": str(e), "success": False}
    
    def _create_analysis_prompt(self, ingredients: List[str], user_conditions: List[str], analysis_type: str) -> str:
        """
        Create prompt for ingredient analysis
        """
        prompt = f"""
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
        return prompt
    
    def _create_structured_prompt(self, ingredients: List[str], user_conditions: List[str]) -> str:
        """
        Create prompt requesting strict JSON output for each ingredient.
        """
        conditions = ", ".join(user_conditions) if user_conditions else "general"
        ingredient_lines = "\n".join(f"- {ing}" for ing in ingredients)
        return f"""
Eres un químico cosmetólogo que evalúa ingredientes cosméticos para consumidores con condiciones: {conditions}.

Para cada ingrediente listado a continuación entrega únicamente un arreglo JSON donde cada objeto tenga los campos:
  name (string),
  safety_score (entero 0-100),
  ewg_score (entero 0-10),
  risk (\"low\", \"moderate\", \"high\" o \"critical\"),
  eco_friendly (boolean),
  analysis (string corto en español),
  substitutes (arreglo con hasta 3 alternativas seguras, strings).

Debes responder EXCLUSIVAMENTE con JSON válido, sin texto adicional.

Ingredientes:
{ingredient_lines}
"""
    
    def _create_alternatives_prompt(self, problematic_ingredients: List[str], user_conditions: List[str], preferences: Optional[Dict[str, Any]] = None) -> str:
        """
        Create prompt for ingredient alternatives
        """
        prompt = f"""
Sugiere alternativas seguras para estos ingredientes problemáticos:

Ingredientes problemáticos: {', '.join(problematic_ingredients)}
Condiciones del usuario: {', '.join(user_conditions) if user_conditions else 'General'}
Preferencias: {preferences if preferences else 'Ninguna'}

Proporciona:
1. Alternativas seguras para cada ingrediente
2. Razón por la cual son mejores
3. Consideraciones especiales
4. Nivel de confianza en las recomendaciones

Responde en español, sé específico y práctico.
"""
        return prompt
    
    def _extract_recommendations(self, analysis: str) -> str:
        """
        Extract recommendations from analysis text
        """
        try:
            # Simple extraction logic
            # This would be more sophisticated in production
            lines = analysis.split('\n')
            recommendations = []
            
            for line in lines:
                if any(keyword in line.lower() for keyword in ['recomendación', 'sugerencia', 'consejo']):
                    recommendations.append(line.strip())
            
            return '\n'.join(recommendations) if recommendations else "No se encontraron recomendaciones específicas."
            
        except Exception as e:
            logger.error(f"Error extracting recommendations: {e}")
            return "Error al extraer recomendaciones."
    
    def _extract_alternatives(self, response_text: str) -> List[str]:
        """
        Extract alternative ingredients from response
        """
        try:
            # Simple extraction logic
            # This would be more sophisticated in production
            alternatives = []
            lines = response_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('*'):
                    # Clean up the line
                    clean_line = line.replace('•', '').replace('-', '').strip()
                    if clean_line and len(clean_line) > 2:
                        alternatives.append(clean_line)
            
            return alternatives[:5]  # Return top 5 alternatives
            
        except Exception as e:
            logger.error(f"Error extracting alternatives: {e}")
            return []
    
    def _extract_reasoning(self, response_text: str) -> str:
        """
        Extract reasoning from response
        """
        try:
            # Simple extraction logic
            # This would be more sophisticated in production
            lines = response_text.split('\n')
            reasoning_lines = []
            
            for line in lines:
                if any(keyword in line.lower() for keyword in ['porque', 'debido a', 'ya que', 'por lo tanto']):
                    reasoning_lines.append(line.strip())
            
            return '\n'.join(reasoning_lines) if reasoning_lines else "No se proporcionó razonamiento específico."
            
        except Exception as e:
            logger.error(f"Error extracting reasoning: {e}")
            return "Error al extraer razonamiento."
    
    def _extract_json_payload(self, raw_text: str) -> Any:
        """
        Attempt to extract the first JSON array from the response.
        """
        try:
            cleaned = raw_text.strip()
            if cleaned.startswith("["):
                return json.loads(cleaned)
            match = re.search(r"(\[.*\])", cleaned, re.DOTALL)
            if match:
                snippet = match.group(1)
                return json.loads(snippet)
        except Exception as exc:
            logger.error(f"Failed to parse structured Ollama output: {exc}")
        return []

    @staticmethod
    def _safe_number(value: Any, default: int, scale: int) -> int:
        """
        Convert a value to an integer bounded by the provided scale.
        """
        try:
            number = float(value)
            if number < 0:
                return 0
            if number > scale:
                return int(scale)
            return int(round(number))
        except Exception:
            return default

    @staticmethod
    def _normalize_risk(value: Any) -> str:
        """
        Normalize textual risk indicators into canonical categories.
        """
        if not value:
            return "moderate"
        text = str(value).strip().lower()
        if any(keyword in text for keyword in ["critical", "alto", "high", "severo"]):
            return "high"
        if any(keyword in text for keyword in ["moderado", "moderate"]):
            return "moderate"
        if any(keyword in text for keyword in ["bajo", "low", "seguro", "safe"]):
            return "low"
        return "moderate"
