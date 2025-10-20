#!/bin/bash

echo "🧪 PROBANDO ENDPOINT /api/test/analyze-image"
echo "============================================="

# Verificar que Ollama esté ejecutándose
echo "1️⃣ Verificando Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama está ejecutándose"
else
    echo "❌ Ollama no está ejecutándose. Iniciando..."
    # Aquí podrías iniciar Ollama si es necesario
fi

echo ""
echo "2️⃣ Probando endpoint con test3.jpg..."

# Probar el endpoint
curl -X POST \
  -F "file=@/Users/arielsanroj/Downloads/test3.jpg" \
  -F "productName=Crema Hidratante" \
  http://localhost:8080/api/test/analyze-image

echo ""
echo "✅ Prueba completada"