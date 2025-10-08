"""
Nemotron Integration for MommyShops
Enhanced multimodal AI for ingredient analysis
"""
import os
import json
import logging
import asyncio
from typing import Any, Dict, List, Optional, Union
from dotenv import load_dotenv
import httpx
from PIL import Image
import base64
import io

load_dotenv()
logger = logging.getLogger(__name__)

# NVIDIA API configuration
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_ENDPOINT = "https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions"

class NemotronAnalyzer:
    """Enhanced ingredient analyzer using NVIDIA Llama 3.1 with Nemotron-inspired prompts."""
    
    def __init__(self):
        self.api_key = NVIDIA_API_KEY
        self.endpoint = NVIDIA_ENDPOINT
        self.model = "meta/llama-4-maverick-17b-128e-instruct"  # Correct model ID with "e" for experts
        
    async def analyze_ingredient_multimodal(
        self, 
        ingredient: str, 
        image_data: Optional[bytes] = None,
        user_need: str = "general safety"
    ) -> Dict:
        """Analyze ingredient using Nemotron's multimodal capabilities."""
        try:
            messages = []
            
            # Enhanced system prompt inspired by Nemotron's advanced reasoning
            system_prompt = f"""
            You are an advanced AI system with graduate-level expertise in cosmetic chemistry, toxicology, and regulatory science. 
            You specialize in multimodal analysis combining chemical knowledge, regulatory data, and safety assessments for {user_need}.
            
            For ingredient "{ingredient}", perform comprehensive analysis using advanced reasoning:
            
            CHEMICAL ANALYSIS:
            - Molecular structure and functional groups
            - Physical-chemical properties (solubility, stability, pH sensitivity)
            - Mechanism of action and biological pathways
            - Metabolism and elimination pathways
            
            SAFETY ASSESSMENT:
            - Acute and chronic toxicity data
            - Carcinogenicity, mutagenicity, reproductive toxicity (IARC, FDA, EWG classifications)
            - Skin sensitization and irritation potential
            - Systemic absorption and bioavailability
            - Dose-response relationships and NOAEL/LOAEL values
            
            REGULATORY INTELLIGENCE:
            - FDA GRAS status and cosmetic regulations
            - EU Cosmetics Regulation (Annex II/III/IV/V/VI)
            - EWG Skin Deep database ratings
            - CIR, SCCS, and ICCR safety assessments
            - Global regulatory status and restrictions
            
            ENVIRONMENTAL IMPACT:
            - Biodegradability and persistence
            - Aquatic toxicity and bioaccumulation
            - Carbon footprint and sustainability metrics
            - Green chemistry principles compliance
            
            CLINICAL EFFICACY:
            - Evidence-based benefits and mechanisms
            - Clinical trial data and peer-reviewed studies
            - Optimal concentration ranges for efficacy
            - Synergistic or antagonistic interactions
            
            Provide structured analysis in JSON format:
            {{
                "benefits": "Detailed scientific benefits with mechanisms of action",
                "risks_detailed": "Comprehensive risk assessment with scientific basis",
                "risk_level": "seguro|riesgo bajo|riesgo medio|riesgo alto|cancerígeno|desconocido",
                "eco_score": number from 0-100 (100 = most eco-friendly),
                "sources": "FDA, CIR, SCCS, ICCR, and regulatory databases",
                "concentration_safe": "Evidence-based safe concentration range",
                "pregnancy_safe": "Pregnancy and breastfeeding safety assessment",
                "interactions": "Known pharmacological and chemical interactions"
            }}
            """
            
            messages.append({"role": "system", "content": system_prompt})
            
            # Add image if provided
            if image_data:
                # Convert image to base64
                image_b64 = base64.b64encode(image_data).decode('utf-8')
                
                # Add multimodal prompt
                multimodal_prompt = f"""
                Analyze this cosmetic product image for ingredient "{ingredient}".
                
                Look for:
                - Ingredient list on the label
                - Concentration information
                - Product type and intended use
                - Any safety warnings or certifications
                - Brand and formulation details
                
                Use this visual information to enhance your analysis of "{ingredient}".
                """
                
                messages.append({
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": multimodal_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}"
                            }
                        }
                    ]
                })
            else:
                # Text-only analysis
                messages.append({
                    "role": "user", 
                    "content": f"Analyze the cosmetic ingredient: {ingredient}"
                })
            
            # Call Nemotron API
            response = await self._call_nemotron_api(messages)
            
            if response:
                return self._parse_nemotron_response(response)
            else:
                return self._get_fallback_analysis(ingredient)
                
        except Exception as e:
            logger.error(f"Nemotron analysis error for {ingredient}: {e}")
            return self._get_fallback_analysis(ingredient)
    
    async def _call_nemotron_api(self, messages: List[Dict]) -> Optional[str]:
        """Call NVIDIA Nemotron API with corrected 2025 NVCF endpoint and model."""
        try:
            # Enhanced API call with proper headers and timeout
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # NVIDIA NIM endpoints for 2025 compatibility with correct model ID
            endpoints_to_try = [
                "https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions/meta/llama-4-maverick-17b-128e-instruct",
                "https://api.nvcf.nvidia.com/v2/nvcf/infer/functions/meta-llama-4-maverick-17b-128e-instruct",
                "https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions/meta/llama-3.1-8b-instruct",
                "https://api.nvcf.nvidia.com/v2/nvcf/infer/functions/meta-llama3-8b-instruct"
            ]
            
            models_to_try = [
                "meta/llama-4-maverick-17b-128e-instruct",
                "meta-llama-4-maverick-17b-128e-instruct",
                "meta/llama-3.1-8b-instruct",
                "meta-llama/llama-3.1-8b-instruct"
            ]
            
            # Use first endpoint/model combination
            corrected_endpoint = endpoints_to_try[0]
            corrected_model = models_to_try[0]
            
            payload = {
                "messages": messages,
                "model": corrected_model,
                "max_tokens": 512,
                "temperature": 0.2,
                "top_p": 0.7
            }
            
            logger.info(f"Calling NVIDIA API with corrected model: {corrected_model}")
            logger.info(f"Using endpoint: {corrected_endpoint}")
            
            # Try multiple endpoints/models until one works
            async with httpx.AsyncClient(timeout=30.0) as client:
                for i, endpoint in enumerate(endpoints_to_try):
                    model = models_to_try[i] if i < len(models_to_try) else models_to_try[0]
                    
                    payload["model"] = model
                    
                    try:
                        logger.info(f"Trying endpoint {i+1}/{len(endpoints_to_try)}: {endpoint}")
                        logger.info(f"Using model: {model}")
                        
                        response = await client.post(endpoint, headers=headers, json=payload)
                        
                        if response.status_code == 404:
                            logger.warning(f"404 Error with endpoint {i+1}, trying next...")
                            continue
                        
                        response.raise_for_status()
                        
                        result = response.json()
                        content = result.get('choices', [{}])[0].get('message', {}).get('content')
                        logger.info(f"NVIDIA API response received: {content[:100]}...")
                        return content
                        
                    except httpx.HTTPStatusError as e:
                        if e.response.status_code == 404:
                            logger.warning(f"404 Error with endpoint {i+1}, trying next...")
                            continue
                        else:
                            logger.error(f"HTTP error with endpoint {i+1}: {e.response.status_code}")
                            continue
                    except Exception as e:
                        logger.warning(f"Error with endpoint {i+1}: {e}")
                        continue
                
                # If all endpoints failed
                logger.error("All NVIDIA endpoints failed - Check model ID or deploy NIM at build.nvidia.com")
                return None
                
        except httpx.TimeoutException:
            logger.error("NVIDIA API timeout")
            return None
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.error("404: Invalid endpoint/model - Redeploy at build.nvidia.com")
                logger.error(f"Response: {e.response.text}")
            else:
                logger.error(f"NVIDIA API HTTP error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"NVIDIA API error: {e}")
            return None
    
    async def extract_ingredients_multimodal(self, image_data: bytes) -> List[str]:
        """Extract ingredients from image using NVIDIA multimodal capabilities."""
        try:
            # Convert image to base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            # Enhanced multimodal prompt for ingredient extraction
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert cosmetic chemist with advanced OCR and image analysis capabilities. Your task is to extract EVERY SINGLE cosmetic INCI ingredient from product labels, even from blurry, distorted, or partially obscured text. You must be extremely thorough and find ALL ingredients listed on the label."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "CRITICAL: Extract EVERY cosmetic ingredient from this product label image. Look carefully for ALL text, even small print, blurry text, or text in different sections. Common ingredients to specifically look for include: Water (Aqua), Cetearyl Alcohol, Glyceryl Stearate, PEG-100 Stearate, Glycerin, Phenoxyethanol, Ethylhexylglycerin, Stearic Acid, Parfum (Fragrance), Isopropyl Palmitate, Triethanolamine, Acrylates/C10-30 Alkyl Acrylate Crosspolymer, Helianthus Annuus Seed Oil, Aloe Barbadensis Leaf Extract, Avena Sativa Kernel Extract, Gossypium Herbaceum Seed Oil, Citric Acid, Sodium Hyaluronate, Dimethicone, Cyclomethicone, Tocopherol, Retinol, Niacinamide, Salicylic Acid, Glycolic Acid, Lactic Acid, Ceramides, Peptides, Hyaluronic Acid. Fix OCR errors like 'glner'→'glycerin', 'celearyt'→'cetearyl', 'stearate'→'stearate'. Return ONLY a comma-separated list of corrected INCI ingredient names. Be extremely thorough - find ALL ingredients!"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_b64}"
                            }
                        }
                    ]
                }
            ]
            
            logger.info("Calling NVIDIA multimodal API for ingredient extraction...")
            response = await self._call_nemotron_api(messages)
            
            if response:
                # Parse ingredients from response
                ingredients = []
                for ingredient in response.split(','):
                    ingredient = ingredient.strip()
                    if ingredient and len(ingredient) > 2:
                        ingredients.append(ingredient)
                
                logger.info(f"NVIDIA multimodal extracted {len(ingredients)} ingredients: {ingredients}")
                return ingredients
            else:
                logger.warning("NVIDIA multimodal extraction failed")
                return []
                
        except Exception as e:
            logger.error(f"NVIDIA multimodal extraction error: {e}")
            return []

    async def suggest_substitutes_from_profile(
        self,
        user_profile: Dict[str, Any],
        current_product: str,
        issues: List[str],
        safe_ingredients: List[str],
        excluded_ingredients: List[str],
        candidate_products: List[Dict[str, Any]],
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """Use NVIDIA LLM to pick best substitutes from candidate list for given user profile."""
        if not self.api_key:
            logger.warning("NVIDIA API key not configured; skipping Nemotron recommendations")
            return []

        if not candidate_products:
            return []

        profile_summary = self._format_user_profile(user_profile)
        issues_summary = "\n".join(f"- {item}" for item in issues) if issues else "- Sin alertas específicas; busca alternativas más seguras y efectivas."
        safe_summary = ", ".join(safe_ingredients) if safe_ingredients else "ningún ingrediente seguro clave detectado"
        excluded_summary = ", ".join(excluded_ingredients) if excluded_ingredients else "ningún ingrediente crítico detectado"

        indexed_candidates: List[Dict[str, Any]] = []
        candidate_lines: List[str] = []
        for idx, item in enumerate(candidate_products, start=1):
            enriched = item.copy()
            enriched["candidate_id"] = idx
            indexed_candidates.append(enriched)

            ingredients_preview = ", ".join(enriched.get("ingredients", [])[:8]) or "Ingredientes no disponibles"
            candidate_lines.append(
                f"{idx}. {enriched.get('name')} | Marca: {enriched.get('brand') or 'N/D'} | Eco-score: {enriched.get('eco_score') or 'N/D'} | Riesgo: {enriched.get('risk_level') or 'N/D'} | Categoría: {enriched.get('category') or 'N/D'} | Ingredientes clave: {ingredients_preview}"
            )

        candidates_block = "\n".join(candidate_lines) if candidate_lines else "Sin candidatos disponibles"

        prompt = f"""
Estás ayudando a Personal Shopper MommyShops a sustituir el producto "{current_product}" por opciones más seguras y alineadas con el perfil del usuario.

Perfil del usuario (resumen normalizado):
{profile_summary}

Alertas detectadas en el producto actual:
{issues_summary}

Ingredientes seguros detectados: {safe_summary}
Ingredientes que deben evitarse: {excluded_summary}

Lista de candidatos disponibles (elige solo de este listado, usando el `candidate_id`):
{candidates_block}

Evalúa cada candidato considerando necesidades de piel, cabello, clima, objetivos y condiciones médicas del usuario. Elige hasta {top_k} sustitutos.

Responde en JSON estricto con el formato:
{{
  "recommendations": [
    {{
      "candidate_id": <numero>,
      "score": <0-1 indicando afinidad>,
      "reason": "Explicación breve en español resaltando compatibilidad con el perfil",
      "match_goals": ["Objetivos del usuario que cumple"],
      "avoids": ["Ingredientes problemáticos que evita"],
      "key_ingredients": ["Activos relevantes"]
    }}
  ]
}}

Si ningún candidato es apto, devuelve:
{{ "recommendations": [] }}
"""

        messages = [
            {
                "role": "system",
                "content": (
                    "Eres una especialista en dermocosmética. Prioriza seguridad, control de condiciones como alergias y necesidades de hidratación."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        logger.info("Calling NVIDIA API for substitute recommendations with %d candidates", len(indexed_candidates))
        response = await self._call_nemotron_api(messages)
        if not response:
            return []

        try:
            return self._parse_substitute_response(response, indexed_candidates, top_k)
        except Exception as exc:
            logger.error("Failed to parse NVIDIA substitute response: %s", exc)
            return []

    def _get_enhanced_fallback_analysis(self, ingredient: str) -> str:
        """Enhanced fallback analysis with Nemotron-style reasoning."""
        # Basic ingredient knowledge for common ingredients
        ingredient_lower = ingredient.lower()
        
        if "retinol" in ingredient_lower:
            return """
            {
                "benefits": "Anti-aging, mejora textura de la piel, reduce arrugas finas",
                "risks_detailed": "Puede causar irritación, fotosensibilidad, evitar durante embarazo",
                "risk_level": "riesgo medio",
                "eco_score": 60,
                "sources": "Enhanced Analysis Database",
                "concentration_safe": "0.1-1.0%",
                "pregnancy_safe": "No recomendado",
                "interactions": "Evitar con ácidos y vitamina C"
            }
            """
        elif "niacinamide" in ingredient_lower:
            return """
            {
                "benefits": "Regula producción de sebo, mejora barrera cutánea, antiinflamatorio",
                "risks_detailed": "Generalmente bien tolerado, posible irritación leve",
                "risk_level": "seguro",
                "eco_score": 85,
                "sources": "Enhanced Analysis Database",
                "concentration_safe": "2-10%",
                "pregnancy_safe": "Sí, seguro",
                "interactions": "Compatible con la mayoría de ingredientes"
            }
            """
        elif "hyaluronic" in ingredient_lower:
            return """
            {
                "benefits": "Hidratación intensa, mejora volumen, suaviza arrugas",
                "risks_detailed": "Muy seguro, raramente causa reacciones",
                "risk_level": "seguro",
                "eco_score": 90,
                "sources": "Enhanced Analysis Database",
                "concentration_safe": "0.1-2%",
                "pregnancy_safe": "Sí, seguro",
                "interactions": "Sinergia con péptidos y ceramidas"
            }
            """
        else:
            return """
            {
                "benefits": "Análisis detallado no disponible en base de datos",
                "risks_detailed": "Consulte dermatólogo para evaluación personalizada",
                "risk_level": "desconocido",
                "eco_score": 50,
                "sources": "Enhanced Analysis Database",
                "concentration_safe": "Consultar etiqueta",
                "pregnancy_safe": "Consultar médico",
                "interactions": "Revisar con especialista"
            }
            """

    def _format_user_profile(self, user_profile: Dict[str, Any]) -> str:
        parts: List[str] = []
        if not user_profile:
            return "- Perfil no disponible"

        skin_face = user_profile.get("skin_face")
        if skin_face:
            parts.append(f"- Piel facial: {skin_face}")

        skin_body = user_profile.get("skin_body")
        if skin_body:
            parts.append(f"- Piel corporal: {', '.join(skin_body)}")

        hair_type = user_profile.get("hair_type")
        if hair_type:
            parts.append(f"- Tipo de cabello: {hair_type}")

        hair_porosity = user_profile.get("hair_porosity")
        if hair_porosity:
            parts.append(f"- Porosidad: {', '.join(hair_porosity)}")

        hair_thickness = user_profile.get("hair_thickness")
        if hair_thickness:
            parts.append(f"- Grosor del cabello: {', '.join(hair_thickness)}")

        scalp = user_profile.get("scalp")
        if scalp:
            parts.append(f"- Cuero cabelludo: {', '.join(scalp)}")

        climate = user_profile.get("climate")
        if climate:
            parts.append(f"- Clima: {climate}")

        goals_face = user_profile.get("goals_face")
        if goals_face:
            parts.append(f"- Objetivos rostro: {', '.join(goals_face)}")

        goals_body = user_profile.get("goals_body")
        if goals_body:
            parts.append(f"- Objetivos cuerpo: {', '.join(goals_body)}")

        goals_hair = user_profile.get("goals_hair")
        if goals_hair:
            ordered = ", ".join(f"{goal} ({score}/5)" for goal, score in goals_hair.items())
            parts.append(f"- Objetivos cabello: {ordered}")

        conditions = user_profile.get("conditions")
        if conditions:
            parts.append(f"- Condiciones/alertas: {', '.join(conditions)}")

        return "\n".join(parts) if parts else "- Perfil no disponible"

    def _extract_json_blob(self, response: str) -> Optional[str]:
        if not response:
            return None
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            if end == -1:
                end = len(response)
            return response[start:end].strip()
        if "{" in response and "}" in response:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end != -1:
                return response[start:end]
        return None

    def _parse_substitute_response(
        self,
        response: str,
        candidates: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        json_blob = self._extract_json_blob(response)
        if not json_blob:
            raise ValueError("No JSON block found in NVIDIA response")

        payload = json.loads(json_blob)
        recommendations = payload.get("recommendations")
        if recommendations is None:
            if isinstance(payload, list):
                recommendations = payload
            else:
                raise ValueError("NVIDIA response missing 'recommendations' key")

        id_map = {str(item.get("candidate_id")): item for item in candidates}
        name_map = {str(item.get("name", "")).strip().lower(): item for item in candidates if item.get("name")}

        results: List[Dict[str, Any]] = []
        for entry in recommendations:
            if not isinstance(entry, dict):
                continue

            candidate = None
            candidate_id = entry.get("candidate_id") or entry.get("id")
            if candidate_id is not None:
                candidate = id_map.get(str(candidate_id))

            if candidate is None:
                name = entry.get("name")
                if name:
                    candidate = name_map.get(str(name).strip().lower())

            if candidate is None:
                continue

            result = candidate.copy()
            result.pop("candidate_id", None)

            reason = entry.get("reason") or candidate.get("reason")
            if reason:
                result["reason"] = reason

            score = entry.get("score")
            if score is not None:
                try:
                    result["similarity"] = float(score)
                except (TypeError, ValueError):
                    pass

            if entry.get("match_goals"):
                result["match_goals"] = entry.get("match_goals")
            if entry.get("avoids"):
                result["avoids"] = entry.get("avoids")
            if entry.get("key_ingredients"):
                result["key_ingredients"] = entry.get("key_ingredients")

            results.append(result)
            if len(results) >= top_k:
                break

        return results
    
    def _parse_nemotron_response(self, response: str) -> Dict:
        """Parse Nemotron response and extract structured data."""
        try:
            # Try to extract JSON from response
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
            else:
                # Fallback to text parsing
                return self._parse_text_response(response)
            
            data = json.loads(json_str)
            
            # Ensure all required fields exist
            return {
                "benefits": data.get("benefits", "No disponible"),
                "risks_detailed": data.get("risks_detailed", "No disponible"),
                "risk_level": data.get("risk_level", "desconocido"),
                "eco_score": data.get("eco_score", 50),
                "sources": data.get("sources", "Nemotron Analysis"),
                "concentration_safe": data.get("concentration_safe", "No especificado"),
                "pregnancy_safe": data.get("pregnancy_safe", "Consultar médico"),
                "interactions": data.get("interactions", "No conocidas")
            }
            
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON response, using text parsing")
            return self._parse_text_response(response)
        except Exception as e:
            logger.error(f"Error parsing Nemotron response: {e}")
            return self._get_fallback_analysis("unknown")
    
    def _parse_text_response(self, response: str) -> Dict:
        """Parse text response when JSON parsing fails."""
        # Simple text parsing for key information
        response_lower = response.lower()
        
        # Determine risk level from text
        if any(word in response_lower for word in ["safe", "seguro", "low risk", "bajo riesgo"]):
            risk_level = "seguro"
        elif any(word in response_lower for word in ["moderate", "medio", "caution", "precaución"]):
            risk_level = "riesgo medio"
        elif any(word in response_lower for word in ["high risk", "alto riesgo", "dangerous", "peligroso"]):
            risk_level = "riesgo alto"
        elif any(word in response_lower for word in ["carcinogen", "cancerígeno"]):
            risk_level = "cancerígeno"
        else:
            risk_level = "desconocido"
        
        # Estimate eco score from text
        eco_score = 50  # Default
        if any(word in response_lower for word in ["eco-friendly", "biodegradable", "natural", "sustainable"]):
            eco_score = 75
        elif any(word in response_lower for word in ["synthetic", "chemical", "artificial"]):
            eco_score = 40
        
        return {
            "benefits": response[:200] + "..." if len(response) > 200 else response,
            "risks_detailed": "Análisis detallado no disponible en formato texto",
            "risk_level": risk_level,
            "eco_score": eco_score,
            "sources": "Nemotron Text Analysis",
            "concentration_safe": "No especificado",
            "pregnancy_safe": "Consultar médico",
            "interactions": "No conocidas"
        }
    
    def _get_fallback_analysis(self, ingredient: str) -> Dict:
        """Fallback analysis when Nemotron is unavailable."""
        return {
            "benefits": "Análisis no disponible",
            "risks_detailed": "Consulte base de datos profesional",
            "risk_level": "desconocido",
            "eco_score": 50,
            "sources": "Fallback Analysis",
            "concentration_safe": "No especificado",
            "pregnancy_safe": "Consultar médico",
            "interactions": "No conocidas"
        }

# Global instance
nemotron_analyzer = NemotronAnalyzer()

async def analyze_with_nemotron(
    ingredient: str, 
    image_data: Optional[bytes] = None,
    user_need: str = "general safety"
) -> Dict:
    """Convenience function for Nemotron analysis."""
    return await nemotron_analyzer.analyze_ingredient_multimodal(
        ingredient, image_data, user_need
    )


async def suggest_substitutes_with_nemotron(
    user_profile: Dict[str, Any],
    current_product: str,
    issues: List[str],
    safe_ingredients: List[str],
    excluded_ingredients: List[str],
    candidate_products: List[Dict[str, Any]],
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """Wrapper to generate substitute recommendations using Nemotron."""
    return await nemotron_analyzer.suggest_substitutes_from_profile(
        user_profile=user_profile,
        current_product=current_product,
        issues=issues,
        safe_ingredients=safe_ingredients,
        excluded_ingredients=excluded_ingredients,
        candidate_products=candidate_products,
        top_k=top_k,
    )


async def enrich_with_nemotron_async(
    ingredient: str,
    user_conditions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Get Nemotron enrichment (risks, alternatives) for a single ingredient."""
    if not ingredient or not NVIDIA_API_KEY:
        return {}

    conditions_text = ", ".join(user_conditions or []) or "sin condiciones específicas"
    prompt = (
        "Eres una dermocosmetóloga experta. Analiza el ingrediente '"
        f"{ingredient}' para una persona con condiciones: {conditions_text}. "
        "Responde solo en JSON con la forma {\"ingredient\": str, \"summary\": str, "
        "\"risks\": [str], \"alternatives\": [{\"name\": str, \"brand\": str, \"reason\": str}]}."
    )

    messages = [
        {
            "role": "system",
            "content": "Eres una dermocosmetóloga que genera análisis concisos y accionables.",
        },
        {"role": "user", "content": prompt},
    ]

    response = await nemotron_analyzer._call_nemotron_api(messages)
    if not response:
        return {}

    try:
        json_blob = nemotron_analyzer._extract_json_blob(response)
        if not json_blob:
            return {}
        payload = json.loads(json_blob)
        if not isinstance(payload, dict):
            return {}
        payload.setdefault("ingredient", ingredient)
        return payload
    except json.JSONDecodeError:
        logger.warning("Nemotron enrichment JSON parse failed for %s", ingredient)
        return {}


def enrich_with_nemotron(
    ingredient: str,
    user_conditions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Synchronous helper for scripts that need Nemotron enrichment."""
    if not ingredient:
        return {}
    return asyncio.run(enrich_with_nemotron_async(ingredient, user_conditions=user_conditions))

# Test function
async def test_nemotron():
    """Test Nemotron integration."""
    print("🧪 Testing Nemotron integration...")
    
    # Test with sample ingredient
    result = await analyze_with_nemotron("retinol", user_need="sensible skin")
    
    print("✅ Nemotron test completed!")
    print(f"Risk Level: {result['risk_level']}")
    print(f"Eco Score: {result['eco_score']}")
    print(f"Benefits: {result['benefits'][:100]}...")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_nemotron())