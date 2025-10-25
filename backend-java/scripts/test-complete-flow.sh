#!/bin/bash

# Complete Test Script for MommyShops Image Analysis
# This script tests the entire flow from image upload to analysis results

set -e

echo "🧪 Testing Complete MommyShops Image Analysis Flow"
echo "=================================================="
echo ""

# Check if test image exists
TEST_IMAGE="test3.jpg"
if [ ! -f "$TEST_IMAGE" ]; then
    echo "❌ Test image '$TEST_IMAGE' not found in current directory"
    echo "Please place your test image in the current directory and name it 'test3.jpg'"
    exit 1
fi

echo "📁 Test image found: $TEST_IMAGE"
echo "📏 Image size: $(du -h "$TEST_IMAGE" | cut -f1)"
echo ""

# Check if all services are running
echo "🔍 Checking service dependencies..."

# Check PostgreSQL
if psql -h localhost -U mommyshops -d mommyshops -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ PostgreSQL is running"
else
    echo "❌ PostgreSQL is not running"
    echo "Run: ./scripts/setup-database.sh"
    exit 1
fi

# Check Ollama
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama is running"
else
    echo "❌ Ollama is not running"
    echo "Run: ./scripts/setup-ollama-complete.sh"
    exit 1
fi

# Check if required models are available
if ollama list | grep -q "llama3.1"; then
    echo "✅ llama3.1 model is available"
else
    echo "❌ llama3.1 model not found"
    echo "Run: ollama pull llama3.1"
    exit 1
fi

if ollama list | grep -q "llava"; then
    echo "✅ llava vision model is available"
else
    echo "❌ llava vision model not found"
    echo "Run: ollama pull llava"
    exit 1
fi

# Check Spring Boot application
if curl -s http://localhost:8080/actuator/health > /dev/null; then
    echo "✅ Spring Boot application is running"
else
    echo "❌ Spring Boot application is not running"
    echo "Run: ./scripts/start-application.sh"
    exit 1
fi

echo ""
echo "🎯 All services are running! Starting comprehensive test..."
echo ""

# Test 1: Ollama Health Check
echo "1️⃣ Testing Ollama Health Check"
echo "-------------------------------"
OLLAMA_HEALTH=$(curl -s http://localhost:8080/api/ollama/health | jq -r '.status' 2>/dev/null || echo "unknown")
if [ "$OLLAMA_HEALTH" = "UP" ]; then
    echo "✅ Ollama health check passed"
else
    echo "⚠️  Ollama health check: $OLLAMA_HEALTH"
fi
echo ""

# Test 2: Direct Ollama Vision Test
echo "2️⃣ Testing Direct Ollama Vision Analysis"
echo "----------------------------------------"
echo "Analyzing test image with Ollama vision model..."

# Convert image to base64
BASE64_IMAGE=$(base64 -i "$TEST_IMAGE")

# Test vision analysis
VISION_RESPONSE=$(curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"llava\",
    \"prompt\": \"Analyze this cosmetic product image and extract the ingredient list. Look for INCI names of cosmetic ingredients. Return ONLY the ingredient list in format: INGREDIENT1, INGREDIENT2, INGREDIENT3, etc.\",
    \"images\": [\"$BASE64_IMAGE\"],
    \"stream\": false
  }" | jq -r '.response' 2>/dev/null || echo "Error: jq not installed")

if [ "$VISION_RESPONSE" != "null" ] && [ -n "$VISION_RESPONSE" ]; then
    echo "✅ Vision analysis successful"
    echo "📋 Extracted ingredients: ${VISION_RESPONSE:0:200}..."
else
    echo "❌ Vision analysis failed"
    echo "Response: $VISION_RESPONSE"
fi
echo ""

# Test 3: Application Health Check
echo "3️⃣ Testing Application Health Check"
echo "-----------------------------------"
APP_HEALTH=$(curl -s http://localhost:8080/actuator/health | jq -r '.status' 2>/dev/null || echo "unknown")
if [ "$APP_HEALTH" = "UP" ]; then
    echo "✅ Application health check passed"
else
    echo "⚠️  Application health check: $APP_HEALTH"
fi
echo ""

# Test 4: Database Connection Test
echo "4️⃣ Testing Database Connection"
echo "------------------------------"
DB_TEST=$(psql -h localhost -U mommyshops -d mommyshops -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" -t 2>/dev/null || echo "0")
if [ "$DB_TEST" -gt 0 ]; then
    echo "✅ Database connection and tables are working"
else
    echo "⚠️  Database connection test inconclusive"
fi
echo ""

# Test 5: Manual Image Analysis Test
echo "5️⃣ Manual Image Analysis Test"
echo "-----------------------------"
echo "To test the complete image analysis flow:"
echo ""
echo "1. Open your browser and go to: http://localhost:8080/analysis"
echo "2. Upload the test image: $TEST_IMAGE"
echo "3. Enter a product name (e.g., 'Test Product')"
echo "4. Click 'Analizar imagen'"
echo "5. Wait for the AI analysis to complete"
echo "6. Review the safety scores and recommendations"
echo ""

echo "🎉 Complete test setup is ready!"
echo ""
echo "📋 Summary:"
echo "   - PostgreSQL: ✅ Running"
echo "   - Ollama: ✅ Running with models"
echo "   - Spring Boot: ✅ Running"
echo "   - Test Image: ✅ Available ($TEST_IMAGE)"
echo ""
echo "🌐 Access Points:"
echo "   - Main App: http://localhost:8080"
echo "   - Analysis: http://localhost:8080/analysis"
echo "   - Health: http://localhost:8080/actuator/health"
echo "   - Ollama Health: http://localhost:8080/api/ollama/health"
echo ""
echo "🔧 Troubleshooting:"
echo "   - If Ollama health shows DOWN: Check if models are loaded"
echo "   - If analysis fails: Check browser console for errors"
echo "   - If database errors: Check PostgreSQL connection"
echo ""
echo "✨ Ready to test image analysis with test3.jpg!"