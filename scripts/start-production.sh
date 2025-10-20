#!/bin/bash

# MommyShops Production Startup Script
# Based on start.py functionality

set -e

echo "🚀 Starting MommyShops Production Environment"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is available
port_available() {
    local port=$1
    ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1
}

# Function to wait for service
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1
    
    print_status $BLUE "Waiting for $service_name to be available at $host:$port..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z $host $port 2>/dev/null; then
            print_status $GREEN "✅ $service_name is available"
            return 0
        fi
        
        print_status $YELLOW "Attempt $attempt/$max_attempts: $service_name not ready yet..."
        sleep 2
        ((attempt++))
    done
    
    print_status $RED "❌ $service_name failed to start after $max_attempts attempts"
    return 1
}

# Check prerequisites
print_status $BLUE "🔍 Checking prerequisites..."

# Check Java
if ! command_exists java; then
    print_status $RED "❌ Java is not installed. Please install Java 21 or higher."
    exit 1
fi

JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
if [ "$JAVA_VERSION" -lt 21 ]; then
    print_status $RED "❌ Java version $JAVA_VERSION is not supported. Please install Java 21 or higher."
    exit 1
fi

print_status $GREEN "✅ Java $JAVA_VERSION is installed"

# Check Maven
if ! command_exists mvn; then
    print_status $RED "❌ Maven is not installed. Please install Maven."
    exit 1
fi

print_status $GREEN "✅ Maven is installed"

# Check Docker
if ! command_exists docker; then
    print_status $RED "❌ Docker is not installed. Please install Docker."
    exit 1
fi

print_status $GREEN "✅ Docker is installed"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_status $RED "❌ Docker is not running. Please start Docker."
    exit 1
fi

print_status $GREEN "✅ Docker is running"

# Check Ollama
if ! command_exists ollama; then
    print_status $YELLOW "⚠️  Ollama is not installed. AI features will be disabled."
    OLLAMA_AVAILABLE=false
else
    print_status $GREEN "✅ Ollama is installed"
    OLLAMA_AVAILABLE=true
fi

# Check if Ollama is running
if [ "$OLLAMA_AVAILABLE" = true ]; then
    if ! curl -s http://localhost:11434/api/version >/dev/null 2>&1; then
        print_status $YELLOW "⚠️  Ollama is not running. Starting Ollama..."
        ollama serve &
        sleep 5
        
        if ! curl -s http://localhost:11434/api/version >/dev/null 2>&1; then
            print_status $RED "❌ Failed to start Ollama. AI features will be disabled."
            OLLAMA_AVAILABLE=false
        else
            print_status $GREEN "✅ Ollama is running"
        fi
    else
        print_status $GREEN "✅ Ollama is running"
    fi
fi

# Check if required models are available
if [ "$OLLAMA_AVAILABLE" = true ]; then
    print_status $BLUE "🤖 Checking Ollama models..."
    
    # Check for llama3.1 model
    if ! ollama list | grep -q "llama3.1"; then
        print_status $YELLOW "⚠️  llama3.1 model not found. Pulling model..."
        ollama pull llama3.1
    fi
    
    # Check for llava model
    if ! ollama list | grep -q "llava"; then
        print_status $YELLOW "⚠️  llava model not found. Pulling model..."
        ollama pull llava
    fi
    
    print_status $GREEN "✅ Required Ollama models are available"
fi

# Check if ports are available
print_status $BLUE "🔌 Checking port availability..."

if ! port_available 8080; then
    print_status $RED "❌ Port 8080 is already in use. Please stop the service using this port."
    exit 1
fi

if ! port_available 5432; then
    print_status $YELLOW "⚠️  Port 5432 is already in use. Using existing PostgreSQL instance."
    USE_EXISTING_POSTGRES=true
else
    USE_EXISTING_POSTGRES=false
fi

if ! port_available 6379; then
    print_status $YELLOW "⚠️  Port 6379 is already in use. Using existing Redis instance."
    USE_EXISTING_REDIS=true
else
    USE_EXISTING_REDIS=false
fi

# Start required services
print_status $BLUE "🐳 Starting required services..."

# Start PostgreSQL if not already running
if [ "$USE_EXISTING_POSTGRES" = false ]; then
    print_status $BLUE "Starting PostgreSQL..."
    docker run -d \
        --name mommyshops-postgres \
        -e POSTGRES_DB=mommyshops_prod \
        -e POSTGRES_USER=mommyshops \
        -e POSTGRES_PASSWORD=mommyshops123 \
        -p 5432:5432 \
        postgres:15-alpine
    
    wait_for_service localhost 5432 "PostgreSQL"
fi

# Start Redis if not already running
if [ "$USE_EXISTING_REDIS" = false ]; then
    print_status $BLUE "Starting Redis..."
    docker run -d \
        --name mommyshops-redis \
        -p 6379:6379 \
        redis:7-alpine
    
    wait_for_service localhost 6379 "Redis"
fi

# Set environment variables
print_status $BLUE "🔧 Setting environment variables..."

export SPRING_PROFILES_ACTIVE=production
export DATABASE_URL=jdbc:postgresql://localhost:5432/mommyshops_prod
export DATABASE_USERNAME=mommyshops
export DATABASE_PASSWORD=mommyshops123
export REDIS_HOST=localhost
export REDIS_PORT=6379
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=llama3.1
export OLLAMA_VISION_MODEL=llava
export LOG_LEVEL=INFO
export BACKEND_LOG_PATH=logs/backend.log

# Create logs directory
mkdir -p logs

# Build the application
print_status $BLUE "🔨 Building the application..."

if [ ! -f "pom.xml" ]; then
    print_status $RED "❌ pom.xml not found. Please run this script from the project root directory."
    exit 1
fi

mvn clean package -DskipTests

if [ $? -ne 0 ]; then
    print_status $RED "❌ Build failed. Please check the error messages above."
    exit 1
fi

print_status $GREEN "✅ Build completed successfully"

# Run database migrations
print_status $BLUE "🗄️  Running database migrations..."

# This would typically use Flyway or Liquibase
# For now, we'll just create the database if it doesn't exist
docker exec mommyshops-postgres psql -U mommyshops -d postgres -c "CREATE DATABASE IF NOT EXISTS mommyshops_prod;" 2>/dev/null || true

# Start the application
print_status $BLUE "🚀 Starting MommyShops application..."

# Set JVM options for production
export JAVA_OPTS="-Xms512m -Xmx2g -XX:+UseG1GC -XX:+UseStringDeduplication -XX:+OptimizeStringConcat"

# Start the application
java $JAVA_OPTS -jar target/mommyshops-app-*.jar &

# Get the PID
APP_PID=$!

# Wait for application to start
print_status $BLUE "⏳ Waiting for application to start..."
wait_for_service localhost 8080 "MommyShops Application"

if [ $? -eq 0 ]; then
    print_status $GREEN "🎉 MommyShops is now running!"
    print_status $GREEN "📱 Application URL: http://localhost:8080"
    print_status $GREEN "🔍 Health Check: http://localhost:8080/api/health"
    print_status $GREEN "📊 Metrics: http://localhost:8080/actuator/health"
    
    # Save PID to file
    echo $APP_PID > mommyshops.pid
    
    print_status $BLUE "💡 To stop the application, run: kill $APP_PID"
    print_status $BLUE "💡 Or use: ./stop-production.sh"
    
    # Show logs
    print_status $BLUE "📋 Application logs:"
    tail -f logs/mommyshops.log
else
    print_status $RED "❌ Application failed to start. Check the logs for details."
    exit 1
fi