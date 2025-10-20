#!/bin/bash

# Script para demostrar el análisis completo de test2.jpg usando Ollama
# Este script simula el pipeline completo que debería ejecutar el backend

echo "🧪 ANÁLISIS COMPLETO DE IMAGEN - test2.jpg"
echo "=========================================="
echo "Simulando el pipeline completo del backend MommyShops"
echo ""

# Verificar que test2.jpg existe
if [ ! -f "test2.jpg" ]; then
    echo "❌ test2.jpg no encontrado. Copiando desde Downloads..."
    cp /Users/arielsanroj/Downloads/test2.jpg ./test2.jpg
fi

echo "1️⃣ EXTRACCIÓN DE INGREDIENTES CON OLLAMA VISION"
echo "=============================================="
INGREDIENTS=$(curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llava",
    "prompt": "Read the text in this image carefully. This is a cosmetic product ingredient list. Extract and list all the ingredients you can see, one per line. Focus on the ingredient names only.",
    "images": ["'$(base64 -i test2.jpg)'"],
    "stream": false
  }' | jq -r '.response')

echo "Ingredientes extraídos:"
echo "$INGREDIENTS"
echo ""

echo "2️⃣ ANÁLISIS DE SEGURIDAD CON IA"
echo "==============================="
SAFETY_ANALYSIS=$(curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1",
    "prompt": "Analiza estos ingredientes cosméticos y proporciona un análisis completo de seguridad:\n\n'$(echo "$INGREDIENTS" | grep -E "^\d+\.|^[A-Z]" | head -10 | tr '\n' ',' | sed 's/,$//' | sed 's/,/, /g')'\n\nPara cada ingrediente, proporciona:\n1. Puntaje EWG (1-10, donde 1 es más seguro)\n2. Nivel de riesgo (bajo, medio, alto)\n3. Puntaje eco-friendly (0-100)\n4. Ingredientes sustitutos recomendados\n5. Análisis de seguridad general\n\nResponde en formato JSON estructurado.",
    "stream": false
  }' | jq -r '.response')

echo "Análisis de seguridad:"
echo "$SAFETY_ANALYSIS"
echo ""

echo "3️⃣ GENERACIÓN DE RECOMENDACIONES DE PRODUCTOS"
echo "============================================="
PRODUCT_RECOMMENDATIONS=$(curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1",
    "prompt": "Basándote en el análisis de ingredientes anterior, recomienda 3 productos cosméticos alternativos más seguros y eco-friendly que contengan ingredientes naturales. Para cada producto incluye:\n\n1. Nombre del producto\n2. Marca\n3. Ingredientes principales\n4. Puntaje de seguridad (0-100)\n5. Puntaje eco-friendly (0-100)\n6. Precio estimado\n7. Dónde comprarlo\n8. Por qué es mejor que el producto original\n\nResponde en formato JSON estructurado.",
    "stream": false
  }' | jq -r '.response')

echo "Recomendaciones de productos:"
echo "$PRODUCT_RECOMMENDATIONS"
echo ""

echo "4️⃣ GENERACIÓN DE RESUMEN EJECUTIVO"
echo "=================================="
EXECUTIVE_SUMMARY=$(curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1",
    "prompt": "Crea un resumen ejecutivo profesional para el análisis de este producto cosmético. Incluye:\n\n1. Calificación general (A, B, C, D, F)\n2. Puntaje de seguridad general (0-100)\n3. Puntaje eco-friendly general (0-100)\n4. Principales preocupaciones de seguridad\n5. Recomendación final (Recomendado, Seguro, Precaución, Evitar)\n6. Alertas específicas para grupos de riesgo\n7. Próximos pasos recomendados\n\nFormato el resultado como un reporte profesional.",
    "stream": false
  }' | jq -r '.response')

echo "Resumen Ejecutivo:"
echo "$EXECUTIVE_SUMMARY"
echo ""

echo "5️⃣ GENERACIÓN DE REPORTE FINAL"
echo "=============================="
FINAL_REPORT=$(curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1",
    "prompt": "Crea un reporte final completo y profesional para el análisis del producto cosmético. El reporte debe incluir:\n\n1. Portada con título y fecha\n2. Resumen ejecutivo\n3. Lista de ingredientes analizados\n4. Análisis detallado de cada ingrediente\n5. Recomendaciones de ingredientes sustitutos\n6. Productos alternativos recomendados\n7. Conclusiones y recomendaciones finales\n8. Información sobre fuentes de datos\n\nFormatea el resultado como un reporte profesional con secciones claras y fáciles de leer.",
    "stream": false
  }' | jq -r '.response')

echo "REPORTE FINAL COMPLETO:"
echo "======================"
echo "$FINAL_REPORT"
echo ""

echo "✅ ANÁLISIS COMPLETO FINALIZADO"
echo "==============================="
echo "El pipeline completo de análisis ha sido ejecutado exitosamente."
echo "Este es el mismo proceso que ejecutaría el backend de MommyShops."
echo ""
echo "🔧 COMPONENTES UTILIZADOS:"
echo "• Ollama Vision (llava) - Extracción de ingredientes"
echo "• Ollama Text (llama3.1) - Análisis de seguridad"
echo "• Ollama Text (llama3.1) - Recomendaciones de productos"
echo "• Ollama Text (llama3.1) - Resumen ejecutivo"
echo "• Ollama Text (llama3.1) - Reporte final"
echo ""
echo "📊 RESULTADOS GENERADOS:"
echo "• Lista de ingredientes extraídos"
echo "• Análisis de seguridad detallado"
echo "• Puntajes EWG y eco-friendly"
echo "• Recomendaciones de sustitutos"
echo "• Productos alternativos"
echo "• Resumen ejecutivo"
echo "• Reporte final completo"