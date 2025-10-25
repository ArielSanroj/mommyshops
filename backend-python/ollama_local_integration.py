#!/usr/bin/env python3
"""
Integración con Ollama local para procesamiento de imágenes y OCR mejorado
"""

import os
import sys
import base64
import requests
import json
from typing import Optional, Dict, Any, List
from PIL import Image
import io

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class OllamaLocalIntegration:
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.model = "llama3.1:8b"
    
    def test_connection(self) -> bool:
        """Probar conexión con Ollama local"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Error testing Ollama connection: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Obtener modelos disponibles"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except Exception as e:
            print(f"Error getting models: {e}")
            return []
    
    def analyze_text_with_llama(self, text: str, prompt: str = None) -> Optional[str]:
        """Analizar texto usando Llama local"""
        try:
            if not prompt:
                prompt = """Analyze this text and provide a detailed analysis in JSON format:
{
    "product_name": "extracted product name",
    "brand": "extracted brand",
    "product_type": "type of cosmetic product",
    "ingredients": ["list", "of", "ingredients"],
    "claims": ["list", "of", "claims"],
    "warnings": ["list", "of", "warnings"],
    "net_content": "net content/volume",
    "safety_notes": "safety observations"
}

Text to analyze:"""
            
            full_prompt = f"{prompt}\n\n{text}"
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "max_tokens": 2000
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('response', '')
            else:
                print(f"Error in Ollama API: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error analyzing text with Llama: {e}")
            return None
    
    def improve_ocr_text(self, text: str) -> Optional[str]:
        """Mejorar texto extraído por OCR usando Llama"""
        try:
            prompt = f"""Improve and correct this OCR text extracted from a cosmetic product label. 
Fix spelling errors, complete missing words, and format it properly.

Original OCR text:
{text}

Please provide the corrected and improved text:"""
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=20
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('response', '')
            else:
                print(f"Error improving OCR text: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error improving OCR text: {e}")
            return None
    
    def analyze_ingredients_safety(self, ingredients: List[str]) -> Optional[Dict[str, Any]]:
        """Analizar seguridad de ingredientes usando Llama"""
        try:
            ingredients_text = ", ".join(ingredients)
            
            prompt = f"""Analyze the safety of these cosmetic ingredients and provide a safety assessment in JSON format:

Ingredients: {ingredients_text}

Please provide analysis in this JSON format:
{{
    "overall_safety_score": 1-10,
    "safety_level": "Very Safe|Safe|Moderate|Caution|Dangerous",
    "ingredient_analysis": [
        {{
            "ingredient": "name",
            "safety_score": 1-10,
            "concerns": ["concern1", "concern2"],
            "benefits": ["benefit1", "benefit2"],
            "recommendation": "string"
        }}
    ],
    "recommendations": ["rec1", "rec2"],
    "warnings": ["warning1", "warning2"]
}}"""
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get('response', '')
                
                try:
                    # Intentar extraer JSON de la respuesta
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    if json_start != -1 and json_end > json_start:
                        json_str = content[json_start:json_end]
                        return json.loads(json_str)
                    else:
                        return {
                            "raw_response": content,
                            "overall_safety_score": 5,
                            "safety_level": "Moderate"
                        }
                except json.JSONDecodeError:
                    return {
                        "raw_response": content,
                        "overall_safety_score": 5,
                        "safety_level": "Moderate"
                    }
            else:
                print(f"Error analyzing ingredients: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error analyzing ingredients safety: {e}")
            return None

def test_ollama_local():
    """Probar la integración con Ollama local"""
    print("🧪 PROBANDO INTEGRACIÓN CON OLLAMA LOCAL")
    print("=" * 50)
    
    ollama = OllamaLocalIntegration()
    
    # 1. Probar conexión
    print("1️⃣ Probando conexión...")
    if ollama.test_connection():
        print("✅ Conexión exitosa con Ollama local")
    else:
        print("❌ Error de conexión")
        return False
    
    # 2. Obtener modelos
    print("\n2️⃣ Obteniendo modelos disponibles...")
    models = ollama.get_available_models()
    if models:
        print(f"✅ Modelos disponibles: {len(models)}")
        for model in models:
            print(f"   - {model}")
    else:
        print("⚠️  No se pudieron obtener modelos")
    
    # 3. Probar análisis de texto
    print("\n3️⃣ Probando análisis de texto...")
    test_text = "Natura feeling - LOCION HIDRATANTE CORPORAL Con extracto de aloe vera PROBADO DERMATOLOGICAMENTE CONT. NETO 1000 ML"
    
    result = ollama.analyze_text_with_llama(test_text)
    if result:
        print("✅ Análisis de texto exitoso")
        print(f"   Resultado: {result[:200]}...")
    else:
        print("❌ Error en análisis de texto")
    
    # 4. Probar mejora de OCR
    print("\n4️⃣ Probando mejora de OCR...")
    improved = ollama.improve_ocr_text(test_text)
    if improved:
        print("✅ Mejora de OCR exitosa")
        print(f"   Original: {test_text}")
        print(f"   Mejorado: {improved}")
    else:
        print("❌ Error en mejora de OCR")
    
    # 5. Probar análisis de ingredientes
    print("\n5️⃣ Probando análisis de ingredientes...")
    ingredients = ["aloe vera", "glycerin", "water", "fragrance"]
    safety_result = ollama.analyze_ingredients_safety(ingredients)
    if safety_result:
        print("✅ Análisis de ingredientes exitoso")
        print(f"   Puntuación: {safety_result.get('overall_safety_score', 'N/A')}")
        print(f"   Nivel: {safety_result.get('safety_level', 'N/A')}")
    else:
        print("❌ Error en análisis de ingredientes")
    
    print("\n🎉 Prueba de integración completada")
    return True

if __name__ == "__main__":
    test_ollama_local()