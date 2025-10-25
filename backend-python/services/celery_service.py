"""
Celery service for background tasks and async processing
"""

import logging
from typing import Dict, Any, List, Optional
from celery import Celery
from celery.result import AsyncResult
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Celery configuration
celery_app = Celery(
    'mommyshops',
    broker='redis://localhost:6379/1',  # Use different Redis DB for Celery
    backend='redis://localhost:6379/1',
    include=['backend.services.celery_service']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_compression='gzip',
    result_compression='gzip',
    result_expires=3600,  # 1 hour
    task_routes={
        'backend.services.celery_service.scrape_ingredient_data': {'queue': 'scraping'},
        'backend.services.celery_service.analyze_user_routine': {'queue': 'analysis'},
        'backend.services.celery_service.send_notification': {'queue': 'notifications'},
        'backend.services.celery_service.cleanup_old_data': {'queue': 'maintenance'},
    }
)

class CeleryService:
    """
    Service for managing background tasks with Celery
    """
    
    def __init__(self):
        self.app = celery_app
    
    async def enqueue_task(self, task_name: str, *args, **kwargs) -> str:
        """
        Enqueue a background task
        
        Args:
            task_name: Name of the task function
            *args: Positional arguments for the task
            **kwargs: Keyword arguments for the task
            
        Returns:
            Task ID
        """
        try:
            result = self.app.send_task(task_name, args=args, kwargs=kwargs)
            logger.info(f"Enqueued task {task_name} with ID: {result.id}")
            return result.id
        except Exception as e:
            logger.error(f"Failed to enqueue task {task_name}: {e}")
            raise
    
    async def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """
        Get task result by ID
        
        Args:
            task_id: Task ID
            
        Returns:
            Task result and status
        """
        try:
            result = AsyncResult(task_id, app=self.app)
            
            return {
                "task_id": task_id,
                "status": result.status,
                "result": result.result if result.ready() else None,
                "ready": result.ready(),
                "successful": result.successful() if result.ready() else None,
                "failed": result.failed() if result.ready() else None
            }
        except Exception as e:
            logger.error(f"Failed to get task result {task_id}: {e}")
            return {
                "task_id": task_id,
                "status": "FAILURE",
                "error": str(e)
            }
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task
        
        Args:
            task_id: Task ID to cancel
            
        Returns:
            True if cancelled successfully
        """
        try:
            self.app.control.revoke(task_id, terminate=True)
            logger.info(f"Cancelled task: {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics
        
        Returns:
            Queue statistics
        """
        try:
            inspect = self.app.control.inspect()
            
            stats = {
                "active_tasks": inspect.active(),
                "scheduled_tasks": inspect.scheduled(),
                "reserved_tasks": inspect.reserved(),
                "queues": {
                    "scraping": 0,
                    "analysis": 0,
                    "notifications": 0,
                    "maintenance": 0
                }
            }
            
            # Get queue lengths
            for queue in stats["queues"]:
                try:
                    length = self.app.control.inspect().active()
                    if length:
                        stats["queues"][queue] = len(length.get(queue, []))
                except:
                    pass
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {"error": str(e)}


# Background task functions
@celery_app.task(bind=True, name='backend.services.celery_service.scrape_ingredient_data')
def scrape_ingredient_data(self, ingredient_name: str, sources: List[str]) -> Dict[str, Any]:
    """
    Background task to scrape ingredient data from multiple sources
    
    Args:
        ingredient_name: Name of ingredient to scrape
        sources: List of sources to scrape from
        
    Returns:
        Scraped data dictionary
    """
    try:
        logger.info(f"Starting ingredient scraping for: {ingredient_name}")
        
        # Simulate scraping from multiple sources
        scraped_data = {
            "ingredient": ingredient_name,
            "sources": {},
            "timestamp": datetime.now().isoformat(),
            "task_id": self.request.id
        }
        
        for source in sources:
            # Simulate API call delay
            import time
            time.sleep(2)
            
            scraped_data["sources"][source] = {
                "status": "success",
                "data": f"Data from {source} for {ingredient_name}",
                "scraped_at": datetime.now().isoformat()
            }
        
        logger.info(f"Completed ingredient scraping for: {ingredient_name}")
        return scraped_data
        
    except Exception as e:
        logger.error(f"Ingredient scraping failed for {ingredient_name}: {e}")
        self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, name='backend.services.celery_service.analyze_user_routine')
def analyze_user_routine(self, user_id: int, routine_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Background task to analyze user's cosmetic routine
    
    Args:
        user_id: User ID
        routine_data: User's routine data
        
    Returns:
        Analysis results
    """
    try:
        logger.info(f"Starting routine analysis for user: {user_id}")
        
        # Simulate complex analysis
        import time
        time.sleep(10)  # Simulate processing time
        
        analysis_result = {
            "user_id": user_id,
            "analysis_id": f"routine_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "recommendations": [
                "Consider switching to paraben-free products",
                "Your routine is well-balanced for sensitive skin"
            ],
            "risk_factors": [
                "High fragrance content in current products"
            ],
            "compatibility_score": 8.5,
            "analyzed_at": datetime.now().isoformat(),
            "task_id": self.request.id
        }
        
        logger.info(f"Completed routine analysis for user: {user_id}")
        return analysis_result
        
    except Exception as e:
        logger.error(f"Routine analysis failed for user {user_id}: {e}")
        self.retry(countdown=120, max_retries=2)


@celery_app.task(bind=True, name='backend.services.celery_service.send_notification')
def send_notification(self, user_id: int, notification_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Background task to send notifications
    
    Args:
        user_id: User ID
        notification_type: Type of notification
        data: Notification data
        
    Returns:
        Notification result
    """
    try:
        logger.info(f"Sending {notification_type} notification to user: {user_id}")
        
        # Simulate notification sending
        import time
        time.sleep(1)
        
        result = {
            "user_id": user_id,
            "notification_type": notification_type,
            "status": "sent",
            "sent_at": datetime.now().isoformat(),
            "task_id": self.request.id
        }
        
        logger.info(f"Notification sent to user: {user_id}")
        return result
        
    except Exception as e:
        logger.error(f"Notification failed for user {user_id}: {e}")
        self.retry(countdown=30, max_retries=3)


@celery_app.task(bind=True, name='backend.services.celery_service.cleanup_old_data')
def cleanup_old_data(self, days_old: int = 30) -> Dict[str, Any]:
    """
    Background task to cleanup old data
    
    Args:
        days_old: Number of days old data to cleanup
        
    Returns:
        Cleanup results
    """
    try:
        logger.info(f"Starting cleanup of data older than {days_old} days")
        
        # Simulate cleanup process
        import time
        time.sleep(5)
        
        cleanup_result = {
            "cleanup_date": datetime.now().isoformat(),
            "days_old": days_old,
            "items_cleaned": 150,  # Simulated
            "space_freed": "2.5GB",  # Simulated
            "task_id": self.request.id
        }
        
        logger.info(f"Cleanup completed: {cleanup_result['items_cleaned']} items")
        return cleanup_result
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        self.retry(countdown=300, max_retries=2)


# Global celery service instance
_celery_service: Optional[CeleryService] = None

def get_celery_service() -> CeleryService:
    """Get or create celery service instance"""
    global _celery_service
    if _celery_service is None:
        _celery_service = CeleryService()
    return _celery_service
