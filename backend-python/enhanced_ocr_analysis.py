#!/usr/bin/env python3
"""
Análisis mejorado de imágenes con OCR avanzado y procesamiento de IA
"""

import os
import sys
from dotenv import load_dotenv
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import cv2
import numpy as np
import re
from typing import Dict, List, Any, Optional

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, User
from ollama_integration import ollama_integration, analyze_ingredients_with_ollama

class EnhancedOCRAnalysis:
    def __init__(self):
        # Configurar Tesseract
        tesseract_path = os.getenv('TESSERACT_PATH', '/opt/homebrew/bin/tesseract')
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Configuración de Tesseract para mejor OCR
        self.tesseract_config = '--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,;:()[]{}"\'/\\- '
    
    def preprocess_image(self, image_path: str) -> List[np.ndarray]:
        """Preprocesar imagen para mejorar OCR"""
        try:
            # Cargar imagen
            image = cv2.imread(image_path)
            if image is None:
                return []
            
            # Convertir a escala de grises
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Diferentes versiones preprocesadas
            processed_images = []
            
            # 1. Imagen original en escala de grises
            processed_images.append(gray)
            
            # 2. Mejorar contraste
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            processed_images.append(enhanced)
            
            # 3. Desenfoque gaussiano para reducir ruido
            blurred = cv2.GaussianBlur(gray, (1, 1), 0)
            processed_images.append(blurred)
            
            # 4. Binarización adaptativa
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            processed_images.append(binary)
            
            # 5. Morfología para limpiar
            kernel = np.ones((1,1), np.uint8)
            morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            processed_images.append(morph)
            
            return processed_images
            
        except Exception as e:
            print(f"Error preprocessing image: {e}")
            return []
    
    def extract_text_multiple_methods(self, image_path: str) -> Dict[str, str]:
        """Extraer texto usando múltiples métodos"""
        results = {}
        
        try:
            # Método 1: Tesseract estándar
            image = Image.open(image_path)
            text_standard = pytesseract.image_to_string(image, config=self.tesseract_config)
            results['standard'] = text_standard.strip()
            
            # Método 2: Tesseract con PSM 3 (automático)
            text_auto = pytesseract.image_to_string(image, config='--oem 3 --psm 3')
            results['auto'] = text_auto.strip()
            
            # Método 3: Tesseract con PSM 6 (bloque uniforme)
            text_block = pytesseract.image_to_string(image, config='--oem 3 --psm 6')
            results['block'] = text_block.strip()
            
            # Método 4: Tesseract con PSM 8 (palabra única)
            text_word = pytesseract.image_to_string(image, config='--oem 3 --psm 8')
            results['word'] = text_word.strip()
            
            # Método 5: Procesamiento con OpenCV
            processed_images = self.preprocess_image(image_path)
            for i, processed_img in enumerate(processed_images):
                try:
                    # Convertir de OpenCV a PIL
                    pil_image = Image.fromarray(processed_img)
                    text_processed = pytesseract.image_to_string(pil_image, config=self.tesseract_config)
                    results[f'processed_{i}'] = text_processed.strip()
                except Exception as e:
                    print(f"Error processing image {i}: {e}")
            
            return results
            
        except Exception as e:
            print(f"Error extracting text: {e}")
            return {}
    
    def clean_and_merge_text(self, text_results: Dict[str, str]) -> str:
        """Limpiar y combinar resultados de texto"""
        all_texts = [text for text in text_results.values() if text.strip()]
        
        if not all_texts:
            return ""
        
        # Usar el texto más largo como base
        base_text = max(all_texts, key=len)
        
        # Limpiar texto
        cleaned = self.clean_text(base_text)
        
        # Agregar información de otros métodos si es relevante
        for text in all_texts:
            if text != base_text and len(text) > 10:
                # Buscar palabras que no estén en el texto base
                base_words = set(cleaned.lower().split())
                new_words = set(text.lower().split())
                missing_words = new_words - base_words
                
                if missing_words:
                    # Agregar palabras faltantes
                    missing_text = ' '.join(missing_words)
                    cleaned += f" {missing_text}"
        
        return cleaned
    
    async def enhance_text_with_ollama(self, text: str) -> str:
        """Mejorar texto usando Ollama si está disponible"""
        if not text.strip() or not ollama_integration.is_available():
            return text
        
        try:
            # Usar Ollama para mejorar el texto OCR
            ollama_result = await ollama_integration.analyze_ingredients([text])
            if ollama_result.success and ollama_result.content:
                # Si Ollama devuelve un texto mejorado, usarlo
                if len(ollama_result.content) > len(text) * 0.5:  # Al menos 50% del texto original
                    return ollama_result.content
        except Exception as e:
            print(f"Error mejorando texto con Ollama: {e}")
        
        return text
    
    def clean_text(self, text: str) -> str:
        """Limpiar texto extraído"""
        if not text:
            return ""
        
        # Remover caracteres especiales problemáticos
        text = re.sub(r'[^\w\s.,;:()\[\]{}"\'/\\-]', ' ', text)
        
        # Remover espacios múltiples
        text = re.sub(r'\s+', ' ', text)
        
        # Remover líneas vacías
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Unir líneas
        text = ' '.join(lines)
        
        return text.strip()
    
    def extract_cosmetic_info(self, text: str) -> Dict[str, Any]:
        """Extraer información específica de productos cosméticos"""
        info = {
            'product_name': '',
            'brand': '',
            'product_type': '',
            'ingredients': [],
            'claims': [],
            'warnings': [],
            'net_content': '',
            'extracted_text': text
        }
        
        if not text:
            return info
        
        text_lower = text.lower()
        
        # Buscar marca/producto
        brand_patterns = [
            r'([A-Z][a-z]+)\s+(feeling|natura|loreal|maybelline|revlon|covergirl)',
            r'(natura|feeling|loreal|maybelline|revlon|covergirl)',
            r'([A-Z][A-Z\s]+)\s+(feeling|natura)'
        ]
        
        for pattern in brand_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info['brand'] = match.group(1) if match.groups() else match.group(0)
                break
        
        # Buscar tipo de producto
        product_types = [
            'lotion', 'cream', 'serum', 'moisturizer', 'cleanser', 'toner',
            'sunscreen', 'spf', 'mask', 'scrub', 'gel', 'oil', 'balm',
            'hidratante', 'corporal', 'facial', 'anti-aging', 'anti-edad'
        ]
        
        for product_type in product_types:
            if product_type in text_lower:
                info['product_type'] = product_type
                break
        
        # Buscar ingredientes comunes
        common_ingredients = [
            'water', 'aqua', 'glycerin', 'hyaluronic acid', 'vitamin c', 'niacinamide',
            'ceramides', 'peptides', 'retinol', 'aloe vera', 'shea butter', 'coconut oil',
            'jojoba oil', 'argan oil', 'squalane', 'collagen', 'elastin', 'antioxidants',
            'spf', 'sunscreen', 'titanium dioxide', 'zinc oxide', 'dimethicone',
            'cyclopentasiloxane', 'phenoxyethanol', 'parabens', 'fragrance', 'parfum'
        ]
        
        for ingredient in common_ingredients:
            if ingredient in text_lower:
                info['ingredients'].append(ingredient)
        
        # Buscar afirmaciones
        claim_patterns = [
            r'probado\s+dermatol[oó]gicamente',
            r'testado\s+dermatol[oó]gicamente',
            r'hipoalerg[eé]nico',
            r'sin\s+parabenos',
            r'org[aá]nico',
            r'natural',
            r'anti-edad',
            r'anti-aging',
            r'hidratante',
            r'nutritivo'
        ]
        
        for pattern in claim_patterns:
            matches = re.findall(pattern, text_lower)
            info['claims'].extend(matches)
        
        # Buscar advertencias
        warning_patterns = [
            r'evitar\s+contacto\s+con\s+los\s+ojos',
            r'para\s+uso\s+externo',
            r'no\s+ingerir',
            r'mantener\s+fuera\s+del\s+alcance\s+de\s+los\s+ni[ñn]os',
            r'probar\s+en\s+una\s+peque[ñn]a\s+[áa]rea'
        ]
        
        for pattern in warning_patterns:
            matches = re.findall(pattern, text_lower)
            info['warnings'].extend(matches)
        
        # Buscar contenido neto
        net_content_patterns = [
            r'(\d+)\s*(ml|g|oz|fl\s*oz)',
            r'cont\.\s*neto\s*(\d+)\s*(ml|g|oz)',
            r'net\s*content\s*(\d+)\s*(ml|g|oz)'
        ]
        
        for pattern in net_content_patterns:
            match = re.search(pattern, text_lower)
            if match:
                info['net_content'] = f"{match.group(1)} {match.group(2)}"
                break
        
        return info
    
    def analyze_safety_score(self, ingredients: List[str]) -> Dict[str, Any]:
        """Analizar puntuación de seguridad de ingredientes"""
        safety_data = {
            'overall_score': 5,
            'safe_ingredients': [],
            'moderate_ingredients': [],
            'caution_ingredients': [],
            'recommendations': []
        }
        
        # Base de datos simple de seguridad
        safe_ingredients = [
            'water', 'aqua', 'glycerin', 'hyaluronic acid', 'vitamin c',
            'niacinamide', 'ceramides', 'peptides', 'aloe vera', 'shea butter',
            'coconut oil', 'jojoba oil', 'argan oil', 'squalane'
        ]
        
        moderate_ingredients = [
            'retinol', 'spf', 'sunscreen', 'titanium dioxide', 'zinc oxide',
            'dimethicone', 'cyclopentasiloxane'
        ]
        
        caution_ingredients = [
            'parabens', 'fragrance', 'parfum', 'alcohol', 'sulfates',
            'formaldehyde', 'phthalates'
        ]
        
        for ingredient in ingredients:
            ingredient_lower = ingredient.lower()
            
            if any(safe in ingredient_lower for safe in safe_ingredients):
                safety_data['safe_ingredients'].append(ingredient)
            elif any(mod in ingredient_lower for mod in moderate_ingredients):
                safety_data['moderate_ingredients'].append(ingredient)
            elif any(caution in ingredient_lower for caution in caution_ingredients):
                safety_data['caution_ingredients'].append(ingredient)
        
        # Calcular puntuación
        safe_count = len(safety_data['safe_ingredients'])
        moderate_count = len(safety_data['moderate_ingredients'])
        caution_count = len(safety_data['caution_ingredients'])
        total_count = len(ingredients)
        
        if total_count > 0:
            safety_data['overall_score'] = max(1, min(10, 
                10 - (caution_count * 3 + moderate_count * 1) / total_count * 10))
        
        # Generar recomendaciones
        if caution_count > 0:
            safety_data['recommendations'].append("⚠️ Contiene ingredientes que requieren precaución")
        if moderate_count > 0:
            safety_data['recommendations'].append("🟡 Algunos ingredientes requieren uso moderado")
        if safe_count > total_count * 0.7:
            safety_data['recommendations'].append("✅ Mayoría de ingredientes seguros")
        
        return safety_data

async def analyze_image_enhanced(image_path: str) -> Dict[str, Any]:
    """Análisis mejorado de imagen con OCR avanzado"""
    print("🔍 ANÁLISIS MEJORADO DE IMAGEN")
    print("=" * 50)
    
    analyzer = EnhancedOCRAnalysis()
    
    # 1. Extraer texto con múltiples métodos
    print("1️⃣ Extrayendo texto con múltiples métodos...")
    text_results = analyzer.extract_text_multiple_methods(image_path)
    
    print(f"✅ Métodos utilizados: {len(text_results)}")
    for method, text in text_results.items():
        print(f"   - {method}: {len(text)} caracteres")
    
    # 2. Limpiar y combinar texto
    print("\n2️⃣ Limpiando y combinando texto...")
    final_text = analyzer.clean_and_merge_text(text_results)
    print(f"✅ Texto final: {len(final_text)} caracteres")
    print(f"📝 Contenido: {final_text[:200]}{'...' if len(final_text) > 200 else ''}")
    
    # 2.5. Mejorar texto con Ollama si está disponible
    print("\n2️⃣.5️⃣ Mejorando texto con Ollama...")
    enhanced_text = await analyzer.enhance_text_with_ollama(final_text)
    if enhanced_text != final_text:
        print("✅ Texto mejorado con Ollama")
        final_text = enhanced_text
    else:
        print("ℹ️  Ollama no disponible o no mejoró el texto")
    
    # 3. Extraer información cosmética
    print("\n3️⃣ Extrayendo información cosmética...")
    cosmetic_info = analyzer.extract_cosmetic_info(final_text)
    
    print(f"✅ Información extraída:")
    print(f"   - Marca: {cosmetic_info['brand'] or 'No detectada'}")
    print(f"   - Tipo: {cosmetic_info['product_type'] or 'No detectado'}")
    print(f"   - Ingredientes: {len(cosmetic_info['ingredients'])}")
    print(f"   - Afirmaciones: {len(cosmetic_info['claims'])}")
    print(f"   - Advertencias: {len(cosmetic_info['warnings'])}")
    print(f"   - Contenido neto: {cosmetic_info['net_content'] or 'No detectado'}")
    
    # 4. Análisis de seguridad
    print("\n4️⃣ Analizando seguridad...")
    safety_analysis = analyzer.analyze_safety_score(cosmetic_info['ingredients'])
    
    print(f"✅ Análisis de seguridad:")
    print(f"   - Puntuación: {safety_analysis['overall_score']:.1f}/10")
    print(f"   - Ingredientes seguros: {len(safety_analysis['safe_ingredients'])}")
    print(f"   - Ingredientes moderados: {len(safety_analysis['moderate_ingredients'])}")
    print(f"   - Ingredientes de precaución: {len(safety_analysis['caution_ingredients'])}")
    
    # 5. Análisis adicional con Ollama si está disponible
    ollama_insights = ""
    if ollama_integration.is_available() and cosmetic_info['ingredients']:
        try:
            print("\n5️⃣ Análisis adicional con Ollama...")
            ollama_result = await analyze_ingredients_with_ollama(cosmetic_info['ingredients'])
            if ollama_result.success and ollama_result.content:
                ollama_insights = f"\n\n🤖 Análisis adicional con IA:\n{ollama_result.content}"
                print("✅ Análisis con Ollama completado")
            else:
                print("ℹ️  Ollama no devolvió análisis")
        except Exception as e:
            print(f"⚠️  Error en análisis con Ollama: {e}")
    
    # 6. Resultado final
    result = {
        'extracted_text': final_text,
        'cosmetic_info': cosmetic_info,
        'safety_analysis': safety_analysis,
        'text_methods': text_results,
        'analysis_method': 'enhanced_ocr_with_ollama',
        'ollama_insights': ollama_insights
    }
    
    print("\n" + "=" * 50)
    print("🎉 ANÁLISIS COMPLETADO")
    print("=" * 50)
    
    return result

if __name__ == "__main__":
    import asyncio
    image_path = "/Users/arielsanroj/Downloads/test1.jpg"
    if os.path.exists(image_path):
        result = asyncio.run(analyze_image_enhanced(image_path))
        print(f"\n📊 RESUMEN FINAL:")
        print(f"   - Texto extraído: {len(result['extracted_text'])} caracteres")
        print(f"   - Ingredientes: {len(result['cosmetic_info']['ingredients'])}")
        print(f"   - Puntuación de seguridad: {result['safety_analysis']['overall_score']:.1f}/10")
    else:
        print(f"❌ Imagen no encontrada: {image_path}")