"""
CORS middleware configuration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings

def configure_cors(app: FastAPI):
    """Configure CORS middleware"""
    settings = get_settings()
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS.split(","),
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS.split(","),
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=600,
    )
