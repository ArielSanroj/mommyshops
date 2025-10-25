"""
Database session management for MommyShops application
Consolidated session handling from main database.py
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev_sqlite.db")

# Create engine
try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("Database connection configured successfully")
except Exception as e:
    logger.error("Database connection failed: %s", e)
    engine = None
    SessionLocal = None


def get_db() -> Generator[Session, None, None]:
    """
    Database dependency for FastAPI
    Provides a database session that is automatically closed
    """
    if SessionLocal is None:
        raise Exception("Database not configured")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Get a database session for direct use
    Caller is responsible for closing the session
    """
    if SessionLocal is None:
        raise Exception("Database not configured")
    
    return SessionLocal()
