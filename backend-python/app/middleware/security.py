"""
Security middleware configuration
"""

from fastapi import FastAPI
from security_enhanced import configure_enhanced_security

def configure_security_middleware(app: FastAPI):
    """Configure security middleware"""
    configure_enhanced_security(app)
