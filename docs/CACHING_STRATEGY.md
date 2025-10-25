# MommyShops Caching Strategy

## 🚀 Overview

The MommyShops project implements a comprehensive multi-level caching strategy to optimize performance and reduce external API calls. The caching system consists of three levels: L1 (in-memory), L2 (Redis), and L3 (database).

## 🏗️ Architecture

### Cache Levels

#### L1 Cache (In-Memory)
- **Purpose**: Fastest access for frequently used data
- **Storage**: Application memory
- **Capacity**: 1,000 entries (configurable)
- **TTL**: 5 minutes (configurable)
- **Eviction**: LRU (Least Recently Used)
- **Use Case**: Hot data, session data, frequently accessed ingredients

#### L2 Cache (Redis)
- **Purpose**: Shared cache between application instances
- **Storage**: Redis server
- **Capacity**: 256MB (configurable)
- **TTL**: 1 hour (configurable)
- **Eviction**: LRU with TTL
- **Use Case**: Shared data, external API responses, user sessions

#### L3 Cache (Database)
- **Purpose**: Persistent cache for long-term storage
- **Storage**: PostgreSQL database
- **Capacity**: Limited by database storage
- **TTL**: 24 hours (configurable)
- **Eviction**: TTL-based
- **Use Case**: Historical data, analysis results, user preferences

## 🔄 Cache Strategies

### Write-Through
- **Description**: Write to all cache levels immediately
- **Use Case**: Critical data that must be consistent
- **Performance**: Slower writes, faster reads
- **Example**: User authentication data

### Write-Back
- **Description**: Write to L1 first, L2 and L3 later
- **Use Case**: High-frequency writes
- **Performance**: Fastest writes, eventual consistency
- **Example**: User activity logs

### Write-Around
- **Description**: Write to L2 and L3, skip L1
- **Use Case**: Large data that doesn't fit in L1
- **Performance**: Medium writes, slower reads
- **Example**: Large analysis results

### Read-Through
- **Description**: Read through cache to data source
- **Use Case**: Data that's always needed
- **Performance**: Slower first read, faster subsequent reads
- **Example**: External API data

### Cache-Aside
- **Description**: Application manages cache and data source
- **Use Case**: Complex business logic
- **Performance**: Most control, requires more code
- **Example**: Custom analysis workflows

## 📊 Cache Configuration

### Python Configuration

```python
# core/caching.py
@dataclass
class CacheConfig:
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
```

### Java Configuration

```yaml
# application.yml
cache:
  l1:
    enabled: true
    max-size: 1000
    ttl: 300
  l2:
    enabled: true
    ttl: 3600
  l3:
    enabled: true
    ttl: 86400
  default-ttl: 1800

spring:
  redis:
    host: localhost
    port: 6379
    password: ${REDIS_PASSWORD:}
    database: 0
```

## 🎯 Cache Usage Patterns

### 1. Ingredient Analysis Caching

```python
# Python
@cached(ttl=3600, key_prefix="ingredient", cache_levels=[CacheLevel.L1, CacheLevel.L2])
def analyze_ingredient(ingredient_name: str) -> Dict[str, Any]:
    # Analysis logic
    pass
```

```java
// Java
@Cacheable(
    keyPrefix = "ingredient",
    ttl = 3600,
    levels = {CacheLevel.L1, CacheLevel.L2},
    strategy = CacheStrategy.WRITE_THROUGH
)
public Optional<IngredientAnalysis> analyzeIngredient(String ingredientName) {
    // Analysis logic
}
```

### 2. External API Response Caching

```python
# Python
def cache_external_api_response(api_name: str, endpoint: str, params: Dict[str, Any], response: Any, ttl: int = 3600) -> bool:
    cache = get_cache()
    if not cache:
        return False
    
    key = f"external_api:{api_name}:{endpoint}:{cache_key(**params)}"
    return cache.set(key, response, ttl)
```

```java
// Java
@Cacheable(
    keyPrefix = "external_api",
    ttl = 3600,
    levels = {CacheLevel.L2, CacheLevel.L3},
    strategy = CacheStrategy.WRITE_THROUGH
)
public ExternalApiResponse getExternalApiData(String apiName, String endpoint, Map<String, Object> params) {
    // API call logic
}
```

### 3. Product Analysis Caching

```python
# Python
def cache_product_analysis(analysis_id: str, analysis: Dict[str, Any], ttl: int = 1800) -> bool:
    cache = get_cache()
    if not cache:
        return False
    
    key = f"product_analysis:{analysis_id}"
    return cache.set(key, analysis, ttl)
```

```java
// Java
@Cacheable(
    keyPrefix = "product_analysis",
    ttl = 1800,
    levels = {CacheLevel.L1, CacheLevel.L2},
    strategy = CacheStrategy.WRITE_BACK
)
public ProductAnalysisResponse analyzeProduct(ProductAnalysisRequest request) {
    // Analysis logic
}
```

## 🔧 Cache Management

### Cache Statistics

```python
# Python
def get_cache_stats() -> Dict[str, Any]:
    cache = get_cache()
    if not cache:
        return {}
    
    return cache.get_stats()
```

```java
// Java
@GetMapping("/cache/stats")
public CacheStats getCacheStats() {
    return cacheService.getStats();
}
```

### Cache Clearing

```python
# Python
def clear_cache_pattern(pattern: str) -> bool:
    cache = get_cache()
    if not cache:
        return False
    
    # Clear by pattern
    return cache.clear_pattern(pattern)
```

```java
// Java
@PostMapping("/cache/clear")
public ResponseEntity<String> clearCache(@RequestParam String pattern) {
    cacheService.clearPattern(pattern);
    return ResponseEntity.ok("Cache cleared");
}
```

### Cache Warming

```python
# Python
def warm_cache():
    """Warm cache with frequently accessed data"""
    # Warm ingredient cache
    common_ingredients = ["Hyaluronic Acid", "Niacinamide", "Retinol", "Vitamin C"]
    for ingredient in common_ingredients:
        analyze_ingredient(ingredient)
    
    # Warm external API cache
    warm_external_api_cache()
```

```java
// Java
@PostConstruct
public void warmCache() {
    // Warm ingredient cache
    List<String> commonIngredients = Arrays.asList(
        "Hyaluronic Acid", "Niacinamide", "Retinol", "Vitamin C"
    );
    
    for (String ingredient : commonIngredients) {
        ingredientService.analyzeIngredient(ingredient);
    }
}
```

## 📈 Performance Optimization

### Cache Hit Rates

| Cache Level | Target Hit Rate | Typical Hit Rate |
|-------------|----------------|------------------|
| L1 Cache    | 80%+           | 85-90%          |
| L2 Cache    | 70%+           | 75-80%          |
| L3 Cache    | 60%+           | 65-70%          |

### Cache Size Optimization

```python
# Python - Dynamic cache sizing
def optimize_cache_size():
    stats = get_cache_stats()
    
    if stats['l1_hit_rate'] < 0.8:
        # Increase L1 cache size
        config.l1_max_size = min(config.l1_max_size * 1.2, 2000)
    
    if stats['l2_hit_rate'] < 0.7:
        # Increase L2 cache TTL
        config.l2_ttl = min(config.l2_ttl * 1.5, 7200)
```

### Memory Usage Monitoring

```python
# Python - Memory monitoring
def monitor_cache_memory():
    cache = get_cache()
    stats = cache.get_stats()
    
    l1_size = stats.get('l1_size', 0)
    l2_connected = stats.get('l2_connected', False)
    
    if l1_size > 800:  # 80% of max size
        logger.warning("L1 cache approaching capacity")
    
    if not l2_connected:
        logger.error("L2 cache (Redis) not connected")
```

## 🚨 Cache Invalidation

### Time-Based Invalidation

```python
# Python - TTL-based invalidation
def set_ingredient_analysis(ingredient: str, analysis: Dict[str, Any], ttl: int = 3600) -> bool:
    cache = get_cache()
    if not cache:
        return False
    
    key = f"ingredient:{ingredient}"
    return cache.set(key, analysis, ttl)
```

### Event-Based Invalidation

```python
# Python - Event-based invalidation
def invalidate_ingredient_cache(ingredient: str):
    """Invalidate cache when ingredient data is updated"""
    cache = get_cache()
    if not cache:
        return
    
    # Clear specific ingredient
    cache.delete(f"ingredient:{ingredient}")
    
    # Clear related caches
    cache.clear_pattern(f"*{ingredient}*")
```

### Manual Invalidation

```java
// Java - Manual invalidation
@PostMapping("/cache/invalidate")
public ResponseEntity<String> invalidateCache(
    @RequestParam String key,
    @RequestParam(required = false) String pattern
) {
    if (pattern != null) {
        cacheService.clearPattern(pattern);
    } else {
        cacheService.delete(key);
    }
    
    return ResponseEntity.ok("Cache invalidated");
}
```

## 🔍 Cache Monitoring

### Health Checks

```python
# Python - Cache health check
def check_cache_health() -> Dict[str, Any]:
    health = {
        "l1_cache": {"status": "healthy", "size": 0},
        "l2_cache": {"status": "healthy", "connected": False},
        "l3_cache": {"status": "healthy", "connected": False}
    }
    
    cache = get_cache()
    if cache:
        stats = cache.get_stats()
        health["l1_cache"]["size"] = stats.get("l1_size", 0)
        health["l2_cache"]["connected"] = stats.get("l2_connected", False)
        health["l3_cache"]["connected"] = stats.get("l3_enabled", False)
    
    return health
```

### Metrics Collection

```python
# Python - Metrics collection
def collect_cache_metrics() -> Dict[str, Any]:
    cache = get_cache()
    if not cache:
        return {}
    
    stats = cache.get_stats()
    return {
        "cache_hits": stats.get("hits", 0),
        "cache_misses": stats.get("misses", 0),
        "cache_hit_rate": stats.get("hit_rate", 0.0),
        "l1_hits": stats.get("l1_hits", 0),
        "l2_hits": stats.get("l2_hits", 0),
        "l3_hits": stats.get("l3_hits", 0),
        "cache_sets": stats.get("sets", 0),
        "cache_deletes": stats.get("deletes", 0),
        "cache_errors": stats.get("errors", 0)
    }
```

## 🛠️ Troubleshooting

### Common Issues

1. **High Memory Usage**
   - Reduce L1 cache size
   - Implement cache eviction
   - Monitor cache hit rates

2. **Redis Connection Issues**
   - Check Redis server status
   - Verify connection configuration
   - Implement connection pooling

3. **Cache Inconsistency**
   - Use write-through strategy
   - Implement cache invalidation
   - Monitor cache TTL

4. **Low Hit Rates**
   - Analyze cache patterns
   - Adjust TTL values
   - Implement cache warming

### Debug Commands

```bash
# Check Redis status
redis-cli ping

# Check Redis memory usage
redis-cli info memory

# Check Redis keys
redis-cli keys "*"

# Clear Redis cache
redis-cli flushdb
```

## 📚 Best Practices

### 1. Cache Key Design
- Use descriptive prefixes
- Include version numbers
- Avoid special characters
- Keep keys short but meaningful

### 2. TTL Configuration
- Set appropriate TTL for each data type
- Use shorter TTL for frequently changing data
- Use longer TTL for stable data
- Monitor cache hit rates

### 3. Cache Warming
- Pre-load frequently accessed data
- Implement background cache warming
- Monitor cache performance
- Adjust warming strategies

### 4. Error Handling
- Implement fallback mechanisms
- Log cache errors
- Monitor cache health
- Implement circuit breakers

### 5. Security
- Encrypt sensitive cached data
- Implement access controls
- Monitor cache usage
- Implement audit logging

---

**Last Updated**: December 2024  
**Version**: 3.0.1  
**Maintainer**: CTO Team
