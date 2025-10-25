package com.mommyshops.integration.controller;

import com.mommyshops.integration.service.EWGService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;
import java.util.List;
import java.util.HashMap;

/**
 * REST Controller for EWG Skin Deep integration
 */
@RestController
@RequestMapping("/api/ewg")
@CrossOrigin(origins = "*")
public class EWGController {
    
    private static final Logger logger = LoggerFactory.getLogger(EWGController.class);
    
    @Autowired
    private EWGService ewgService;
    
    /**
     * Get EWG data for a single ingredient
     */
    @GetMapping("/ingredient/{ingredient}")
    public ResponseEntity<Map<String, Object>> getIngredientData(@PathVariable String ingredient) {
        try {
            logger.info("Fetching EWG data for ingredient: {}", ingredient);
            Map<String, Object> data = ewgService.getIngredientData(ingredient);
            return ResponseEntity.ok(data);
        } catch (Exception e) {
            logger.error("Error fetching EWG data for ingredient {}: {}", ingredient, e.getMessage());
            Map<String, Object> error = new HashMap<>();
            error.put("error", "Failed to fetch EWG data");
            error.put("message", e.getMessage());
            return ResponseEntity.internalServerError().body(error);
        }
    }
    
    /**
     * Get EWG data for multiple ingredients
     */
    @PostMapping("/ingredients")
    public ResponseEntity<Map<String, Object>> getMultipleIngredientsData(@RequestBody List<String> ingredients) {
        try {
            logger.info("Fetching EWG data for {} ingredients", ingredients.size());
            Map<String, Object> data = ewgService.getMultipleIngredientsData(ingredients);
            return ResponseEntity.ok(data);
        } catch (Exception e) {
            logger.error("Error fetching EWG data for multiple ingredients: {}", e.getMessage());
            Map<String, Object> error = new HashMap<>();
            error.put("error", "Failed to fetch EWG data");
            error.put("message", e.getMessage());
            return ResponseEntity.internalServerError().body(error);
        }
    }
    
    /**
     * Health check for EWG service
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> healthCheck() {
        try {
            boolean isHealthy = ewgService.isHealthy();
            Map<String, Object> response = new HashMap<>();
            response.put("status", isHealthy ? "UP" : "DOWN");
            response.put("service", "EWG Skin Deep");
            response.put("timestamp", System.currentTimeMillis());
            
            if (isHealthy) {
                return ResponseEntity.ok(response);
            } else {
                return ResponseEntity.status(503).body(response);
            }
        } catch (Exception e) {
            logger.error("EWG health check failed: {}", e.getMessage());
            Map<String, Object> error = new HashMap<>();
            error.put("status", "DOWN");
            error.put("service", "EWG Skin Deep");
            error.put("error", e.getMessage());
            error.put("timestamp", System.currentTimeMillis());
            return ResponseEntity.status(503).body(error);
        }
    }
    
    /**
     * Test endpoint for EWG scraping
     */
    @GetMapping("/test")
    public ResponseEntity<Map<String, Object>> testEWGScraping() {
        try {
            logger.info("Testing EWG scraping with sample ingredients");
            
            List<String> testIngredients = List.of(
                "Sodium Laureth Sulfate",
                "Phenoxyethanol", 
                "Benzyl Alcohol",
                "Aloe Vera",
                "Water"
            );
            
            Map<String, Object> results = ewgService.getMultipleIngredientsData(testIngredients);
            
            Map<String, Object> response = new HashMap<>();
            response.put("testIngredients", testIngredients);
            response.put("results", results);
            response.put("timestamp", System.currentTimeMillis());
            response.put("status", "SUCCESS");
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("EWG test failed: {}", e.getMessage());
            Map<String, Object> error = new HashMap<>();
            error.put("error", "EWG test failed");
            error.put("message", e.getMessage());
            error.put("timestamp", System.currentTimeMillis());
            return ResponseEntity.internalServerError().body(error);
        }
    }
}