"""
Rate limiting middleware configuration
"""

from fastapi import FastAPI
from security import configure_security

def configure_rate_limiting(app: FastAPI):
    """Configure rate limiting middleware"""
    configure_security(app)
