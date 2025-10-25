#!/usr/bin/env python3
"""
Análisis detallado de ingredientes con puntuación eco-friendly y evaluación de riesgo
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

from database import SessionLocal, User

def analyze_ingredients_detailed():
    """Análisis detallado de ingredientes con puntuaciones"""
    
    print("🧪 ANÁLISIS DETALLADO DE INGREDIENTES")
    print("=" * 60)
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Ruta de la imagen de prueba
    image_path = "/Users/arielsanroj/Downloads/test3.jpg"
    
    print(f"📸 Imagen: {os.path.basename(image_path)}")
    print(f"📏 Tamaño: {os.path.getsize(image_path)} bytes")
    
    # 1. Verificar imagen
    print("\n1️⃣ VERIFICANDO IMAGEN...")
    try:
        with Image.open(image_path) as img:
            print(f"✅ Imagen válida: {img.size[0]}x{img.size[1]} pixels")
            print(f"✅ Formato: {img.format}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # 2. OCR con Tesseract
    print("\n2️⃣ EXTRACCIÓN DE TEXTO...")
    try:
        tesseract_path = os.getenv('TESSERACT_PATH', '/opt/homebrew/bin/tesseract')
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        tesseract_text = pytesseract.image_to_string(Image.open(image_path))
        
        if tesseract_text and tesseract_text.strip():
            print(f"✅ Texto extraído: {len(tesseract_text)} caracteres")
            print(f"📝 Contenido OCR:")
            print(f"   {tesseract_text}")
        else:
            print("⚠️  No se pudo extraer texto")
            return False
    except Exception as e:
        print(f"❌ Error en OCR: {e}")
        return False
    
    # 3. Mejorar texto con Ollama
    print("\n3️⃣ MEJORANDO TEXTO CON OLLAMA...")
    try:
        prompt = f"""Improve and correct this OCR text from a cosmetic ingredients list. 
Format it properly and identify each ingredient clearly.

Original OCR text:
{tesseract_text}

Please provide the corrected and formatted ingredients list:"""
        
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
            print(f"✅ Texto mejorado en {end_time - start_time:.1f} segundos")
            print(f"📝 Texto mejorado:")
            print(f"   {improved_text}")
        else:
            print(f"❌ Error mejorando texto: {response.status_code}")
            improved_text = tesseract_text
    except Exception as e:
        print(f"❌ Error mejorando texto: {e}")
        improved_text = tesseract_text
    
    # 4. Análisis detallado de ingredientes con puntuaciones
    print("\n4️⃣ ANÁLISIS DETALLADO DE INGREDIENTES...")
    try:
        detailed_prompt = f"""Analyze these cosmetic ingredients and provide a comprehensive safety and eco-friendly assessment in JSON format:

Ingredients: {improved_text}

For each ingredient, provide:
- Safety score (1-10, where 10 is safest)
- Risk level (Very Low, Low, Moderate, High, Very High)
- Eco-friendly score (1-10, where 10 is most eco-friendly)
- Environmental impact (Low, Moderate, High)
- Skin sensitivity risk (Low, Moderate, High)
- Common uses in cosmetics
- Potential concerns or benefits

Please provide analysis in this JSON format:
{{
    "overall_safety_score": 1-10,
    "overall_eco_score": 1-10,
    "overall_risk_level": "Very Low|Low|Moderate|High|Very High",
    "ingredients_analysis": [
        {{
            "ingredient": "ingredient name",
            "safety_score": 1-10,
            "risk_level": "Very Low|Low|Moderate|High|Very High",
            "eco_friendly_score": 1-10,
            "environmental_impact": "Low|Moderate|High",
            "skin_sensitivity": "Low|Moderate|High",
            "common_uses": "description",
            "concerns": ["concern1", "concern2"],
            "benefits": ["benefit1", "benefit2"],
            "recommendation": "safe|moderate|caution|avoid"
        }}
    ],
    "eco_friendly_summary": "overall environmental assessment",
    "safety_summary": "overall safety assessment",
    "recommendations": ["recommendation1", "recommendation2"],
    "warnings": ["warning1", "warning2"]
}}"""
        
        payload = {
            "model": "llama3.1:8b",
            "prompt": detailed_prompt,
            "stream": False
        }
        
        start_time = time.time()
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=120
        )
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            analysis_response = data.get('response', '')
            print(f"✅ Análisis detallado completado en {end_time - start_time:.1f} segundos")
            
            # Intentar parsear JSON
            try:
                json_start = analysis_response.find('{')
                json_end = analysis_response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = analysis_response[json_start:json_end]
                    detailed_analysis = json.loads(json_str)
                    
                    # Mostrar resultados detallados
                    print(f"\n📊 RESULTADOS DETALLADOS:")
                    print(f"   🛡️  Puntuación de Seguridad General: {detailed_analysis.get('overall_safety_score', 'N/A')}/10")
                    print(f"   🌱 Puntuación Eco-Friendly: {detailed_analysis.get('overall_eco_score', 'N/A')}/10")
                    print(f"   ⚠️  Nivel de Riesgo General: {detailed_analysis.get('overall_risk_level', 'N/A')}")
                    
                    # Análisis por ingrediente
                    ingredients_analysis = detailed_analysis.get('ingredients_analysis', [])
                    if ingredients_analysis:
                        print(f"\n🧪 ANÁLISIS POR INGREDIENTE:")
                        for i, ingredient in enumerate(ingredients_analysis, 1):
                            print(f"\n   {i}. {ingredient.get('ingredient', 'N/A')}")
                            print(f"      🛡️  Seguridad: {ingredient.get('safety_score', 'N/A')}/10")
                            print(f"      ⚠️  Riesgo: {ingredient.get('risk_level', 'N/A')}")
                            print(f"      🌱 Eco-Friendly: {ingredient.get('eco_friendly_score', 'N/A')}/10")
                            print(f"      🌍 Impacto Ambiental: {ingredient.get('environmental_impact', 'N/A')}")
                            print(f"      🧴 Sensibilidad: {ingredient.get('skin_sensitivity', 'N/A')}")
                            print(f"      💡 Usos: {ingredient.get('common_uses', 'N/A')}")
                            print(f"      ⚠️  Preocupaciones: {', '.join(ingredient.get('concerns', []))}")
                            print(f"      ✅ Beneficios: {', '.join(ingredient.get('benefits', []))}")
                            print(f"      📋 Recomendación: {ingredient.get('recommendation', 'N/A')}")
                    
                    # Resúmenes
                    print(f"\n🌱 RESUMEN ECO-FRIENDLY:")
                    print(f"   {detailed_analysis.get('eco_friendly_summary', 'N/A')}")
                    
                    print(f"\n🛡️  RESUMEN DE SEGURIDAD:")
                    print(f"   {detailed_analysis.get('safety_summary', 'N/A')}")
                    
                    # Recomendaciones
                    recommendations = detailed_analysis.get('recommendations', [])
                    if recommendations:
                        print(f"\n💡 RECOMENDACIONES:")
                        for i, rec in enumerate(recommendations, 1):
                            print(f"   {i}. {rec}")
                    
                    # Advertencias
                    warnings = detailed_analysis.get('warnings', [])
                    if warnings:
                        print(f"\n⚠️  ADVERTENCIAS:")
                        for i, warning in enumerate(warnings, 1):
                            print(f"   {i}. {warning}")
                    
                    return detailed_analysis
                else:
                    print(f"📝 Análisis en texto:")
                    print(f"   {analysis_response[:500]}...")
                    return {"raw_response": analysis_response}
            except json.JSONDecodeError:
                print(f"📝 Análisis en texto:")
                print(f"   {analysis_response[:500]}...")
                return {"raw_response": analysis_response}
        else:
            print(f"❌ Error en análisis detallado: {response.status_code}")
            return {}
    except Exception as e:
        print(f"❌ Error en análisis detallado: {e}")
        return {}
    
    print("\n🎉 ANÁLISIS DETALLADO COMPLETADO!")
    return True

if __name__ == "__main__":
    print("🚀 Iniciando análisis detallado de ingredientes...")
    result = analyze_ingredients_detailed()
    
    if result:
        print("\n✅ Análisis detallado completado exitosamente!")
    else:
        print("\n❌ El análisis falló.")
        sys.exit(1)