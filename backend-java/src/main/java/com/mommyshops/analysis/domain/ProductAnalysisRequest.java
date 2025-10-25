package com.mommyshops.analysis.domain;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Request object for product analysis
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProductAnalysisRequest {
    
    private String productName;
    private String imageBase64;
    private String userId;
    private String analysisType;
    private Boolean includeSubstitutions;
    private Boolean includeDetailedAnalysis;
}
