"""
Unified Data Service for MommyShops
Handles dual write to both SQLite and Firebase for data consistency
"""

import json
import logging
import os
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# Import database modules
from database import SessionLocal, User
from firebase_config import (
    is_firebase_available,
    create_user as firebase_create_user,
    update_user_profile as firebase_update_user_profile,
    save_analysis_result as firebase_save_analysis_result,
    get_firestore_client,
)
from firebase_admin import firestore

# Import Ollama integration
try:
    from ollama_integration import (
        ollama_integration,
        analyze_ingredient_safety_with_ollama,
        enhance_ocr_text_with_ollama
    )
    from api_utils_production import enhance_ingredient_analysis_with_ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("Ollama integration not available")

load_dotenv()

_STANDARD_LOG_KEYS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
}


class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # pragma: no cover - logging helper
        payload = {
            "timestamp": self.formatTime(record, self.datefmt) if self.datefmt else self.formatTime(record),
            "logger": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _STANDARD_LOG_KEYS and not key.startswith("_")
        }
        if extras:
            payload["context"] = extras
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


logger = logging.getLogger("mommyshops.unified_data_service")
if not logger.handlers:
    backend_log_path = Path(os.getenv("BACKEND_LOG_PATH", Path(__file__).resolve().parent / "backend.log"))
    try:
        backend_log_path.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(backend_log_path)
        handler.setFormatter(_JSONFormatter())
        logger.addHandler(handler)
    except Exception as log_exc:  # pragma: no cover - logging fallback
        logging.getLogger(__name__).warning("Failed to configure unified data service logger", exc_info=log_exc)
logger.setLevel(logging.INFO)
logger.propagate = False


@contextmanager
def managed_session(commit: bool = False):
    if SessionLocal is None:
        raise RuntimeError("Database session factory not configured")
    session = SessionLocal()
    try:
        yield session
        if commit:
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class UnifiedDataService:
    """Service for managing data across SQLite and Firebase"""
    
    def __init__(self):
        self.firebase_available = is_firebase_available()
        if not self.firebase_available:
            logger.warning("Firebase not available - data will only be saved to SQLite")
    
    def create_user(self, user_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Create user in both SQLite and Firebase
        
        Returns:
            (success, sqlite_user_id, firebase_uid)
        """
        sqlite_user_id = None
        firebase_uid = None
        
        # Create user in SQLite
        try:
            with managed_session(commit=True) as db:
                user = User(
                    username=user_data.get('username'),
                    email=user_data.get('email'),
                    google_id=user_data.get('google_id'),
                    google_name=user_data.get('google_name'),
                    google_picture=user_data.get('google_picture'),
                    auth_provider=user_data.get('auth_provider', 'local')
                )
                db.add(user)
                db.flush()
                sqlite_user_id = str(user.id)
                logger.info(
                    "User created in SQLite",
                    extra={"user_id": user.id, "email": user.email},
                )
        except Exception as exc:
            logger.exception(
                "Failed to create user in SQLite",
                extra={"email": user_data.get('email')},
            )
            return False, None, None
        
        # Create user in Firebase (if available)
        if self.firebase_available:
            try:
                firebase_user_data = {
                    'email': user_data.get('email'),
                    'password': user_data.get('password', 'TempPassword123!'),
                    'username': user_data.get('username')
                }
                
                # For Google OAuth users, we need to create a Firebase user differently
                if user_data.get('auth_provider') == 'google':
                    # Create Firebase user with Google OAuth
                    firebase_uid = self._create_firebase_google_user(user_data)
                else:
                    # Create Firebase user with email/password
                    if firebase_create_user(firebase_user_data):
                        # Get the Firebase UID
                        firebase_uid = self._get_firebase_user_uid(user_data.get('email'))
                
                if firebase_uid:
                    logger.info(
                        "User created in Firebase",
                        extra={"firebase_uid": firebase_uid, "email": user_data.get('email')},
                    )
                else:
                    logger.warning(
                        "Failed to create user in Firebase",
                        extra={"email": user_data.get('email')},
                    )

            except Exception as exc:
                logger.exception(
                    "Failed to create user in Firebase",
                    extra={"email": user_data.get('email')},
                )
                # Don't fail the entire operation if Firebase fails
        
        return True, sqlite_user_id, firebase_uid
    
    def update_user_profile(self, user_id: str, profile_data: Dict[str, Any], 
                          firebase_uid: Optional[str] = None) -> bool:
        """
        Update user profile in both SQLite and Firebase
        
        Args:
            user_id: SQLite user ID
            profile_data: Profile data to update
            firebase_uid: Firebase UID (if available)
        """
        sqlite_success = False
        firebase_success = True  # Default to True if Firebase not available
        
        # Update SQLite
        try:
            with managed_session(commit=True) as db:
                user = db.query(User).filter(User.id == int(user_id)).first()
                if user:
                    for key, value in profile_data.items():
                        if hasattr(user, key):
                            setattr(user, key, value)

                    user.updated_at = datetime.utcnow()
                    sqlite_success = True
                    logger.info(
                        "User profile updated in SQLite",
                        extra={"user_id": user_id},
                    )
                else:
                    logger.error(
                        "User not found in SQLite",
                        extra={"user_id": user_id},
                    )
        except Exception as exc:
            logger.exception(
                "Failed to update user profile in SQLite",
                extra={"user_id": user_id},
            )
        
        # Update Firebase (if available and UID provided)
        if self.firebase_available and firebase_uid:
            try:
                firebase_success = firebase_update_user_profile(firebase_uid, profile_data)
                if firebase_success:
                    logger.info(
                        "User profile updated in Firebase",
                        extra={"firebase_uid": firebase_uid},
                    )
                else:
                    logger.warning(
                        "Failed to update user profile in Firebase",
                        extra={"firebase_uid": firebase_uid},
                    )
            except Exception as exc:
                logger.exception(
                    "Failed to update user profile in Firebase",
                    extra={"firebase_uid": firebase_uid},
                )
                firebase_success = False
        
        return sqlite_success and firebase_success
    
    def save_analysis_result(self, user_id: str, analysis_data: Dict[str, Any],
                           firebase_uid: Optional[str] = None) -> bool:
        """
        Save analysis result to both SQLite and Firebase
        
        Args:
            user_id: SQLite user ID
            analysis_data: Analysis data to save
            firebase_uid: Firebase UID (if available)
        """
        sqlite_success = False
        firebase_success = True  # Default to True if Firebase not available
        
        # Save to SQLite (if you have an analysis table)
        # For now, we'll just log it
        try:
            logger.info(
                "Analysis result logged",
                extra={
                    "user_id": user_id,
                    "product_name": analysis_data.get('product_name', 'Unknown'),
                },
            )
            sqlite_success = True
        except Exception:
            logger.exception(
                "Failed to record analysis result for SQLite",
                extra={"user_id": user_id},
            )
        
        # Save to Firebase (if available and UID provided)
        if self.firebase_available and firebase_uid:
            try:
                firebase_success = firebase_save_analysis_result(firebase_uid, analysis_data)
                if firebase_success:
                    logger.info(
                        "Analysis result saved in Firebase",
                        extra={"firebase_uid": firebase_uid},
                    )
                else:
                    logger.warning(
                        "Failed to save analysis result in Firebase",
                        extra={"firebase_uid": firebase_uid},
                    )
            except Exception:
                logger.exception(
                    "Failed to persist analysis in Firebase",
                    extra={"firebase_uid": firebase_uid},
                )
                firebase_success = False
        
        return sqlite_success and firebase_success
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email from SQLite (primary source)
        
        Returns:
            User data with both SQLite ID and Firebase UID
        """
        try:
            with managed_session() as db:
                user = db.query(User).filter(User.email == email).first()
                if user:
                    user_data = {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'google_id': user.google_id,
                        'google_name': user.google_name,
                        'google_picture': user.google_picture,
                        'auth_provider': user.auth_provider,
                        'skin_face': user.skin_face,
                        'hair_type': user.hair_type,
                        'goals_face': user.goals_face,
                        'climate': user.climate,
                        'skin_body': user.skin_body,
                        'goals_body': user.goals_body,
                        'hair_porosity': user.hair_porosity,
                        'goals_hair': user.goals_hair,
                        'hair_thickness_scalp': user.hair_thickness_scalp,
                        'conditions': user.conditions,
                        'created_at': user.created_at,
                        'updated_at': user.updated_at
                    }

                    if self.firebase_available:
                        firebase_uid = self._get_firebase_user_uid(email)
                        if firebase_uid:
                            user_data['firebase_uid'] = firebase_uid

                    logger.info(
                        "User retrieved from SQLite",
                        extra={"user_id": user.id, "email": email},
                    )
                    return user_data
                return None
        except Exception:
            logger.exception(
                "Failed to get user by email",
                extra={"email": email},
            )
            return None
    
    def _create_firebase_google_user(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Create Firebase user for Google OAuth"""
        try:
            from firebase_config import get_firebase_auth
            firebase_auth = get_firebase_auth()
            
            # Create user in Firebase Auth
            user_record = firebase_auth.create_user(
                email=user_data.get('email'),
                display_name=user_data.get('google_name') or user_data.get('username')
            )
            
            # Create user profile in Firestore
            profile_data = {
                'uid': user_record.uid,
                'email': user_data.get('email'),
                'username': user_data.get('username'),
                'google_id': user_data.get('google_id'),
                'google_name': user_data.get('google_name'),
                'google_picture': user_data.get('google_picture'),
                'auth_provider': 'google',
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            db = get_firestore_client()
            db.collection('users').document(user_record.uid).set(profile_data)
            
            return user_record.uid
            
        except Exception as e:
            logger.error(f"Failed to create Firebase Google user: {e}")
            return None
    
    def _get_firebase_user_uid(self, email: str) -> Optional[str]:
        """Get Firebase UID by email"""
        try:
            from firebase_config import get_firebase_auth
            firebase_auth = get_firebase_auth()
            user_record = firebase_auth.get_user_by_email(email)
            return user_record.uid
        except Exception as e:
            logger.debug(f"Firebase user not found for email {email}: {e}")
            return None
    
    async def save_analysis_with_ollama_enhancement(self, user_id: str, analysis_data: Dict[str, Any], 
                                                   skin_type: str = "normal") -> Tuple[bool, Optional[str]]:
        """
        Save analysis result with Ollama enhancement for better insights
        
        Args:
            user_id: User ID
            analysis_data: Analysis data to save
            skin_type: User's skin type for personalized analysis
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Enhance analysis with Ollama if available
            enhanced_data = analysis_data.copy()
            
            if OLLAMA_AVAILABLE and ollama_integration.is_available():
                try:
                    # Extract ingredients for Ollama analysis
                    ingredients = []
                    if 'ingredients' in analysis_data:
                        if isinstance(analysis_data['ingredients'], list):
                            ingredients = analysis_data['ingredients']
                        elif isinstance(analysis_data['ingredients'], str):
                            ingredients = [analysis_data['ingredients']]
                    
                    if ingredients:
                        # Get Ollama safety analysis
                        ollama_result = await analyze_ingredient_safety_with_ollama(ingredients, skin_type)
                        
                        if ollama_result.success and ollama_result.content:
                            enhanced_data['ollama_analysis'] = {
                                'content': ollama_result.content,
                                'model': ollama_result.model,
                                'skin_type': skin_type,
                                'timestamp': datetime.now().isoformat()
                            }
                            
                            # Try to extract safety score
                            safety_score = self._extract_safety_score(ollama_result.content)
                            if safety_score:
                                enhanced_data['ollama_safety_score'] = safety_score
                            
                            logger.info(f"Ollama analysis added to analysis data for user {user_id}")
                        else:
                            logger.warning(f"Ollama analysis failed: {ollama_result.error}")
                    else:
                        logger.warning("No ingredients found for Ollama analysis")
                        
                except Exception as e:
                    logger.error(f"Error enhancing analysis with Ollama: {e}")
                    # Continue with original data if Ollama fails
            
            # Save the enhanced analysis
            return await self.save_analysis_result(user_id, enhanced_data)
            
        except Exception as e:
            logger.error(f"Error saving analysis with Ollama enhancement: {e}")
            return False, str(e)
    
    def _extract_safety_score(self, content: str) -> Optional[float]:
        """Extract safety score from Ollama response content"""
        try:
            import re
            
            # Look for patterns like "8/10", "Score: 8", "Safety Score: 8.5", etc.
            patterns = [
                r'(\d+(?:\.\d+)?)\s*/\s*10',  # X/10 format
                r'(?:safety\s+)?score\s*:?\s*(\d+(?:\.\d+)?)',  # Score: X format
                r'(\d+(?:\.\d+)?)\s+out\s+of\s+10'  # X out of 10 format
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    return float(match.group(1))
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting safety score: {e}")
            return None
    
    async def get_enhanced_ingredient_analysis(self, ingredients: List[str], skin_type: str = "normal") -> Dict[str, Any]:
        """
        Get enhanced ingredient analysis combining traditional APIs with Ollama
        
        Args:
            ingredients: List of ingredient names
            skin_type: User's skin type
            
        Returns:
            Enhanced analysis results
        """
        try:
            # Get basic analysis data
            analysis_data = {
                'ingredients': ingredients,
                'skin_type': skin_type,
                'timestamp': datetime.now().isoformat()
            }
            
            # Enhance with Ollama if available
            if OLLAMA_AVAILABLE and ollama_integration.is_available():
                try:
                    ollama_result = await analyze_ingredient_safety_with_ollama(ingredients, skin_type)
                    
                    if ollama_result.success and ollama_result.content:
                        analysis_data['ollama_analysis'] = {
                            'content': ollama_result.content,
                            'model': ollama_result.model,
                            'skin_type': skin_type,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        # Extract safety score
                        safety_score = self._extract_safety_score(ollama_result.content)
                        if safety_score:
                            analysis_data['ollama_safety_score'] = safety_score
                        
                        logger.info(f"Enhanced analysis completed for {len(ingredients)} ingredients")
                    else:
                        logger.warning(f"Ollama analysis failed: {ollama_result.error}")
                        
                except Exception as e:
                    logger.error(f"Error in Ollama analysis: {e}")
            
            return analysis_data
            
        except Exception as e:
            logger.error(f"Error in enhanced ingredient analysis: {e}")
            return {
                'error': str(e),
                'ingredients': ingredients,
                'skin_type': skin_type
            }

# Global instance
unified_data_service = UnifiedDataService()

# Convenience functions
def create_user_unified(user_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
    """Create user in both databases"""
    return unified_data_service.create_user(user_data)

def update_user_profile_unified(user_id: str, profile_data: Dict[str, Any], 
                              firebase_uid: Optional[str] = None) -> bool:
    """Update user profile in both databases"""
    return unified_data_service.update_user_profile(user_id, profile_data, firebase_uid)

def save_analysis_result_unified(user_id: str, analysis_data: Dict[str, Any],
                               firebase_uid: Optional[str] = None) -> bool:
    """Save analysis result in both databases"""
    return unified_data_service.save_analysis_result(user_id, analysis_data, firebase_uid)

def get_user_by_email_unified(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email from primary source (SQLite)"""
    return unified_data_service.get_user_by_email(email)

async def save_analysis_with_ollama_unified(user_id: str, analysis_data: Dict[str, Any], 
                                          skin_type: str = "normal") -> Tuple[bool, Optional[str]]:
    """Save analysis with Ollama enhancement"""
    return await unified_data_service.save_analysis_with_ollama_enhancement(user_id, analysis_data, skin_type)

async def get_enhanced_ingredient_analysis_unified(ingredients: List[str], skin_type: str = "normal") -> Dict[str, Any]:
    """Get enhanced ingredient analysis with Ollama"""
    return await unified_data_service.get_enhanced_ingredient_analysis(ingredients, skin_type)