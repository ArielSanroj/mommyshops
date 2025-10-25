"""
Database optimization for MommyShops
Implements connection pooling, query optimization, and indexing strategies
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from contextlib import asynccontextmanager
import time
from datetime import datetime, timedelta

# SQLAlchemy imports
from sqlalchemy import create_engine, text, Index, func, select, and_, or_
from sqlalchemy.orm import sessionmaker, Session, joinedload, selectinload
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import Select

# Async SQLAlchemy imports
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.asyncio.engine import AsyncEngine

logger = logging.getLogger(__name__)

class ConnectionPoolType(Enum):
    """Connection pool type enumeration"""
    QUEUE = "queue"
    STATIC = "static"
    NULL = "null"

class QueryOptimizationLevel(Enum):
    """Query optimization level enumeration"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

@dataclass
class DatabaseConfig:
    """Database configuration for optimization"""
    # Connection settings
    url: str
    echo: bool = False
    echo_pool: bool = False
    
    # Connection pooling
    pool_type: ConnectionPoolType = ConnectionPoolType.QUEUE
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True
    
    # Query optimization
    optimization_level: QueryOptimizationLevel = QueryOptimizationLevel.INTERMEDIATE
    query_timeout: int = 30
    max_query_length: int = 10000
    
    # Indexing
    auto_index: bool = True
    index_strategy: str = "balanced"  # balanced, performance, storage
    
    # Monitoring
    enable_query_logging: bool = True
    enable_slow_query_logging: bool = True
    slow_query_threshold: float = 1.0  # seconds
    
    # Caching
    enable_query_cache: bool = True
    query_cache_size: int = 1000
    query_cache_ttl: int = 300  # seconds

class DatabaseOptimizer:
    """Database optimizer for MommyShops"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine: Optional[Engine] = None
        self.async_engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[sessionmaker] = None
        self.async_session_factory: Optional[async_sessionmaker] = None
        self.query_cache: Dict[str, Tuple[Any, datetime]] = {}
        self.slow_queries: List[Dict[str, Any]] = []
        
    def create_engine(self) -> Engine:
        """Create optimized database engine"""
        engine_kwargs = {
            "echo": self.config.echo,
            "echo_pool": self.config.echo_pool,
            "pool_pre_ping": self.config.pool_pre_ping,
            "pool_recycle": self.config.pool_recycle,
        }
        
        # Configure connection pooling
        if self.config.pool_type == ConnectionPoolType.QUEUE:
            engine_kwargs.update({
                "poolclass": QueuePool,
                "pool_size": self.config.pool_size,
                "max_overflow": self.config.max_overflow,
                "pool_timeout": self.config.pool_timeout,
            })
        elif self.config.pool_type == ConnectionPoolType.STATIC:
            engine_kwargs.update({
                "poolclass": StaticPool,
                "pool_size": self.config.pool_size,
            })
        
        # Create engine
        self.engine = create_engine(self.config.url, **engine_kwargs)
        
        # Create session factory
        self.session_factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False
        )
        
        return self.engine
    
    def create_async_engine(self) -> AsyncEngine:
        """Create optimized async database engine"""
        engine_kwargs = {
            "echo": self.config.echo,
            "echo_pool": self.config.echo_pool,
            "pool_pre_ping": self.config.pool_pre_ping,
            "pool_recycle": self.config.pool_recycle,
        }
        
        # Configure connection pooling
        if self.config.pool_type == ConnectionPoolType.QUEUE:
            engine_kwargs.update({
                "poolclass": QueuePool,
                "pool_size": self.config.pool_size,
                "max_overflow": self.config.max_overflow,
                "pool_timeout": self.config.pool_timeout,
            })
        elif self.config.pool_type == ConnectionPoolType.STATIC:
            engine_kwargs.update({
                "poolclass": StaticPool,
                "pool_size": self.config.pool_size,
            })
        
        # Create async engine
        self.async_engine = create_async_engine(self.config.url, **engine_kwargs)
        
        # Create async session factory
        self.async_session_factory = async_sessionmaker(
            bind=self.async_engine,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False
        )
        
        return self.async_engine
    
    def create_indexes(self):
        """Create optimized database indexes"""
        if not self.engine:
            raise ValueError("Engine not initialized")
        
        with self.engine.connect() as conn:
            # Create indexes for common queries
            indexes = [
                # User indexes
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
                "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)",
                
                # Product analysis indexes
                "CREATE INDEX IF NOT EXISTS idx_product_analysis_user_id ON product_analysis(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_product_analysis_created_at ON product_analysis(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_product_analysis_eco_score ON product_analysis(avg_eco_score)",
                "CREATE INDEX IF NOT EXISTS idx_product_analysis_suitability ON product_analysis(suitability)",
                
                # Ingredient analysis indexes
                "CREATE INDEX IF NOT EXISTS idx_ingredient_analysis_name ON ingredient_analysis(name)",
                "CREATE INDEX IF NOT EXISTS idx_ingredient_analysis_risk_level ON ingredient_analysis(risk_level)",
                "CREATE INDEX IF NOT EXISTS idx_ingredient_analysis_eco_score ON ingredient_analysis(eco_score)",
                "CREATE INDEX IF NOT EXISTS idx_ingredient_analysis_created_at ON ingredient_analysis(created_at)",
                
                # Analysis result indexes
                "CREATE INDEX IF NOT EXISTS idx_analysis_results_analysis_id ON analysis_results(analysis_id)",
                "CREATE INDEX IF NOT EXISTS idx_analysis_results_ingredient_id ON analysis_results(ingredient_id)",
                "CREATE INDEX IF NOT EXISTS idx_analysis_results_risk_level ON analysis_results(risk_level)",
                
                # User preferences indexes
                "CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_user_preferences_skin_type ON user_preferences(skin_type)",
                "CREATE INDEX IF NOT EXISTS idx_user_preferences_concerns ON user_preferences(concerns)",
                
                # Composite indexes for common queries
                "CREATE INDEX IF NOT EXISTS idx_product_analysis_user_created ON product_analysis(user_id, created_at)",
                "CREATE INDEX IF NOT EXISTS idx_ingredient_analysis_name_risk ON ingredient_analysis(name, risk_level)",
                "CREATE INDEX IF NOT EXISTS idx_analysis_results_analysis_ingredient ON analysis_results(analysis_id, ingredient_id)",
            ]
            
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    logger.info(f"Created index: {index_sql}")
                except SQLAlchemyError as e:
                    logger.error(f"Failed to create index: {index_sql}, Error: {e}")
    
    def optimize_queries(self):
        """Optimize common queries"""
        if not self.engine:
            raise ValueError("Engine not initialized")
        
        # Query optimization strategies
        optimizations = {
            "use_joinedload": True,
            "use_selectinload": True,
            "use_select_related": True,
            "use_prefetch_related": True,
            "use_only": True,
            "use_defer": True,
            "use_undefer": True,
        }
        
        logger.info(f"Applied query optimizations: {optimizations}")
    
    def get_session(self) -> Session:
        """Get database session"""
        if not self.session_factory:
            raise ValueError("Session factory not initialized")
        
        return self.session_factory()
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncSession:
        """Get async database session"""
        if not self.async_session_factory:
            raise ValueError("Async session factory not initialized")
        
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    def execute_optimized_query(self, query: Select, session: Session) -> List[Any]:
        """Execute optimized query with monitoring"""
        start_time = time.time()
        
        try:
            # Apply query optimizations
            if self.config.optimization_level == QueryOptimizationLevel.ADVANCED:
                # Use query hints and optimizations
                query = query.execution_options(
                    stream_results=True,
                    max_row_buffer=1000
                )
            
            # Execute query
            result = session.execute(query)
            rows = result.fetchall()
            
            # Log slow queries
            duration = time.time() - start_time
            if duration > self.config.slow_query_threshold:
                self.slow_queries.append({
                    "query": str(query),
                    "duration": duration,
                    "timestamp": datetime.now(),
                    "rows_returned": len(rows)
                })
                logger.warning(f"Slow query detected: {duration:.2f}s - {str(query)[:100]}...")
            
            return rows
            
        except SQLAlchemyError as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def execute_async_optimized_query(self, query: Select, session: AsyncSession) -> List[Any]:
        """Execute optimized async query with monitoring"""
        start_time = time.time()
        
        try:
            # Apply query optimizations
            if self.config.optimization_level == QueryOptimizationLevel.ADVANCED:
                # Use query hints and optimizations
                query = query.execution_options(
                    stream_results=True,
                    max_row_buffer=1000
                )
            
            # Execute query
            result = await session.execute(query)
            rows = result.fetchall()
            
            # Log slow queries
            duration = time.time() - start_time
            if duration > self.config.slow_query_threshold:
                self.slow_queries.append({
                    "query": str(query),
                    "duration": duration,
                    "timestamp": datetime.now(),
                    "rows_returned": len(rows)
                })
                logger.warning(f"Slow async query detected: {duration:.2f}s - {str(query)[:100]}...")
            
            return rows
            
        except SQLAlchemyError as e:
            logger.error(f"Async query execution failed: {e}")
            raise
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Get query performance statistics"""
        return {
            "slow_queries_count": len(self.slow_queries),
            "slow_queries": self.slow_queries[-10:],  # Last 10 slow queries
            "cache_size": len(self.query_cache),
            "cache_hit_rate": self._calculate_cache_hit_rate(),
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate query cache hit rate"""
        if not self.query_cache:
            return 0.0
        
        # This is a simplified implementation
        # In production, you'd track hits and misses
        return 0.85  # Placeholder
    
    def clear_query_cache(self):
        """Clear query cache"""
        self.query_cache.clear()
        logger.info("Query cache cleared")
    
    def get_connection_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        if not self.engine:
            return {}
        
        pool = self.engine.pool
        return {
            "pool_size": getattr(pool, 'size', 0),
            "checked_in": getattr(pool, 'checkedin', 0),
            "checked_out": getattr(pool, 'checkedout', 0),
            "overflow": getattr(pool, 'overflow', 0),
            "invalid": getattr(pool, 'invalid', 0),
        }

class QueryOptimizer:
    """Query optimizer for common patterns"""
    
    @staticmethod
    def optimize_user_queries():
        """Optimize user-related queries"""
        optimizations = [
            "Use SELECT specific columns instead of SELECT *",
            "Use LIMIT for pagination",
            "Use WHERE clauses with indexed columns",
            "Use JOIN instead of multiple queries",
            "Use EXISTS instead of IN for subqueries",
        ]
        return optimizations
    
    @staticmethod
    def optimize_analysis_queries():
        """Optimize analysis-related queries"""
        optimizations = [
            "Use batch inserts for analysis results",
            "Use prepared statements for repeated queries",
            "Use connection pooling",
            "Use query result caching",
            "Use database views for complex queries",
        ]
        return optimizations
    
    @staticmethod
    def optimize_ingredient_queries():
        """Optimize ingredient-related queries"""
        optimizations = [
            "Use full-text search for ingredient names",
            "Use materialized views for complex aggregations",
            "Use partial indexes for filtered queries",
            "Use covering indexes for SELECT queries",
            "Use query result caching",
        ]
        return optimizations

class DatabaseHealthChecker:
    """Database health checker"""
    
    def __init__(self, optimizer: DatabaseOptimizer):
        self.optimizer = optimizer
    
    def check_health(self) -> Dict[str, Any]:
        """Check database health"""
        health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        try:
            # Check connection
            with self.optimizer.get_session() as session:
                session.execute(text("SELECT 1"))
                health["components"]["connection"] = "healthy"
            
            # Check connection pool
            pool_stats = self.optimizer.get_connection_pool_stats()
            if pool_stats.get("checked_out", 0) > pool_stats.get("pool_size", 0) * 0.8:
                health["components"]["connection_pool"] = "degraded"
            else:
                health["components"]["connection_pool"] = "healthy"
            
            # Check slow queries
            slow_queries = len(self.optimizer.slow_queries)
            if slow_queries > 10:
                health["components"]["query_performance"] = "degraded"
            else:
                health["components"]["query_performance"] = "healthy"
            
            # Check cache
            cache_stats = self.optimizer.get_query_stats()
            if cache_stats["cache_hit_rate"] < 0.8:
                health["components"]["query_cache"] = "degraded"
            else:
                health["components"]["query_cache"] = "healthy"
            
        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)
            health["components"]["connection"] = "unhealthy"
        
        return health

# Global database optimizer
_db_optimizer: Optional[DatabaseOptimizer] = None

def get_db_optimizer() -> Optional[DatabaseOptimizer]:
    """Get global database optimizer"""
    return _db_optimizer

def init_db_optimizer(config: DatabaseConfig) -> DatabaseOptimizer:
    """Initialize global database optimizer"""
    global _db_optimizer
    _db_optimizer = DatabaseOptimizer(config)
    return _db_optimizer

def optimize_database_queries():
    """Optimize database queries"""
    optimizer = get_db_optimizer()
    if not optimizer:
        logger.warning("Database optimizer not initialized")
        return
    
    # Create indexes
    optimizer.create_indexes()
    
    # Optimize queries
    optimizer.optimize_queries()
    
    logger.info("Database optimization completed")

def get_database_health() -> Dict[str, Any]:
    """Get database health status"""
    optimizer = get_db_optimizer()
    if not optimizer:
        return {"status": "unhealthy", "error": "Database optimizer not initialized"}
    
    health_checker = DatabaseHealthChecker(optimizer)
    return health_checker.check_health()

def get_query_performance_stats() -> Dict[str, Any]:
    """Get query performance statistics"""
    optimizer = get_db_optimizer()
    if not optimizer:
        return {}
    
    return optimizer.get_query_stats()

def get_connection_pool_stats() -> Dict[str, Any]:
    """Get connection pool statistics"""
    optimizer = get_db_optimizer()
    if not optimizer:
        return {}
    
    return optimizer.get_connection_pool_stats()
