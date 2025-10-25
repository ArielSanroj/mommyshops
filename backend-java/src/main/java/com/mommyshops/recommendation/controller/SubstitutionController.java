package com.mommyshops.recommendation.controller;

import com.mommyshops.recommendation.service.SubstitutionMappingService;
import com.mommyshops.recommendation.service.EnhancedRecommendationService;
import com.mommyshops.auth.domain.UserAccount;
import com.mommyshops.auth.service.AuthService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.security.core.Authentication;

import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

/**
 * REST controller for enhanced substitution mapping endpoints
 * Based on the Python FastAPI substitution_endpoints.py
 */
@RestController
@RequestMapping("/api/substitution")
@CrossOrigin(origins = "*")
public class SubstitutionController {
    
    @Autowired
    private SubstitutionMappingService substitutionMappingService;
    
    @Autowired
    private EnhancedRecommendationService enhancedRecommendationService;
    
    @Autowired
    private AuthService authService;
    
    /**
     * Comprehensive ingredient analysis with ML-powered substitution suggestions
     */
    @PostMapping("/analyze")
    public CompletableFuture<ResponseEntity<SubstitutionMappingService.EnhancedAnalysisResponse>> analyzeIngredientsForSubstitution(
            @RequestBody IngredientAnalysisRequest request,
            Authentication authentication) {
        
        try {
            UserAccount user = authService.getCurrentUser();
            if (user == null) {
                return CompletableFuture.completedFuture(ResponseEntity.status(HttpStatus.UNAUTHORIZED).build());
            }
            
            return substitutionMappingService.analyzeIngredientsForSubstitution(
                request.getIngredients(),
                request.getUserConditions(),
                request.isIncludeSafetyAnalysis()
            ).thenApply(ResponseEntity::ok);
            
        } catch (Exception e) {
            return CompletableFuture.completedFuture(
                ResponseEntity.internalServerError().body(null));
        }
    }
    
    /**
     * Get safer alternatives for problematic ingredients
     */
    @PostMapping("/alternatives")
    public CompletableFuture<ResponseEntity<List<Map<String, Object>>>> getSaferAlternatives(
            @RequestBody SaferAlternativesRequest request,
            Authentication authentication) {
        
        try {
            UserAccount user = authService.getCurrentUser();
            if (user == null) {
                return CompletableFuture.completedFuture(ResponseEntity.status(HttpStatus.UNAUTHORIZED).build());
            }
            
            return substitutionMappingService.getSaferAlternatives(
                request.getIngredients(),
                request.getUserConditions()
            ).thenApply(ResponseEntity::ok);
            
        } catch (Exception e) {
            return CompletableFuture.completedFuture(
                ResponseEntity.internalServerError().body(null));
        }
    }
    
    /**
     * Batch analysis of multiple ingredient lists
     */
    @PostMapping("/batch-analyze")
    public CompletableFuture<ResponseEntity<List<SubstitutionMappingService.EnhancedAnalysisResponse>>> batchAnalyzeIngredients(
            @RequestBody BatchAnalysisRequest request,
            Authentication authentication) {
        
        try {
            UserAccount user = authService.getCurrentUser();
            if (user == null) {
                return CompletableFuture.completedFuture(ResponseEntity.status(HttpStatus.UNAUTHORIZED).build());
            }
            
            return substitutionMappingService.batchAnalyzeIngredients(
                request.getIngredientBatches(),
                request.getUserConditions()
            ).thenApply(ResponseEntity::ok);
            
        } catch (Exception e) {
            return CompletableFuture.completedFuture(
                ResponseEntity.internalServerError().body(null));
        }
    }
    
    /**
     * Enhance existing product recommendations with substitution analysis
     */
    @PostMapping("/enhance-recommendations")
    public CompletableFuture<ResponseEntity<List<Map<String, Object>>>> enhanceProductRecommendations(
            @RequestBody List<Map<String, Object>> recommendations,
            @RequestParam(required = false) List<String> userConditions,
            Authentication authentication) {
        
        try {
            UserAccount user = authService.getCurrentUser();
            if (user == null) {
                return CompletableFuture.completedFuture(ResponseEntity.status(HttpStatus.UNAUTHORIZED).build());
            }
            
            return substitutionMappingService.enhanceProductRecommendations(
                recommendations,
                userConditions
            ).thenApply(ResponseEntity::ok);
            
        } catch (Exception e) {
            return CompletableFuture.completedFuture(
                ResponseEntity.internalServerError().body(null));
        }
    }
    
    /**
     * Health check for the substitution system
     */
    @GetMapping("/health")
    public CompletableFuture<ResponseEntity<Map<String, Object>>> substitutionHealthCheck() {
        try {
            return substitutionMappingService.analyzeIngredientsForSubstitution(
                List.of("glycerin"),
                null,
                true
            ).thenApply(result -> {
                Map<String, Object> health = Map.of(
                    "status", "healthy",
                    "ml_models_loaded", true,
                    "safety_databases_accessible", true,
                    "test_analysis_successful", true,
                    "timestamp", result.getAnalysisTimestamp()
                );
                return ResponseEntity.ok(health);
            });
            
        } catch (Exception e) {
            Map<String, Object> health = Map.of(
                "status", "unhealthy",
                "ml_models_loaded", false,
                "safety_databases_accessible", false,
                "test_analysis_successful", false,
                "error", e.getMessage()
            );
            return CompletableFuture.completedFuture(ResponseEntity.ok(health));
        }
    }
    
    /**
     * Get information about supported cosmetic safety standards
     */
    @GetMapping("/safety-standards")
    public ResponseEntity<Map<String, Object>> getSupportedSafetyStandards() {
        Map<String, Object> standards = Map.of(
            "supported_standards", List.of(
                Map.of(
                    "name", "FDA",
                    "description", "Food and Drug Administration",
                    "weight", 0.3,
                    "focus", "Regulatory approval and safety"
                ),
                Map.of(
                    "name", "EWG",
                    "description", "Environmental Working Group",
                    "weight", 0.25,
                    "focus", "Eco-friendliness and consumer safety"
                ),
                Map.of(
                    "name", "CIR",
                    "description", "Cosmetic Ingredient Review",
                    "weight", 0.2,
                    "focus", "Scientific safety assessment"
                ),
                Map.of(
                    "name", "SCCS",
                    "description", "Scientific Committee on Consumer Safety",
                    "weight", 0.15,
                    "focus", "EU safety evaluation"
                ),
                Map.of(
                    "name", "ICCR",
                    "description", "International Cooperation on Cosmetics Regulation",
                    "weight", 0.1,
                    "focus", "International harmonization"
                )
            ),
            "functional_categories", List.of(
                "emollients", "humectants", "emulsifiers", "preservatives",
                "antioxidants", "surfactants", "fragrance", "colorants"
            ),
            "ml_models", List.of(
                "sentence-transformers (all-MiniLM-L6-v2)",
                "TF-IDF vectorization",
                "cosine similarity matching"
            )
        );
        
        return ResponseEntity.ok(standards);
    }
    
    /**
     * Quick substitution lookup for a single ingredient
     */
    @PostMapping("/quick-substitute")
    public CompletableFuture<ResponseEntity<Map<String, Object>>> quickSubstituteLookup(
            @RequestParam String ingredient,
            @RequestParam(required = false) List<String> userConditions,
            @RequestParam(defaultValue = "5") int maxSubstitutes,
            Authentication authentication) {
        
        try {
            UserAccount user = authService.getCurrentUser();
            if (user == null) {
                return CompletableFuture.completedFuture(ResponseEntity.status(HttpStatus.UNAUTHORIZED).build());
            }
            
            return substitutionMappingService.quickSubstituteLookup(
                ingredient,
                userConditions,
                maxSubstitutes
            ).thenApply(ResponseEntity::ok);
            
        } catch (Exception e) {
            return CompletableFuture.completedFuture(
                ResponseEntity.internalServerError().body(null));
        }
    }
    
    /**
     * Integrate substitution analysis with existing routine analysis
     */
    @PostMapping("/integrate-with-routine-analysis")
    public CompletableFuture<ResponseEntity<Map<String, Object>>> integrateWithRoutineAnalysis(
            @RequestBody Map<String, Object> routineData,
            @RequestParam(required = false) List<String> userConditions,
            Authentication authentication) {
        
        try {
            UserAccount user = authService.getCurrentUser();
            if (user == null) {
                return CompletableFuture.completedFuture(ResponseEntity.status(HttpStatus.UNAUTHORIZED).build());
            }
            
            // Extract ingredients from routine data
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> products = (List<Map<String, Object>>) routineData.get("products");
            
            if (products == null || products.isEmpty()) {
                Map<String, Object> response = Map.of(
                    "message", "No ingredients found in routine data",
                    "substitution_analysis", Map.of()
                );
                return CompletableFuture.completedFuture(ResponseEntity.ok(response));
            }
            
            // Extract ingredients from products
            List<String> ingredients = products.stream()
                .filter(product -> product.containsKey("ingredients"))
                .flatMap(product -> {
                    @SuppressWarnings("unchecked")
                    List<String> productIngredients = (List<String>) product.get("ingredients");
                    return productIngredients != null ? productIngredients.stream() : List.<String>of().stream();
                })
                .toList();
            
            if (ingredients.isEmpty()) {
                Map<String, Object> response = Map.of(
                    "message", "No ingredients found in routine data",
                    "substitution_analysis", Map.of()
                );
                return CompletableFuture.completedFuture(ResponseEntity.ok(response));
            }
            
            // Get substitution analysis
            return substitutionMappingService.analyzeIngredientsForSubstitution(
                ingredients,
                userConditions,
                true
            ).thenApply(result -> {
                Map<String, Object> response = Map.of(
                    "routine_data", routineData,
                    "substitution_analysis", result,
                    "integration_timestamp", result.getAnalysisTimestamp()
                );
                return ResponseEntity.ok(response);
            });
            
        } catch (Exception e) {
            return CompletableFuture.completedFuture(
                ResponseEntity.internalServerError().body(null));
        }
    }
    
    // Request/Response DTOs
    
    public static class IngredientAnalysisRequest {
        private List<String> ingredients;
        private List<String> userConditions;
        private boolean includeSafetyAnalysis = true;
        
        // Getters and setters
        public List<String> getIngredients() { return ingredients; }
        public void setIngredients(List<String> ingredients) { this.ingredients = ingredients; }
        public List<String> getUserConditions() { return userConditions; }
        public void setUserConditions(List<String> userConditions) { this.userConditions = userConditions; }
        public boolean isIncludeSafetyAnalysis() { return includeSafetyAnalysis; }
        public void setIncludeSafetyAnalysis(boolean includeSafetyAnalysis) { this.includeSafetyAnalysis = includeSafetyAnalysis; }
    }
    
    public static class SaferAlternativesRequest {
        private List<String> ingredients;
        private List<String> userConditions;
        
        // Getters and setters
        public List<String> getIngredients() { return ingredients; }
        public void setIngredients(List<String> ingredients) { this.ingredients = ingredients; }
        public List<String> getUserConditions() { return userConditions; }
        public void setUserConditions(List<String> userConditions) { this.userConditions = userConditions; }
    }
    
    public static class BatchAnalysisRequest {
        private List<List<String>> ingredientBatches;
        private List<String> userConditions;
        
        // Getters and setters
        public List<List<String>> getIngredientBatches() { return ingredientBatches; }
        public void setIngredientBatches(List<List<String>> ingredientBatches) { this.ingredientBatches = ingredientBatches; }
        public List<String> getUserConditions() { return userConditions; }
        public void setUserConditions(List<String> userConditions) { this.userConditions = userConditions; }
    }
}