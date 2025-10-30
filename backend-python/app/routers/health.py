"""
Health check router
Handles application health monitoring and status checks
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging
import time
import psutil
import os

from app.dependencies import get_database
from core.config import get_settings
from app.services.external_apis import health_check as external_api_health_check
import redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "mommyshops-backend"
    }

@router.get("/detailed")
async def detailed_health_check(
    db: Session = Depends(get_database)
):
    """Detailed health check with system metrics"""
    try:
        # Check database connectivity
        db_status = "healthy"
        try:
            db.execute("SELECT 1")
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
        
        # Get application settings
        settings = get_settings()
        
        # Check Redis connectivity
        redis_status = "healthy"
        try:
            r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, password=settings.REDIS_PASSWORD)
            r.ping()
        except Exception as e:
            redis_status = f"unhealthy: {str(e)}"
        
        # Check external APIs
        external_api_status = await external_api_health_check()
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "status": "healthy" if db_status == "healthy" else "degraded",
            "timestamp": time.time(),
            "service": "mommyshops-backend",
            "version": "1.0.0",
            "components": {
                "database": db_status,
                "redis": redis_status,
                "external_apis": external_api_status
            },
            "system_metrics": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2)
            },
            "configuration": {
                "environment": settings.ENVIRONMENT,
                "debug": settings.DEBUG,
                "database_url_configured": bool(settings.DATABASE_URL),
                "jwt_secret_configured": bool(settings.JWT_SECRET)
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )

@router.get("/readiness")
async def readiness_check(
    db: Session = Depends(get_database)
):
    """Kubernetes readiness probe"""
    try:
        # Check critical dependencies
        db.execute("SELECT 1")
        
        return {
            "status": "ready",
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )

@router.get("/liveness")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {
        "status": "alive",
        "timestamp": time.time()
    }

@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Format as Prometheus metrics
        metrics_data = f"""# HELP system_cpu_percent CPU usage percentage
# TYPE system_cpu_percent gauge
system_cpu_percent {cpu_percent}

# HELP system_memory_percent Memory usage percentage
# TYPE system_memory_percent gauge
system_memory_percent {memory.percent}

# HELP system_memory_available_gb Memory available in GB
# TYPE system_memory_available_gb gauge
system_memory_available_gb {round(memory.available / (1024**3), 2)}

# HELP system_disk_percent Disk usage percentage
# TYPE system_disk_percent gauge
system_disk_percent {disk.percent}

# HELP system_disk_free_gb Disk free space in GB
# TYPE system_disk_free_gb gauge
system_disk_free_gb {round(disk.free / (1024**3), 2)}
"""
        
        return metrics_data
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return f"# Error collecting metrics: {str(e)}"
