"""
Authentication routes for MommyShops API
Handles user registration, login, and JWT token management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
import logging

from ...core.database import get_db
from ...core.security import verify_password, create_access_token, get_current_user
from ...models.requests import AuthRegisterRequest, AuthLoginRequest
from ...models.responses import AuthRegisterResponse, TokenResponse, AuthenticatedUser
from ...database import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=AuthRegisterResponse, tags=["auth"])
async def register_user(
    request: AuthRegisterRequest,
    db: Session = Depends(get_db)
) -> AuthRegisterResponse:
    """
    Register a new user account
    """
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        user = User(
            email=request.email,
            hashed_password=request.password,  # This should be hashed
            full_name=request.full_name,
            is_active=True
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"User registered successfully: {user.email}")
        
        return AuthRegisterResponse(
            success=True,
            message="User registered successfully",
            user_id=str(user.id),
            email=user.email
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/token", response_model=TokenResponse, tags=["auth"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> TokenResponse:
    """
    Authenticate user and return JWT token
    """
    try:
        # Get user by email
        user = db.query(User).filter(User.email == form_data.username).first()
        
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token = create_access_token(data={"sub": user.email})
        
        logger.info(f"User logged in successfully: {user.email}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=3600
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/me", response_model=AuthenticatedUser, tags=["auth"])
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> AuthenticatedUser:
    """
    Get current authenticated user information
    """
    return AuthenticatedUser(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active
    )

@router.get("/google", tags=["auth"])
async def google_auth():
    """
    Initiate Google OAuth2 flow
    """
    # This would redirect to Google OAuth2
    pass

@router.get("/google/callback", tags=["auth"])
async def google_auth_callback():
    """
    Handle Google OAuth2 callback
    """
    # This would handle the OAuth2 callback
    pass

