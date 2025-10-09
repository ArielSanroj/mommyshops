#!/usr/bin/env python3
"""
Migrate existing SQLite user to Firebase
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, User
from unified_data_service import unified_data_service

def migrate_existing_user():
    """Migrate the existing user from SQLite to Firebase"""
    
    print("🔄 Migrating existing user to Firebase")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check if Firebase is available
    if not unified_data_service.firebase_available:
        print("❌ Firebase is not available. Please configure Firebase first.")
        print("   Run: python3 test_firebase_connection.py")
        return False
    
    # Get existing user from SQLite
    db = SessionLocal()
    try:
        user = db.query(User).first()
        if not user:
            print("❌ No users found in SQLite database")
            return False
        
        print(f"📋 Found user: {user.email}")
        print(f"   - Username: {user.username}")
        print(f"   - Auth Provider: {user.auth_provider}")
        print(f"   - Google ID: {user.google_id}")
        
        # Check if user already exists in Firebase
        firebase_uid = unified_data_service._get_firebase_user_uid(user.email)
        if firebase_uid:
            print(f"✅ User already exists in Firebase: {firebase_uid}")
            # Update SQLite user with Firebase UID for future reference
            user.firebase_uid = firebase_uid
            db.commit()
            print("✅ SQLite user updated with Firebase UID")
            return True
        
        # Create user directly in Firebase (not through unified service to avoid SQLite conflict)
        print("🔄 Creating user in Firebase...")
        try:
            from firebase_config import get_firebase_auth, get_firestore_client
            firebase_auth = get_firebase_auth()
            firestore_db = get_firestore_client()
            
            # Create user in Firebase Auth
            user_record = firebase_auth.create_user(
                email=user.email,
                display_name=user.google_name or user.username
            )
            
            # Create user profile in Firestore
            profile_data = {
                'uid': user_record.uid,
                'email': user.email,
                'username': user.username,
                'google_id': user.google_id,
                'google_name': user.google_name,
                'google_picture': user.google_picture,
                'auth_provider': 'google',
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
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            firestore_db.collection('users').document(user_record.uid).set(profile_data)
            
            # Update SQLite user with Firebase UID for future reference
            user.firebase_uid = user_record.uid
            db.commit()
            
            print(f"✅ User successfully migrated to Firebase!")
            print(f"   - SQLite ID: {user.id}")
            print(f"   - Firebase UID: {user_record.uid}")
            print("✅ SQLite user updated with Firebase UID")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to create user in Firebase: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        return False
    finally:
        db.close()

def verify_migration():
    """Verify that the migration was successful"""
    
    print("\n🔍 Verifying migration...")
    print("-" * 30)
    
    # Check SQLite
    db = SessionLocal()
    try:
        user = db.query(User).first()
        if user and user.firebase_uid:
            print(f"✅ SQLite user has Firebase UID: {user.firebase_uid}")
        else:
            print("❌ SQLite user missing Firebase UID")
            return False
    finally:
        db.close()
    
    # Check Firebase
    if unified_data_service.firebase_available:
        try:
            from firebase_config import get_firestore_client
            db = get_firestore_client()
            
            # Get user from Firestore
            user_doc = db.collection('users').document(user.firebase_uid).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                print(f"✅ Firebase user found: {user_data.get('email')}")
                print(f"   - Username: {user_data.get('username')}")
                print(f"   - Auth Provider: {user_data.get('auth_provider')}")
                return True
            else:
                print("❌ Firebase user not found")
                return False
        except Exception as e:
            print(f"❌ Error checking Firebase: {e}")
            return False
    else:
        print("❌ Firebase not available for verification")
        return False

if __name__ == "__main__":
    print("🚀 MommyShops User Migration Tool")
    print("=" * 50)
    
    # Test Firebase connection first
    print("1. Testing Firebase connection...")
    if not unified_data_service.firebase_available:
        print("❌ Firebase not available. Please configure Firebase first.")
        print("   See: FIREBASE_SETUP_COMPLETE.md")
        sys.exit(1)
    print("✅ Firebase connection OK")
    
    # Migrate user
    print("\n2. Migrating user...")
    if migrate_existing_user():
        print("✅ Migration completed successfully!")
        
        # Verify migration
        if verify_migration():
            print("\n🎉 Migration verification successful!")
            print("The user is now available in both SQLite and Firebase.")
        else:
            print("\n⚠️  Migration completed but verification failed.")
            print("Please check the logs for details.")
    else:
        print("❌ Migration failed!")
        sys.exit(1)