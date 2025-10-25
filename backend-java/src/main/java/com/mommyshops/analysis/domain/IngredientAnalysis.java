package com.mommyshops.analysis.domain;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;

/**
 * Ingredient analysis data from Python backend
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class IngredientAnalysis {
    
    private String name;
    private String riskLevel;
    private Double ecoScore;
    private String benefits;
    private String risksDetailed;
    private String sources;
    private String function;
    private String origin;
    private List<String> concerns;
    private Boolean isNatural;
    private String casNumber;
    private String inciName;
}

