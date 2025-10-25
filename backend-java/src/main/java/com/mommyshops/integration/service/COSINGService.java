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
 * COSING (Cosmetic Ingredient Database) Service
 * 
 * This service provides access to the EU COSING database for cosmetic ingredients.
 * It loads data from a JSON file containing ingredient information including
 * INCI names, CAS numbers, functions, restrictions, and regulatory status.
 */
@Service
public class COSINGService {
    
    private static final Logger logger = LoggerFactory.getLogger(COSINGService.class);
    
    private final ObjectMapper objectMapper;
    private final ResourceLoader resourceLoader;
    private final String cosingDataPath;
    
    // In-memory database for fast lookups
    private Map<String, Map<String, Object>> ingredientDatabase;
    private boolean databaseLoaded = false;
    
    public COSINGService(ObjectMapper objectMapper,
                        ResourceLoader resourceLoader,
                        @Value("${external.api.cosing.data-path:classpath:cosing_database.json}") String cosingDataPath) {
        this.objectMapper = objectMapper;
        this.resourceLoader = resourceLoader;
        this.cosingDataPath = cosingDataPath;
    }
    
    /**
     * Get COSING data for a specific ingredient
     * 
     * @param ingredient The ingredient name to search for
     * @return COSING data including INCI, CAS, function, restrictions, etc.
     */
    public Map<String, Object> getIngredientData(String ingredient) {
        try {
            ensureDatabaseLoaded();
            
            String searchKey = ingredient.toLowerCase().trim();
            
            // Direct lookup
            if (ingredientDatabase.containsKey(searchKey)) {
                return ingredientDatabase.get(searchKey);
            }
            
            // Partial match search
            Map<String, Object> partialMatch = findPartialMatch(searchKey);
            if (partialMatch != null) {
                return partialMatch;
            }
            
            // No match found
            return Map.of(
                "ingredient", ingredient,
                "error", "Ingredient not found in COSING database",
                "dataSource", "COSING EU Database"
            );
            
        } catch (Exception e) {
            logger.error("Error fetching COSING data for ingredient {}: {}", ingredient, e.getMessage());
            return Map.of(
                "ingredient", ingredient,
                "error", "COSING data unavailable",
                "message", e.getMessage()
            );
        }
    }
    
    /**
     * Get COSING data for multiple ingredients
     */
    public Map<String, Object> getMultipleIngredientsData(List<String> ingredients) {
        Map<String, Object> results = new HashMap<>();
        
        for (String ingredient : ingredients) {
            results.put(ingredient, getIngredientData(ingredient));
        }
        
        return results;
    }
    
    /**
     * Search ingredients by function
     */
    public List<Map<String, Object>> searchByFunction(String function) {
        try {
            ensureDatabaseLoaded();
            
            return ingredientDatabase.values().stream()
                .filter(ingredient -> {
                    String ingredientFunction = (String) ingredient.get("Function");
                    return ingredientFunction != null && 
                           ingredientFunction.toLowerCase().contains(function.toLowerCase());
                })
                .collect(Collectors.toList());
                
        } catch (Exception e) {
            logger.error("Error searching by function {}: {}", function, e.getMessage());
            return new ArrayList<>();
        }
    }
    
    /**
     * Search ingredients by restriction level
     */
    public List<Map<String, Object>> searchByRestriction(String restriction) {
        try {
            ensureDatabaseLoaded();
            
            return ingredientDatabase.values().stream()
                .filter(ingredient -> {
                    String ingredientRestriction = (String) ingredient.get("Restrictions");
                    return ingredientRestriction != null && 
                           ingredientRestriction.toLowerCase().contains(restriction.toLowerCase());
                })
                .collect(Collectors.toList());
                
        } catch (Exception e) {
            logger.error("Error searching by restriction {}: {}", restriction, e.getMessage());
            return new ArrayList<>();
        }
    }
    
    /**
     * Get all ingredients in a specific annex
     */
    public List<Map<String, Object>> getIngredientsByAnnex(String annex) {
        try {
            ensureDatabaseLoaded();
            
            return ingredientDatabase.values().stream()
                .filter(ingredient -> {
                    String ingredientAnnex = (String) ingredient.get("Annex");
                    return ingredientAnnex != null && 
                           ingredientAnnex.toLowerCase().contains(annex.toLowerCase());
                })
                .collect(Collectors.toList());
                
        } catch (Exception e) {
            logger.error("Error searching by annex {}: {}", annex, e.getMessage());
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
            stats.put("totalIngredients", ingredientDatabase.size());
            stats.put("databaseLoaded", databaseLoaded);
            stats.put("dataSource", "COSING EU Database");
            
            // Count by status
            Map<String, Long> statusCount = ingredientDatabase.values().stream()
                .collect(Collectors.groupingBy(
                    ingredient -> (String) ingredient.getOrDefault("Status", "Unknown"),
                    Collectors.counting()
                ));
            stats.put("statusDistribution", statusCount);
            
            // Count by annex
            Map<String, Long> annexCount = ingredientDatabase.values().stream()
                .collect(Collectors.groupingBy(
                    ingredient -> (String) ingredient.getOrDefault("Annex", "None"),
                    Collectors.counting()
                ));
            stats.put("annexDistribution", annexCount);
            
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
     * Load the COSING database from JSON file
     */
    private void loadDatabase() throws IOException {
        logger.info("Loading COSING database from: {}", cosingDataPath);
        
        Resource resource = resourceLoader.getResource(cosingDataPath);
        
        if (!resource.exists()) {
            logger.warn("COSING database file not found: {}", cosingDataPath);
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
            
            logger.info("COSING database loaded successfully with {} ingredients", 
                       ingredientDatabase.size());
                       
        } catch (Exception e) {
            logger.error("Error loading COSING database: {}", e.getMessage());
            throw new IOException("Failed to load COSING database", e);
        }
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
        
        // Try to find by INCI name
        for (Map<String, Object> ingredient : ingredientDatabase.values()) {
            String inciName = (String) ingredient.get("INCI");
            if (inciName != null && 
                inciName.toLowerCase().contains(searchKey)) {
                return ingredient;
            }
        }
        
        return null;
    }
    
    /**
     * Check if COSING service is healthy
     */
    public boolean isHealthy() {
        try {
            ensureDatabaseLoaded();
            return databaseLoaded && !ingredientDatabase.isEmpty();
        } catch (Exception e) {
            logger.error("COSING health check failed: {}", e.getMessage());
            return false;
        }
    }
}