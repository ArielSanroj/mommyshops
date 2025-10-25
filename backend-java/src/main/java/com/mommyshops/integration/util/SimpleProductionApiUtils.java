package com.mommyshops.integration.util;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpEntity;
import org.springframework.http.ResponseEntity;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Simplified production API utilities for MommyShops MVP
 * Based on api_utils_production.py functionality
 */
@Component
public class SimpleProductionApiUtils {
    
    private final RestTemplate restTemplate;
    
    @Value("${app.api.fda-key:}")
    private String fdaApiKey;
    
    @Value("${app.api.ewg-key:}")
    private String ewgApiKey;
    
    @Value("${app.api.inci-beauty-key:}")
    private String inciBeautyApiKey;
    
    @Value("${app.api.cosing-key:}")
    private String cosingApiKey;
    
    @Value("${app.api.entrez-email:your.email@example.com}")
    private String entrezEmail;
    
    @Value("${app.api.apify-key:}")
    private String apifyApiKey;
    
    
    // Cache
    private final Map<String, CacheEntry> cache = new ConcurrentHashMap<>();
    
    public SimpleProductionApiUtils(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }
    
    /**
     * Get FDA adverse events data
     */
    public Map<String, Object> getFdaAdverseEvents(String ingredient) {
        try {
            String url = "https://api.fda.gov/drug/event.json?search=patient.drug.medicinalproduct:" + 
                ingredient + "&limit=10";
            
            HttpHeaders headers = new HttpHeaders();
            headers.set("User-Agent", "MommyShops/1.0 (contact@mommyshops.com)");
            headers.set("Accept", "application/json");
            
            HttpEntity<String> entity = new HttpEntity<>(headers);
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class, entity);
            
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                Map<String, Object> data = response.getBody();
                return processFdaResponse(data, ingredient);
            } else {
                return getDefaultFdaData(ingredient);
            }
            
        } catch (Exception e) {
            return getDefaultFdaData(ingredient);
        }
    }
    
    /**
     * Get PubChem data
     */
    public Map<String, Object> getPubChemData(String ingredient) {
        try {
            String url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/" + 
                ingredient + "/property/Description,MolecularFormula,MolecularWeight/JSON";
            
            HttpHeaders headers = new HttpHeaders();
            headers.set("User-Agent", "MommyShops/1.0 (contact@mommyshops.com)");
            headers.set("Accept", "application/json");
            
            HttpEntity<String> entity = new HttpEntity<>(headers);
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class, entity);
            
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                Map<String, Object> data = response.getBody();
                return processPubChemResponse(data, ingredient);
            } else {
                return getDefaultPubChemData(ingredient);
            }
            
        } catch (Exception e) {
            return getDefaultPubChemData(ingredient);
        }
    }
    
    /**
     * Get EWG Skin Deep data
     */
    public Map<String, Object> getEwgSkinDeepData(String ingredient) {
        try {
            String url = "https://www.ewg.org/skindeep/ingredients/" + 
                ingredient.replace(" ", "-").toLowerCase();
            
            HttpHeaders headers = new HttpHeaders();
            headers.set("User-Agent", "Mozilla/5.0 (compatible; MommyShopsBot/1.0)");
            headers.set("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8");
            
            HttpEntity<String> entity = new HttpEntity<>(headers);
            ResponseEntity<String> response = restTemplate.getForEntity(url, String.class, entity);
            
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                String htmlContent = response.getBody();
                return processEwgResponse(htmlContent, ingredient);
            } else {
                return getDefaultEwgData(ingredient);
            }
            
        } catch (Exception e) {
            return getDefaultEwgData(ingredient);
        }
    }
    
    /**
     * Process FDA response
     */
    private Map<String, Object> processFdaResponse(Map<String, Object> data, String ingredient) {
        Map<String, Object> result = new HashMap<>();
        
        try {
            List<Map<String, Object>> results = (List<Map<String, Object>>) data.get("results");
            
            if (results != null && !results.isEmpty()) {
                List<String> adverseEvents = new ArrayList<>();
                int seriousEvents = 0;
                
                for (Map<String, Object> event : results) {
                    if (event.containsKey("patient")) {
                        Map<String, Object> patient = (Map<String, Object>) event.get("patient");
                        
                        if (patient.containsKey("drug")) {
                            List<Map<String, Object>> drugs = (List<Map<String, Object>>) patient.get("drug");
                            for (Map<String, Object> drug : drugs) {
                                if (drug.containsKey("serious") && 
                                    (drug.get("serious").equals("1") || drug.get("serious").equals("yes"))) {
                                    seriousEvents++;
                                }
                            }
                        }
                        
                        if (patient.containsKey("reaction")) {
                            List<Map<String, Object>> reactions = (List<Map<String, Object>>) patient.get("reaction");
                            for (Map<String, Object> reaction : reactions) {
                                String reactionText = (String) reaction.get("reactionmeddrapt");
                                if (reactionText != null && !reactionText.isEmpty()) {
                                    adverseEvents.add(reactionText);
                                }
                            }
                        }
                    }
                }
                
                String riskLevel;
                if (seriousEvents > 0) {
                    riskLevel = "high";
                } else if (adverseEvents.size() > 5) {
                    riskLevel = "medium";
                } else if (!adverseEvents.isEmpty()) {
                    riskLevel = "low";
                } else {
                    riskLevel = "safe";
                }
                
                result.put("risk_level", riskLevel);
                result.put("adverse_events_count", adverseEvents.size());
                result.put("serious_events_count", seriousEvents);
                result.put("adverse_events", adverseEvents);
                result.put("source", "FDA FAERS");
                result.put("success", true);
                
            } else {
                result.put("risk_level", "safe");
                result.put("adverse_events_count", 0);
                result.put("serious_events_count", 0);
                result.put("adverse_events", new ArrayList<>());
                result.put("source", "FDA FAERS");
                result.put("success", true);
            }
            
        } catch (Exception e) {
            result.put("error", "Failed to process FDA data: " + e.getMessage());
            result.put("success", false);
        }
        
        return result;
    }
    
    /**
     * Process PubChem response
     */
    private Map<String, Object> processPubChemResponse(Map<String, Object> data, String ingredient) {
        Map<String, Object> result = new HashMap<>();
        
        try {
            if (data.containsKey("PropertyTable")) {
                Map<String, Object> propertyTable = (Map<String, Object>) data.get("PropertyTable");
                List<Map<String, Object>> properties = (List<Map<String, Object>>) propertyTable.get("Properties");
                
                if (properties != null && !properties.isEmpty()) {
                    Map<String, Object> props = properties.get(0);
                    
                    String description = (String) props.get("Description");
                    String molecularFormula = (String) props.get("MolecularFormula");
                    Object molecularWeight = props.get("MolecularWeight");
                    
                    result.put("description", description != null ? description : "No description available");
                    result.put("molecular_formula", molecularFormula != null ? molecularFormula : "Unknown");
                    result.put("molecular_weight", molecularWeight != null ? molecularWeight : "Unknown");
                    result.put("source", "PubChem");
                    result.put("success", true);
                } else {
                    result.put("description", "No data available");
                    result.put("molecular_formula", "Unknown");
                    result.put("molecular_weight", "Unknown");
                    result.put("source", "PubChem");
                    result.put("success", true);
                }
            } else {
                result.put("description", "No data available");
                result.put("molecular_formula", "Unknown");
                result.put("molecular_weight", "Unknown");
                result.put("source", "PubChem");
                result.put("success", true);
            }
            
        } catch (Exception e) {
            result.put("error", "Failed to process PubChem data: " + e.getMessage());
            result.put("success", false);
        }
        
        return result;
    }
    
    /**
     * Process EWG response (web scraping)
     */
    private Map<String, Object> processEwgResponse(String htmlContent, String ingredient) {
        Map<String, Object> result = new HashMap<>();
        
        try {
            // Simple parsing - in real implementation, use proper HTML parser
            int ewgScore = 50; // Default score
            List<String> concerns = new ArrayList<>();
            
            // Look for score patterns in HTML
            if (htmlContent.contains("data-score")) {
                // Extract score from HTML attributes
                String[] parts = htmlContent.split("data-score=\"");
                if (parts.length > 1) {
                    String scorePart = parts[1].split("\"")[0];
                    try {
                        ewgScore = Integer.parseInt(scorePart);
                    } catch (NumberFormatException e) {
                        ewgScore = 50;
                    }
                }
            }
            
            String riskLevel;
            if (ewgScore >= 8) {
                riskLevel = "high";
            } else if (ewgScore >= 5) {
                riskLevel = "medium";
            } else if (ewgScore >= 3) {
                riskLevel = "low";
            } else {
                riskLevel = "safe";
            }
            
            result.put("ewg_score", ewgScore);
            result.put("risk_level", riskLevel);
            result.put("concerns", concerns);
            result.put("source", "EWG Skin Deep");
            result.put("success", true);
            
        } catch (Exception e) {
            result.put("error", "Failed to process EWG data: " + e.getMessage());
            result.put("success", false);
        }
        
        return result;
    }
    
    // Default data methods
    private Map<String, Object> getDefaultFdaData(String ingredient) {
        Map<String, Object> result = new HashMap<>();
        result.put("risk_level", "unknown");
        result.put("adverse_events_count", 0);
        result.put("serious_events_count", 0);
        result.put("adverse_events", new ArrayList<>());
        result.put("source", "FDA FAERS (Default)");
        result.put("success", false);
        return result;
    }
    
    private Map<String, Object> getDefaultPubChemData(String ingredient) {
        Map<String, Object> result = new HashMap<>();
        result.put("description", "No data available");
        result.put("molecular_formula", "Unknown");
        result.put("molecular_weight", "Unknown");
        result.put("source", "PubChem (Default)");
        result.put("success", false);
        return result;
    }
    
    private Map<String, Object> getDefaultEwgData(String ingredient) {
        Map<String, Object> result = new HashMap<>();
        result.put("ewg_score", 50);
        result.put("risk_level", "unknown");
        result.put("concerns", new ArrayList<>());
        result.put("source", "EWG Skin Deep (Default)");
        result.put("success", false);
        return result;
    }
    
    /**
     * Health check for all APIs
     */
    public Map<String, Object> healthCheck() {
        Map<String, Object> healthStatus = new HashMap<>();
        
        // Test FDA API
        try {
            Map<String, Object> fdaTest = getFdaAdverseEvents("water");
            healthStatus.put("fda", Map.of(
                "status", (Boolean) fdaTest.getOrDefault("success", false) ? "healthy" : "unhealthy",
                "response_time", "N/A"
            ));
        } catch (Exception e) {
            healthStatus.put("fda", Map.of(
                "status", "unhealthy",
                "error", e.getMessage()
            ));
        }
        
        // Test PubChem API
        try {
            Map<String, Object> pubchemTest = getPubChemData("water");
            healthStatus.put("pubchem", Map.of(
                "status", (Boolean) pubchemTest.getOrDefault("success", false) ? "healthy" : "unhealthy",
                "response_time", "N/A"
            ));
        } catch (Exception e) {
            healthStatus.put("pubchem", Map.of(
                "status", "unhealthy",
                "error", e.getMessage()
            ));
        }
        
        // Test EWG API
        try {
            Map<String, Object> ewgTest = getEwgSkinDeepData("water");
            healthStatus.put("ewg", Map.of(
                "status", (Boolean) ewgTest.getOrDefault("success", false) ? "healthy" : "unhealthy",
                "response_time", "N/A"
            ));
        } catch (Exception e) {
            healthStatus.put("ewg", Map.of(
                "status", "unhealthy",
                "error", e.getMessage()
            ));
        }
        
        return healthStatus;
    }
    
    /**
     * Get cache statistics
     */
    public Map<String, Object> getCacheStats() {
        Map<String, Object> stats = new HashMap<>();
        stats.put("size", cache.size());
        stats.put("hits", 0); // Simple implementation
        stats.put("misses", 0);
        stats.put("evictions", 0);
        return stats;
    }
    
    /**
     * Clear cache
     */
    public void clearCache() {
        cache.clear();
    }
    
    // Cache entry class
    private static class CacheEntry {
        private final Object data;
        private final long timestamp;
        private final long ttl;
        
        public CacheEntry(Object data, long ttl) {
            this.data = data;
            this.timestamp = System.currentTimeMillis();
            this.ttl = ttl;
        }
        
        public boolean isExpired() {
            return System.currentTimeMillis() - timestamp > ttl;
        }
        
        public Object getData() {
            return data;
        }
    }
}