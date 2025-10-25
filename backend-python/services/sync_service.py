"""
Synchronization service for dual-write Firebase/PostgreSQL
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import asyncio

logger = logging.getLogger(__name__)

class SyncService:
    """
    Service to handle dual-write synchronization between Firebase and PostgreSQL
    with eventual consistency and error handling
    """
    
    def __init__(self):
        self.sync_queue = asyncio.Queue()
        self.retry_attempts = 3
        self.retry_delay = 2  # seconds
    
    async def sync_user_create(
        self, 
        user_data: Dict[str, Any],
        db: Session,
        firebase_client: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Synchronize user creation between PostgreSQL and Firebase
        
        Strategy: PostgreSQL first, then Firebase (with retry)
        """
        pg_success = False
        firebase_success = False
        errors = []
        
        try:
            # 1. Write to PostgreSQL (primary source of truth)
            from ..core.database import User
            
            db_user = User(
                email=user_data.get("email"),
                hashed_password=user_data.get("hashed_password"),
                full_name=user_data.get("full_name"),
                profile_data=user_data.get("profile_data", {})
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            pg_success = True
            logger.info(f"User created in PostgreSQL: {db_user.id}")
            
            # 2. Write to Firebase (with retry logic)
            if firebase_client:
                for attempt in range(self.retry_attempts):
                    try:
                        firebase_user = firebase_client.create_user(
                            email=user_data.get("email"),
                            password=user_data.get("password"),  # Firebase needs plain password
                            display_name=user_data.get("full_name")
                        )
                        
                        # Store PostgreSQL ID in Firebase custom claims
                        firebase_client.set_custom_user_claims(
                            firebase_user.uid,
                            {"pg_user_id": str(db_user.id)}
                        )
                        
                        firebase_success = True
                        logger.info(f"User created in Firebase: {firebase_user.uid}")
                        break
                        
                    except Exception as fb_error:
                        logger.error(f"Firebase sync attempt {attempt + 1} failed: {fb_error}")
                        errors.append(f"Firebase error: {str(fb_error)}")
                        
                        if attempt < self.retry_attempts - 1:
                            await asyncio.sleep(self.retry_delay)
                        else:
                            # Queue for background retry
                            await self.queue_sync_retry({
                                "operation": "create_user",
                                "pg_user_id": db_user.id,
                                "user_data": user_data
                            })
            
            return {
                "success": pg_success,
                "user_id": db_user.id,
                "firebase_synced": firebase_success,
                "errors": errors if errors else None
            }
            
        except SQLAlchemyError as db_error:
            logger.error(f"PostgreSQL error during user creation: {db_error}")
            db.rollback()
            raise Exception(f"Database error: {str(db_error)}")
        
        except Exception as e:
            logger.error(f"Unexpected error during user sync: {e}")
            if pg_success:
                db.rollback()
            raise
    
    async def sync_user_update(
        self,
        user_id: int,
        update_data: Dict[str, Any],
        db: Session,
        firebase_client: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Synchronize user updates between PostgreSQL and Firebase
        """
        pg_success = False
        firebase_success = False
        errors = []
        
        try:
            # 1. Update PostgreSQL
            from ..core.database import User
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise Exception(f"User {user_id} not found in PostgreSQL")
            
            for key, value in update_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            db.commit()
            db.refresh(user)
            pg_success = True
            logger.info(f"User updated in PostgreSQL: {user_id}")
            
            # 2. Update Firebase (if available)
            if firebase_client and hasattr(user, 'firebase_uid') and user.firebase_uid:
                for attempt in range(self.retry_attempts):
                    try:
                        firebase_client.update_user(
                            user.firebase_uid,
                            display_name=update_data.get("full_name"),
                            email=update_data.get("email")
                        )
                        firebase_success = True
                        logger.info(f"User updated in Firebase: {user.firebase_uid}")
                        break
                    except Exception as fb_error:
                        logger.error(f"Firebase update attempt {attempt + 1} failed: {fb_error}")
                        errors.append(f"Firebase error: {str(fb_error)}")
                        
                        if attempt < self.retry_attempts - 1:
                            await asyncio.sleep(self.retry_delay)
            
            return {
                "success": pg_success,
                "firebase_synced": firebase_success,
                "errors": errors if errors else None
            }
            
        except SQLAlchemyError as db_error:
            logger.error(f"PostgreSQL error during user update: {db_error}")
            db.rollback()
            raise Exception(f"Database error: {str(db_error)}")
    
    async def sync_user_delete(
        self,
        user_id: int,
        db: Session,
        firebase_client: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Synchronize user deletion between PostgreSQL and Firebase
        """
        pg_success = False
        firebase_success = False
        errors = []
        
        try:
            # 1. Get Firebase UID before deletion
            from ..core.database import User
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise Exception(f"User {user_id} not found in PostgreSQL")
            
            firebase_uid = getattr(user, 'firebase_uid', None)
            
            # 2. Soft delete in PostgreSQL (recommended for audit trail)
            user.is_active = False
            user.deleted_at = asyncio.get_event_loop().time()
            db.commit()
            pg_success = True
            logger.info(f"User soft-deleted in PostgreSQL: {user_id}")
            
            # 3. Delete from Firebase
            if firebase_client and firebase_uid:
                for attempt in range(self.retry_attempts):
                    try:
                        firebase_client.delete_user(firebase_uid)
                        firebase_success = True
                        logger.info(f"User deleted from Firebase: {firebase_uid}")
                        break
                    except Exception as fb_error:
                        logger.error(f"Firebase delete attempt {attempt + 1} failed: {fb_error}")
                        errors.append(f"Firebase error: {str(fb_error)}")
                        
                        if attempt < self.retry_attempts - 1:
                            await asyncio.sleep(self.retry_delay)
            
            return {
                "success": pg_success,
                "firebase_synced": firebase_success,
                "errors": errors if errors else None
            }
            
        except SQLAlchemyError as db_error:
            logger.error(f"PostgreSQL error during user deletion: {db_error}")
            db.rollback()
            raise Exception(f"Database error: {str(db_error)}")
    
    async def queue_sync_retry(self, sync_data: Dict[str, Any]):
        """
        Queue failed sync operations for background retry
        """
        await self.sync_queue.put(sync_data)
        logger.info(f"Queued sync retry: {sync_data['operation']}")
    
    async def process_sync_queue(self):
        """
        Background task to process queued sync operations
        """
        while True:
            try:
                sync_data = await self.sync_queue.get()
                logger.info(f"Processing queued sync: {sync_data}")
                
                # Process based on operation type
                # This would be implemented based on specific requirements
                
                self.sync_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error processing sync queue: {e}")
                await asyncio.sleep(5)  # Wait before retrying

# Global sync service instance
_sync_service: Optional[SyncService] = None

def get_sync_service() -> SyncService:
    """
    Get or create sync service instance
    """
    global _sync_service
    if _sync_service is None:
        _sync_service = SyncService()
    return _sync_service

