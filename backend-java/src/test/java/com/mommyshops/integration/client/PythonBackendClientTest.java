package com.mommyshops.integration.client;

import com.mommyshops.analysis.domain.ProductAnalysisResponse;
import com.mommyshops.integration.service.ExternalApiService;
import com.mommyshops.logging.ProductionLoggingService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.util.List;
import java.util.Map;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;

/**
 * Tests for PythonBackendClient
 */
@ExtendWith(MockitoExtension.class)
class PythonBackendClientTest {

    @Mock
    private WebClient.Builder webClientBuilder;

    @Mock
    private WebClient webClient;

    @Mock
    private WebClient.RequestBodyUriSpec requestBodyUriSpec;

    @Mock
    private WebClient.RequestBodySpec requestBodySpec;

    @Mock
    private WebClient.ResponseSpec responseSpec;

    @Mock
    private ExternalApiService externalApiService;

    @Mock
    private ProductionLoggingService loggingService;

    private PythonBackendClient client;

    @BeforeEach
    void setUp() {
        when(webClientBuilder.baseUrl(anyString())).thenReturn(webClientBuilder);
        when(webClientBuilder.build()).thenReturn(webClient);
        
        client = new PythonBackendClient(webClientBuilder, externalApiService, loggingService);
    }

    @Test
    void testAnalyzeImage_Success() {
        // Given
        MockMultipartFile file = new MockMultipartFile(
            "file", 
            "test.jpg", 
            MediaType.IMAGE_JPEG_VALUE, 
            "test image content".getBytes()
        );
        String userNeed = "sensitive skin";

        ProductAnalysisResponse mockResponse = ProductAnalysisResponse.builder()
            .success(true)
            .productName("Test Product")
            .avgEcoScore(75.0)
            .suitability("Suitable for sensitive skin")
            .recommendations("Use with caution")
            .analysisId("test_123")
            .processingTimeMs(1500)
            .build();

        when(webClient.post()).thenReturn(requestBodyUriSpec);
        when(requestBodyUriSpec.uri(anyString())).thenReturn(requestBodySpec);
        when(requestBodySpec.contentType(any(MediaType.class))).thenReturn(requestBodySpec);
        when(requestBodySpec.body(any())).thenReturn(requestBodySpec);
        when(requestBodySpec.retrieve()).thenReturn(responseSpec);
        when(responseSpec.bodyToMono(ProductAnalysisResponse.class)).thenReturn(Mono.just(mockResponse));

        // When
        Mono<ProductAnalysisResponse> result = client.analyzeImage(file, userNeed);

        // Then
        StepVerifier.create(result)
            .expectNext(mockResponse)
            .verifyComplete();
    }

    @Test
    void testAnalyzeImage_Error() {
        // Given
        MockMultipartFile file = new MockMultipartFile(
            "file", 
            "test.jpg", 
            MediaType.IMAGE_JPEG_VALUE, 
            "test image content".getBytes()
        );
        String userNeed = "sensitive skin";

        when(webClient.post()).thenReturn(requestBodyUriSpec);
        when(requestBodyUriSpec.uri(anyString())).thenReturn(requestBodySpec);
        when(requestBodySpec.contentType(any(MediaType.class))).thenReturn(requestBodySpec);
        when(requestBodySpec.body(any())).thenReturn(requestBodySpec);
        when(requestBodySpec.retrieve()).thenReturn(responseSpec);
        when(responseSpec.bodyToMono(ProductAnalysisResponse.class))
            .thenReturn(Mono.error(new RuntimeException("Python backend error")));

        // When
        Mono<ProductAnalysisResponse> result = client.analyzeImage(file, userNeed);

        // Then
        StepVerifier.create(result)
            .expectNextMatches(response -> 
                !response.isSuccess() && 
                response.getError().contains("Python backend error"))
            .verifyComplete();
    }

    @Test
    void testHealthCheck_Success() {
        // Given
        Map<String, Object> healthResponse = Map.of(
            "status", "healthy",
            "service", "python-backend",
            "version", "3.0.1"
        );

        when(webClient.get()).thenReturn(requestBodyUriSpec);
        when(requestBodyUriSpec.uri(anyString())).thenReturn(requestBodySpec);
        when(requestBodySpec.retrieve()).thenReturn(responseSpec);
        when(responseSpec.bodyToMono(Map.class)).thenReturn(Mono.just(healthResponse));

        // When
        Mono<Map<String, Object>> result = client.healthCheck();

        // Then
        StepVerifier.create(result)
            .expectNext(healthResponse)
            .verifyComplete();
    }
}
