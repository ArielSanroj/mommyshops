#!/usr/bin/env python3
"""
Análisis rápido de ingredientes con puntuaciones
"""

import os
import sys
from dotenv import load_dotenv
from PIL import Image
import pytesseract
import requests
import json
import time

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def quick_ingredient_analysis():
    """Análisis rápido de ingredientes"""
    
    print("🧪 ANÁLISIS RÁPIDO DE INGREDIENTES")
    print("=" * 50)
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Ruta de la imagen de prueba
    image_path = "/Users/arielsanroj/Downloads/test3.jpg"
    
    print(f"📸 Imagen: {os.path.basename(image_path)}")
    
    # 1. OCR
    print("\n1️⃣ EXTRACCIÓN DE TEXTO...")
    try:
        tesseract_path = os.getenv('TESSERACT_PATH', '/opt/homebrew/bin/tesseract')
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        tesseract_text = pytesseract.image_to_string(Image.open(image_path))
        print(f"✅ Texto extraído: {tesseract_text.strip()}")
    except Exception as e:
        print(f"❌ Error en OCR: {e}")
        return False
    
    # 2. Análisis rápido con Ollama
    print("\n2️⃣ ANÁLISIS RÁPIDO CON OLLAMA...")
    try:
        prompt = f"""Analyze these cosmetic ingredients quickly and provide safety and eco scores:

Ingredients: {tesseract_text}

Provide brief analysis in JSON format:
{{
    "ingredients": ["list", "of", "ingredients"],
    "overall_safety_score": 1-10,
    "overall_eco_score": 1-10,
    "risk_level": "Low|Moderate|High",
    "eco_level": "Low|Moderate|High",
    "safe_ingredients": ["safe1", "safe2"],
    "moderate_ingredients": ["mod1", "mod2"],
    "caution_ingredients": ["caution1", "caution2"],
    "recommendation": "safe|moderate|caution"
}}"""
        
        payload = {
            "model": "llama3.1:8b",
            "prompt": prompt,
            "stream": False
        }
        
        start_time = time.time()
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=60
        )
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            analysis_response = data.get('response', '')
            print(f"✅ Análisis completado en {end_time - start_time:.1f} segundos")
            
            # Intentar parsear JSON
            try:
                json_start = analysis_response.find('{')
                json_end = analysis_response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = analysis_response[json_start:json_end]
                    analysis = json.loads(json_str)
                    
                    # Mostrar resultados
                    print(f"\n📊 RESULTADOS:")
                    print(f"   🛡️  Puntuación de Seguridad: {analysis.get('overall_safety_score', 'N/A')}/10")
                    print(f"   🌱 Puntuación Eco-Friendly: {analysis.get('overall_eco_score', 'N/A')}/10")
                    print(f"   ⚠️  Nivel de Riesgo: {analysis.get('risk_level', 'N/A')}")
                    print(f"   🌍 Nivel Eco: {analysis.get('eco_level', 'N/A')}")
                    
                    ingredients = analysis.get('ingredients', [])
                    if ingredients:
                        print(f"\n🧪 INGREDIENTES DETECTADOS ({len(ingredients)}):")
                        for i, ingredient in enumerate(ingredients, 1):
                            print(f"   {i}. {ingredient}")
                    
                    safe = analysis.get('safe_ingredients', [])
                    moderate = analysis.get('moderate_ingredients', [])
                    caution = analysis.get('caution_ingredients', [])
                    
                    if safe:
                        print(f"\n✅ INGREDIENTES SEGUROS ({len(safe)}):")
                        for ingredient in safe:
                            print(f"   - {ingredient}")
                    
                    if moderate:
                        print(f"\n🟡 INGREDIENTES MODERADOS ({len(moderate)}):")
                        for ingredient in moderate:
                            print(f"   - {ingredient}")
                    
                    if caution:
                        print(f"\n⚠️  INGREDIENTES DE PRECAUCIÓN ({len(caution)}):")
                        for ingredient in caution:
                            print(f"   - {ingredient}")
                    
                    recommendation = analysis.get('recommendation', 'N/A')
                    print(f"\n📋 RECOMENDACIÓN GENERAL: {recommendation.upper()}")
                    
                    # Análisis detallado de cada ingrediente
                    print(f"\n🔍 ANÁLISIS DETALLADO POR INGREDIENTE:")
                    for ingredient in ingredients:
                        print(f"\n   📝 {ingredient}:")
                        
                        # Análisis individual
                        individual_prompt = f"""Quick analysis of this cosmetic ingredient: {ingredient}

Provide brief info in JSON:
{{
    "safety_score": 1-10,
    "eco_score": 1-10,
    "risk_level": "Low|Moderate|High",
    "common_use": "brief description",
    "concerns": ["concern1", "concern2"],
    "benefits": ["benefit1", "benefit2"]
}}"""
                        
                        individual_payload = {
                            "model": "llama3.1:8b",
                            "prompt": individual_prompt,
                            "stream": False
                        }
                        
                        try:
                            individual_response = requests.post(
                                "http://localhost:11434/api/generate",
                                json=individual_payload,
                                timeout=30
                            )
                            
                            if individual_response.status_code == 200:
                                individual_data = individual_response.json()
                                individual_analysis = individual_data.get('response', '')
                                
                                try:
                                    json_start = individual_analysis.find('{')
                                    json_end = individual_analysis.rfind('}') + 1
                                    if json_start != -1 and json_end > json_start:
                                        json_str = individual_analysis[json_start:json_end]
                                        individual = json.loads(json_str)
                                        
                                        print(f"      🛡️  Seguridad: {individual.get('safety_score', 'N/A')}/10")
                                        print(f"      🌱 Eco: {individual.get('eco_score', 'N/A')}/10")
                                        print(f"      ⚠️  Riesgo: {individual.get('risk_level', 'N/A')}")
                                        print(f"      💡 Uso: {individual.get('common_use', 'N/A')}")
                                        print(f"      ⚠️  Preocupaciones: {', '.join(individual.get('concerns', []))}")
                                        print(f"      ✅ Beneficios: {', '.join(individual.get('benefits', []))}")
                                    else:
                                        print(f"      📝 {individual_analysis[:100]}...")
                                except json.JSONDecodeError:
                                    print(f"      📝 {individual_analysis[:100]}...")
                        except Exception as e:
                            print(f"      ❌ Error: {e}")
                    
                    return analysis
                else:
                    print(f"📝 Análisis en texto:")
                    print(f"   {analysis_response[:300]}...")
                    return {"raw_response": analysis_response}
            except json.JSONDecodeError:
                print(f"📝 Análisis en texto:")
                print(f"   {analysis_response[:300]}...")
                return {"raw_response": analysis_response}
        else:
            print(f"❌ Error: {response.status_code}")
            return {}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {}
    
    print("\n🎉 ANÁLISIS COMPLETADO!")
    return True

if __name__ == "__main__":
    print("🚀 Iniciando análisis rápido de ingredientes...")
    result = quick_ingredient_analysis()
    
    if result:
        print("\n✅ Análisis completado exitosamente!")
    else:
        print("\n❌ El análisis falló.")
        sys.exit(1)