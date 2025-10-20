package com.mommyshops.recommendation.repository;

import com.mommyshops.recommendation.domain.RecommendationFeedback;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface RecommendationFeedbackRepository extends JpaRepository<RecommendationFeedback, UUID> {
    List<RecommendationFeedback> findByUserIdOrderByCreatedAtDesc(UUID userId);
    List<RecommendationFeedback> findByRecommendationType(String recommendationType);
}