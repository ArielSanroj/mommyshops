package com.mommyshops.analysis.domain;

import jakarta.persistence.*;
import java.time.OffsetDateTime;
import java.util.UUID;

/**
 * Enhanced ProductAnalysis with additional fields for structured analysis data
 * Based on the Python analyze_* modules functionality
 */
@Entity
@Table(name = "product_analysis_enhanced")
public class ProductAnalysisEnhanced {
    
    @Id
    private UUID id;
    
    @Column(name = "user_id", nullable = false)
    private UUID userId;
    
    @Column(name = "product_name", nullable = false)
    private String productName;
    
    @Column(name = "brand")
    private String brand;
    
    @Column(name = "product_type")
    private String productType;
    
    @Column(name = "ingredient_source", columnDefinition = "TEXT")
    private String ingredientSource;
    
    @Column(name = "analysis_summary", columnDefinition = "TEXT")
    private String analysisSummary;
    
    @Column(name = "analyzed_at")
    private OffsetDateTime analyzedAt;
    
    @Column(name = "confidence_score")
    private Integer confidenceScore;
    
    // Enhanced analysis fields
    @Column(name = "overall_safety_score")
    private Integer overallSafetyScore;
    
    @Column(name = "overall_eco_score")
    private Integer overallEcoScore;
    
    @Column(name = "recommendation")
    private String recommendation;
    
    @Column(name = "risk_level")
    private String riskLevel;
    
    // Risk flags as JSON
    @Column(name = "risk_flags", columnDefinition = "TEXT")
    private String riskFlagsJson;
    
    // Ingredient analysis as JSON
    @Column(name = "ingredient_analysis", columnDefinition = "TEXT")
    private String ingredientAnalysisJson;
    
    // External API data as JSON
    @Column(name = "external_data", columnDefinition = "TEXT")
    private String externalDataJson;
    
    // Cosmetic information as JSON
    @Column(name = "cosmetic_info", columnDefinition = "TEXT")
    private String cosmeticInfoJson;
    
    // AI insights as JSON
    @Column(name = "ai_insights", columnDefinition = "TEXT")
    private String aiInsightsJson;
    
    // Analysis metadata
    @Column(name = "analysis_method")
    private String analysisMethod; // "manual", "image", "url", "enhanced_image"
    
    @Column(name = "processing_time_ms")
    private Long processingTimeMs;
    
    @Column(name = "ingredient_count")
    private Integer ingredientCount;
    
    @Column(name = "safe_ingredient_count")
    private Integer safeIngredientCount;
    
    @Column(name = "moderate_ingredient_count")
    private Integer moderateIngredientCount;
    
    @Column(name = "caution_ingredient_count")
    private Integer cautionIngredientCount;
    
    // Constructors
    public ProductAnalysisEnhanced() {}
    
    public ProductAnalysisEnhanced(UUID id, UUID userId, String productName) {
        this.id = id;
        this.userId = userId;
        this.productName = productName;
        this.analyzedAt = OffsetDateTime.now();
    }
    
    // Getters and setters
    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }
    
    public UUID getUserId() { return userId; }
    public void setUserId(UUID userId) { this.userId = userId; }
    
    public String getProductName() { return productName; }
    public void setProductName(String productName) { this.productName = productName; }
    
    public String getBrand() { return brand; }
    public void setBrand(String brand) { this.brand = brand; }
    
    public String getProductType() { return productType; }
    public void setProductType(String productType) { this.productType = productType; }
    
    public String getIngredientSource() { return ingredientSource; }
    public void setIngredientSource(String ingredientSource) { this.ingredientSource = ingredientSource; }
    
    public String getAnalysisSummary() { return analysisSummary; }
    public void setAnalysisSummary(String analysisSummary) { this.analysisSummary = analysisSummary; }
    
    public OffsetDateTime getAnalyzedAt() { return analyzedAt; }
    public void setAnalyzedAt(OffsetDateTime analyzedAt) { this.analyzedAt = analyzedAt; }
    
    public Integer getConfidenceScore() { return confidenceScore; }
    public void setConfidenceScore(Integer confidenceScore) { this.confidenceScore = confidenceScore; }
    
    public Integer getOverallSafetyScore() { return overallSafetyScore; }
    public void setOverallSafetyScore(Integer overallSafetyScore) { this.overallSafetyScore = overallSafetyScore; }
    
    public Integer getOverallEcoScore() { return overallEcoScore; }
    public void setOverallEcoScore(Integer overallEcoScore) { this.overallEcoScore = overallEcoScore; }
    
    public String getRecommendation() { return recommendation; }
    public void setRecommendation(String recommendation) { this.recommendation = recommendation; }
    
    public String getRiskLevel() { return riskLevel; }
    public void setRiskLevel(String riskLevel) { this.riskLevel = riskLevel; }
    
    public String getRiskFlagsJson() { return riskFlagsJson; }
    public void setRiskFlagsJson(String riskFlagsJson) { this.riskFlagsJson = riskFlagsJson; }
    
    public String getIngredientAnalysisJson() { return ingredientAnalysisJson; }
    public void setIngredientAnalysisJson(String ingredientAnalysisJson) { this.ingredientAnalysisJson = ingredientAnalysisJson; }
    
    public String getExternalDataJson() { return externalDataJson; }
    public void setExternalDataJson(String externalDataJson) { this.externalDataJson = externalDataJson; }
    
    public String getCosmeticInfoJson() { return cosmeticInfoJson; }
    public void setCosmeticInfoJson(String cosmeticInfoJson) { this.cosmeticInfoJson = cosmeticInfoJson; }
    
    public String getAiInsightsJson() { return aiInsightsJson; }
    public void setAiInsightsJson(String aiInsightsJson) { this.aiInsightsJson = aiInsightsJson; }
    
    public String getAnalysisMethod() { return analysisMethod; }
    public void setAnalysisMethod(String analysisMethod) { this.analysisMethod = analysisMethod; }
    
    public Long getProcessingTimeMs() { return processingTimeMs; }
    public void setProcessingTimeMs(Long processingTimeMs) { this.processingTimeMs = processingTimeMs; }
    
    public Integer getIngredientCount() { return ingredientCount; }
    public void setIngredientCount(Integer ingredientCount) { this.ingredientCount = ingredientCount; }
    
    public Integer getSafeIngredientCount() { return safeIngredientCount; }
    public void setSafeIngredientCount(Integer safeIngredientCount) { this.safeIngredientCount = safeIngredientCount; }
    
    public Integer getModerateIngredientCount() { return moderateIngredientCount; }
    public void setModerateIngredientCount(Integer moderateIngredientCount) { this.moderateIngredientCount = moderateIngredientCount; }
    
    public Integer getCautionIngredientCount() { return cautionIngredientCount; }
    public void setCautionIngredientCount(Integer cautionIngredientCount) { this.cautionIngredientCount = cautionIngredientCount; }
    
    // Helper methods for risk level calculation
    public void calculateRiskLevel() {
        if (overallSafetyScore == null) {
            this.riskLevel = "unknown";
            return;
        }
        
        if (overallSafetyScore >= 80) {
            this.riskLevel = "low";
        } else if (overallSafetyScore >= 60) {
            this.riskLevel = "moderate";
        } else if (overallSafetyScore >= 40) {
            this.riskLevel = "high";
        } else {
            this.riskLevel = "very_high";
        }
    }
    
    // Helper method to get ingredient counts
    public void calculateIngredientCounts() {
        if (ingredientSource == null || ingredientSource.isEmpty()) {
            this.ingredientCount = 0;
            this.safeIngredientCount = 0;
            this.moderateIngredientCount = 0;
            this.cautionIngredientCount = 0;
            return;
        }
        
        String[] ingredients = ingredientSource.split("[,;]");
        this.ingredientCount = ingredients.length;
        
        // This would be calculated based on the actual ingredient analysis
        // For now, set to 0 - would be populated by the analysis service
        this.safeIngredientCount = 0;
        this.moderateIngredientCount = 0;
        this.cautionIngredientCount = 0;
    }
    
    // Helper method to get processing time
    public void setProcessingTime(OffsetDateTime startTime) {
        if (startTime != null && analyzedAt != null) {
            this.processingTimeMs = java.time.Duration.between(startTime, analyzedAt).toMillis();
        }
    }
}