"""
Shared dependencies for MommyShops application
Centralized dependency injection for better maintainability
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database.session import get_db
from app.database.models import User
from core.config import get_settings
from app.security.auth import get_current_user, get_current_user_optional

logger = logging.getLogger(__name__)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Settings dependency
def get_app_settings():
    """Get application settings"""
    return get_settings()

# Database dependency
def get_database() -> Session:
    """Get database session"""
    return get_db()

# Authentication dependencies
def require_auth(current_user: User = Depends(get_current_user)) -> User:
    """Require authenticated user"""
    return current_user

def optional_auth(current_user: Optional[User] = Depends(get_current_user_optional)) -> Optional[User]:
    """Optional authentication"""
    return current_user

# Admin authentication
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin user"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# Rate limiting dependency
def get_rate_limit_key(request, current_user: Optional[User] = Depends(optional_auth)) -> str:
    """Get rate limit key for user or IP"""
    if current_user:
        return f"user:{current_user.id}"
    else:
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

# Logging dependency
def get_request_logger():
    """Get request logger with context"""
    return logger
