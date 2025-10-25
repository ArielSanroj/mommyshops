package com.mommyshops.metrics;

import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.Gauge;
import io.micrometer.core.instrument.Histogram;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import io.micrometer.core.instrument.Tags;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Comprehensive metrics service for MommyShops
 */
@Service
public class MetricsService {

    @Autowired
    private MeterRegistry meterRegistry;

    // HTTP Request Metrics
    private final Counter httpRequestsTotal;
    private final Timer httpRequestDuration;

    // Analysis Metrics
    private final Counter analysisRequestsTotal;
    private final Timer analysisDuration;
    private final Gauge analysisSuccessRate;

    // Ingredient Metrics
    private final Counter ingredientAnalysisTotal;
    private final Histogram ingredientEcoScore;

    // Cache Metrics
    private final Counter cacheOperationsTotal;
    private final Gauge cacheHitRate;
    private final Gauge cacheSize;

    // External API Metrics
    private final Counter externalApiRequestsTotal;
    private final Timer externalApiDuration;

    // OCR Metrics
    private final Counter ocrRequestsTotal;
    private final Timer ocrDuration;
    private final Histogram ocrConfidence;

    // Ollama AI Metrics
    private final Counter ollamaRequestsTotal;
    private final Timer ollamaDuration;

    // Database Metrics
    private final Counter databaseQueriesTotal;
    private final Timer databaseDuration;

    // System Metrics
    private final Gauge memoryUsage;
    private final Gauge cpuUsage;
    private final Gauge activeConnections;

    // Error Metrics
    private final Counter errorsTotal;

    // Business Metrics
    private final Gauge usersTotal;
    private final Counter productsAnalyzedTotal;
    private final Counter ingredientsAnalyzedTotal;

    public MetricsService(MeterRegistry meterRegistry) {
        this.meterRegistry = meterRegistry;

        // Initialize HTTP metrics
        this.httpRequestsTotal = Counter.builder("http_requests_total")
                .description("Total HTTP requests")
                .tag("method", "unknown")
                .tag("endpoint", "unknown")
                .tag("status_code", "unknown")
                .register(meterRegistry);

        this.httpRequestDuration = Timer.builder("http_request_duration_seconds")
                .description("HTTP request duration")
                .tag("method", "unknown")
                .tag("endpoint", "unknown")
                .register(meterRegistry);

        // Initialize analysis metrics
        this.analysisRequestsTotal = Counter.builder("analysis_requests_total")
                .description("Total analysis requests")
                .tag("analysis_type", "unknown")
                .tag("user_need", "unknown")
                .register(meterRegistry);

        this.analysisDuration = Timer.builder("analysis_duration_seconds")
                .description("Analysis processing duration")
                .tag("analysis_type", "unknown")
                .register(meterRegistry);

        this.analysisSuccessRate = Gauge.builder("analysis_success_rate")
                .description("Analysis success rate")
                .tag("analysis_type", "unknown")
                .register(meterRegistry, new AtomicLong(0), AtomicLong::get);

        // Initialize ingredient metrics
        this.ingredientAnalysisTotal = Counter.builder("ingredient_analysis_total")
                .description("Total ingredient analyses")
                .tag("ingredient_name", "unknown")
                .tag("risk_level", "unknown")
                .register(meterRegistry);

        this.ingredientEcoScore = Histogram.builder("ingredient_eco_score")
                .description("Ingredient eco scores")
                .tag("ingredient_name", "unknown")
                .register(meterRegistry);

        // Initialize cache metrics
        this.cacheOperationsTotal = Counter.builder("cache_operations_total")
                .description("Total cache operations")
                .tag("operation", "unknown")
                .tag("cache_level", "unknown")
                .tag("result", "unknown")
                .register(meterRegistry);

        this.cacheHitRate = Gauge.builder("cache_hit_rate")
                .description("Cache hit rate")
                .tag("cache_level", "unknown")
                .register(meterRegistry, new AtomicLong(0), AtomicLong::get);

        this.cacheSize = Gauge.builder("cache_size")
                .description("Cache size")
                .tag("cache_level", "unknown")
                .register(meterRegistry, new AtomicLong(0), AtomicLong::get);

        // Initialize external API metrics
        this.externalApiRequestsTotal = Counter.builder("external_api_requests_total")
                .description("Total external API requests")
                .tag("api_name", "unknown")
                .tag("endpoint", "unknown")
                .tag("status", "unknown")
                .register(meterRegistry);

        this.externalApiDuration = Timer.builder("external_api_duration_seconds")
                .description("External API request duration")
                .tag("api_name", "unknown")
                .tag("endpoint", "unknown")
                .register(meterRegistry);

        // Initialize OCR metrics
        this.ocrRequestsTotal = Counter.builder("ocr_requests_total")
                .description("Total OCR requests")
                .tag("image_type", "unknown")
                .tag("status", "unknown")
                .register(meterRegistry);

        this.ocrDuration = Timer.builder("ocr_duration_seconds")
                .description("OCR processing duration")
                .tag("image_type", "unknown")
                .register(meterRegistry);

        this.ocrConfidence = Histogram.builder("ocr_confidence")
                .description("OCR confidence scores")
                .tag("image_type", "unknown")
                .register(meterRegistry);

        // Initialize Ollama metrics
        this.ollamaRequestsTotal = Counter.builder("ollama_requests_total")
                .description("Total Ollama requests")
                .tag("model", "unknown")
                .tag("operation", "unknown")
                .tag("status", "unknown")
                .register(meterRegistry);

        this.ollamaDuration = Timer.builder("ollama_duration_seconds")
                .description("Ollama processing duration")
                .tag("model", "unknown")
                .tag("operation", "unknown")
                .register(meterRegistry);

        // Initialize database metrics
        this.databaseQueriesTotal = Counter.builder("database_queries_total")
                .description("Total database queries")
                .tag("operation", "unknown")
                .tag("table", "unknown")
                .tag("status", "unknown")
                .register(meterRegistry);

        this.databaseDuration = Timer.builder("database_duration_seconds")
                .description("Database query duration")
                .tag("operation", "unknown")
                .tag("table", "unknown")
                .register(meterRegistry);

        // Initialize system metrics
        this.memoryUsage = Gauge.builder("memory_usage_bytes")
                .description("Memory usage in bytes")
                .tag("type", "heap")
                .register(meterRegistry, new AtomicLong(0), AtomicLong::get);

        this.cpuUsage = Gauge.builder("cpu_usage_percent")
                .description("CPU usage percentage")
                .register(meterRegistry, new AtomicLong(0), AtomicLong::get);

        this.activeConnections = Gauge.builder("active_connections")
                .description("Active connections")
                .tag("connection_type", "http")
                .register(meterRegistry, new AtomicLong(0), AtomicLong::get);

        // Initialize error metrics
        this.errorsTotal = Counter.builder("errors_total")
                .description("Total errors")
                .tag("error_type", "unknown")
                .tag("component", "unknown")
                .tag("severity", "unknown")
                .register(meterRegistry);

        // Initialize business metrics
        this.usersTotal = Gauge.builder("users_total")
                .description("Total number of users")
                .register(meterRegistry, new AtomicLong(0), AtomicLong::get);

        this.productsAnalyzedTotal = Counter.builder("products_analyzed_total")
                .description("Total products analyzed")
                .tag("analysis_type", "unknown")
                .register(meterRegistry);

        this.ingredientsAnalyzedTotal = Counter.builder("ingredients_analyzed_total")
                .description("Total ingredients analyzed")
                .register(meterRegistry);
    }

    // HTTP Request Metrics
    public void recordHttpRequest(String method, String endpoint, int statusCode, Duration duration) {
        Counter.builder("http_requests_total")
                .description("Total HTTP requests")
                .tag("method", method)
                .tag("endpoint", endpoint)
                .tag("status_code", String.valueOf(statusCode))
                .register(meterRegistry)
                .increment();

        Timer.builder("http_request_duration_seconds")
                .description("HTTP request duration")
                .tag("method", method)
                .tag("endpoint", endpoint)
                .register(meterRegistry)
                .record(duration);
    }

    // Analysis Metrics
    public void recordAnalysisRequest(String analysisType, String userNeed, Duration duration, boolean success) {
        Counter.builder("analysis_requests_total")
                .description("Total analysis requests")
                .tag("analysis_type", analysisType)
                .tag("user_need", userNeed)
                .register(meterRegistry)
                .increment();

        Timer.builder("analysis_duration_seconds")
                .description("Analysis processing duration")
                .tag("analysis_type", analysisType)
                .register(meterRegistry)
                .record(duration);

        Gauge.builder("analysis_success_rate")
                .description("Analysis success rate")
                .tag("analysis_type", analysisType)
                .register(meterRegistry, new AtomicLong(success ? 1 : 0), AtomicLong::get);
    }

    // Ingredient Metrics
    public void recordIngredientAnalysis(String ingredientName, String riskLevel, double ecoScore) {
        Counter.builder("ingredient_analysis_total")
                .description("Total ingredient analyses")
                .tag("ingredient_name", ingredientName)
                .tag("risk_level", riskLevel)
                .register(meterRegistry)
                .increment();

        Histogram.builder("ingredient_eco_score")
                .description("Ingredient eco scores")
                .tag("ingredient_name", ingredientName)
                .register(meterRegistry)
                .record(ecoScore);
    }

    // Cache Metrics
    public void recordCacheOperation(String operation, String cacheLevel, String result) {
        Counter.builder("cache_operations_total")
                .description("Total cache operations")
                .tag("operation", operation)
                .tag("cache_level", cacheLevel)
                .tag("result", result)
                .register(meterRegistry)
                .increment();
    }

    public void updateCacheHitRate(String cacheLevel, double hitRate) {
        Gauge.builder("cache_hit_rate")
                .description("Cache hit rate")
                .tag("cache_level", cacheLevel)
                .register(meterRegistry, new AtomicLong((long) (hitRate * 100)), AtomicLong::get);
    }

    public void updateCacheSize(String cacheLevel, long size) {
        Gauge.builder("cache_size")
                .description("Cache size")
                .tag("cache_level", cacheLevel)
                .register(meterRegistry, new AtomicLong(size), AtomicLong::get);
    }

    // External API Metrics
    public void recordExternalApiRequest(String apiName, String endpoint, String status, Duration duration) {
        Counter.builder("external_api_requests_total")
                .description("Total external API requests")
                .tag("api_name", apiName)
                .tag("endpoint", endpoint)
                .tag("status", status)
                .register(meterRegistry)
                .increment();

        Timer.builder("external_api_duration_seconds")
                .description("External API request duration")
                .tag("api_name", apiName)
                .tag("endpoint", endpoint)
                .register(meterRegistry)
                .record(duration);
    }

    // OCR Metrics
    public void recordOcrRequest(String imageType, String status, Duration duration, double confidence) {
        Counter.builder("ocr_requests_total")
                .description("Total OCR requests")
                .tag("image_type", imageType)
                .tag("status", status)
                .register(meterRegistry)
                .increment();

        Timer.builder("ocr_duration_seconds")
                .description("OCR processing duration")
                .tag("image_type", imageType)
                .register(meterRegistry)
                .record(duration);

        Histogram.builder("ocr_confidence")
                .description("OCR confidence scores")
                .tag("image_type", imageType)
                .register(meterRegistry)
                .record(confidence);
    }

    // Ollama Metrics
    public void recordOllamaRequest(String model, String operation, String status, Duration duration) {
        Counter.builder("ollama_requests_total")
                .description("Total Ollama requests")
                .tag("model", model)
                .tag("operation", operation)
                .tag("status", status)
                .register(meterRegistry)
                .increment();

        Timer.builder("ollama_duration_seconds")
                .description("Ollama processing duration")
                .tag("model", model)
                .tag("operation", operation)
                .register(meterRegistry)
                .record(duration);
    }

    // Database Metrics
    public void recordDatabaseQuery(String operation, String table, String status, Duration duration) {
        Counter.builder("database_queries_total")
                .description("Total database queries")
                .tag("operation", operation)
                .tag("table", table)
                .tag("status", status)
                .register(meterRegistry)
                .increment();

        Timer.builder("database_duration_seconds")
                .description("Database query duration")
                .tag("operation", operation)
                .tag("table", table)
                .register(meterRegistry)
                .record(duration);
    }

    // System Metrics
    public void updateSystemMetrics(long memoryUsage, double cpuUsage, int activeConnections) {
        Gauge.builder("memory_usage_bytes")
                .description("Memory usage in bytes")
                .tag("type", "heap")
                .register(meterRegistry, new AtomicLong(memoryUsage), AtomicLong::get);

        Gauge.builder("cpu_usage_percent")
                .description("CPU usage percentage")
                .register(meterRegistry, new AtomicLong((long) (cpuUsage * 100)), AtomicLong::get);

        Gauge.builder("active_connections")
                .description("Active connections")
                .tag("connection_type", "http")
                .register(meterRegistry, new AtomicLong(activeConnections), AtomicLong::get);
    }

    // Error Metrics
    public void recordError(String errorType, String component, String severity) {
        Counter.builder("errors_total")
                .description("Total errors")
                .tag("error_type", errorType)
                .tag("component", component)
                .tag("severity", severity)
                .register(meterRegistry)
                .increment();
    }

    // Business Metrics
    public void updateBusinessMetrics(long usersTotal, long productsAnalyzed, long ingredientsAnalyzed) {
        Gauge.builder("users_total")
                .description("Total number of users")
                .register(meterRegistry, new AtomicLong(usersTotal), AtomicLong::get);

        Counter.builder("products_analyzed_total")
                .description("Total products analyzed")
                .tag("analysis_type", "all")
                .register(meterRegistry)
                .increment(productsAnalyzed);

        Counter.builder("ingredients_analyzed_total")
                .description("Total ingredients analyzed")
                .register(meterRegistry)
                .increment(ingredientsAnalyzed);
    }
}
