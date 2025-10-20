package com.mommyshops.recommendation.domain;

import jakarta.persistence.*;
import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "recommendation_feedback")
public class RecommendationFeedback {
    
    @Id
    private UUID id;
    
    @Column(name = "user_id", nullable = false)
    private UUID userId;
    
    @Column(name = "analysis_id", nullable = false)
    private UUID analysisId;
    
    @Column(name = "recommendation_type", nullable = false)
    private String recommendationType;
    
    @Column(name = "rating", nullable = false)
    private Integer rating;
    
    @Column(name = "comments", columnDefinition = "TEXT")
    private String comments;
    
    @Column(name = "created_at", nullable = false)
    private OffsetDateTime createdAt;
    
    // Constructors
    public RecommendationFeedback() {}
    
    public RecommendationFeedback(UUID id, UUID userId, UUID analysisId, String recommendationType, 
                                Integer rating, String comments, OffsetDateTime createdAt) {
        this.id = id;
        this.userId = userId;
        this.analysisId = analysisId;
        this.recommendationType = recommendationType;
        this.rating = rating;
        this.comments = comments;
        this.createdAt = createdAt;
    }
    
    // Getters and setters
    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }
    
    public UUID getUserId() { return userId; }
    public void setUserId(UUID userId) { this.userId = userId; }
    
    public UUID getAnalysisId() { return analysisId; }
    public void setAnalysisId(UUID analysisId) { this.analysisId = analysisId; }
    
    public String getRecommendationType() { return recommendationType; }
    public void setRecommendationType(String recommendationType) { this.recommendationType = recommendationType; }
    
    public Integer getRating() { return rating; }
    public void setRating(Integer rating) { this.rating = rating; }
    
    public String getComments() { return comments; }
    public void setComments(String comments) { this.comments = comments; }
    
    public OffsetDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(OffsetDateTime createdAt) { this.createdAt = createdAt; }
}