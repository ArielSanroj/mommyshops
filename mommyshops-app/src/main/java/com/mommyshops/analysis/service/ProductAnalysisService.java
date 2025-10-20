package com.mommyshops.analysis.service;

import com.mommyshops.analysis.domain.ProductAnalysis;
import com.mommyshops.auth.domain.UserAccount;
import com.mommyshops.profile.domain.UserProfile;
import com.mommyshops.ai.service.RealOllamaService;
import com.mommyshops.integration.service.ResilientExternalApiService;
import com.mommyshops.analysis.repository.ProductAnalysisRepository;
import com.mommyshops.profile.repository.UserProfileRepository;
import com.mommyshops.recommendation.service.RecommendationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

@Service
@Transactional
public class ProductAnalysisService {
    
    private final RealOllamaService ollamaService;
    private final ResilientExternalApiService externalApiService;
    private final OCRService ocrService;
    private final WebScrapingService webScrapingService;
    private final EnhancedOCRService enhancedOCRService;
    private final ProductAnalysisRepository analysisRepository;
    private final UserProfileRepository userProfileRepository;
    
    @Autowired
    public ProductAnalysisService(RealOllamaService ollamaService,
                                 ResilientExternalApiService externalApiService,
                                 OCRService ocrService,
                                 WebScrapingService webScrapingService,
                                 EnhancedOCRService enhancedOCRService,
                                 ProductAnalysisRepository analysisRepository,
                                 UserProfileRepository userProfileRepository,
                                 ) {
        this.ollamaService = ollamaService;
        this.externalApiService = externalApiService;
        this.ocrService = ocrService;
        this.webScrapingService = webScrapingService;
        this.enhancedOCRService = enhancedOCRService;
        this.analysisRepository = analysisRepository;
        this.userProfileRepository = userProfileRepository;
    }
    
    public AnalysisResult analyzeProduct(String productName, 
                                        String ingredients, 
                                        UserAccount user) {
        
        UserProfile profile = userProfileRepository.findByUserId(user.getId())
            .orElseThrow(() -> new IllegalStateException("Perfil de usuario no encontrado"));
        List<String> ingredientList = parseIngredients(ingredients);
        
        // Analyze each ingredient with Ollama
        List<CompletableFuture<IngredientAnalysisResult>> futures = ingredientList.stream()
            .map(ingredient -> analyzeIngredientAsync(ingredient, profile))
            .collect(Collectors.toList());
        
        // Wait for all analyses to complete
        List<IngredientAnalysisResult> results = futures.stream()
            .map(CompletableFuture::join)
            .collect(Collectors.toList());
        
        // Generate overall product analysis
        ProductAnalysisSummary summary = generateProductSummary(productName, results);
        
        // Generate substitute recommendations
        List<SubstituteRecommendation> substitutes = generateSubstitutes(results, profile);
        
        // Save analysis to database
        ProductAnalysis analysis = saveAnalysis(user.getId(), productName, ingredients, summary);
        
        return new AnalysisResult(analysis, summary, substitutes, results);
    }
    
    public AnalysisResult analyzeProductFromImage(String productName, 
                                                 byte[] imageData, 
                                                 UserAccount user) {
        
        Optional<UserProfile> profileOpt = userProfileRepository.findByUserId(user.getId());
        if (profileOpt.isEmpty()) {
            return new AnalysisResult(
                null,
                new ProductAnalysisSummary(
                    productName,
                    "No se encontró el perfil de usuario. Por favor, completa tu perfil primero.",
                    0, 0,
                    List.of("Perfil de usuario no encontrado"),
                    "unknown",
                    0
                ),
                List.of(),
                List.of()
            );
        }
        
        UserProfile profile = profileOpt.get();
        
        // Extract ingredients from image using OCR
        String ingredientsText = ocrService.extractIngredientsFromImage(imageData);
        
        if ("INGREDIENTS_NOT_FOUND".equals(ingredientsText) || "OCR_ERROR".equals(ingredientsText)) {
            return new AnalysisResult(
                null,
                new ProductAnalysisSummary(
                    productName,
                    "No se pudieron extraer ingredientes de la imagen. Por favor, intenta con una imagen más clara o ingresa los ingredientes manualmente.",
                    0, 0,
                    List.of("No se pudieron extraer ingredientes de la imagen"),
                    "unknown",
                    0
                ),
                List.of(),
                List.of()
            );
        }
        
        // Parse ingredients from extracted text
        List<String> ingredientList = parseIngredients(ingredientsText);
        
        if (ingredientList.isEmpty()) {
            return new AnalysisResult(
                null,
                new ProductAnalysisSummary(
                    productName,
                    "No se encontraron ingredientes válidos en la imagen. Por favor, verifica que la imagen contenga una lista de ingredientes legible.",
                    0, 0,
                    List.of("No se encontraron ingredientes válidos"),
                    "unknown",
                    0
                ),
                List.of(),
                List.of()
            );
        }
        
        // Analyze each ingredient with Ollama
        List<CompletableFuture<IngredientAnalysisResult>> futures = ingredientList.stream()
            .map(ingredient -> analyzeIngredientAsync(ingredient, profile))
            .collect(Collectors.toList());
        
        // Wait for all analyses to complete
        List<IngredientAnalysisResult> results = futures.stream()
            .map(CompletableFuture::join)
            .collect(Collectors.toList());
        
        // Generate overall product analysis
        ProductAnalysisSummary summary = generateProductSummary(productName, results);
        
        // Generate substitute recommendations
        List<SubstituteRecommendation> substitutes = generateSubstitutes(results, profile);
        
        // Save analysis to database
        ProductAnalysis analysis = saveAnalysis(user.getId(), productName, ingredientsText, summary);
        
        return new AnalysisResult(analysis, summary, substitutes, results);
    }
    
    public AnalysisResult analyzeProductFromImageEnhanced(String productName, 
                                                         byte[] imageData, 
                                                         UserAccount user) {
        
        Optional<UserProfile> profileOpt = userProfileRepository.findByUserId(user.getId());
        if (profileOpt.isEmpty()) {
            return new AnalysisResult(
                null,
                new ProductAnalysisSummary(
                    productName,
                    "No se encontró el perfil de usuario. Por favor, completa tu perfil primero.",
                    0, 0,
                    List.of("Perfil de usuario no encontrado"),
                    "unknown",
                    0
                ),
                List.of(),
                List.of()
            );
        }
        
        UserProfile profile = profileOpt.get();
        
        // Use enhanced OCR analysis
        EnhancedOCRService.EnhancedOCRAnalysisResult ocrResult = enhancedOCRService.analyzeImageEnhanced(imageData);
        
        if (ocrResult.getExtractedText() == null || ocrResult.getExtractedText().isEmpty()) {
            return new AnalysisResult(
                null,
                new ProductAnalysisSummary(
                    productName,
                    "No se pudieron extraer ingredientes de la imagen. Por favor, intenta con una imagen más clara o ingresa los ingredientes manualmente.",
                    0, 0,
                    List.of("No se pudieron extraer ingredientes de la imagen"),
                    "unknown",
                    0
                ),
                List.of(),
                List.of()
            );
        }
        
        // Get ingredients from enhanced analysis
        List<String> ingredientList = ocrResult.getCosmeticInfo().getIngredients();
        
        if (ingredientList.isEmpty()) {
            // Fallback to parsing the extracted text
            ingredientList = parseIngredients(ocrResult.getExtractedText());
        }
        
        if (ingredientList.isEmpty()) {
            return new AnalysisResult(
                null,
                new ProductAnalysisSummary(
                    productName,
                    "No se encontraron ingredientes válidos en la imagen. Por favor, verifica que la imagen contenga una lista de ingredientes legible.",
                    0, 0,
                    List.of("No se encontraron ingredientes válidos"),
                    "unknown",
                    0
                ),
                List.of(),
                List.of()
            );
        }
        
        // Analyze each ingredient with Ollama
        List<CompletableFuture<IngredientAnalysisResult>> futures = ingredientList.stream()
            .map(ingredient -> analyzeIngredientAsync(ingredient, profile))
            .collect(Collectors.toList());
        
        // Wait for all analyses to complete
        List<IngredientAnalysisResult> results = futures.stream()
            .map(CompletableFuture::join)
            .collect(Collectors.toList());
        
        // Generate overall product analysis with enhanced data
        ProductAnalysisSummary summary = generateEnhancedProductSummary(productName, results, ocrResult);
        
        // Generate substitute recommendations
        List<SubstituteRecommendation> substitutes = generateSubstitutes(results, profile);
        
        // Save analysis to database with enhanced data
        ProductAnalysis analysis = saveEnhancedAnalysis(user.getId(), productName, ocrResult.getExtractedText(), summary, ocrResult);
        
        return new AnalysisResult(analysis, summary, substitutes, results);
    }
    
    public AnalysisResult analyzeProductFromUrl(String productUrl, UserAccount user) {
        try {
            // 1. Extract ingredients from URL using web scraping
            String extractedIngredients = webScrapingService.extractIngredientsFromUrl(productUrl);
            
            if ("SCRAPING_ERROR".equals(extractedIngredients) || "INGREDIENTS_NOT_FOUND".equals(extractedIngredients)) {
                return new AnalysisResult(
                    null,
                    new ProductAnalysisSummary(
                        "Product from URL",
                        "Error extracting ingredients from URL: " + extractedIngredients,
                        0, 0,
                        List.of("Error extracting ingredients from URL"),
                        "unknown",
                        0
                    ),
                    List.of(),
                    List.of()
                );
            }
            
            // 2. Run the same analysis pipeline as manual input
            return analyzeProduct("Product from URL", extractedIngredients, user);
            
        } catch (Exception e) {
            return new AnalysisResult(
                null,
                new ProductAnalysisSummary(
                    "Product from URL",
                    "Error analyzing product from URL: " + e.getMessage(),
                    0, 0,
                    List.of("Error analyzing product from URL"),
                    "unknown",
                    0
                ),
                List.of(),
                List.of()
            );
        }
    }
    
    public List<ProductAnalysis> getUserAnalysisHistory(UUID userId) {
        return analysisRepository.findByUserIdOrderByAnalyzedAtDesc(userId);
    }
    
    private CompletableFuture<IngredientAnalysisResult> analyzeIngredientAsync(String ingredient, UserProfile profile) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                // Get comprehensive data from all external APIs with resilience
                Map<String, Object> comprehensiveData = externalApiService.getComprehensiveIngredientData(ingredient).get(30, TimeUnit.SECONDS);
                
                // Extract individual API data
                Map<String, Object> fdaData = (Map<String, Object>) comprehensiveData.get("fda");
                Map<String, Object> pubchemData = (Map<String, Object>) comprehensiveData.get("pubchem");
                Map<String, Object> ewgData = (Map<String, Object>) comprehensiveData.get("ewg");
                
                // Get AI analysis from Ollama
                RealOllamaService.IngredientAnalysis aiAnalysis = ollamaService.analyzeIngredient(ingredient, profile);
                
                // Create enhanced analysis result
                IngredientAnalysisResult result = new IngredientAnalysisResult(ingredient, aiAnalysis, fdaData, pubchemData, ewgData);
                result.setComprehensiveData(comprehensiveData);
                return result;
            } catch (Exception e) {
                return new IngredientAnalysisResult(ingredient, null, Map.of(), Map.of(), Map.of());
            }
        });
    }
    
    private List<String> parseIngredients(String ingredients) {
        return Arrays.stream(ingredients.split("[,;]"))
            .map(String::trim)
            .filter(s -> !s.isEmpty())
            .collect(Collectors.toList());
    }
    
    private ProductAnalysisSummary generateProductSummary(String productName, List<IngredientAnalysisResult> results) {
        // Calculate overall scores from comprehensive data
        double avgSafetyScore = 50.0; // Default
        double avgEcoScore = 50.0; // Default
        List<String> riskFlags = new ArrayList<>();
        
        // Use comprehensive data if available
        boolean hasComprehensiveData = false;
        for (IngredientAnalysisResult result : results) {
            if (result.getComprehensiveData() != null) {
                hasComprehensiveData = true;
                Double safetyScore = (Double) result.getComprehensiveData().get("overall_safety_score");
                Double ecoScore = (Double) result.getComprehensiveData().get("overall_eco_score");
                List<String> flags = (List<String>) result.getComprehensiveData().get("risk_flags");
                
                if (safetyScore != null) {
                    avgSafetyScore = safetyScore;
                }
                if (ecoScore != null) {
                    avgEcoScore = ecoScore;
                }
                if (flags != null) {
                    riskFlags.addAll(flags);
                }
                break; // Use first comprehensive result
            }
        }
        
        // Fallback to AI analysis if no comprehensive data
        if (!hasComprehensiveData) {
            avgSafetyScore = results.stream()
                .mapToDouble(r -> r.getAiAnalysis() != null ? r.getAiAnalysis().getSafetyScore() : 50)
                .average()
                .orElse(50);
            
            avgEcoScore = results.stream()
                .mapToDouble(r -> r.getAiAnalysis() != null ? r.getAiAnalysis().getEcoFriendlinessScore() : 50)
                .average()
                .orElse(50);
            
            riskFlags = results.stream()
                .filter(r -> r.getAiAnalysis() != null)
                .flatMap(r -> r.getAiAnalysis().getHealthRisks().stream())
                .distinct()
                .collect(Collectors.toList());
        }
        
        // Determine overall recommendation
        String recommendation = avgSafetyScore >= 80 ? "recommended" : 
                              avgSafetyScore >= 60 ? "safe" : 
                              avgSafetyScore >= 40 ? "caution" : "avoid";
        
        // Generate analysis text with comprehensive information
        StringBuilder analysisText = new StringBuilder();
        analysisText.append(String.format("Análisis completo de %s:\n", productName));
        analysisText.append(String.format("Puntuación de seguridad: %.1f/100\n", avgSafetyScore));
        analysisText.append(String.format("Puntuación eco-amigable: %.1f/100\n", avgEcoScore));
        analysisText.append(String.format("Recomendación: %s\n", recommendation));
        
        if (!riskFlags.isEmpty()) {
            analysisText.append("\nBanderas de riesgo identificadas:\n");
            for (String flag : riskFlags) {
                analysisText.append("• ").append(flag).append("\n");
            }
        }
        
        // Add data source information
        analysisText.append("\nFuentes de datos: FDA, PubChem, EWG, INCI Beauty, COSING");
        
        return new ProductAnalysisSummary(
            productName,
            analysisText.toString(),
            (int) avgSafetyScore,
            (int) avgEcoScore,
            riskFlags,
            recommendation,
            (int) (avgSafetyScore + avgEcoScore) / 2
        );
    }
    
    private List<SubstituteRecommendation> generateSubstitutes(List<IngredientAnalysisResult> results, UserProfile profile) {
        // Generate substitutes using the recommendation service
        List<SubstituteRecommendation> substitutes = new ArrayList<>();
        
        for (IngredientAnalysisResult result : results) {
            if (result.getAiAnalysis() != null) {
                // Get substitutes from Ollama
                List<RealOllamaService.SubstituteRecommendation> ollamaSubstitutes = 
                    ollamaService.generateSubstitutes(result.getIngredient(), result.getAiAnalysis(), profile);
                
                // Convert to our format
                for (RealOllamaService.SubstituteRecommendation ollamaSub : ollamaSubstitutes) {
                    SubstituteRecommendation sub = new SubstituteRecommendation();
                    sub.setIngredient(ollamaSub.getIngredient());
                    sub.setSafetyScore(ollamaSub.getSafetyScore());
                    sub.setEcoFriendlinessScore(ollamaSub.getEcoFriendlinessScore());
                    sub.setBenefits(ollamaSub.getBenefits());
                    sub.setReasoning(ollamaSub.getReasoning());
                    sub.setAvailability(ollamaSub.getAvailability());
                    sub.setCost(ollamaSub.getCost());
                    sub.setConfidence(ollamaSub.getConfidence());
                    substitutes.add(sub);
                }
            }
        }
        
        return substitutes;
    }
    
    private ProductAnalysis saveAnalysis(UUID userId, String productName, String ingredients, ProductAnalysisSummary summary) {
        ProductAnalysis analysis = new ProductAnalysis();
        analysis.setId(UUID.randomUUID());
        analysis.setUserId(userId);
        analysis.setProductName(productName);
        analysis.setIngredientSource(ingredients);
        analysis.setAnalysisSummary(summary.getAnalysisText());
        analysis.setAnalyzedAt(OffsetDateTime.now());
        analysis.setConfidenceScore(summary.getConfidence());
        
        return analysisRepository.save(analysis);
    }
    
    private ProductAnalysisSummary generateEnhancedProductSummary(String productName, 
                                                                List<IngredientAnalysisResult> results, 
                                                                EnhancedOCRService.EnhancedOCRAnalysisResult ocrResult) {
        // Calculate overall scores
        double avgSafetyScore = results.stream()
            .mapToDouble(r -> r.getAiAnalysis() != null ? r.getAiAnalysis().getSafetyScore() : 0)
            .average()
            .orElse(0);
        
        double avgEcoScore = results.stream()
            .mapToDouble(r -> r.getAiAnalysis() != null ? r.getAiAnalysis().getEcoFriendlinessScore() : 0)
            .average()
            .orElse(0);
        
        // Use enhanced safety analysis if available
        if (ocrResult.getSafetyAnalysis() != null && ocrResult.getSafetyAnalysis().getOverallScore() > 0) {
            avgSafetyScore = ocrResult.getSafetyAnalysis().getOverallScore() * 10; // Convert to 0-100 scale
        }
        
        // Collect risk flags from both AI analysis and enhanced OCR
        List<String> riskFlags = new ArrayList<>();
        riskFlags.addAll(results.stream()
            .filter(r -> r.getAiAnalysis() != null)
            .flatMap(r -> r.getAiAnalysis().getHealthRisks().stream())
            .distinct()
            .collect(Collectors.toList()));
        
        if (ocrResult.getSafetyAnalysis() != null) {
            riskFlags.addAll(ocrResult.getSafetyAnalysis().getRecommendations());
        }
        
        // Determine overall recommendation
        String recommendation = avgSafetyScore >= 80 ? "recommended" : 
                              avgSafetyScore >= 60 ? "safe" : 
                              avgSafetyScore >= 40 ? "caution" : "avoid";
        
        // Generate enhanced analysis text
        StringBuilder analysisText = new StringBuilder();
        analysisText.append(String.format("Análisis mejorado de %s:\n", productName));
        analysisText.append(String.format("Puntuación de seguridad: %.1f/100\n", avgSafetyScore));
        analysisText.append(String.format("Puntuación eco-amigable: %.1f/100\n", avgEcoScore));
        analysisText.append(String.format("Recomendación: %s\n", recommendation));
        
        // Add cosmetic info if available
        if (ocrResult.getCosmeticInfo() != null) {
            if (!ocrResult.getCosmeticInfo().getBrand().isEmpty()) {
                analysisText.append(String.format("Marca: %s\n", ocrResult.getCosmeticInfo().getBrand()));
            }
            if (!ocrResult.getCosmeticInfo().getProductType().isEmpty()) {
                analysisText.append(String.format("Tipo: %s\n", ocrResult.getCosmeticInfo().getProductType()));
            }
            if (!ocrResult.getCosmeticInfo().getNetContent().isEmpty()) {
                analysisText.append(String.format("Contenido: %s\n", ocrResult.getCosmeticInfo().getNetContent()));
            }
        }
        
        // Add AI insights if available
        if (ocrResult.getAiInsights() != null && !ocrResult.getAiInsights().isEmpty()) {
            analysisText.append("\nInsights adicionales:\n").append(ocrResult.getAiInsights());
        }
        
        return new ProductAnalysisSummary(
            productName,
            analysisText.toString(),
            (int) avgSafetyScore,
            (int) avgEcoScore,
            riskFlags,
            recommendation,
            (int) (avgSafetyScore + avgEcoScore) / 2
        );
    }
    
    private ProductAnalysis saveEnhancedAnalysis(UUID userId, String productName, String ingredients, 
                                               ProductAnalysisSummary summary, 
                                               EnhancedOCRService.EnhancedOCRAnalysisResult ocrResult) {
        ProductAnalysis analysis = new ProductAnalysis();
        analysis.setId(UUID.randomUUID());
        analysis.setUserId(userId);
        analysis.setProductName(productName);
        analysis.setIngredientSource(ingredients);
        analysis.setAnalysisSummary(summary.getAnalysisText());
        analysis.setAnalyzedAt(OffsetDateTime.now());
        analysis.setConfidenceScore(summary.getConfidence());
        
        // Add enhanced data if available
        if (ocrResult.getCosmeticInfo() != null) {
            // Store additional cosmetic information
            analysis.setProductName(ocrResult.getCosmeticInfo().getProductName().isEmpty() ? 
                                  productName : ocrResult.getCosmeticInfo().getProductName());
        }
        
        return analysisRepository.save(analysis);
    }
    
    // Data classes
    public static class AnalysisResult {
        private final ProductAnalysis analysis;
        private final ProductAnalysisSummary summary;
        private final List<SubstituteRecommendation> substitutes;
        private final List<IngredientAnalysisResult> ingredientDetails;
        
        public AnalysisResult(ProductAnalysis analysis,
                              ProductAnalysisSummary summary,
                              List<SubstituteRecommendation> substitutes,
                              List<IngredientAnalysisResult> ingredientDetails) {
            this.analysis = analysis;
            this.summary = summary;
            this.substitutes = substitutes;
            this.ingredientDetails = ingredientDetails;
        }
        
        public AnalysisResult() {
            this(null, null, List.of(), List.of());
        }
        
        public ProductAnalysis getAnalysis() { return analysis; }
        public ProductAnalysisSummary getSummary() { return summary; }
        public List<SubstituteRecommendation> getSubstitutes() { return substitutes; }
        public List<IngredientAnalysisResult> getIngredientDetails() { return ingredientDetails; }
    }
    
    public static class ProductAnalysisSummary {
        private final String productName;
        private final String analysisText;
        private final int overallSafetyScore;
        private final int overallEcoScore;
        private final List<String> riskFlags;
        private final String recommendation;
        private final int confidence;
        
        public ProductAnalysisSummary(String productName, String analysisText, int overallSafetyScore, 
                                    int overallEcoScore, List<String> riskFlags, String recommendation, int confidence) {
            this.productName = productName;
            this.analysisText = analysisText;
            this.overallSafetyScore = overallSafetyScore;
            this.overallEcoScore = overallEcoScore;
            this.riskFlags = riskFlags;
            this.recommendation = recommendation;
            this.confidence = confidence;
        }
        
        public String getProductName() { return productName; }
        public String getAnalysisText() { return analysisText; }
        public int getOverallSafetyScore() { return overallSafetyScore; }
        public int getOverallEcoScore() { return overallEcoScore; }
        public List<String> getRiskFlags() { return riskFlags; }
        public String getRecommendation() { return recommendation; }
        public int getConfidence() { return confidence; }
    }
    
    public static class IngredientAnalysisResult {
        private final String ingredient;
        private final RealOllamaService.IngredientAnalysis aiAnalysis;
        private final Map<String, Object> fdaData;
        private final Map<String, Object> pubchemData;
        private final Map<String, Object> ewgData;
        private Map<String, Object> inciData;
        private Map<String, Object> cosingData;
        private Map<String, Object> comprehensiveData;
        
        public IngredientAnalysisResult(String ingredient, RealOllamaService.IngredientAnalysis aiAnalysis, 
                                      Map<String, Object> fdaData, Map<String, Object> pubchemData, Map<String, Object> ewgData) {
            this.ingredient = ingredient;
            this.aiAnalysis = aiAnalysis;
            this.fdaData = fdaData;
            this.pubchemData = pubchemData;
            this.ewgData = ewgData;
        }
        
        public String getIngredient() { return ingredient; }
        public RealOllamaService.IngredientAnalysis getAiAnalysis() { return aiAnalysis; }
        public Map<String, Object> getFdaData() { return fdaData; }
        public Map<String, Object> getPubchemData() { return pubchemData; }
        public Map<String, Object> getEwgData() { return ewgData; }
        public Map<String, Object> getInciData() { return inciData; }
        public void setInciData(Map<String, Object> inciData) { this.inciData = inciData; }
        public Map<String, Object> getCosingData() { return cosingData; }
        public void setCosingData(Map<String, Object> cosingData) { this.cosingData = cosingData; }
        public Map<String, Object> getComprehensiveData() { return comprehensiveData; }
        public void setComprehensiveData(Map<String, Object> comprehensiveData) { this.comprehensiveData = comprehensiveData; }
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