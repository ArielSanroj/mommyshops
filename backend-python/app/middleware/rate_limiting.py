"""
Rate limiting middleware configuration
"""

from fastapi import FastAPI, Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import redis
import json
from typing import Dict, Optional
from core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis"""
    
    def __init__(self, app, redis_client: Optional[redis.Redis] = None):
        super().__init__(app)
        self.redis_client = redis_client
        self.settings = get_settings()
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path.startswith('/health'):
            return await call_next(request)
        
        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        user_id = getattr(request.state, 'user_id', None)
        
        # Use user ID if available, otherwise use IP
        identifier = f"user:{user_id}" if user_id else f"ip:{client_ip}"
        
        # Check rate limit
        if not await self._check_rate_limit(identifier, request.url.path):
            logger.warning(f"Rate limit exceeded for {identifier} on {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        return await call_next(request)
    
    async def _check_rate_limit(self, identifier: str, path: str) -> bool:
        """Check if request is within rate limit"""
        if not self.redis_client:
            return True  # Skip rate limiting if Redis is not available
        
        try:
            # Different rate limits for different endpoints
            if path.startswith('/auth/'):
                limit = 5  # 5 requests per minute for auth endpoints
                window = 60
            elif path.startswith('/analysis/'):
                limit = 10  # 10 requests per minute for analysis endpoints
                window = 60
            else:
                limit = 60  # 60 requests per minute for other endpoints
                window = 60
            
            key = f"rate_limit:{identifier}:{path}"
            current_time = int(time.time())
            window_start = current_time - window
            
            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set expiration
            pipe.expire(key, window)
            
            results = pipe.execute()
            current_requests = results[1]
            
            return current_requests < limit
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            return True  # Allow request if rate limiting fails


def configure_rate_limiting(app: FastAPI):
    """Configure rate limiting middleware"""
    try:
        settings = get_settings()
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
        
        # Test Redis connection
        redis_client.ping()
        
        app.add_middleware(RateLimitMiddleware, redis_client=redis_client)
        logger.info("Rate limiting middleware configured successfully")
        
    except Exception as e:
        logger.warning(f"Rate limiting not configured: {e}")
        # Continue without rate limiting if Redis is not available
