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
