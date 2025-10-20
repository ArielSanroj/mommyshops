package com.mommyshops.integration.controller;

import com.mommyshops.integration.service.COSINGService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;
import java.util.List;
import java.util.HashMap;

/**
 * REST Controller for COSING (Cosmetic Ingredient Database) integration
 */
@RestController
@RequestMapping("/api/cosing")
@CrossOrigin(origins = "*")
public class COSINGController {
    
    private static final Logger logger = LoggerFactory.getLogger(COSINGController.class);
    
    @Autowired
    private COSINGService cosingService;
    
    /**
     * Get COSING data for a single ingredient
     */
    @GetMapping("/ingredient/{ingredient}")
    public ResponseEntity<Map<String, Object>> getIngredientData(@PathVariable String ingredient) {
        try {
            logger.info("Fetching COSING data for ingredient: {}", ingredient);
            Map<String, Object> data = cosingService.getIngredientData(ingredient);
            return ResponseEntity.ok(data);
        } catch (Exception e) {
            logger.error("Error fetching COSING data for ingredient {}: {}", ingredient, e.getMessage());
            Map<String, Object> error = new HashMap<>();
            error.put("error", "Failed to fetch COSING data");
            error.put("message", e.getMessage());
            return ResponseEntity.internalServerError().body(error);
        }
    }
    
    /**
     * Get COSING data for multiple ingredients
     */
    @PostMapping("/ingredients")
    public ResponseEntity<Map<String, Object>> getMultipleIngredientsData(@RequestBody List<String> ingredients) {
        try {
            logger.info("Fetching COSING data for {} ingredients", ingredients.size());
            Map<String, Object> data = cosingService.getMultipleIngredientsData(ingredients);
            return ResponseEntity.ok(data);
        } catch (Exception e) {
            logger.error("Error fetching COSING data for multiple ingredients: {}", e.getMessage());
            Map<String, Object> error = new HashMap<>();
            error.put("error", "Failed to fetch COSING data");
            error.put("message", e.getMessage());
            return ResponseEntity.internalServerError().body(error);
        }
    }
    
    /**
     * Search ingredients by function
     */
    @GetMapping("/search/function/{function}")
    public ResponseEntity<List<Map<String, Object>>> searchByFunction(@PathVariable String function) {
        try {
            logger.info("Searching COSING ingredients by function: {}", function);
            List<Map<String, Object>> results = cosingService.searchByFunction(function);
            return ResponseEntity.ok(results);
        } catch (Exception e) {
            logger.error("Error searching by function {}: {}", function, e.getMessage());
            return ResponseEntity.internalServerError().body(List.of());
        }
    }
    
    /**
     * Search ingredients by restriction
     */
    @GetMapping("/search/restriction/{restriction}")
    public ResponseEntity<List<Map<String, Object>>> searchByRestriction(@PathVariable String restriction) {
        try {
            logger.info("Searching COSING ingredients by restriction: {}", restriction);
            List<Map<String, Object>> results = cosingService.searchByRestriction(restriction);
            return ResponseEntity.ok(results);
        } catch (Exception e) {
            logger.error("Error searching by restriction {}: {}", restriction, e.getMessage());
            return ResponseEntity.internalServerError().body(List.of());
        }
    }
    
    /**
     * Get ingredients by annex
     */
    @GetMapping("/search/annex/{annex}")
    public ResponseEntity<List<Map<String, Object>>> getIngredientsByAnnex(@PathVariable String annex) {
        try {
            logger.info("Searching COSING ingredients by annex: {}", annex);
            List<Map<String, Object>> results = cosingService.getIngredientsByAnnex(annex);
            return ResponseEntity.ok(results);
        } catch (Exception e) {
            logger.error("Error searching by annex {}: {}", annex, e.getMessage());
            return ResponseEntity.internalServerError().body(List.of());
        }
    }
    
    /**
     * Get database statistics
     */
    @GetMapping("/stats")
    public ResponseEntity<Map<String, Object>> getDatabaseStats() {
        try {
            logger.info("Fetching COSING database statistics");
            Map<String, Object> stats = cosingService.getDatabaseStats();
            return ResponseEntity.ok(stats);
        } catch (Exception e) {
            logger.error("Error fetching COSING database stats: {}", e.getMessage());
            Map<String, Object> error = new HashMap<>();
            error.put("error", "Failed to fetch database statistics");
            error.put("message", e.getMessage());
            return ResponseEntity.internalServerError().body(error);
        }
    }
    
    /**
     * Health check for COSING service
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> healthCheck() {
        try {
            boolean isHealthy = cosingService.isHealthy();
            Map<String, Object> response = new HashMap<>();
            response.put("status", isHealthy ? "UP" : "DOWN");
            response.put("service", "COSING EU Database");
            response.put("timestamp", System.currentTimeMillis());
            
            if (isHealthy) {
                return ResponseEntity.ok(response);
            } else {
                return ResponseEntity.status(503).body(response);
            }
        } catch (Exception e) {
            logger.error("COSING health check failed: {}", e.getMessage());
            Map<String, Object> error = new HashMap<>();
            error.put("status", "DOWN");
            error.put("service", "COSING EU Database");
            error.put("error", e.getMessage());
            error.put("timestamp", System.currentTimeMillis());
            return ResponseEntity.status(503).body(error);
        }
    }
    
    /**
     * Test endpoint for COSING functionality
     */
    @GetMapping("/test")
    public ResponseEntity<Map<String, Object>> testCOSINGService() {
        try {
            logger.info("Testing COSING service with sample ingredients");
            
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
            
            Map<String, Object> results = cosingService.getMultipleIngredientsData(testIngredients);
            
            Map<String, Object> response = new HashMap<>();
            response.put("testIngredients", testIngredients);
            response.put("results", results);
            response.put("timestamp", System.currentTimeMillis());
            response.put("status", "SUCCESS");
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("COSING test failed: {}", e.getMessage());
            Map<String, Object> error = new HashMap<>();
            error.put("error", "COSING test failed");
            error.put("message", e.getMessage());
            error.put("timestamp", System.currentTimeMillis());
            return ResponseEntity.internalServerError().body(error);
        }
    }
}