package com.mommyshops.integration.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.HttpEntity;
import org.springframework.http.ResponseEntity;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.Map;
import java.util.HashMap;
import java.util.List;

/**
 * Enhanced external API service with real integrations
 * Based on the Python ewg_scraper.py, inci_beauty_api.py, cosing_api_store.py functionality
 */
@Service
public class EnhancedExternalApiService {
    
    private final RestTemplate restTemplate;
    private final String fdaApiKey;
    private final String ewgApiKey;
    private final String pubchemBaseUrl;
    private final String whoBaseUrl;
    private final String inciBeautyApiKey;
    private final String cosingApiKey;
    
    public EnhancedExternalApiService(RestTemplate restTemplate,
                                    @Value("${external.api.fda.key:}") String fdaApiKey,
                                    @Value("${external.api.ewg.key:}") String ewgApiKey,
                                    @Value("${external.api.pubchem.base-url:https://pubchem.ncbi.nlm.nih.gov/rest/pug}") String pubchemBaseUrl,
                                    @Value("${external.api.who.base-url:https://ghoapi.azureedge.net/api}") String whoBaseUrl,
                                    @Value("${external.api.inci-beauty.key:}") String inciBeautyApiKey,
                                    @Value("${external.api.cosing.key:}") String cosingApiKey) {
        this.restTemplate = restTemplate;
        this.fdaApiKey = fdaApiKey;
        this.ewgApiKey = ewgApiKey;
        this.pubchemBaseUrl = pubchemBaseUrl;
        this.whoBaseUrl = whoBaseUrl;
        this.inciBeautyApiKey = inciBeautyApiKey;
        this.cosingApiKey = cosingApiKey;
    }
    
    /**
     * Enhanced FDA adverse events data
     */
    public Map<String, Object> getFdaAdverseEvents(String ingredient) {
        if (fdaApiKey == null || fdaApiKey.isEmpty()) {
            return createErrorResponse("FDA API key not configured");
        }
        
        try {
            String url = String.format(
                "https://api.fda.gov/drug/event.json?api_key=%s&search=patient.drug.medicinalproduct:%s&limit=10",
                fdaApiKey, ingredient.replace(" ", "%20")
            );
            
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            Map<String, Object> responseBody = response.getBody();
            
            if (responseBody != null && responseBody.containsKey("results")) {
                return processFdaResponse(responseBody, ingredient);
            } else {
                return createErrorResponse("No FDA data found for ingredient: " + ingredient);
            }
            
        } catch (Exception e) {
            return createErrorResponse("FDA API error: " + e.getMessage());
        }
    }
    
    /**
     * Enhanced PubChem data
     */
    public Map<String, Object> getPubChemData(String ingredient) {
        try {
            // First, search for the compound
            String searchUrl = String.format("%s/compound/name/%s/property/MolecularFormula,MolecularWeight,CanonicalSMILES,IsomericSMILES,Description/json",
                pubchemBaseUrl, ingredient.replace(" ", "%20"));
            
            ResponseEntity<Map> response = restTemplate.getForEntity(searchUrl, Map.class);
            Map<String, Object> responseBody = response.getBody();
            
            if (responseBody != null) {
                return processPubChemResponse(responseBody, ingredient);
            } else {
                return createErrorResponse("No PubChem data found for ingredient: " + ingredient);
            }
            
        } catch (Exception e) {
            return createErrorResponse("PubChem API error: " + e.getMessage());
        }
    }
    
    /**
     * Enhanced EWG Skin Deep data
     */
    public Map<String, Object> getEwgSkinDeepData(String ingredient) {
        if (ewgApiKey == null || ewgApiKey.isEmpty()) {
            return createErrorResponse("EWG API key not configured");
        }
        
        try {
            String url = String.format(
                "https://api.ewg.org/v1/ingredients?api_key=%s&search=%s&limit=5",
                ewgApiKey, ingredient.replace(" ", "%20")
            );
            
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<String> request = new HttpEntity<>(headers);
            
            ResponseEntity<Map> response = restTemplate.postForEntity(url, request, Map.class);
            Map<String, Object> responseBody = response.getBody();
            
            if (responseBody != null) {
                return processEwgResponse(responseBody, ingredient);
            } else {
                return createErrorResponse("No EWG data found for ingredient: " + ingredient);
            }
            
        } catch (Exception e) {
            return createErrorResponse("EWG API error: " + e.getMessage());
        }
    }
    
    /**
     * Enhanced WHO health data
     */
    public Map<String, Object> getWhoHealthData(String ingredient) {
        try {
            String url = String.format(
                "%s/COUNTRY?$filter=contains(IndicatorName,'%s')&$top=10",
                whoBaseUrl, ingredient.replace(" ", "%20")
            );
            
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            Map<String, Object> responseBody = response.getBody();
            
            if (responseBody != null) {
                return processWhoResponse(responseBody, ingredient);
            } else {
                return createErrorResponse("No WHO data found for ingredient: " + ingredient);
            }
            
        } catch (Exception e) {
            return createErrorResponse("WHO API error: " + e.getMessage());
        }
    }
    
    /**
     * INCI Beauty API integration
     */
    public Map<String, Object> getInciBeautyData(String ingredient) {
        if (inciBeautyApiKey == null || inciBeautyApiKey.isEmpty()) {
            return createErrorResponse("INCI Beauty API key not configured");
        }
        
        try {
            String url = String.format(
                "https://api.incibeauty.com/v1/ingredients/%s?api_key=%s",
                ingredient.replace(" ", "%20"), inciBeautyApiKey
            );
            
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            Map<String, Object> responseBody = response.getBody();
            
            if (responseBody != null) {
                return processInciBeautyResponse(responseBody, ingredient);
            } else {
                return createErrorResponse("No INCI Beauty data found for ingredient: " + ingredient);
            }
            
        } catch (Exception e) {
            return createErrorResponse("INCI Beauty API error: " + e.getMessage());
        }
    }
    
    /**
     * COSING API integration
     */
    public Map<String, Object> getCosingData(String ingredient) {
        if (cosingApiKey == null || cosingApiKey.isEmpty()) {
            return createErrorResponse("COSING API key not configured");
        }
        
        try {
            String url = String.format(
                "https://api.cosing.eu/ingredients?search=%s&api_key=%s",
                ingredient.replace(" ", "%20"), cosingApiKey
            );
            
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            Map<String, Object> responseBody = response.getBody();
            
            if (responseBody != null) {
                return processCosingResponse(responseBody, ingredient);
            } else {
                return createErrorResponse("No COSING data found for ingredient: " + ingredient);
            }
            
        } catch (Exception e) {
            return createErrorResponse("COSING API error: " + e.getMessage());
        }
    }
    
    /**
     * Get comprehensive ingredient data from all sources
     */
    public Map<String, Object> getComprehensiveIngredientData(String ingredient) {
        Map<String, Object> comprehensiveData = new HashMap<>();
        
        // FDA data
        comprehensiveData.put("fda", getFdaAdverseEvents(ingredient));
        
        // PubChem data
        comprehensiveData.put("pubchem", getPubChemData(ingredient));
        
        // EWG data
        comprehensiveData.put("ewg", getEwgSkinDeepData(ingredient));
        
        // WHO data
        comprehensiveData.put("who", getWhoHealthData(ingredient));
        
        // INCI Beauty data
        comprehensiveData.put("inci_beauty", getInciBeautyData(ingredient));
        
        // COSING data
        comprehensiveData.put("cosing", getCosingData(ingredient));
        
        // Calculate overall safety score
        comprehensiveData.put("overall_safety_score", calculateOverallSafetyScore(comprehensiveData));
        
        return comprehensiveData;
    }
    
    // Private helper methods
    
    private Map<String, Object> processFdaResponse(Map<String, Object> response, String ingredient) {
        Map<String, Object> processed = new HashMap<>();
        processed.put("ingredient", ingredient);
        processed.put("source", "FDA");
        processed.put("data", response.get("results"));
        processed.put("total_results", ((List<?>) response.get("results")).size());
        processed.put("status", "success");
        return processed;
    }
    
    private Map<String, Object> processPubChemResponse(Map<String, Object> response, String ingredient) {
        Map<String, Object> processed = new HashMap<>();
        processed.put("ingredient", ingredient);
        processed.put("source", "PubChem");
        processed.put("data", response);
        processed.put("status", "success");
        return processed;
    }
    
    private Map<String, Object> processEwgResponse(Map<String, Object> response, String ingredient) {
        Map<String, Object> processed = new HashMap<>();
        processed.put("ingredient", ingredient);
        processed.put("source", "EWG Skin Deep");
        processed.put("data", response);
        processed.put("status", "success");
        return processed;
    }
    
    private Map<String, Object> processWhoResponse(Map<String, Object> response, String ingredient) {
        Map<String, Object> processed = new HashMap<>();
        processed.put("ingredient", ingredient);
        processed.put("source", "WHO");
        processed.put("data", response);
        processed.put("status", "success");
        return processed;
    }
    
    private Map<String, Object> processInciBeautyResponse(Map<String, Object> response, String ingredient) {
        Map<String, Object> processed = new HashMap<>();
        processed.put("ingredient", ingredient);
        processed.put("source", "INCI Beauty");
        processed.put("data", response);
        processed.put("status", "success");
        return processed;
    }
    
    private Map<String, Object> processCosingResponse(Map<String, Object> response, String ingredient) {
        Map<String, Object> processed = new HashMap<>();
        processed.put("ingredient", ingredient);
        processed.put("source", "COSING");
        processed.put("data", response);
        processed.put("status", "success");
        return processed;
    }
    
    private Map<String, Object> createErrorResponse(String errorMessage) {
        Map<String, Object> error = new HashMap<>();
        error.put("error", errorMessage);
        error.put("status", "error");
        return error;
    }
    
    private int calculateOverallSafetyScore(Map<String, Object> comprehensiveData) {
        int score = 50; // Base score
        
        // Adjust based on FDA data
        Map<String, Object> fdaData = (Map<String, Object>) comprehensiveData.get("fda");
        if (fdaData != null && fdaData.containsKey("total_results")) {
            int fdaResults = (Integer) fdaData.get("total_results");
            if (fdaResults > 0) {
                score -= Math.min(30, fdaResults * 2); // Reduce score for adverse events
            }
        }
        
        // Adjust based on EWG data
        Map<String, Object> ewgData = (Map<String, Object>) comprehensiveData.get("ewg");
        if (ewgData != null && ewgData.containsKey("data")) {
            // This would need to be adjusted based on actual EWG response structure
            score -= 10; // Placeholder adjustment
        }
        
        return Math.max(0, Math.min(100, score));
    }
}