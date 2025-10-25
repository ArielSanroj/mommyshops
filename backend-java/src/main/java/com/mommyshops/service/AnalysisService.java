package com.mommyshops.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

import java.io.IOException;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;

@Service
public class AnalysisService {
    
    @Autowired
    private RestTemplate restTemplate;
    
    @Autowired
    private ObjectMapper objectMapper;
    
    private final String backendBaseUrl;
    
    public AnalysisService(@Value("${analysis.backend.base-url:http://localhost:8081}") String backendBaseUrl) {
        this.backendBaseUrl = backendBaseUrl;
    }
    
    public Map<String, Object> analyzeProduct(String imageUrl, Map<String, Object> userProfile) {
        try {
            Map<String, Object> request = new HashMap<>();
            request.put("imageUrl", imageUrl);
            request.put("userProfile", userProfile);

            String url = backendBaseUrl + "/api/analysis/analyze-product";
            Map<String, Object> response = restTemplate.postForObject(url, request, Map.class);
            return response != null ? response : createFallbackResults();
        } catch (Exception e) {
            return createFallbackResults();
        }
    }

    public Map<String, Object> analyzeUploadedImage(byte[] imageBytes, String originalFilename) {
        if (imageBytes == null || imageBytes.length == 0) {
            return createFallbackResults();
        }
        String filename = originalFilename != null && !originalFilename.isBlank()
            ? originalFilename
            : "uploaded-image.jpg";

        return analyzeImageBytes(imageBytes, filename);
    }

    public Map<String, Object> analyzeUploadedImage(InputStream inputStream, String originalFilename) {
        if (inputStream == null) {
            return createFallbackResults();
        }
        try {
            byte[] bytes = inputStream.readAllBytes();
            return analyzeUploadedImage(bytes, originalFilename);
        } catch (IOException e) {
            return createFallbackResults();
        }
    }

    private Map<String, Object> analyzeImageBytes(byte[] imageBytes, String fileName) {
        try {
            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            body.add("file", new ByteArrayResource(imageBytes) {
                @Override
                public String getFilename() {
                    return fileName;
                }
            });
            body.add("productName", fileName);
            body.add("userId", "00000000-0000-0000-0000-000000000001");

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);

            HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);

            String url = backendBaseUrl + "/api/analysis/analyze-image";
            Map<String, Object> response = restTemplate.postForObject(url, requestEntity, Map.class);
            return response != null ? response : createFallbackResults();
        } catch (Exception e) {
            return createFallbackResults();
        }
    }
    
    private Map<String, Object> createFallbackResults() {
        Map<String, Object> fallback = new HashMap<>();
        fallback.put("status", "fallback");
        fallback.put("errorMessage", "No se pudo analizar la imagen.");
        fallback.put("productName", "Análisis no disponible");
        fallback.put("analysisSummary", "No se pudo analizar la imagen. Asegúrate de que el enfoque sea claro o pega la URL del producto e intenta nuevamente.");
        fallback.put("recommendations", "Haz clic en 'Nuevo Análisis' y vuelve a subir una foto donde los ingredientes se lean claramente o ingresa una URL de producto.");
        return fallback;
    }
}