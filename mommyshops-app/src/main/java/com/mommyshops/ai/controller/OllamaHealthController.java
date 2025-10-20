package com.mommyshops.ai.controller;

import com.mommyshops.ai.service.OllamaService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/ollama")
public class OllamaHealthController {
    
    private final OllamaService ollamaService;
    
    @Autowired
    public OllamaHealthController(OllamaService ollamaService) {
        this.ollamaService = ollamaService;
    }
    
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> checkHealth() {
        try {
            Boolean healthy = ollamaService.isHealthy();
            Map<String, Object> response = Map.of(
                "status", healthy ? "UP" : "DOWN",
                "service", "Ollama",
                "timestamp", System.currentTimeMillis()
            );
            
            return ResponseEntity.status(healthy ? 200 : 503)
                .body(response);
        } catch (Exception e) {
            return ResponseEntity.status(503)
                .body(Map.of(
                    "status", "DOWN",
                    "service", "Ollama",
                    "error", "Connection failed",
                    "timestamp", System.currentTimeMillis()
                ));
        }
    }
    
    @GetMapping("/models")
    public ResponseEntity<Map<String, Object>> listModels() {
        try {
            Boolean healthy = ollamaService.isHealthy();
            if (healthy) {
                return ResponseEntity.ok(Map.of(
                    "status", "UP",
                    "models", "llama3.1, llava",
                    "timestamp", System.currentTimeMillis()
                ));
            } else {
                return ResponseEntity.status(503)
                    .body(Map.of(
                        "status", "DOWN",
                        "error", "Ollama service unavailable",
                        "timestamp", System.currentTimeMillis()
                    ));
            }
        } catch (Exception e) {
            return ResponseEntity.status(503)
                .body(Map.of(
                    "status", "DOWN",
                    "error", "Ollama service unavailable",
                    "timestamp", System.currentTimeMillis()
                ));
        }
    }
}