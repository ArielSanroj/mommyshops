import java.io.*;
import java.net.http.*;
import java.net.URI;
import java.nio.file.Files;
import java.util.Base64;

/**
 * MommyShops Product Analysis using Ollama API
 * Real analysis of cosmetic products using Ollama LLM
 */
public class OllamaProductAnalysis {
    
    private static final String OLLAMA_BASE_URL = "http://localhost:11434";
    private static final String MODEL_NAME = "llama3.1:8b";
    private static final String OLLAMA_API_KEY = "***REMOVED***";
    
    public static void main(String[] args) {
        System.out.println("🧪 MommyShops Real Ollama Analysis");
        System.out.println("==================================");
        System.out.println("Using Ollama API with model: " + MODEL_NAME);
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
            
            // Step 3: Analyze the product with Ollama
            System.out.println("🤖 Analyzing product with Ollama LLM...");
            String analysis = analyzeProductWithLLM(base64Image);
            System.out.println("Analysis complete!");
            System.out.println();
            
            // Step 4: Display results
            displayResults(analysis);
            
        } catch (Exception e) {
            System.err.println("❌ Error during analysis: " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    private static String encodeImageToBase64(File imageFile) throws IOException {
        byte[] imageBytes = Files.readAllBytes(imageFile.toPath());
        return Base64.getEncoder().encodeToString(imageBytes);
    }
    
    private static String analyzeProductWithLLM(String base64Image) throws Exception {
        String prompt = """
            You are a cosmetic safety expert analyzing a product image. Please analyze this cosmetic product image and provide a comprehensive safety and eco-friendliness assessment.
            
            Please provide:
            1. List of ingredients you can identify from the image
            2. Safety analysis for each ingredient (0-100 score)
            3. Eco-friendliness assessment (0-100 score)
            4. Overall recommendation (RECOMMENDED/CAUTION/AVOID)
            5. Specific concerns and risks
            6. Safer alternatives and recommendations
            
            Format your response clearly with sections and bullet points for easy reading.
            """;
        
        String requestBody = String.format("""
            {
                "model": "%s",
                "prompt": "%s",
                "images": ["%s"],
                "stream": false,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9
                }
            }
            """, MODEL_NAME, prompt, base64Image);
        
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
    
    private static void displayResults(String analysis) {
        System.out.println("📊 OLLAMA LLM ANALYSIS RESULTS");
        System.out.println("==============================");
        System.out.println();
        System.out.println(analysis);
        System.out.println();
        System.out.println("✅ Analysis complete! This is the real analysis from Ollama LLM.");
    }
}