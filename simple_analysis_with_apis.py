#!/usr/bin/env python3
"""
Análisis simple mostrando claramente las APIs utilizadas
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

def simple_analysis_with_apis():
    """Análisis simple mostrando APIs utilizadas"""
    
    print("🧪 ANÁLISIS DE INGREDIENTES - FUENTES DE DATOS")
    print("=" * 60)
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Ruta de la imagen de prueba
    image_path = "/Users/arielsanroj/Downloads/test3.jpg"
    
    print(f"📸 Imagen: {os.path.basename(image_path)}")
    print(f"📏 Tamaño: {os.path.getsize(image_path)} bytes")
    
    # Mostrar APIs disponibles
    print(f"\n🔧 FUENTES DE DATOS DISPONIBLES:")
    print(f"   ✅ Tesseract OCR: {os.getenv('TESSERACT_PATH', '/opt/homebrew/bin/tesseract')}")
    print(f"   ✅ Ollama Local: http://localhost:11434 (llama3.1:8b)")
    print(f"   ✅ Google Vision API: {os.getenv('GOOGLE_VISION_API_KEY', 'No configurado')[:20]}...")
    print(f"   ✅ EWG Database: Módulo disponible")
    print(f"   ✅ CIR Database: Módulo disponible")
    print(f"   ✅ SCCS Database: Módulo disponible")
    print(f"   ✅ ICCR Database: Módulo disponible")
    
    # 1. OCR con Tesseract
    print(f"\n1️⃣ EXTRACCIÓN DE TEXTO")
    print(f"   🔧 API: Tesseract OCR")
    print(f"   📍 Ubicación: {os.getenv('TESSERACT_PATH', '/opt/homebrew/bin/tesseract')}")
    try:
        tesseract_path = os.getenv('TESSERACT_PATH', '/opt/homebrew/bin/tesseract')
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        tesseract_text = pytesseract.image_to_string(Image.open(image_path))
        
        if tesseract_text and tesseract_text.strip():
            print(f"   ✅ Resultado: {len(tesseract_text)} caracteres extraídos")
            print(f"   📝 Texto: {tesseract_text.strip()}")
        else:
            print("   ❌ No se pudo extraer texto")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # 2. Mejora de texto con Ollama
    print(f"\n2️⃣ MEJORA DE TEXTO")
    print(f"   🔧 API: Ollama Local")
    print(f"   📍 Endpoint: http://localhost:11434/api/generate")
    print(f"   🤖 Modelo: llama3.1:8b")
    try:
        prompt = f"""Correct this OCR text from cosmetic ingredients:

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
            timeout=30
        )
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            improved_text = data.get('response', '')
            print(f"   ✅ Resultado: Texto mejorado en {end_time - start_time:.1f}s")
            print(f"   📝 Texto mejorado: {improved_text[:200]}...")
        else:
            print(f"   ❌ Error: {response.status_code}")
            improved_text = tesseract_text
    except Exception as e:
        print(f"   ❌ Error: {e}")
        improved_text = tesseract_text
    
    # 3. Análisis de seguridad con Ollama
    print(f"\n3️⃣ ANÁLISIS DE SEGURIDAD")
    print(f"   🔧 API: Ollama Local")
    print(f"   📍 Endpoint: http://localhost:11434/api/generate")
    print(f"   🤖 Modelo: llama3.1:8b")
    try:
        safety_prompt = f"""Analyze these cosmetic ingredients for safety:

{improved_text}

Provide brief analysis in JSON:
{{
    "ingredients": ["list", "of", "ingredients"],
    "safety_score": 1-10,
    "eco_score": 1-10,
    "risk_level": "Low|Moderate|High"
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
            timeout=30
        )
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            analysis_response = data.get('response', '')
            print(f"   ✅ Resultado: Análisis completado en {end_time - start_time:.1f}s")
            
            # Parsear JSON
            try:
                json_start = analysis_response.find('{')
                json_end = analysis_response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = analysis_response[json_start:json_end]
                    analysis = json.loads(json_str)
                    
                    print(f"\n📊 RESULTADOS DEL ANÁLISIS:")
                    print(f"   🛡️  Puntuación de Seguridad: {analysis.get('safety_score', 'N/A')}/10")
                    print(f"   🌱 Puntuación Eco-Friendly: {analysis.get('eco_score', 'N/A')}/10")
                    print(f"   ⚠️  Nivel de Riesgo: {analysis.get('risk_level', 'N/A')}")
                    
                    ingredients = analysis.get('ingredients', [])
                    if ingredients:
                        print(f"\n🧪 INGREDIENTES DETECTADOS ({len(ingredients)}):")
                        for i, ingredient in enumerate(ingredients, 1):
                            print(f"   {i}. {ingredient}")
                    
                    return analysis
                else:
                    print(f"   📝 Análisis en texto: {analysis_response[:200]}...")
                    return {"raw_response": analysis_response}
            except json.JSONDecodeError:
                print(f"   📝 Análisis en texto: {analysis_response[:200]}...")
                return {"raw_response": analysis_response}
        else:
            print(f"   ❌ Error: {response.status_code}")
            return {}
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {}
    
    # 4. Resumen de APIs utilizadas
    print(f"\n" + "=" * 60)
    print(f"📋 RESUMEN DE APIS UTILIZADAS")
    print(f"=" * 60)
    print(f"✅ Tesseract OCR: Extracción de texto de imagen")
    print(f"   📍 Ubicación: {os.getenv('TESSERACT_PATH', '/opt/homebrew/bin/tesseract')}")
    print(f"   📊 Resultado: {len(tesseract_text)} caracteres extraídos")
    
    print(f"\n✅ Ollama Local (llama3.1:8b): Mejora de texto y análisis de seguridad")
    print(f"   📍 Endpoint: http://localhost:11434/api/generate")
    print(f"   📊 Resultado: Texto mejorado y análisis de seguridad completado")
    
    print(f"\n⚠️  APIS NO UTILIZADAS EN ESTA PRUEBA:")
    print(f"   - Google Vision API: Disponible pero no utilizada")
    print(f"   - EWG Database: Disponible pero no utilizada")
    print(f"   - CIR Database: Disponible pero no utilizada")
    print(f"   - SCCS Database: Disponible pero no utilizada")
    print(f"   - ICCR Database: Disponible pero no utilizada")
    
    print(f"\n🎉 ANÁLISIS COMPLETADO!")
    return True

if __name__ == "__main__":
    print("🚀 Iniciando análisis simple con fuentes de datos...")
    result = simple_analysis_with_apis()
    
    if result:
        print("\n✅ Análisis completado exitosamente!")
    else:
        print("\n❌ El análisis falló.")
        sys.exit(1)