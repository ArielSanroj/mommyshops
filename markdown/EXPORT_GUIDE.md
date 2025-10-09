# 📦 MommyShops Project Export Guide

## 🚀 Quick Export (Automated)

Run the automated export script:

```bash
./export_project.sh
```

This will create a complete export package with everything needed to set up MommyShops on another Mac.

## 📋 Manual Export Steps

If you prefer to do it manually:

### 1. Create Export Directory
```bash
mkdir mommyshops_export
cd mommyshops_export
```

### 2. Copy Project Files
```bash
# Copy all files except virtual environment and cache
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
          ../mommyshops/ .
```

### 3. Export Requirements
```bash
# Activate virtual environment and export requirements
source ../mommyshops/.venv/bin/activate
pip freeze > requirements.txt
deactivate
```

### 4. Create Setup Script
Create `setup_new_mac.sh` with the setup instructions.

### 5. Create Archive
```bash
cd ..
tar -czf mommyshops_export.tar.gz mommyshops_export/
```

## 🖥️ Setting Up on New Mac

### Method 1: Automated Setup
1. Copy the export package to the new Mac
2. Extract: `tar -xzf mommyshops_export.tar.gz`
3. Navigate: `cd mommyshops_export`
4. Run: `./setup_new_mac.sh`
5. Configure `.env` with your API keys
6. Start: `./start_app.sh`

### Method 2: Manual Setup
1. Install dependencies:
   ```bash
   brew install python@3.11 postgresql tesseract tesseract-lang
   ```

2. Setup Python environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Setup database:
   ```bash
   brew services start postgresql
   createdb mommyshops_db
   python init_db.py
   ```

4. Configure environment:
   - Copy `.env` file
   - Add your API keys

5. Start application:
   ```bash
   ./start_app.sh
   ```

## 🔑 Required API Keys

Make sure to have these API keys ready:

- **OpenAI API Key**: For AI-powered ingredient analysis
- **Apify API Key**: For web scraping product information
- **Meta Access Token**: For WhatsApp integration (optional)
- **NVIDIA API Key**: For Nemotron integration (optional)

## 📱 Access Points

Once set up, access the application at:

- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🆘 Troubleshooting

### Common Issues:

1. **Tesseract not found**:
   - Check path in `.env` file
   - Install: `brew install tesseract tesseract-lang`

2. **Database connection error**:
   - Ensure PostgreSQL is running: `brew services start postgresql`
   - Check database exists: `createdb mommyshops_db`

3. **API errors**:
   - Verify API keys in `.env` file
   - Check internet connection

4. **Python dependencies**:
   - Reinstall: `pip install -r requirements.txt`
   - Check Python version: `python3 --version`

## ✨ Features Included

The exported project includes:

- ✅ Enhanced product recognition system
- ✅ Multi-source ingredient analysis (FDA, EWG, PubChem, etc.)
- ✅ AI-powered analysis (OpenAI, NVIDIA)
- ✅ Web interface (Streamlit)
- ✅ REST API (FastAPI)
- ✅ Database integration (PostgreSQL)
- ✅ OCR processing (Tesseract)
- ✅ WhatsApp integration (optional)

## 📞 Support

If you encounter issues:

1. Check the logs: `tail -f backend.log`
2. Review the setup documentation
3. Verify all dependencies are installed
4. Ensure API keys are correctly configured