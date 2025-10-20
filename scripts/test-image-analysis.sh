#!/bin/bash

# Test script for Ollama image analysis integration
# This script tests the complete flow: Ollama -> Vision Model -> Image Analysis

set -e

echo "🧪 Testing Ollama Image Analysis Integration"
echo "============================================="
echo ""

# Check if Ollama is running
echo "1. Checking Ollama service..."
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama is running"
else
    echo "❌ Ollama is not running. Please start it with: ollama serve"
    exit 1
fi

# Check if required models are installed
echo ""
echo "2. Checking required models..."
if ollama list | grep -q "llama3.1"; then
    echo "✅ llama3.1 model is installed"
else
    echo "❌ llama3.1 model not found. Installing..."
    ollama pull llama3.1
fi

if ollama list | grep -q "llava"; then
    echo "✅ llava vision model is installed"
else
    echo "❌ llava vision model not found. Installing..."
    ollama pull llava
fi

# Test basic text generation
echo ""
echo "3. Testing text generation..."
TEXT_RESPONSE=$(curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1",
    "prompt": "List 3 common cosmetic ingredients",
    "stream": false
  }' | jq -r '.response')

if [ "$TEXT_RESPONSE" != "null" ] && [ -n "$TEXT_RESPONSE" ]; then
    echo "✅ Text generation working"
    echo "   Sample response: ${TEXT_RESPONSE:0:100}..."
else
    echo "❌ Text generation failed"
    exit 1
fi

# Test vision model (if we have a test image)
echo ""
echo "4. Testing vision model..."
if [ -f "test-image.jpg" ]; then
    echo "✅ Test image found, testing vision analysis..."
    
    # Convert image to base64
    BASE64_IMAGE=$(base64 -i test-image.jpg)
    
    VISION_RESPONSE=$(curl -s -X POST http://localhost:11434/api/generate \
      -H "Content-Type: application/json" \
      -d "{
        \"model\": \"llava\",
        \"prompt\": \"Analyze this cosmetic product image and list any ingredients you can see\",
        \"images\": [\"$BASE64_IMAGE\"],
        \"stream\": false
      }" | jq -r '.response')
    
    if [ "$VISION_RESPONSE" != "null" ] && [ -n "$VISION_RESPONSE" ]; then
        echo "✅ Vision analysis working"
        echo "   Sample response: ${VISION_RESPONSE:0:150}..."
    else
        echo "❌ Vision analysis failed"
        exit 1
    fi
else
    echo "⚠️  No test image found (test-image.jpg), skipping vision test"
    echo "   To test vision: place an image named 'test-image.jpg' in this directory"
fi

# Test application health endpoints
echo ""
echo "5. Testing application health endpoints..."
if curl -s http://localhost:8080/actuator/health > /dev/null; then
    echo "✅ Application is running"
    
    # Test Ollama health endpoint
    OLLAMA_HEALTH=$(curl -s http://localhost:8080/api/ollama/health | jq -r '.status')
    if [ "$OLLAMA_HEALTH" = "UP" ]; then
        echo "✅ Ollama health check passed"
    else
        echo "⚠️  Ollama health check failed (this is expected if app isn't fully configured)"
    fi
else
    echo "⚠️  Application not running. Start it with: ./mvnw spring-boot:run"
fi

echo ""
echo "🎉 Ollama Image Analysis Integration Test Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Start your application: ./mvnw spring-boot:run"
echo "2. Open http://localhost:8080/analysis"
echo "3. Upload an image of a cosmetic product"
echo "4. Click 'Analizar imagen' to test the complete flow"
echo ""
echo "🔧 Configuration:"
echo "   - Ollama Base URL: http://localhost:11434"
echo "   - Text Model: llama3.1"
echo "   - Vision Model: llava"
echo "   - Application: http://localhost:8080"