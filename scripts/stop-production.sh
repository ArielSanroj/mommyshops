#!/bin/bash

# MommyShops Production Stop Script

set -e

echo "🛑 Stopping MommyShops Production Environment"
echo "============================================="

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

# Function to check if process is running
is_process_running() {
    local pid=$1
    kill -0 $pid 2>/dev/null
}

# Stop the application
print_status $BLUE "🛑 Stopping MommyShops application..."

if [ -f "mommyshops.pid" ]; then
    APP_PID=$(cat mommyshops.pid)
    
    if is_process_running $APP_PID; then
        print_status $BLUE "Stopping process $APP_PID..."
        kill $APP_PID
        
        # Wait for graceful shutdown
        local count=0
        while is_process_running $APP_PID && [ $count -lt 30 ]; do
            print_status $YELLOW "Waiting for graceful shutdown... ($count/30)"
            sleep 1
            ((count++))
        done
        
        if is_process_running $APP_PID; then
            print_status $YELLOW "Force stopping process $APP_PID..."
            kill -9 $APP_PID
        fi
        
        print_status $GREEN "✅ Application stopped"
    else
        print_status $YELLOW "⚠️  Application process $APP_PID is not running"
    fi
    
    rm -f mommyshops.pid
else
    print_status $YELLOW "⚠️  PID file not found. Attempting to find and stop the application..."
    
    # Try to find the application process
    local pids=$(pgrep -f "mommyshops-app.*jar")
    if [ -n "$pids" ]; then
        echo $pids | xargs kill
        print_status $GREEN "✅ Application stopped"
    else
        print_status $YELLOW "⚠️  No application process found"
    fi
fi

# Stop Docker containers
print_status $BLUE "🐳 Stopping Docker containers..."

# Stop PostgreSQL
if docker ps -q -f name=mommyshops-postgres | grep -q .; then
    print_status $BLUE "Stopping PostgreSQL container..."
    docker stop mommyshops-postgres
    docker rm mommyshops-postgres
    print_status $GREEN "✅ PostgreSQL container stopped"
else
    print_status $YELLOW "⚠️  PostgreSQL container not found"
fi

# Stop Redis
if docker ps -q -f name=mommyshops-redis | grep -q .; then
    print_status $BLUE "Stopping Redis container..."
    docker stop mommyshops-redis
    docker rm mommyshops-redis
    print_status $GREEN "✅ Redis container stopped"
else
    print_status $YELLOW "⚠️  Redis container not found"
fi

# Stop Ollama if it was started by us
if pgrep -f "ollama serve" >/dev/null; then
    print_status $BLUE "Stopping Ollama..."
    pkill -f "ollama serve"
    print_status $GREEN "✅ Ollama stopped"
else
    print_status $YELLOW "⚠️  Ollama not running or not started by this script"
fi

# Clean up temporary files
print_status $BLUE "🧹 Cleaning up temporary files..."

# Remove PID file
rm -f mommyshops.pid

# Clean up logs if requested
if [ "$1" = "--clean-logs" ]; then
    print_status $BLUE "Cleaning up log files..."
    rm -rf logs/*
    print_status $GREEN "✅ Log files cleaned"
fi

print_status $GREEN "🎉 MommyShops production environment stopped successfully!"
print_status $BLUE "💡 To start again, run: ./start-production.sh"