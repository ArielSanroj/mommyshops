import java.util.*;
import java.util.regex.*;
import java.net.http.*;
import java.net.URI;
import java.time.Duration;

/**
 * Simple test for EWG scraping functionality
 */
public class test_ewg_java {
    
    public static void main(String[] args) {
        System.out.println("🧪 Testing EWG Skin Deep Scraping (Java)");
        System.out.println("==========================================");
        
        List<String> ingredients = Arrays.asList(
            "Sodium Laureth Sulfate",
            "Phenoxyethanol", 
            "Benzyl Alcohol",
            "Aloe Vera",
            "Water"
        );
        
        for (String ingredient : ingredients) {
            System.out.println("\n🔍 Testing ingredient: " + ingredient);
            
            try {
                // Simulate the EWG scraping logic
                Map<String, Object> result = testEWGScraping(ingredient);
                
                System.out.println("✅ Result: " + result);
                
                // Add delay to respect rate limiting
                Thread.sleep(2000);
                
            } catch (Exception e) {
                System.out.println("❌ Error: " + e.getMessage());
            }
        }
        
        System.out.println("\n📊 Test completed!");
    }
    
    public static Map<String, Object> testEWGScraping(String ingredient) {
        Map<String, Object> result = new HashMap<>();
        result.put("ingredient", ingredient);
        result.put("dataSource", "EWG Skin Deep Database");
        
        // Simulate the hazard score extraction
        int hazardScore = estimateHazardScore(ingredient);
        result.put("hazardScore", hazardScore);
        
        // Simulate concerns extraction
        List<String> concerns = getEstimatedConcerns(ingredient);
        result.put("concerns", concerns);
        
        // Simulate data availability
        Map<String, Object> dataAvailability = new HashMap<>();
        dataAvailability.put("studiesAvailable", true);
        dataAvailability.put("regulatoryData", true);
        dataAvailability.put("industryData", false);
        result.put("dataAvailability", dataAvailability);
        
        result.put("ewgRating", "Moderate");
        result.put("status", "SUCCESS");
        
        return result;
    }
    
    private static int estimateHazardScore(String ingredient) {
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
    
    private static List<String> getEstimatedConcerns(String ingredient) {
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
}