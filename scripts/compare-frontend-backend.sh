#!/bin/bash

# Script para comparar resultados del frontend vs backend
echo "🔍 COMPARACIÓN FRONTEND vs BACKEND"
echo "=================================="
echo ""

# Verificar que test2.jpg existe
if [ ! -f "test2.jpg" ]; then
    echo "❌ test2.jpg no encontrado. Copiando desde Downloads..."
    cp /Users/arielsanroj/Downloads/test2.jpg ./test2.jpg
fi

echo "1️⃣ PRUEBA DIRECTA DEL BACKEND"
echo "============================="
echo "Llamando directamente al endpoint /api/analysis/analyze-image"
echo ""

BACKEND_RESPONSE=$(curl -s -X POST http://localhost:8080/api/analysis/analyze-image \
  -F "file=@test2.jpg" \
  -F "productName=Producto Test 2" \
  -F "userId=00000000-0000-0000-0000-000000000001")

echo "Respuesta del Backend:"
echo "$BACKEND_RESPONSE" | jq . 2>/dev/null || echo "$BACKEND_RESPONSE"
echo ""

echo "2️⃣ ANÁLISIS DE DIFERENCIAS"
echo "=========================="
echo ""

# Extraer campos específicos del backend
BACKEND_PRODUCT_NAME=$(echo "$BACKEND_RESPONSE" | jq -r '.productName // "N/A"' 2>/dev/null)
BACKEND_EWG_SCORE=$(echo "$BACKEND_RESPONSE" | jq -r '.ewgScore // "N/A"' 2>/dev/null)
BACKEND_SAFETY_PERCENTAGE=$(echo "$BACKEND_RESPONSE" | jq -r '.safetyPercentage // "N/A"' 2>/dev/null)
BACKEND_INGREDIENTS=$(echo "$BACKEND_RESPONSE" | jq -r '.ingredients // "N/A"' 2>/dev/null)
BACKEND_RECOMMENDATIONS=$(echo "$BACKEND_RESPONSE" | jq -r '.recommendations // "N/A"' 2>/dev/null)

echo "📊 CAMPOS DEL BACKEND:"
echo "• Product Name: $BACKEND_PRODUCT_NAME"
echo "• EWG Score: $BACKEND_EWG_SCORE"
echo "• Safety Percentage: $BACKEND_SAFETY_PERCENTAGE"
echo "• Ingredients: $BACKEND_INGREDIENTS"
echo "• Recommendations: $BACKEND_RECOMMENDATIONS"
echo ""

echo "3️⃣ SIMULACIÓN DEL FRONTEND"
echo "=========================="
echo "Simulando lo que haría el frontend con los datos del cuestionario"
echo ""

# Simular el perfil de usuario del cuestionario
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

echo "Perfil de usuario del cuestionario:"
echo "$USER_PROFILE" | jq .
echo ""

echo "4️⃣ ANÁLISIS CON OLLAMA USANDO PERFIL REAL"
echo "========================================="
echo "Ejecutando análisis con Ollama usando el perfil real del usuario"
echo ""

# Extraer ingredientes con Ollama
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

# Análisis personalizado con el perfil del usuario
PERSONALIZED_ANALYSIS=$(curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1",
    "prompt": "Analiza estos ingredientes cosméticos considerando el perfil específico del usuario:\n\nIngredientes: '$(echo "$INGREDIENTS" | grep -E "^\d+\.|^[A-Z]" | head -10 | tr '\n' ',' | sed 's/,$//' | sed 's/,/, /g')'\n\nPerfil del usuario:\n- Tipo de piel: Mixta\n- Preocupaciones: Acné, Piel grasa, Poros dilatados\n- Alergias: No conocidas\n- Ingredientes a evitar: Parabenos, Sulfatos, Ftalatos\n- Presupuesto: Medio ($20-$50)\n\nPara cada ingrediente, proporciona:\n1. Puntaje EWG (1-10, donde 1 es más seguro)\n2. Nivel de riesgo (bajo, medio, alto)\n3. Puntaje eco-friendly (0-100)\n4. Compatibilidad con piel mixta y acné\n5. Si contiene ingredientes a evitar\n6. Ingredientes sustitutos recomendados\n7. Análisis de seguridad personalizado\n\nResponde en formato JSON estructurado.",
    "stream": false
  }' | jq -r '.response')

echo "Análisis personalizado con perfil real:"
echo "$PERSONALIZED_ANALYSIS"
echo ""

echo "5️⃣ COMPARACIÓN DE RESULTADOS"
echo "============================"
echo ""

echo "🔍 DIFERENCIAS IDENTIFICADAS:"
echo ""

if [ "$BACKEND_PRODUCT_NAME" != "N/A" ]; then
    echo "✅ Backend devuelve: $BACKEND_PRODUCT_NAME"
else
    echo "❌ Backend no devuelve productName"
fi

if [ "$BACKEND_EWG_SCORE" != "N/A" ]; then
    echo "✅ Backend devuelve EWG Score: $BACKEND_EWG_SCORE"
else
    echo "❌ Backend no devuelve ewgScore"
fi

if [ "$BACKEND_SAFETY_PERCENTAGE" != "N/A" ]; then
    echo "✅ Backend devuelve Safety Percentage: $BACKEND_SAFETY_PERCENTAGE"
else
    echo "❌ Backend no devuelve safetyPercentage"
fi

echo ""
echo "🎯 CAUSAS POSIBLES DE DIFERENCIAS:"
echo "1. Backend usa UserProfile de la base de datos"
echo "2. Frontend usa datos del cuestionario en memoria"
echo "3. Diferentes fuentes de datos para el análisis"
echo "4. Backend puede estar usando APIs externas reales"
echo "5. Frontend puede estar usando datos simulados como fallback"
echo ""

echo "🔧 SOLUCIONES RECOMENDADAS:"
echo "1. Verificar que el UserProfile en la BD coincida con el cuestionario"
echo "2. Asegurar que el frontend use el mismo userId que el backend"
echo "3. Verificar que el backend esté usando los datos del UserProfile correctamente"
echo "4. Revisar si hay fallbacks activos en el frontend"
echo ""

echo "✅ COMPARACIÓN COMPLETADA"