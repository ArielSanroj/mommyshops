# External API Resilience Guide

## Overview

This guide covers the comprehensive resilience strategy implemented for MommyShops external API integrations, including circuit breakers, retry logic, and caching mechanisms.

## Architecture

### Python Backend (FastAPI)
- **Circuit Breaker**: State-based failure protection
- **Retry Logic**: Exponential backoff with jitter
- **Caching**: In-memory cache with TTL
- **Async Support**: Full async/await support

### Java Backend (Spring Boot)
- **Circuit Breaker**: Atomic state management
- **Retry Logic**: Configurable retry strategies
- **Caching**: Spring Cache integration
- **Synchronous**: Blocking operations with resilience

## Components

### 1. Circuit Breaker

#### Python Implementation
```python
from core.resilience import CircuitBreaker, CircuitBreakerConfig

# Configure circuit breaker
config = CircuitBreakerConfig(
    failure_threshold=5,
    recovery_timeout=60,
    success_threshold=3
)

circuit_breaker = CircuitBreaker(config)

# Use in API calls
if circuit_breaker.can_execute():
    try:
        result = await api_call()
        circuit_breaker.record_success()
        return result
    except Exception as e:
        circuit_breaker.record_failure()
        raise e
```

#### Java Implementation
```java
@Autowired
private CircuitBreaker circuitBreaker;

public ResponseEntity<Object> callExternalAPI() {
    if (!circuitBreaker.canExecute()) {
        throw new RuntimeException("Circuit breaker is open");
    }
    
    try {
        ResponseEntity<Object> result = restTemplate.getForEntity(url, Object.class);
        circuitBreaker.recordSuccess();
        return result;
    } catch (Exception e) {
        circuitBreaker.recordFailure();
        throw e;
    }
}
```

### 2. Retry Logic

#### Python Implementation
```python
from core.resilience import RetryHandler, RetryConfig, RetryStrategy

# Configure retry handler
config = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=60.0,
    strategy=RetryStrategy.EXPONENTIAL,
    backoff_factor=2.0,
    jitter=True
)

retry_handler = RetryHandler(config)

# Use in API calls
result = await retry_handler.execute_with_retry(api_call, *args, **kwargs)
```

#### Java Implementation
```java
@Autowired
private RetryHandler retryHandler;

public Object callExternalAPI() {
    return retryHandler.executeWithRetry(() -> {
        return restTemplate.getForObject(url, Object.class);
    }, "external_api_call");
}
```

### 3. Caching

#### Python Implementation
```python
from core.resilience import APICache, CacheConfig

# Configure cache
config = CacheConfig(
    ttl=300,  # 5 minutes
    max_size=1000,
    enabled=True
)

cache = APICache(config)

# Use in API calls
cache_key = f"api_call:{hash(str(args))}"
cached_result = cache.get(cache_key)
if cached_result is not None:
    return cached_result

result = await api_call()
cache.set(cache_key, result)
return result
```

#### Java Implementation
```java
@Cacheable(value = "api_cache", key = "#url")
public ResponseEntity<Object> callExternalAPI(String url) {
    return restTemplate.getForEntity(url, Object.class);
}
```

## Pre-configured API Clients

### FDA API Client
```python
# Python
from core.resilience import get_fda_api_client

async with get_fda_api_client() as client:
    result = await client.get("/drug/label.json", cache_key="fda_drugs")
```

```java
// Java
@Autowired
private ResilientAPIClient resilientAPIClient;

public ResponseEntity<Object> getFDAData() {
    return resilientAPIClient.get("https://api.fda.gov/drug/label.json", 
        Object.class, null);
}
```

### PubChem API Client
```python
# Python
from core.resilience import get_pubchem_api_client

async with get_pubchem_api_client() as client:
    result = await client.get("/compound/cid/2244/property/MolecularFormula,MolecularWeight/JSON")
```

```java
// Java
public ResponseEntity<Object> getPubChemData() {
    return resilientAPIClient.get("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/property/MolecularFormula,MolecularWeight/JSON", 
        Object.class, null);
}
```

### EWG API Client
```python
# Python
from core.resilience import get_ewg_api_client

async with get_ewg_api_client() as client:
    result = await client.get("/ingredient/702355", cache_key="ewg_ingredient")
```

```java
// Java
public ResponseEntity<Object> getEWGData() {
    return resilientAPIClient.get("https://www.ewg.org/skindeep/api/ingredient/702355", 
        Object.class, null);
}
```

## Configuration

### Python Configuration
```python
# Circuit breaker settings
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60
CIRCUIT_BREAKER_SUCCESS_THRESHOLD=3

# Retry settings
RETRY_MAX_ATTEMPTS=3
RETRY_BASE_DELAY=1.0
RETRY_MAX_DELAY=60.0
RETRY_STRATEGY=exponential
RETRY_BACKOFF_FACTOR=2.0
RETRY_JITTER=true

# Cache settings
CACHE_TTL=300
CACHE_MAX_SIZE=1000
CACHE_ENABLED=true
```

### Java Configuration
```properties
# Circuit breaker settings
resilience.circuit-breaker.failure-threshold=5
resilience.circuit-breaker.recovery-timeout=60
resilience.circuit-breaker.success-threshold=3

# Retry settings
resilience.retry.max-attempts=3
resilience.retry.base-delay=1000
resilience.retry.max-delay=60000
resilience.retry.strategy=exponential
resilience.retry.backoff-factor=2.0
resilience.retry.jitter=true

# Cache settings
spring.cache.type=caffeine
spring.cache.caffeine.spec=maximumSize=1000,expireAfterWrite=300s
```

## Monitoring

### Health Endpoints

#### Python Endpoints
- `GET /api/resilience/health` - Resilience health status
- `GET /api/resilience/stats` - Circuit breaker and retry statistics
- `GET /api/resilience/circuit-breakers` - Circuit breaker states
- `GET /api/resilience/cache/stats` - Cache statistics

#### Java Endpoints
- `GET /api/resilience/health` - Resilience health status
- `GET /api/resilience/stats` - Circuit breaker and retry statistics
- `GET /api/resilience/circuit-breakers` - Circuit breaker states

### Metrics

1. **Circuit Breaker Metrics**
   - State transitions
   - Failure counts
   - Success counts
   - Recovery time

2. **Retry Metrics**
   - Retry attempts
   - Success rate
   - Average retry time
   - Failure rate

3. **Cache Metrics**
   - Hit rate
   - Miss rate
   - Cache size
   - TTL effectiveness

## Best Practices

### 1. Circuit Breaker Configuration
- Set appropriate failure thresholds
- Configure recovery timeouts
- Monitor state transitions
- Implement fallback mechanisms

### 2. Retry Logic
- Use exponential backoff
- Implement jitter to avoid thundering herd
- Set reasonable retry limits
- Log retry attempts

### 3. Caching
- Use appropriate TTL values
- Implement cache invalidation
- Monitor cache hit rates
- Use cache keys effectively

### 4. Monitoring
- Track circuit breaker states
- Monitor retry patterns
- Analyze failure rates
- Set up alerts

## Troubleshooting

### Common Issues

1. **Circuit Breaker Stuck Open**
   - Check failure thresholds
   - Verify recovery timeouts
   - Review error patterns

2. **Excessive Retries**
   - Adjust retry limits
   - Check network connectivity
   - Review API rate limits

3. **Cache Issues**
   - Verify TTL settings
   - Check cache size limits
   - Monitor memory usage

### Performance Tuning

1. **Circuit Breaker Tuning**
   - Adjust failure thresholds
   - Optimize recovery timeouts
   - Balance sensitivity vs. stability

2. **Retry Tuning**
   - Optimize retry strategies
   - Adjust backoff factors
   - Set appropriate limits

3. **Cache Tuning**
   - Optimize TTL values
   - Adjust cache size
   - Monitor hit rates

## Security Considerations

1. **API Security**
   - Use secure connections
   - Implement authentication
   - Monitor API usage

2. **Data Security**
   - Encrypt sensitive data
   - Implement access controls
   - Monitor data access

3. **Rate Limiting**
   - Implement rate limiting
   - Monitor API usage
   - Handle rate limit errors

## Conclusion

This resilience strategy provides comprehensive protection for external API integrations through circuit breakers, retry logic, and caching. Regular monitoring and tuning ensure optimal performance and reliability.
