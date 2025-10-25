"""
Database security functions for MommyShops application
Consolidated security-related database operations
"""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from .models import User, Ingredient
from .session import get_db_session

logger = logging.getLogger(__name__)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email address"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_google_id(db: Session, google_id: str) -> Optional[User]:
    """Get user by Google ID"""
    return db.query(User).filter(User.google_id == google_id).first()


def get_user_by_firebase_uid(db: Session, firebase_uid: str) -> Optional[User]:
    """Get user by Firebase UID"""
    return db.query(User).filter(User.firebase_uid == firebase_uid).first()


def get_ingredient_by_name(db: Session, name: str) -> Optional[Ingredient]:
    """Get ingredient by name"""
    return db.query(Ingredient).filter(Ingredient.name == name).first()


def search_ingredients(db: Session, query: str, limit: int = 10) -> List[Ingredient]:
    """Search ingredients by name"""
    return db.query(Ingredient).filter(
        Ingredient.name.ilike(f"%{query}%")
    ).limit(limit).all()


def get_all_ingredients(db: Session, limit: int = 1000) -> List[Ingredient]:
    """Get all ingredients with limit"""
    return db.query(Ingredient).limit(limit).all()


def normalize_ingredient_name(name: str) -> str:
    """
    Normalize ingredient name for consistent matching
    """
    if not name:
        return ""
    
    # Convert to lowercase
    normalized = name.lower().strip()
    
    # Remove extra whitespace
    normalized = " ".join(normalized.split())
    
    return normalized


def canonicalize_ingredients(ingredients: List[str]) -> List[str]:
    """
    Canonicalize a list of ingredient names
    """
    if not ingredients:
        return []
    
    canonicalized = []
    for ingredient in ingredients:
        if ingredient and ingredient.strip():
            normalized = normalize_ingredient_name(ingredient)
            if normalized and normalized not in canonicalized:
                canonicalized.append(normalized)
    
    return canonicalized


def ensure_recommendation_feedback_schema(db: Session) -> bool:
    """
    Ensure the recommendation feedback table schema exists
    """
    try:
        # Check if table exists
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'recommendation_feedback'
            );
        """))
        
        table_exists = result.scalar()
        
        if not table_exists:
            logger.info("Creating recommendation_feedback table")
            # Create table if it doesn't exist
            db.execute(text("""
                CREATE TABLE recommendation_feedback (
                    id SERIAL PRIMARY KEY,
                    recommendation_id INTEGER REFERENCES recommendations(id) ON DELETE CASCADE,
                    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    feedback_type VARCHAR(32),
                    feedback_text TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """))
            db.commit()
            logger.info("recommendation_feedback table created successfully")
        else:
            logger.info("recommendation_feedback table already exists")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to ensure recommendation_feedback schema: {e}")
        db.rollback()
        return False
