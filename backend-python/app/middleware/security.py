"""
Security middleware configuration
"""

from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware

def configure_security_middleware(app: FastAPI):
    """Configure security middleware"""
    # Add trusted host middleware
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
