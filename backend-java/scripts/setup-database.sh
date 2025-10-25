#!/bin/bash

# PostgreSQL Database Setup Script for MommyShops
# This script sets up the PostgreSQL database and user

set -e

echo "🗄️ Setting up PostgreSQL database for MommyShops..."

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed. Installing PostgreSQL..."
    brew install postgresql
    echo "✅ PostgreSQL installed successfully"
else
    echo "✅ PostgreSQL is already installed"
fi

# Start PostgreSQL service
echo "🔄 Starting PostgreSQL service..."
brew services start postgresql

# Wait for PostgreSQL to start
echo "⏳ Waiting for PostgreSQL to start..."
sleep 3

# Create database and user
echo "📊 Creating database and user..."
psql postgres -c "CREATE DATABASE mommyshops;" 2>/dev/null || echo "Database already exists"
psql postgres -c "CREATE USER mommyshops WITH PASSWORD 'change-me';" 2>/dev/null || echo "User already exists"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE mommyshops TO mommyshops;" 2>/dev/null || echo "Privileges already granted"

# Test connection
echo "🧪 Testing database connection..."
if psql -h localhost -U mommyshops -d mommyshops -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Database connection successful"
else
    echo "❌ Database connection failed"
    echo "Please check your PostgreSQL configuration"
    exit 1
fi

echo ""
echo "🎉 PostgreSQL setup completed successfully!"
echo ""
echo "📋 Database Configuration:"
echo "   - Host: localhost"
echo "   - Port: 5432"
echo "   - Database: mommyshops"
echo "   - Username: mommyshops"
echo "   - Password: change-me"
echo ""
echo "🔧 Next steps:"
echo "1. Run: ./scripts/setup-ollama-complete.sh"
echo "2. Run: ./scripts/start-application.sh"
echo "3. Test with: ./scripts/test-complete-flow.sh"