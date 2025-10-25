"""
Security utilities for MommyShops API
"""

import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, UploadFile
from passlib.context import CryptContext
import magic
import os

from .config import get_settings

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    """
    return pwd_context.verify(plain_password, hashed_password)

# JWT tokens
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(seconds=settings.JWT_EXPIRATION)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt

def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify a JWT access token
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

# File upload validation
async def validate_image_upload(file: UploadFile) -> bool:
    """
    Validate uploaded image file for security
    
    Args:
        file: The uploaded file
        
    Returns:
        True if valid, raises HTTPException otherwise
        
    Raises:
        HTTPException: If file is invalid or dangerous
    """
    # Check file extension
    allowed_extensions = [ext.strip() for ext in settings.ALLOWED_IMAGE_EXTENSIONS.split(",")]
    file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Check file size
    contents = await file.read()
    file_size = len(contents)
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
        )
    
    # Check actual MIME type (not just extension)
    try:
        mime = magic.from_buffer(contents, mime=True)
        allowed_mimes = ["image/jpeg", "image/png", "image/webp", "image/jpg"]
        
        if mime not in allowed_mimes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. File appears to be: {mime}"
            )
    except Exception as e:
        # If python-magic is not available, skip MIME check
        pass
    
    # Reset file pointer for further processing
    await file.seek(0)
    
    return True

def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token
    """
    return secrets.token_urlsafe(length)

def hash_data(data: str) -> str:
    """
    Hash data using SHA-256
    """
    return hashlib.sha256(data.encode()).hexdigest()

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal attacks
    """
    # Remove any path components
    filename = os.path.basename(filename)
    
    # Remove or replace dangerous characters
    dangerous_chars = ['..', '/', '\\', '\x00', '<', '>', ':', '"', '|', '?', '*']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    return filename

def validate_password_strength(password: str) -> bool:
    """
    Validate password meets security requirements
    
    Requirements:
    - At least 8 characters
    - Contains uppercase and lowercase
    - Contains numbers
    - Contains special characters
    """
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    if not any(c.isupper() for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one uppercase letter"
        )
    
    if not any(c.islower() for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one lowercase letter"
        )
    
    if not any(c.isdigit() for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one number"
        )
    
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one special character"
        )
    
    return True
