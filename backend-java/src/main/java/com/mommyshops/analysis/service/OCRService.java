package com.mommyshops.analysis.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.HttpEntity;
import org.springframework.http.ResponseEntity;
import java.util.Base64;
import java.util.Map;

@Service
public class OCRService {
    
    private final RestTemplate restTemplate;
    private final String ollamaBaseUrl;
    private final String visionModel;
    
    public OCRService(RestTemplate restTemplate,
                     @Value("${ollama.base-url:http://localhost:11434}") String ollamaBaseUrl,
                     @Value("${ollama.vision-model:llava}") String visionModel) {
        this.restTemplate = restTemplate;
        this.ollamaBaseUrl = ollamaBaseUrl;
        this.visionModel = visionModel;
    }
    
    public String extractIngredientsFromImage(byte[] imageData) {
        try {
            String base64Image = Base64.getEncoder().encodeToString(imageData);
            
            String prompt = """
                Analyze this cosmetic product image and extract the ingredient list.
                Look for:
                1. The ingredients list on the product label
                2. INCI names of cosmetic ingredients
                3. Any safety warnings or allergen information
                
                Return ONLY the ingredient list in the following format:
                INGREDIENT1, INGREDIENT2, INGREDIENT3, etc.
                
                If you cannot find ingredients, return "INGREDIENTS_NOT_FOUND"
                """;
            
            Map<String, Object> requestBody = Map.of(
                "model", visionModel,
                "prompt", prompt,
                "images", new String[]{base64Image},
                "stream", false,
                "options", Map.of(
                    "temperature", 0.1,
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
            
            String responseText = (String) response.getBody().get("response");
            return parseIngredientResponse(responseText);
        } catch (Exception e) {
            return "OCR_ERROR";
        }
    }
    
    private String parseIngredientResponse(String response) {
        if (response == null || response.isEmpty()) {
            return "INGREDIENTS_NOT_FOUND";
        }
        
        // Look for ingredient list patterns
        String[] lines = response.split("\n");
        for (String line : lines) {
            line = line.trim();
            if (line.contains(",") && line.length() > 20) {
                // This looks like an ingredient list
                return line;
            }
        }
        
        // If no clear ingredient list found, return the whole response
        return response.length() > 500 ? response.substring(0, 500) + "..." : response;
    }
}