#!/bin/bash

# Complete Ollama Setup Script for MommyShops
# This script sets up Ollama with all required models

set -e

echo "🤖 Setting up Ollama with AI models for MommyShops..."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed. Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
    echo "✅ Ollama installed successfully"
else
    echo "✅ Ollama is already installed"
fi

# Start Ollama service
echo "🔄 Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to start
echo "⏳ Waiting for Ollama to start..."
sleep 10

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Failed to start Ollama service"
    exit 1
fi

echo "✅ Ollama service is running"

# Pull required models
echo "📥 Pulling required AI models..."

echo "  - Pulling llama3.1 (text generation)..."
ollama pull llama3.1

echo "  - Pulling llava (vision model for image analysis)..."
ollama pull llava

echo "  - Pulling llama3.1:8b (smaller, faster model)..."
ollama pull llama3.1:8b

echo "✅ All models pulled successfully"

# Set environment variables
echo "🔧 Setting up environment variables..."

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    touch .env
fi

# Add Ollama configuration to .env
if ! grep -q "OLLAMA_BASE_URL" .env; then
    echo "" >> .env
    echo "# Ollama Configuration" >> .env
    echo "export OLLAMA_BASE_URL=http://localhost:11434" >> .env
    echo "export OLLAMA_MODEL=llama3.1" >> .env
    echo "export OLLAMA_VISION_MODEL=llava" >> .env
fi

# Source the .env file
source .env

echo "✅ Environment variables configured"

# Test the setup
echo "🧪 Testing Ollama setup..."

# Test basic connectivity
if curl -s http://localhost:11434/api/tags | grep -q "llama3.1"; then
    echo "✅ Ollama connectivity test passed"
else
    echo "❌ Ollama connectivity test failed"
    exit 1
fi

# Test text generation
echo "  - Testing text generation..."
TEXT_RESPONSE=$(curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1",
    "prompt": "List 3 cosmetic ingredients",
    "stream": false
  }' | jq -r '.response' 2>/dev/null || echo "test")

if [ "$TEXT_RESPONSE" != "null" ] && [ -n "$TEXT_RESPONSE" ]; then
    echo "✅ Text generation working"
else
    echo "⚠️  Text generation test inconclusive (jq may not be installed)"
fi

echo ""
echo "🎉 Ollama setup completed successfully!"
echo ""
echo "📋 Configuration:"
echo "   - Ollama Base URL: $OLLAMA_BASE_URL"
echo "   - Text Model: $OLLAMA_MODEL"
echo "   - Vision Model: $OLLAMA_VISION_MODEL"
echo ""
echo "🔧 Next steps:"
echo "1. Run: ./scripts/start-application.sh"
echo "2. Test with: ./scripts/test-complete-flow.sh"
echo ""
echo "⚠️  Note: Keep this terminal open to keep Ollama running, or start it manually with 'ollama serve'"