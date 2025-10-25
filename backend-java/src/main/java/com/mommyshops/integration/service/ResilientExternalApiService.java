package com.mommyshops.integration.service;

import com.mommyshops.integration.util.SimpleProductionApiUtils;
import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.github.resilience4j.ratelimiter.RateLimiter;
import io.github.resilience4j.bulkhead.Bulkhead;
// import io.github.resilience4j.decorators.Decorators;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.cache.annotation.Cacheable;

import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.function.Supplier;

/**
 * Resilient External API Service
 * Ensures all external API calls use rate limiting, circuit breakers, and caching consistently
 */
@Service
public class ResilientExternalApiService {
    
    private final SimpleProductionApiUtils apiUtils;
    private final CircuitBreaker circuitBreaker;
    private final RateLimiter rateLimiter;
    private final Bulkhead bulkhead;
    
    @Autowired
    public ResilientExternalApiService(SimpleProductionApiUtils apiUtils,
                                     CircuitBreaker circuitBreaker,
                                     RateLimiter rateLimiter,
                                     Bulkhead bulkhead) {
        this.apiUtils = apiUtils;
        this.circuitBreaker = circuitBreaker;
        this.rateLimiter = rateLimiter;
        this.bulkhead = bulkhead;
    }
    
    /**
     * Get FDA adverse events data with resilience patterns
     */
    @Cacheable(value = "fda-data", key = "#ingredient")
    public Map<String, Object> getFdaAdverseEvents(String ingredient) {
        return executeWithResilience(() -> apiUtils.getFdaAdverseEvents(ingredient));
    }
    
    /**
     * Get PubChem data with resilience patterns
     */
    @Cacheable(value = "pubchem-data", key = "#ingredient")
    public Map<String, Object> getPubChemData(String ingredient) {
        return executeWithResilience(() -> apiUtils.getPubChemData(ingredient));
    }
    
    /**
     * Get EWG Skin Deep data with resilience patterns
     */
    @Cacheable(value = "ewg-data", key = "#ingredient")
    public Map<String, Object> getEwgSkinDeepData(String ingredient) {
        return executeWithResilience(() -> apiUtils.getEwgSkinDeepData(ingredient));
    }
    
    /**
     * Get comprehensive ingredient data from all sources with resilience patterns
     */
    public CompletableFuture<Map<String, Object>> getComprehensiveIngredientData(String ingredient) {
        return CompletableFuture.supplyAsync(() -> {
            Map<String, Object> result = new java.util.HashMap<>();
            
            // Get data from all sources with resilience
            Map<String, Object> fdaData = getFdaAdverseEvents(ingredient);
            Map<String, Object> pubchemData = getPubChemData(ingredient);
            Map<String, Object> ewgData = getEwgSkinDeepData(ingredient);
            
            // Combine results
            result.put("ingredient", ingredient);
            result.put("fda", fdaData);
            result.put("pubchem", pubchemData);
            result.put("ewg", ewgData);
            result.put("timestamp", System.currentTimeMillis());
            result.put("success", true);
            
            // Calculate overall scores
            double safetyScore = calculateOverallSafetyScore(fdaData, pubchemData, ewgData);
            double ecoScore = calculateOverallEcoScore(ewgData);
            
            result.put("overall_safety_score", safetyScore);
            result.put("overall_eco_score", ecoScore);
            result.put("risk_level", determineRiskLevel(safetyScore));
            
            return result;
        });
    }
    
    /**
     * Execute API call with all resilience patterns
     */
    private Map<String, Object> executeWithResilience(Supplier<Map<String, Object>> apiCall) {
        try {
            // Apply rate limiting
            rateLimiter.acquirePermission();
            
            // Apply bulkhead
            bulkhead.acquirePermission();
            
            try {
                // Apply circuit breaker
                return circuitBreaker.executeSupplier(apiCall);
            } finally {
                bulkhead.releasePermission();
            }
        } catch (Exception e) {
            // Return default data on failure
            Map<String, Object> defaultData = new java.util.HashMap<>();
            defaultData.put("success", false);
            defaultData.put("error", e.getMessage());
            defaultData.put("source", "ResilientExternalApiService");
            return defaultData;
        }
    }
    
    /**
     * Calculate overall safety score from all sources
     */
    private double calculateOverallSafetyScore(Map<String, Object> fdaData, 
                                             Map<String, Object> pubchemData, 
                                             Map<String, Object> ewgData) {
        double score = 50.0; // Default neutral score
        
        // FDA data influence (40% weight)
        if (fdaData != null && fdaData.containsKey("adverse_events_count")) {
            int adverseEvents = (Integer) fdaData.getOrDefault("adverse_events_count", 0);
            int seriousEvents = (Integer) fdaData.getOrDefault("serious_events_count", 0);
            
            if (seriousEvents > 0) {
                score -= 30; // Serious events significantly reduce score
            } else if (adverseEvents > 5) {
                score -= 15; // Many adverse events reduce score
            } else if (adverseEvents > 0) {
                score -= 5; // Some adverse events slightly reduce score
            }
        }
        
        // EWG data influence (35% weight)
        if (ewgData != null && ewgData.containsKey("ewg_score")) {
            int ewgScore = (Integer) ewgData.getOrDefault("ewg_score", 50);
            score += (50 - ewgScore) * 0.7; // EWG score 0-10, we want higher scores for safety
        }
        
        // PubChem data influence (25% weight)
        if (pubchemData != null && pubchemData.containsKey("success")) {
            boolean success = (Boolean) pubchemData.getOrDefault("success", false);
            if (success) {
                score += 5; // Available data is good
            }
        }
        
        return Math.max(0, Math.min(100, score)); // Clamp between 0-100
    }
    
    /**
     * Calculate overall eco score from EWG data
     */
    private double calculateOverallEcoScore(Map<String, Object> ewgData) {
        if (ewgData != null && ewgData.containsKey("ewg_score")) {
            int ewgScore = (Integer) ewgData.getOrDefault("ewg_score", 50);
            return (10 - ewgScore) * 10; // Convert 0-10 scale to 0-100 scale
        }
        return 50.0; // Default neutral score
    }
    
    /**
     * Determine risk level based on safety score
     */
    private String determineRiskLevel(double safetyScore) {
        if (safetyScore >= 80) {
            return "safe";
        } else if (safetyScore >= 60) {
            return "low";
        } else if (safetyScore >= 40) {
            return "medium";
        } else {
            return "high";
        }
    }
}