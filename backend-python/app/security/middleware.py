"""
Security middleware for MommyShops application
Consolidated security middleware configuration
"""

from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
import os
import logging

logger = logging.getLogger(__name__)


def configure_security_middleware(app: FastAPI) -> None:
    """
    Configure security middleware for the FastAPI application
    
    Args:
        app: FastAPI application instance
    """
    
    # Trusted hosts middleware
    trusted_hosts = os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1").split(",")
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=trusted_hosts
    )
    
    # HTTPS redirect (only in production)
    if os.getenv("REQUIRE_HTTPS", "false").lower() == "true":
        app.add_middleware(HTTPSRedirectMiddleware)
        logger.info("HTTPS redirect middleware enabled")
    
    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # HSTS header (only in production with HTTPS)
        if os.getenv("REQUIRE_HTTPS", "false").lower() == "true":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
    
    logger.info("Security middleware configured successfully")
