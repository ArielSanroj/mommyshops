import java.io.*;
import java.net.http.*;
import java.net.URI;
import java.nio.file.Files;
import java.util.Base64;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

/**
 * Real Ollama LLM Analysis for MommyShops
 * Uses actual Ollama API to analyze cosmetic product images
 */
public class RealImageAnalysis {
    
    private static final String OLLAMA_BASE_URL = "https://api.ollama.ai";
    private static final String MODEL_NAME = "llama3.1:8b";
    private static final String VISION_MODEL = "llava"; // For image analysis
    private static final String OLLAMA_API_KEY = "***REMOVED***";
    
    public static void main(String[] args) {
        System.out.println("🧪 MommyShops Real Ollama Analysis");
        System.out.println("==================================");
        System.out.println();
        
        String imagePath = "/Users/arielsanroj/downloads/test3.jpg";
        analyzeProductWithOllama(imagePath);
    }
    
    public static void analyzeProductWithOllama(String imagePath) {
        try {
            // Step 1: Check if image exists
            File imageFile = new File(imagePath);
            if (!imageFile.exists()) {
                System.out.println("❌ Image file not found: " + imagePath);
                return;
            }
            
            System.out.println("📁 Image File: " + imageFile.getName());
            System.out.println("📏 File Size: " + (imageFile.length() / 1024) + " KB");
            System.out.println();
            
            // Step 2: Convert image to base64
            System.out.println("🔄 Converting image to base64...");
            String base64Image = encodeImageToBase64(imageFile);
            System.out.println("✅ Image encoded successfully");
            System.out.println();
            
            // Step 3: Extract ingredients using vision model
            System.out.println("🔍 Step 1: Extracting ingredients using Ollama Vision...");
            String ingredients = extractIngredientsWithVision(base64Image);
            System.out.println("Extracted ingredients: " + ingredients);
            System.out.println();
            
            // Step 4: Analyze ingredients with LLM
            System.out.println("🤖 Step 2: Analyzing ingredients with Ollama LLM...");
            String analysis = analyzeIngredientsWithLLM(ingredients);
            System.out.println("Analysis complete!");
            System.out.println();
            
            // Step 5: Generate recommendations
            System.out.println("💡 Step 3: Generating recommendations...");
            String recommendations = generateRecommendationsWithLLM(ingredients, analysis);
            System.out.println("Recommendations generated!");
            System.out.println();
            
            // Step 6: Display final results
            displayFinalResults(ingredients, analysis, recommendations);
            
        } catch (Exception e) {
            System.err.println("❌ Error during analysis: " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    private static String encodeImageToBase64(File imageFile) throws IOException {
        byte[] imageBytes = Files.readAllBytes(imageFile.toPath());
        return Base64.getEncoder().encodeToString(imageBytes);
    }
    
    private static String extractIngredientsWithVision(String base64Image) throws Exception {
        String prompt = "Analyze this cosmetic product image and extract ONLY the ingredient list. " +
                       "Look for the ingredients section on the label and list them exactly as they appear. " +
                       "Return only the ingredients separated by commas, nothing else.";
        
        String requestBody = String.format("""
            {
                "model": "%s",
                "prompt": "%s",
                "images": ["%s"],
                "stream": false
            }
            """, VISION_MODEL, prompt, base64Image);
        
        return callOllamaAPI("/api/generate", requestBody);
    }
    
    private static String analyzeIngredientsWithLLM(String ingredients) throws Exception {
        String prompt = String.format("""
            You are a cosmetic safety expert. Analyze these cosmetic ingredients for safety and eco-friendliness:
            
            Ingredients: %s
            
            For each ingredient, provide:
            1. Safety score (0-100, where 100 is safest)
            2. Eco-friendliness score (0-100, where 100 is most eco-friendly)
            3. Risk level (LOW, MODERATE, HIGH)
            4. Main concerns (if any)
            
            Format your response as JSON:
            {
                "overall_safety_score": number,
                "overall_eco_score": number,
                "overall_recommendation": "RECOMMENDED/CAUTION/AVOID",
                "ingredients": [
                    {
                        "name": "ingredient_name",
                        "safety_score": number,
                        "eco_score": number,
                        "risk_level": "LOW/MODERATE/HIGH",
                        "concerns": ["concern1", "concern2"]
                    }
                ]
            }
            """, ingredients);
        
        String requestBody = String.format("""
            {
                "model": "%s",
                "prompt": "%s",
                "stream": false
            }
            """, MODEL_NAME, prompt);
        
        return callOllamaAPI("/api/generate", requestBody);
    }
    
    private static String generateRecommendationsWithLLM(String ingredients, String analysis) throws Exception {
        String prompt = String.format("""
            Based on this ingredient analysis, provide personalized recommendations:
            
            Ingredients: %s
            Analysis: %s
            
            Provide:
            1. Specific safer alternatives for concerning ingredients
            2. Recommended product types to look for
            3. Ingredients to avoid in future purchases
            4. Eco-friendly alternatives
            
            Format as JSON:
            {
                "alternatives": [
                    {
                        "ingredient_to_replace": "name",
                        "safer_alternative": "name",
                        "reason": "explanation"
                    }
                ],
                "product_recommendations": [
                    {
                        "type": "product_type",
                        "description": "description",
                        "key_benefits": ["benefit1", "benefit2"]
                    }
                ],
                "ingredients_to_avoid": ["ingredient1", "ingredient2"],
                "eco_tips": ["tip1", "tip2"]
            }
            """, ingredients, analysis);
        
        String requestBody = String.format("""
            {
                "model": "%s",
                "prompt": "%s",
                "stream": false
            }
            """, MODEL_NAME, prompt);
        
        return callOllamaAPI("/api/generate", requestBody);
    }
    
    private static String callOllamaAPI(String endpoint, String requestBody) throws Exception {
        HttpClient client = HttpClient.newHttpClient();
        
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(OLLAMA_BASE_URL + endpoint))
            .header("Content-Type", "application/json")
            .header("Authorization", "Bearer " + OLLAMA_API_KEY)
            .POST(HttpRequest.BodyPublishers.ofString(requestBody))
            .timeout(java.time.Duration.ofMinutes(5))
            .build();
        
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        
        if (response.statusCode() != 200) {
            throw new RuntimeException("Ollama API error: " + response.statusCode() + " - " + response.body());
        }
        
        // Parse the response to extract the actual content
        String responseBody = response.body();
        if (responseBody.contains("\"response\":")) {
            // Extract the response field from JSON
            int start = responseBody.indexOf("\"response\":\"") + 12;
            int end = responseBody.lastIndexOf("\"");
            if (start > 11 && end > start) {
                return responseBody.substring(start, end).replace("\\n", "\n").replace("\\\"", "\"");
            }
        }
        
        return responseBody;
    }
    
    private static void displayFinalResults(String ingredients, String analysis, String recommendations) {
        System.out.println("📊 FINAL ANALYSIS RESULTS");
        System.out.println("=========================");
        System.out.println();
        
        System.out.println("🧪 Ingredients Found:");
        System.out.println(ingredients);
        System.out.println();
        
        System.out.println("🔍 AI Analysis:");
        System.out.println(analysis);
        System.out.println();
        
        System.out.println("💡 Recommendations:");
        System.out.println(recommendations);
        System.out.println();
        
        System.out.println("✅ Analysis complete! The Ollama LLM has provided a comprehensive safety and eco-friendliness assessment.");
    }
}