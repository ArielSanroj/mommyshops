#!/bin/bash

# Ollama Setup Script for MommyShops
# This script sets up Ollama for local development

set -e

echo "🚀 Setting up Ollama for MommyShops..."

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
sleep 5

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Failed to start Ollama service"
    exit 1
fi

echo "✅ Ollama service is running"

# Pull required models
echo "📥 Pulling required models..."

echo "  - Pulling llama3.1..."
ollama pull llama3.1

echo "  - Pulling llava (for image analysis)..."
ollama pull llava

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

# Test model availability
if ollama list | grep -q "llama3.1"; then
    echo "✅ Model availability test passed"
else
    echo "❌ Model availability test failed"
    exit 1
fi

echo ""
echo "🎉 Ollama setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Make sure to source the environment variables:"
echo "   source .env"
echo ""
echo "2. Start your Spring Boot application:"
echo "   ./mvnw spring-boot:run"
echo ""
echo "3. Verify the integration by checking the health endpoint:"
echo "   curl http://localhost:8080/actuator/health"
echo ""
echo "🔧 Configuration:"
echo "   - Ollama Base URL: $OLLAMA_BASE_URL"
echo "   - Text Model: $OLLAMA_MODEL"
echo "   - Vision Model: $OLLAMA_VISION_MODEL"
echo ""
echo "⚠️  Note: Keep this terminal open to keep Ollama running, or start it manually with 'ollama serve'"