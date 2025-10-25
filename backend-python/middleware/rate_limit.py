"""
Rate limiting middleware for MommyShops API
Prevents DDoS attacks and abuse
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import time
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

# Rate limit configurations
RATE_LIMITS = {
    "general": "100/minute",
    "analysis": "10/minute", 
    "auth": "5/minute",
    "upload": "5/minute",
    "api": "200/hour"
}

def create_rate_limit_middleware(app):
    """
    Create and configure rate limiting middleware
    """
    # Add slowapi middleware
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    
    return app

def get_rate_limit_for_endpoint(endpoint: str) -> str:
    """
    Get appropriate rate limit for endpoint
    """
    if "auth" in endpoint or "login" in endpoint or "register" in endpoint:
        return RATE_LIMITS["auth"]
    elif "analyze" in endpoint or "ocr" in endpoint or "upload" in endpoint:
        return RATE_LIMITS["analysis"]
    elif "api" in endpoint:
        return RATE_LIMITS["api"]
    else:
        return RATE_LIMITS["general"]

class RateLimitTracker:
    """
    Simple in-memory rate limit tracker
    """
    
    def __init__(self):
        self.requests: Dict[str, list] = {}
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """
        Check if request is allowed based on rate limit
        """
        now = time.time()
        
        # Cleanup old entries periodically
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_entries(now)
            self.last_cleanup = now
        
        # Get requests for this key
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside window
        cutoff = now - window
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > cutoff]
        
        # Check if under limit
        if len(self.requests[key]) < limit:
            self.requests[key].append(now)
            return True
        
        return False
    
    def _cleanup_old_entries(self, now: float):
        """
        Cleanup old entries to prevent memory leaks
        """
        cutoff = now - 3600  # 1 hour
        for key in list(self.requests.keys()):
            self.requests[key] = [req_time for req_time in self.requests[key] if req_time > cutoff]
            if not self.requests[key]:
                del self.requests[key]

# Global rate limit tracker
rate_tracker = RateLimitTracker()

def check_rate_limit(request: Request, limit: str) -> bool:
    """
    Check rate limit for request
    """
    try:
        # Parse limit (e.g., "10/minute")
        count, period = limit.split("/")
        count = int(count)
        
        # Convert period to seconds
        if period == "minute":
            window = 60
        elif period == "hour":
            window = 3600
        elif period == "day":
            window = 86400
        else:
            window = 60  # default to minute
        
        # Get client identifier
        client_ip = get_remote_address(request)
        user_agent = request.headers.get("user-agent", "")
        key = f"{client_ip}:{user_agent}"
        
        # Check rate limit
        allowed = rate_tracker.is_allowed(key, count, window)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for {client_ip}: {limit}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking rate limit: {e}")
        return True  # Allow request on error

def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Handle rate limit exceeded
    """
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Limit: {exc.detail}",
            "retry_after": 60
        }
    )
