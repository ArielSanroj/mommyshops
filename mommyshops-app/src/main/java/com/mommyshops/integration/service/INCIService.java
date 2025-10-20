package com.mommyshops.integration.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;
import org.springframework.stereotype.Service;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.io.InputStream;
import java.util.Map;
import java.util.HashMap;
import java.util.List;
import java.util.ArrayList;
import java.util.stream.Collectors;

/**
 * INCI (International Nomenclature of Cosmetic Ingredients) Service
 * 
 * This service provides hazard scoring for cosmetic ingredients based on
 * Biodizionario data, similar to the inci_score Ruby gem.
 * 
 * Hazard scores range from 0 (safe) to 4 (dangerous):
 * - 0: Safe
 * - 1: Low hazard
 * - 2: Moderate hazard
 * - 3: High hazard
 * - 4: Dangerous
 */
@Service
public class INCIService {
    
    private static final Logger logger = LoggerFactory.getLogger(INCIService.class);
    
    // Constants based on inci_score Ruby gem
    private static final double HAZARD_RATIO = 25.0;
    
    private final ObjectMapper objectMapper;
    private final ResourceLoader resourceLoader;
    private final String biodizionarioDataPath;
    
    // In-memory database for fast lookups
    private Map<String, Map<String, Object>> ingredientDatabase;
    private boolean databaseLoaded = false;
    
    public INCIService(ObjectMapper objectMapper,
                      ResourceLoader resourceLoader,
                      @Value("${external.api.inci.data-path:classpath:biodizionario_database.json}") String biodizionarioDataPath) {
        this.objectMapper = objectMapper;
        this.resourceLoader = resourceLoader;
        this.biodizionarioDataPath = biodizionarioDataPath;
    }
    
    /**
     * Calculate hazard score for a single ingredient
     * 
     * @param ingredient The ingredient name to analyze
     * @return INCI hazard data including score, description, and safety level
     */
    public Map<String, Object> getIngredientHazardScore(String ingredient) {
        try {
            ensureDatabaseLoaded();
            
            String searchKey = ingredient.toLowerCase().trim();
            
            // Direct lookup
            if (ingredientDatabase.containsKey(searchKey)) {
                Map<String, Object> data = ingredientDatabase.get(searchKey);
                return createIngredientResponse(ingredient, data);
            }
            
            // Partial match search
            Map<String, Object> partialMatch = findPartialMatch(searchKey);
            if (partialMatch != null) {
                return createIngredientResponse(ingredient, partialMatch);
            }
            
            // No match found - assume unknown hazard
            return Map.of(
                "ingredient", ingredient,
                "hazard_score", 2, // Moderate hazard for unknown ingredients
                "description", "Unknown ingredient - Moderate hazard assumed",
                "safety_level", "Moderate Risk",
                "data_source", "Biodizionario Database"
            );
            
        } catch (Exception e) {
            logger.error("Error calculating INCI hazard score for ingredient {}: {}", ingredient, e.getMessage());
            return Map.of(
                "ingredient", ingredient,
                "error", "INCI hazard score unavailable",
                "message", e.getMessage()
            );
        }
    }
    
    /**
     * Calculate hazard score for multiple ingredients
     * 
     * @param ingredients List of ingredient names
     * @return Comprehensive hazard analysis including total score and breakdown
     */
    public Map<String, Object> calculateHazardScore(List<String> ingredients) {
        try {
            ensureDatabaseLoaded();
            
            if (ingredients == null || ingredients.isEmpty()) {
                return Map.of(
                    "total_score", 0.0,
                    "average_hazard", 0.0,
                    "hazard_level", "Unknown",
                    "ingredients", new ArrayList<>(),
                    "total_ingredients", 0
                );
            }
            
            List<Map<String, Object>> ingredientScores = new ArrayList<>();
            double totalHazard = 0.0;
            
            for (String ingredient : ingredients) {
                Map<String, Object> ingredientData = getIngredientHazardScore(ingredient);
                ingredientScores.add(ingredientData);
                
                if (ingredientData.containsKey("hazard_score")) {
                    totalHazard += ((Number) ingredientData.get("hazard_score")).doubleValue();
                }
            }
            
            // Calculate average hazard
            double averageHazard = totalHazard / ingredients.size();
            
            // Calculate percentage score based on inci_score formula: (100 - avg * 25)
            double percentageScore = Math.max(0, 100 - averageHazard * HAZARD_RATIO);
            
            // Determine hazard level
            String hazardLevel = determineHazardLevel(percentageScore);
            
            Map<String, Object> result = new HashMap<>();
            result.put("total_score", Math.round(percentageScore * 100.0) / 100.0);
            result.put("average_hazard", Math.round(averageHazard * 100.0) / 100.0);
            result.put("hazard_level", hazardLevel);
            result.put("ingredients", ingredientScores);
            result.put("total_ingredients", ingredients.size());
            result.put("data_source", "Biodizionario Database");
            result.put("calculation_method", "INCI Score Algorithm");
            
            return result;
            
        } catch (Exception e) {
            logger.error("Error calculating hazard score for multiple ingredients: {}", e.getMessage());
            return Map.of(
                "error", "Hazard score calculation failed",
                "message", e.getMessage()
            );
        }
    }
    
    /**
     * Search ingredients by hazard level
     */
    public List<Map<String, Object>> searchByHazardLevel(int hazardLevel) {
        try {
            ensureDatabaseLoaded();
            
            return ingredientDatabase.values().stream()
                .filter(ingredient -> {
                    int score = ((Number) ingredient.getOrDefault("hazard_score", 0)).intValue();
                    return score == hazardLevel;
                })
                .collect(Collectors.toList());
                
        } catch (Exception e) {
            logger.error("Error searching by hazard level {}: {}", hazardLevel, e.getMessage());
            return new ArrayList<>();
        }
    }
    
    /**
     * Search ingredients by description/keyword
     */
    public List<Map<String, Object>> searchByDescription(String keyword) {
        try {
            ensureDatabaseLoaded();
            
            String searchTerm = keyword.toLowerCase();
            
            return ingredientDatabase.values().stream()
                .filter(ingredient -> {
                    String description = (String) ingredient.getOrDefault("description", "");
                    return description.toLowerCase().contains(searchTerm);
                })
                .collect(Collectors.toList());
                
        } catch (Exception e) {
            logger.error("Error searching by description {}: {}", keyword, e.getMessage());
            return new ArrayList<>();
        }
    }
    
    /**
     * Get database statistics
     */
    public Map<String, Object> getDatabaseStats() {
        try {
            ensureDatabaseLoaded();
            
            Map<String, Object> stats = new HashMap<>();
            stats.put("total_ingredients", ingredientDatabase.size());
            stats.put("database_loaded", databaseLoaded);
            stats.put("data_source", "Biodizionario Database");
            
            // Count by hazard level
            Map<String, Long> hazardDistribution = ingredientDatabase.values().stream()
                .collect(Collectors.groupingBy(
                    ingredient -> {
                        int score = ((Number) ingredient.getOrDefault("hazard_score", 0)).intValue();
                        return getHazardLevelName(score);
                    },
                    Collectors.counting()
                ));
            stats.put("hazard_distribution", hazardDistribution);
            
            return stats;
            
        } catch (Exception e) {
            logger.error("Error getting database stats: {}", e.getMessage());
            return Map.of("error", "Could not retrieve database statistics");
        }
    }
    
    /**
     * Ensure the database is loaded
     */
    private void ensureDatabaseLoaded() throws IOException {
        if (!databaseLoaded) {
            loadDatabase();
        }
    }
    
    /**
     * Load the Biodizionario database from JSON file
     */
    private void loadDatabase() throws IOException {
        logger.info("Loading Biodizionario database from: {}", biodizionarioDataPath);
        
        Resource resource = resourceLoader.getResource(biodizionarioDataPath);
        
        if (!resource.exists()) {
            logger.warn("Biodizionario database file not found: {}", biodizionarioDataPath);
            // Create empty database
            ingredientDatabase = new HashMap<>();
            databaseLoaded = true;
            return;
        }
        
        try (InputStream inputStream = resource.getInputStream()) {
            @SuppressWarnings("unchecked")
            Map<String, Map<String, Object>> data = objectMapper.readValue(
                inputStream, 
                Map.class
            );
            
            ingredientDatabase = data;
            databaseLoaded = true;
            
            logger.info("Biodizionario database loaded successfully with {} ingredients", 
                       ingredientDatabase.size());
                       
        } catch (Exception e) {
            logger.error("Error loading Biodizionario database: {}", e.getMessage());
            throw new IOException("Failed to load Biodizionario database", e);
        }
    }
    
    /**
     * Create ingredient response with hazard data
     */
    private Map<String, Object> createIngredientResponse(String ingredient, Map<String, Object> data) {
        Map<String, Object> response = new HashMap<>();
        response.put("ingredient", ingredient);
        response.put("hazard_score", data.get("hazard_score"));
        response.put("description", data.get("description"));
        
        int hazardScore = ((Number) data.getOrDefault("hazard_score", 0)).intValue();
        response.put("safety_level", getHazardLevelName(hazardScore));
        response.put("data_source", "Biodizionario Database");
        
        return response;
    }
    
    /**
     * Find partial match for ingredient name
     */
    private Map<String, Object> findPartialMatch(String searchKey) {
        // Try to find ingredients that contain the search term
        for (Map.Entry<String, Map<String, Object>> entry : ingredientDatabase.entrySet()) {
            String key = entry.getKey();
            if (key.contains(searchKey) || searchKey.contains(key)) {
                return entry.getValue();
            }
        }
        
        return null;
    }
    
    /**
     * Determine hazard level based on percentage score
     */
    private String determineHazardLevel(double percentageScore) {
        if (percentageScore >= 80) {
            return "Safe";
        } else if (percentageScore >= 60) {
            return "Low Risk";
        } else if (percentageScore >= 40) {
            return "Moderate Risk";
        } else if (percentageScore >= 20) {
            return "High Risk";
        } else {
            return "Dangerous";
        }
    }
    
    /**
     * Get hazard level name based on score
     */
    private String getHazardLevelName(int hazardScore) {
        switch (hazardScore) {
            case 0: return "Safe";
            case 1: return "Low Risk";
            case 2: return "Moderate Risk";
            case 3: return "High Risk";
            case 4: return "Dangerous";
            default: return "Unknown";
        }
    }
    
    /**
     * Check if INCI service is healthy
     */
    public boolean isHealthy() {
        try {
            ensureDatabaseLoaded();
            return databaseLoaded && !ingredientDatabase.isEmpty();
        } catch (Exception e) {
            logger.error("INCI health check failed: {}", e.getMessage());
            return false;
        }
    }
}