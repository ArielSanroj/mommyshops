"""
Authentication utilities for MommyShops application
Consolidated user authentication and authorization
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database.session import get_db
from app.database.models import User
from app.database.security import get_user_by_email, get_user_by_username
from .jwt import verify_token
from .password import verify_password

logger = logging.getLogger(__name__)

# OAuth2 scheme with optional token support
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    
    Args:
        token: JWT token from request
        db: Database session
        
    Returns:
        Authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(token)
        if payload is None:
            raise credentials_exception
        
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except Exception:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise
    
    Args:
        token: JWT token from request (optional)
        db: Database session
        
    Returns:
        Authenticated user or None
    """
    if not token:
        return None
    
    try:
        payload = verify_token(token)
        if payload is None:
            return None
        
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
            
        user = db.query(User).filter(User.id == user_id).first()
        return user
        
    except Exception:
        return None


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate user with username/email and password
    
    Args:
        db: Database session
        username: Username or email
        password: Plain text password
        
    Returns:
        Authenticated user or None
    """
    # Try username first
    user = get_user_by_username(db, username)
    
    # If not found, try email
    if not user:
        user = get_user_by_email(db, username)
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


def create_user(
    db: Session,
    username: str,
    email: str,
    password: str,
    **kwargs
) -> User:
    """
    Create a new user
    
    Args:
        db: Database session
        username: Username
        email: Email address
        password: Plain text password
        **kwargs: Additional user fields
        
    Returns:
        Created user
        
    Raises:
        HTTPException: If user already exists
    """
    from .password import hash_password
    
    # Check if user already exists
    if get_user_by_username(db, username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    if get_user_by_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = hash_password(password)
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        **kwargs
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user
