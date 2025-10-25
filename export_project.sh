#!/bin/bash

# MommyShops Project Export Script
# This script creates a complete export package for transferring to another Mac

set -e

echo "🚀 MommyShops Project Export Script"
echo "=================================="

# Configuration
PROJECT_NAME="mommyshops"
EXPORT_DIR="${PROJECT_NAME}_export_$(date +%Y%m%d_%H%M%S)"
CURRENT_DIR=$(pwd)

echo "📦 Creating export package: $EXPORT_DIR"
mkdir -p "$EXPORT_DIR"

# 1. Copy all project files (excluding virtual environment and cache)
echo "📁 Copying project files..."
rsync -av --exclude='.venv/' \
          --exclude='__pycache__/' \
          --exclude='*.pyc' \
          --exclude='.git/' \
          --exclude='backend.log' \
          --exclude='*.log' \
          --exclude='.DS_Store' \
          --exclude='node_modules/' \
          --exclude='*.sqlite' \
          --exclude='*.db' \
          "$CURRENT_DIR/" "$EXPORT_DIR/"

# 2. Create requirements.txt with current environment
echo "📋 Creating requirements.txt..."
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    pip freeze > "$EXPORT_DIR/requirements.txt"
    echo "✅ Requirements exported from virtual environment"
else
    echo "⚠️  No virtual environment found, using existing requirements.txt"
fi

# 3. Create setup script for the new Mac
echo "🛠️  Creating setup script..."
cat > "$EXPORT_DIR/setup_new_mac.sh" << 'EOF'
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
EOF

chmod +x "$EXPORT_DIR/setup_new_mac.sh"

# 4. Create README for the new Mac
echo "📖 Creating setup README..."
cat > "$EXPORT_DIR/README_SETUP.md" << 'EOF'
# MommyShops - Setup on New Mac

## Quick Setup

1. **Run the setup script:**
   ```bash
   chmod +x setup_new_mac.sh
   ./setup_new_mac.sh
   ```

2. **Configure environment variables:**
   Edit `.env` file with your API keys:
   - OpenAI API Key
   - Apify API Key  
   - Meta/WhatsApp tokens (if using WhatsApp integration)

3. **Initialize database:**
   ```bash
   python init_db.py
   ```

4. **Start the application:**
   ```bash
   ./start_app.sh
   ```

## Manual Setup (Alternative)

If the automated setup doesn't work, follow these steps:

### 1. Install Dependencies
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install system dependencies
brew install python@3.11 postgresql tesseract tesseract-lang
```

### 2. Setup Python Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Setup Database
```bash
brew services start postgresql
createdb mommyshops_db
python init_db.py
```

### 4. Configure Environment
Copy `.env` file and update with your API keys.

### 5. Start Application
```bash
./start_app.sh
```

## Features

- **Enhanced Product Recognition**: Recognizes products from photos
- **Multi-source Ingredient Analysis**: FDA, EWG, PubChem, etc.
- **AI-powered Analysis**: OpenAI and NVIDIA integration
- **Web Interface**: Streamlit frontend
- **REST API**: FastAPI backend

## Troubleshooting

- **Tesseract not found**: Check path in `.env` file
- **Database connection**: Ensure PostgreSQL is running
- **API errors**: Verify API keys in `.env` file
EOF

# 5. Create a compressed archive
echo "🗜️  Creating compressed archive..."
tar -czf "${EXPORT_DIR}.tar.gz" "$EXPORT_DIR"

# 6. Create transfer instructions
echo "📋 Creating transfer instructions..."
cat > "${EXPORT_DIR}_TRANSFER_INSTRUCTIONS.txt" << EOF
MommyShops Project Export - Transfer Instructions
================================================

Export created: $(date)
Source Mac: $(hostname)
Project: $PROJECT_NAME

📦 EXPORT PACKAGE: ${EXPORT_DIR}.tar.gz

🚀 QUICK TRANSFER:
1. Copy ${EXPORT_DIR}.tar.gz to the new Mac
2. Extract: tar -xzf ${EXPORT_DIR}.tar.gz
3. Navigate to: cd $EXPORT_DIR
4. Run setup: ./setup_new_mac.sh
5. Configure: Edit .env with your API keys
6. Start: ./start_app.sh

📋 WHAT'S INCLUDED:
✅ All source code and configurations
✅ Requirements.txt with exact versions
✅ Automated setup script
✅ Database initialization
✅ Environment configuration template
✅ Complete documentation

🔑 REQUIRED API KEYS:
- OpenAI API Key (for AI analysis)
- Apify API Key (for web scraping)
- Meta Access Token (for WhatsApp integration)

📱 ACCESS POINTS:
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

🆘 SUPPORT:
- Check README_SETUP.md for detailed instructions
- Review logs in backend.log for troubleshooting
EOF

echo ""
echo "✅ Export completed successfully!"
echo ""
echo "📦 Export package: ${EXPORT_DIR}.tar.gz"
echo "📁 Export directory: $EXPORT_DIR"
echo "📋 Instructions: ${EXPORT_DIR}_TRANSFER_INSTRUCTIONS.txt"
echo ""
echo "🚀 To transfer to another Mac:"
echo "1. Copy ${EXPORT_DIR}.tar.gz to the new Mac"
echo "2. Extract: tar -xzf ${EXPORT_DIR}.tar.gz"
echo "3. Run: cd $EXPORT_DIR && ./setup_new_mac.sh"
echo ""
echo "📱 The new Mac will have the complete MommyShops system!"
