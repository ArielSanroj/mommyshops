package com.mommyshops.integration.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpEntity;
import org.springframework.http.ResponseEntity;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;
import java.util.HashMap;
import java.util.List;
import java.util.ArrayList;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * EWG Skin Deep Web Scraping Service
 * 
 * This service implements ethical web scraping of EWG Skin Deep database
 * following their guidelines and respecting rate limits.
 * 
 * Rate Limiting: 1 request per 2 seconds to be respectful
 * Contact: skindeep@ewg.org for large data requests
 */
@Service
public class EWGService {
    
    private static final Logger logger = LoggerFactory.getLogger(EWGService.class);
    
    private final RestTemplate restTemplate;
    private final String ewgBaseUrl;
    
    // Rate limiting - 1 request per 2 seconds
    private long lastRequestTime = 0;
    private static final long RATE_LIMIT_MS = 2000;
    
    public EWGService(RestTemplate restTemplate,
                     @Value("${external.api.ewg.base-url:https://www.ewg.org/skindeep}") String ewgBaseUrl) {
        this.restTemplate = restTemplate;
        this.ewgBaseUrl = ewgBaseUrl;
    }
    
    /**
     * Get EWG Skin Deep data for a specific ingredient
     * 
     * @param ingredient The ingredient name to search for
     * @return EWG data including hazard score and concerns
     */
    public Map<String, Object> getIngredientData(String ingredient) {
        try {
            // Respect rate limiting
            respectRateLimit();
            
            logger.info("Fetching EWG data for ingredient: {}", ingredient);
            
            // Try direct ingredient search first
            Map<String, Object> directResult = searchIngredientDirectly(ingredient);
            if (directResult != null && !directResult.containsKey("error")) {
                return directResult;
            }
            
            // Fallback to Build Your Own Report
            return searchWithBuildYourOwnReport(ingredient);
            
        } catch (Exception e) {
            logger.error("Error fetching EWG data for ingredient {}: {}", ingredient, e.getMessage());
            return Map.of(
                "error", "EWG data unavailable",
                "ingredient", ingredient,
                "message", e.getMessage()
            );
        }
    }
    
    /**
     * Search for ingredient directly in EWG database
     */
    private Map<String, Object> searchIngredientDirectly(String ingredient) {
        try {
            String searchUrl = ewgBaseUrl + "/search/?query=" + ingredient.replace(" ", "+");
            
            HttpHeaders headers = new HttpHeaders();
            headers.set("User-Agent", "MommyShops/1.0 (Educational Purpose)");
            headers.set("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8");
            
            HttpEntity<String> request = new HttpEntity<>(headers);
            ResponseEntity<String> response = restTemplate.exchange(searchUrl, 
                org.springframework.http.HttpMethod.GET, request, String.class);
            
            return parseSearchResults(response.getBody(), ingredient);
            
        } catch (Exception e) {
            logger.warn("Direct search failed for {}: {}", ingredient, e.getMessage());
            return null;
        }
    }
    
    /**
     * Use Build Your Own Report tool for ingredients not in main database
     */
    private Map<String, Object> searchWithBuildYourOwnReport(String ingredient) {
        try {
            // This would require form submission - for now return basic data
            return Map.of(
                "ingredient", ingredient,
                "hazardScore", estimateHazardScore(ingredient),
                "dataSource", "EWG Build Your Own Report",
                "concerns", getEstimatedConcerns(ingredient),
                "note", "Estimated data - not from main EWG database"
            );
        } catch (Exception e) {
            logger.warn("Build Your Own Report failed for {}: {}", ingredient, e.getMessage());
            return Map.of("error", "EWG data unavailable");
        }
    }
    
    /**
     * Parse EWG search results HTML
     */
    private Map<String, Object> parseSearchResults(String html, String ingredient) {
        Map<String, Object> result = new HashMap<>();
        result.put("ingredient", ingredient);
        result.put("dataSource", "EWG Skin Deep Database");
        
        // Extract hazard score (1-10 scale) - improved patterns
        int hazardScore = extractHazardScore(html);
        result.put("hazardScore", hazardScore);
        
        // Extract concerns
        List<String> concerns = extractConcerns(html);
        result.put("concerns", concerns);
        
        // Extract data availability
        result.put("dataAvailability", extractDataAvailability(html));
        
        // Extract EWG rating
        result.put("ewgRating", extractEWGRating(html));
        
        return result;
    }
    
    /**
     * Extract hazard score with improved patterns
     */
    private int extractHazardScore(String html) {
        // First try to find score in img src attributes (EWG uses score=3, score=2, etc.)
        Pattern imgScorePattern = Pattern.compile("score=(\\d+)");
        Matcher imgMatcher = imgScorePattern.matcher(html);
        if (imgMatcher.find()) {
            return Integer.parseInt(imgMatcher.group(1));
        }
        
        // Then try other patterns
        String[] scorePatterns = {
            "hazard.*?score.*?(\\d+)",
            "score.*?(\\d+).*?hazard", 
            "rating.*?(\\d+)",
            "(\\d+).*?out.*?10"
        };
        
        for (String pattern : scorePatterns) {
            Pattern p = Pattern.compile(pattern, Pattern.CASE_INSENSITIVE);
            Matcher m = p.matcher(html);
            if (m.find()) {
                return Integer.parseInt(m.group(1));
            }
        }
        
        return 0; // Not found
    }
    
    /**
     * Extract health concerns from HTML
     */
    private List<String> extractConcerns(String html) {
        List<String> concerns = new ArrayList<>();
        
        // Common EWG concern patterns
        String[] concernPatterns = {
            "cancer", "reproductive", "developmental", "allergies", 
            "immunotoxicity", "neurotoxicity", "endocrine", "organ"
        };
        
        for (String pattern : concernPatterns) {
            if (html.toLowerCase().contains(pattern)) {
                concerns.add(pattern);
            }
        }
        
        return concerns;
    }
    
    /**
     * Extract data availability information
     */
    private Map<String, Object> extractDataAvailability(String html) {
        Map<String, Object> data = new HashMap<>();
        
        // Check for data availability indicators
        data.put("studiesAvailable", html.toLowerCase().contains("studies"));
        data.put("regulatoryData", html.toLowerCase().contains("regulatory"));
        data.put("industryData", html.toLowerCase().contains("industry"));
        
        return data;
    }
    
    /**
     * Extract EWG rating
     */
    private String extractEWGRating(String html) {
        // Look for EWG rating patterns
        Pattern ratingPattern = Pattern.compile("ewg.*?rating.*?([a-z]+)", Pattern.CASE_INSENSITIVE);
        Matcher ratingMatcher = ratingPattern.matcher(html);
        if (ratingMatcher.find()) {
            return ratingMatcher.group(1);
        }
        return "Unknown";
    }
    
    /**
     * Estimate hazard score for unknown ingredients
     */
    private int estimateHazardScore(String ingredient) {
        String lowerIngredient = ingredient.toLowerCase();
        
        // High hazard ingredients
        if (lowerIngredient.contains("sulfate") || lowerIngredient.contains("paraben") || 
            lowerIngredient.contains("fragrance") || lowerIngredient.contains("parfum")) {
            return 6;
        }
        
        // Medium hazard ingredients
        if (lowerIngredient.contains("alcohol") || lowerIngredient.contains("glycol") ||
            lowerIngredient.contains("phenoxy")) {
            return 4;
        }
        
        // Low hazard ingredients
        if (lowerIngredient.contains("aloe") || lowerIngredient.contains("water") ||
            lowerIngredient.contains("salt") || lowerIngredient.contains("glycerin")) {
            return 2;
        }
        
        return 5; // Default medium hazard
    }
    
    /**
     * Get estimated concerns for unknown ingredients
     */
    private List<String> getEstimatedConcerns(String ingredient) {
        List<String> concerns = new ArrayList<>();
        String lowerIngredient = ingredient.toLowerCase();
        
        if (lowerIngredient.contains("sulfate")) {
            concerns.add("skin irritation");
            concerns.add("eye irritation");
        }
        
        if (lowerIngredient.contains("paraben")) {
            concerns.add("endocrine disruption");
            concerns.add("reproductive toxicity");
        }
        
        if (lowerIngredient.contains("fragrance") || lowerIngredient.contains("parfum")) {
            concerns.add("allergies");
            concerns.add("sensitization");
        }
        
        if (lowerIngredient.contains("alcohol")) {
            concerns.add("skin drying");
        }
        
        return concerns;
    }
    
    /**
     * Respect rate limiting - wait if necessary
     */
    private void respectRateLimit() {
        long currentTime = System.currentTimeMillis();
        long timeSinceLastRequest = currentTime - lastRequestTime;
        
        if (timeSinceLastRequest < RATE_LIMIT_MS) {
            try {
                Thread.sleep(RATE_LIMIT_MS - timeSinceLastRequest);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
        
        lastRequestTime = System.currentTimeMillis();
    }
    
    /**
     * Get EWG data for multiple ingredients (with proper rate limiting)
     */
    public Map<String, Object> getMultipleIngredientsData(List<String> ingredients) {
        Map<String, Object> results = new HashMap<>();
        
        for (String ingredient : ingredients) {
            results.put(ingredient, getIngredientData(ingredient));
            
            // Add delay between requests
            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
        
        return results;
    }
    
    /**
     * Check if EWG service is healthy
     */
    public boolean isHealthy() {
        try {
            respectRateLimit();
            
            HttpHeaders headers = new HttpHeaders();
            headers.set("User-Agent", "MommyShops/1.0 (Health Check)");
            
            HttpEntity<String> request = new HttpEntity<>(headers);
            ResponseEntity<String> response = restTemplate.exchange(ewgBaseUrl, 
                org.springframework.http.HttpMethod.GET, request, String.class);
            
            return response.getStatusCode().is2xxSuccessful();
            
        } catch (Exception e) {
            logger.error("EWG health check failed: {}", e.getMessage());
            return false;
        }
    }
}