"""
External API resilience implementation
Circuit breakers, retry logic, and caching for external APIs
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, Callable, List, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import aiohttp
import json
from functools import wraps
import random

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class RetryStrategy(Enum):
    """Retry strategies"""
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    CUSTOM = "custom"

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    expected_exception: type = Exception
    success_threshold: int = 3

@dataclass
class RetryConfig:
    """Retry configuration"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    backoff_factor: float = 2.0
    jitter: bool = True

@dataclass
class CacheConfig:
    """Cache configuration"""
    ttl: int = 300  # seconds
    max_size: int = 1000
    enabled: bool = True

class CircuitBreaker:
    """Circuit breaker implementation"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.name = "default"
    
    def can_execute(self) -> bool:
        """Check if circuit breaker allows execution"""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        
        if self.state == CircuitState.HALF_OPEN:
            return True
        
        return False
    
    def record_success(self):
        """Record successful execution"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._reset()
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    def record_failure(self):
        """Record failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker {self.name} opened due to {self.failure_count} failures")
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if not self.last_failure_time:
            return True
        
        return time.time() - self.last_failure_time >= self.config.recovery_timeout
    
    def _reset(self):
        """Reset circuit breaker"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info(f"Circuit breaker {self.name} reset to closed state")

class RetryHandler:
    """Retry handler implementation"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.config.max_attempts - 1:
                    logger.error(f"All retry attempts failed for {func.__name__}: {e}")
                    raise e
                
                delay = self._calculate_delay(attempt)
                logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}, retrying in {delay}s: {e}")
                await asyncio.sleep(delay)
        
        raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt"""
        if self.config.strategy == RetryStrategy.FIXED:
            delay = self.config.base_delay
        elif self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.base_delay * (self.config.backoff_factor ** attempt)
        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.base_delay * (attempt + 1)
        else:
            delay = self.config.base_delay
        
        # Apply jitter
        if self.config.jitter:
            jitter = random.uniform(0, delay * 0.1)
            delay += jitter
        
        return min(delay, self.config.max_delay)

class APICache:
    """API response cache"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        if not self.config.enabled:
            return None
        
        if key not in self.cache:
            return None
        
        cached_data = self.cache[key]
        
        # Check TTL
        if time.time() - cached_data["timestamp"] > self.config.ttl:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
            return None
        
        # Update access time
        self.access_times[key] = time.time()
        return cached_data["value"]
    
    def set(self, key: str, value: Any):
        """Set cached value"""
        if not self.config.enabled:
            return
        
        # Evict oldest entries if cache is full
        if len(self.cache) >= self.config.max_size:
            self._evict_oldest()
        
        self.cache[key] = {
            "value": value,
            "timestamp": time.time()
        }
        self.access_times[key] = time.time()
    
    def _evict_oldest(self):
        """Evict oldest cache entry"""
        if not self.access_times:
            return
        
        oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        del self.cache[oldest_key]
        del self.access_times[oldest_key]
    
    def clear(self):
        """Clear cache"""
        self.cache.clear()
        self.access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.config.max_size,
            "enabled": self.config.enabled,
            "ttl": self.config.ttl
        }

class ResilientAPIClient:
    """Resilient API client with circuit breaker, retry, and caching"""
    
    def __init__(
        self,
        circuit_breaker_config: CircuitBreakerConfig,
        retry_config: RetryConfig,
        cache_config: CacheConfig,
        base_url: str = "",
        timeout: int = 30
    ):
        self.circuit_breaker = CircuitBreaker(circuit_breaker_config)
        self.retry_handler = RetryHandler(retry_config)
        self.cache = APICache(cache_config)
        self.base_url = base_url
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get(self, url: str, headers: Dict[str, str] = None, cache_key: str = None) -> Dict[str, Any]:
        """Make GET request with resilience"""
        return await self._make_request("GET", url, headers=headers, cache_key=cache_key)
    
    async def post(self, url: str, data: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
        """Make POST request with resilience"""
        return await self._make_request("POST", url, data=data, headers=headers)
    
    async def _make_request(
        self,
        method: str,
        url: str,
        data: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
        cache_key: str = None
    ) -> Dict[str, Any]:
        """Make HTTP request with resilience"""
        
        # Check circuit breaker
        if not self.circuit_breaker.can_execute():
            raise Exception(f"Circuit breaker is open for {url}")
        
        # Check cache for GET requests
        if method == "GET" and cache_key:
            cached_response = self.cache.get(cache_key)
            if cached_response is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_response
        
        # Make request with retry
        try:
            response = await self.retry_handler.execute_with_retry(
                self._execute_request, method, url, data, headers
            )
            
            # Record success
            self.circuit_breaker.record_success()
            
            # Cache GET responses
            if method == "GET" and cache_key:
                self.cache.set(cache_key, response)
            
            return response
            
        except Exception as e:
            # Record failure
            self.circuit_breaker.record_failure()
            raise e
    
    async def _execute_request(
        self,
        method: str,
        url: str,
        data: Dict[str, Any] = None,
        headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Execute HTTP request"""
        if not self.session:
            raise Exception("Session not initialized")
        
        full_url = f"{self.base_url}{url}" if self.base_url else url
        
        request_kwargs = {
            "headers": headers or {},
            "timeout": aiohttp.ClientTimeout(total=self.timeout)
        }
        
        if data:
            request_kwargs["json"] = data
        
        async with self.session.request(method, full_url, **request_kwargs) as response:
            if response.status >= 400:
                raise Exception(f"HTTP {response.status}: {await response.text()}")
            
            return await response.json()

# Global resilience components
_circuit_breakers: Dict[str, CircuitBreaker] = {}
_retry_handlers: Dict[str, RetryHandler] = {}
_api_caches: Dict[str, APICache] = {}

def get_circuit_breaker(name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
    """Get or create circuit breaker"""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(config or CircuitBreakerConfig())
        _circuit_breakers[name].name = name
    return _circuit_breakers[name]

def get_retry_handler(name: str, config: RetryConfig = None) -> RetryHandler:
    """Get or create retry handler"""
    if name not in _retry_handlers:
        _retry_handlers[name] = RetryHandler(config or RetryConfig())
    return _retry_handlers[name]

def get_api_cache(name: str, config: CacheConfig = None) -> APICache:
    """Get or create API cache"""
    if name not in _api_caches:
        _api_caches[name] = APICache(config or CacheConfig())
    return _api_caches[name]

def resilient_api_call(
    circuit_breaker_name: str = "default",
    retry_handler_name: str = "default",
    cache_name: str = "default"
):
    """Decorator for resilient API calls"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            circuit_breaker = get_circuit_breaker(circuit_breaker_name)
            retry_handler = get_retry_handler(retry_handler_name)
            cache = get_api_cache(cache_name)
            
            # Check circuit breaker
            if not circuit_breaker.can_execute():
                raise Exception(f"Circuit breaker {circuit_breaker_name} is open")
            
            # Check cache
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute with retry
            try:
                result = await retry_handler.execute_with_retry(func, *args, **kwargs)
                circuit_breaker.record_success()
                cache.set(cache_key, result)
                return result
            except Exception as e:
                circuit_breaker.record_failure()
                raise e
        
        return wrapper
    return decorator

# Pre-configured resilience components for common APIs
def get_fda_api_client() -> ResilientAPIClient:
    """Get FDA API client with resilience"""
    return ResilientAPIClient(
        circuit_breaker_config=CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30
        ),
        retry_config=RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            strategy=RetryStrategy.EXPONENTIAL
        ),
        cache_config=CacheConfig(
            ttl=3600,  # 1 hour
            max_size=500
        ),
        base_url="https://api.fda.gov",
        timeout=30
    )

def get_pubchem_api_client() -> ResilientAPIClient:
    """Get PubChem API client with resilience"""
    return ResilientAPIClient(
        circuit_breaker_config=CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=60
        ),
        retry_config=RetryConfig(
            max_attempts=3,
            base_delay=2.0,
            strategy=RetryStrategy.EXPONENTIAL
        ),
        cache_config=CacheConfig(
            ttl=7200,  # 2 hours
            max_size=1000
        ),
        base_url="https://pubchem.ncbi.nlm.nih.gov/rest/pug",
        timeout=45
    )

def get_ewg_api_client() -> ResilientAPIClient:
    """Get EWG API client with resilience"""
    return ResilientAPIClient(
        circuit_breaker_config=CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=45
        ),
        retry_config=RetryConfig(
            max_attempts=2,
            base_delay=1.5,
            strategy=RetryStrategy.LINEAR
        ),
        cache_config=CacheConfig(
            ttl=1800,  # 30 minutes
            max_size=300
        ),
        base_url="https://www.ewg.org/skindeep/api",
        timeout=20
    )
