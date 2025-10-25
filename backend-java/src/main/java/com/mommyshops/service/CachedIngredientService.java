package com.mommyshops.service;

import com.mommyshops.cache.Cacheable;
import com.mommyshops.cache.CacheLevel;
import com.mommyshops.cache.CacheStrategy;
import com.mommyshops.cache.MultiLevelCacheService;
import com.mommyshops.analysis.domain.IngredientAnalysis;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

/**
 * Cached ingredient service with multi-level caching
 */
@Service
public class CachedIngredientService {

    @Autowired
    private MultiLevelCacheService cacheService;

    @Autowired
    private IngredientService ingredientService;

    /**
     * Get ingredient analysis with caching
     */
    @Cacheable(
        keyPrefix = "ingredient",
        ttl = 3600, // 1 hour
        levels = {CacheLevel.L1, CacheLevel.L2},
        strategy = CacheStrategy.WRITE_THROUGH
    )
    public Optional<IngredientAnalysis> getIngredientAnalysis(String ingredientName) {
        // Try cache first
        Optional<IngredientAnalysis> cached = cacheService.get(
            "ingredient:" + ingredientName, 
            IngredientAnalysis.class
        );
        
        if (cached.isPresent()) {
            return cached;
        }
        
        // Get from service
        Optional<IngredientAnalysis> analysis = ingredientService.analyzeIngredient(ingredientName);
        
        // Cache the result
        if (analysis.isPresent()) {
            cacheService.set("ingredient:" + ingredientName, analysis.get());
        }
        
        return analysis;
    }

    /**
     * Get batch ingredient analysis with caching
     */
    @Cacheable(
        keyPrefix = "ingredients_batch",
        ttl = 1800, // 30 minutes
        levels = {CacheLevel.L1, CacheLevel.L2},
        strategy = CacheStrategy.WRITE_THROUGH
    )
    public List<IngredientAnalysis> getBatchIngredientAnalysis(List<String> ingredientNames) {
        // Try cache first
        String cacheKey = "ingredients_batch:" + String.join(",", ingredientNames);
        Optional<List<IngredientAnalysis>> cached = cacheService.get(cacheKey, List.class);
        
        if (cached.isPresent()) {
            return cached.get();
        }
        
        // Get from service
        List<IngredientAnalysis> analyses = ingredientService.analyzeIngredientsBatch(ingredientNames);
        
        // Cache the result
        cacheService.set(cacheKey, analyses);
        
        return analyses;
    }

    /**
     * Get ingredient alternatives with caching
     */
    @Cacheable(
        keyPrefix = "alternatives",
        ttl = 7200, // 2 hours
        levels = {CacheLevel.L1, CacheLevel.L2, CacheLevel.L3},
        strategy = CacheStrategy.WRITE_THROUGH
    )
    public List<String> getIngredientAlternatives(String ingredientName, List<String> userConditions) {
        // Try cache first
        String cacheKey = "alternatives:" + ingredientName + ":" + String.join(",", userConditions);
        Optional<List<String>> cached = cacheService.get(cacheKey, List.class);
        
        if (cached.isPresent()) {
            return cached.get();
        }
        
        // Get from service
        List<String> alternatives = ingredientService.getAlternatives(ingredientName, userConditions);
        
        // Cache the result
        cacheService.set(cacheKey, alternatives);
        
        return alternatives;
    }

    /**
     * Clear ingredient cache
     */
    public void clearIngredientCache(String ingredientName) {
        cacheService.delete("ingredient:" + ingredientName);
    }

    /**
     * Clear all ingredient caches
     */
    public void clearAllIngredientCaches() {
        // This would implement pattern-based clearing
        // For now, just clear all
        cacheService.clear();
    }

    /**
     * Get cache statistics
     */
    public MultiLevelCacheService.CacheStats getCacheStats() {
        return cacheService.getStats();
    }
}
