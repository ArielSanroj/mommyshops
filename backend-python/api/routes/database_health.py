"""
Database health and optimization endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import logging
import time
from datetime import datetime

from core.database_optimization import (
    get_database_health, 
    get_query_performance_stats, 
    get_connection_pool_stats,
    optimize_database_queries
)
from core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/database", tags=["database"])

@router.get("/health")
async def get_database_health_endpoint():
    """Get database health status"""
    try:
        health = get_database_health()
        return health
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_database_stats():
    """Get database performance statistics"""
    try:
        stats = {
            "query_performance": get_query_performance_stats(),
            "connection_pool": get_connection_pool_stats(),
            "timestamp": datetime.now().isoformat()
        }
        return stats
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize")
async def optimize_database():
    """Optimize database performance"""
    try:
        logger.info("Starting database optimization...")
        start_time = time.time()
        
        # Run database optimization
        optimize_database_queries()
        
        duration = time.time() - start_time
        
        return {
            "status": "success",
            "message": "Database optimization completed",
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/slow-queries")
async def get_slow_queries():
    """Get slow query statistics"""
    try:
        stats = get_query_performance_stats()
        slow_queries = stats.get("slow_queries", [])
        
        return {
            "slow_queries": slow_queries,
            "count": len(slow_queries),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get slow queries: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connection-pool")
async def get_connection_pool_status():
    """Get connection pool status"""
    try:
        pool_stats = get_connection_pool_stats()
        return pool_stats
    except Exception as e:
        logger.error(f"Failed to get connection pool stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
