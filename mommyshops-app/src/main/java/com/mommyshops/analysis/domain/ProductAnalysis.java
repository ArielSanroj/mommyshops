package com.mommyshops.analysis.domain;

import jakarta.persistence.*;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "product_analysis")
public class ProductAnalysis {
    
    @Id
    private UUID id;
    
    @Column(name = "user_id", nullable = false)
    private UUID userId;
    
    @Column(name = "product_name", nullable = false)
    private String productName;
    
    @Column(name = "ingredient_source", columnDefinition = "TEXT")
    private String ingredientSource;
    
    @Column(name = "analysis_summary", columnDefinition = "TEXT")
    private String analysisSummary;
    
    @Column(name = "analyzed_at", nullable = false)
    private OffsetDateTime analyzedAt;
    
    @Column(name = "confidence_score")
    private Integer confidenceScore;
    
    // Constructors
    public ProductAnalysis() {}
    
    public ProductAnalysis(UUID id, UUID userId, String productName, String ingredientSource, 
                          String analysisSummary, OffsetDateTime analyzedAt, Integer confidenceScore) {
        this.id = id;
        this.userId = userId;
        this.productName = productName;
        this.ingredientSource = ingredientSource;
        this.analysisSummary = analysisSummary;
        this.analyzedAt = analyzedAt;
        this.confidenceScore = confidenceScore;
    }
    
    // Getters and setters
    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }
    
    public UUID getUserId() { return userId; }
    public void setUserId(UUID userId) { this.userId = userId; }
    
    public String getProductName() { return productName; }
    public void setProductName(String productName) { this.productName = productName; }
    
    public String getIngredientSource() { return ingredientSource; }
    public void setIngredientSource(String ingredientSource) { this.ingredientSource = ingredientSource; }
    
    public String getAnalysisSummary() { return analysisSummary; }
    public void setAnalysisSummary(String analysisSummary) { this.analysisSummary = analysisSummary; }
    
    public OffsetDateTime getAnalyzedAt() { return analyzedAt; }
    public void setAnalyzedAt(OffsetDateTime analyzedAt) { this.analyzedAt = analyzedAt; }
    
    public Integer getConfidenceScore() { return confidenceScore; }
    public void setConfidenceScore(Integer confidenceScore) { this.confidenceScore = confidenceScore; }
    
    // Helper method for frontend compatibility
    public List<String> getRiskFlags() {
        // This is a placeholder - in a real implementation, you'd parse the analysisSummary
        // or store risk flags separately in the database
        return List.of("No risk flags available");
    }
}