package com.mommyshops.service;

import com.mommyshops.analysis.domain.ProductAnalysis;
import com.mommyshops.analysis.domain.ProductAnalysisRequest;
import com.mommyshops.analysis.domain.ProductAnalysisResponse;
import com.mommyshops.analysis.domain.IngredientAnalysis;
import com.mommyshops.integration.client.PythonBackendClient;
import com.mommyshops.repository.ProductAnalysisRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

/**
 * Unit tests for ProductAnalysisService
 */
@ExtendWith(MockitoExtension.class)
public class ProductAnalysisServiceTest {

    @Mock
    private ProductAnalysisRepository productAnalysisRepository;

    @Mock
    private PythonBackendClient pythonBackendClient;

    @InjectMocks
    private ProductAnalysisService productAnalysisService;

    private ProductAnalysisRequest testRequest;
    private ProductAnalysisResponse testResponse;
    private ProductAnalysis testAnalysis;

    @BeforeEach
    void setUp() {
        // Setup test request
        testRequest = new ProductAnalysisRequest();
        testRequest.setText("Aqua, Glycerin, Hyaluronic Acid, Niacinamide");
        testRequest.setUserNeed("sensitive skin");

        // Setup test response
        testResponse = new ProductAnalysisResponse();
        testResponse.setSuccess(true);
        testResponse.setProductName("Test Product");
        testResponse.setAvgEcoScore(85.0);
        testResponse.setSuitability("good");
        testResponse.setRecommendations("Product is suitable for sensitive skin");

        // Setup test analysis
        testAnalysis = new ProductAnalysis();
        testAnalysis.setId(UUID.randomUUID().toString());
        testAnalysis.setUserId("test-user-123");
        testAnalysis.setProductName("Test Product");
        testAnalysis.setIngredients(List.of("Aqua", "Glycerin", "Hyaluronic Acid", "Niacinamide"));
        testAnalysis.setAnalysisResult("{\"suitability\":\"good\",\"eco_score\":85.0}");
    }

    @Test
    void testAnalyzeProductSuccess() {
        // Given
        when(pythonBackendClient.analyzeText(anyString(), anyString()))
                .thenReturn(Mono.just(testResponse));
        when(productAnalysisRepository.save(any(ProductAnalysis.class)))
                .thenReturn(testAnalysis);

        // When
        Mono<ProductAnalysisResponse> result = productAnalysisService.analyzeProduct(testRequest, "test-user-123");

        // Then
        StepVerifier.create(result)
                .assertNext(response -> {
                    assertTrue(response.isSuccess());
                    assertEquals("Test Product", response.getProductName());
                    assertEquals(85.0, response.getAvgEcoScore());
                    assertEquals("good", response.getSuitability());
                })
                .verifyComplete();

        verify(pythonBackendClient).analyzeText(testRequest.getText(), testRequest.getUserNeed());
        verify(productAnalysisRepository).save(any(ProductAnalysis.class));
    }

    @Test
    void testAnalyzeProductFailure() {
        // Given
        when(pythonBackendClient.analyzeText(anyString(), anyString()))
                .thenReturn(Mono.error(new RuntimeException("Python backend error")));

        // When
        Mono<ProductAnalysisResponse> result = productAnalysisService.analyzeProduct(testRequest, "test-user-123");

        // Then
        StepVerifier.create(result)
                .assertNext(response -> {
                    assertFalse(response.isSuccess());
                    assertNotNull(response.getError());
                    assertTrue(response.getError().contains("Python backend error"));
                })
                .verifyComplete();

        verify(pythonBackendClient).analyzeText(testRequest.getText(), testRequest.getUserNeed());
        verify(productAnalysisRepository, never()).save(any(ProductAnalysis.class));
    }

    @Test
    void testAnalyzeProductWithEmptyText() {
        // Given
        testRequest.setText("");
        when(pythonBackendClient.analyzeText(anyString(), anyString()))
                .thenReturn(Mono.just(testResponse));

        // When
        Mono<ProductAnalysisResponse> result = productAnalysisService.analyzeProduct(testRequest, "test-user-123");

        // Then
        StepVerifier.create(result)
                .assertNext(response -> {
                    assertFalse(response.isSuccess());
                    assertNotNull(response.getError());
                })
                .verifyComplete();
    }

    @Test
    void testAnalyzeProductWithNullText() {
        // Given
        testRequest.setText(null);
        when(pythonBackendClient.analyzeText(anyString(), anyString()))
                .thenReturn(Mono.just(testResponse));

        // When
        Mono<ProductAnalysisResponse> result = productAnalysisService.analyzeProduct(testRequest, "test-user-123");

        // Then
        StepVerifier.create(result)
                .assertNext(response -> {
                    assertFalse(response.isSuccess());
                    assertNotNull(response.getError());
                })
                .verifyComplete();
    }

    @Test
    void testAnalyzeProductWithLongText() {
        // Given
        StringBuilder longText = new StringBuilder();
        for (int i = 0; i < 1000; i++) {
            longText.append("Aqua, Glycerin, ");
        }
        testRequest.setText(longText.toString());
        when(pythonBackendClient.analyzeText(anyString(), anyString()))
                .thenReturn(Mono.just(testResponse));

        // When
        Mono<ProductAnalysisResponse> result = productAnalysisService.analyzeProduct(testRequest, "test-user-123");

        // Then
        StepVerifier.create(result)
                .assertNext(response -> {
                    assertTrue(response.isSuccess());
                    assertEquals("Test Product", response.getProductName());
                })
                .verifyComplete();
    }

    @Test
    void testAnalyzeProductWithSpecialCharacters() {
        // Given
        testRequest.setText("Aqua, Glycerin, Hyaluronic Acid (1%), Niacinamide 4%");
        when(pythonBackendClient.analyzeText(anyString(), anyString()))
                .thenReturn(Mono.just(testResponse));

        // When
        Mono<ProductAnalysisResponse> result = productAnalysisService.analyzeProduct(testRequest, "test-user-123");

        // Then
        StepVerifier.create(result)
                .assertNext(response -> {
                    assertTrue(response.isSuccess());
                    assertEquals("Test Product", response.getProductName());
                })
                .verifyComplete();
    }

    @Test
    void testAnalyzeProductWithUnicodeCharacters() {
        // Given
        testRequest.setText("Aqua, Glicerina, Ácido Hialurónico, Niacinamida");
        when(pythonBackendClient.analyzeText(anyString(), anyString()))
                .thenReturn(Mono.just(testResponse));

        // When
        Mono<ProductAnalysisResponse> result = productAnalysisService.analyzeProduct(testRequest, "test-user-123");

        // Then
        StepVerifier.create(result)
                .assertNext(response -> {
                    assertTrue(response.isSuccess());
                    assertEquals("Test Product", response.getProductName());
                })
                .verifyComplete();
    }

    @Test
    void testAnalyzeProductWithDifferentUserNeeds() {
        // Given
        String[] userNeeds = {"sensitive skin", "acne-prone", "anti-aging", "general safety"};
        when(pythonBackendClient.analyzeText(anyString(), anyString()))
                .thenReturn(Mono.just(testResponse));

        for (String userNeed : userNeeds) {
            testRequest.setUserNeed(userNeed);

            // When
            Mono<ProductAnalysisResponse> result = productAnalysisService.analyzeProduct(testRequest, "test-user-123");

            // Then
            StepVerifier.create(result)
                    .assertNext(response -> {
                        assertTrue(response.isSuccess());
                        assertEquals("Test Product", response.getProductName());
                        assertEquals("good", response.getSuitability());
                    })
                    .verifyComplete();
        }
    }

    @Test
    void testAnalyzeProductRepositoryError() {
        // Given
        when(pythonBackendClient.analyzeText(anyString(), anyString()))
                .thenReturn(Mono.just(testResponse));
        when(productAnalysisRepository.save(any(ProductAnalysis.class)))
                .thenThrow(new RuntimeException("Database error"));

        // When
        Mono<ProductAnalysisResponse> result = productAnalysisService.analyzeProduct(testRequest, "test-user-123");

        // Then
        StepVerifier.create(result)
                .assertNext(response -> {
                    assertTrue(response.isSuccess()); // Python analysis succeeded
                    assertEquals("Test Product", response.getProductName());
                })
                .verifyComplete();

        verify(pythonBackendClient).analyzeText(testRequest.getText(), testRequest.getUserNeed());
        verify(productAnalysisRepository).save(any(ProductAnalysis.class));
    }

    @Test
    void testAnalyzeProductWithNullUserNeed() {
        // Given
        testRequest.setUserNeed(null);
        when(pythonBackendClient.analyzeText(anyString(), anyString()))
                .thenReturn(Mono.just(testResponse));

        // When
        Mono<ProductAnalysisResponse> result = productAnalysisService.analyzeProduct(testRequest, "test-user-123");

        // Then
        StepVerifier.create(result)
                .assertNext(response -> {
                    assertTrue(response.isSuccess());
                    assertEquals("Test Product", response.getProductName());
                })
                .verifyComplete();
    }

    @Test
    void testAnalyzeProductWithEmptyUserNeed() {
        // Given
        testRequest.setUserNeed("");
        when(pythonBackendClient.analyzeText(anyString(), anyString()))
                .thenReturn(Mono.just(testResponse));

        // When
        Mono<ProductAnalysisResponse> result = productAnalysisService.analyzeProduct(testRequest, "test-user-123");

        // Then
        StepVerifier.create(result)
                .assertNext(response -> {
                    assertTrue(response.isSuccess());
                    assertEquals("Test Product", response.getProductName());
                })
                .verifyComplete();
    }

    @Test
    void testAnalyzeProductResponseStructure() {
        // Given
        when(pythonBackendClient.analyzeText(anyString(), anyString()))
                .thenReturn(Mono.just(testResponse));

        // When
        Mono<ProductAnalysisResponse> result = productAnalysisService.analyzeProduct(testRequest, "test-user-123");

        // Then
        StepVerifier.create(result)
                .assertNext(response -> {
                    // Check required fields
                    assertNotNull(response.isSuccess());
                    assertNotNull(response.getProductName());
                    assertNotNull(response.getAvgEcoScore());
                    assertNotNull(response.getSuitability());
                    assertNotNull(response.getRecommendations());
                    
                    // Check data types
                    assertTrue(response.getAvgEcoScore() >= 0 && response.getAvgEcoScore() <= 100);
                    assertTrue(response.getSuitability().length() > 0);
                    assertTrue(response.getRecommendations().length() > 0);
                })
                .verifyComplete();
    }
}
