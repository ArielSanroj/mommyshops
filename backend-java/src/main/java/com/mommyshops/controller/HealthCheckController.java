package com.mommyshops.controller;

import com.mommyshops.startup.StartupHealthCheckService;
import com.mommyshops.startup.EnvironmentValidationService;
import com.mommyshops.integration.util.SimpleProductionApiUtils;
import com.mommyshops.logging.ProductionLoggingService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.HashMap;
import java.util.concurrent.CompletableFuture;

/**
 * Health check controller for MommyShops
 * Provides comprehensive health monitoring and status endpoints
 */
@RestController
@RequestMapping("/api/health")
@CrossOrigin(origins = "*")
public class HealthCheckController {
    
    @Autowired
    private StartupHealthCheckService startupHealthCheckService;
    
    @Autowired
    private EnvironmentValidationService environmentValidationService;
    
    @Autowired
    private SimpleProductionApiUtils productionApiUtils;
    
    @Autowired
    private ProductionLoggingService productionLoggingService;
    
    /**
     * Overall health check endpoint
     */
    @GetMapping
    public ResponseEntity<Map<String, Object>> healthCheck() {
        try {
            StartupHealthCheckService.HealthStatus overallHealth = startupHealthCheckService.getOverallHealth();
            
            Map<String, Object> response = Map.of(
                "status", overallHealth.getStatus(),
                "healthy", overallHealth.isHealthy(),
                "message", overallHealth.getMessage(),
                "timestamp", System.currentTimeMillis(),
                "uptime", getUptime(),
                "version", getVersion(),
                "components", startupHealthCheckService.getHealthStatus()
            );
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            Map<String, Object> errorResponse = Map.of(
                "status", "unhealthy",
                "healthy", false,
                "message", "Health check failed: " + e.getMessage(),
                "timestamp", System.currentTimeMillis(),
                "error", e.getMessage()
            );
            
            return ResponseEntity.status(500).body(errorResponse);
        }
    }
    
    /**
     * Quick health check endpoint
     */
    @GetMapping("/quick")
    public CompletableFuture<ResponseEntity<Map<String, Object>>> quickHealthCheck() {
        return startupHealthCheckService.quickHealthCheck()
            .thenApply(healthData -> {
                Map<String, Object> response = Map.of(
                    "status", "healthy",
                    "healthy", true,
                    "message", "Quick health check completed",
                    "timestamp", System.currentTimeMillis(),
                    "components", healthData
                );
                
                return ResponseEntity.ok(response);
            })
            .exceptionally(throwable -> {
                Map<String, Object> errorResponse = Map.of(
                    "status", "unhealthy",
                    "healthy", false,
                    "message", "Quick health check failed: " + throwable.getMessage(),
                    "timestamp", System.currentTimeMillis(),
                    "error", throwable.getMessage()
                );
                
                return ResponseEntity.status(500).body(errorResponse);
            });
    }
    
    /**
     * Detailed health check endpoint
     */
    @GetMapping("/detailed")
    public ResponseEntity<Map<String, Object>> detailedHealthCheck() {
        try {
            Map<String, StartupHealthCheckService.HealthStatus> componentHealth = 
                startupHealthCheckService.getHealthStatus();
            
            Map<String, Object> response = Map.of(
                "status", "healthy",
                "healthy", true,
                "message", "Detailed health check completed",
                "timestamp", System.currentTimeMillis(),
                "uptime", getUptime(),
                "version", getVersion(),
                "components", componentHealth,
                "environment", environmentValidationService.getValidationResults(),
                "cache_stats", productionApiUtils.getCacheStats(),
                "log_stats", productionLoggingService.getLogStatistics()
            );
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            Map<String, Object> errorResponse = Map.of(
                "status", "unhealthy",
                "healthy", false,
                "message", "Detailed health check failed: " + e.getMessage(),
                "timestamp", System.currentTimeMillis(),
                "error", e.getMessage()
            );
            
            return ResponseEntity.status(500).body(errorResponse);
        }
    }
    
    /**
     * Component-specific health check
     */
    @GetMapping("/component/{component}")
    public ResponseEntity<Map<String, Object>> componentHealthCheck(@PathVariable String component) {
        try {
            Map<String, StartupHealthCheckService.HealthStatus> allComponents = 
                startupHealthCheckService.getHealthStatus();
            
            StartupHealthCheckService.HealthStatus componentStatus = allComponents.get(component);
            
            if (componentStatus == null) {
                Map<String, Object> notFoundResponse = Map.of(
                    "status", "not_found",
                    "healthy", false,
                    "message", "Component not found: " + component,
                    "timestamp", System.currentTimeMillis()
                );
                
                return ResponseEntity.status(404).body(notFoundResponse);
            }
            
            Map<String, Object> response = Map.of(
                "component", component,
                "status", componentStatus.getStatus(),
                "healthy", componentStatus.isHealthy(),
                "message", componentStatus.getMessage(),
                "response_time", componentStatus.getResponseTime(),
                "last_checked", componentStatus.getLastChecked(),
                "details", componentStatus.getDetails(),
                "timestamp", System.currentTimeMillis()
            );
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            Map<String, Object> errorResponse = Map.of(
                "component", component,
                "status", "error",
                "healthy", false,
                "message", "Component health check failed: " + e.getMessage(),
                "timestamp", System.currentTimeMillis(),
                "error", e.getMessage()
            );
            
            return ResponseEntity.status(500).body(errorResponse);
        }
    }
    
    /**
     * Environment validation endpoint
     */
    @GetMapping("/environment")
    public ResponseEntity<Map<String, Object>> environmentValidation() {
        try {
            Map<String, EnvironmentValidationService.ValidationResult> validationResults = 
                environmentValidationService.validateEnvironment();
            
            boolean isValid = environmentValidationService.isEnvironmentValid();
            
            Map<String, Object> response = Map.of(
                "valid", isValid,
                "message", isValid ? "Environment validation passed" : "Environment validation failed",
                "timestamp", System.currentTimeMillis(),
                "validations", validationResults,
                "critical_issues", environmentValidationService.getCriticalIssues(),
                "warnings", environmentValidationService.getWarnings()
            );
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            Map<String, Object> errorResponse = Map.of(
                "valid", false,
                "message", "Environment validation failed: " + e.getMessage(),
                "timestamp", System.currentTimeMillis(),
                "error", e.getMessage()
            );
            
            return ResponseEntity.status(500).body(errorResponse);
        }
    }
    
    /**
     * API health check endpoint
     */
    @GetMapping("/apis")
    public CompletableFuture<ResponseEntity<Map<String, Object>>> apiHealthCheck() {
        return CompletableFuture.supplyAsync(() -> {
            Map<String, Object> apiHealth = productionApiUtils.healthCheck();
            Map<String, Object> response = new HashMap<>();
            response.put("status", "healthy");
            response.put("healthy", true);
            response.put("message", "API health check completed");
            response.put("timestamp", System.currentTimeMillis());
            response.put("apis", apiHealth);
            return ResponseEntity.ok(response);
        })
            .exceptionally(throwable -> {
                Map<String, Object> errorResponse = Map.of(
                    "status", "unhealthy",
                    "healthy", false,
                    "message", "API health check failed: " + throwable.getMessage(),
                    "timestamp", System.currentTimeMillis(),
                    "error", throwable.getMessage()
                );
                
                return ResponseEntity.status(500).body(errorResponse);
            });
    }
    
    /**
     * Cache health check endpoint
     */
    @GetMapping("/cache")
    public ResponseEntity<Map<String, Object>> cacheHealthCheck() {
        try {
            Map<String, Object> cacheStats = productionApiUtils.getCacheStats();
            
            Map<String, Object> response = Map.of(
                "status", "healthy",
                "healthy", true,
                "message", "Cache health check completed",
                "timestamp", System.currentTimeMillis(),
                "cache_stats", cacheStats
            );
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            Map<String, Object> errorResponse = Map.of(
                "status", "unhealthy",
                "healthy", false,
                "message", "Cache health check failed: " + e.getMessage(),
                "timestamp", System.currentTimeMillis(),
                "error", e.getMessage()
            );
            
            return ResponseEntity.status(500).body(errorResponse);
        }
    }
    
    /**
     * Logging health check endpoint
     */
    @GetMapping("/logging")
    public ResponseEntity<Map<String, Object>> loggingHealthCheck() {
        try {
            Map<String, Object> logStats = productionLoggingService.getLogStatistics();
            
            Map<String, Object> response = Map.of(
                "status", "healthy",
                "healthy", true,
                "message", "Logging health check completed",
                "timestamp", System.currentTimeMillis(),
                "log_stats", logStats
            );
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            Map<String, Object> errorResponse = Map.of(
                "status", "unhealthy",
                "healthy", false,
                "message", "Logging health check failed: " + e.getMessage(),
                "timestamp", System.currentTimeMillis(),
                "error", e.getMessage()
            );
            
            return ResponseEntity.status(500).body(errorResponse);
        }
    }
    
    /**
     * Clear cache endpoint
     */
    @PostMapping("/cache/clear")
    public ResponseEntity<Map<String, Object>> clearCache() {
        try {
            productionApiUtils.clearCache();
            
            Map<String, Object> response = Map.of(
                "status", "success",
                "message", "Cache cleared successfully",
                "timestamp", System.currentTimeMillis()
            );
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            Map<String, Object> errorResponse = Map.of(
                "status", "error",
                "message", "Cache clear failed: " + e.getMessage(),
                "timestamp", System.currentTimeMillis(),
                "error", e.getMessage()
            );
            
            return ResponseEntity.status(500).body(errorResponse);
        }
    }
    
    /**
     * Get application information
     */
    @GetMapping("/info")
    public ResponseEntity<Map<String, Object>> applicationInfo() {
        Map<String, Object> info = new HashMap<>();
        info.put("name", "MommyShops");
        info.put("version", getVersion());
        info.put("description", "AI-powered cosmetic ingredient analysis and recommendation platform");
        info.put("uptime", getUptime());
        info.put("timestamp", System.currentTimeMillis());
        info.put("java_version", System.getProperty("java.version"));
        info.put("os_name", System.getProperty("os.name"));
        info.put("os_version", System.getProperty("os.version"));
        info.put("available_processors", Runtime.getRuntime().availableProcessors());
        info.put("max_memory", Runtime.getRuntime().maxMemory());
        info.put("total_memory", Runtime.getRuntime().totalMemory());
        info.put("free_memory", Runtime.getRuntime().freeMemory());
        
        return ResponseEntity.ok(info);
    }
    
    /**
     * Get uptime in milliseconds
     */
    private long getUptime() {
        return System.currentTimeMillis() - getStartTime();
    }
    
    /**
     * Get application start time
     */
    private long getStartTime() {
        // This would typically be set during application startup
        return System.currentTimeMillis() - 1000; // Placeholder
    }
    
    /**
     * Get application version
     */
    private String getVersion() {
        return "1.0.0"; // This would typically come from application properties
    }
}