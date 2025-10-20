#!/bin/bash
# Script para instalar dependencias faltantes

echo "🔧 MommyShops - Fixing Dependencies"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found. Run this script from the project root."
    exit 1
fi

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "🔍 Checking Tesseract installation..."

# Check if Tesseract is installed
if command -v tesseract &> /dev/null; then
    echo "✅ Tesseract is installed"
    tesseract --version
else
    echo "❌ Tesseract not found"
    echo "💡 Installing Tesseract via Homebrew..."
    
    # Check if Homebrew is installed
    if command -v brew &> /dev/null; then
        brew install tesseract
        echo "✅ Tesseract installed via Homebrew"
    else
        echo "❌ Homebrew not found. Please install Tesseract manually:"
        echo "   - macOS: brew install tesseract"
        echo "   - Ubuntu: sudo apt-get install tesseract-ocr"
        echo "   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
    fi
fi

echo ""
echo "🔍 Checking PostgreSQL..."

# Check if PostgreSQL is running
if pg_isready -q; then
    echo "✅ PostgreSQL is running"
else
    echo "❌ PostgreSQL not running"
    echo "💡 Start PostgreSQL:"
    echo "   - macOS: brew services start postgresql"
    echo "   - Ubuntu: sudo systemctl start postgresql"
    echo "   - Or start via pgAdmin/other tools"
fi

echo ""
echo "🧪 Running diagnostic tests..."
python test_ocr_debug.py

echo ""
echo "✅ Dependency fix complete!"
echo "💡 If tests still fail, check the error messages above."