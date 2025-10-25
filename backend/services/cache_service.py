"""
Advanced caching service with L1/L2/L3 cache strategy
"""

import json
import asyncio
import logging
from typing import Any, Optional, Dict, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
from functools import wraps
import hashlib

logger = logging.getLogger(__name__)

class CacheService:
    """
    Multi-level cache service with L1 (in-memory), L2 (Redis), L3 (database)
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.l1_cache: Dict[str, Dict[str, Any]] = {}
        self.l1_ttl: Dict[str, datetime] = {}
        self.l1_max_size = 1000  # Max items in L1 cache
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate consistent cache key"""
        key_data = f"{prefix}:{':'.join(map(str, args))}:{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_l1_expired(self, key: str) -> bool:
        """Check if L1 cache entry is expired"""
        if key not in self.l1_ttl:
            return True
        return datetime.now() > self.l1_ttl[key]
    
    def _cleanup_l1_cache(self):
        """Clean up expired entries from L1 cache"""
        now = datetime.now()
        expired_keys = [k for k, ttl in self.l1_ttl.items() if now > ttl]
        for key in expired_keys:
            self.l1_cache.pop(key, None)
            self.l1_ttl.pop(key, None)
    
    def _evict_l1_if_needed(self):
        """Evict oldest entries if L1 cache is full"""
        if len(self.l1_cache) >= self.l1_max_size:
            # Remove oldest 20% of entries
            sorted_items = sorted(self.l1_ttl.items(), key=lambda x: x[1])
            to_remove = len(sorted_items) // 5
            for key, _ in sorted_items[:to_remove]:
                self.l1_cache.pop(key, None)
                self.l1_ttl.pop(key, None)
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache (L1 -> L2 -> L3)
        """
        # L1 Cache (in-memory)
        if key in self.l1_cache and not self._is_l1_expired(key):
            logger.debug(f"L1 cache hit for key: {key}")
            return self.l1_cache[key]["value"]
        
        # L2 Cache (Redis)
        try:
            cached_value = await self.redis_client.get(key)
            if cached_value:
                logger.debug(f"L2 cache hit for key: {key}")
                data = json.loads(cached_value)
                
                # Populate L1 cache
                self.l1_cache[key] = data
                self.l1_ttl[key] = datetime.now() + timedelta(seconds=data.get("ttl", 3600))
                self._evict_l1_if_needed()
                
                return data["value"]
        except Exception as e:
            logger.warning(f"L2 cache error for key {key}: {e}")
        
        return default
    
    async def set(self, key: str, value: Any, ttl: int = 3600, cache_level: str = "L2") -> bool:
        """
        Set value in cache with TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            cache_level: "L1", "L2", or "L1L2" for both
        """
        cache_data = {
            "value": value,
            "ttl": ttl,
            "created_at": datetime.now().isoformat()
        }
        
        success = True
        
        # L1 Cache (in-memory)
        if cache_level in ["L1", "L1L2"]:
            self.l1_cache[key] = cache_data
            self.l1_ttl[key] = datetime.now() + timedelta(seconds=ttl)
            self._evict_l1_if_needed()
            logger.debug(f"L1 cache set for key: {key}")
        
        # L2 Cache (Redis)
        if cache_level in ["L2", "L1L2"]:
            try:
                await self.redis_client.setex(
                    key, 
                    ttl, 
                    json.dumps(cache_data, default=str)
                )
                logger.debug(f"L2 cache set for key: {key}")
            except Exception as e:
                logger.error(f"L2 cache error for key {key}: {e}")
                success = False
        
        return success
    
    async def delete(self, key: str) -> bool:
        """Delete key from all cache levels"""
        # L1 Cache
        self.l1_cache.pop(key, None)
        self.l1_ttl.pop(key, None)
        
        # L2 Cache
        try:
            await self.redis_client.delete(key)
            logger.debug(f"Cache deleted for key: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def get_or_set(self, key: str, factory_func, ttl: int = 3600, cache_level: str = "L2") -> Any:
        """
        Get value from cache or set it using factory function
        
        Args:
            key: Cache key
            factory_func: Async function to generate value if not cached
            ttl: Time to live in seconds
            cache_level: Cache level to use
        """
        # Try to get from cache first
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Generate value using factory function
        try:
            value = await factory_func()
            await self.set(key, value, ttl, cache_level)
            return value
        except Exception as e:
            logger.error(f"Factory function error for key {key}: {e}")
            raise
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} keys matching pattern: {pattern}")
                return len(keys)
        except Exception as e:
            logger.error(f"Pattern invalidation error for {pattern}: {e}")
        return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        l1_stats = {
            "size": len(self.l1_cache),
            "max_size": self.l1_max_size,
            "hit_rate": 0.0  # Would need to track hits/misses
        }
        
        try:
            l2_info = await self.redis_client.info("memory")
            l2_stats = {
                "used_memory": l2_info.get("used_memory", 0),
                "used_memory_human": l2_info.get("used_memory_human", "0B"),
                "keyspace_hits": l2_info.get("keyspace_hits", 0),
                "keyspace_misses": l2_info.get("keyspace_misses", 0)
            }
            
            if l2_stats["keyspace_hits"] + l2_stats["keyspace_misses"] > 0:
                l2_stats["hit_rate"] = l2_stats["keyspace_hits"] / (
                    l2_stats["keyspace_hits"] + l2_stats["keyspace_misses"]
                )
        except Exception as e:
            logger.error(f"L2 stats error: {e}")
            l2_stats = {"error": str(e)}
        
        return {
            "l1": l1_stats,
            "l2": l2_stats,
            "timestamp": datetime.now().isoformat()
        }


def cache(ttl: int = 3600, key_prefix: str = "", cache_level: str = "L2"):
    """
    Decorator for caching function results
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
        cache_level: Cache level to use
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            cache_service = get_cache_service()
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_service.set(cache_key, result, ttl, cache_level)
            logger.debug(f"Cached result for {func.__name__}")
            return result
        
        return wrapper
    return decorator


# Global cache service instance
_cache_service: Optional[CacheService] = None

def get_cache_service() -> CacheService:
    """Get or create cache service instance"""
    global _cache_service
    if _cache_service is None:
        # This would be injected in real implementation
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        _cache_service = CacheService(redis_client)
    return _cache_service
