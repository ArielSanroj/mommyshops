package com.mommyshops.analysis.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.HttpEntity;
import org.springframework.http.ResponseEntity;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.*;
import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.util.stream.Collectors;

/**
 * Enhanced OCR service with advanced image processing and AI integration
 * Based on the Python enhanced_ocr_analysis.py functionality
 */
@Service
public class EnhancedOCRService {
    
    private final RestTemplate restTemplate;
    private final String ollamaBaseUrl;
    private final String visionModel;
    
    // Common cosmetic ingredients for pattern matching
    private static final Set<String> COMMON_INGREDIENTS = Set.of(
        "water", "aqua", "glycerin", "hyaluronic acid", "vitamin c", "niacinamide",
        "ceramides", "peptides", "retinol", "aloe vera", "shea butter", "coconut oil",
        "jojoba oil", "argan oil", "squalane", "collagen", "elastin", "antioxidants",
        "spf", "sunscreen", "titanium dioxide", "zinc oxide", "dimethicone",
        "cyclopentasiloxane", "phenoxyethanol", "parabens", "fragrance", "parfum"
    );
    
    // Safety classification for ingredients
    private static final Set<String> SAFE_INGREDIENTS = Set.of(
        "water", "aqua", "glycerin", "hyaluronic acid", "vitamin c",
        "niacinamide", "ceramides", "peptides", "aloe vera", "shea butter",
        "coconut oil", "jojoba oil", "argan oil", "squalane"
    );
    
    private static final Set<String> MODERATE_INGREDIENTS = Set.of(
        "retinol", "spf", "sunscreen", "titanium dioxide", "zinc oxide",
        "dimethicone", "cyclopentasiloxane"
    );
    
    private static final Set<String> CAUTION_INGREDIENTS = Set.of(
        "parabens", "fragrance", "parfum", "alcohol", "sulfates",
        "formaldehyde", "phthalates"
    );
    
    // Product type patterns
    private static final Set<String> PRODUCT_TYPES = Set.of(
        "lotion", "cream", "serum", "moisturizer", "cleanser", "toner",
        "sunscreen", "spf", "mask", "scrub", "gel", "oil", "balm",
        "hidratante", "corporal", "facial", "anti-aging", "anti-edad"
    );
    
    // Brand patterns
    private static final Pattern BRAND_PATTERNS = Pattern.compile(
        "([A-Z][a-z]+)\\s+(feeling|natura|loreal|maybelline|revlon|covergirl)|" +
        "(natura|feeling|loreal|maybelline|revlon|covergirl)|" +
        "([A-Z][A-Z\\s]+)\\s+(feeling|natura)",
        Pattern.CASE_INSENSITIVE
    );
    
    // Claim patterns
    private static final Pattern CLAIM_PATTERNS = Pattern.compile(
        "probado\\s+dermatol[oó]gicamente|" +
        "testado\\s+dermatol[oó]gicamente|" +
        "hipoalerg[eé]nico|" +
        "sin\\s+parabenos|" +
        "org[aá]nico|" +
        "natural|" +
        "anti-edad|" +
        "anti-aging|" +
        "hidratante|" +
        "nutritivo",
        Pattern.CASE_INSENSITIVE
    );
    
    // Warning patterns
    private static final Pattern WARNING_PATTERNS = Pattern.compile(
        "evitar\\s+contacto\\s+con\\s+los\\s+ojos|" +
        "para\\s+uso\\s+externo|" +
        "no\\s+ingerir|" +
        "mantener\\s+fuera\\s+del\\s+alcance\\s+de\\s+los\\s+ni[ñn]os|" +
        "probar\\s+en\\s+una\\s+peque[ñn]a\\s+[áa]rea",
        Pattern.CASE_INSENSITIVE
    );
    
    // Net content patterns
    private static final Pattern NET_CONTENT_PATTERNS = Pattern.compile(
        "(\\d+)\\s*(ml|g|oz|fl\\s*oz)|" +
        "cont\\.\\s*neto\\s*(\\d+)\\s*(ml|g|oz)|" +
        "net\\s*content\\s*(\\d+)\\s*(ml|g|oz)",
        Pattern.CASE_INSENSITIVE
    );
    
    public EnhancedOCRService(RestTemplate restTemplate,
                             @Value("${ollama.base-url:http://localhost:11434}") String ollamaBaseUrl,
                             @Value("${ollama.vision-model:llava}") String visionModel,
                             ) {
        this.restTemplate = restTemplate;
        this.ollamaBaseUrl = ollamaBaseUrl;
        this.visionModel = visionModel;
    }
    
    /**
     * Enhanced image analysis with multiple OCR methods and AI processing
     */
    public EnhancedOCRAnalysisResult analyzeImageEnhanced(byte[] imageData) {
        try {
            String base64Image = Base64.getEncoder().encodeToString(imageData);
            
            // 1. Extract text using multiple methods
            Map<String, String> textResults = extractTextMultipleMethods(base64Image);
            
            // 2. Clean and merge text
            String finalText = cleanAndMergeText(textResults);
            
            // 3. Enhance text with Ollama if available
            String enhancedText = enhanceTextWithOllama(finalText);
            
            // 4. Extract cosmetic information
            CosmeticInfo cosmeticInfo = extractCosmeticInfo(enhancedText);
            
            // 5. Analyze safety score
            SafetyAnalysis safetyAnalysis = analyzeSafetyScore(cosmeticInfo.getIngredients());
            
            // 6. Generate additional AI insights
            String aiInsights = generateAIInsights(cosmeticInfo.getIngredients());
            
            return new EnhancedOCRAnalysisResult(
                enhancedText,
                cosmeticInfo,
                safetyAnalysis,
                textResults,
                aiInsights
            );
            
        } catch (Exception e) {
            return new EnhancedOCRAnalysisResult(
                "Error analyzing image: " + e.getMessage(),
                new CosmeticInfo(),
                new SafetyAnalysis(),
                Map.of("error", e.getMessage()),
                ""
            );
        }
    }
    
    /**
     * Extract text using multiple OCR methods
     */
    private Map<String, String> extractTextMultipleMethods(String base64Image) {
        Map<String, String> results = new HashMap<>();
        
        try {
            // Method 1: Standard Ollama vision analysis
            String standardText = extractTextWithOllama(base64Image, "standard");
            results.put("standard", standardText);
            
            // Method 2: Detailed ingredient analysis
            String ingredientText = extractTextWithOllama(base64Image, "ingredients");
            results.put("ingredients", ingredientText);
            
            // Method 3: Product information analysis
            String productText = extractTextWithOllama(base64Image, "product");
            results.put("product", productText);
            
            // Method 4: Safety information analysis
            String safetyText = extractTextWithOllama(base64Image, "safety");
            results.put("safety", safetyText);
            
        } catch (Exception e) {
            results.put("error", "Error extracting text: " + e.getMessage());
        }
        
        return results;
    }
    
    /**
     * Extract text using Ollama with different prompts
     */
    private String extractTextWithOllama(String base64Image, String method) {
        try {
            String prompt = getPromptForMethod(method);
            
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
            return responseText != null ? responseText.trim() : "";
            
        } catch (Exception e) {
            return "Error with " + method + " method: " + e.getMessage();
        }
    }
    
    /**
     * Get appropriate prompt for each OCR method
     */
    private String getPromptForMethod(String method) {
        return switch (method) {
            case "ingredients" -> """
                Analyze this cosmetic product image and extract ONLY the ingredient list.
                Look for:
                1. The complete ingredients list on the product label
                2. INCI names of cosmetic ingredients
                3. Any safety warnings or allergen information
                
                Return ONLY the ingredient list in the following format:
                INGREDIENT1, INGREDIENT2, INGREDIENT3, etc.
                
                If you cannot find ingredients, return "INGREDIENTS_NOT_FOUND"
                """;
            case "product" -> """
                Analyze this cosmetic product image and extract product information.
                Look for:
                1. Product name and brand
                2. Product type (shampoo, cream, lotion, etc.)
                3. Net content (ml, oz, etc.)
                4. Product claims and benefits
                
                Return the information in a structured format.
                """;
            case "safety" -> """
                Analyze this cosmetic product image for safety information.
                Look for:
                1. Safety warnings
                2. Usage instructions
                3. Age restrictions
                4. Allergen information
                
                Return the safety information found.
                """;
            default -> """
                Analyze this cosmetic product image and extract all visible text.
                Focus on:
                1. Product name and brand
                2. Ingredient list
                3. Product claims
                4. Safety warnings
                5. Net content
                
                Return all text found in the image.
                """;
        };
    }
    
    /**
     * Clean and merge text from multiple methods
     */
    private String cleanAndMergeText(Map<String, String> textResults) {
        List<String> allTexts = textResults.values().stream()
            .filter(text -> text != null && !text.trim().isEmpty())
            .collect(Collectors.toList());
        
        if (allTexts.isEmpty()) {
            return "";
        }
        
        // Use the longest text as base
        String baseText = allTexts.stream()
            .max(Comparator.comparing(String::length))
            .orElse("");
        
        // Clean text
        String cleaned = cleanText(baseText);
        
        // Add missing information from other methods
        for (String text : allTexts) {
            if (!text.equals(baseText) && text.length() > 10) {
                // Find words not in base text
                Set<String> baseWords = Arrays.stream(cleaned.toLowerCase().split("\\s+"))
                    .collect(Collectors.toSet());
                Set<String> newWords = Arrays.stream(text.toLowerCase().split("\\s+"))
                    .collect(Collectors.toSet());
                
                Set<String> missingWords = new HashSet<>(newWords);
                missingWords.removeAll(baseWords);
                
                if (!missingWords.isEmpty()) {
                    String missingText = String.join(" ", missingWords);
                    cleaned += " " + missingText;
                }
            }
        }
        
        return cleaned;
    }
    
    /**
     * Enhance text using Ollama AI
     */
    private String enhanceTextWithOllama(String text) {
        if (text == null || text.trim().isEmpty()) {
            return text;
        }
        
        try {
            String prompt = String.format("""
                Improve and correct this OCR text from a cosmetic product image:
                
                Original text: %s
                
                Please:
                1. Fix any OCR errors
                2. Correct ingredient names to proper INCI names
                3. Improve readability
                4. Maintain all important information
                
                Return the improved text:
                """, text);
            
            Map<String, Object> requestBody = Map.of(
                "model", "llama3.1",
                "prompt", prompt,
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
            return responseText != null && responseText.length() > text.length() * 0.5 
                ? responseText.trim() 
                : text;
                
        } catch (Exception e) {
            return text; // Return original text if enhancement fails
        }
    }
    
    /**
     * Clean extracted text
     */
    private String cleanText(String text) {
        if (text == null || text.isEmpty()) {
            return "";
        }
        
        // Remove problematic special characters
        text = text.replaceAll("[^\\w\\s.,;:()\\[\\]{}'\"\\-]", " ");
        
        // Remove multiple spaces
        text = text.replaceAll("\\s+", " ");
        
        // Remove empty lines
        String[] lines = text.split("\\n");
        List<String> nonEmptyLines = Arrays.stream(lines)
            .map(String::trim)
            .filter(line -> !line.isEmpty())
            .collect(Collectors.toList());
        
        return String.join(" ", nonEmptyLines).trim();
    }
    
    /**
     * Extract cosmetic-specific information
     */
    private CosmeticInfo extractCosmeticInfo(String text) {
        CosmeticInfo info = new CosmeticInfo();
        info.setExtractedText(text);
        
        if (text == null || text.isEmpty()) {
            return info;
        }
        
        String textLower = text.toLowerCase();
        
        // Extract brand
        Matcher brandMatcher = BRAND_PATTERNS.matcher(text);
        if (brandMatcher.find()) {
            info.setBrand(brandMatcher.group(1) != null ? brandMatcher.group(1) : brandMatcher.group(0));
        }
        
        // Extract product type
        for (String productType : PRODUCT_TYPES) {
            if (textLower.contains(productType)) {
                info.setProductType(productType);
                break;
            }
        }
        
        // Extract ingredients
        List<String> ingredients = new ArrayList<>();
        for (String ingredient : COMMON_INGREDIENTS) {
            if (textLower.contains(ingredient)) {
                ingredients.add(ingredient);
            }
        }
        info.setIngredients(ingredients);
        
        // Extract claims
        List<String> claims = new ArrayList<>();
        Matcher claimMatcher = CLAIM_PATTERNS.matcher(text);
        while (claimMatcher.find()) {
            claims.add(claimMatcher.group());
        }
        info.setClaims(claims);
        
        // Extract warnings
        List<String> warnings = new ArrayList<>();
        Matcher warningMatcher = WARNING_PATTERNS.matcher(text);
        while (warningMatcher.find()) {
            warnings.add(warningMatcher.group());
        }
        info.setWarnings(warnings);
        
        // Extract net content
        Matcher netContentMatcher = NET_CONTENT_PATTERNS.matcher(text);
        if (netContentMatcher.find()) {
            info.setNetContent(netContentMatcher.group(1) + " " + netContentMatcher.group(2));
        }
        
        return info;
    }
    
    /**
     * Analyze safety score of ingredients
     */
    private SafetyAnalysis analyzeSafetyScore(List<String> ingredients) {
        SafetyAnalysis analysis = new SafetyAnalysis();
        analysis.setOverallScore(5.0);
        
        List<String> safeIngredients = new ArrayList<>();
        List<String> moderateIngredients = new ArrayList<>();
        List<String> cautionIngredients = new ArrayList<>();
        List<String> recommendations = new ArrayList<>();
        
        for (String ingredient : ingredients) {
            String ingredientLower = ingredient.toLowerCase();
            
            if (SAFE_INGREDIENTS.stream().anyMatch(safe -> ingredientLower.contains(safe))) {
                safeIngredients.add(ingredient);
            } else if (MODERATE_INGREDIENTS.stream().anyMatch(mod -> ingredientLower.contains(mod))) {
                moderateIngredients.add(ingredient);
            } else if (CAUTION_INGREDIENTS.stream().anyMatch(caution -> ingredientLower.contains(caution))) {
                cautionIngredients.add(ingredient);
            }
        }
        
        analysis.setSafeIngredients(safeIngredients);
        analysis.setModerateIngredients(moderateIngredients);
        analysis.setCautionIngredients(cautionIngredients);
        
        // Calculate overall score
        int totalCount = ingredients.size();
        if (totalCount > 0) {
            double score = 10.0 - (cautionIngredients.size() * 3.0 + moderateIngredients.size() * 1.0) / totalCount * 10.0;
            analysis.setOverallScore(Math.max(1.0, Math.min(10.0, score)));
        }
        
        // Generate recommendations
        if (!cautionIngredients.isEmpty()) {
            recommendations.add("⚠️ Contiene ingredientes que requieren precaución");
        }
        if (!moderateIngredients.isEmpty()) {
            recommendations.add("🟡 Algunos ingredientes requieren uso moderado");
        }
        if (safeIngredients.size() > totalCount * 0.7) {
            recommendations.add("✅ Mayoría de ingredientes seguros");
        }
        
        analysis.setRecommendations(recommendations);
        
        return analysis;
    }
    
    /**
     * Generate additional AI insights
     */
    private String generateAIInsights(List<String> ingredients) {
        if (ingredients == null || ingredients.isEmpty()) {
            return "";
        }
        
        try {
            String prompt = String.format("""
                Analyze these cosmetic ingredients and provide insights:
                
                Ingredients: %s
                
                Please provide:
                1. Safety assessment
                2. Potential benefits
                3. Skin type recommendations
                4. Usage suggestions
                5. Any concerns or warnings
                
                Keep the response concise and practical.
                """, String.join(", ", ingredients));
            
            Map<String, Object> requestBody = Map.of(
                "model", "llama3.1",
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
            
            String responseText = (String) response.getBody().get("response");
            return responseText != null ? responseText.trim() : "";
            
        } catch (Exception e) {
            return "Error generating AI insights: " + e.getMessage();
        }
    }
    
    // Data classes for results
    public static class EnhancedOCRAnalysisResult {
        private String extractedText;
        private CosmeticInfo cosmeticInfo;
        private SafetyAnalysis safetyAnalysis;
        private Map<String, String> textMethods;
        private String aiInsights;
        
        public EnhancedOCRAnalysisResult() {}
        
        public EnhancedOCRAnalysisResult(String extractedText, CosmeticInfo cosmeticInfo, 
                                       SafetyAnalysis safetyAnalysis, Map<String, String> textMethods, 
                                       String aiInsights) {
            this.extractedText = extractedText;
            this.cosmeticInfo = cosmeticInfo;
            this.safetyAnalysis = safetyAnalysis;
            this.textMethods = textMethods;
            this.aiInsights = aiInsights;
        }
        
        // Getters and setters
        public String getExtractedText() { return extractedText; }
        public void setExtractedText(String extractedText) { this.extractedText = extractedText; }
        public CosmeticInfo getCosmeticInfo() { return cosmeticInfo; }
        public void setCosmeticInfo(CosmeticInfo cosmeticInfo) { this.cosmeticInfo = cosmeticInfo; }
        public SafetyAnalysis getSafetyAnalysis() { return safetyAnalysis; }
        public void setSafetyAnalysis(SafetyAnalysis safetyAnalysis) { this.safetyAnalysis = safetyAnalysis; }
        public Map<String, String> getTextMethods() { return textMethods; }
        public void setTextMethods(Map<String, String> textMethods) { this.textMethods = textMethods; }
        public String getAiInsights() { return aiInsights; }
        public void setAiInsights(String aiInsights) { this.aiInsights = aiInsights; }
    }
    
    public static class CosmeticInfo {
        private String productName = "";
        private String brand = "";
        private String productType = "";
        private List<String> ingredients = new ArrayList<>();
        private List<String> claims = new ArrayList<>();
        private List<String> warnings = new ArrayList<>();
        private String netContent = "";
        private String extractedText = "";
        
        // Getters and setters
        public String getProductName() { return productName; }
        public void setProductName(String productName) { this.productName = productName; }
        public String getBrand() { return brand; }
        public void setBrand(String brand) { this.brand = brand; }
        public String getProductType() { return productType; }
        public void setProductType(String productType) { this.productType = productType; }
        public List<String> getIngredients() { return ingredients; }
        public void setIngredients(List<String> ingredients) { this.ingredients = ingredients; }
        public List<String> getClaims() { return claims; }
        public void setClaims(List<String> claims) { this.claims = claims; }
        public List<String> getWarnings() { return warnings; }
        public void setWarnings(List<String> warnings) { this.warnings = warnings; }
        public String getNetContent() { return netContent; }
        public void setNetContent(String netContent) { this.netContent = netContent; }
        public String getExtractedText() { return extractedText; }
        public void setExtractedText(String extractedText) { this.extractedText = extractedText; }
    }
    
    public static class SafetyAnalysis {
        private double overallScore = 5.0;
        private List<String> safeIngredients = new ArrayList<>();
        private List<String> moderateIngredients = new ArrayList<>();
        private List<String> cautionIngredients = new ArrayList<>();
        private List<String> recommendations = new ArrayList<>();
        
        // Getters and setters
        public double getOverallScore() { return overallScore; }
        public void setOverallScore(double overallScore) { this.overallScore = overallScore; }
        public List<String> getSafeIngredients() { return safeIngredients; }
        public void setSafeIngredients(List<String> safeIngredients) { this.safeIngredients = safeIngredients; }
        public List<String> getModerateIngredients() { return moderateIngredients; }
        public void setModerateIngredients(List<String> moderateIngredients) { this.moderateIngredients = moderateIngredients; }
        public List<String> getCautionIngredients() { return cautionIngredients; }
        public void setCautionIngredients(List<String> cautionIngredients) { this.cautionIngredients = cautionIngredients; }
        public List<String> getRecommendations() { return recommendations; }
        public void setRecommendations(List<String> recommendations) { this.recommendations = recommendations; }
    }
}