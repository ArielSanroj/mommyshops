"""
MommyShops FastAPI Application
Modular application with clean architecture
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
import time
from typing import Dict, Any

# Import routers
from app.routers import auth_router, analysis_router, health_router, admin_router

# Import middleware
from app.middleware import (
    configure_cors,
    configure_security_middleware,
    configure_logging_middleware,
    configure_rate_limiting
)

# Import dependencies
from app.dependencies import get_app_settings

# Setup logging
from app.core.logging import setup_logging, get_logger
setup_logging(os.getenv("ENVIRONMENT", "development"))
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting MommyShops application...")
    
    # Initialize application settings
    settings = get_app_settings()
    logger.info(f"Application configured for environment: {settings.ENVIRONMENT}")
    
    # TODO: Initialize database connections
    # TODO: Initialize Redis connections
    # TODO: Initialize external API clients
    
    yield
    
    # Shutdown
    logger.info("Shutting down MommyShops application...")
    # TODO: Close database connections
    # TODO: Close Redis connections
    # TODO: Cleanup resources

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    # Create FastAPI app
    app = FastAPI(
        title="MommyShops API",
        description="Clean and Optimized Cosmetic Ingredient Analysis System",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # Configure middleware
    configure_cors(app)
    configure_security_middleware(app)
    configure_logging_middleware(app)
    configure_rate_limiting(app)
    
    # Include routers
    app.include_router(auth_router)
    app.include_router(analysis_router)
    app.include_router(health_router)
    app.include_router(admin_router)
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "request_id": getattr(request.state, 'request_id', None)
            }
        )
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "MommyShops API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health"
        }
    
    return app

# Create app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
