package com.mommyshops.recommendation.service;

import com.mommyshops.profile.domain.UserProfile;
import com.mommyshops.recommendation.domain.RecommendationFeedback;
import com.mommyshops.recommendation.repository.RecommendationFeedbackRepository;
import com.mommyshops.ai.service.OllamaService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Enhanced recommendation service with ML-based substitute generation
 * Based on the Python enhanced_substitution_mapping.py functionality
 */
@Service
@Transactional
public class EnhancedRecommendationService {
    
    private final RecommendationFeedbackRepository feedbackRepository;
    private final OllamaService ollamaService;
    
    // Enhanced substitution mapping based on ingredient categories and safety profiles
    private static final Map<String, List<SubstituteMapping>> SUBSTITUTION_MAPPINGS = Map.of(
        "sulfates", List.of(
            new SubstituteMapping("Cocamidopropyl Betaine", 85, 90, "Gentle surfactant", "common", "medium"),
            new SubstituteMapping("Sodium Coco Sulfate", 75, 85, "Natural sulfate alternative", "moderate", "medium"),
            new SubstituteMapping("Decyl Glucoside", 90, 95, "Plant-based surfactant", "common", "high"),
            new SubstituteMapping("Lauryl Glucoside", 88, 92, "Mild glucoside surfactant", "moderate", "high")
        ),
        "parabens", List.of(
            new SubstituteMapping("Phenoxyethanol", 70, 75, "Gentle preservative", "common", "low"),
            new SubstituteMapping("Ethylhexylglycerin", 85, 90, "Natural preservative", "moderate", "medium"),
            new SubstituteMapping("Caprylyl Glycol", 80, 85, "Multi-functional preservative", "common", "medium"),
            new SubstituteMapping("Benzyl Alcohol", 75, 80, "Alcohol-based preservative", "common", "low")
        ),
        "fragrance", List.of(
            new SubstituteMapping("Essential Oils", 85, 95, "Natural fragrance", "common", "high"),
            new SubstituteMapping("Natural Extracts", 90, 98, "Plant-based fragrance", "moderate", "high"),
            new SubstituteMapping("Unscented", 95, 100, "No fragrance added", "common", "low"),
            new SubstituteMapping("Hypoallergenic Fragrance", 80, 85, "Sensitive skin friendly", "moderate", "medium")
        ),
        "alcohol", List.of(
            new SubstituteMapping("Glycerin", 95, 100, "Humectant moisturizer", "common", "low"),
            new SubstituteMapping("Hyaluronic Acid", 98, 100, "Hydrating ingredient", "common", "medium"),
            new SubstituteMapping("Squalane", 90, 95, "Natural moisturizer", "moderate", "high"),
            new SubstituteMapping("Ceramides", 95, 98, "Skin barrier repair", "common", "high")
        ),
        "formaldehyde", List.of(
            new SubstituteMapping("Phenoxyethanol", 70, 75, "Gentle preservative", "common", "low"),
            new SubstituteMapping("Ethylhexylglycerin", 85, 90, "Natural preservative", "moderate", "medium"),
            new SubstituteMapping("Caprylyl Glycol", 80, 85, "Multi-functional preservative", "common", "medium"),
            new SubstituteMapping("Natural Preservatives", 90, 95, "Plant-based preservation", "moderate", "high")
        )
    );
    
    // Ingredient category mapping
    private static final Map<String, String> INGREDIENT_CATEGORIES = new HashMap<String, String>() {{
        put("sodium lauryl sulfate", "sulfates");
        put("sodium laureth sulfate", "sulfates");
        put("ammonium lauryl sulfate", "sulfates");
        put("methylparaben", "parabens");
        put("propylparaben", "parabens");
        put("butylparaben", "parabens");
        put("fragrance", "fragrance");
        put("parfum", "fragrance");
        put("alcohol", "alcohol");
        put("ethanol", "alcohol");
        put("formaldehyde", "formaldehyde");
        put("dmdm hydantoin", "formaldehyde");
    }};
    
    @Autowired
    public EnhancedRecommendationService(RecommendationFeedbackRepository feedbackRepository,
                                       OllamaService ollamaService) {
        this.feedbackRepository = feedbackRepository;
        this.ollamaService = ollamaService;
    }
    
    /**
     * Generate personalized substitute recommendations using ML-based approach
     */
    public List<SubstituteRecommendation> generatePersonalizedRecommendations(
            String originalIngredient, 
            UserProfile userProfile, 
            List<String> excludedIngredients) {
        
        List<SubstituteRecommendation> recommendations = new ArrayList<>();
        
        try {
            // 1. Categorize the original ingredient
            String category = categorizeIngredient(originalIngredient);
            
            // 2. Get base substitutions for the category
            List<SubstituteMapping> baseSubstitutes = SUBSTITUTION_MAPPINGS.getOrDefault(category, new ArrayList<>());
            
            // 3. Filter out excluded ingredients
            baseSubstitutes = baseSubstitutes.stream()
                .filter(sub -> !excludedIngredients.contains(sub.getIngredient().toLowerCase()))
                .collect(Collectors.toList());
            
            // 4. Personalize based on user profile
            List<SubstituteMapping> personalizedSubstitutes = personalizeSubstitutes(baseSubstitutes, userProfile);
            
            // 5. Score and rank recommendations
            List<SubstituteRecommendation> scoredRecommendations = scoreRecommendations(
                personalizedSubstitutes, originalIngredient, userProfile);
            
            // 6. Get AI-enhanced recommendations
            List<SubstituteRecommendation> aiRecommendations = getAIEnhancedRecommendations(
                originalIngredient, userProfile, excludedIngredients);
            
            // 7. Combine and deduplicate recommendations
            recommendations = combineRecommendations(scoredRecommendations, aiRecommendations);
            
            // 8. Limit to top recommendations
            return recommendations.stream()
                .sorted((a, b) -> Integer.compare(b.getConfidence(), a.getConfidence()))
                .limit(5)
                .collect(Collectors.toList());
                
        } catch (Exception e) {
            // Fallback to basic recommendations
            return generateBasicRecommendations(originalIngredient, userProfile);
        }
    }
    
    /**
     * Categorize ingredient based on its properties
     */
    private String categorizeIngredient(String ingredient) {
        String ingredientLower = ingredient.toLowerCase();
        
        return INGREDIENT_CATEGORIES.entrySet().stream()
            .filter(entry -> ingredientLower.contains(entry.getKey()))
            .map(Map.Entry::getValue)
            .findFirst()
            .orElse("other");
    }
    
    /**
     * Personalize substitutes based on user profile
     */
    private List<SubstituteMapping> personalizeSubstitutes(List<SubstituteMapping> substitutes, UserProfile profile) {
        return substitutes.stream()
            .map(sub -> personalizeSubstitute(sub, profile))
            .collect(Collectors.toList());
    }
    
    /**
     * Personalize a single substitute based on user profile
     */
    private SubstituteMapping personalizeSubstitute(SubstituteMapping substitute, UserProfile profile) {
        int adjustedSafetyScore = substitute.getSafetyScore();
        int adjustedEcoScore = substitute.getEcoScore();
        String adjustedReasoning = substitute.getReasoning();
        
        // Adjust based on skin preferences
        if (profile.getFacialSkinPreferences().toLowerCase().contains("sensitive")) {
            adjustedSafetyScore = Math.min(100, adjustedSafetyScore + 10);
            adjustedReasoning += " Ideal para piel sensible.";
        }
        
        if (profile.getFacialSkinPreferences().toLowerCase().contains("acne")) {
            adjustedSafetyScore = Math.min(100, adjustedSafetyScore + 5);
            adjustedReasoning += " Recomendado para piel propensa al acné.";
        }
        
        // Adjust based on brand preferences
        if (profile.getBrandPreferences().toLowerCase().contains("natural")) {
            adjustedEcoScore = Math.min(100, adjustedEcoScore + 10);
            adjustedReasoning += " Ingrediente natural y eco-amigable.";
        }
        
        if (profile.getBrandPreferences().toLowerCase().contains("organic")) {
            adjustedEcoScore = Math.min(100, adjustedEcoScore + 15);
            adjustedReasoning += " Ingrediente orgánico certificado.";
        }
        
        // Adjust based on budget preferences
        if (profile.getBudgetPreferences().toLowerCase().contains("economic")) {
            substitute = new SubstituteMapping(
                substitute.getIngredient(),
                adjustedSafetyScore,
                adjustedEcoScore,
                adjustedReasoning + " Opción económica disponible.",
                "common",
                "low"
            );
        } else if (profile.getBudgetPreferences().toLowerCase().contains("premium")) {
            substitute = new SubstituteMapping(
                substitute.getIngredient(),
                adjustedSafetyScore,
                adjustedEcoScore,
                adjustedReasoning + " Ingrediente premium de alta calidad.",
                "moderate",
                "high"
            );
        }
        
        return substitute;
    }
    
    /**
     * Score and rank recommendations
     */
    private List<SubstituteRecommendation> scoreRecommendations(List<SubstituteMapping> substitutes, 
                                                               String originalIngredient, 
                                                               UserProfile profile) {
        return substitutes.stream()
            .map(sub -> {
                SubstituteRecommendation rec = new SubstituteRecommendation();
                rec.setIngredient(sub.getIngredient());
                rec.setSafetyScore(sub.getSafetyScore());
                rec.setEcoFriendlinessScore(sub.getEcoScore());
                rec.setReasoning(sub.getReasoning());
                rec.setAvailability(sub.getAvailability());
                rec.setCost(sub.getCost());
                
                // Calculate confidence score
                int confidence = calculateConfidenceScore(sub, originalIngredient, profile);
                rec.setConfidence(confidence);
                
                // Generate benefits
                rec.setBenefits(generateBenefits(sub, profile));
                
                return rec;
            })
            .collect(Collectors.toList());
    }
    
    /**
     * Calculate confidence score for a recommendation
     */
    private int calculateConfidenceScore(SubstituteMapping substitute, String originalIngredient, UserProfile profile) {
        int baseConfidence = 70;
        
        // Adjust based on safety score
        if (substitute.getSafetyScore() >= 90) baseConfidence += 15;
        else if (substitute.getSafetyScore() >= 80) baseConfidence += 10;
        else if (substitute.getSafetyScore() >= 70) baseConfidence += 5;
        
        // Adjust based on eco score
        if (substitute.getEcoScore() >= 90) baseConfidence += 10;
        else if (substitute.getEcoScore() >= 80) baseConfidence += 5;
        
        // Adjust based on availability
        if ("common".equals(substitute.getAvailability())) baseConfidence += 10;
        else if ("moderate".equals(substitute.getAvailability())) baseConfidence += 5;
        
        // Adjust based on user profile match
        if (profile.getBrandPreferences().toLowerCase().contains("natural") && 
            substitute.getReasoning().toLowerCase().contains("natural")) {
            baseConfidence += 10;
        }
        
        return Math.min(100, baseConfidence);
    }
    
    /**
     * Generate benefits for a substitute
     */
    private List<String> generateBenefits(SubstituteMapping substitute, UserProfile profile) {
        List<String> benefits = new ArrayList<>();
        
        if (substitute.getSafetyScore() >= 85) {
            benefits.add("Alta seguridad");
        }
        if (substitute.getEcoScore() >= 85) {
            benefits.add("Eco-amigable");
        }
        if (substitute.getReasoning().toLowerCase().contains("natural")) {
            benefits.add("Origen natural");
        }
        if (substitute.getReasoning().toLowerCase().contains("gentle")) {
            benefits.add("Suave para la piel");
        }
        if (profile.getFacialSkinPreferences().toLowerCase().contains("sensitive") && 
            substitute.getSafetyScore() >= 80) {
            benefits.add("Ideal para piel sensible");
        }
        
        return benefits;
    }
    
    /**
     * Get AI-enhanced recommendations using Ollama
     */
    private List<SubstituteRecommendation> getAIEnhancedRecommendations(String originalIngredient, 
                                                                       UserProfile profile, 
                                                                       List<String> excludedIngredients) {
        try {
            // Create a mock analysis for the original ingredient
            OllamaService.IngredientAnalysis mockAnalysis = new OllamaService.IngredientAnalysis();
            mockAnalysis.setIngredient(originalIngredient);
            mockAnalysis.setSafetyScore(50); // Default score
            mockAnalysis.setEcoFriendlinessScore(50);
            
            // Get AI recommendations
            List<OllamaService.SubstituteRecommendation> aiRecs = ollamaService.generateSubstitutes(
                originalIngredient, mockAnalysis, profile);
            
            // Convert to our format
            return aiRecs.stream()
                .filter(rec -> !excludedIngredients.contains(rec.getIngredient().toLowerCase()))
                .map(rec -> {
                    SubstituteRecommendation subRec = new SubstituteRecommendation();
                    subRec.setIngredient(rec.getIngredient());
                    subRec.setSafetyScore(rec.getSafetyScore());
                    subRec.setEcoFriendlinessScore(rec.getEcoFriendlinessScore());
                    subRec.setBenefits(rec.getBenefits());
                    subRec.setReasoning(rec.getReasoning());
                    subRec.setAvailability(rec.getAvailability());
                    subRec.setCost(rec.getCost());
                    subRec.setConfidence(rec.getConfidence());
                    return subRec;
                })
                .collect(Collectors.toList());
                
        } catch (Exception e) {
            return new ArrayList<>();
        }
    }
    
    /**
     * Combine ML-based and AI-based recommendations
     */
    private List<SubstituteRecommendation> combineRecommendations(List<SubstituteRecommendation> mlRecs, 
                                                                List<SubstituteRecommendation> aiRecs) {
        Map<String, SubstituteRecommendation> combined = new HashMap<>();
        
        // Add ML recommendations
        for (SubstituteRecommendation rec : mlRecs) {
            combined.put(rec.getIngredient().toLowerCase(), rec);
        }
        
        // Add AI recommendations (prefer higher confidence)
        for (SubstituteRecommendation rec : aiRecs) {
            String key = rec.getIngredient().toLowerCase();
            if (!combined.containsKey(key) || combined.get(key).getConfidence() < rec.getConfidence()) {
                combined.put(key, rec);
            }
        }
        
        return new ArrayList<>(combined.values());
    }
    
    /**
     * Generate basic recommendations as fallback
     */
    private List<SubstituteRecommendation> generateBasicRecommendations(String originalIngredient, UserProfile profile) {
        List<SubstituteRecommendation> recommendations = new ArrayList<>();
        
        // Basic fallback recommendations
        SubstituteRecommendation basicRec = new SubstituteRecommendation();
        basicRec.setIngredient("Ingrediente natural alternativo");
        basicRec.setSafetyScore(80);
        basicRec.setEcoFriendlinessScore(85);
        basicRec.setBenefits(List.of("Natural", "Eco-amigable"));
        basicRec.setReasoning("Alternativa natural y segura");
        basicRec.setAvailability("common");
        basicRec.setCost("medium");
        basicRec.setConfidence(60);
        
        recommendations.add(basicRec);
        return recommendations;
    }
    
    /**
     * Record feedback for recommendations
     */
    public void recordFeedback(UUID userId, UUID analysisId, String recommendationType, 
                             int rating, String comments) {
        RecommendationFeedback feedback = new RecommendationFeedback(
            UUID.randomUUID(),
            userId,
            analysisId,
            recommendationType,
            rating,
            comments,
            OffsetDateTime.now()
        );
        
        feedbackRepository.save(feedback);
    }
    
    /**
     * Get user feedback history
     */
    public List<RecommendationFeedback> getUserFeedback(UUID userId) {
        return feedbackRepository.findByUserIdOrderByCreatedAtDesc(userId);
    }
    
    /**
     * Get average rating for a recommendation type
     */
    public double getAverageRatingForRecommendation(String recommendationType) {
        return feedbackRepository.findByRecommendationType(recommendationType)
            .stream()
            .mapToInt(RecommendationFeedback::getRating)
            .average()
            .orElse(0.0);
    }
    
    /**
     * Data class for substitute mappings
     */
    private static class SubstituteMapping {
        private final String ingredient;
        private final int safetyScore;
        private final int ecoScore;
        private final String reasoning;
        private final String availability;
        private final String cost;
        
        public SubstituteMapping(String ingredient, int safetyScore, int ecoScore, 
                               String reasoning, String availability, String cost) {
            this.ingredient = ingredient;
            this.safetyScore = safetyScore;
            this.ecoScore = ecoScore;
            this.reasoning = reasoning;
            this.availability = availability;
            this.cost = cost;
        }
        
        public String getIngredient() { return ingredient; }
        public int getSafetyScore() { return safetyScore; }
        public int getEcoScore() { return ecoScore; }
        public String getReasoning() { return reasoning; }
        public String getAvailability() { return availability; }
        public String getCost() { return cost; }
    }
    
    /**
     * Data class for substitute recommendations
     */
    public static class SubstituteRecommendation {
        private String ingredient;
        private int safetyScore;
        private int ecoFriendlinessScore;
        private List<String> benefits;
        private String reasoning;
        private String availability;
        private String cost;
        private int confidence;
        
        // Getters and setters
        public String getIngredient() { return ingredient; }
        public void setIngredient(String ingredient) { this.ingredient = ingredient; }
        public int getSafetyScore() { return safetyScore; }
        public void setSafetyScore(int safetyScore) { this.safetyScore = safetyScore; }
        public int getEcoFriendlinessScore() { return ecoFriendlinessScore; }
        public void setEcoFriendlinessScore(int ecoFriendlinessScore) { this.ecoFriendlinessScore = ecoFriendlinessScore; }
        public List<String> getBenefits() { return benefits; }
        public void setBenefits(List<String> benefits) { this.benefits = benefits; }
        public String getReasoning() { return reasoning; }
        public void setReasoning(String reasoning) { this.reasoning = reasoning; }
        public String getAvailability() { return availability; }
        public void setAvailability(String availability) { this.availability = availability; }
        public String getCost() { return cost; }
        public void setCost(String cost) { this.cost = cost; }
        public int getConfidence() { return confidence; }
        public void setConfidence(int confidence) { this.confidence = confidence; }
    }
}