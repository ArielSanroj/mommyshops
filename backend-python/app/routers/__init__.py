"""
Routers package for MommyShops application
"""

from .auth import router as auth_router
from .analysis import router as analysis_router
from .builder import router as builder_router
from .formulation import router as formulation_router
from .profile import router as profile_router
from .health import router as health_router
from .admin import router as admin_router

# WhatsApp router is optional (requires waha module)
try:
    from .whatsapp import router as whatsapp_router
except ImportError:
    whatsapp_router = None

__all__ = [
    "auth_router",
    "analysis_router", 
    "profile_router",
    "builder_router",
    "formulation_router",
    "health_router",
    "admin_router",
    "whatsapp_router",
]
