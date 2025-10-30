"""
Cache service for MommyShops application
Coordinated caching strategy with Redis L2 cache and in-memory L1 cache
"""

import json
import pickle
import time
import asyncio
from typing import Any, Optional, Dict, Union
import redis
import logging
from functools import wraps
from core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheService:
    """
    Coordinated caching service with L1 (in-memory) and L2 (Redis) cache
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.l1_cache: Dict[str, Any] = {}  # In-memory cache
        self.l1_max_size = 1000  # Maximum items in L1 cache
        self.l1_ttl = 300  # 5 minutes TTL for L1 cache
        
        # Redis connection
        try:
            self.redis_client = redis.Redis(
                host=self.settings.REDIS_HOST,
                port=self.settings.REDIS_PORT,
                password=self.settings.REDIS_PASSWORD,
                decode_responses=False,  # Keep binary for pickle
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            self.redis_available = True
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
            self.redis_client = None
            self.redis_available = False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (L1 first, then L2)
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        # Try L1 cache first
        if key in self.l1_cache:
            item = self.l1_cache[key]
            if time.time() - item['timestamp'] < self.l1_ttl:
                logger.debug(f"Cache hit (L1): {key}")
                return item['value']
            else:
                # Remove expired item
                del self.l1_cache[key]
        
        # Try L2 cache (Redis)
        if self.redis_available:
            try:
                cached_data = self.redis_client.get(f"cache:{key}")
                if cached_data:
                    value = pickle.loads(cached_data)
                    # Store in L1 cache for faster access
                    self._store_l1(key, value)
                    logger.debug(f"Cache hit (L2): {key}")
                    return value
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        logger.debug(f"Cache miss: {key}")
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set value in cache (both L1 and L2)
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        try:
            # Store in L1 cache
            self._store_l1(key, value)
            
            # Store in L2 cache (Redis)
            if self.redis_available:
                try:
                    serialized_data = pickle.dumps(value)
                    self.redis_client.setex(f"cache:{key}", ttl, serialized_data)
                    logger.debug(f"Cache set (L1+L2): {key}")
                except Exception as e:
                    logger.error(f"Redis set error: {e}")
                    return False
            else:
                logger.debug(f"Cache set (L1 only): {key}")
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache (both L1 and L2)
        
        Args:
            key: Cache key
            
        Returns:
            True if successful
        """
        try:
            # Remove from L1 cache
            if key in self.l1_cache:
                del self.l1_cache[key]
            
            # Remove from L2 cache
            if self.redis_available:
                try:
                    self.redis_client.delete(f"cache:{key}")
                except Exception as e:
                    logger.error(f"Redis delete error: {e}")
            
            logger.debug(f"Cache delete: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def clear(self) -> bool:
        """
        Clear all cache (both L1 and L2)
        
        Returns:
            True if successful
        """
        try:
            # Clear L1 cache
            self.l1_cache.clear()
            
            # Clear L2 cache
            if self.redis_available:
                try:
                    # Delete all cache keys
                    keys = self.redis_client.keys("cache:*")
                    if keys:
                        self.redis_client.delete(*keys)
                except Exception as e:
                    logger.error(f"Redis clear error: {e}")
            
            logger.info("Cache cleared")
            return True
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def _store_l1(self, key: str, value: Any) -> None:
        """Store value in L1 cache with size management"""
        # Remove oldest items if cache is full
        if len(self.l1_cache) >= self.l1_max_size:
            # Remove 10% of oldest items
            items_to_remove = self.l1_max_size // 10
            sorted_items = sorted(
                self.l1_cache.items(),
                key=lambda x: x[1]['timestamp']
            )
            for old_key, _ in sorted_items[:items_to_remove]:
                del self.l1_cache[old_key]
        
        self.l1_cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Cache statistics
        """
        stats = {
            'l1_size': len(self.l1_cache),
            'l1_max_size': self.l1_max_size,
            'l2_available': self.redis_available
        }
        
        if self.redis_available:
            try:
                # Get Redis info
                info = self.redis_client.info()
                stats.update({
                    'l2_used_memory': info.get('used_memory_human', 'N/A'),
                    'l2_connected_clients': info.get('connected_clients', 0),
                    'l2_keyspace_hits': info.get('keyspace_hits', 0),
                    'l2_keyspace_misses': info.get('keyspace_misses', 0)
                })
                
                # Calculate hit rate
                hits = stats['l2_keyspace_hits']
                misses = stats['l2_keyspace_misses']
                if hits + misses > 0:
                    stats['l2_hit_rate'] = round(hits / (hits + misses) * 100, 2)
                else:
                    stats['l2_hit_rate'] = 0
                    
            except Exception as e:
                logger.error(f"Error getting Redis stats: {e}")
                stats['l2_error'] = str(e)
        
        return stats


# Global cache service instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get or create cache service instance"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def cached(ttl: int = 3600, key_prefix: str = ""):
    """
    Decorator for caching function results
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_service = get_cache_service()
            
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Cache the result
            cache_service.set(cache_key, result, ttl)
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_service = get_cache_service()
            
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            
            # Cache the result
            cache_service.set(cache_key, result, ttl)
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Cache warming functions
async def warm_cache():
    """Warm up cache with frequently accessed data"""
    cache_service = get_cache_service()
    logger.info("Starting cache warming...")
    
    try:
        # Warm up ingredient data
        from app.database.session import get_db_session
        from app.database.models import Ingredient
        
        db = get_db_session()
        try:
            # Cache popular ingredients
            popular_ingredients = db.query(Ingredient).limit(100).all()
            for ingredient in popular_ingredients:
                cache_key = f"ingredient:{ingredient.name}"
                cache_service.set(cache_key, {
                    'name': ingredient.name,
                    'eco_score': ingredient.eco_score,
                    'risk_level': ingredient.risk_level,
                    'description': ingredient.description
                }, ttl=7200)  # 2 hours
            
            logger.info(f"Warmed cache with {len(popular_ingredients)} ingredients")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Cache warming failed: {e}")


# Health check for cache
async def cache_health_check() -> Dict[str, Any]:
    """
    Check cache health
    
    Returns:
        Cache health status
    """
    cache_service = get_cache_service()
    
    health_status = {
        'l1_cache': 'healthy',
        'l2_cache': 'unknown',
        'overall': 'unknown'
    }
    
    try:
        # Test L1 cache
        test_key = 'health_check_test'
        test_value = {'test': True, 'timestamp': time.time()}
        
        cache_service.set(test_key, test_value, ttl=60)
        retrieved_value = cache_service.get(test_key)
        
        if retrieved_value and retrieved_value.get('test'):
            health_status['l1_cache'] = 'healthy'
        else:
            health_status['l1_cache'] = 'unhealthy'
        
        # Test L2 cache (Redis)
        if cache_service.redis_available:
            try:
                cache_service.redis_client.ping()
                health_status['l2_cache'] = 'healthy'
            except Exception:
                health_status['l2_cache'] = 'unhealthy'
        else:
            health_status['l2_cache'] = 'unavailable'
        
        # Overall health
        if health_status['l1_cache'] == 'healthy':
            if health_status['l2_cache'] in ['healthy', 'unavailable']:
                health_status['overall'] = 'healthy'
            else:
                health_status['overall'] = 'degraded'
        else:
            health_status['overall'] = 'unhealthy'
        
        # Clean up test key
        cache_service.delete(test_key)
        
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        health_status['overall'] = 'unhealthy'
        health_status['error'] = str(e)
    
    return health_status
