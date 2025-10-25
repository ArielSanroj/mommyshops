package com.mommyshops.analysis.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpEntity;
import org.springframework.http.ResponseEntity;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.*;
import java.util.regex.Pattern;
import java.util.regex.Matcher;

/**
 * Real web scraping service for ingredient extraction from URLs
 * Based on Python web scraping functionality
 */
@Service
public class WebScrapingService {
    
    private final RestTemplate restTemplate;
    
    // Common ingredient list patterns
    private static final List<Pattern> INGREDIENT_PATTERNS = List.of(
        Pattern.compile("(?i)(?:ingredients?|ingredientes?|componentes?|composition)\\s*:?\\s*([^\\n]+(?:\\n[^\\n]+)*)", Pattern.MULTILINE),
        Pattern.compile("(?i)(?:active\\s+ingredients?|ingredientes?\\s+activos?)\\s*:?\\s*([^\\n]+(?:\\n[^\\n]+)*)", Pattern.MULTILINE),
        Pattern.compile("(?i)(?:inactive\\s+ingredients?|ingredientes?\\s+inactivos?)\\s*:?\\s*([^\\n]+(?:\\n[^\\n]+)*)", Pattern.MULTILINE)
    );
    
    // Common cosmetic ingredient keywords
    private static final Set<String> COSMETIC_KEYWORDS = Set.of(
        "aqua", "water", "glycerin", "dimethicone", "cyclomethicone", "squalane",
        "hyaluronic acid", "niacinamide", "retinol", "vitamin c", "ascorbic acid",
        "salicylic acid", "glycolic acid", "lactic acid", "alpha hydroxy acid",
        "beta hydroxy acid", "peptides", "ceramides", "sunscreen", "spf",
        "octocrylene", "avobenzone", "zinc oxide", "titanium dioxide",
        "parabens", "sulfates", "fragrance", "parfum", "alcohol", "ethanol",
        "propylene glycol", "butylene glycol", "caprylic triglyceride",
        "cetearyl alcohol", "cetyl alcohol", "stearyl alcohol", "behenyl alcohol",
        "sodium lauryl sulfate", "sodium laureth sulfate", "cocamidopropyl betaine",
        "polysorbate", "sorbitan", "lecithin", "xanthan gum", "carbomer",
        "sodium hyaluronate", "panthenol", "allantoin", "bisabolol", "chamomile",
        "green tea", "aloe vera", "jojoba oil", "argan oil", "coconut oil",
        "shea butter", "cocoa butter", "beeswax", "lanolin", "squalene"
    );
    
    // Common non-ingredient patterns to filter out
    private static final List<Pattern> FILTER_PATTERNS = List.of(
        Pattern.compile("(?i)(?:directions?|instrucciones?|how to use|como usar)"),
        Pattern.compile("(?i)(?:warnings?|advertencias?|precautions?|precauciones?)"),
        Pattern.compile("(?i)(?:storage|almacenamiento|keep|mantener)"),
        Pattern.compile("(?i)(?:expires?|expira|use by|usar antes de)"),
        Pattern.compile("(?i)(?:net weight|peso neto|volume|volumen)"),
        Pattern.compile("(?i)(?:made in|hecho en|manufactured|fabricado)"),
        Pattern.compile("(?i)(?:contact|contacto|website|sitio web)"),
        Pattern.compile("(?i)(?:follow us|síguenos|social media|redes sociales)")
    );
    
    @Autowired
    public WebScrapingService(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }
    
    /**
     * Extract ingredients from a product URL
     */
    public String extractIngredientsFromUrl(String url) {
        try {
            // Validate URL
            if (!isValidUrl(url)) {
                return "INVALID_URL";
            }
            
            // Fetch the webpage content
            String htmlContent = fetchWebpageContent(url);
            if (htmlContent == null || htmlContent.isEmpty()) {
                return "SCRAPING_ERROR";
            }
            
            // Extract ingredients from HTML content
            String ingredients = extractIngredientsFromHtml(htmlContent);
            
            if (ingredients == null || ingredients.trim().isEmpty()) {
                return "INGREDIENTS_NOT_FOUND";
            }
            
            // Clean and validate ingredients
            String cleanedIngredients = cleanIngredients(ingredients);
            
            if (cleanedIngredients.trim().isEmpty()) {
                return "INGREDIENTS_NOT_FOUND";
            }
            
            return cleanedIngredients;
            
        } catch (Exception e) {
            return "SCRAPING_ERROR";
        }
    }
    
    /**
     * Validate URL format
     */
    private boolean isValidUrl(String url) {
        try {
            return url.startsWith("http://") || url.startsWith("https://");
        } catch (Exception e) {
            return false;
        }
    }
    
    /**
     * Fetch webpage content
     */
    private String fetchWebpageContent(String url) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.set("User-Agent", "Mozilla/5.0 (compatible; MommyShopsBot/1.0; +https://mommyshops.com/bot)");
            headers.set("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8");
            headers.set("Accept-Language", "en-US,en;q=0.5,es;q=0.3");
            headers.set("Accept-Encoding", "gzip, deflate");
            headers.set("Connection", "keep-alive");
            headers.set("Upgrade-Insecure-Requests", "1");
            
            HttpEntity<String> entity = new HttpEntity<>(headers);
            ResponseEntity<String> response = restTemplate.getForEntity(url, String.class, entity);
            
            if (response.getStatusCode().is2xxSuccessful()) {
                return response.getBody();
            } else {
                return null;
            }
            
        } catch (Exception e) {
            return null;
        }
    }
    
    /**
     * Extract ingredients from HTML content
     */
    private String extractIngredientsFromHtml(String htmlContent) {
        // Remove HTML tags and normalize whitespace
        String textContent = htmlContent
            .replaceAll("<script[^>]*>.*?</script>", " ")
            .replaceAll("<style[^>]*>.*?</style>", " ")
            .replaceAll("<[^>]+>", " ")
            .replaceAll("\\s+", " ")
            .trim();
        
        // Look for ingredient patterns
        for (Pattern pattern : INGREDIENT_PATTERNS) {
            Matcher matcher = pattern.matcher(textContent);
            if (matcher.find()) {
                String ingredients = matcher.group(1).trim();
                
                // Filter out non-ingredient content
                if (!containsNonIngredientContent(ingredients)) {
                    return ingredients;
                }
            }
        }
        
        // Fallback: look for cosmetic keywords in the text
        return findIngredientsByKeywords(textContent);
    }
    
    /**
     * Check if text contains non-ingredient content
     */
    private boolean containsNonIngredientContent(String text) {
        String lowerText = text.toLowerCase();
        
        for (Pattern filterPattern : FILTER_PATTERNS) {
            if (filterPattern.matcher(lowerText).find()) {
                return true;
            }
        }
        
        // Check if text is too short (likely not ingredients)
        if (text.length() < 20) {
            return true;
        }
        
        // Check if text contains too many non-cosmetic words
        String[] words = text.toLowerCase().split("\\s+");
        long cosmeticWordCount = Arrays.stream(words)
            .mapToLong(word -> COSMETIC_KEYWORDS.contains(word) ? 1 : 0)
            .sum();
        
        return cosmeticWordCount < words.length * 0.1; // Less than 10% cosmetic words
    }
    
    /**
     * Find ingredients by looking for cosmetic keywords
     */
    private String findIngredientsByKeywords(String textContent) {
        List<String> foundIngredients = new ArrayList<>();
        String lowerText = textContent.toLowerCase();
        
        for (String keyword : COSMETIC_KEYWORDS) {
            if (lowerText.contains(keyword)) {
                // Find the context around the keyword
                int index = lowerText.indexOf(keyword);
                String context = extractContext(textContent, index, 100);
                
                if (isValidIngredientContext(context)) {
                    foundIngredients.add(keyword);
                }
            }
        }
        
        if (foundIngredients.isEmpty()) {
            return null;
        }
        
        return String.join(", ", foundIngredients);
    }
    
    /**
     * Extract context around a keyword
     */
    private String extractContext(String text, int index, int contextLength) {
        int start = Math.max(0, index - contextLength);
        int end = Math.min(text.length(), index + contextLength);
        return text.substring(start, end);
    }
    
    /**
     * Check if context looks like ingredient list
     */
    private boolean isValidIngredientContext(String context) {
        // Look for common ingredient list patterns
        return context.matches(".*[,;]\\s*\\w+.*") || // Contains commas or semicolons
               context.matches(".*\\w+\\s*[,;]\\s*\\w+.*") || // Multiple words separated by commas/semicolons
               context.matches(".*\\w+\\s+\\w+.*"); // Multiple words
    }
    
    /**
     * Clean and validate extracted ingredients
     */
    private String cleanIngredients(String ingredients) {
        // Split by common separators
        String[] ingredientArray = ingredients.split("[,;]");
        
        List<String> cleanedIngredients = new ArrayList<>();
        
        for (String ingredient : ingredientArray) {
            String cleaned = ingredient.trim()
                .replaceAll("\\s+", " ") // Normalize whitespace
                .replaceAll("[^\\w\\s\\-\\/\\(\\)]", "") // Remove special characters except common ones
                .trim();
            
            // Validate ingredient
            if (isValidIngredient(cleaned)) {
                cleanedIngredients.add(cleaned);
            }
        }
        
        // Remove duplicates while preserving order
        List<String> uniqueIngredients = new ArrayList<>();
        Set<String> seen = new HashSet<>();
        
        for (String ingredient : cleanedIngredients) {
            String lowerIngredient = ingredient.toLowerCase();
            if (!seen.contains(lowerIngredient)) {
                seen.add(lowerIngredient);
                uniqueIngredients.add(ingredient);
            }
        }
        
        return String.join(", ", uniqueIngredients);
    }
    
    /**
     * Validate if a string is a valid ingredient
     */
    private boolean isValidIngredient(String ingredient) {
        if (ingredient == null || ingredient.trim().isEmpty()) {
            return false;
        }
        
        String trimmed = ingredient.trim();
        
        // Must be at least 2 characters
        if (trimmed.length() < 2) {
            return false;
        }
        
        // Must contain at least one letter
        if (!trimmed.matches(".*[a-zA-Z].*")) {
            return false;
        }
        
        // Must not be just numbers
        if (trimmed.matches("\\d+")) {
            return false;
        }
        
        // Must not be common non-ingredient words
        String lowerIngredient = trimmed.toLowerCase();
        Set<String> nonIngredientWords = Set.of(
            "ingredients", "ingredientes", "componentes", "composition",
            "active", "inactive", "activos", "inactivos", "directions",
            "instrucciones", "warnings", "advertencias", "storage",
            "almacenamiento", "expires", "expira", "net", "weight",
            "peso", "volume", "volumen", "made", "hecho", "manufactured",
            "fabricado", "contact", "contacto", "website", "sitio",
            "follow", "síguenos", "social", "media", "redes", "sociales"
        );
        
        if (nonIngredientWords.contains(lowerIngredient)) {
            return false;
        }
        
        return true;
    }
    
    /**
     * Extract product information from URL
     */
    public Map<String, String> extractProductInfo(String url) {
        Map<String, String> productInfo = new HashMap<>();
        
        try {
            String htmlContent = fetchWebpageContent(url);
            if (htmlContent == null) {
                return productInfo;
            }
            
            // Extract title
            String title = extractTitle(htmlContent);
            if (title != null && !title.isEmpty()) {
                productInfo.put("title", title);
            }
            
            // Extract brand
            String brand = extractBrand(htmlContent);
            if (brand != null && !brand.isEmpty()) {
                productInfo.put("brand", brand);
            }
            
            // Extract product type
            String productType = extractProductType(htmlContent);
            if (productType != null && !productType.isEmpty()) {
                productInfo.put("productType", productType);
            }
            
            // Extract net content
            String netContent = extractNetContent(htmlContent);
            if (netContent != null && !netContent.isEmpty()) {
                productInfo.put("netContent", netContent);
            }
            
        } catch (Exception e) {
            // Return empty map on error
        }
        
        return productInfo;
    }
    
    /**
     * Extract product title from HTML
     */
    private String extractTitle(String htmlContent) {
        // Look for title in various places
        String[] titlePatterns = {
            "<title[^>]*>([^<]+)</title>",
            "<h1[^>]*>([^<]+)</h1>",
            "<meta[^>]*property=\"og:title\"[^>]*content=\"([^\"]+)\"",
            "<meta[^>]*name=\"title\"[^>]*content=\"([^\"]+)\""
        };
        
        for (String pattern : titlePatterns) {
            Pattern compiledPattern = Pattern.compile(pattern, Pattern.CASE_INSENSITIVE);
            Matcher matcher = compiledPattern.matcher(htmlContent);
            if (matcher.find()) {
                String title = matcher.group(1).trim();
                if (!title.isEmpty() && title.length() < 200) {
                    return title;
                }
            }
        }
        
        return null;
    }
    
    /**
     * Extract brand from HTML
     */
    private String extractBrand(String htmlContent) {
        // Look for brand in various places
        String[] brandPatterns = {
            "<meta[^>]*property=\"og:brand\"[^>]*content=\"([^\"]+)\"",
            "<meta[^>]*name=\"brand\"[^>]*content=\"([^\"]+)\"",
            "<span[^>]*class=\"[^\"]*brand[^\"]*\"[^>]*>([^<]+)</span>",
            "<div[^>]*class=\"[^\"]*brand[^\"]*\"[^>]*>([^<]+)</div>"
        };
        
        for (String pattern : brandPatterns) {
            Pattern compiledPattern = Pattern.compile(pattern, Pattern.CASE_INSENSITIVE);
            Matcher matcher = compiledPattern.matcher(htmlContent);
            if (matcher.find()) {
                String brand = matcher.group(1).trim();
                if (!brand.isEmpty() && brand.length() < 100) {
                    return brand;
                }
            }
        }
        
        return null;
    }
    
    /**
     * Extract product type from HTML
     */
    private String extractProductType(String htmlContent) {
        // Look for product type in various places
        String[] typePatterns = {
            "<meta[^>]*property=\"og:type\"[^>]*content=\"([^\"]+)\"",
            "<meta[^>]*name=\"product:type\"[^>]*content=\"([^\"]+)\"",
            "<span[^>]*class=\"[^\"]*type[^\"]*\"[^>]*>([^<]+)</span>",
            "<div[^>]*class=\"[^\"]*type[^\"]*\"[^>]*>([^<]+)</div>"
        };
        
        for (String pattern : typePatterns) {
            Pattern compiledPattern = Pattern.compile(pattern, Pattern.CASE_INSENSITIVE);
            Matcher matcher = compiledPattern.matcher(htmlContent);
            if (matcher.find()) {
                String type = matcher.group(1).trim();
                if (!type.isEmpty() && type.length() < 100) {
                    return type;
                }
            }
        }
        
        return null;
    }
    
    /**
     * Extract net content from HTML
     */
    private String extractNetContent(String htmlContent) {
        // Look for net content in various places
        String[] contentPatterns = {
            "<meta[^>]*name=\"product:size\"[^>]*content=\"([^\"]+)\"",
            "<span[^>]*class=\"[^\"]*size[^\"]*\"[^>]*>([^<]+)</span>",
            "<div[^>]*class=\"[^\"]*size[^\"]*\"[^>]*>([^<]+)</div>",
            "\\b(\\d+\\s*(?:ml|g|oz|fl\\s*oz|grams?|milliliters?|ounces?))\\b"
        };
        
        for (String pattern : contentPatterns) {
            Pattern compiledPattern = Pattern.compile(pattern, Pattern.CASE_INSENSITIVE);
            Matcher matcher = compiledPattern.matcher(htmlContent);
            if (matcher.find()) {
                String content = matcher.group(1).trim();
                if (!content.isEmpty() && content.length() < 50) {
                    return content;
                }
            }
        }
        
        return null;
    }
}