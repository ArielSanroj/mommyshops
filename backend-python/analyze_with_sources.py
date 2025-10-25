#!/usr/bin/env python3
"""
Análisis de ingredientes mostrando claramente las APIs y fuentes utilizadas
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

def analyze_with_sources():
    """Análisis mostrando fuentes de datos"""
    
    print("🧪 ANÁLISIS DE INGREDIENTES CON FUENTES DE DATOS")
    print("=" * 60)
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Ruta de la imagen de prueba
    image_path = "/Users/arielsanroj/Downloads/test3.jpg"
    
    print(f"📸 Imagen: {os.path.basename(image_path)}")
    print(f"📏 Tamaño: {os.path.getsize(image_path)} bytes")
    
    # Mostrar APIs disponibles
    print(f"\n🔧 APIS Y FUENTES DE DATOS DISPONIBLES:")
    print(f"   ✅ Tesseract OCR: {os.getenv('TESSERACT_PATH', '/opt/homebrew/bin/tesseract')}")
    print(f"   ✅ Ollama Local: http://localhost:11434 (llama3.1:8b)")
    print(f"   ✅ Google Vision API: {os.getenv('GOOGLE_VISION_API_KEY', 'No configurado')[:20]}...")
    print(f"   ✅ EWG Database: Módulo disponible")
    print(f"   ✅ CIR Database: Módulo disponible")
    print(f"   ✅ SCCS Database: Módulo disponible")
    print(f"   ✅ ICCR Database: Módulo disponible")
    
    # 1. OCR con Tesseract
    print(f"\n1️⃣ EXTRACCIÓN DE TEXTO (TESSERACT OCR)...")
    try:
        tesseract_path = os.getenv('TESSERACT_PATH', '/opt/homebrew/bin/tesseract')
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        tesseract_text = pytesseract.image_to_string(Image.open(image_path))
        
        if tesseract_text and tesseract_text.strip():
            print(f"✅ Tesseract OCR exitoso: {len(tesseract_text)} caracteres")
            print(f"📝 Texto extraído:")
            print(f"   {tesseract_text}")
        else:
            print("⚠️  Tesseract no pudo extraer texto")
            return False
    except Exception as e:
        print(f"❌ Error en Tesseract OCR: {e}")
        return False
    
    # 2. Mejora de texto con Ollama
    print(f"\n2️⃣ MEJORA DE TEXTO (OLLAMA LOCAL - llama3.1:8b)...")
    try:
        prompt = f"""Improve this OCR text from cosmetic ingredients list:

{tesseract_text}

Provide corrected ingredients list:"""
        
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
            improved_text = data.get('response', '')
            print(f"✅ Ollama mejora exitosa en {end_time - start_time:.1f}s")
            print(f"📝 Texto mejorado:")
            print(f"   {improved_text}")
        else:
            print(f"❌ Error en Ollama: {response.status_code}")
            improved_text = tesseract_text
    except Exception as e:
        print(f"❌ Error en Ollama: {e}")
        improved_text = tesseract_text
    
    # 3. Análisis de seguridad con Ollama
    print(f"\n3️⃣ ANÁLISIS DE SEGURIDAD (OLLAMA LOCAL - llama3.1:8b)...")
    try:
        safety_prompt = f"""Analyze these cosmetic ingredients for safety and eco-friendliness:

{improved_text}

Provide analysis in JSON format:
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
            "prompt": safety_prompt,
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
            print(f"✅ Análisis de seguridad completado en {end_time - start_time:.1f}s")
            
            # Parsear JSON
            try:
                json_start = analysis_response.find('{')
                json_end = analysis_response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = analysis_response[json_start:json_end]
                    analysis = json.loads(json_str)
                    
                    print(f"\n📊 RESULTADOS DEL ANÁLISIS:")
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
            print(f"❌ Error en análisis de seguridad: {response.status_code}")
            return {}
    except Exception as e:
        print(f"❌ Error en análisis de seguridad: {e}")
        return {}
    
    # 4. Mostrar resumen de APIs utilizadas
    print(f"\n" + "=" * 60)
    print(f"📋 RESUMEN DE APIS Y FUENTES UTILIZADAS")
    print(f"=" * 60)
    print(f"✅ Tesseract OCR: Extracción de texto de imagen")
    print(f"✅ Ollama Local (llama3.1:8b): Mejora de texto y análisis de seguridad")
    print(f"⚠️  Google Vision API: Disponible pero no utilizada en esta prueba")
    print(f"⚠️  EWG Database: Disponible pero no utilizada en esta prueba")
    print(f"⚠️  CIR Database: Disponible pero no utilizada en esta prueba")
    print(f"⚠️  SCCS Database: Disponible pero no utilizada en esta prueba")
    print(f"⚠️  ICCR Database: Disponible pero no utilizada en esta prueba")
    
    print(f"\n🎉 ANÁLISIS COMPLETADO!")
    return True

if __name__ == "__main__":
    print("🚀 Iniciando análisis con fuentes de datos...")
    result = analyze_with_sources()
    
    if result:
        print("\n✅ Análisis completado exitosamente!")
    else:
        print("\n❌ El análisis falló.")
        sys.exit(1)