package com.mommyshops.recommendation.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.stream.Collectors;

/**
 * Ingredient analysis and substitution helper service
 * Based on ingredient_substitute_recommendation.py
 */
@Service
public class IngredientAnalysisHelper {
    
    private final ObjectMapper objectMapper;
    private final String ollamaBaseUrl;
    private final SubstitutionMappingService substitutionMappingService;
    
    // Safe risk levels
    private static final Set<String> SAFE_RISK_LEVELS = Set.of("", "seguro", "riesgo bajo", "safe", "low risk");
    
    // Eco-friendly threshold
    private static final double ECO_FRIENDLY_THRESHOLD = 70.0;
    
    // Default substitute message
    private static final String DEFAULT_SUBSTITUTE_MESSAGE = "alternativa natural (ej. aloe vera, glicerina vegetal)";
    
    // Default substitute mappings
    private static final Map<String, String> DEFAULT_SUBSTITUTE_MAP = new HashMap<String, String>() {{
        put("paraben", "extracto de romero");
        put("parabeno", "extracto de romero");
        put("parabenos", "extracto de romero");
        put("phthalate", "chamomile extract");
        put("ftalato", "extracto de manzanilla");
        put("sodium lauryl sulfate", "cocamidopropyl betaine");
        put("sodium laureth sulfate", "decyl glucoside");
        put("formaldehyde", "fermentos naturales");
        put("formaldehido", "fermentos naturales");
        put("triclosan", "aceite de árbol de té");
        put("triclocarban", "aceite de árbol de té");
    }};
    
    @Autowired
    public IngredientAnalysisHelper(
                                  ObjectMapper objectMapper,
                                  String ollamaBaseUrl,
                                  SubstitutionMappingService substitutionMappingService) {
        this.objectMapper = objectMapper;
        this.ollamaBaseUrl = ollamaBaseUrl;
        this.substitutionMappingService = substitutionMappingService;
    }
    
    /**
     * Analyze ingredients for safety and risk assessment
     */
    public CompletableFuture<List<IngredientAssessment>> analyzeIngredients(List<String> ingredients) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                // Clean and canonicalize ingredients
                List<String> cleanedIngredients = ingredients.stream()
                    .filter(Objects::nonNull)
                    .map(String::trim)
                    .filter(s -> !s.isEmpty())
                    .collect(Collectors.toList());
                
                if (cleanedIngredients.isEmpty()) {
                    return new ArrayList<>();
                }
                
                // Canonicalize ingredients (simplified version)
                List<String> canonicalIngredients = canonicalizeIngredients(cleanedIngredients);
                
                // Analyze each ingredient
                return canonicalIngredients.stream()
                    .map(this::analyzeSingleIngredient)
                    .collect(Collectors.toList());
                
            } catch (Exception e) {
                throw new RuntimeException("Ingredient analysis failed: " + e.getMessage(), e);
            }
        });
    }
    
    /**
     * Find substitutes for risky ingredients
     */
    public List<Map<String, String>> findSubstitutes(List<String> riskyIngredients) {
        return riskyIngredients.stream()
            .map(ingredient -> {
                String substitute = findSubstituteForIngredient(ingredient);
                Map<String, String> result = new HashMap<>();
                result.put("original", ingredient);
                result.put("substitute", substitute);
                return result;
            })
            .collect(Collectors.toList());
    }
    
    /**
     * Recommend products based on ingredient analysis
     */
    public CompletableFuture<List<Map<String, Object>>> recommendProducts(
            List<IngredientAssessment> assessments,
            List<String> userConditions,
            int topK) {
        
        return CompletableFuture.supplyAsync(() -> {
            try {
                // Split ingredients into safe and risky
                List<String> safeIngredients = new ArrayList<>();
                List<String> riskyIngredients = new ArrayList<>();
                
                for (IngredientAssessment assessment : assessments) {
                    if (assessment.isRisky()) {
                        riskyIngredients.add(assessment.getName());
                    } else {
                        safeIngredients.add(assessment.getName());
                    }
                }
                
                // Use safe ingredients for recommendations, exclude risky ones
                List<String> queryIngredients = safeIngredients.isEmpty() ? riskyIngredients : safeIngredients;
                
                if (queryIngredients.isEmpty()) {
                    return new ArrayList<>();
                }
                
                // Generate product recommendations (simplified version)
                return generateProductRecommendations(queryIngredients, riskyIngredients, userConditions, topK);
                
            } catch (Exception e) {
                throw new RuntimeException("Product recommendation failed: " + e.getMessage(), e);
            }
        });
    }
    
    /**
     * Generate comprehensive recommendations
     */
    public CompletableFuture<Map<String, List<Map<String, Object>>>> generateRecommendations(
            List<String> ingredients,
            List<String> userConditions,
            int topK) {
        
        return analyzeIngredients(ingredients)
            .thenCompose(assessments -> {
                // Find substitutes for risky ingredients
                List<String> riskyIngredients = assessments.stream()
                    .filter(IngredientAssessment::isRisky)
                    .map(IngredientAssessment::getName)
                    .collect(Collectors.toList());
                
                List<Map<String, String>> substitutes = findSubstitutes(riskyIngredients);
                
                // Get product recommendations
                return recommendProducts(assessments, userConditions, topK)
                    .thenApply(recommendations -> {
                        Map<String, List<Map<String, Object>>> result = new HashMap<>();
                        result.put("analysis", assessments.stream()
                            .map(IngredientAssessment::asDict)
                            .collect(Collectors.toList()));
                        result.put("substitutes", substitutes.stream()
                            .map(substitute -> new HashMap<String, Object>(substitute))
                            .collect(Collectors.toList()));
                        result.put("recommendations", recommendations);
                        return result;
                    });
            });
    }
    
    /**
     * Get supported safety standards information
     */
    public Map<String, Object> getSupportedSafetyStandards() {
        return Map.of(
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
    }
    
    // Private helper methods
    
    private List<String> canonicalizeIngredients(List<String> ingredients) {
        // Simplified canonicalization - in production this would use more sophisticated logic
        return ingredients.stream()
            .map(String::toLowerCase)
            .map(ingredient -> ingredient.replaceAll("[^a-zA-Z0-9\\s]", ""))
            .map(String::trim)
            .distinct()
            .collect(Collectors.toList());
    }
    
    private IngredientAssessment analyzeSingleIngredient(String ingredient) {
        try {
            // This would integrate with external APIs and ML models
            // For now, using simplified logic based on known problematic ingredients
            
            String ingredientLower = ingredient.toLowerCase();
            boolean isRisky = isProblematicIngredient(ingredientLower);
            
            double safetyScore = isRisky ? 30.0 : 80.0;
            String riskLevel = isRisky ? "high" : "low";
            double ecoScore = isRisky ? 40.0 : 85.0;
            String ecoStatus = ecoScore >= ECO_FRIENDLY_THRESHOLD ? "eco-friendly" : "needs attention";
            
            return new IngredientAssessment(
                ingredient,
                riskLevel,
                ecoScore,
                ecoStatus,
                isRisky ? "Contains potentially harmful ingredients" : "Safe for use",
                "EWG, CIR",
                isRisky,
                isRisky ? "May cause skin irritation" : "Gentle and safe"
            );
            
        } catch (Exception e) {
            return new IngredientAssessment(
                ingredient,
                "unknown",
                null,
                "unknown",
                "Analysis failed: " + e.getMessage(),
                null,
                true,
                "Unable to assess safety"
            );
        }
    }
    
    private boolean isProblematicIngredient(String ingredient) {
        return ingredient.contains("paraben") ||
               ingredient.contains("sulfate") ||
               ingredient.contains("formaldehyde") ||
               ingredient.contains("triclosan") ||
               ingredient.contains("phthalate") ||
               ingredient.contains("alcohol") ||
               ingredient.contains("fragrance") ||
               ingredient.contains("parfum");
    }
    
    private String findSubstituteForIngredient(String ingredient) {
        String ingredientLower = ingredient.toLowerCase();
        
        // Check exact matches first
        String substitute = DEFAULT_SUBSTITUTE_MAP.get(ingredientLower);
        if (substitute != null) {
            return substitute;
        }
        
        // Check partial matches
        for (Map.Entry<String, String> entry : DEFAULT_SUBSTITUTE_MAP.entrySet()) {
            if (ingredientLower.contains(entry.getKey())) {
                return entry.getValue();
            }
        }
        
        return DEFAULT_SUBSTITUTE_MESSAGE;
    }
    
    private List<Map<String, Object>> generateProductRecommendations(
            List<String> queryIngredients,
            List<String> excludedIngredients,
            List<String> userConditions,
            int topK) {
        
        // This would integrate with product catalog service
        // For now, return mock recommendations
        List<Map<String, Object>> recommendations = new ArrayList<>();
        
        for (int i = 0; i < Math.min(topK, 3); i++) {
            Map<String, Object> recommendation = new HashMap<>();
            recommendation.put("product_id", "rec_" + String.format("%03d", i + 1));
            recommendation.put("name", "Producto Natural Recomendado " + (i + 1));
            recommendation.put("brand", "Marca Natural");
            recommendation.put("eco_score", 85.0 - (i * 5));
            recommendation.put("risk_level", "low");
            recommendation.put("reason", "Ingredientes seguros y naturales");
            recommendation.put("similarity", 0.9 - (i * 0.1));
            recommendation.put("category", "skincare");
            recommendation.put("rating_average", 4.5 - (i * 0.1));
            recommendation.put("rating_count", 120 - (i * 20));
            recommendations.add(recommendation);
        }
        
        return recommendations;
    }
    
    // Data class for ingredient assessment
    public static class IngredientAssessment {
        private final String name;
        private final String riskLevel;
        private final Double ecoScore;
        private final String ecoStatus;
        private final String risksDetailed;
        private final String sources;
        private final boolean isRisky;
        private final String benefits;
        
        public IngredientAssessment(String name, String riskLevel, Double ecoScore,
                                  String ecoStatus, String risksDetailed, String sources,
                                  boolean isRisky, String benefits) {
            this.name = name;
            this.riskLevel = riskLevel;
            this.ecoScore = ecoScore;
            this.ecoStatus = ecoStatus;
            this.risksDetailed = risksDetailed;
            this.sources = sources;
            this.isRisky = isRisky;
            this.benefits = benefits;
        }
        
        // Getters
        public String getName() { return name; }
        public String getRiskLevel() { return riskLevel; }
        public Double getEcoScore() { return ecoScore; }
        public String getEcoStatus() { return ecoStatus; }
        public String getRisksDetailed() { return risksDetailed; }
        public String getSources() { return sources; }
        public boolean isRisky() { return isRisky; }
        public String getBenefits() { return benefits; }
        
        public Map<String, Object> asDict() {
            Map<String, Object> dict = new HashMap<>();
            dict.put("name", name);
            dict.put("risk_level", riskLevel);
            dict.put("eco_score", ecoScore);
            dict.put("eco_status", ecoStatus);
            dict.put("risks_detailed", risksDetailed);
            dict.put("sources", sources);
            dict.put("is_risky", isRisky);
            dict.put("benefits", benefits);
            return dict;
        }
    }
}