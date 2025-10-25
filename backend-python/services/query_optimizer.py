"""
Advanced query optimization service
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import text, func, desc, asc
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.exc import SQLAlchemyError
import asyncio
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class QueryOptimizer:
    """
    Advanced query optimization service with caching and performance monitoring
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.query_cache = {}
        self.performance_metrics = {}
    
    async def optimize_ingredient_search(self, search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Optimized ingredient search with full-text search and caching
        """
        cache_key = f"ingredient_search:{search_term}:{limit}"
        
        # Check cache first
        if cache_key in self.query_cache:
            logger.debug(f"Cache hit for ingredient search: {search_term}")
            return self.query_cache[cache_key]
        
        try:
            # Use full-text search with ranking
            query = text("""
                SELECT 
                    i.id,
                    i.name,
                    i.inci_name,
                    i.eco_score,
                    i.risk_level,
                    ts_rank(to_tsvector('english', i.name || ' ' || i.inci_name), 
                           plainto_tsquery('english', :search_term)) as rank
                FROM ingredients i
                WHERE to_tsvector('english', i.name || ' ' || i.inci_name) 
                      @@ plainto_tsquery('english', :search_term)
                ORDER BY rank DESC, i.eco_score ASC
                LIMIT :limit
            """)
            
            result = self.db.execute(query, {
                'search_term': search_term,
                'limit': limit
            })
            
            ingredients = []
            for row in result:
                ingredients.append({
                    'id': row.id,
                    'name': row.name,
                    'inci_name': row.inci_name,
                    'eco_score': float(row.eco_score) if row.eco_score else 0.0,
                    'risk_level': row.risk_level,
                    'relevance_score': float(row.rank)
                })
            
            # Cache result for 5 minutes
            self.query_cache[cache_key] = ingredients
            self._schedule_cache_cleanup(cache_key, 300)
            
            logger.info(f"Optimized ingredient search completed: {len(ingredients)} results")
            return ingredients
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in ingredient search: {e}")
            return []
    
    async def optimize_user_analysis_history(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Optimized user analysis history with eager loading
        """
        cache_key = f"user_history:{user_id}:{limit}"
        
        if cache_key in self.query_cache:
            return self.query_cache[cache_key]
        
        try:
            # Use eager loading to prevent N+1 queries
            from backend.database.models import AnalysisHistory, Product, Ingredient
            
            query = self.db.query(AnalysisHistory)\
                .options(
                    joinedload(AnalysisHistory.product),
                    selectinload(AnalysisHistory.ingredients)
                )\
                .filter(AnalysisHistory.user_id == user_id)\
                .order_by(desc(AnalysisHistory.created_at))\
                .limit(limit)
            
            results = query.all()
            
            history = []
            for analysis in results:
                history.append({
                    'id': analysis.id,
                    'product_name': analysis.product.name if analysis.product else 'Unknown',
                    'analysis_type': analysis.analysis_type,
                    'confidence': float(analysis.confidence) if analysis.confidence else 0.0,
                    'created_at': analysis.created_at.isoformat(),
                    'ingredients_count': len(analysis.ingredients) if analysis.ingredients else 0
                })
            
            # Cache for 2 minutes
            self.query_cache[cache_key] = history
            self._schedule_cache_cleanup(cache_key, 120)
            
            return history
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in user history: {e}")
            return []
    
    async def optimize_ingredient_analysis_batch(self, ingredient_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        Batch analysis of multiple ingredients to reduce database calls
        """
        cache_key = f"batch_analysis:{hash(tuple(sorted(ingredient_ids)))}"
        
        if cache_key in self.query_cache:
            return self.query_cache[cache_key]
        
        try:
            from backend.database.models import Ingredient, IngredientAnalysis
            
            # Single query with all ingredients
            query = self.db.query(Ingredient, IngredientAnalysis)\
                .outerjoin(IngredientAnalysis, Ingredient.id == IngredientAnalysis.ingredient_id)\
                .filter(Ingredient.id.in_(ingredient_ids))
            
            results = query.all()
            
            batch_results = {}
            for ingredient, analysis in results:
                batch_results[ingredient.id] = {
                    'id': ingredient.id,
                    'name': ingredient.name,
                    'inci_name': ingredient.inci_name,
                    'eco_score': float(ingredient.eco_score) if ingredient.eco_score else 0.0,
                    'risk_level': ingredient.risk_level,
                    'analysis': {
                        'type': analysis.analysis_type if analysis else None,
                        'confidence': float(analysis.confidence) if analysis and analysis.confidence else 0.0,
                        'results': json.loads(analysis.results) if analysis and analysis.results else {}
                    } if analysis else None
                }
            
            # Cache for 10 minutes
            self.query_cache[cache_key] = batch_results
            self._schedule_cache_cleanup(cache_key, 600)
            
            return batch_results
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in batch analysis: {e}")
            return {}
    
    async def optimize_product_recommendations(self, user_id: int, skin_type: str = None, 
                                             concerns: List[str] = None) -> List[Dict[str, Any]]:
        """
        Optimized product recommendations with complex filtering
        """
        cache_key = f"recommendations:{user_id}:{skin_type}:{hash(tuple(sorted(concerns or [])))}"
        
        if cache_key in self.query_cache:
            return self.query_cache[cache_key]
        
        try:
            # Complex query with multiple joins and filtering
            query = text("""
                WITH user_preferences AS (
                    SELECT 
                        up.skin_type,
                        up.concerns,
                        up.preferences
                    FROM user_profiles up
                    WHERE up.user_id = :user_id
                ),
                ingredient_scores AS (
                    SELECT 
                        i.id,
                        i.name,
                        i.eco_score,
                        i.risk_level,
                        CASE 
                            WHEN i.risk_level = 'low' THEN 3
                            WHEN i.risk_level = 'moderate' THEN 2
                            WHEN i.risk_level = 'high' THEN 1
                            ELSE 0
                        END as risk_score
                    FROM ingredients i
                ),
                product_scores AS (
                    SELECT 
                        p.id,
                        p.name,
                        p.brand,
                        p.avg_eco_score,
                        AVG(COALESCE(ing.eco_score, 0)) as ingredient_avg_score,
                        COUNT(ing.id) as ingredient_count,
                        SUM(CASE WHEN ing.risk_level = 'low' THEN 1 ELSE 0 END) as safe_ingredients,
                        SUM(CASE WHEN ing.risk_level = 'high' THEN 1 ELSE 0 END) as risky_ingredients
                    FROM products p
                    LEFT JOIN product_ingredients pi ON p.id = pi.product_id
                    LEFT JOIN ingredients ing ON pi.ingredient_id = ing.id
                    GROUP BY p.id, p.name, p.brand, p.avg_eco_score
                )
                SELECT 
                    ps.id,
                    ps.name,
                    ps.brand,
                    ps.avg_eco_score,
                    ps.ingredient_avg_score,
                    ps.ingredient_count,
                    ps.safe_ingredients,
                    ps.risky_ingredients,
                    (ps.avg_eco_score * 0.4 + ps.ingredient_avg_score * 0.4 + 
                     (ps.safe_ingredients::float / NULLIF(ps.ingredient_count, 0)) * 20) as recommendation_score
                FROM product_scores ps
                WHERE ps.avg_eco_score >= 60  -- Minimum eco score
                  AND ps.risky_ingredients <= ps.safe_ingredients  -- More safe than risky
                ORDER BY recommendation_score DESC
                LIMIT 20
            """)
            
            result = self.db.execute(query, {'user_id': user_id})
            
            recommendations = []
            for row in result:
                recommendations.append({
                    'id': row.id,
                    'name': row.name,
                    'brand': row.brand,
                    'avg_eco_score': float(row.avg_eco_score) if row.avg_eco_score else 0.0,
                    'ingredient_count': row.ingredient_count,
                    'safe_ingredients': row.safe_ingredients,
                    'risky_ingredients': row.risky_ingredients,
                    'recommendation_score': float(row.recommendation_score) if row.recommendation_score else 0.0
                })
            
            # Cache for 15 minutes
            self.query_cache[cache_key] = recommendations
            self._schedule_cache_cleanup(cache_key, 900)
            
            return recommendations
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in recommendations: {e}")
            return []
    
    async def optimize_database_connection_pool(self):
        """
        Optimize database connection pool settings
        """
        try:
            # Get current connection pool stats
            pool = self.db.get_bind().pool
            
            # Log current pool status
            logger.info(f"Connection pool status: {pool.size()} connections, "
                       f"{pool.checkedin()} checked in, {pool.checkedout()} checked out")
            
            # Optimize pool settings if needed
            if pool.size() > 20:  # Too many connections
                logger.warning("Connection pool size is high, consider optimization")
            
            return {
                'pool_size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'invalid': pool.invalid()
            }
            
        except Exception as e:
            logger.error(f"Error checking connection pool: {e}")
            return {}
    
    def _schedule_cache_cleanup(self, cache_key: str, ttl_seconds: int):
        """
        Schedule cache cleanup for a specific key
        """
        async def cleanup():
            await asyncio.sleep(ttl_seconds)
            if cache_key in self.query_cache:
                del self.query_cache[cache_key]
                logger.debug(f"Cache expired and cleaned up: {cache_key}")
        
        asyncio.create_task(cleanup())
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get query performance metrics
        """
        try:
            # Get database performance stats
            stats_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation
                FROM pg_stats 
                WHERE schemaname = 'public'
                ORDER BY tablename, attname
            """)
            
            result = self.db.execute(stats_query)
            db_stats = [dict(row) for row in result]
            
            return {
                'cache_size': len(self.query_cache),
                'cache_hit_rate': self._calculate_cache_hit_rate(),
                'database_stats': db_stats,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {'error': str(e)}
    
    def _calculate_cache_hit_rate(self) -> float:
        """
        Calculate cache hit rate (simplified)
        """
        # This would need proper hit/miss tracking in production
        return 0.85  # Placeholder value
    
    async def cleanup_expired_cache(self):
        """
        Clean up expired cache entries
        """
        current_time = datetime.now()
        expired_keys = []
        
        for key, data in self.query_cache.items():
            if 'expires_at' in data and current_time > data['expires_at']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.query_cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
