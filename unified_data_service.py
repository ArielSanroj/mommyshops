"""
Unified Data Service for MommyShops
Handles dual write to both SQLite and Firebase for data consistency
"""

import os
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Import database modules
from database import SessionLocal, User, Routine, Recommendation, engine, Base
from firebase_config import (
    initialize_firebase, is_firebase_available, 
    create_user as firebase_create_user,
    update_user_profile as firebase_update_user_profile,
    save_analysis_result as firebase_save_analysis_result,
    get_firestore_client
)
from firebase_admin import firestore

load_dotenv()
logger = logging.getLogger(__name__)

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
            db = SessionLocal()
            user = User(
                username=user_data.get('username'),
                email=user_data.get('email'),
                google_id=user_data.get('google_id'),
                google_name=user_data.get('google_name'),
                google_picture=user_data.get('google_picture'),
                auth_provider=user_data.get('auth_provider', 'local')
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            sqlite_user_id = str(user.id)
            logger.info(f"User created in SQLite: {user.id}")
        except Exception as e:
            logger.error(f"Failed to create user in SQLite: {e}")
            return False, None, None
        finally:
            db.close()
        
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
                    logger.info(f"User created in Firebase: {firebase_uid}")
                else:
                    logger.warning("Failed to create user in Firebase")
                    
            except Exception as e:
                logger.error(f"Failed to create user in Firebase: {e}")
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
            db = SessionLocal()
            user = db.query(User).filter(User.id == int(user_id)).first()
            if user:
                # Update user fields
                for key, value in profile_data.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                
                user.updated_at = datetime.utcnow()
                db.commit()
                sqlite_success = True
                logger.info(f"User profile updated in SQLite: {user_id}")
            else:
                logger.error(f"User not found in SQLite: {user_id}")
        except Exception as e:
            logger.error(f"Failed to update user profile in SQLite: {e}")
        finally:
            db.close()
        
        # Update Firebase (if available and UID provided)
        if self.firebase_available and firebase_uid:
            try:
                firebase_success = firebase_update_user_profile(firebase_uid, profile_data)
                if firebase_success:
                    logger.info(f"User profile updated in Firebase: {firebase_uid}")
                else:
                    logger.warning("Failed to update user profile in Firebase")
            except Exception as e:
                logger.error(f"Failed to update user profile in Firebase: {e}")
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
            logger.info(f"Analysis result for user {user_id}: {analysis_data.get('product_name', 'Unknown')}")
            sqlite_success = True
        except Exception as e:
            logger.error(f"Failed to save analysis result in SQLite: {e}")
        
        # Save to Firebase (if available and UID provided)
        if self.firebase_available and firebase_uid:
            try:
                firebase_success = firebase_save_analysis_result(firebase_uid, analysis_data)
                if firebase_success:
                    logger.info(f"Analysis result saved in Firebase: {firebase_uid}")
                else:
                    logger.warning("Failed to save analysis result in Firebase")
            except Exception as e:
                logger.error(f"Failed to save analysis result in Firebase: {e}")
                firebase_success = False
        
        return sqlite_success and firebase_success
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email from SQLite (primary source)
        
        Returns:
            User data with both SQLite ID and Firebase UID
        """
        try:
            db = SessionLocal()
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
                
                # Try to get Firebase UID if available
                if self.firebase_available:
                    firebase_uid = self._get_firebase_user_uid(email)
                    if firebase_uid:
                        user_data['firebase_uid'] = firebase_uid
                
                return user_data
            return None
        except Exception as e:
            logger.error(f"Failed to get user by email: {e}")
            return None
        finally:
            db.close()
    
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