package com.mommyshops.recommendation.service;

import com.mommyshops.profile.domain.UserProfile;
import com.mommyshops.recommendation.domain.RecommendationFeedback;
import com.mommyshops.recommendation.repository.RecommendationFeedbackRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@Transactional
public class RecommendationService {
    
    private final RecommendationFeedbackRepository feedbackRepository;
    private final EnhancedRecommendationService enhancedRecommendationService;
    
    @Autowired
    public RecommendationService(RecommendationFeedbackRepository feedbackRepository,
                               EnhancedRecommendationService enhancedRecommendationService) {
        this.feedbackRepository = feedbackRepository;
        this.enhancedRecommendationService = enhancedRecommendationService;
    }
    
    public List<SubstituteRecommendation> generatePersonalizedRecommendations(
            String originalIngredient, 
            UserProfile userProfile, 
            List<String> excludedIngredients) {
        
        // Use the enhanced recommendation service for ML-based recommendations
        List<EnhancedRecommendationService.SubstituteRecommendation> enhancedRecs = 
            enhancedRecommendationService.generatePersonalizedRecommendations(
                originalIngredient, userProfile, excludedIngredients);
        
        // Convert to the original format
        return enhancedRecs.stream()
            .map(this::convertToOriginalFormat)
            .collect(Collectors.toList());
    }
    
    private SubstituteRecommendation convertToOriginalFormat(EnhancedRecommendationService.SubstituteRecommendation enhanced) {
        SubstituteRecommendation original = new SubstituteRecommendation();
        original.setIngredient(enhanced.getIngredient());
        original.setSafetyScore(enhanced.getSafetyScore());
        original.setEcoFriendlinessScore(enhanced.getEcoFriendlinessScore());
        original.setBenefits(enhanced.getBenefits());
        original.setReasoning(enhanced.getReasoning());
        original.setAvailability(enhanced.getAvailability());
        original.setCost(enhanced.getCost());
        original.setConfidence(enhanced.getConfidence());
        return original;
    }
    
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
    
    public List<RecommendationFeedback> getUserFeedback(UUID userId) {
        return feedbackRepository.findByUserIdOrderByCreatedAtDesc(userId);
    }
    
    public double getAverageRatingForRecommendation(String recommendationType) {
        return feedbackRepository.findByRecommendationType(recommendationType)
            .stream()
            .mapToInt(RecommendationFeedback::getRating)
            .average()
            .orElse(0.0);
    }
    
    // Data class for substitute recommendations
    public static class SubstituteRecommendation {
        private String ingredient;
        private int safetyScore;
        private int ecoFriendlinessScore;
        private List<String> benefits;
        private String reasoning;
        private String availability;
        private String cost;
        private int confidence;
        
        // Constructors, getters, and setters
        public SubstituteRecommendation() {}
        
        public SubstituteRecommendation(String ingredient, int safetyScore, int ecoFriendlinessScore, 
                                      List<String> benefits, String reasoning, String availability, 
                                      String cost, int confidence) {
            this.ingredient = ingredient;
            this.safetyScore = safetyScore;
            this.ecoFriendlinessScore = ecoFriendlinessScore;
            this.benefits = benefits;
            this.reasoning = reasoning;
            this.availability = availability;
            this.cost = cost;
            this.confidence = confidence;
        }
        
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