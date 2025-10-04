"""
Nemotron Integration for MommyShops
Enhanced multimodal AI for ingredient analysis
"""
import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Union
from dotenv import load_dotenv
import httpx
from PIL import Image
import base64
import io

load_dotenv()
logger = logging.getLogger(__name__)

# NVIDIA API configuration
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "***REMOVED***")
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