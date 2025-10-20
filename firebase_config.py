"""
Firebase Configuration for MommyShops
Handles Firebase Admin SDK initialization and Firestore client setup
"""

import os
import json
import logging
from typing import Optional
from firebase_admin import credentials, initialize_app, auth, firestore
from firebase_admin.exceptions import FirebaseError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Global variables for Firebase services
_firebase_app = None
_firestore_client = None

def get_firebase_credentials() -> Optional[credentials.Certificate]:
    """Get Firebase credentials from environment variables or service account file."""
    try:
        # Option 1: JSON credentials as environment variable (for Railway)
        firebase_credentials_json = os.getenv("FIREBASE_CREDENTIALS")
        if firebase_credentials_json:
            try:
                cred_dict = json.loads(firebase_credentials_json)
                logger.info("Using Firebase credentials from environment variable")
                return credentials.Certificate(cred_dict)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in FIREBASE_CREDENTIALS: {e}")
                return None
        
        # Option 2: Service account file path (for local development)
        service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        if service_account_path and os.path.exists(service_account_path):
            logger.info(f"Using Firebase service account file: {service_account_path}")
            return credentials.Certificate(service_account_path)
        
        # Option 3: Default service account file (for local development)
        default_service_account = "firebase-service-account.json"
        if os.path.exists(default_service_account):
            logger.info(f"Using default Firebase service account file: {default_service_account}")
            return credentials.Certificate(default_service_account)
        
        # Option 4: Google Application Default Credentials
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            logger.info("Using Google Application Default Credentials")
            return credentials.ApplicationDefault()
        
        logger.warning("No Firebase credentials found. Firebase features will be disabled.")
        logger.warning("To enable Firebase, set FIREBASE_CREDENTIALS environment variable or create firebase-service-account.json")
        return None
        
    except Exception as e:
        logger.error(f"Error getting Firebase credentials: {e}")
        return None

def initialize_firebase() -> bool:
    """Initialize Firebase Admin SDK."""
    global _firebase_app, _firestore_client
    
    if _firebase_app is not None:
        logger.info("Firebase already initialized")
        return True
    
    try:
        cred = get_firebase_credentials()
        if not cred:
            logger.warning("Firebase credentials not available. Firebase features will be disabled.")
            return False
        
        _firebase_app = initialize_app(cred)
        _firestore_client = firestore.client()
        
        logger.info("Firebase Admin SDK initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        _firebase_app = None
        _firestore_client = None
        return False

def get_firestore_client():
    """Get Firestore client instance."""
    global _firestore_client
    
    if _firestore_client is None:
        if not initialize_firebase():
            raise RuntimeError("Firebase not initialized. Check your credentials.")
    
    return _firestore_client

def get_firebase_auth():
    """Get Firebase Auth instance."""
    if _firebase_app is None:
        if not initialize_firebase():
            raise RuntimeError("Firebase not initialized. Check your credentials.")
    
    return auth

def is_firebase_available() -> bool:
    """Check if Firebase is properly initialized and available."""
    return _firebase_app is not None and _firestore_client is not None

# User Management Functions
def create_user(user_data: dict) -> bool:
    """
    Create a new user in Firebase Auth and Firestore.
    
    Args:
        user_data: Dictionary containing user information (username, email, password)
        
    Returns:
        bool: True if user created successfully, False otherwise
    """
    try:
        if not is_firebase_available():
            logger.error("Firebase not available")
            return False
        
        firebase_auth = get_firebase_auth()
        firestore_db = get_firestore_client()
        
        email = user_data.get('email', '').strip()
        password = user_data.get('password', '')
        username = user_data.get('username', '').strip()
        
        if not email or not password:
            logger.error("Email and password are required")
            return False
        
        # Create user in Firebase Auth
        user_record = firebase_auth.create_user(
            email=email,
            password=password,
            display_name=username
        )
        
        # Save user profile to Firestore
        user_profile = {
            'uid': user_record.uid,
            'email': email,
            'username': username,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        }
        
        firestore_db.collection('users').document(user_record.uid).set(user_profile)
        
        logger.info(f"User created successfully: {email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        return False

def verify_user_credentials(email: str, password: str) -> dict:
    """
    Verify user credentials and return user information.
    
    Args:
        email: User's email address
        password: User's password
        
    Returns:
        dict: User information if credentials are valid, None otherwise
    """
    try:
        if not is_firebase_available():
            logger.error("Firebase not available")
            return None
        
        firebase_auth = get_firebase_auth()
        firestore_db = get_firestore_client()
        
        # Get user by email
        user_record = firebase_auth.get_user_by_email(email)
        
        # Get user profile from Firestore
        user_doc = firestore_db.collection('users').document(user_record.uid).get()
        
        if user_doc.exists:
            user_data = user_doc.to_dict()
            return {
                'user_id': user_record.uid,
                'email': user_record.email,
                'username': user_data.get('username', ''),
                'access_token': 'firebase_token'  # Placeholder for compatibility
            }
        else:
            logger.error(f"User profile not found in Firestore: {email}")
            return None
            
    except firebase_auth.UserNotFoundError:
        logger.error(f"User not found: {email}")
        return None
    except Exception as e:
        logger.error(f"Failed to verify credentials: {e}")
        return None

def update_user_profile(user_id: str, profile_data: dict) -> bool:
    """
    Update user profile in Firestore.
    
    Args:
        user_id: User's Firebase UID
        profile_data: Dictionary containing profile information to update
        
    Returns:
        bool: True if profile updated successfully, False otherwise
    """
    try:
        if not is_firebase_available():
            logger.error("Firebase not available")
            return False
        
        firestore_db = get_firestore_client()
        
        # Add updated timestamp
        profile_data['updated_at'] = firestore.SERVER_TIMESTAMP
        
        # Update user profile in Firestore
        firestore_db.collection('users').document(user_id).update(profile_data)
        
        logger.info(f"User profile updated successfully: {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update user profile: {e}")
        return False

def save_analysis_result(user_id: str, analysis_data: dict) -> bool:
    """
    Save analysis result to Firestore.
    
    Args:
        user_id: User's Firebase UID
        analysis_data: Dictionary containing analysis results
        
    Returns:
        bool: True if analysis saved successfully, False otherwise
    """
    try:
        if not is_firebase_available():
            logger.error("Firebase not available")
            return False
        
        firestore_db = get_firestore_client()
        
        # Add metadata
        analysis_data['user_id'] = user_id
        analysis_data['created_at'] = firestore.SERVER_TIMESTAMP
        
        # Save analysis to Firestore
        firestore_db.collection('analysis_results').add(analysis_data)
        
        logger.info(f"Analysis result saved successfully for user: {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save analysis result: {e}")
        return False

def get_user_analysis_history(user_id: str) -> list:
    """
    Get user's analysis history from Firestore.
    
    Args:
        user_id: User's Firebase UID
        
    Returns:
        list: List of analysis results
    """
    try:
        if not is_firebase_available():
            logger.error("Firebase not available")
            return []
        
        firestore_db = get_firestore_client()
        
        # Query analysis results for the user
        query = firestore_db.collection('analysis_results').where('user_id', '==', user_id).order_by('created_at', direction=firestore.Query.DESCENDING)
        
        results = []
        for doc in query.stream():
            analysis_data = doc.to_dict()
            analysis_data['id'] = doc.id
            results.append(analysis_data)
        
        logger.info(f"Retrieved {len(results)} analysis results for user: {user_id}")
        return results
        
    except Exception as e:
        logger.error(f"Failed to get user analysis history: {e}")
        return []

# Initialize Firebase on module import
if not initialize_firebase():
    logger.warning("Firebase initialization failed. Some features may not be available.")