#!/bin/bash

# Script para probar el flujo completo del usuario con datos reales
# 1. Completar cuestionario (simulado)
# 2. Subir imagen y analizar con datos reales del usuario

echo "🧪 PRUEBA DEL FLUJO COMPLETO DEL USUARIO - test2.jpg"
echo "=================================================="
echo "Simulando el flujo real: Cuestionario → Análisis de Imagen"
echo ""

# Verificar que test2.jpg existe
if [ ! -f "test2.jpg" ]; then
    echo "❌ test2.jpg no encontrado. Copiando desde Downloads..."
    cp /Users/arielsanroj/Downloads/test2.jpg ./test2.jpg
fi

echo "1️⃣ SIMULANDO CUESTIONARIO COMPLETADO"
echo "===================================="
echo "Datos del usuario que se almacenarían en la sesión:"
echo "• Edad: 26-35"
echo "• Tipo de piel: Mixta"
echo "• Preocupaciones: Acné, Piel grasa, Poros dilatados"
echo "• Alergias: No, no tengo alergias conocidas"
echo "• Ingredientes a evitar: Parabenos, Sulfatos, Ftalatos"
echo "• Preferencias: Cuidado facial"
echo "• Presupuesto: Medio ($20-$50)"
echo "• Frecuencia: Mensualmente"
echo "• Información: Análisis detallado"
echo ""

echo "2️⃣ ANÁLISIS DE IMAGEN CON PERFIL REAL DEL USUARIO"
echo "================================================="

# Crear el perfil de usuario real basado en el cuestionario
USER_PROFILE='{
  "age": "26-35",
  "skin_type": "Mixta",
  "skin_concerns": ["Acné", "Piel grasa", "Poros dilatados"],
  "allergies": "No, no tengo alergias conocidas",
  "avoid_ingredients": ["Parabenos", "Sulfatos", "Ftalatos"],
  "product_preferences": "Cuidado facial",
  "budget": "Medio ($20-$50)",
  "purchase_frequency": "Mensualmente",
  "information_preference": "Análisis detallado"
}'

echo "Perfil de usuario real:"
echo "$USER_PROFILE" | jq .
echo ""

echo "3️⃣ EXTRACCIÓN DE INGREDIENTES CON OLLAMA VISION"
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

echo "4️⃣ ANÁLISIS PERSONALIZADO CON PERFIL DEL USUARIO"
echo "==============================================="
PERSONALIZED_ANALYSIS=$(curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1",
    "prompt": "Analiza estos ingredientes cosméticos considerando el perfil específico del usuario:\n\nIngredientes: '$(echo "$INGREDIENTS" | grep -E "^\d+\.|^[A-Z]" | head -10 | tr '\n' ',' | sed 's/,$//' | sed 's/,/, /g')'\n\nPerfil del usuario:\n- Tipo de piel: Mixta\n- Preocupaciones: Acné, Piel grasa, Poros dilatados\n- Alergias: No conocidas\n- Ingredientes a evitar: Parabenos, Sulfatos, Ftalatos\n- Presupuesto: Medio ($20-$50)\n\nPara cada ingrediente, proporciona:\n1. Puntaje EWG (1-10, donde 1 es más seguro)\n2. Nivel de riesgo (bajo, medio, alto)\n3. Puntaje eco-friendly (0-100)\n4. Compatibilidad con piel mixta y acné\n5. Si contiene ingredientes a evitar\n6. Ingredientes sustitutos recomendados\n7. Análisis de seguridad personalizado\n\nResponde en formato JSON estructurado.",
    "stream": false
  }' | jq -r '.response')

echo "Análisis personalizado:"
echo "$PERSONALIZED_ANALYSIS"
echo ""

echo "5️⃣ RECOMENDACIONES PERSONALIZADAS DE PRODUCTOS"
echo "============================================="
PERSONALIZED_RECOMMENDATIONS=$(curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1",
    "prompt": "Basándote en el análisis anterior y el perfil del usuario, recomienda 3 productos cosméticos alternativos específicamente para:\n\n- Piel mixta con tendencia al acné\n- Presupuesto medio ($20-$50)\n- Sin parabenos, sulfatos o ftalatos\n- Disponibles mensualmente\n\nPara cada producto incluye:\n1. Nombre del producto\n2. Marca\n3. Ingredientes principales\n4. Puntaje de seguridad (0-100)\n5. Puntaje eco-friendly (0-100)\n6. Precio estimado\n7. Dónde comprarlo\n8. Por qué es mejor para piel mixta con acné\n9. Compatibilidad con ingredientes a evitar\n\nResponde en formato JSON estructurado.",
    "stream": false
  }' | jq -r '.response')

echo "Recomendaciones personalizadas:"
echo "$PERSONALIZED_RECOMMENDATIONS"
echo ""

echo "6️⃣ RESUMEN EJECUTIVO PERSONALIZADO"
echo "================================="
EXECUTIVE_SUMMARY=$(curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1",
    "prompt": "Crea un resumen ejecutivo personalizado para este producto cosmético considerando el perfil específico del usuario:\n\nPerfil: Piel mixta, acné, evita parabenos/sulfatos/ftalatos, presupuesto medio\n\nIncluye:\n1. Calificación general (A, B, C, D, F)\n2. Puntaje de seguridad general (0-100)\n3. Puntaje eco-friendly general (0-100)\n4. Compatibilidad con piel mixta y acné\n5. Contenido de ingredientes a evitar\n6. Recomendación final personalizada\n7. Alertas específicas para su tipo de piel\n8. Próximos pasos recomendados\n\nFormato el resultado como un reporte profesional personalizado.",
    "stream": false
  }' | jq -r '.response')

echo "Resumen Ejecutivo Personalizado:"
echo "$EXECUTIVE_SUMMARY"
echo ""

echo "✅ FLUJO COMPLETO FINALIZADO"
echo "==========================="
echo "El análisis completo ha sido ejecutado con el perfil real del usuario."
echo "Este es el mismo proceso que ejecutaría el backend de MommyShops con datos reales."
echo ""
echo "🔧 COMPONENTES UTILIZADOS:"
echo "• Perfil de usuario real del cuestionario"
echo "• Ollama Vision (llava) - Extracción de ingredientes"
echo "• Ollama Text (llama3.1) - Análisis personalizado"
echo "• Ollama Text (llama3.1) - Recomendaciones específicas"
echo "• Ollama Text (llama3.1) - Resumen ejecutivo personalizado"
echo ""
echo "📊 RESULTADOS GENERADOS:"
echo "• Lista de ingredientes extraídos"
echo "• Análisis de seguridad personalizado"
echo "• Puntajes EWG y eco-friendly"
echo "• Compatibilidad con tipo de piel específico"
echo "• Detección de ingredientes a evitar"
echo "• Recomendaciones de sustitutos personalizadas"
echo "• Productos alternativos específicos"
echo "• Resumen ejecutivo personalizado"
echo ""
echo "🎯 PERSONALIZACIÓN:"
echo "• Tipo de piel: Mixta"
echo "• Preocupaciones: Acné, Piel grasa, Poros dilatados"
echo "• Ingredientes evitados: Parabenos, Sulfatos, Ftalatos"
echo "• Presupuesto: Medio ($20-$50)"
echo "• Frecuencia: Mensualmente"