#!/usr/bin/env python3
"""
Startup script for MommyShops MVP
"""
import os
import sys
import subprocess
import asyncio
from pathlib import Path

def check_requirements():
    """Check if all requirements are installed."""
    print("🔍 Checking requirements...")
    
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import httpx
        import pytesseract
        from PIL import Image
        import pandas
        from Bio import Entrez
        from bs4 import BeautifulSoup
        print("✅ All Python packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_tesseract():
    """Check if Tesseract is installed."""
    print("🔍 Checking Tesseract OCR...")
    
    tesseract_path = os.getenv("TESSERACT_PATH", "tesseract")
    try:
        result = subprocess.run([tesseract_path, "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Tesseract OCR is installed")
            return True
        else:
            print("❌ Tesseract OCR not found")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Tesseract OCR not found")
        return False

def check_database():
    """Check database connection."""
    print("🔍 Checking database connection...")
    
    try:
        from database import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Please check your DATABASE_URL in .env file")
        return False

def check_env_file():
    """Check if .env file exists and has required variables."""
    print("🔍 Checking environment configuration...")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("Please copy .env.example to .env and configure it")
        return False
    
    required_vars = [
        "DATABASE_URL",
        "TESSERACT_PATH",
        "META_ACCESS_TOKEN",
        "META_PHONE_NUMBER_ID"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ Environment configuration looks good")
    return True

async def test_basic_functionality():
    """Test basic application functionality."""
    print("🔍 Testing basic functionality...")
    
    try:
        from api_utils import fetch_ingredient_data
        import httpx
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            result = await fetch_ingredient_data("glicerina", client)
            if result and "name" in result:
                print("✅ Basic API functionality works")
                return True
            else:
                print("❌ API functionality test failed")
                return False
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def initialize_database():
    """Initialize the database."""
    print("🔍 Initializing database...")
    
    try:
        from database import Base, engine
        Base.metadata.create_all(bind=engine)
        print("✅ Database initialized")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def main():
    """Main startup function."""
    print("🚀 MommyShops MVP Startup Check\n")
    
    checks = [
        ("Environment Configuration", check_env_file),
        ("Python Requirements", check_requirements),
        ("Tesseract OCR", check_tesseract),
        ("Database Connection", check_database),
        ("Database Initialization", initialize_database),
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n--- {check_name} ---")
        result = check_func()
        results.append((check_name, result))
    
    # Test basic functionality
    print(f"\n--- Basic Functionality ---")
    try:
        result = asyncio.run(test_basic_functionality())
        results.append(("Basic Functionality", result))
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        results.append(("Basic Functionality", False))
    
    print("\n" + "="*50)
    print("📊 Startup Check Results:")
    print("="*50)
    
    passed = 0
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} checks passed")
    
    if passed == len(results):
        print("\n🎉 All checks passed! You can start the application with:")
        print("   uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        print("\n📱 The API will be available at: http://localhost:8000")
        print("📚 API documentation at: http://localhost:8000/docs")
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above before starting.")
        sys.exit(1)

if __name__ == "__main__":
    main()