"""
Routers package for MommyShops application
"""

from .auth import router as auth_router
from .analysis import router as analysis_router
from .health import router as health_router
from .admin import router as admin_router

__all__ = [
    "auth_router",
    "analysis_router", 
    "health_router",
    "admin_router"
]
