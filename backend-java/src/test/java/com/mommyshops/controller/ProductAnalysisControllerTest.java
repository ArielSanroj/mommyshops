package com.mommyshops.controller;

import com.mommyshops.analysis.service.ProductAnalysisService;
import com.mommyshops.integration.client.PythonBackendClient;
import com.mommyshops.profile.repository.UserProfileRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import reactor.core.publisher.Mono;

import java.util.Map;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Tests for ProductAnalysisController
 */
@ExtendWith(MockitoExtension.class)
class ProductAnalysisControllerTest {

    @Mock
    private ProductAnalysisService productAnalysisService;

    @Mock
    private UserProfileRepository userProfileRepository;

    @Mock
    private PythonBackendClient pythonBackendClient;

    @InjectMocks
    private ProductAnalysisController controller;

    private MockMvc mockMvc;

    @BeforeEach
    void setUp() {
        mockMvc = MockMvcBuilders.standaloneSetup(controller).build();
    }

    @Test
    void testAnalyzeImage_Success() throws Exception {
        // Given
        MockMultipartFile file = new MockMultipartFile(
            "file", 
            "test.jpg", 
            MediaType.IMAGE_JPEG_VALUE, 
            "test image content".getBytes()
        );
        
        String productName = "Test Product";
        String userId = UUID.randomUUID().toString();
        String userNeed = "sensitive skin";

        // Mock Python backend response
        Map<String, Object> mockResponse = Map.of(
            "success", true,
            "productName", productName,
            "ingredientsDetails", java.util.List.of(),
            "avgEcoScore", 75.0,
            "suitability", "Suitable for sensitive skin",
            "recommendations", "Use with caution",
            "analysisId", "test_123",
            "processingTimeMs", 1500
        );

        when(pythonBackendClient.analyzeImage(any(), anyString()))
            .thenReturn(Mono.just(mockResponse));

        // When & Then
        mockMvc.perform(multipart("/api/analysis/analyze-image")
                .file(file)
                .param("productName", productName)
                .param("userId", userId)
                .param("userNeed", userNeed)
                .contentType(MediaType.MULTIPART_FORM_DATA))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("success"))
                .andExpect(jsonPath("$.productName").value(productName))
                .andExpect(jsonPath("$.avgEcoScore").value(75.0));
    }

    @Test
    void testAnalyzeImage_PythonBackendError() throws Exception {
        // Given
        MockMultipartFile file = new MockMultipartFile(
            "file", 
            "test.jpg", 
            MediaType.IMAGE_JPEG_VALUE, 
            "test image content".getBytes()
        );

        // Mock Python backend error
        Map<String, Object> errorResponse = Map.of(
            "success", false,
            "error", "Python backend unavailable"
        );

        when(pythonBackendClient.analyzeImage(any(), anyString()))
            .thenReturn(Mono.just(errorResponse));

        // When & Then
        mockMvc.perform(multipart("/api/analysis/analyze-image")
                .file(file)
                .param("productName", "Test Product")
                .param("userId", UUID.randomUUID().toString())
                .contentType(MediaType.MULTIPART_FORM_DATA))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("error"))
                .andExpect(jsonPath("$.message").value("Python backend error: Python backend unavailable"));
    }

    @Test
    void testAnalyzeImage_InvalidFileType() throws Exception {
        // Given
        MockMultipartFile file = new MockMultipartFile(
            "file", 
            "test.txt", 
            MediaType.TEXT_PLAIN_VALUE, 
            "test content".getBytes()
        );

        // When & Then
        mockMvc.perform(multipart("/api/analysis/analyze-image")
                .file(file)
                .param("productName", "Test Product")
                .param("userId", UUID.randomUUID().toString())
                .contentType(MediaType.MULTIPART_FORM_DATA))
                .andExpect(status().isBadRequest());
    }
}
