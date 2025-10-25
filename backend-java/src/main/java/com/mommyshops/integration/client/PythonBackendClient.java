package com.mommyshops.integration.client;

import com.mommyshops.analysis.domain.IngredientAnalysis;
import com.mommyshops.analysis.domain.ProductAnalysis;
import com.mommyshops.analysis.domain.ProductAnalysisRequest;
import com.mommyshops.analysis.domain.ProductAnalysisResponse;
import com.mommyshops.config.WebClientConfig;
import com.mommyshops.integration.domain.ExternalSourceLog;
import com.mommyshops.integration.service.ExternalApiService;
import com.mommyshops.logging.ProductionLoggingService;
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import io.github.resilience4j.retry.annotation.Retry;
import io.github.resilience4j.timelimiter.annotation.TimeLimiter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Mono;
import org.springframework.core.ParameterizedTypeReference;

import java.time.Duration;
import java.util.List;
import java.util.Map;

/**
 * Client for communicating with Python FastAPI backend
 * Handles OCR, external API aggregation, and AI analysis
 */
@Service
public class PythonBackendClient {

    private static final Logger logger = LoggerFactory.getLogger(PythonBackendClient.class);
    
    @Value("${python.backend.url:http://localhost:8000}")
    private String pythonBackendUrl;
    
    @Value("${python.backend.timeout:30000}")
    private int timeoutMs;
    
    private final WebClient webClient;
    private final ExternalApiService externalApiService;
    private final ProductionLoggingService loggingService;

    @Autowired
    public PythonBackendClient(WebClient.Builder webClientBuilder, 
                              ExternalApiService externalApiService,
                              ProductionLoggingService loggingService) {
        this.webClient = webClientBuilder
                .baseUrl(pythonBackendUrl)
                .codecs(configurer -> configurer.defaultCodecs().maxInMemorySize(10 * 1024 * 1024)) // 10MB
                .build();
        this.externalApiService = externalApiService;
        this.loggingService = loggingService;
    }

    /**
     * Analyze image using Python OCR and AI services
     * 
     * @param imageFile The image file to analyze
     * @param userNeed User's skin type or concern
     * @return ProductAnalysisResponse with ingredient analysis
     */
    @CircuitBreaker(name = "python-backend", fallbackMethod = "analyzeImageFallback")
    @Retry(name = "python-backend")
    @TimeLimiter(name = "python-backend")
    public Mono<ProductAnalysisResponse> analyzeImage(MultipartFile imageFile, String userNeed) {
        logger.info("Sending image analysis request to Python backend for user need: {}", userNeed);
        
        MultipartBodyBuilder builder = new MultipartBodyBuilder();
        builder.part("file", imageFile.getResource());
        builder.part("user_need", userNeed);
        
        return webClient
                .post()
                .uri("/analyze-image")
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(BodyInserters.fromMultipartData(builder.build()))
                .retrieve()
                .bodyToMono(ProductAnalysisResponse.class)
                .timeout(Duration.ofMillis(timeoutMs))
                .doOnSuccess(response -> {
                    logger.info("Successfully received image analysis from Python backend");
                    logExternalApiCall("python-backend", "analyze-image", "success", null);
                })
                .doOnError(error -> {
                    logger.error("Error calling Python backend for image analysis: {}", error.getMessage());
                    logExternalApiCall("python-backend", "analyze-image", "error", error.getMessage());
                });
    }

    /**
     * Analyze text containing ingredients using Python AI services
     * 
     * @param text The text containing ingredients
     * @param userNeed User's skin type or concern
     * @return ProductAnalysisResponse with ingredient analysis
     */
    @CircuitBreaker(name = "python-backend", fallbackMethod = "analyzeTextFallback")
    @Retry(name = "python-backend")
    @TimeLimiter(name = "python-backend")
    public Mono<ProductAnalysisResponse> analyzeText(String text, String userNeed) {
        logger.info("Sending text analysis request to Python backend for user need: {}", userNeed);
        
        Map<String, String> requestBody = Map.of(
            "text", text,
            "user_need", userNeed
        );
        
        return webClient
                .post()
                .uri("/analyze-text")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(requestBody)
                .retrieve()
                .bodyToMono(ProductAnalysisResponse.class)
                .timeout(Duration.ofMillis(timeoutMs))
                .doOnSuccess(response -> {
                    logger.info("Successfully received text analysis from Python backend");
                    logExternalApiCall("python-backend", "analyze-text", "success", null);
                })
                .doOnError(error -> {
                    logger.error("Error calling Python backend for text analysis: {}", error.getMessage());
                    logExternalApiCall("python-backend", "analyze-text", "error", error.getMessage());
                });
    }

    /**
     * Get ingredient analysis using Python's external API aggregation
     * 
     * @param ingredientName The ingredient to analyze
     * @return IngredientAnalysis with safety data
     */
    @CircuitBreaker(name = "python-backend", fallbackMethod = "getIngredientAnalysisFallback")
    @Retry(name = "python-backend")
    @TimeLimiter(name = "python-backend")
    public Mono<IngredientAnalysis> getIngredientAnalysis(String ingredientName) {
        logger.info("Requesting ingredient analysis from Python backend for: {}", ingredientName);
        
        Map<String, String> requestBody = Map.of("ingredient", ingredientName);
        
        return webClient
                .post()
                .uri("/ingredients/analyze")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(requestBody)
                .retrieve()
                .bodyToMono(IngredientAnalysis.class)
                .timeout(Duration.ofMillis(timeoutMs))
                .doOnSuccess(response -> {
                    logger.info("Successfully received ingredient analysis from Python backend");
                    logExternalApiCall("python-backend", "ingredients/analyze", "success", null);
                })
                .doOnError(error -> {
                    logger.error("Error calling Python backend for ingredient analysis: {}", error.getMessage());
                    logExternalApiCall("python-backend", "ingredients/analyze", "error", error.getMessage());
                });
    }

    /**
     * Get AI-powered ingredient alternatives using Ollama
     * 
     * @param problematicIngredients List of ingredients to find alternatives for
     * @param userConditions User's skin conditions
     * @return List of alternative ingredients
     */
    @CircuitBreaker(name = "python-backend", fallbackMethod = "getAlternativesFallback")
    @Retry(name = "python-backend")
    @TimeLimiter(name = "python-backend")
    public Mono<List<String>> getAlternatives(List<String> problematicIngredients, List<String> userConditions) {
        logger.info("Requesting alternatives from Python Ollama service for: {}", problematicIngredients);
        
        Map<String, Object> requestBody = Map.of(
            "problematic_ingredients", problematicIngredients,
            "user_conditions", userConditions != null ? userConditions : List.of()
        );
        
        return webClient
                .post()
                .uri("/ollama/alternatives")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(requestBody)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<List<String>>() {})
                .timeout(Duration.ofMillis(timeoutMs))
                .doOnSuccess(response -> {
                    logger.info("Successfully received alternatives from Python Ollama service");
                    logExternalApiCall("python-backend", "ollama/alternatives", "success", null);
                })
                .doOnError(error -> {
                    logger.error("Error calling Python Ollama service for alternatives: {}", error.getMessage());
                    logExternalApiCall("python-backend", "ollama/alternatives", "error", error.getMessage());
                });
    }

    /**
     * Check Python backend health
     * 
     * @return Health status
     */
    @CircuitBreaker(name = "python-backend", fallbackMethod = "healthCheckFallback")
    @Retry(name = "python-backend")
    @TimeLimiter(name = "python-backend")
    public Mono<Map<String, Object>> healthCheck() {
        return webClient
                .get()
                .uri("/health")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                .timeout(Duration.ofMillis(5000))
                .doOnSuccess(response -> {
                    logger.info("Python backend health check successful");
                    logExternalApiCall("python-backend", "health", "success", null);
                })
                .doOnError(error -> {
                    logger.error("Python backend health check failed: {}", error.getMessage());
                    logExternalApiCall("python-backend", "health", "error", error.getMessage());
                });
    }

    // Fallback methods
    public Mono<ProductAnalysisResponse> analyzeImageFallback(MultipartFile imageFile, String userNeed, Exception ex) {
        logger.warn("Python backend unavailable for image analysis, using fallback");
        return Mono.just(ProductAnalysisResponse.builder()
                .success(false)
                .error("Python backend unavailable: " + ex.getMessage())
                .build());
    }

    public Mono<ProductAnalysisResponse> analyzeTextFallback(String text, String userNeed, Exception ex) {
        logger.warn("Python backend unavailable for text analysis, using fallback");
        return Mono.just(ProductAnalysisResponse.builder()
                .success(false)
                .error("Python backend unavailable: " + ex.getMessage())
                .build());
    }

    public Mono<IngredientAnalysis> getIngredientAnalysisFallback(String ingredientName, Exception ex) {
        logger.warn("Python backend unavailable for ingredient analysis, using fallback");
        return Mono.just(IngredientAnalysis.builder()
                .name(ingredientName)
                .riskLevel("desconocido")
                .ecoScore(50.0)
                .benefits("No disponible")
                .risksDetailed("Servicio no disponible")
                .sources("Fallback")
                .build());
    }

    public Mono<List<String>> getAlternativesFallback(List<String> problematicIngredients, List<String> userConditions, Exception ex) {
        logger.warn("Python backend unavailable for alternatives, using fallback");
        return Mono.just(List.of("Servicio no disponible"));
    }

    public Mono<Map<String, Object>> healthCheckFallback(Exception ex) {
        logger.warn("Python backend health check failed, using fallback");
        return Mono.just(Map.of(
            "status", "unhealthy",
            "error", ex.getMessage(),
            "service", "python-backend"
        ));
    }

    private void logExternalApiCall(String service, String endpoint, String status, String error) {
        try {
            ExternalSourceLog log = ExternalSourceLog.builder()
                    .id(java.util.UUID.randomUUID())
                    .sourceName(service)
                    .query(endpoint)
                    .responseSummary(error != null ? error : "Success")
                    .fetchedAt(java.time.OffsetDateTime.now())
                    .statusCode(status.equals("success") ? 200 : 500)
                    .build();
            
            loggingService.logExternalApiCall(log);
        } catch (Exception e) {
            logger.warn("Failed to log external API call: {}", e.getMessage());
        }
    }
}

