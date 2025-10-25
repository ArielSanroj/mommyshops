package com.mommyshops.logging;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.OffsetDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Map;
import java.util.HashMap;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Production-grade logging service for MommyShops
 * Based on api_utils_production.py logging functionality
 */
@Service
public class ProductionLoggingService {
    
    private final ObjectMapper objectMapper;
    private final Path logDirectory;
    private final Path backendLogPath;
    private final Map<String, AtomicLong> logCounters;
    private final Map<String, AtomicLong> errorCounters;
    private final Map<String, AtomicLong> performanceCounters;
    
    @Value("${app.logging.level:INFO}")
    private String logLevel;
    
    @Value("${app.logging.backend-path:logs/backend.log}")
    private String backendLogPathProperty;
    
    @Value("${app.logging.max-file-size:10MB}")
    private String maxFileSize;
    
    @Value("${app.logging.max-files:10}")
    private int maxFiles;
    
    public ProductionLoggingService(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
        this.logDirectory = Paths.get("logs");
        this.backendLogPath = Paths.get("logs/backend.log");
        this.logCounters = new ConcurrentHashMap<>();
        this.errorCounters = new ConcurrentHashMap<>();
        this.performanceCounters = new ConcurrentHashMap<>();
        
        // Initialize log directory
        try {
            Files.createDirectories(logDirectory);
        } catch (IOException e) {
            System.err.println("Failed to create log directory: " + e.getMessage());
        }
    }
    
    /**
     * Log a message with structured JSON format
     */
    public void log(String level, String message, Map<String, Object> context) {
        try {
            ObjectNode logEntry = createLogEntry(level, message, context);
            writeToLogFile(logEntry);
            updateCounters(level, context);
        } catch (Exception e) {
            System.err.println("Failed to write log entry: " + e.getMessage());
        }
    }
    
    /**
     * Log info message
     */
    public void info(String message) {
        log("INFO", message, Map.of());
    }
    
    /**
     * Log info message with context
     */
    public void info(String message, Map<String, Object> context) {
        log("INFO", message, context);
    }
    
    /**
     * Log warning message
     */
    public void warning(String message) {
        log("WARNING", message, Map.of());
    }
    
    /**
     * Log warning message with context
     */
    public void warning(String message, Map<String, Object> context) {
        log("WARNING", message, context);
    }
    
    /**
     * Log error message
     */
    public void error(String message) {
        log("ERROR", message, Map.of());
    }
    
    /**
     * Log error message with context
     */
    public void error(String message, Map<String, Object> context) {
        log("ERROR", message, context);
    }
    
    /**
     * Log error message with exception
     */
    public void error(String message, Throwable throwable) {
        Map<String, Object> context = Map.of(
            "exception", throwable.getClass().getSimpleName(),
            "message", throwable.getMessage(),
            "stack_trace", getStackTrace(throwable)
        );
        log("ERROR", message, context);
    }
    
    /**
     * Log debug message
     */
    public void debug(String message) {
        log("DEBUG", message, Map.of());
    }
    
    /**
     * Log debug message with context
     */
    public void debug(String message, Map<String, Object> context) {
        log("DEBUG", message, context);
    }
    
    /**
     * Log API call
     */
    public void logApiCall(String api, String endpoint, long responseTime, boolean success) {
        Map<String, Object> context = Map.of(
            "api", api,
            "endpoint", endpoint,
            "response_time_ms", responseTime,
            "success", success
        );
        
        String level = success ? "INFO" : "ERROR";
        String message = success ? 
            "API call successful" : 
            "API call failed";
        
        log(level, message, context);
    }
    
    /**
     * Log ingredient analysis
     */
    public void logIngredientAnalysis(String ingredient, String source, boolean success, long responseTime) {
        Map<String, Object> context = Map.of(
            "ingredient", ingredient,
            "source", source,
            "success", success,
            "response_time_ms", responseTime
        );
        
        String level = success ? "INFO" : "ERROR";
        String message = success ? 
            "Ingredient analysis completed" : 
            "Ingredient analysis failed";
        
        log(level, message, context);
    }
    
    /**
     * Log OCR analysis
     */
    public void logOcrAnalysis(String imageType, int ingredientCount, boolean success, long responseTime) {
        Map<String, Object> context = Map.of(
            "image_type", imageType,
            "ingredient_count", ingredientCount,
            "success", success,
            "response_time_ms", responseTime
        );
        
        String level = success ? "INFO" : "ERROR";
        String message = success ? 
            "OCR analysis completed" : 
            "OCR analysis failed";
        
        log(level, message, context);
    }
    
    /**
     * Log substitution analysis
     */
    public void logSubstitutionAnalysis(int ingredientCount, int substituteCount, boolean success, long responseTime) {
        Map<String, Object> context = Map.of(
            "ingredient_count", ingredientCount,
            "substitute_count", substituteCount,
            "success", success,
            "response_time_ms", responseTime
        );
        
        String level = success ? "INFO" : "ERROR";
        String message = success ? 
            "Substitution analysis completed" : 
            "Substitution analysis failed";
        
        log(level, message, context);
    }
    
    /**
     * Log performance metrics
     */
    public void logPerformance(String operation, long duration, Map<String, Object> metrics) {
        Map<String, Object> context = new HashMap<>(metrics);
        context.put("operation", operation);
        context.put("duration_ms", duration);
        
        log("INFO", "Performance metric recorded", context);
        updatePerformanceCounter(operation, duration);
    }
    
    /**
     * Log security event
     */
    public void logSecurityEvent(String eventType, String userId, String details) {
        Map<String, Object> context = Map.of(
            "event_type", eventType,
            "user_id", userId,
            "details", details
        );
        
        log("WARNING", "Security event detected", context);
    }
    
    /**
     * Log cache operation
     */
    public void logCacheOperation(String operation, String key, boolean hit, long responseTime) {
        Map<String, Object> context = Map.of(
            "operation", operation,
            "key", key,
            "hit", hit,
            "response_time_ms", responseTime
        );
        
        log("DEBUG", "Cache operation", context);
    }
    
    /**
     * Create structured log entry
     */
    private ObjectNode createLogEntry(String level, String message, Map<String, Object> context) {
        ObjectNode logEntry = objectMapper.createObjectNode();
        
        // Standard fields
        logEntry.put("timestamp", OffsetDateTime.now().format(DateTimeFormatter.ISO_INSTANT));
        logEntry.put("logger", "mommyshops.api_utils");
        logEntry.put("level", level);
        logEntry.put("message", message);
        
        // Add context
        if (context != null && !context.isEmpty()) {
            ObjectNode contextNode = objectMapper.createObjectNode();
            context.forEach((key, value) -> {
                if (value instanceof String) {
                    contextNode.put(key, (String) value);
                } else if (value instanceof Number) {
                    contextNode.put(key, value.toString());
                } else if (value instanceof Boolean) {
                    contextNode.put(key, (Boolean) value);
                } else {
                    contextNode.put(key, value.toString());
                }
            });
            logEntry.set("context", contextNode);
        }
        
        return logEntry;
    }
    
    /**
     * Write log entry to file
     */
    private void writeToLogFile(ObjectNode logEntry) throws IOException {
        try (FileWriter writer = new FileWriter(backendLogPath.toFile(), true)) {
            writer.write(objectMapper.writeValueAsString(logEntry) + "\n");
        }
    }
    
    /**
     * Update log counters
     */
    private void updateCounters(String level, Map<String, Object> context) {
        // Update level counter
        logCounters.computeIfAbsent(level, k -> new AtomicLong(0)).incrementAndGet();
        
        // Update error counter
        if ("ERROR".equals(level)) {
            errorCounters.computeIfAbsent("total", k -> new AtomicLong(0)).incrementAndGet();
            
            // Update specific error counters
            if (context.containsKey("api")) {
                errorCounters.computeIfAbsent("api_" + context.get("api"), k -> new AtomicLong(0)).incrementAndGet();
            }
            if (context.containsKey("source")) {
                errorCounters.computeIfAbsent("source_" + context.get("source"), k -> new AtomicLong(0)).incrementAndGet();
            }
        }
    }
    
    /**
     * Update performance counter
     */
    private void updatePerformanceCounter(String operation, long duration) {
        performanceCounters.computeIfAbsent(operation, k -> new AtomicLong(0)).incrementAndGet();
    }
    
    /**
     * Get log statistics
     */
    public Map<String, Object> getLogStatistics() {
        Map<String, Object> stats = new HashMap<>();
        
        // Log level counts
        Map<String, Long> levelCounts = new HashMap<>();
        logCounters.forEach((level, counter) -> levelCounts.put(level, counter.get()));
        stats.put("log_levels", levelCounts);
        
        // Error counts
        Map<String, Long> errorCounts = new HashMap<>();
        errorCounters.forEach((type, counter) -> errorCounts.put(type, counter.get()));
        stats.put("errors", errorCounts);
        
        // Performance counts
        Map<String, Long> performanceCounts = new HashMap<>();
        performanceCounters.forEach((operation, counter) -> performanceCounts.put(operation, counter.get()));
        stats.put("performance", performanceCounts);
        
        // Total counts
        long totalLogs = logCounters.values().stream().mapToLong(AtomicLong::get).sum();
        long totalErrors = errorCounters.values().stream().mapToLong(AtomicLong::get).sum();
        
        stats.put("total_logs", totalLogs);
        stats.put("total_errors", totalErrors);
        stats.put("error_rate", totalLogs > 0 ? (double) totalErrors / totalLogs : 0.0);
        
        return stats;
    }
    
    /**
     * Get stack trace as string
     */
    private String getStackTrace(Throwable throwable) {
        StringBuilder sb = new StringBuilder();
        for (StackTraceElement element : throwable.getStackTrace()) {
            sb.append(element.toString()).append("\n");
        }
        return sb.toString();
    }
    
    /**
     * Log startup information
     */
    public void logStartup(String component, boolean success, long duration) {
        Map<String, Object> context = Map.of(
            "component", component,
            "success", success,
            "duration_ms", duration
        );
        
        String level = success ? "INFO" : "ERROR";
        String message = success ? 
            "Component started successfully" : 
            "Component startup failed";
        
        log(level, message, context);
    }
    
    /**
     * Log shutdown information
     */
    public void logShutdown(String component, boolean success, long duration) {
        Map<String, Object> context = Map.of(
            "component", component,
            "success", success,
            "duration_ms", duration
        );
        
        String level = success ? "INFO" : "ERROR";
        String message = success ? 
            "Component shutdown successfully" : 
            "Component shutdown failed";
        
        log(level, message, context);
    }
    
    /**
     * Log health check
     */
    public void logHealthCheck(String component, String status, long responseTime) {
        Map<String, Object> context = Map.of(
            "component", component,
            "status", status,
            "response_time_ms", responseTime
        );
        
        String level = "healthy".equals(status) ? "INFO" : "WARNING";
        String message = "Health check completed";
        
        log(level, message, context);
    }
    
    /**
     * Log rate limiting event
     */
    public void logRateLimit(String api, String reason) {
        Map<String, Object> context = Map.of(
            "api", api,
            "reason", reason
        );
        
        log("WARNING", "Rate limit exceeded", context);
    }
    
    /**
     * Log circuit breaker event
     */
    public void logCircuitBreaker(String api, String state, String reason) {
        Map<String, Object> context = Map.of(
            "api", api,
            "state", state,
            "reason", reason
        );
        
        String level = "OPEN".equals(state) ? "ERROR" : "INFO";
        String message = "Circuit breaker state changed";
        
        log(level, message, context);
    }
    
    /**
     * Log external API call
     */
    public void logExternalApiCall(com.mommyshops.integration.domain.ExternalSourceLog logEntry) {
        Map<String, Object> context = Map.of(
            "source_name", logEntry.getSourceName(),
            "query", logEntry.getQuery(),
            "status_code", logEntry.getStatusCode(),
            "fetched_at", logEntry.getFetchedAt().toString()
        );
        
        String level = logEntry.getStatusCode() >= 200 && logEntry.getStatusCode() < 300 ? "INFO" : "ERROR";
        String message = "External API call logged";
        
        log(level, message, context);
    }
}