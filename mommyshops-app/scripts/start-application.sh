#!/bin/bash

# Spring Boot Application Startup Script for MommyShops
# This script starts the Spring Boot application with proper configuration

set -e

echo "🚀 Starting MommyShops Spring Boot Application..."

# Check if we're in the right directory
if [ ! -f "pom.xml" ]; then
    echo "❌ Please run this script from the mommyshops-app directory"
    exit 1
fi

# Check if Maven is available
if ! command -v mvn &> /dev/null; then
    echo "❌ Maven is not installed. Please install Maven first."
    exit 1
fi

# Check if PostgreSQL is running
echo "🔍 Checking PostgreSQL connection..."
if ! psql -h localhost -U mommyshops -d mommyshops -c "SELECT 1;" > /dev/null 2>&1; then
    echo "❌ PostgreSQL is not running or not accessible"
    echo "Please run: ./scripts/setup-database.sh"
    exit 1
fi
echo "✅ PostgreSQL is running"

# Check if Ollama is running
echo "🔍 Checking Ollama connection..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama is not running or not accessible"
    echo "Please run: ./scripts/setup-ollama-complete.sh"
    exit 1
fi
echo "✅ Ollama is running"

# Load environment variables
if [ -f ".env" ]; then
    echo "📋 Loading environment variables..."
    source .env
fi

# Set default environment variables if not set
export OLLAMA_BASE_URL=${OLLAMA_BASE_URL:-http://localhost:11434}
export OLLAMA_MODEL=${OLLAMA_MODEL:-llama3.1}
export OLLAMA_VISION_MODEL=${OLLAMA_VISION_MODEL:-llava}

# Set database configuration
export SPRING_DATASOURCE_URL=${SPRING_DATASOURCE_URL:-jdbc:postgresql://localhost:5432/mommyshops}
export SPRING_DATASOURCE_USERNAME=${SPRING_DATASOURCE_USERNAME:-mommyshops}
export SPRING_DATASOURCE_PASSWORD=${SPRING_DATASOURCE_PASSWORD:-change-me}

# Set Redis configuration (optional)
export SPRING_DATA_REDIS_HOST=${SPRING_DATA_REDIS_HOST:-localhost}
export SPRING_DATA_REDIS_PORT=${SPRING_DATA_REDIS_PORT:-6379}

echo "🔧 Configuration:"
echo "   - Database: $SPRING_DATASOURCE_URL"
echo "   - Ollama: $OLLAMA_BASE_URL"
echo "   - Text Model: $OLLAMA_MODEL"
echo "   - Vision Model: $OLLAMA_VISION_MODEL"
echo ""

# Compile the application
echo "🔨 Compiling application..."
mvn clean compile -q

if [ $? -eq 0 ]; then
    echo "✅ Compilation successful"
else
    echo "❌ Compilation failed"
    exit 1
fi

# Start the application
echo "🚀 Starting Spring Boot application..."
echo "   Application will be available at: http://localhost:8080"
echo "   Analysis view: http://localhost:8080/analysis"
echo "   Health check: http://localhost:8080/actuator/health"
echo "   Ollama health: http://localhost:8080/api/ollama/health"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

# Start the application
mvn spring-boot:run