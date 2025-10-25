#!/usr/bin/env python3
"""
Migration Script: SQLite to Firebase for MommyShops
Migrates user data from SQLite database to Firebase Auth and Firestore
"""

import os
import sys
import json
import sqlite3
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from firebase_config import initialize_firebase, get_firebase_auth, get_firestore_client, is_firebase_available
from firebase_admin import firestore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def connect_sqlite_db(db_path: str) -> sqlite3.Connection:
    """Connect to SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        logger.info(f"Connected to SQLite database: {db_path}")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to SQLite database: {e}")
        raise

def get_sqlite_users(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Get all users from SQLite database."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, email, hashed_password, google_id, google_name, 
                   google_picture, auth_provider, skin_face, hair_type, goals_face,
                   climate, skin_body, goals_body, hair_porosity, goals_hair,
                   hair_thickness_scalp, conditions, created_at, updated_at
            FROM users
        """)
        
        users = []
        for row in cursor.fetchall():
            user_dict = dict(row)
            users.append(user_dict)
        
        logger.info(f"Found {len(users)} users in SQLite database")
        return users
    except Exception as e:
        logger.error(f"Failed to get users from SQLite: {e}")
        raise

def convert_sqlite_user_to_firebase(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert SQLite user data to Firebase format with robust JSON validation."""
    firebase_data = {
        "uid": "",  # Will be set after Firebase Auth user creation
        "email": user_data.get("email", ""),
        "name": user_data.get("google_name") or user_data.get("username", ""),
        "created_at": firestore.SERVER_TIMESTAMP,
        "updated_at": firestore.SERVER_TIMESTAMP
    }
    
    # Add optional fields if they exist and are not None
    optional_fields = [
        "skin_face", "hair_type", "climate"
    ]
    
    for field in optional_fields:
        value = user_data.get(field)
        if value is not None and value != "":
            firebase_data[field] = value
    
    # Handle JSON fields with robust validation
    json_fields = [
        "goals_face", "skin_body", "goals_body", "hair_porosity",
        "goals_hair", "hair_thickness_scalp", "conditions"
    ]
    
    for field in json_fields:
        value = user_data.get(field)
        if value is not None:
            try:
                if isinstance(value, str):
                    # Check if string is not empty and not just whitespace
                    if value.strip():
                        parsed = json.loads(value)
                        # Validate that parsed data is a dict or list
                        if isinstance(parsed, (dict, list)):
                            firebase_data[field] = parsed
                        else:
                            logger.warning(f"JSON field {field} for user {user_data.get('email')} is not dict/list, skipping")
                            firebase_data[field] = {}
                    else:
                        firebase_data[field] = {}
                else:
                    # If it's already a dict/list, use it directly
                    if isinstance(value, (dict, list)):
                        firebase_data[field] = value
                    else:
                        logger.warning(f"Non-JSON field {field} for user {user_data.get('email')}, converting to empty dict")
                        firebase_data[field] = {}
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse JSON field {field} for user {user_data.get('email')}: {e}")
                # Set to empty dict instead of None for consistency
                firebase_data[field] = {}
    
    return firebase_data

def create_firebase_user(user_data: Dict[str, Any], firebase_auth) -> Optional[str]:
    """Create user in Firebase Auth and return UID."""
    try:
        email = user_data.get("email")
        if not email:
            logger.warning("Skipping user without email")
            return None
        
        # Check if user already exists
        try:
            existing_user = firebase_auth.get_user_by_email(email)
            logger.info(f"User {email} already exists in Firebase Auth")
            return existing_user.uid
        except firebase_auth.UserNotFoundError:
            pass  # User doesn't exist, continue with creation
        
        # Create user in Firebase Auth
        user_record = firebase_auth.create_user(
            email=email,
            password="TempPassword123!",  # Temporary password
            display_name=user_data.get("google_name") or user_data.get("username", "")
        )
        
        logger.info(f"Created Firebase Auth user: {email} (UID: {user_record.uid})")
        return user_record.uid
        
    except firebase_auth.EmailAlreadyExistsError:
        logger.warning(f"User {email} already exists in Firebase Auth")
        return None
    except Exception as e:
        logger.error(f"Failed to create Firebase user for {email}: {e}")
        return None

def save_user_to_firestore(uid: str, firebase_data: Dict[str, Any], firestore_db) -> bool:
    """Save user profile to Firestore."""
    try:
        firebase_data["uid"] = uid
        firestore_db.collection('users').document(uid).set(firebase_data)
        logger.info(f"Saved user profile to Firestore: {uid}")
        return True
    except Exception as e:
        logger.error(f"Failed to save user {uid} to Firestore: {e}")
        return False

def migrate_users(sqlite_path: str, dry_run: bool = False) -> Dict[str, int]:
    """Migrate users from SQLite to Firebase."""
    stats = {
        "total_users": 0,
        "migrated": 0,
        "skipped": 0,
        "errors": 0
    }
    
    try:
        # Initialize Firebase
        if not initialize_firebase():
            logger.error("Failed to initialize Firebase")
            return stats
        
        if not is_firebase_available():
            logger.error("Firebase is not available")
            return stats
        
        # Connect to SQLite
        conn = connect_sqlite_db(sqlite_path)
        
        # Get users from SQLite
        users = get_sqlite_users(conn)
        stats["total_users"] = len(users)
        
        if dry_run:
            logger.info("DRY RUN MODE - No data will be migrated")
            for user in users:
                logger.info(f"Would migrate user: {user.get('email')} - {user.get('username')}")
            conn.close()
            return stats
        
        # Initialize Firebase services
        firebase_auth = get_firebase_auth()
        firestore_db = get_firestore_client()
        
        # Migrate each user
        for i, user_data in enumerate(users, 1):
            try:
                email = user_data.get("email")
                username = user_data.get("username", "N/A")
                
                logger.info(f"Processing user {i}/{len(users)}: {email} ({username})")
                
                if not email:
                    logger.warning(f"Skipping user {i} without email")
                    stats["skipped"] += 1
                    continue
                
                # Convert user data to Firebase format
                firebase_data = convert_sqlite_user_to_firebase(user_data)
                
                # Create user in Firebase Auth
                uid = create_firebase_user(user_data, firebase_auth)
                if not uid:
                    logger.warning(f"Failed to create Firebase Auth user for {email}")
                    stats["skipped"] += 1
                    continue
                
                # Save user profile to Firestore
                if save_user_to_firestore(uid, firebase_data, firestore_db):
                    logger.info(f"✅ Successfully migrated user {email} (UID: {uid})")
                    stats["migrated"] += 1
                else:
                    logger.error(f"❌ Failed to save Firestore profile for {email}")
                    stats["errors"] += 1
                
            except Exception as e:
                logger.error(f"❌ Error migrating user {user_data.get('email')}: {e}")
                stats["errors"] += 1
        
        conn.close()
        logger.info(f"Migration completed. Stats: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        stats["errors"] += 1
        return stats

def main():
    """Main migration function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate SQLite users to Firebase")
    parser.add_argument(
        "--sqlite-path", 
        default="dev_sqlite.db",
        help="Path to SQLite database file (default: dev_sqlite.db)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Perform a dry run without actually migrating data"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if SQLite file exists
    if not os.path.exists(args.sqlite_path):
        logger.error(f"SQLite database not found: {args.sqlite_path}")
        sys.exit(1)
    
    logger.info("Starting SQLite to Firebase migration...")
    logger.info(f"SQLite path: {args.sqlite_path}")
    logger.info(f"Dry run: {args.dry_run}")
    
    # Run migration
    stats = migrate_users(args.sqlite_path, args.dry_run)
    
    # Print results
    print("\n" + "="*50)
    print("MIGRATION RESULTS")
    print("="*50)
    print(f"Total users found: {stats['total_users']}")
    print(f"Successfully migrated: {stats['migrated']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Errors: {stats['errors']}")
    print("="*50)
    
    if stats['errors'] > 0:
        sys.exit(1)
    else:
        logger.info("Migration completed successfully!")

if __name__ == "__main__":
    main()