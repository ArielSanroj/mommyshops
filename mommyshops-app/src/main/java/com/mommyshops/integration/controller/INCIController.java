package com.mommyshops.integration.controller;

import com.mommyshops.integration.service.INCIService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;
import java.util.List;
import java.util.HashMap;

/**
 * REST Controller for INCI (International Nomenclature of Cosmetic Ingredients) integration
 * Provides hazard scoring based on Biodizionario database
 */
@RestController
@RequestMapping("/api/inci")
@CrossOrigin(origins = "*")
public class INCIController {
    
    private static final Logger logger = LoggerFactory.getLogger(INCIController.class);
    
    @Autowired
    private INCIService inciService;
    
    /**
     * Get hazard score for a single ingredient
     */
    @GetMapping("/ingredient/{ingredient}")
    public ResponseEntity<Map<String, Object>> getIngredientHazardScore(@PathVariable String ingredient) {
        try {
            logger.info("Fetching INCI hazard score for ingredient: {}", ingredient);
            Map<String, Object> data = inciService.getIngredientHazardScore(ingredient);
            return ResponseEntity.ok(data);
        } catch (Exception e) {
            logger.error("Error fetching INCI hazard score for ingredient {}: {}", ingredient, e.getMessage());
            Map<String, Object> error = new HashMap<>();
            error.put("error", "Failed to fetch INCI hazard score");
            error.put("message", e.getMessage());
            return ResponseEntity.internalServerError().body(error);
        }
    }
    
    /**
     * Calculate hazard score for multiple ingredients
     */
    @PostMapping("/calculate")
    public ResponseEntity<Map<String, Object>> calculateHazardScore(@RequestBody List<String> ingredients) {
        try {
            logger.info("Calculating INCI hazard score for {} ingredients", ingredients.size());
            Map<String, Object> data = inciService.calculateHazardScore(ingredients);
            return ResponseEntity.ok(data);
        } catch (Exception e) {
            logger.error("Error calculating INCI hazard score for multiple ingredients: {}", e.getMessage());
            Map<String, Object> error = new HashMap<>();
            error.put("error", "Failed to calculate INCI hazard score");
            error.put("message", e.getMessage());
            return ResponseEntity.internalServerError().body(error);
        }
    }
    
    /**
     * Search ingredients by hazard level
     */
    @GetMapping("/search/hazard/{hazardLevel}")
    public ResponseEntity<List<Map<String, Object>>> searchByHazardLevel(@PathVariable int hazardLevel) {
        try {
            logger.info("Searching INCI ingredients by hazard level: {}", hazardLevel);
            List<Map<String, Object>> results = inciService.searchByHazardLevel(hazardLevel);
            return ResponseEntity.ok(results);
        } catch (Exception e) {
            logger.error("Error searching by hazard level {}: {}", hazardLevel, e.getMessage());
            return ResponseEntity.internalServerError().body(List.of());
        }
    }
    
    /**
     * Search ingredients by description/keyword
     */
    @GetMapping("/search/description/{keyword}")
    public ResponseEntity<List<Map<String, Object>>> searchByDescription(@PathVariable String keyword) {
        try {
            logger.info("Searching INCI ingredients by description: {}", keyword);
            List<Map<String, Object>> results = inciService.searchByDescription(keyword);
            return ResponseEntity.ok(results);
        } catch (Exception e) {
            logger.error("Error searching by description {}: {}", keyword, e.getMessage());
            return ResponseEntity.internalServerError().body(List.of());
        }
    }
    
    /**
     * Get database statistics
     */
    @GetMapping("/stats")
    public ResponseEntity<Map<String, Object>> getDatabaseStats() {
        try {
            logger.info("Fetching INCI database statistics");
            Map<String, Object> stats = inciService.getDatabaseStats();
            return ResponseEntity.ok(stats);
        } catch (Exception e) {
            logger.error("Error fetching INCI database stats: {}", e.getMessage());
            Map<String, Object> error = new HashMap<>();
            error.put("error", "Failed to fetch database statistics");
            error.put("message", e.getMessage());
            return ResponseEntity.internalServerError().body(error);
        }
    }
    
    /**
     * Health check for INCI service
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> healthCheck() {
        try {
            boolean isHealthy = inciService.isHealthy();
            Map<String, Object> response = new HashMap<>();
            response.put("status", isHealthy ? "UP" : "DOWN");
            response.put("service", "INCI Hazard Scoring");
            response.put("data_source", "Biodizionario Database");
            response.put("timestamp", System.currentTimeMillis());
            
            if (isHealthy) {
                return ResponseEntity.ok(response);
            } else {
                return ResponseEntity.status(503).body(response);
            }
        } catch (Exception e) {
            logger.error("INCI health check failed: {}", e.getMessage());
            Map<String, Object> error = new HashMap<>();
            error.put("status", "DOWN");
            error.put("service", "INCI Hazard Scoring");
            error.put("error", e.getMessage());
            error.put("timestamp", System.currentTimeMillis());
            return ResponseEntity.status(503).body(error);
        }
    }
    
    /**
     * Test endpoint for INCI functionality
     */
    @GetMapping("/test")
    public ResponseEntity<Map<String, Object>> testINCIService() {
        try {
            logger.info("Testing INCI service with sample ingredients");
            
            List<String> testIngredients = List.of(
                "Sodium Laureth Sulfate",
                "Phenoxyethanol", 
                "Benzyl Alcohol",
                "Aloe Barbadensis Leaf Juice",
                "Aqua",
                "Propylene Glycol",
                "Parfum",
                "Sodium Chloride",
                "Ethylhexylglycerin",
                "Melaleuca Alternifolia Leaf Oil"
            );
            
            Map<String, Object> results = inciService.calculateHazardScore(testIngredients);
            
            Map<String, Object> response = new HashMap<>();
            response.put("test_ingredients", testIngredients);
            response.put("results", results);
            response.put("timestamp", System.currentTimeMillis());
            response.put("status", "SUCCESS");
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("INCI test failed: {}", e.getMessage());
            Map<String, Object> error = new HashMap<>();
            error.put("error", "INCI test failed");
            error.put("message", e.getMessage());
            error.put("timestamp", System.currentTimeMillis());
            return ResponseEntity.internalServerError().body(error);
        }
    }
    
    /**
     * Get hazard level explanation
     */
    @GetMapping("/hazard-levels")
    public ResponseEntity<Map<String, Object>> getHazardLevels() {
        try {
            Map<String, Object> hazardLevels = new HashMap<>();
            hazardLevels.put("0", Map.of(
                "name", "Safe",
                "description", "No known hazards",
                "color", "green"
            ));
            hazardLevels.put("1", Map.of(
                "name", "Low Risk",
                "description", "Minimal hazards, generally safe",
                "color", "light-green"
            ));
            hazardLevels.put("2", Map.of(
                "name", "Moderate Risk",
                "description", "Some concerns, use with caution",
                "color", "yellow"
            ));
            hazardLevels.put("3", Map.of(
                "name", "High Risk",
                "description", "Significant hazards, avoid if possible",
                "color", "orange"
            ));
            hazardLevels.put("4", Map.of(
                "name", "Dangerous",
                "description", "Severe hazards, avoid completely",
                "color", "red"
            ));
            
            Map<String, Object> response = new HashMap<>();
            response.put("hazard_levels", hazardLevels);
            response.put("scoring_method", "Biodizionario Database");
            response.put("total_score_range", "0-100 (higher is safer)");
            response.put("individual_score_range", "0-4 (lower is safer)");
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Error getting hazard levels: {}", e.getMessage());
            Map<String, Object> error = new HashMap<>();
            error.put("error", "Failed to get hazard levels");
            error.put("message", e.getMessage());
            return ResponseEntity.internalServerError().body(error);
        }
    }
}