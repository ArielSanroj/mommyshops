"""
LLM utilities for ingredient analysis using OpenAI API
"""
import os
import json
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# OpenAI API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

async def analyze_ingredient_with_openai(ingredient: str, user_need: str = "general safety") -> Dict:
    """Analyze ingredient using OpenAI API."""
    try:
        import openai
        
        if not OPENAI_API_KEY:
            logger.warning("OpenAI API key not found, using fallback")
            return get_fallback_analysis(ingredient)
        
        client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        prompt = f"""
        Analiza el ingrediente cosmético "{ingredient}" para un usuario con necesidad: "{user_need}".
        
        Proporciona un análisis completo en formato JSON con los siguientes campos:
        {{
            "benefits": "Beneficios principales del ingrediente",
            "risks_detailed": "Riesgos específicos y precauciones",
            "risk_level": "seguro|riesgo bajo|riesgo medio|riesgo alto|cancerígeno|desconocido",
            "eco_score": número del 0-100 (100 = muy eco-friendly),
            "sources": "Fuentes de información utilizadas"
        }}
        
        Considera:
        - Seguridad para piel sensible si aplica
        - Impacto ambiental y biodegradabilidad
        - Evidencia científica disponible
        - Regulaciones internacionales (FDA, EWG, COSING)
        """
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un experto en ingredientes cosméticos y seguridad. Responde siempre en formato JSON válido."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        logger.info(f"OpenAI response for {ingredient}: {content[:200]}...")
        
        # Parse JSON response
        try:
            analysis = json.loads(content)
            return {
                "benefits": analysis.get("benefits", "No disponible"),
                "risks_detailed": analysis.get("risks_detailed", "No disponible"),
                "risk_level": analysis.get("risk_level", "desconocido"),
                "eco_score": float(analysis.get("eco_score", 50.0)),
                "sources": analysis.get("sources", "OpenAI GPT-4")
            }
        except json.JSONDecodeError:
            logger.error(f"Failed to parse OpenAI JSON response for {ingredient}")
            return get_fallback_analysis(ingredient)
            
    except Exception as e:
        logger.error(f"OpenAI API error for {ingredient}: {e}")
        return get_fallback_analysis(ingredient)

async def extract_ingredients_from_text_openai(text: str, image_data: bytes = None) -> List[str]:
    """Extract ingredients from text using NVIDIA Nemotron (preferred) or OpenAI API with improved prompt for noisy OCR text."""
    try:
        # Try NVIDIA Nemotron first (preferred)
        try:
            from nemotron_integration import extract_ingredients_with_nemotron
            ingredients = await extract_ingredients_with_nemotron(text)
            if ingredients:
                logger.info(f"NVIDIA Nemotron extracted {len(ingredients)} ingredients: {ingredients}")
                return ingredients
        except Exception as e:
            logger.warning(f"NVIDIA Nemotron failed: {e}")
        
        # Fallback to OpenAI if Nemotron fails
        import openai
        
        if not OPENAI_API_KEY:
            logger.warning("OpenAI API key not found, using regex fallback")
            return extract_ingredients_regex(text)
        
        client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        # Enhanced prompt for noisy OCR text
        prompt = f"""
        Extract ALL cosmetic INCI ingredients from this noisy OCR text from a product label.
        The text may contain garbled characters, missing letters, or OCR errors.
        
        Known ingredients to look for and correct:
        Water (Aqua), Cetearyl Alcohol, Glyceryl Stearate, PEG-100 Stearate, 
        Glycerin, Phenoxyethanol, Ethylhexylglycerin, Stearic Acid, 
        Parfum (Fragrance), Isopropyl Palmitate, Triethanolamine, 
        Acrylates/C10-30 Alkyl Acrylate Crosspolymer, Helianthus Annuus Seed Oil, 
        Aloe Barbadensis Leaf Extract, Avena Sativa Kernel Extract, 
        Gossypium Herbaceum Seed Oil, Citric Acid.
        
        Fix common OCR errors like:
        - 'glner' → 'glycerin'
        - 'celearyt' → 'cetearyl'
        - 'stearc' → 'stearic'
        - 'phenoxyeth' → 'phenoxyethanol'
        
        Text to analyze: {text[:4000]}
        
        Return only a comma-separated list of corrected ingredients.
        """
        
        # Prepare messages for OpenAI
        messages = [
            {"role": "system", "content": "Eres un experto en ingredientes cosméticos INCI. Extrae solo ingredientes cosméticos válidos de texto noisy/garbled. Ignora texto irrelevante."},
            {"role": "user", "content": prompt}
        ]
        
        # Add image if provided
        if image_data:
            import base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            messages = [
                {
                    "role": "system",
                    "content": "Eres un experto en ingredientes cosméticos INCI. Extrae solo ingredientes cosméticos válidos de imágenes de etiquetas de productos."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_b64}"
                            }
                        }
                    ]
                }
            ]
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.1,
            max_tokens=500
        )
        
        content = response.choices[0].message.content.strip()
        logger.info(f"OpenAI extracted ingredients: {content}")
        
        # Parse ingredients - más robusto para texto noisy
        ingredients = []
        for ing in content.split(','):
            ing = ing.strip().lower()
            if ing and len(ing) > 2:  # Filtrar strings muy cortos
                # Limpiar caracteres extraños comunes en OCR
                ing = ing.replace('\n', '').replace('\r', '').replace('*', '').replace('•', '')
                if ing:
                    ingredients.append(ing)
        
        logger.info(f"Parsed {len(ingredients)} ingredients from OpenAI")
        return ingredients
        
    except Exception as e:
        logger.error(f"OpenAI extraction error: {e}")
        return extract_ingredients_regex(text)

def extract_ingredients_regex(text: str) -> List[str]:
    """Enhanced regex-based ingredient extraction."""
    import re
    
    # Enhanced cosmetic ingredients patterns - más específicos para ingredientes faltantes
    patterns = [
        # Conservantes específicos
        r'\b(phenoxyethanol|ethylhexylglycerin|methylparaben|propylparaben|butylparaben|benzyl alcohol|sorbic acid|potassium sorbate)\b',
        # Estabilizantes y polímeros
        r'\b(acrylates?/c10-30\s+alkyl\s+acrylate\s+crosspolymer|acrylates?\s+crosspolymer|carbomer|polyacrylamide)\b',
        # Aceites naturales específicos
        r'\b(helianthus\s+annuus\s+seed\s+oil|sunflower\s+seed\s+oil|argania\s+spinosa\s+kernel\s+oil|olea\s+europaea\s+fruit\s+oil)\b',
        # Extractos específicos
        r'\b(avena\s+sativa\s+kernel\s+extract|oat\s+kernel\s+extract|aloe\s+barbadensis\s+leaf\s+extract|centella\s+asiatica\s+extract)\b',
        # Fragancias
        r'\b(parfum|fragrance|aroma|perfume)\b',
        # Ingredientes comunes
        r'\b(aqua|water|octocrylene|dimethicone|sodium hyaluronate|titanium dioxide|zinc oxide|avobenzone|homosalate|octinoxate|oxybenzone)\b',
        r'\b(propylene glycol|glycerin|hyaluronic acid|vitamin e|tocopherol|retinol|niacinamide|salicylic acid|glycolic acid)\b',
        r'\b(ethylhexyl|benzyl|methyl|propyl|butyl|isopropyl)\s+\w+',
        r'\b(peg-\d+|polysorbate \d+|sodium \w+|potassium \w+)\b',
        r'\b(citric acid|ascorbic acid|tocopherol|benzyl alcohol)\b',
        # Patrones más amplios para capturar ingredientes complejos
        r'\b[a-z]+\s+[a-z]+\s+(oil|extract|powder|wax|butter)\b',
        r'\b[a-z]+/[a-z]+\s+[a-z]+\s+[a-z]+\b'
    ]
    
    ingredients = set()
    for pattern in patterns:
        matches = re.findall(pattern, text, re.I)
        ingredients.update([match.lower() for match in matches])
    
    return list(ingredients)

def get_fallback_analysis(ingredient: str) -> Dict:
    """Fallback analysis when APIs fail."""
    # Basic analysis based on common knowledge
    fallback_data = {
        "retinol": {
            "benefits": "Anti-envejecimiento, mejora la textura de la piel",
            "risks_detailed": "Evitar durante el embarazo, puede causar irritación",
            "risk_level": "riesgo medio",
            "eco_score": 45.0,
            "sources": "FDA + CIR"
        },
        "aqua": {
            "benefits": "Hidratante base, solvente natural",
            "risks_detailed": "Ninguno conocido",
            "risk_level": "seguro",
            "eco_score": 95.0,
            "sources": "Basic Knowledge"
        },
        "octocrylene": {
            "benefits": "Filtro UVB, protege contra quemaduras solares",
            "risks_detailed": "Posible irritante ocular, disruptor endocrino potencial",
            "risk_level": "riesgo medio",
            "eco_score": 35.0,
            "sources": "EWG Research"
        },
        "dimethicone": {
            "benefits": "Suavizante, mejora la textura",
            "risks_detailed": "Generalmente considerado seguro",
            "risk_level": "seguro",
            "eco_score": 60.0,
            "sources": "FDA Database"
        }
    }
    
    ingredient_lower = ingredient.lower()
    if ingredient_lower in fallback_data:
        return fallback_data[ingredient_lower]
    
    # Generic fallback
    return {
        "benefits": "No disponible",
        "risks_detailed": "No disponible",
        "risk_level": "desconocido",
        "eco_score": 50.0,
        "sources": "Unknown"
    }

async def enrich_ingredient_data(ingredient: str, user_need: str = "general safety") -> Dict:
    """Enrich ingredient data using multiple sources."""
    from database import get_ingredient_data
    
    # First, check local database
    local_data = get_ingredient_data(ingredient)
    if local_data and local_data.get("risk_level") != "desconocido":
        logger.info(f"Found {ingredient} in local database")
        return local_data
    
    # Try OpenAI API
    try:
        openai_data = await analyze_ingredient_with_openai(ingredient, user_need)
        if openai_data.get("risk_level") != "desconocido":
            logger.info(f"Enriched {ingredient} with OpenAI")
            return openai_data
    except Exception as e:
        logger.error(f"OpenAI enrichment failed for {ingredient}: {e}")
    
    # Fallback to basic analysis
    logger.info(f"Using fallback analysis for {ingredient}")
    return get_fallback_analysis(ingredient)