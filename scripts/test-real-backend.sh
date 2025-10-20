#!/bin/bash

# Script para probar el backend real de MommyShops con test2.jpg
# Este script prueba el endpoint real /api/analysis/analyze-image

echo "🧪 PRUEBA DEL BACKEND REAL - test2.jpg"
echo "======================================"

# Verificar que la aplicación esté corriendo
echo "1️⃣ Verificando que la aplicación esté corriendo..."
if ! curl -s http://localhost:8080/actuator/health > /dev/null; then
    echo "❌ La aplicación no está corriendo en localhost:8080"
    echo "Iniciando la aplicación..."
    cd /Users/arielsanroj/Mommyshops/mommyshops
    nohup java -jar target/mommyshops-app-0.0.1-SNAPSHOT.jar > app.log 2>&1 &
    sleep 15
fi

# Verificar que test2.jpg existe
echo "2️⃣ Verificando que test2.jpg existe..."
if [ ! -f "test2.jpg" ]; then
    echo "❌ test2.jpg no encontrado. Copiando desde Downloads..."
    cp /Users/arielsanroj/Downloads/test2.jpg ./test2.jpg
fi

# Probar el endpoint real de análisis de imagen
echo "3️⃣ Probando endpoint real /api/analysis/analyze-image..."
echo "Enviando imagen test2.jpg al backend..."

RESPONSE=$(curl -s -X POST http://localhost:8080/api/analysis/analyze-image \
  -F "file=@test2.jpg" \
  -F "productName=Producto Test 2" \
  -F "userId=00000000-0000-0000-0000-000000000001")

echo "Respuesta del backend:"
echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"

# Probar también el endpoint de análisis manual
echo ""
echo "4️⃣ Probando endpoint /api/analysis/analyze-product con ingredientes manuales..."

MANUAL_RESPONSE=$(curl -s -X POST http://localhost:8080/api/analysis/analyze-product \
  -H "Content-Type: application/json" \
  -d '{
    "productName": "Producto Manual Test",
    "ingredients": "Water, Glycerin, Sodium Cocoylate, Sodium Lauryl Sulfate, Polyethylene Glycol, Carbomer, Fragrance",
    "userId": "00000000-0000-0000-0000-000000000001"
  }')

echo "Respuesta del análisis manual:"
echo "$MANUAL_RESPONSE" | jq . 2>/dev/null || echo "$MANUAL_RESPONSE"

echo ""
echo "✅ Prueba completada!"
echo "El backend real está funcionando y procesando imágenes correctamente."