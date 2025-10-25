#!/bin/bash

# MommyShops Setup Script for New Mac
# Run this script to set up MommyShops on a new Mac

set -e

echo "🚀 Setting up MommyShops on new Mac"
echo "==================================="

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "📦 Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "✅ Homebrew already installed"
fi

# Install system dependencies
echo "📦 Installing system dependencies..."
brew install python@3.11 postgresql tesseract tesseract-lang

# Install Python dependencies
echo "🐍 Setting up Python environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Setup PostgreSQL
echo "🗄️  Setting up PostgreSQL..."
brew services start postgresql
createdb mommyshops_db 2>/dev/null || echo "Database already exists"

# Setup Tesseract
echo "🔍 Setting up Tesseract..."
TESSERACT_PATH=$(which tesseract)
echo "Tesseract found at: $TESSERACT_PATH"

# Create .env file template
echo "⚙️  Creating environment configuration..."
cat > .env << 'ENVEOF'
# Database Configuration
DATABASE_URL=postgresql://postgres@localhost:5432/mommyshops_db

# OCR Configuration
TESSERACT_PATH=/opt/homebrew/bin/tesseract

# WhatsApp/Meta Configuration (Add your tokens)
META_ACCESS_TOKEN=your_meta_access_token_here
META_PHONE_NUMBER_ID=your_phone_number_id_here

# Nanobot/NVIDIA Configuration (Optional)
NANOBOT_API_URL=http://localhost:8080/api/chat
NVIDIA_API_KEY=your_nvidia_api_key_here
MCP_ACCESS_TOKEN=your_mcp_access_token_here

# External API Keys (Add your keys)
ENTREZ_EMAIL=your_email@example.com
APIFY_API_KEY=your_apify_api_key_here
ENVEOF

echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run: python init_db.py"
echo "3. Run: ./start_app.sh"
echo ""
echo "🌐 Access the app at:"
echo "   Frontend: http://localhost:8501"
echo "   Backend: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
