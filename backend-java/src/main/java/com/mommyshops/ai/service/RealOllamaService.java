package com.mommyshops.ai.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.HttpEntity;
import org.springframework.http.ResponseEntity;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.regex.Pattern;
import java.util.regex.Matcher;

/**
 * Real Ollama service integration with live AI models
 * Replaces placeholder responses with actual AI analysis
 */
@Service
public class RealOllamaService {
    
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    
    @Value("${app.ollama.base-url:http://localhost:11434}")
    private String ollamaBaseUrl;
    
    @Value("${app.ollama.model:llama3.1}")
    private String textModel;
    
    @Value("${app.ollama.vision-model:llava}")
    private String visionModel;
    
    @Value("${app.ollama.timeout:30000}")
    private int timeout;
    
    public RealOllamaService(RestTemplate restTemplate, ObjectMapper objectMapper) {
        this.restTemplate = restTemplate;
        this.objectMapper = objectMapper;
    }
    
    /**
     * Analyze ingredient with AI
     */
    public IngredientAnalysis analyzeIngredient(String ingredient, com.mommyshops.profile.domain.UserProfile profile) {
        try {
            // Create analysis prompt
            String prompt = createIngredientAnalysisPrompt(ingredient, profile);
            
            // Call Ollama API
            Map<String, Object> response = callOllamaApi(prompt, textModel).get();
            
            if (response != null && response.containsKey("response")) {
                String aiResponse = (String) response.get("response");
                return parseIngredientAnalysis(aiResponse, ingredient);
            } else {
                return getDefaultIngredientAnalysis(ingredient);
            }
            
        } catch (Exception e) {
            return getDefaultIngredientAnalysis(ingredient);
        }
    }
    
    /**
     * Generate substitute recommendations
     */
    public List<SubstituteRecommendation> generateSubstitutes(String ingredient, IngredientAnalysis analysis, com.mommyshops.profile.domain.UserProfile profile) {
        try {
            // Create substitute generation prompt
            String prompt = createSubstitutePrompt(ingredient, analysis, profile);
            
            // Call Ollama API
            Map<String, Object> response = callOllamaApi(prompt, textModel).get();
            
            if (response != null && response.containsKey("response")) {
                String aiResponse = (String) response.get("response");
                return parseSubstituteRecommendations(aiResponse, ingredient);
            } else {
                return getDefaultSubstitutes(ingredient);
            }
            
        } catch (Exception e) {
            return getDefaultSubstitutes(ingredient);
        }
    }
    
    /**
     * Analyze image with vision model
     */
    public CompletableFuture<Map<String, Object>> analyzeImage(byte[] imageData) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                // Convert image to base64
                String base64Image = java.util.Base64.getEncoder().encodeToString(imageData);
                
                // Create vision analysis prompt
                String prompt = createImageAnalysisPrompt();
                
                // Call Ollama vision API
                Map<String, Object> request = new HashMap<>();
                request.put("model", visionModel);
                request.put("prompt", prompt);
                request.put("images", Arrays.asList(base64Image));
                request.put("stream", false);
                
                HttpHeaders headers = new HttpHeaders();
                headers.setContentType(MediaType.APPLICATION_JSON);
                
                HttpEntity<Map<String, Object>> entity = new HttpEntity<>(request, headers);
                ResponseEntity<Map> response = restTemplate.postForEntity(
                    ollamaBaseUrl + "/api/generate", entity, Map.class);
                
                if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                    Map<String, Object> data = response.getBody();
                    String aiResponse = (String) data.get("response");
                    return parseImageAnalysis(aiResponse);
                } else {
                    return getDefaultImageAnalysis();
                }
                
            } catch (Exception e) {
                return getDefaultImageAnalysis();
            }
        });
    }
    
    /**
     * Call Ollama API
     */
    public CompletableFuture<Map<String, Object>> callOllamaApi(String prompt, String model) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                Map<String, Object> request = new HashMap<>();
                request.put("model", model);
                request.put("prompt", prompt);
                request.put("stream", false);
                request.put("options", Map.of(
                    "temperature", 0.7,
                    "top_p", 0.9,
                    "max_tokens", 1000
                ));
                
                HttpHeaders headers = new HttpHeaders();
                headers.setContentType(MediaType.APPLICATION_JSON);
                
                HttpEntity<Map<String, Object>> entity = new HttpEntity<>(request, headers);
                ResponseEntity<Map> response = restTemplate.postForEntity(
                    ollamaBaseUrl + "/api/generate", entity, Map.class);
                
                if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                    return response.getBody();
                } else {
                    return null;
                }
                
            } catch (Exception e) {
                return null;
            }
        });
    }
    
    /**
     * Create ingredient analysis prompt
     */
    private String createIngredientAnalysisPrompt(String ingredient, com.mommyshops.profile.domain.UserProfile profile) {
        StringBuilder prompt = new StringBuilder();
        prompt.append("Analyze the cosmetic ingredient '").append(ingredient).append("' for safety and eco-friendliness.\n\n");
        
        // Add user profile context
        if (profile != null) {
            prompt.append("User profile:\n");
            prompt.append("- Facial skin preferences: ").append(profile.getFacialSkinPreferences() != null ? profile.getFacialSkinPreferences() : "unknown").append("\n");
            prompt.append("- Body skin preferences: ").append(profile.getBodySkinPreferences() != null ? profile.getBodySkinPreferences() : "none").append("\n");
            prompt.append("- Hair preferences: ").append(profile.getHairPreferences() != null ? profile.getHairPreferences() : "none").append("\n");
            prompt.append("- Brand preferences: ").append(profile.getBrandPreferences() != null ? profile.getBrandPreferences() : "unknown").append("\n\n");
        }
        
        prompt.append("Please provide a detailed analysis in the following JSON format:\n");
        prompt.append("{\n");
        prompt.append("  \"safety_score\": <0-100>,\n");
        prompt.append("  \"eco_friendliness_score\": <0-100>,\n");
        prompt.append("  \"health_risks\": [\"risk1\", \"risk2\"],\n");
        prompt.append("  \"benefits\": [\"benefit1\", \"benefit2\"],\n");
        prompt.append("  \"safety_assessment\": \"detailed safety assessment\",\n");
        prompt.append("  \"eco_assessment\": \"detailed eco-friendliness assessment\",\n");
        prompt.append("  \"recommendation\": \"safe|caution|avoid\",\n");
        prompt.append("  \"confidence\": <0-100>\n");
        prompt.append("}\n\n");
        prompt.append("Focus on cosmetic safety standards (FDA, EWG, CIR, SCCS) and provide specific, actionable information.");
        
        return prompt.toString();
    }
    
    /**
     * Create substitute generation prompt
     */
    private String createSubstitutePrompt(String ingredient, IngredientAnalysis analysis, com.mommyshops.profile.domain.UserProfile profile) {
        StringBuilder prompt = new StringBuilder();
        prompt.append("Find safe alternatives to the cosmetic ingredient '").append(ingredient).append("'.\n\n");
        
        prompt.append("Current ingredient analysis:\n");
        prompt.append("- Safety score: ").append(analysis.getSafetyScore()).append("/100\n");
        prompt.append("- Eco-friendliness score: ").append(analysis.getEcoFriendlinessScore()).append("/100\n");
        prompt.append("- Health risks: ").append(String.join(", ", analysis.getHealthRisks())).append("\n");
        prompt.append("- Recommendation: ").append(analysis.getRecommendation()).append("\n\n");
        
        if (profile != null) {
            prompt.append("User profile:\n");
            prompt.append("- Facial skin preferences: ").append(profile.getFacialSkinPreferences() != null ? profile.getFacialSkinPreferences() : "unknown").append("\n");
            prompt.append("- Body skin preferences: ").append(profile.getBodySkinPreferences() != null ? profile.getBodySkinPreferences() : "none").append("\n");
            prompt.append("- Hair preferences: ").append(profile.getHairPreferences() != null ? profile.getHairPreferences() : "none").append("\n\n");
        }
        
        prompt.append("Please provide 3-5 substitute recommendations in the following JSON format:\n");
        prompt.append("{\n");
        prompt.append("  \"substitutes\": [\n");
        prompt.append("    {\n");
        prompt.append("      \"ingredient\": \"substitute name\",\n");
        prompt.append("      \"safety_score\": <0-100>,\n");
        prompt.append("      \"eco_friendliness_score\": <0-100>,\n");
        prompt.append("      \"benefits\": [\"benefit1\", \"benefit2\"],\n");
        prompt.append("      \"reasoning\": \"why this is a good substitute\",\n");
        prompt.append("      \"availability\": \"common|moderate|rare\",\n");
        prompt.append("      \"cost\": \"low|medium|high\",\n");
        prompt.append("      \"confidence\": <0-100>\n");
        prompt.append("    }\n");
        prompt.append("  ]\n");
        prompt.append("}\n\n");
        prompt.append("Focus on functionally similar ingredients that are safer and more eco-friendly.");
        
        return prompt.toString();
    }
    
    /**
     * Create image analysis prompt
     */
    private String createImageAnalysisPrompt() {
        return "Analyze this cosmetic product image and extract the following information:\n\n" +
               "1. Product name and brand\n" +
               "2. Product type (e.g., moisturizer, cleanser, serum)\n" +
               "3. Net content/volume\n" +
               "4. Complete ingredient list\n" +
               "5. Any safety warnings or claims\n" +
               "6. Product benefits mentioned\n\n" +
               "Please provide the information in a structured format, focusing on the ingredient list which is most important for safety analysis.";
    }
    
    /**
     * Parse ingredient analysis from AI response
     */
    private IngredientAnalysis parseIngredientAnalysis(String aiResponse, String ingredient) {
        try {
            // Try to extract JSON from response
            String jsonStr = extractJsonFromResponse(aiResponse);
            if (jsonStr != null) {
                Map<String, Object> data = objectMapper.readValue(jsonStr, Map.class);
                
                int safetyScore = getIntValue(data, "safety_score", 50);
                int ecoScore = getIntValue(data, "eco_friendliness_score", 50);
                List<String> healthRisks = getStringList(data, "health_risks");
                List<String> benefits = getStringList(data, "benefits");
                String safetyAssessment = getStringValue(data, "safety_assessment", "No assessment available");
                String ecoAssessment = getStringValue(data, "eco_assessment", "No assessment available");
                String recommendation = getStringValue(data, "recommendation", "caution");
                int confidence = getIntValue(data, "confidence", 70);
                
                return new IngredientAnalysis(
                    ingredient, safetyScore, ecoScore, healthRisks, benefits,
                    safetyAssessment, ecoAssessment, recommendation, confidence
                );
            }
        } catch (Exception e) {
            // Fall through to default
        }
        
        return getDefaultIngredientAnalysis(ingredient);
    }
    
    /**
     * Parse substitute recommendations from AI response
     */
    private List<SubstituteRecommendation> parseSubstituteRecommendations(String aiResponse, String ingredient) {
        try {
            // Try to extract JSON from response
            String jsonStr = extractJsonFromResponse(aiResponse);
            if (jsonStr != null) {
                Map<String, Object> data = objectMapper.readValue(jsonStr, Map.class);
                List<Map<String, Object>> substitutes = (List<Map<String, Object>>) data.get("substitutes");
                
                if (substitutes != null) {
                    List<SubstituteRecommendation> recommendations = new ArrayList<>();
                    for (Map<String, Object> sub : substitutes) {
                        SubstituteRecommendation rec = new SubstituteRecommendation();
                        rec.setIngredient(getStringValue(sub, "ingredient", "Unknown"));
                        rec.setSafetyScore(getIntValue(sub, "safety_score", 50));
                        rec.setEcoFriendlinessScore(getIntValue(sub, "eco_friendliness_score", 50));
                        rec.setBenefits(getStringList(sub, "benefits"));
                        rec.setReasoning(getStringValue(sub, "reasoning", "No reasoning provided"));
                        rec.setAvailability(getStringValue(sub, "availability", "unknown"));
                        rec.setCost(getStringValue(sub, "cost", "unknown"));
                        rec.setConfidence(getIntValue(sub, "confidence", 70));
                        recommendations.add(rec);
                    }
                    return recommendations;
                }
            }
        } catch (Exception e) {
            // Fall through to default
        }
        
        return getDefaultSubstitutes(ingredient);
    }
    
    /**
     * Parse image analysis from AI response
     */
    private Map<String, Object> parseImageAnalysis(String aiResponse) {
        Map<String, Object> result = new HashMap<>();
        
        try {
            // Extract structured information from response
            result.put("product_name", extractField(aiResponse, "Product name", "brand"));
            result.put("brand", extractField(aiResponse, "Brand", "brand"));
            result.put("product_type", extractField(aiResponse, "Product type", "type"));
            result.put("net_content", extractField(aiResponse, "Net content", "volume"));
            result.put("ingredients", extractIngredients(aiResponse));
            result.put("safety_warnings", extractField(aiResponse, "Safety warnings", "warnings"));
            result.put("benefits", extractField(aiResponse, "Benefits", "benefits"));
            result.put("success", true);
            
        } catch (Exception e) {
            result.put("error", "Failed to parse image analysis: " + e.getMessage());
            result.put("success", false);
        }
        
        return result;
    }
    
    /**
     * Extract JSON from AI response
     */
    private String extractJsonFromResponse(String response) {
        // Look for JSON block in response
        Pattern jsonPattern = Pattern.compile("\\{[\\s\\S]*\\}");
        Matcher matcher = jsonPattern.matcher(response);
        
        if (matcher.find()) {
            return matcher.group();
        }
        
        return null;
    }
    
    /**
     * Extract field from text
     */
    private String extractField(String text, String fieldName, String alternative) {
        Pattern pattern = Pattern.compile("(?i)" + fieldName + "[:\\s]+([^\\n]+)");
        Matcher matcher = pattern.matcher(text);
        
        if (matcher.find()) {
            return matcher.group(1).trim();
        }
        
        return alternative;
    }
    
    /**
     * Extract ingredients from text
     */
    private List<String> extractIngredients(String text) {
        List<String> ingredients = new ArrayList<>();
        
        // Look for ingredient list patterns
        Pattern ingredientPattern = Pattern.compile("(?i)(?:ingredients?|ingredientes?)[:\\s]+([^\\n]+(?:\\n[^\\n]+)*)");
        Matcher matcher = ingredientPattern.matcher(text);
        
        if (matcher.find()) {
            String ingredientList = matcher.group(1);
            String[] parts = ingredientList.split("[,;]");
            for (String part : parts) {
                String ingredient = part.trim();
                if (!ingredient.isEmpty() && ingredient.length() > 2) {
                    ingredients.add(ingredient);
                }
            }
        }
        
        return ingredients;
    }
    
    /**
     * Helper methods for parsing
     */
    private int getIntValue(Map<String, Object> data, String key, int defaultValue) {
        Object value = data.get(key);
        if (value instanceof Number) {
            return ((Number) value).intValue();
        } else if (value instanceof String) {
            try {
                return Integer.parseInt((String) value);
            } catch (NumberFormatException e) {
                return defaultValue;
            }
        }
        return defaultValue;
    }
    
    private String getStringValue(Map<String, Object> data, String key, String defaultValue) {
        Object value = data.get(key);
        return value != null ? value.toString() : defaultValue;
    }
    
    @SuppressWarnings("unchecked")
    private List<String> getStringList(Map<String, Object> data, String key) {
        Object value = data.get(key);
        if (value instanceof List) {
            return (List<String>) value;
        }
        return new ArrayList<>();
    }
    
    /**
     * Default responses
     */
    private IngredientAnalysis getDefaultIngredientAnalysis(String ingredient) {
        return new IngredientAnalysis(
            ingredient, 50, 50, 
            Arrays.asList("Limited data available"), 
            Arrays.asList("Unknown benefits"),
            "Limited safety data available for this ingredient",
            "Limited eco-friendliness data available",
            "caution", 50
        );
    }
    
    private List<SubstituteRecommendation> getDefaultSubstitutes(String ingredient) {
        List<SubstituteRecommendation> substitutes = new ArrayList<>();
        
        SubstituteRecommendation sub1 = new SubstituteRecommendation();
        sub1.setIngredient("Glycerin");
        sub1.setSafetyScore(85);
        sub1.setEcoFriendlinessScore(90);
        sub1.setBenefits(Arrays.asList("Humectant", "Moisturizing"));
        sub1.setReasoning("Safe, natural humectant alternative");
        sub1.setAvailability("common");
        sub1.setCost("low");
        sub1.setConfidence(70);
        substitutes.add(sub1);
        
        return substitutes;
    }
    
    private Map<String, Object> getDefaultImageAnalysis() {
        Map<String, Object> result = new HashMap<>();
        result.put("product_name", "Unknown");
        result.put("brand", "Unknown");
        result.put("product_type", "Unknown");
        result.put("net_content", "Unknown");
        result.put("ingredients", new ArrayList<>());
        result.put("safety_warnings", "None detected");
        result.put("benefits", "Unknown");
        result.put("success", false);
        return result;
    }
    
    /**
     * Data classes
     */
    public static class IngredientAnalysis {
        private final String ingredient;
        private final int safetyScore;
        private final int ecoFriendlinessScore;
        private final List<String> healthRisks;
        private final List<String> benefits;
        private final String safetyAssessment;
        private final String ecoAssessment;
        private final String recommendation;
        private final int confidence;
        
        public IngredientAnalysis(String ingredient, int safetyScore, int ecoFriendlinessScore,
                                List<String> healthRisks, List<String> benefits,
                                String safetyAssessment, String ecoAssessment,
                                String recommendation, int confidence) {
            this.ingredient = ingredient;
            this.safetyScore = safetyScore;
            this.ecoFriendlinessScore = ecoFriendlinessScore;
            this.healthRisks = healthRisks;
            this.benefits = benefits;
            this.safetyAssessment = safetyAssessment;
            this.ecoAssessment = ecoAssessment;
            this.recommendation = recommendation;
            this.confidence = confidence;
        }
        
        // Getters
        public String getIngredient() { return ingredient; }
        public int getSafetyScore() { return safetyScore; }
        public int getEcoFriendlinessScore() { return ecoFriendlinessScore; }
        public List<String> getHealthRisks() { return healthRisks; }
        public List<String> getBenefits() { return benefits; }
        public String getSafetyAssessment() { return safetyAssessment; }
        public String getEcoAssessment() { return ecoAssessment; }
        public String getRecommendation() { return recommendation; }
        public int getConfidence() { return confidence; }
    }
    
    public static class SubstituteRecommendation {
        private String ingredient;
        private int safetyScore;
        private int ecoFriendlinessScore;
        private List<String> benefits;
        private String reasoning;
        private String availability;
        private String cost;
        private int confidence;
        
        // Getters and setters
        public String getIngredient() { return ingredient; }
        public void setIngredient(String ingredient) { this.ingredient = ingredient; }
        public int getSafetyScore() { return safetyScore; }
        public void setSafetyScore(int safetyScore) { this.safetyScore = safetyScore; }
        public int getEcoFriendlinessScore() { return ecoFriendlinessScore; }
        public void setEcoFriendlinessScore(int ecoFriendlinessScore) { this.ecoFriendlinessScore = ecoFriendlinessScore; }
        public List<String> getBenefits() { return benefits; }
        public void setBenefits(List<String> benefits) { this.benefits = benefits; }
        public String getReasoning() { return reasoning; }
        public void setReasoning(String reasoning) { this.reasoning = reasoning; }
        public String getAvailability() { return availability; }
        public void setAvailability(String availability) { this.availability = availability; }
        public String getCost() { return cost; }
        public void setCost(String cost) { this.cost = cost; }
        public int getConfidence() { return confidence; }
        public void setConfidence(int confidence) { this.confidence = confidence; }
    }
}