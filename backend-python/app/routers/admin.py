"""
Admin router
Handles administrative functions and system management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from app.dependencies import get_database, require_admin
from database import User, Product, Ingredient
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

# Pydantic models
class UserStats(BaseModel):
    total_users: int
    active_users: int
    new_users_today: int
    new_users_this_week: int

class SystemStats(BaseModel):
    total_products: int
    total_ingredients: int
    total_analyses: int
    system_uptime: float

@router.get("/users/stats", response_model=UserStats)
async def get_user_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_database)
):
    """Get user statistics"""
    try:
        from datetime import datetime, timedelta
        
        # Get user counts
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        
        # Get new users
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        new_users_today = db.query(User).filter(
            User.created_at >= today
        ).count()
        
        new_users_this_week = db.query(User).filter(
            User.created_at >= week_ago
        ).count()
        
        return UserStats(
            total_users=total_users,
            active_users=active_users,
            new_users_today=new_users_today,
            new_users_this_week=new_users_this_week
        )
        
    except Exception as e:
        logger.error(f"Failed to get user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user statistics"
        )

@router.get("/system/stats", response_model=SystemStats)
async def get_system_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_database)
):
    """Get system statistics"""
    try:
        import time
        import psutil
        
        # Get counts
        total_products = db.query(Product).count()
        total_ingredients = db.query(Ingredient).count()
        
        # Get system uptime
        uptime = time.time() - psutil.boot_time()
        
        return SystemStats(
            total_products=total_products,
            total_ingredients=total_ingredients,
            total_analyses=0,  # TODO: Implement analysis counting
            system_uptime=uptime
        )
        
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system statistics"
        )

@router.get("/users")
async def list_users(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_database)
):
    """List users (admin only)"""
    try:
        users = db.query(User).offset(offset).limit(limit).all()
        
        return {
            "users": [
                {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "is_active": user.is_active,
                    "created_at": user.created_at
                }
                for user in users
            ],
            "total": db.query(User).count(),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )

@router.put("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_database)
):
    """Activate/deactivate user"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = not user.is_active
        db.commit()
        
        return {
            "success": True,
            "user_id": user_id,
            "is_active": user.is_active
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate user: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate user"
        )
