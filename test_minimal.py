#!/usr/bin/env python3
"""
Minimal test app to verify Railway deployment
"""

from fastapi import FastAPI
import os

app = FastAPI(title="MommyShops Test", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "MommyShops Test API is running", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/debug/env")
async def debug_env():
    """Debug environment variables."""
    return {
        "GOOGLE_CLIENT_ID": "SET" if os.getenv("GOOGLE_CLIENT_ID") else "NOT_SET",
        "GOOGLE_CLIENT_SECRET": "SET" if os.getenv("GOOGLE_CLIENT_SECRET") else "NOT_SET",
        "GOOGLE_REDIRECT_URI": os.getenv("GOOGLE_REDIRECT_URI", "NOT_SET"),
        "FIREBASE_CREDENTIALS": "SET" if os.getenv("FIREBASE_CREDENTIALS") else "NOT_SET",
        "GOOGLE_VISION_API_KEY": "SET" if os.getenv("GOOGLE_VISION_API_KEY") else "NOT_SET",
        "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT", "NOT_SET"),
        "DATABASE_URL": "SET" if os.getenv("DATABASE_URL") else "NOT_SET"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)