package com.mommyshops.ai.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;
import com.mommyshops.profile.domain.UserProfile;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import java.util.Map;
import java.util.List;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;

@Service
public class OllamaService {
    
    private static final Logger logger = LoggerFactory.getLogger(OllamaService.class);
    
    private final RestTemplate restTemplate;
    private final String ollamaBaseUrl;
    private final String modelName;
    private final String visionModelName;
    private final ObjectMapper objectMapper;
    
    public OllamaService(RestTemplate restTemplate,
                        @Value("${ollama.base-url:http://localhost:11434}") String ollamaBaseUrl,
                        @Value("${ollama.model:llama3.1}") String modelName,
                        @Value("${ollama.vision-model:llava}") String visionModelName,
                        ObjectMapper objectMapper) {
        this.restTemplate = restTemplate;
        this.ollamaBaseUrl = ollamaBaseUrl;
        this.modelName = modelName;
        this.visionModelName = visionModelName;
        this.objectMapper = objectMapper;
    }
    
    public IngredientAnalysis analyzeIngredient(String ingredient, UserProfile profile) {
        try {
            String prompt = buildAnalysisPrompt(ingredient, profile);
            
            Map<String, Object> requestBody = Map.of(
                "model", modelName,
                "prompt", prompt,
                "stream", false,
                "options", Map.of(
                    "temperature", 0.3,
                    "top_p", 0.9
                )
            );
            
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);
            
            ResponseEntity<Map> response = restTemplate.postForEntity(
                ollamaBaseUrl + "/api/generate", 
                request, 
                Map.class
            );
            
            return parseAnalysisResponse(response.getBody());
        } catch (Exception e) {
            logger.error("Error analyzing ingredient: " + ingredient, e);
            return createErrorAnalysis(ingredient);
        }
    }
    
    public Boolean isHealthy() {
        try {
            restTemplate.getForEntity(ollamaBaseUrl + "/api/tags", Map.class);
            logger.info("Ollama health check successful");
            return true;
        } catch (Exception e) {
            logger.error("Ollama health check failed", e);
            return false;
        }
    }
    
    public List<SubstituteRecommendation> generateSubstitutes(String ingredient, 
                                                             IngredientAnalysis analysis, 
                                                             UserProfile profile) {
        try {
            String prompt = buildSubstitutePrompt(ingredient, analysis, profile);
            
            Map<String, Object> requestBody = Map.of(
                "model", modelName,
                "prompt", prompt,
                "stream", false,
                "options", Map.of(
                    "temperature", 0.4,
                    "top_p", 0.9
                )
            );
            
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);
            
            ResponseEntity<Map> response = restTemplate.postForEntity(
                ollamaBaseUrl + "/api/generate", 
                request, 
                Map.class
            );
            
            return parseSubstituteResponse(response.getBody());
        } catch (Exception e) {
            logger.error("Error generating substitutes for ingredient: " + ingredient, e);
            return new ArrayList<>();
        }
    }
    
    public ProductImageAnalysis analyzeProductImage(String base64Image, UserProfile profile) {
        try {
            String prompt = buildImageAnalysisPrompt(profile);
            
            Map<String, Object> requestBody = Map.of(
                "model", visionModelName,
                "prompt", prompt,
                "images", List.of(base64Image),
                "stream", false,
                "options", Map.of(
                    "temperature", 0.3,
                    "top_p", 0.9
                )
            );
            
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);
            
            ResponseEntity<Map> response = restTemplate.postForEntity(
                ollamaBaseUrl + "/api/generate", 
                request, 
                Map.class
            );
            
            return parseImageAnalysisResponse(response.getBody());
        } catch (Exception e) {
            logger.error("Error analyzing product image", e);
            return createErrorImageAnalysis();
        }
    }
    
    private String buildAnalysisPrompt(String ingredient, UserProfile profile) {
        return String.format("""
            Analyze the cosmetic ingredient: %s
            
            User Profile:
            - Hair Type: %s
            - Facial Skin: %s
            - Body Skin: %s
            - Budget: %s
            - Brand Preferences: %s
            
            Please provide a comprehensive analysis in JSON format with the following structure:
            {
                "ingredient": "%s",
                "safetyScore": 0-100,
                "ecoFriendlinessScore": 0-100,
                "healthRisks": ["risk1", "risk2"],
                "benefits": ["benefit1", "benefit2"],
                "allergenPotential": "low|medium|high",
                "pregnancySafe": true|false,
                "childSafe": true|false,
                "sustainability": "poor|fair|good|excellent",
                "biodegradability": "poor|fair|good|excellent",
                "confidence": 0-100,
                "recommendation": "avoid|caution|safe|recommended",
                "reasoning": "detailed explanation"
            }
            
            Focus on:
            1. Health safety for mothers and families
            2. Environmental impact and sustainability
            3. Allergen potential and skin sensitivity
            4. Pregnancy and child safety
            5. Biodegradability and eco-friendliness
            """, 
            ingredient, 
            profile.getHairPreferences(),
            profile.getFacialSkinPreferences(),
            profile.getBodySkinPreferences(),
            profile.getBudgetPreferences(),
            profile.getBrandPreferences(),
            ingredient
        );
    }
    
    private String buildSubstitutePrompt(String ingredient, IngredientAnalysis analysis, UserProfile profile) {
        return String.format("""
            Based on the analysis of %s, suggest safer and more eco-friendly alternatives.
            
            Original Analysis:
            - Safety Score: %d/100
            - Eco-Friendliness: %d/100
            - Health Risks: %s
            - Recommendation: %s
            
            User Profile:
            - Hair Type: %s
            - Facial Skin: %s
            - Body Skin: %s
            - Budget: %s
            
            Provide 3-5 substitute recommendations in JSON format:
            [
                {
                    "ingredient": "substitute_name",
                    "safetyScore": 0-100,
                    "ecoFriendlinessScore": 0-100,
                    "benefits": ["benefit1", "benefit2"],
                    "reasoning": "why this is better",
                    "availability": "common|moderate|rare",
                    "cost": "low|medium|high",
                    "confidence": 0-100
                }
            ]
            
            Prioritize:
            1. Higher safety scores
            2. Better eco-friendliness
            3. Similar functionality
            4. Budget considerations
            5. Local availability
            """,
            ingredient,
            analysis.getSafetyScore(),
            analysis.getEcoFriendlinessScore(),
            String.join(", ", analysis.getHealthRisks()),
            analysis.getRecommendation(),
            profile.getHairPreferences(),
            profile.getFacialSkinPreferences(),
            profile.getBodySkinPreferences(),
            profile.getBudgetPreferences()
        );
    }
    
    private String buildImageAnalysisPrompt(UserProfile profile) {
        return String.format("""
            You are a cosmetic safety expert analyzing a product image. Please analyze this cosmetic product image and provide a comprehensive safety and eco-friendliness assessment.
            
            User Profile:
            - Hair Type: %s
            - Facial Skin: %s
            - Body Skin: %s
            - Budget: %s
            - Brand Preferences: %s
            
            Please provide your analysis in JSON format with the following structure:
            {
                "productName": "identified product name",
                "brand": "brand name if visible",
                "ingredients": ["ingredient1", "ingredient2"],
                "safetyScore": 0-100,
                "ecoFriendlinessScore": 0-100,
                "healthRisks": ["risk1", "risk2"],
                "benefits": ["benefit1", "benefit2"],
                "allergenPotential": "low|medium|high",
                "pregnancySafe": true|false,
                "childSafe": true|false,
                "sustainability": "poor|fair|good|excellent",
                "biodegradability": "poor|fair|good|excellent",
                "confidence": 0-100,
                "recommendation": "avoid|caution|safe|recommended",
                "reasoning": "detailed explanation",
                "alternatives": ["safer alternative 1", "safer alternative 2"]
            }
            
            Focus on:
            1. Health safety for mothers and families
            2. Environmental impact and sustainability
            3. Allergen potential and skin sensitivity
            4. Pregnancy and child safety
            5. Biodegradability and eco-friendliness
            6. Product type and intended use
            7. Ingredient list visibility and analysis
            """,
            profile.getHairPreferences(),
            profile.getFacialSkinPreferences(),
            profile.getBodySkinPreferences(),
            profile.getBudgetPreferences(),
            profile.getBrandPreferences()
        );
    }
    
    private IngredientAnalysis parseAnalysisResponse(Map<String, Object> response) {
        try {
            String responseText = (String) response.get("response");
            logger.debug("Ollama response: {}", responseText);
            
            // Try to extract JSON from the response
            String jsonText = extractJsonFromResponse(responseText);
            JsonNode jsonNode = objectMapper.readTree(jsonText);
            
            IngredientAnalysis analysis = new IngredientAnalysis();
            analysis.setIngredient(jsonNode.path("ingredient").asText());
            analysis.setSafetyScore(jsonNode.path("safetyScore").asInt(0));
            analysis.setEcoFriendlinessScore(jsonNode.path("ecoFriendlinessScore").asInt(0));
            analysis.setAllergenPotential(jsonNode.path("allergenPotential").asText("unknown"));
            analysis.setPregnancySafe(jsonNode.path("pregnancySafe").asBoolean(false));
            analysis.setChildSafe(jsonNode.path("childSafe").asBoolean(false));
            analysis.setSustainability(jsonNode.path("sustainability").asText("unknown"));
            analysis.setBiodegradability(jsonNode.path("biodegradability").asText("unknown"));
            analysis.setConfidence(jsonNode.path("confidence").asInt(0));
            analysis.setRecommendation(jsonNode.path("recommendation").asText("unknown"));
            analysis.setReasoning(jsonNode.path("reasoning").asText("No reasoning provided"));
            
            // Parse arrays
            List<String> healthRisks = new ArrayList<>();
            if (jsonNode.has("healthRisks") && jsonNode.get("healthRisks").isArray()) {
                for (JsonNode risk : jsonNode.get("healthRisks")) {
                    healthRisks.add(risk.asText());
                }
            }
            analysis.setHealthRisks(healthRisks);
            
            List<String> benefits = new ArrayList<>();
            if (jsonNode.has("benefits") && jsonNode.get("benefits").isArray()) {
                for (JsonNode benefit : jsonNode.get("benefits")) {
                    benefits.add(benefit.asText());
                }
            }
            analysis.setBenefits(benefits);
            
            return analysis;
        } catch (Exception e) {
            logger.error("Error parsing Ollama analysis response", e);
            return createErrorAnalysis("unknown");
        }
    }
    
    private List<SubstituteRecommendation> parseSubstituteResponse(Map<String, Object> response) {
        try {
            String responseText = (String) response.get("response");
            logger.debug("Ollama substitute response: {}", responseText);
            
            // Try to extract JSON from the response
            String jsonText = extractJsonFromResponse(responseText);
            JsonNode jsonArray = objectMapper.readTree(jsonText);
            
            List<SubstituteRecommendation> recommendations = new ArrayList<>();
            
            if (jsonArray.isArray()) {
                for (JsonNode item : jsonArray) {
                    SubstituteRecommendation rec = new SubstituteRecommendation();
                    rec.setIngredient(item.path("ingredient").asText());
                    rec.setSafetyScore(item.path("safetyScore").asInt(0));
                    rec.setEcoFriendlinessScore(item.path("ecoFriendlinessScore").asInt(0));
                    rec.setReasoning(item.path("reasoning").asText("No reasoning provided"));
                    rec.setAvailability(item.path("availability").asText("unknown"));
                    rec.setCost(item.path("cost").asText("unknown"));
                    rec.setConfidence(item.path("confidence").asInt(0));
                    
                    // Parse benefits array
                    List<String> benefits = new ArrayList<>();
                    if (item.has("benefits") && item.get("benefits").isArray()) {
                        for (JsonNode benefit : item.get("benefits")) {
                            benefits.add(benefit.asText());
                        }
                    }
                    rec.setBenefits(benefits);
                    
                    recommendations.add(rec);
                }
            }
            
            return recommendations;
        } catch (Exception e) {
            logger.error("Error parsing Ollama substitute response", e);
            return new ArrayList<>();
        }
    }
    
    private ProductImageAnalysis parseImageAnalysisResponse(Map<String, Object> response) {
        try {
            String responseText = (String) response.get("response");
            logger.debug("Ollama image analysis response: {}", responseText);
            
            // Try to extract JSON from the response
            String jsonText = extractJsonFromResponse(responseText);
            JsonNode jsonNode = objectMapper.readTree(jsonText);
            
            ProductImageAnalysis analysis = new ProductImageAnalysis();
            analysis.setProductName(jsonNode.path("productName").asText("Unknown Product"));
            analysis.setBrand(jsonNode.path("brand").asText("Unknown Brand"));
            analysis.setSafetyScore(jsonNode.path("safetyScore").asInt(0));
            analysis.setEcoFriendlinessScore(jsonNode.path("ecoFriendlinessScore").asInt(0));
            analysis.setAllergenPotential(jsonNode.path("allergenPotential").asText("unknown"));
            analysis.setPregnancySafe(jsonNode.path("pregnancySafe").asBoolean(false));
            analysis.setChildSafe(jsonNode.path("childSafe").asBoolean(false));
            analysis.setSustainability(jsonNode.path("sustainability").asText("unknown"));
            analysis.setBiodegradability(jsonNode.path("biodegradability").asText("unknown"));
            analysis.setConfidence(jsonNode.path("confidence").asInt(0));
            analysis.setRecommendation(jsonNode.path("recommendation").asText("unknown"));
            analysis.setReasoning(jsonNode.path("reasoning").asText("No reasoning provided"));
            
            // Parse arrays
            List<String> ingredients = new ArrayList<>();
            if (jsonNode.has("ingredients") && jsonNode.get("ingredients").isArray()) {
                for (JsonNode ingredient : jsonNode.get("ingredients")) {
                    ingredients.add(ingredient.asText());
                }
            }
            analysis.setIngredients(ingredients);
            
            List<String> healthRisks = new ArrayList<>();
            if (jsonNode.has("healthRisks") && jsonNode.get("healthRisks").isArray()) {
                for (JsonNode risk : jsonNode.get("healthRisks")) {
                    healthRisks.add(risk.asText());
                }
            }
            analysis.setHealthRisks(healthRisks);
            
            List<String> benefits = new ArrayList<>();
            if (jsonNode.has("benefits") && jsonNode.get("benefits").isArray()) {
                for (JsonNode benefit : jsonNode.get("benefits")) {
                    benefits.add(benefit.asText());
                }
            }
            analysis.setBenefits(benefits);
            
            List<String> alternatives = new ArrayList<>();
            if (jsonNode.has("alternatives") && jsonNode.get("alternatives").isArray()) {
                for (JsonNode alternative : jsonNode.get("alternatives")) {
                    alternatives.add(alternative.asText());
                }
            }
            analysis.setAlternatives(alternatives);
            
            return analysis;
        } catch (Exception e) {
            logger.error("Error parsing Ollama image analysis response", e);
            return createErrorImageAnalysis();
        }
    }
    
    private String extractJsonFromResponse(String response) {
        // Try to find JSON object or array in the response
        int jsonStart = response.indexOf("{");
        int arrayStart = response.indexOf("[");
        
        if (jsonStart == -1 && arrayStart == -1) {
            return response; // Return as-is if no JSON found
        }
        
        int start = (jsonStart != -1 && (arrayStart == -1 || jsonStart < arrayStart)) ? jsonStart : arrayStart;
        
        // Find matching closing brace or bracket
        char openChar = response.charAt(start);
        char closeChar = (openChar == '{') ? '}' : ']';
        
        int depth = 1;
        int end = start + 1;
        while (end < response.length() && depth > 0) {
            if (response.charAt(end) == openChar) {
                depth++;
            } else if (response.charAt(end) == closeChar) {
                depth--;
            }
            end++;
        }
        
        if (depth == 0) {
            return response.substring(start, end);
        }
        
        return response; // Return as-is if no complete JSON found
    }
    
    private IngredientAnalysis createErrorAnalysis(String ingredient) {
        IngredientAnalysis analysis = new IngredientAnalysis();
        analysis.setIngredient(ingredient);
        analysis.setSafetyScore(0);
        analysis.setEcoFriendlinessScore(0);
        analysis.setHealthRisks(List.of("Analysis failed"));
        analysis.setBenefits(List.of());
        analysis.setAllergenPotential("unknown");
        analysis.setPregnancySafe(false);
        analysis.setChildSafe(false);
        analysis.setSustainability("unknown");
        analysis.setBiodegradability("unknown");
        analysis.setConfidence(0);
        analysis.setRecommendation("avoid");
        analysis.setReasoning("Unable to analyze ingredient due to technical error");
        return analysis;
    }
    
    private ProductImageAnalysis createErrorImageAnalysis() {
        ProductImageAnalysis analysis = new ProductImageAnalysis();
        analysis.setProductName("Unknown Product");
        analysis.setBrand("Unknown Brand");
        analysis.setSafetyScore(0);
        analysis.setEcoFriendlinessScore(0);
        analysis.setIngredients(List.of());
        analysis.setHealthRisks(List.of("Analysis failed"));
        analysis.setBenefits(List.of());
        analysis.setAllergenPotential("unknown");
        analysis.setPregnancySafe(false);
        analysis.setChildSafe(false);
        analysis.setSustainability("unknown");
        analysis.setBiodegradability("unknown");
        analysis.setConfidence(0);
        analysis.setRecommendation("avoid");
        analysis.setReasoning("Unable to analyze product image due to technical error");
        analysis.setAlternatives(List.of());
        return analysis;
    }
    
    // Data classes
    public static class IngredientAnalysis {
        private String ingredient;
        private int safetyScore;
        private int ecoFriendlinessScore;
        private List<String> healthRisks;
        private List<String> benefits;
        private String allergenPotential;
        private boolean pregnancySafe;
        private boolean childSafe;
        private String sustainability;
        private String biodegradability;
        private int confidence;
        private String recommendation;
        private String reasoning;
        
        // Getters and setters
        public String getIngredient() { return ingredient; }
        public void setIngredient(String ingredient) { this.ingredient = ingredient; }
        public int getSafetyScore() { return safetyScore; }
        public void setSafetyScore(int safetyScore) { this.safetyScore = safetyScore; }
        public int getEcoFriendlinessScore() { return ecoFriendlinessScore; }
        public void setEcoFriendlinessScore(int ecoFriendlinessScore) { this.ecoFriendlinessScore = ecoFriendlinessScore; }
        public List<String> getHealthRisks() { return healthRisks; }
        public void setHealthRisks(List<String> healthRisks) { this.healthRisks = healthRisks; }
        public List<String> getBenefits() { return benefits; }
        public void setBenefits(List<String> benefits) { this.benefits = benefits; }
        public String getAllergenPotential() { return allergenPotential; }
        public void setAllergenPotential(String allergenPotential) { this.allergenPotential = allergenPotential; }
        public boolean isPregnancySafe() { return pregnancySafe; }
        public void setPregnancySafe(boolean pregnancySafe) { this.pregnancySafe = pregnancySafe; }
        public boolean isChildSafe() { return childSafe; }
        public void setChildSafe(boolean childSafe) { this.childSafe = childSafe; }
        public String getSustainability() { return sustainability; }
        public void setSustainability(String sustainability) { this.sustainability = sustainability; }
        public String getBiodegradability() { return biodegradability; }
        public void setBiodegradability(String biodegradability) { this.biodegradability = biodegradability; }
        public int getConfidence() { return confidence; }
        public void setConfidence(int confidence) { this.confidence = confidence; }
        public String getRecommendation() { return recommendation; }
        public void setRecommendation(String recommendation) { this.recommendation = recommendation; }
        public String getReasoning() { return reasoning; }
        public void setReasoning(String reasoning) { this.reasoning = reasoning; }
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
    
    public static class ProductImageAnalysis {
        private String productName;
        private String brand;
        private List<String> ingredients;
        private int safetyScore;
        private int ecoFriendlinessScore;
        private List<String> healthRisks;
        private List<String> benefits;
        private String allergenPotential;
        private boolean pregnancySafe;
        private boolean childSafe;
        private String sustainability;
        private String biodegradability;
        private int confidence;
        private String recommendation;
        private String reasoning;
        private List<String> alternatives;
        
        // Getters and setters
        public String getProductName() { return productName; }
        public void setProductName(String productName) { this.productName = productName; }
        public String getBrand() { return brand; }
        public void setBrand(String brand) { this.brand = brand; }
        public List<String> getIngredients() { return ingredients; }
        public void setIngredients(List<String> ingredients) { this.ingredients = ingredients; }
        public int getSafetyScore() { return safetyScore; }
        public void setSafetyScore(int safetyScore) { this.safetyScore = safetyScore; }
        public int getEcoFriendlinessScore() { return ecoFriendlinessScore; }
        public void setEcoFriendlinessScore(int ecoFriendlinessScore) { this.ecoFriendlinessScore = ecoFriendlinessScore; }
        public List<String> getHealthRisks() { return healthRisks; }
        public void setHealthRisks(List<String> healthRisks) { this.healthRisks = healthRisks; }
        public List<String> getBenefits() { return benefits; }
        public void setBenefits(List<String> benefits) { this.benefits = benefits; }
        public String getAllergenPotential() { return allergenPotential; }
        public void setAllergenPotential(String allergenPotential) { this.allergenPotential = allergenPotential; }
        public boolean isPregnancySafe() { return pregnancySafe; }
        public void setPregnancySafe(boolean pregnancySafe) { this.pregnancySafe = pregnancySafe; }
        public boolean isChildSafe() { return childSafe; }
        public void setChildSafe(boolean childSafe) { this.childSafe = childSafe; }
        public String getSustainability() { return sustainability; }
        public void setSustainability(String sustainability) { this.sustainability = sustainability; }
        public String getBiodegradability() { return biodegradability; }
        public void setBiodegradability(String biodegradability) { this.biodegradability = biodegradability; }
        public int getConfidence() { return confidence; }
        public void setConfidence(int confidence) { this.confidence = confidence; }
        public String getRecommendation() { return recommendation; }
        public void setRecommendation(String recommendation) { this.recommendation = recommendation; }
        public String getReasoning() { return reasoning; }
        public void setReasoning(String reasoning) { this.reasoning = reasoning; }
        public List<String> getAlternatives() { return alternatives; }
        public void setAlternatives(List<String> alternatives) { this.alternatives = alternatives; }
    }
    
}