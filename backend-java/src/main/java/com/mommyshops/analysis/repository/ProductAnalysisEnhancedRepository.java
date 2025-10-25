package com.mommyshops.analysis.repository;

import com.mommyshops.analysis.domain.ProductAnalysisEnhanced;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

/**
 * Repository for enhanced product analysis data
 */
@Repository
public interface ProductAnalysisEnhancedRepository extends JpaRepository<ProductAnalysisEnhanced, UUID> {
    
    /**
     * Find analyses by user ID, ordered by analysis date (most recent first)
     */
    List<ProductAnalysisEnhanced> findByUserIdOrderByAnalyzedAtDesc(UUID userId);
    
    /**
     * Find analyses by user ID and date range
     */
    List<ProductAnalysisEnhanced> findByUserIdAndAnalyzedAtBetweenOrderByAnalyzedAtDesc(
        UUID userId, OffsetDateTime startDate, OffsetDateTime endDate);
    
    /**
     * Find analyses by risk level
     */
    List<ProductAnalysisEnhanced> findByRiskLevelOrderByAnalyzedAtDesc(String riskLevel);
    
    /**
     * Find analyses by user ID and risk level
     */
    List<ProductAnalysisEnhanced> findByUserIdAndRiskLevelOrderByAnalyzedAtDesc(UUID userId, String riskLevel);
    
    /**
     * Find analyses by recommendation type
     */
    List<ProductAnalysisEnhanced> findByRecommendationOrderByAnalyzedAtDesc(String recommendation);
    
    /**
     * Find analyses by user ID and recommendation
     */
    List<ProductAnalysisEnhanced> findByUserIdAndRecommendationOrderByAnalyzedAtDesc(UUID userId, String recommendation);
    
    /**
     * Find analyses by analysis method
     */
    List<ProductAnalysisEnhanced> findByAnalysisMethodOrderByAnalyzedAtDesc(String analysisMethod);
    
    /**
     * Find analyses by user ID and analysis method
     */
    List<ProductAnalysisEnhanced> findByUserIdAndAnalysisMethodOrderByAnalyzedAtDesc(UUID userId, String analysisMethod);
    
    /**
     * Count analyses by user ID
     */
    long countByUserId(UUID userId);
    
    /**
     * Count analyses by user ID and risk level
     */
    long countByUserIdAndRiskLevel(UUID userId, String riskLevel);
    
    /**
     * Count analyses by user ID and recommendation
     */
    long countByUserIdAndRecommendation(UUID userId, String recommendation);
    
    /**
     * Find analyses with high risk level (safety score < 40)
     */
    @Query("SELECT p FROM ProductAnalysisEnhanced p WHERE p.overallSafetyScore < 40 ORDER BY p.analyzedAt DESC")
    List<ProductAnalysisEnhanced> findHighRiskAnalyses();
    
    /**
     * Find analyses with low risk level (safety score >= 80)
     */
    @Query("SELECT p FROM ProductAnalysisEnhanced p WHERE p.overallSafetyScore >= 80 ORDER BY p.analyzedAt DESC")
    List<ProductAnalysisEnhanced> findLowRiskAnalyses();
    
    /**
     * Find analyses by ingredient count range
     */
    @Query("SELECT p FROM ProductAnalysisEnhanced p WHERE p.ingredientCount BETWEEN :minCount AND :maxCount ORDER BY p.analyzedAt DESC")
    List<ProductAnalysisEnhanced> findByIngredientCountRange(@Param("minCount") int minCount, @Param("maxCount") int maxCount);
    
    /**
     * Find analyses by processing time range (in milliseconds)
     */
    @Query("SELECT p FROM ProductAnalysisEnhanced p WHERE p.processingTimeMs BETWEEN :minTime AND :maxTime ORDER BY p.analyzedAt DESC")
    List<ProductAnalysisEnhanced> findByProcessingTimeRange(@Param("minTime") long minTime, @Param("maxTime") long maxTime);
    
    /**
     * Find analyses by brand
     */
    List<ProductAnalysisEnhanced> findByBrandOrderByAnalyzedAtDesc(String brand);
    
    /**
     * Find analyses by product type
     */
    List<ProductAnalysisEnhanced> findByProductTypeOrderByAnalyzedAtDesc(String productType);
    
    /**
     * Find analyses by user ID and brand
     */
    List<ProductAnalysisEnhanced> findByUserIdAndBrandOrderByAnalyzedAtDesc(UUID userId, String brand);
    
    /**
     * Find analyses by user ID and product type
     */
    List<ProductAnalysisEnhanced> findByUserIdAndProductTypeOrderByAnalyzedAtDesc(UUID userId, String productType);
    
    /**
     * Get average safety score by user ID
     */
    @Query("SELECT AVG(p.overallSafetyScore) FROM ProductAnalysisEnhanced p WHERE p.userId = :userId")
    Double getAverageSafetyScoreByUserId(@Param("userId") UUID userId);
    
    /**
     * Get average eco score by user ID
     */
    @Query("SELECT AVG(p.overallEcoScore) FROM ProductAnalysisEnhanced p WHERE p.userId = :userId")
    Double getAverageEcoScoreByUserId(@Param("userId") UUID userId);
    
    /**
     * Get average processing time by user ID
     */
    @Query("SELECT AVG(p.processingTimeMs) FROM ProductAnalysisEnhanced p WHERE p.userId = :userId")
    Double getAverageProcessingTimeByUserId(@Param("userId") UUID userId);
    
    /**
     * Get analysis statistics by user ID
     */
    @Query("SELECT " +
           "COUNT(p) as totalAnalyses, " +
           "AVG(p.overallSafetyScore) as avgSafetyScore, " +
           "AVG(p.overallEcoScore) as avgEcoScore, " +
           "AVG(p.processingTimeMs) as avgProcessingTime, " +
           "SUM(CASE WHEN p.riskLevel = 'low' THEN 1 ELSE 0 END) as lowRiskCount, " +
           "SUM(CASE WHEN p.riskLevel = 'moderate' THEN 1 ELSE 0 END) as moderateRiskCount, " +
           "SUM(CASE WHEN p.riskLevel = 'high' THEN 1 ELSE 0 END) as highRiskCount, " +
           "SUM(CASE WHEN p.riskLevel = 'very_high' THEN 1 ELSE 0 END) as veryHighRiskCount " +
           "FROM ProductAnalysisEnhanced p WHERE p.userId = :userId")
    Object[] getAnalysisStatisticsByUserId(@Param("userId") UUID userId);
    
    /**
     * Delete analyses older than specified date
     */
    void deleteByAnalyzedAtBefore(OffsetDateTime date);
    
    /**
     * Delete analyses by user ID
     */
    void deleteByUserId(UUID userId);
}