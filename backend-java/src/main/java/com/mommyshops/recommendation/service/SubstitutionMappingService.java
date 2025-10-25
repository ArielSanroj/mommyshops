package com.mommyshops.recommendation.service;

import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.*;
import java.time.OffsetDateTime;
import java.util.stream.Collectors;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Enhanced substitution mapping service with ML-based analysis
 * Based on enhanced_substitution_mapping.py and ingredient_substitute_recommendation.py
 */
@Service
public class SubstitutionMappingService {
    
    private final ExecutorService executorService;
    
    
    
    // Default substitution mappings
    private static final Map<String, List<SubstitutionCandidate>> DEFAULT_SUBSTITUTE_MAP = new HashMap<String, List<SubstitutionCandidate>>() {{
        put("paraben", List.of(
            new SubstitutionCandidate("extracto de romero", 0.85, 0.9, 0.8, 0.95, 0.9, 
                "Preservativo natural con propiedades antioxidantes", 0.9, List.of("EWG", "CIR")),
            new SubstitutionCandidate("phenoxyethanol", 0.75, 0.7, 0.85, 0.6, 0.7, 
                "Preservativo suave y efectivo", 0.8, List.of("FDA", "CIR")),
            new SubstitutionCandidate("ethylhexylglycerin", 0.8, 0.8, 0.8, 0.7, 0.8, 
                "Preservativo natural derivado de glicerina", 0.85, List.of("EWG", "SCCS"))
        ));
        put("parabeno", List.of(
            new SubstitutionCandidate("extracto de romero", 0.85, 0.9, 0.8, 0.95, 0.9, 
                "Preservativo natural con propiedades antioxidantes", 0.9, List.of("EWG", "CIR"))
        ));
        put("sodium lauryl sulfate", List.of(
            new SubstitutionCandidate("cocamidopropyl betaine", 0.9, 0.85, 0.9, 0.8, 0.85, 
                "Surfactante suave derivado del coco", 0.9, List.of("EWG", "CIR")),
            new SubstitutionCandidate("decyl glucoside", 0.85, 0.9, 0.85, 0.95, 0.9, 
                "Surfactante natural de glucosa", 0.9, List.of("EWG", "SCCS")),
            new SubstitutionCandidate("sodium coco sulfate", 0.8, 0.75, 0.9, 0.7, 0.8, 
                "Surfactante natural del coco", 0.8, List.of("EWG", "CIR"))
        ));
        put("sodium laureth sulfate", List.of(
            new SubstitutionCandidate("decyl glucoside", 0.85, 0.9, 0.85, 0.95, 0.9, 
                "Surfactante natural de glucosa", 0.9, List.of("EWG", "SCCS")),
            new SubstitutionCandidate("cocamidopropyl betaine", 0.9, 0.85, 0.9, 0.8, 0.85, 
                "Surfactante suave derivado del coco", 0.9, List.of("EWG", "CIR"))
        ));
        put("formaldehyde", List.of(
            new SubstitutionCandidate("fermentos naturales", 0.8, 0.9, 0.75, 0.95, 0.9, 
                "Preservativo natural por fermentación", 0.85, List.of("EWG", "SCCS")),
            new SubstitutionCandidate("phenoxyethanol", 0.7, 0.7, 0.8, 0.6, 0.7, 
                "Preservativo suave y estable", 0.8, List.of("FDA", "CIR"))
        ));
        put("triclosan", List.of(
            new SubstitutionCandidate("aceite de árbol de té", 0.85, 0.9, 0.8, 0.95, 0.9, 
                "Antimicrobiano natural", 0.9, List.of("EWG", "CIR")),
            new SubstitutionCandidate("extracto de tomillo", 0.8, 0.85, 0.8, 0.9, 0.85, 
                "Antimicrobiano natural", 0.85, List.of("EWG", "CIR"))
        ));
        put("phthalate", List.of(
            new SubstitutionCandidate("chamomile extract", 0.8, 0.9, 0.75, 0.95, 0.9, 
                "Extracto natural calmante", 0.85, List.of("EWG", "SCCS")),
            new SubstitutionCandidate("extracto de manzanilla", 0.8, 0.9, 0.75, 0.95, 0.9, 
                "Extracto natural calmante", 0.85, List.of("EWG", "SCCS"))
        ));
    }};
    
    public SubstitutionMappingService(
                                    ) {
        this.executorService = Executors.newFixedThreadPool(10);
    }
    
    /**
     * Enhanced substitute analysis with ML-powered recommendations
     */
    public CompletableFuture<EnhancedAnalysisResponse> analyzeIngredientsForSubstitution(
            List<String> ingredients,
            List<String> userConditions,
            boolean includeSafetyAnalysis) {
        
        return CompletableFuture.supplyAsync(() -> {
            try {
                // 1. Analyze ingredients for safety
                List<SafetyAnalysis> safetyAnalyses = analyzeIngredientSafety(ingredients);
                
                // 2. Find problematic ingredients
                List<String> problematicIngredients = safetyAnalyses.stream()
                    .filter(SafetyAnalysis::isProblematic)
                    .map(SafetyAnalysis::getIngredient)
                    .collect(Collectors.toList());
                
                // 3. Generate substitution mappings
                Map<String, SubstitutionMapping> substitutionMappings = generateSubstitutionMappings(
                    problematicIngredients, userConditions);
                
                // 4. Generate product recommendations
                List<Map<String, Object>> productRecommendations = generateProductRecommendations(
                    ingredients, userConditions, safetyAnalyses);
                
                // 5. Create analysis summary
                AnalysisSummary summary = createAnalysisSummary(safetyAnalyses, substitutionMappings);
                
                return new EnhancedAnalysisResponse(
                    OffsetDateTime.now().toString(),
                    ingredients.size(),
                    problematicIngredients.size(),
                    safetyAnalyses,
                    substitutionMappings,
                    productRecommendations,
                    summary
                );
                
            } catch (Exception e) {
                throw new RuntimeException("Enhanced analysis failed: " + e.getMessage(), e);
            }
        }, executorService);
    }
    
    /**
     * Get safer alternatives for specific ingredients
     */
    public CompletableFuture<List<Map<String, Object>>> getSaferAlternatives(
            List<String> ingredients,
            List<String> userConditions) {
        
        return CompletableFuture.supplyAsync(() -> {
            try {
                List<Map<String, Object>> alternatives = new ArrayList<>();
                
                for (String ingredient : ingredients) {
                    List<SubstitutionCandidate> candidates = findSubstitutionCandidates(
                        ingredient, userConditions);
                    
                    if (!candidates.isEmpty()) {
                        Map<String, Object> alternative = new HashMap<>();
                        alternative.put("original", ingredient);
                        alternative.put("substitutes", candidates);
                        alternative.put("safety_justification", generateSafetyJustification(ingredient, candidates));
                        alternative.put("functional_equivalence", calculateFunctionalEquivalence(candidates));
                        alternative.put("confidence_score", calculateConfidenceScore(candidates));
                        alternatives.add(alternative);
                    }
                }
                
                return alternatives;
                
            } catch (Exception e) {
                throw new RuntimeException("Safer alternatives search failed: " + e.getMessage(), e);
            }
        }, executorService);
    }
    
    /**
     * Batch analysis of multiple ingredient lists
     */
    public CompletableFuture<List<EnhancedAnalysisResponse>> batchAnalyzeIngredients(
            List<List<String>> ingredientBatches,
            List<String> userConditions) {
        
        List<CompletableFuture<EnhancedAnalysisResponse>> futures = ingredientBatches.stream()
            .map(batch -> analyzeIngredientsForSubstitution(batch, userConditions, true))
            .collect(Collectors.toList());
        
        return CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]))
            .thenApply(v -> futures.stream()
                .map(CompletableFuture::join)
                .collect(Collectors.toList()));
    }
    
    /**
     * Enhance existing product recommendations with substitution analysis
     */
    public CompletableFuture<List<Map<String, Object>>> enhanceProductRecommendations(
            List<Map<String, Object>> existingRecommendations,
            List<String> userConditions) {
        
        return CompletableFuture.supplyAsync(() -> {
            try {
                List<Map<String, Object>> enhanced = new ArrayList<>();
                
                for (Map<String, Object> recommendation : existingRecommendations) {
                    Map<String, Object> enhancedRec = new HashMap<>(recommendation);
                    
                    // Extract ingredients from recommendation
                    @SuppressWarnings("unchecked")
                    List<String> ingredients = (List<String>) recommendation.get("ingredients");
                    
                    if (ingredients != null && !ingredients.isEmpty()) {
                        // Get substitution analysis
                        Map<String, SubstitutionMapping> substitutions = generateSubstitutionMappings(
                            ingredients, userConditions);
                        
                        enhancedRec.put("substitution_analysis", substitutions);
                        enhancedRec.put("safety_improvements", calculateSafetyImprovements(substitutions));
                    }
                    
                    enhanced.add(enhancedRec);
                }
                
                return enhanced;
                
            } catch (Exception e) {
                throw new RuntimeException("Enhancement failed: " + e.getMessage(), e);
            }
        }, executorService);
    }
    
    /**
     * Quick substitute lookup for a single ingredient
     */
    public CompletableFuture<Map<String, Object>> quickSubstituteLookup(
            String ingredient,
            List<String> userConditions,
            int maxSubstitutes) {
        
        return CompletableFuture.supplyAsync(() -> {
            try {
                List<SubstitutionCandidate> candidates = findSubstitutionCandidates(
                    ingredient, userConditions);
                
                List<SubstitutionCandidate> limitedCandidates = candidates.stream()
                    .limit(maxSubstitutes)
                    .collect(Collectors.toList());
                
                Map<String, Object> result = new HashMap<>();
                result.put("ingredient", ingredient);
                result.put("substitutes", limitedCandidates);
                
                if (!candidates.isEmpty()) {
                    result.put("safety_justification", generateSafetyJustification(ingredient, candidates));
                    result.put("confidence_score", calculateConfidenceScore(candidates));
                    result.put("functional_equivalence", calculateFunctionalEquivalence(candidates));
                } else {
                    result.put("message", "No substitutes found or ingredient is already safe");
                }
                
                return result;
                
            } catch (Exception e) {
                throw new RuntimeException("Quick lookup failed: " + e.getMessage(), e);
            }
        }, executorService);
    }
    
    // Private helper methods
    
    private List<SafetyAnalysis> analyzeIngredientSafety(List<String> ingredients) {
        return ingredients.stream()
            .map(this::analyzeSingleIngredient)
            .collect(Collectors.toList());
    }
    
    private SafetyAnalysis analyzeSingleIngredient(String ingredient) {
        // This would integrate with external APIs and ML models
        // For now, using simplified logic based on known problematic ingredients
        
        String ingredientLower = ingredient.toLowerCase();
        boolean isProblematic = isProblematicIngredient(ingredientLower);
        
        double safetyScore = isProblematic ? 30.0 : 80.0;
        String riskLevel = isProblematic ? "high" : "low";
        double ecoScore = isProblematic ? 40.0 : 85.0;
        
        return new SafetyAnalysis(
            ingredient,
            safetyScore,
            riskLevel,
            ecoScore,
            isProblematic,
            List.of("EWG", "CIR"),
            isProblematic ? "Contains potentially harmful ingredients" : "Safe for use",
            isProblematic ? "May cause skin irritation" : "Gentle and safe"
        );
    }
    
    private boolean isProblematicIngredient(String ingredient) {
        return ingredient.contains("paraben") ||
               ingredient.contains("sulfate") ||
               ingredient.contains("formaldehyde") ||
               ingredient.contains("triclosan") ||
               ingredient.contains("phthalate") ||
               ingredient.contains("alcohol");
    }
    
    private Map<String, SubstitutionMapping> generateSubstitutionMappings(
            List<String> ingredients,
            List<String> userConditions) {
        
        Map<String, SubstitutionMapping> mappings = new HashMap<>();
        
        for (String ingredient : ingredients) {
            List<SubstitutionCandidate> candidates = findSubstitutionCandidates(ingredient, userConditions);
            
            if (!candidates.isEmpty()) {
                SubstitutionMapping mapping = new SubstitutionMapping(
                    ingredient,
                    candidates,
                    generateSafetyJustification(ingredient, candidates),
                    calculateFunctionalEquivalence(candidates),
                    calculateConfidenceScore(candidates),
                    OffsetDateTime.now().toString()
                );
                mappings.put(ingredient, mapping);
            }
        }
        
        return mappings;
    }
    
    private List<SubstitutionCandidate> findSubstitutionCandidates(
            String ingredient,
            List<String> userConditions) {
        
        String ingredientLower = ingredient.toLowerCase();
        
        // Check default mappings first
        List<SubstitutionCandidate> candidates = DEFAULT_SUBSTITUTE_MAP.get(ingredientLower);
        if (candidates != null) {
            return personalizeCandidates(candidates, userConditions);
        }
        
        // Check for partial matches
        for (Map.Entry<String, List<SubstitutionCandidate>> entry : DEFAULT_SUBSTITUTE_MAP.entrySet()) {
            if (ingredientLower.contains(entry.getKey())) {
                return personalizeCandidates(entry.getValue(), userConditions);
            }
        }
        
        // Use ML-based approach for unknown ingredients
        return generateMLBasedCandidates(ingredient, userConditions);
    }
    
    private List<SubstitutionCandidate> personalizeCandidates(
            List<SubstitutionCandidate> candidates,
            List<String> userConditions) {
        
        if (userConditions == null || userConditions.isEmpty()) {
            return candidates;
        }
        
        return candidates.stream()
            .map(candidate -> personalizeCandidate(candidate, userConditions))
            .collect(Collectors.toList());
    }
    
    private SubstitutionCandidate personalizeCandidate(
            SubstitutionCandidate candidate,
            List<String> userConditions) {
        
        double adjustedSafetyScore = candidate.getSafetyScore();
        double adjustedEcoScore = candidate.getEcoScore();
        String adjustedReason = candidate.getReason();
        
        // Adjust based on user conditions
        for (String condition : userConditions) {
            String conditionLower = condition.toLowerCase();
            
            if (conditionLower.contains("sensitive") || conditionLower.contains("sensible")) {
                adjustedSafetyScore = Math.min(100, adjustedSafetyScore + 10);
                adjustedReason += " Ideal para piel sensible.";
            }
            
            if (conditionLower.contains("acne") || conditionLower.contains("acné")) {
                adjustedSafetyScore = Math.min(100, adjustedSafetyScore + 5);
                adjustedReason += " Recomendado para piel propensa al acné.";
            }
            
            if (conditionLower.contains("natural") || conditionLower.contains("natural")) {
                adjustedEcoScore = Math.min(100, adjustedEcoScore + 10);
                adjustedReason += " Ingrediente natural y eco-amigable.";
            }
        }
        
        return new SubstitutionCandidate(
            candidate.getIngredient(),
            candidate.getSimilarityScore(),
            adjustedSafetyScore,
            candidate.getFunctionalSimilarity(),
            adjustedEcoScore,
            candidate.getRiskReduction(),
            adjustedReason,
            candidate.getConfidence(),
            candidate.getSources()
        );
    }
    
    private List<SubstitutionCandidate> generateMLBasedCandidates(
            String ingredient,
            List<String> userConditions) {
        
        // This would integrate with actual ML models
        // For now, return generic recommendations
        return List.of(
            new SubstitutionCandidate(
                "alternativa natural",
                0.7,
                0.8,
                0.7,
                0.9,
                0.8,
                "Alternativa natural recomendada",
                0.7,
                List.of("ML", "EWG")
            )
        );
    }
    
    private String generateSafetyJustification(String ingredient, List<SubstitutionCandidate> candidates) {
        if (candidates.isEmpty()) {
            return "No substitutes available";
        }
        
        StringBuilder justification = new StringBuilder();
        justification.append("Substitutes for ").append(ingredient).append(": ");
        
        for (int i = 0; i < Math.min(3, candidates.size()); i++) {
            SubstitutionCandidate candidate = candidates.get(i);
            justification.append(candidate.getIngredient())
                .append(" (safety: ")
                .append(String.format("%.1f", candidate.getSafetyScore()))
                .append(")");
            
            if (i < Math.min(3, candidates.size()) - 1) {
                justification.append(", ");
            }
        }
        
        return justification.toString();
    }
    
    private double calculateFunctionalEquivalence(List<SubstitutionCandidate> candidates) {
        return candidates.stream()
            .mapToDouble(SubstitutionCandidate::getFunctionalSimilarity)
            .average()
            .orElse(0.0);
    }
    
    private double calculateConfidenceScore(List<SubstitutionCandidate> candidates) {
        return candidates.stream()
            .mapToDouble(SubstitutionCandidate::getConfidence)
            .average()
            .orElse(0.0);
    }
    
    private List<Map<String, Object>> generateProductRecommendations(
            List<String> ingredients,
            List<String> userConditions,
            List<SafetyAnalysis> safetyAnalyses) {
        
        // This would integrate with product catalog service
        // For now, return mock recommendations
        return List.of(
            Map.of(
                "product_id", "rec_001",
                "name", "Producto Natural Recomendado",
                "brand", "Marca Natural",
                "eco_score", 85.0,
                "risk_level", "low",
                "reason", "Ingredientes seguros y naturales",
                "similarity", 0.9,
                "category", "skincare",
                "rating_average", 4.5,
                "rating_count", 120
            )
        );
    }
    
    private AnalysisSummary createAnalysisSummary(
            List<SafetyAnalysis> safetyAnalyses,
            Map<String, SubstitutionMapping> substitutionMappings) {
        
        int totalIngredients = safetyAnalyses.size();
        int safeIngredients = (int) safetyAnalyses.stream()
            .filter(analysis -> !analysis.isProblematic())
            .count();
        int problematicIngredients = totalIngredients - safeIngredients;
        
        double averageSafetyScore = safetyAnalyses.stream()
            .mapToDouble(SafetyAnalysis::getSafetyScore)
            .average()
            .orElse(0.0);
        
        int ingredientsWithSubstitutes = substitutionMappings.size();
        int totalSubstituteOptions = substitutionMappings.values().stream()
            .mapToInt(mapping -> mapping.getSubstitutes().size())
            .sum();
        
        String recommendation = averageSafetyScore >= 80 ? "safe" :
                              averageSafetyScore >= 60 ? "moderate" : "caution";
        
        return new AnalysisSummary(
            totalIngredients,
            safeIngredients,
            problematicIngredients,
            averageSafetyScore,
            ingredientsWithSubstitutes,
            totalSubstituteOptions,
            recommendation
        );
    }
    
    private Map<String, Object> calculateSafetyImprovements(Map<String, SubstitutionMapping> substitutions) {
        Map<String, Object> improvements = new HashMap<>();
        
        double averageImprovement = substitutions.values().stream()
            .mapToDouble(mapping -> mapping.getSubstitutes().stream()
                .mapToDouble(SubstitutionCandidate::getSafetyImprovement)
                .average()
                .orElse(0.0))
            .average()
            .orElse(0.0);
        
        improvements.put("average_safety_improvement", averageImprovement);
        improvements.put("total_substitutes_available", substitutions.size());
        improvements.put("high_confidence_substitutes", 
            substitutions.values().stream()
                .mapToInt(mapping -> (int) mapping.getSubstitutes().stream()
                    .filter(candidate -> candidate.getConfidence() >= 0.8)
                    .count())
                .sum());
        
        return improvements;
    }
    
    // Data classes
    public static class SubstitutionCandidate {
        private final String ingredient;
        private final double similarityScore;
        private final double safetyScore;
        private final double functionalSimilarity;
        private final double ecoScore;
        private final double riskReduction;
        private final String reason;
        private final double confidence;
        private final List<String> sources;
        
        public SubstitutionCandidate(String ingredient, double similarityScore, double safetyScore,
                                   double functionalSimilarity, double ecoScore, double riskReduction,
                                   String reason, double confidence, List<String> sources) {
            this.ingredient = ingredient;
            this.similarityScore = similarityScore;
            this.safetyScore = safetyScore;
            this.functionalSimilarity = functionalSimilarity;
            this.ecoScore = ecoScore;
            this.riskReduction = riskReduction;
            this.reason = reason;
            this.confidence = confidence;
            this.sources = sources;
        }
        
        // Getters
        public String getIngredient() { return ingredient; }
        public double getSimilarityScore() { return similarityScore; }
        public double getSafetyScore() { return safetyScore; }
        public double getFunctionalSimilarity() { return functionalSimilarity; }
        public double getEcoScore() { return ecoScore; }
        public double getRiskReduction() { return riskReduction; }
        public String getReason() { return reason; }
        public double getConfidence() { return confidence; }
        public List<String> getSources() { return sources; }
        
        public double getSafetyImprovement() { return safetyScore; }
    }
    
    public static class SubstitutionMapping {
        private final String original;
        private final List<SubstitutionCandidate> substitutes;
        private final String safetyJustification;
        private final double functionalEquivalence;
        private final double confidenceScore;
        private final String lastUpdated;
        
        public SubstitutionMapping(String original, List<SubstitutionCandidate> substitutes,
                                 String safetyJustification, double functionalEquivalence,
                                 double confidenceScore, String lastUpdated) {
            this.original = original;
            this.substitutes = substitutes;
            this.safetyJustification = safetyJustification;
            this.functionalEquivalence = functionalEquivalence;
            this.confidenceScore = confidenceScore;
            this.lastUpdated = lastUpdated;
        }
        
        // Getters
        public String getOriginal() { return original; }
        public List<SubstitutionCandidate> getSubstitutes() { return substitutes; }
        public String getSafetyJustification() { return safetyJustification; }
        public double getFunctionalEquivalence() { return functionalEquivalence; }
        public double getConfidenceScore() { return confidenceScore; }
        public String getLastUpdated() { return lastUpdated; }
    }
    
    public static class SafetyAnalysis {
        private final String ingredient;
        private final double safetyScore;
        private final String riskLevel;
        private final double ecoScore;
        private final boolean isProblematic;
        private final List<String> sources;
        private final String risksDetailed;
        private final String benefits;
        
        public SafetyAnalysis(String ingredient, double safetyScore, String riskLevel,
                            double ecoScore, boolean isProblematic, List<String> sources,
                            String risksDetailed, String benefits) {
            this.ingredient = ingredient;
            this.safetyScore = safetyScore;
            this.riskLevel = riskLevel;
            this.ecoScore = ecoScore;
            this.isProblematic = isProblematic;
            this.sources = sources;
            this.risksDetailed = risksDetailed;
            this.benefits = benefits;
        }
        
        // Getters
        public String getIngredient() { return ingredient; }
        public double getSafetyScore() { return safetyScore; }
        public String getRiskLevel() { return riskLevel; }
        public double getEcoScore() { return ecoScore; }
        public boolean isProblematic() { return isProblematic; }
        public List<String> getSources() { return sources; }
        public String getRisksDetailed() { return risksDetailed; }
        public String getBenefits() { return benefits; }
    }
    
    public static class AnalysisSummary {
        private final int totalIngredientsAnalyzed;
        private final int safeIngredients;
        private final int problematicIngredients;
        private final double averageSafetyScore;
        private final int ingredientsWithSubstitutes;
        private final int totalSubstituteOptions;
        private final String recommendation;
        
        public AnalysisSummary(int totalIngredientsAnalyzed, int safeIngredients,
                             int problematicIngredients, double averageSafetyScore,
                             int ingredientsWithSubstitutes, int totalSubstituteOptions,
                             String recommendation) {
            this.totalIngredientsAnalyzed = totalIngredientsAnalyzed;
            this.safeIngredients = safeIngredients;
            this.problematicIngredients = problematicIngredients;
            this.averageSafetyScore = averageSafetyScore;
            this.ingredientsWithSubstitutes = ingredientsWithSubstitutes;
            this.totalSubstituteOptions = totalSubstituteOptions;
            this.recommendation = recommendation;
        }
        
        // Getters
        public int getTotalIngredientsAnalyzed() { return totalIngredientsAnalyzed; }
        public int getSafeIngredients() { return safeIngredients; }
        public int getProblematicIngredients() { return problematicIngredients; }
        public double getAverageSafetyScore() { return averageSafetyScore; }
        public int getIngredientsWithSubstitutes() { return ingredientsWithSubstitutes; }
        public int getTotalSubstituteOptions() { return totalSubstituteOptions; }
        public String getRecommendation() { return recommendation; }
    }
    
    public static class EnhancedAnalysisResponse {
        private final String analysisTimestamp;
        private final int totalIngredients;
        private final int problematicIngredients;
        private final List<SafetyAnalysis> safetyAnalysis;
        private final Map<String, SubstitutionMapping> substitutionMappings;
        private final List<Map<String, Object>> productRecommendations;
        private final AnalysisSummary summary;
        
        public EnhancedAnalysisResponse(String analysisTimestamp, int totalIngredients,
                                     int problematicIngredients, List<SafetyAnalysis> safetyAnalysis,
                                     Map<String, SubstitutionMapping> substitutionMappings,
                                     List<Map<String, Object>> productRecommendations,
                                     AnalysisSummary summary) {
            this.analysisTimestamp = analysisTimestamp;
            this.totalIngredients = totalIngredients;
            this.problematicIngredients = problematicIngredients;
            this.safetyAnalysis = safetyAnalysis;
            this.substitutionMappings = substitutionMappings;
            this.productRecommendations = productRecommendations;
            this.summary = summary;
        }
        
        // Getters
        public String getAnalysisTimestamp() { return analysisTimestamp; }
        public int getTotalIngredients() { return totalIngredients; }
        public int getProblematicIngredients() { return problematicIngredients; }
        public List<SafetyAnalysis> getSafetyAnalysis() { return safetyAnalysis; }
        public Map<String, SubstitutionMapping> getSubstitutionMappings() { return substitutionMappings; }
        public List<Map<String, Object>> getProductRecommendations() { return productRecommendations; }
        public AnalysisSummary getSummary() { return summary; }
    }
}