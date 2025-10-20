#!/bin/bash

# MommyShops - Start Script
echo "🚀 Starting MommyShops Application..."

# Kill any existing processes on ports 8000 and 8501
echo "🧹 Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:8501 | xargs kill -9 2>/dev/null || true
sleep 2

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not activated. Activating..."
    source .venv/bin/activate
fi

# Start backend in background
echo "🔧 Starting Backend (FastAPI) on port 8000..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Check if backend started successfully
if curl -s http://localhost:8000/docs > /dev/null; then
    echo "✅ Backend started successfully!"
else
    echo "❌ Backend failed to start. Check backend.log"
    echo "📄 Backend log:"
    cat backend.log
    exit 1
fi

# Start frontend
echo "🎨 Starting Frontend (Streamlit) on port 8501..."
echo ""
echo "✅ Both services started!"
echo "🌐 Frontend: http://localhost:8501"
echo "🔧 Backend: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "📄 Backend logs: tail -f backend.log"
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    lsof -ti:8501 | xargs kill -9 2>/dev/null || true
    echo "✅ Services stopped"
    exit
}

# Trap Ctrl+C
trap cleanup INT

# Start frontend (this will block)
streamlit run frontend.py --server.port 8501