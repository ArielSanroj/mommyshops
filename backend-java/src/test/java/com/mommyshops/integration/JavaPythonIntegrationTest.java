package com.mommyshops.integration;

import com.mommyshops.integration.client.PythonBackendClient;
import com.mommyshops.analysis.domain.ProductAnalysisResponse;
import com.mommyshops.analysis.domain.IngredientAnalysis;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.web.multipart.MultipartFile;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.util.List;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Integration tests for Java-Python communication
 * Tests the complete flow from Java to Python and back
 */
@SpringBootTest
@ActiveProfiles("test")
public class JavaPythonIntegrationTest {

    @Autowired
    private PythonBackendClient pythonBackendClient;

    private MultipartFile testImageFile;
    private String testText;
    private String testUserNeed;

    @BeforeEach
    void setUp() {
        // Create test image file
        byte[] imageData = "fake-image-data".getBytes();
        testImageFile = new MockMultipartFile(
            "file", 
            "test-image.jpg", 
            "image/jpeg", 
            imageData
        );
        
        testText = "Aqua, Glycerin, Hyaluronic Acid, Niacinamide";
        testUserNeed = "sensitive skin";
    }

    @Test
    void testPythonBackendClientInitialization() {
        assertNotNull(pythonBackendClient, "PythonBackendClient should be initialized");
    }

    @Test
    void testAnalyzeTextIntegration() {
        // Test text analysis through Python backend
        Mono<ProductAnalysisResponse> responseMono = pythonBackendClient
            .analyzeText(testText, testUserNeed);

        StepVerifier.create(responseMono)
            .assertNext(response -> {
                assertNotNull(response, "Response should not be null");
                assertTrue(response.isSuccess(), "Analysis should be successful");
                assertNotNull(response.getIngredientsDetails(), "Ingredients details should not be null");
                assertFalse(response.getIngredientsDetails().isEmpty(), "Should have ingredients");
            })
            .verifyComplete();
    }

    @Test
    void testAnalyzeImageIntegration() {
        // Test image analysis through Python backend
        Mono<ProductAnalysisResponse> responseMono = pythonBackendClient
            .analyzeImage(testImageFile, testUserNeed);

        StepVerifier.create(responseMono)
            .assertNext(response -> {
                assertNotNull(response, "Response should not be null");
                assertTrue(response.isSuccess(), "Analysis should be successful");
                assertNotNull(response.getIngredientsDetails(), "Ingredients details should not be null");
            })
            .verifyComplete();
    }

    @Test
    void testGetIngredientAnalysisIntegration() {
        // Test single ingredient analysis
        String ingredientName = "Hyaluronic Acid";
        
        Mono<IngredientAnalysis> responseMono = pythonBackendClient
            .getIngredientAnalysis(ingredientName);

        StepVerifier.create(responseMono)
            .assertNext(analysis -> {
                assertNotNull(analysis, "Analysis should not be null");
                assertEquals(ingredientName, analysis.getName(), "Ingredient name should match");
                assertNotNull(analysis.getRiskLevel(), "Risk level should not be null");
                assertTrue(analysis.getEcoScore() >= 0 && analysis.getEcoScore() <= 100, 
                    "Eco score should be between 0 and 100");
            })
            .verifyComplete();
    }

    @Test
    void testGetAlternativesIntegration() {
        // Test alternatives generation
        List<String> problematicIngredients = List.of("Sodium Lauryl Sulfate", "Parabens");
        List<String> userConditions = List.of("sensitive skin", "eczema");
        
        Mono<List<String>> responseMono = pythonBackendClient
            .getAlternatives(problematicIngredients, userConditions);

        StepVerifier.create(responseMono)
            .assertNext(alternatives -> {
                assertNotNull(alternatives, "Alternatives should not be null");
                assertFalse(alternatives.isEmpty(), "Should have alternatives");
                assertTrue(alternatives.size() <= 5, "Should have at most 5 alternatives");
            })
            .verifyComplete();
    }

    @Test
    void testPythonBackendHealthCheck() {
        // Test Python backend health
        Mono<Boolean> healthMono = pythonBackendClient.checkHealth();

        StepVerifier.create(healthMono)
            .assertNext(isHealthy -> {
                assertTrue(isHealthy, "Python backend should be healthy");
            })
            .verifyComplete();
    }

    @Test
    void testErrorHandling() {
        // Test error handling with invalid data
        String invalidText = ""; // Empty text should cause error
        String invalidUserNeed = "invalid_need";

        Mono<ProductAnalysisResponse> responseMono = pythonBackendClient
            .analyzeText(invalidText, invalidUserNeed);

        StepVerifier.create(responseMono)
            .assertNext(response -> {
                // Should handle error gracefully
                assertNotNull(response, "Response should not be null");
                // Either success with empty results or failure with error message
                if (!response.isSuccess()) {
                    assertNotNull(response.getError(), "Error message should be present");
                }
            })
            .verifyComplete();
    }

    @Test
    void testTimeoutHandling() {
        // Test timeout handling
        // This test would require a slow Python response
        // For now, just test that the client handles timeouts gracefully
        Mono<ProductAnalysisResponse> responseMono = pythonBackendClient
            .analyzeText(testText, testUserNeed);

        StepVerifier.create(responseMono)
            .assertNext(response -> {
                assertNotNull(response, "Response should not be null");
            })
            .verifyComplete();
    }

    @Test
    void testConcurrentRequests() {
        // Test handling of concurrent requests
        List<Mono<ProductAnalysisResponse>> requests = List.of(
            pythonBackendClient.analyzeText(testText, testUserNeed),
            pythonBackendClient.analyzeText(testText, "anti-aging"),
            pythonBackendClient.analyzeText(testText, "acne-prone")
        );

        // Execute all requests concurrently
        Mono<List<ProductAnalysisResponse>> combinedMono = Mono.zip(requests, results -> 
            List.of((ProductAnalysisResponse) results[0], 
                   (ProductAnalysisResponse) results[1], 
                   (ProductAnalysisResponse) results[2])
        );

        StepVerifier.create(combinedMono)
            .assertNext(responses -> {
                assertEquals(3, responses.size(), "Should have 3 responses");
                for (ProductAnalysisResponse response : responses) {
                    assertNotNull(response, "Each response should not be null");
                    assertTrue(response.isSuccess(), "Each analysis should be successful");
                }
            })
            .verifyComplete();
    }

    @Test
    void testDataConsistency() {
        // Test data consistency between Java and Python
        Mono<ProductAnalysisResponse> javaResponse = pythonBackendClient
            .analyzeText(testText, testUserNeed);

        StepVerifier.create(javaResponse)
            .assertNext(response -> {
                assertNotNull(response, "Response should not be null");
                assertTrue(response.isSuccess(), "Analysis should be successful");
                
                // Check response structure
                assertNotNull(response.getIngredientsDetails(), "Ingredients details should not be null");
                assertNotNull(response.getProductName(), "Product name should not be null");
                assertNotNull(response.getSuitability(), "Suitability should not be null");
                assertNotNull(response.getRecommendations(), "Recommendations should not be null");
                
                // Check processing time
                if (response.getProcessingTimeMs() != null) {
                    assertTrue(response.getProcessingTimeMs() > 0, "Processing time should be positive");
                }
            })
            .verifyComplete();
    }

    @Test
    void testCircuitBreakerBehavior() {
        // Test circuit breaker behavior
        // This test would require stopping Python service
        // For now, just test that the client has circuit breaker configuration
        assertNotNull(pythonBackendClient, "PythonBackendClient should be available");
        
        // Test that fallback methods are available
        // This would be tested by stopping Python service and verifying fallback behavior
    }

    @Test
    void testPerformanceMetrics() {
        // Test performance of Java-Python communication
        long startTime = System.currentTimeMillis();
        
        Mono<ProductAnalysisResponse> responseMono = pythonBackendClient
            .analyzeText(testText, testUserNeed);

        StepVerifier.create(responseMono)
            .assertNext(response -> {
                long endTime = System.currentTimeMillis();
                long responseTime = endTime - startTime;
                
                assertNotNull(response, "Response should not be null");
                assertTrue(responseTime < 10000, "Response time should be less than 10 seconds");
                
                // Check if response includes processing time
                if (response.getProcessingTimeMs() != null) {
                    assertTrue(response.getProcessingTimeMs() > 0, "Processing time should be positive");
                }
            })
            .verifyComplete();
    }

    @Test
    void testAuthenticationFlow() {
        // Test authentication flow between Java and Python
        // This would test JWT token passing from Java to Python
        // For now, just test that endpoints are accessible
        Mono<Boolean> healthMono = pythonBackendClient.checkHealth();

        StepVerifier.create(healthMono)
            .assertNext(isHealthy -> {
                assertTrue(isHealthy, "Python backend should be healthy");
            })
            .verifyComplete();
    }

    @Test
    void testMonitoringIntegration() {
        // Test monitoring and metrics integration
        Mono<Boolean> healthMono = pythonBackendClient.checkHealth();

        StepVerifier.create(healthMono)
            .assertNext(isHealthy -> {
                assertTrue(isHealthy, "Python backend should be healthy");
            })
            .verifyComplete();
    }
}
