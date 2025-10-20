import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.*;

/**
 * MommyShops Image Analysis Test
 * Simulates the analysis of test3.jpg image
 */
public class ImageAnalysisTest {
    
    public static void main(String[] args) {
        System.out.println("🧪 MommyShops Image Analysis Test");
        System.out.println("=================================");
        System.out.println();
        
        // Simulate the image analysis process
        simulateImageAnalysis();
    }
    
    private static void simulateImageAnalysis() {
        String imagePath = "/Users/arielsanroj/downloads/test3.jpg";
        File imageFile = new File(imagePath);
        
        System.out.println("📁 Image File: " + imageFile.getName());
        System.out.println("📏 File Size: " + (imageFile.length() / 1024) + " KB");
        System.out.println("✅ Image exists: " + imageFile.exists());
        System.out.println();
        
        // Simulate OCR processing
        System.out.println("🔍 Step 1: OCR Processing");
        System.out.println("------------------------");
        String extractedText = simulateOCR(imageFile);
        System.out.println("Extracted text: " + extractedText);
        System.out.println();
        
        // Simulate ingredient extraction
        System.out.println("🧪 Step 2: Ingredient Extraction");
        System.out.println("--------------------------------");
        List<String> ingredients = extractIngredients(extractedText);
        System.out.println("Found ingredients:");
        ingredients.forEach(ingredient -> System.out.println("  • " + ingredient));
        System.out.println();
        
        // Simulate AI analysis
        System.out.println("🤖 Step 3: AI Safety Analysis");
        System.out.println("-----------------------------");
        Map<String, IngredientAnalysis> analyses = analyzeIngredients(ingredients);
        analyses.forEach((ingredient, analysis) -> {
            System.out.println(ingredient + ":");
            System.out.println("  Safety Score: " + analysis.safetyScore + "/100");
            System.out.println("  Eco Score: " + analysis.ecoScore + "/100");
            System.out.println("  Risk Level: " + analysis.riskLevel);
            System.out.println("  Concerns: " + String.join(", ", analysis.concerns));
            System.out.println();
        });
        
        // Generate final recommendation
        System.out.println("📊 Step 4: Final Recommendation");
        System.out.println("-------------------------------");
        generateFinalRecommendation(analyses);
    }
    
    private static String simulateOCR(File imageFile) {
        // This would normally use Ollama's vision model
        // For simulation, we'll return a typical shampoo ingredient list
        return "WATER, SODIUM LAURYL SULFATE, COCAMIDOPROPYL BETAINE, GLYCERIN, " +
               "FRAGRANCE, METHYLPARABEN, PROPYLPARABEN, SODIUM CHLORIDE, " +
               "CITRIC ACID, SODIUM HYDROXIDE, TETRASODIUM EDTA";
    }
    
    private static List<String> extractIngredients(String text) {
        return Arrays.asList(text.split(",\\s*"));
    }
    
    private static Map<String, IngredientAnalysis> analyzeIngredients(List<String> ingredients) {
        Map<String, IngredientAnalysis> analyses = new HashMap<>();
        
        for (String ingredient : ingredients) {
            IngredientAnalysis analysis = new IngredientAnalysis();
            analysis.ingredient = ingredient.trim();
            
            // Simulate AI analysis based on ingredient type
            switch (ingredient.toUpperCase()) {
                case "SODIUM LAURYL SULFATE":
                    analysis.safetyScore = 45;
                    analysis.ecoScore = 30;
                    analysis.riskLevel = "HIGH";
                    analysis.concerns = Arrays.asList("Skin irritant", "Eye irritant", "Not eco-friendly");
                    break;
                case "METHYLPARABEN":
                case "PROPYLPARABEN":
                    analysis.safetyScore = 60;
                    analysis.ecoScore = 40;
                    analysis.riskLevel = "MODERATE";
                    analysis.concerns = Arrays.asList("Potential hormone disruptor", "Allergen risk");
                    break;
                case "FRAGRANCE":
                    analysis.safetyScore = 50;
                    analysis.ecoScore = 25;
                    analysis.riskLevel = "MODERATE";
                    analysis.concerns = Arrays.asList("Allergen potential", "Unknown ingredients", "Not biodegradable");
                    break;
                case "WATER":
                    analysis.safetyScore = 95;
                    analysis.ecoScore = 90;
                    analysis.riskLevel = "LOW";
                    analysis.concerns = Arrays.asList();
                    break;
                case "GLYCERIN":
                    analysis.safetyScore = 85;
                    analysis.ecoScore = 80;
                    analysis.riskLevel = "LOW";
                    analysis.concerns = Arrays.asList();
                    break;
                default:
                    analysis.safetyScore = 70;
                    analysis.ecoScore = 60;
                    analysis.riskLevel = "LOW";
                    analysis.concerns = Arrays.asList();
            }
            
            analyses.put(ingredient.trim(), analysis);
        }
        
        return analyses;
    }
    
    private static void generateFinalRecommendation(Map<String, IngredientAnalysis> analyses) {
        // Calculate overall scores
        double avgSafety = analyses.values().stream()
            .mapToInt(a -> a.safetyScore)
            .average()
            .orElse(0.0);
        
        double avgEco = analyses.values().stream()
            .mapToInt(a -> a.ecoScore)
            .average()
            .orElse(0.0);
        
        // Count high-risk ingredients
        long highRiskCount = analyses.values().stream()
            .filter(a -> a.riskLevel.equals("HIGH"))
            .count();
        
        long moderateRiskCount = analyses.values().stream()
            .filter(a -> a.riskLevel.equals("MODERATE"))
            .count();
        
        // Generate recommendation
        String recommendation;
        if (avgSafety >= 80 && avgEco >= 70) {
            recommendation = "✅ RECOMMENDED";
        } else if (avgSafety >= 60 && avgEco >= 50) {
            recommendation = "⚠️ CAUTION";
        } else {
            recommendation = "❌ AVOID";
        }
        
        System.out.println("Overall Safety Score: " + String.format("%.0f", avgSafety) + "/100");
        System.out.println("Overall Eco Score: " + String.format("%.0f", avgEco) + "/100");
        System.out.println("Recommendation: " + recommendation);
        System.out.println();
        
        System.out.println("🚨 Safety Concerns:");
        if (highRiskCount > 0) {
            System.out.println("  • " + highRiskCount + " high-risk ingredients found");
        }
        if (moderateRiskCount > 0) {
            System.out.println("  • " + moderateRiskCount + " moderate-risk ingredients found");
        }
        System.out.println();
        
        System.out.println("💡 Recommendations:");
        System.out.println("  • Look for SLS-free alternatives");
        System.out.println("  • Choose paraben-free products");
        System.out.println("  • Select fragrance-free or naturally scented options");
        System.out.println("  • Consider sulfate-free shampoos for sensitive skin");
        System.out.println();
        
        System.out.println("🌱 Eco-Friendly Alternatives:");
        System.out.println("  • Shampoo bars with natural surfactants");
        System.out.println("  • Products with biodegradable ingredients");
        System.out.println("  • Brands with sustainable packaging");
        System.out.println("  • Organic and natural ingredient formulations");
    }
    
    static class IngredientAnalysis {
        String ingredient;
        int safetyScore;
        int ecoScore;
        String riskLevel;
        List<String> concerns;
    }
}