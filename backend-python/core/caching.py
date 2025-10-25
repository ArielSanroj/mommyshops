"""
Comprehensive caching strategy implementation for MommyShops
Implements L1 (in-memory), L2 (Redis), and L3 (database) caching layers
"""

import redis
import json
import pickle
import hashlib
import time
from typing import Any, Optional, Dict, List, Union, Callable
from functools import wraps
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class CacheLevel(Enum):
    """Cache level enumeration"""
    L1 = "l1"  # In-memory cache
    L2 = "l2"  # Redis cache
    L3 = "l3"  # Database cache

class CacheStrategy(Enum):
    """Cache strategy enumeration"""
    WRITE_THROUGH = "write_through"
    WRITE_BACK = "write_back"
    WRITE_AROUND = "write_around"
    READ_THROUGH = "read_through"
    CACHE_ASIDE = "cache_aside"

@dataclass
class CacheConfig:
    """Cache configuration"""
    # L1 Cache (In-memory)
    l1_enabled: bool = True
    l1_max_size: int = 1000
    l1_ttl: int = 300  # 5 minutes
    
    # L2 Cache (Redis)
    l2_enabled: bool = True
    l2_ttl: int = 3600  # 1 hour
    l2_max_memory: str = "256mb"
    
    # L3 Cache (Database)
    l3_enabled: bool = True
    l3_ttl: int = 86400  # 24 hours
    
    # General settings
    default_ttl: int = 1800  # 30 minutes
    compression_enabled: bool = True
    serialization_format: str = "json"  # json or pickle
    
    # Redis settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    redis_connection_pool_size: int = 10

class CacheStats:
    """Cache statistics"""
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.errors = 0
        self.l1_hits = 0
        self.l2_hits = 0
        self.l3_hits = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "errors": self.errors,
            "hit_rate": self.hit_rate,
            "l1_hits": self.l1_hits,
            "l2_hits": self.l2_hits,
            "l3_hits": self.l3_hits
        }

class L1Cache:
    """L1 Cache - In-memory cache using LRU eviction"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = None  # Would use threading.RLock in production
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from L1 cache"""
        if key not in self._cache:
            return None
        
        # Check TTL
        if time.time() - self._cache[key]["timestamp"] > self.ttl:
            self.delete(key)
            return None
        
        # Update access time
        self._access_times[key] = time.time()
        return self._cache[key]["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in L1 cache"""
        try:
            # Evict if at capacity
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()
            
            self._cache[key] = {
                "value": value,
                "timestamp": time.time()
            }
            self._access_times[key] = time.time()
            return True
        except Exception as e:
            logger.error(f"L1 cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from L1 cache"""
        try:
            self._cache.pop(key, None)
            self._access_times.pop(key, None)
            return True
        except Exception as e:
            logger.error(f"L1 cache delete error: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all values from L1 cache"""
        try:
            self._cache.clear()
            self._access_times.clear()
            return True
        except Exception as e:
            logger.error(f"L1 cache clear error: {e}")
            return False
    
    def _evict_lru(self):
        """Evict least recently used item"""
        if not self._access_times:
            return
        
        lru_key = min(self._access_times.keys(), key=self._access_times.get)
        self.delete(lru_key)
    
    def size(self) -> int:
        """Get current cache size"""
        return len(self._cache)
    
    def keys(self) -> List[str]:
        """Get all cache keys"""
        return list(self._cache.keys())

class L2Cache:
    """L2 Cache - Redis cache"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self._redis: Optional[redis.Redis] = None
        self._connection_pool: Optional[redis.ConnectionPool] = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis"""
        try:
            self._connection_pool = redis.ConnectionPool(
                host=self.config.redis_host,
                port=self.config.redis_port,
                password=self.config.redis_password,
                db=self.config.redis_db,
                max_connections=self.config.redis_connection_pool_size,
                decode_responses=False  # We'll handle encoding/decoding
            )
            self._redis = redis.Redis(connection_pool=self._connection_pool)
            # Test connection
            self._redis.ping()
            logger.info("L2 cache (Redis) connected successfully")
        except Exception as e:
            logger.error(f"L2 cache connection error: {e}")
            self._redis = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from L2 cache"""
        if not self._redis:
            return None
        
        try:
            data = self._redis.get(key)
            if data is None:
                return None
            
            # Deserialize based on format
            if self.config.serialization_format == "json":
                return json.loads(data.decode('utf-8'))
            else:
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"L2 cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in L2 cache"""
        if not self._redis:
            return False
        
        try:
            # Serialize based on format
            if self.config.serialization_format == "json":
                data = json.dumps(value, default=str).encode('utf-8')
            else:
                data = pickle.dumps(value)
            
            # Set with TTL
            ttl = ttl or self.config.l2_ttl
            self._redis.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.error(f"L2 cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from L2 cache"""
        if not self._redis:
            return False
        
        try:
            self._redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"L2 cache delete error: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all values from L2 cache"""
        if not self._redis:
            return False
        
        try:
            self._redis.flushdb()
            return True
        except Exception as e:
            logger.error(f"L2 cache clear error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in L2 cache"""
        if not self._redis:
            return False
        
        try:
            return bool(self._redis.exists(key))
        except Exception as e:
            logger.error(f"L2 cache exists error: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """Get TTL for key in L2 cache"""
        if not self._redis:
            return -1
        
        try:
            return self._redis.ttl(key)
        except Exception as e:
            logger.error(f"L2 cache TTL error: {e}")
            return -1

class L3Cache:
    """L3 Cache - Database cache"""
    
    def __init__(self, db_session, ttl: int = 86400):
        self.db_session = db_session
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from L3 cache"""
        try:
            # This would query a cache table in the database
            # For now, return None as this is a placeholder
            return None
        except Exception as e:
            logger.error(f"L3 cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in L3 cache"""
        try:
            # This would insert/update a cache table in the database
            # For now, return True as this is a placeholder
            return True
        except Exception as e:
            logger.error(f"L3 cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from L3 cache"""
        try:
            # This would delete from a cache table in the database
            # For now, return True as this is a placeholder
            return True
        except Exception as e:
            logger.error(f"L3 cache delete error: {e}")
            return False

class MultiLevelCache:
    """Multi-level cache implementation"""
    
    def __init__(self, config: CacheConfig, db_session=None):
        self.config = config
        self.stats = CacheStats()
        
        # Initialize cache levels
        self.l1_cache = L1Cache(
            max_size=config.l1_max_size,
            ttl=config.l1_ttl
        ) if config.l1_enabled else None
        
        self.l2_cache = L2Cache(config) if config.l2_enabled else None
        self.l3_cache = L3Cache(db_session, config.l3_ttl) if config.l3_enabled and db_session else None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (L1 -> L2 -> L3)"""
        # Try L1 cache first
        if self.l1_cache:
            value = self.l1_cache.get(key)
            if value is not None:
                self.stats.hits += 1
                self.stats.l1_hits += 1
                return value
        
        # Try L2 cache
        if self.l2_cache:
            value = self.l2_cache.get(key)
            if value is not None:
                self.stats.hits += 1
                self.stats.l2_hits += 1
                # Populate L1 cache
                if self.l1_cache:
                    self.l1_cache.set(key, value)
                return value
        
        # Try L3 cache
        if self.l3_cache:
            value = self.l3_cache.get(key)
            if value is not None:
                self.stats.hits += 1
                self.stats.l3_hits += 1
                # Populate L1 and L2 caches
                if self.l1_cache:
                    self.l1_cache.set(key, value)
                if self.l2_cache:
                    self.l2_cache.set(key, value)
                return value
        
        self.stats.misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, strategy: CacheStrategy = CacheStrategy.WRITE_THROUGH) -> bool:
        """Set value in cache"""
        ttl = ttl or self.config.default_ttl
        success = True
        
        if strategy == CacheStrategy.WRITE_THROUGH:
            # Write to all levels
            if self.l1_cache:
                success &= self.l1_cache.set(key, value, ttl)
            if self.l2_cache:
                success &= self.l2_cache.set(key, value, ttl)
            if self.l3_cache:
                success &= self.l3_cache.set(key, value, ttl)
        
        elif strategy == CacheStrategy.WRITE_BACK:
            # Write to L1 first, L2 and L3 later
            if self.l1_cache:
                success &= self.l1_cache.set(key, value, ttl)
            # L2 and L3 would be written asynchronously
        
        elif strategy == CacheStrategy.WRITE_AROUND:
            # Write to L2 and L3, skip L1
            if self.l2_cache:
                success &= self.l2_cache.set(key, value, ttl)
            if self.l3_cache:
                success &= self.l3_cache.set(key, value, ttl)
        
        if success:
            self.stats.sets += 1
        
        return success
    
    def delete(self, key: str) -> bool:
        """Delete value from all cache levels"""
        success = True
        
        if self.l1_cache:
            success &= self.l1_cache.delete(key)
        if self.l2_cache:
            success &= self.l2_cache.delete(key)
        if self.l3_cache:
            success &= self.l3_cache.delete(key)
        
        if success:
            self.stats.deletes += 1
        
        return success
    
    def clear(self) -> bool:
        """Clear all cache levels"""
        success = True
        
        if self.l1_cache:
            success &= self.l1_cache.clear()
        if self.l2_cache:
            success &= self.l2_cache.clear()
        if self.l3_cache:
            success &= self.l3_cache.clear()
        
        return success
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = self.stats.to_dict()
        stats.update({
            "l1_enabled": self.l1_cache is not None,
            "l2_enabled": self.l2_cache is not None,
            "l3_enabled": self.l3_cache is not None,
            "l1_size": self.l1_cache.size() if self.l1_cache else 0,
            "l2_connected": self.l2_cache._redis is not None if self.l2_cache else False
        })
        return stats

def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments"""
    key_data = {
        "args": args,
        "kwargs": sorted(kwargs.items())
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()

def cached(
    ttl: int = 1800,
    key_prefix: str = "",
    cache_levels: List[CacheLevel] = None,
    strategy: CacheStrategy = CacheStrategy.WRITE_THROUGH
):
    """
    Decorator for caching function results
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
        cache_levels: Which cache levels to use
        strategy: Cache strategy to use
    """
    if cache_levels is None:
        cache_levels = [CacheLevel.L1, CacheLevel.L2]
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key_str = f"{key_prefix}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            # This would use the global cache instance
            # For now, just call the function
            result = func(*args, **kwargs)
            
            # Cache the result
            # This would use the global cache instance
            # For now, just return the result
            
            return result
        
        return wrapper
    return decorator

# Global cache instance
_cache_instance: Optional[MultiLevelCache] = None

def get_cache() -> Optional[MultiLevelCache]:
    """Get global cache instance"""
    return _cache_instance

def init_cache(config: CacheConfig, db_session=None) -> MultiLevelCache:
    """Initialize global cache instance"""
    global _cache_instance
    _cache_instance = MultiLevelCache(config, db_session)
    return _cache_instance

def cache_ingredient_analysis(ingredient: str) -> Optional[Dict[str, Any]]:
    """Cache ingredient analysis result"""
    cache = get_cache()
    if not cache:
        return None
    
    key = f"ingredient:{ingredient}"
    return cache.get(key)

def set_ingredient_analysis(ingredient: str, analysis: Dict[str, Any], ttl: int = 3600) -> bool:
    """Cache ingredient analysis result"""
    cache = get_cache()
    if not cache:
        return False
    
    key = f"ingredient:{ingredient}"
    return cache.set(key, analysis, ttl)

def cache_product_analysis(analysis_id: str, analysis: Dict[str, Any], ttl: int = 1800) -> bool:
    """Cache product analysis result"""
    cache = get_cache()
    if not cache:
        return False
    
    key = f"product_analysis:{analysis_id}"
    return cache.set(key, analysis, ttl)

def get_product_analysis(analysis_id: str) -> Optional[Dict[str, Any]]:
    """Get cached product analysis result"""
    cache = get_cache()
    if not cache:
        return None
    
    key = f"product_analysis:{analysis_id}"
    return cache.get(key)

def cache_external_api_response(api_name: str, endpoint: str, params: Dict[str, Any], response: Any, ttl: int = 3600) -> bool:
    """Cache external API response"""
    cache = get_cache()
    if not cache:
        return False
    
    key = f"external_api:{api_name}:{endpoint}:{cache_key(**params)}"
    return cache.set(key, response, ttl)

def get_external_api_response(api_name: str, endpoint: str, params: Dict[str, Any]) -> Optional[Any]:
    """Get cached external API response"""
    cache = get_cache()
    if not cache:
        return None
    
    key = f"external_api:{api_name}:{endpoint}:{cache_key(**params)}"
    return cache.get(key)

def clear_cache_pattern(pattern: str) -> bool:
    """Clear cache entries matching pattern"""
    cache = get_cache()
    if not cache:
        return False
    
    # This would implement pattern-based clearing
    # For now, just return True
    return True

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    cache = get_cache()
    if not cache:
        return {}
    
    return cache.get_stats()
