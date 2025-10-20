#!/bin/bash

# MommyShops - Quick Restart Script
echo "🔄 Restarting MommyShops services..."

# Kill existing processes
echo "🧹 Stopping existing services..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:8501 | xargs kill -9 2>/dev/null || true
sleep 2

# Restart with the main script
echo "🚀 Restarting services..."
./start_app.sh