package com.mommyshops.analysis.domain;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * Response from Python backend for product analysis
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProductAnalysisResponse {
    
    private boolean success;
    private String error;
    private String productName;
    private List<IngredientAnalysis> ingredientsDetails;
    private Double avgEcoScore;
    private String suitability;
    private String recommendations;
    private String analysisId;
    private Long processingTimeMs;
}

