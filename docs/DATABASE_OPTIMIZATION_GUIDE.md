# Database Optimization Guide

## Overview

This guide covers the comprehensive database optimization strategy implemented for MommyShops, including connection pooling, query optimization, indexing, and performance monitoring.

## Architecture

### Python Backend (FastAPI + SQLAlchemy)
- **Connection Pooling**: QueuePool with configurable size and overflow
- **Query Optimization**: Advanced query patterns with monitoring
- **Indexing**: Automated index creation for common queries
- **Caching**: Multi-level caching with Redis integration

### Java Backend (Spring Boot + JPA)
- **Connection Pooling**: HikariCP with optimized settings
- **JPA Optimization**: Batch operations, second-level cache
- **Query Optimization**: Native query optimization
- **Indexing**: Automated index creation and analysis

## Configuration

### Python Configuration

```python
# Database optimization settings
DATABASE_URL=postgresql://user:password@host:port/dbname
DB_USERNAME=mommyshops
DB_PASSWORD=secure_password

# Connection pooling
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Query optimization
DB_OPTIMIZATION_LEVEL=intermediate
DB_QUERY_TIMEOUT=30
DB_SLOW_QUERY_THRESHOLD=1.0

# Caching
DB_ENABLE_QUERY_CACHE=true
DB_QUERY_CACHE_SIZE=1000
DB_QUERY_CACHE_TTL=300
```

### Java Configuration

```properties
# HikariCP settings
spring.datasource.hikari.maximum-pool-size=10
spring.datasource.hikari.minimum-idle=5
spring.datasource.hikari.connection-timeout=30000
spring.datasource.hikari.idle-timeout=600000
spring.datasource.hikari.max-lifetime=1800000

# JPA optimization
spring.jpa.hibernate.jdbc.batch_size=25
spring.jpa.hibernate.order_inserts=true
spring.jpa.hibernate.order_updates=true
spring.jpa.hibernate.jdbc.batch_versioned_data=true
spring.jpa.hibernate.connection.provider_disables_autocommit=true

# Caching
spring.jpa.hibernate.cache.use_second_level_cache=true
spring.jpa.hibernate.cache.use_query_cache=true
spring.jpa.hibernate.cache.region.factory_class=org.hibernate.cache.jcache.JCacheRegionFactory
```

## Indexing Strategy

### Core Indexes

1. **User Indexes**
   - `idx_users_email` - Email lookup
   - `idx_users_created_at` - Time-based queries
   - `idx_users_active` - Active user filtering

2. **Product Analysis Indexes**
   - `idx_product_analysis_user_id` - User-specific analysis
   - `idx_product_analysis_created_at` - Time-based analysis
   - `idx_product_analysis_eco_score` - Eco score filtering
   - `idx_product_analysis_suitability` - Suitability filtering

3. **Ingredient Analysis Indexes**
   - `idx_ingredient_analysis_name` - Ingredient name lookup
   - `idx_ingredient_analysis_risk_level` - Risk level filtering
   - `idx_ingredient_analysis_eco_score` - Eco score filtering
   - `idx_ingredient_analysis_created_at` - Time-based queries

4. **Composite Indexes**
   - `idx_product_analysis_user_created` - User + time queries
   - `idx_ingredient_analysis_name_risk` - Name + risk queries
   - `idx_analysis_results_analysis_ingredient` - Analysis + ingredient queries

### Index Creation

```python
# Python - Automated index creation
from core.database_optimization import DatabaseOptimizer, DatabaseConfig

config = DatabaseConfig(
    url="postgresql://user:password@host:port/dbname",
    pool_size=10,
    max_overflow=20,
    optimization_level=QueryOptimizationLevel.ADVANCED
)

optimizer = DatabaseOptimizer(config)
optimizer.create_indexes()
```

```java
// Java - Automated index creation
@Autowired
private DatabaseIndexingService indexingService;

@PostConstruct
public void initializeIndexes() {
    indexingService.createOptimizedIndexes();
    indexingService.analyzeTables();
}
```

## Query Optimization

### Python Query Patterns

```python
# Optimized user queries
@cacheable(ttl=300)
async def get_user_analysis_history(user_id: int, limit: int = 50):
    query = select(ProductAnalysis)\
        .where(ProductAnalysis.user_id == user_id)\
        .order_by(ProductAnalysis.created_at.desc())\
        .limit(limit)
    
    return await session.execute(query)

# Optimized ingredient queries
@cacheable(ttl=600)
async def search_ingredients(name: str, risk_level: str = None):
    query = select(IngredientAnalysis)\
        .where(IngredientAnalysis.name.ilike(f"%{name}%"))
    
    if risk_level:
        query = query.where(IngredientAnalysis.risk_level == risk_level)
    
    return await session.execute(query)
```

### Java Query Patterns

```java
// Optimized JPA queries
@Query("SELECT pa FROM ProductAnalysis pa WHERE pa.user.id = :userId ORDER BY pa.createdAt DESC")
@QueryHints({
    @QueryHint(name = "org.hibernate.cacheable", value = "true"),
    @QueryHint(name = "org.hibernate.readOnly", value = "true")
})
List<ProductAnalysis> findUserAnalysisHistory(@Param("userId") Long userId, Pageable pageable);

// Batch operations
@Modifying
@Query("UPDATE IngredientAnalysis ia SET ia.ecoScore = :ecoScore WHERE ia.id IN :ids")
@QueryHints(@QueryHint(name = "org.hibernate.jdbc.batch_size", value = "25"))
int updateEcoScores(@Param("ecoScore") Double ecoScore, @Param("ids") List<Long> ids);
```

## Performance Monitoring

### Health Endpoints

#### Python Endpoints
- `GET /api/database/health` - Database health status
- `GET /api/database/stats` - Performance statistics
- `POST /api/database/optimize` - Run optimization
- `GET /api/database/slow-queries` - Slow query analysis
- `GET /api/database/connection-pool` - Connection pool status

#### Java Endpoints
- `GET /api/database/health` - Database health status
- `GET /api/database/stats` - Performance statistics
- `POST /api/database/optimize` - Run optimization

### Monitoring Metrics

1. **Connection Pool Metrics**
   - Active connections
   - Idle connections
   - Connection wait time
   - Connection errors

2. **Query Performance Metrics**
   - Query execution time
   - Slow query count
   - Cache hit rate
   - Query frequency

3. **Index Usage Metrics**
   - Index usage statistics
   - Index size
   - Index maintenance time

## Best Practices

### 1. Connection Pooling
- Set appropriate pool size based on concurrent users
- Monitor connection usage patterns
- Use connection validation
- Implement connection timeout

### 2. Query Optimization
- Use specific column selection
- Implement proper pagination
- Use appropriate JOIN types
- Avoid N+1 queries

### 3. Indexing
- Create indexes for frequently queried columns
- Use composite indexes for multi-column queries
- Monitor index usage
- Regular index maintenance

### 4. Caching
- Implement query result caching
- Use appropriate cache TTL
- Monitor cache hit rates
- Implement cache invalidation

### 5. Monitoring
- Regular performance monitoring
- Slow query analysis
- Connection pool monitoring
- Index usage analysis

## Troubleshooting

### Common Issues

1. **Connection Pool Exhaustion**
   - Increase pool size
   - Check for connection leaks
   - Optimize query performance

2. **Slow Queries**
   - Analyze query execution plans
   - Create appropriate indexes
   - Optimize query patterns

3. **High Memory Usage**
   - Optimize connection pool settings
   - Implement query result caching
   - Use pagination for large result sets

### Performance Tuning

1. **Database Level**
   - Optimize PostgreSQL settings
   - Configure shared_buffers
   - Set appropriate work_mem

2. **Application Level**
   - Implement connection pooling
   - Use prepared statements
   - Implement query caching

3. **Infrastructure Level**
   - Use SSD storage
   - Optimize network configuration
   - Implement load balancing

## Maintenance

### Regular Tasks

1. **Daily**
   - Monitor slow queries
   - Check connection pool status
   - Review error logs

2. **Weekly**
   - Analyze query performance
   - Review index usage
   - Update statistics

3. **Monthly**
   - Full database optimization
   - Index maintenance
   - Performance review

### Automation

```bash
# Automated optimization script
#!/bin/bash
curl -X POST http://localhost:8000/api/database/optimize
curl -X POST http://localhost:8080/api/database/optimize
```

## Security Considerations

1. **Connection Security**
   - Use encrypted connections
   - Implement connection authentication
   - Monitor connection attempts

2. **Query Security**
   - Use prepared statements
   - Implement query validation
   - Monitor for SQL injection

3. **Data Security**
   - Implement data encryption
   - Use secure connection strings
   - Monitor data access patterns

## Conclusion

This database optimization strategy provides a comprehensive approach to improving MommyShops database performance through connection pooling, query optimization, indexing, and monitoring. Regular maintenance and monitoring ensure optimal performance over time.
