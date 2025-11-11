"""
CORS middleware configuration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import get_settings

def configure_cors(app: FastAPI):
    """Configure CORS middleware"""
    settings = get_settings()
    
    # Parse CORS origins, handling wildcards for Vercel domains
    origins = []
    for origin in settings.CORS_ORIGINS.split(","):
        origin = origin.strip()
        if origin:
            origins.append(origin)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS.split(","),
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=600,
    )
