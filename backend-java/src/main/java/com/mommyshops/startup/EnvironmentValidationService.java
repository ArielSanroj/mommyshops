package com.mommyshops.startup;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.core.env.Environment;

import java.util.*;
import java.util.stream.Collectors;

/**
 * Environment validation service for MommyShops
 * Validates all required environment variables and configurations
 */
@Service
public class EnvironmentValidationService {
    
    private final Environment environment;
    private final Map<String, ValidationResult> validationResults;
    
    @Value("${app.api.fda-key:}")
    private String fdaApiKey;
    
    @Value("${app.api.ewg-key:}")
    private String ewgApiKey;
    
    @Value("${app.api.inci-beauty-key:}")
    private String inciBeautyApiKey;
    
    @Value("${app.api.cosing-key:}")
    private String cosingApiKey;
    
    @Value("${app.api.entrez-email:your.email@example.com}")
    private String entrezEmail;
    
    @Value("${app.api.apify-key:}")
    private String apifyApiKey;
    
    @Value("${app.ollama.base-url:http://localhost:11434}")
    private String ollamaBaseUrl;
    
    @Value("${app.ollama.model:text}")
    private String ollamaModel;
    
    @Value("${app.ollama.vision-model:llava}")
    private String ollamaVisionModel;
    
    @Value("${spring.datasource.url:}")
    private String databaseUrl;
    
    @Value("${spring.datasource.username:}")
    private String databaseUsername;
    
    @Value("${spring.datasource.password:}")
    private String databasePassword;
    
    @Value("${spring.redis.host:localhost}")
    private String redisHost;
    
    @Value("${spring.redis.port:6379}")
    private int redisPort;
    
    @Value("${app.logging.level:INFO}")
    private String logLevel;
    
    @Value("${app.logging.backend-path:logs/backend.log}")
    private String backendLogPath;
    
    public EnvironmentValidationService(Environment environment) {
        this.environment = environment;
        this.validationResults = new HashMap<>();
    }
    
    /**
     * Validation result for environment variables
     */
    public static class ValidationResult {
        private boolean valid;
        private String message;
        private String severity; // INFO, WARNING, ERROR
        private Map<String, Object> details;
        
        public ValidationResult(boolean valid, String message, String severity) {
            this.valid = valid;
            this.message = message;
            this.severity = severity;
            this.details = new HashMap<>();
        }
        
        public ValidationResult(boolean valid, String message, String severity, Map<String, Object> details) {
            this.valid = valid;
            this.message = message;
            this.severity = severity;
            this.details = details;
        }
        
        // Getters and setters
        public boolean isValid() { return valid; }
        public void setValid(boolean valid) { this.valid = valid; }
        public String getMessage() { return message; }
        public void setMessage(String message) { this.message = message; }
        public String getSeverity() { return severity; }
        public void setSeverity(String severity) { this.severity = severity; }
        public Map<String, Object> getDetails() { return details; }
        public void setDetails(Map<String, Object> details) { this.details = details; }
    }
    
    /**
     * Validate all environment variables and configurations
     */
    public Map<String, ValidationResult> validateEnvironment() {
        System.out.println("🔍 Validating environment configuration...");
        
        // Clear previous results
        validationResults.clear();
        
        // Validate API keys
        validateApiKeys();
        
        // Validate database configuration
        validateDatabaseConfiguration();
        
        // Validate Redis configuration
        validateRedisConfiguration();
        
        // Validate Ollama configuration
        validateOllamaConfiguration();
        
        // Validate logging configuration
        validateLoggingConfiguration();
        
        // Validate security configuration
        validateSecurityConfiguration();
        
        // Validate performance configuration
        validatePerformanceConfiguration();
        
        // Print validation summary
        printValidationSummary();
        
        return new HashMap<>(validationResults);
    }
    
    /**
     * Validate API keys
     */
    private void validateApiKeys() {
        System.out.println("🔑 Validating API keys...");
        
        // FDA API Key
        if (fdaApiKey == null || fdaApiKey.trim().isEmpty() || fdaApiKey.equals("your_fda_api_key_here")) {
            validationResults.put("fda_api_key", new ValidationResult(
                false, "FDA API key not configured", "WARNING",
                Map.of("key", "app.api.fda-key", "required", true, "impact", "FDA data unavailable")
            ));
            System.out.println("⚠️  FDA API key: Not configured");
        } else {
            validationResults.put("fda_api_key", new ValidationResult(
                true, "FDA API key configured", "INFO",
                Map.of("key", "app.api.fda-key", "configured", true)
            ));
            System.out.println("✅ FDA API key: Configured");
        }
        
        // EWG API Key
        if (ewgApiKey == null || ewgApiKey.trim().isEmpty() || ewgApiKey.equals("your_ewg_api_key_here")) {
            validationResults.put("ewg_api_key", new ValidationResult(
                false, "EWG API key not configured", "WARNING",
                Map.of("key", "app.api.ewg-key", "required", false, "impact", "EWG data via web scraping only")
            ));
            System.out.println("⚠️  EWG API key: Not configured (web scraping fallback available)");
        } else {
            validationResults.put("ewg_api_key", new ValidationResult(
                true, "EWG API key configured", "INFO",
                Map.of("key", "app.api.ewg-key", "configured", true)
            ));
            System.out.println("✅ EWG API key: Configured");
        }
        
        // INCI Beauty API Key
        if (inciBeautyApiKey == null || inciBeautyApiKey.trim().isEmpty() || inciBeautyApiKey.equals("your_inci_beauty_api_key_here")) {
            validationResults.put("inci_beauty_api_key", new ValidationResult(
                false, "INCI Beauty API key not configured", "WARNING",
                Map.of("key", "app.api.inci-beauty-key", "required", false, "impact", "INCI Beauty data unavailable")
            ));
            System.out.println("⚠️  INCI Beauty API key: Not configured");
        } else {
            validationResults.put("inci_beauty_api_key", new ValidationResult(
                true, "INCI Beauty API key configured", "INFO",
                Map.of("key", "app.api.inci-beauty-key", "configured", true)
            ));
            System.out.println("✅ INCI Beauty API key: Configured");
        }
        
        // COSING API Key
        if (cosingApiKey == null || cosingApiKey.trim().isEmpty() || cosingApiKey.equals("your_cosing_api_key_here")) {
            validationResults.put("cosing_api_key", new ValidationResult(
                false, "COSING API key not configured", "WARNING",
                Map.of("key", "app.api.cosing-key", "required", false, "impact", "COSING data via CSV only")
            ));
            System.out.println("⚠️  COSING API key: Not configured (CSV fallback available)");
        } else {
            validationResults.put("cosing_api_key", new ValidationResult(
                true, "COSING API key configured", "INFO",
                Map.of("key", "app.api.cosing-key", "configured", true)
            ));
            System.out.println("✅ COSING API key: Configured");
        }
        
        // Apify API Key
        if (apifyApiKey == null || apifyApiKey.trim().isEmpty() || apifyApiKey.equals("your_apify_api_key_here")) {
            validationResults.put("apify_api_key", new ValidationResult(
                false, "Apify API key not configured", "INFO",
                Map.of("key", "app.api.apify-key", "required", false, "impact", "Web scraping via Apify unavailable")
            ));
            System.out.println("ℹ️  Apify API key: Not configured (optional)");
        } else {
            validationResults.put("apify_api_key", new ValidationResult(
                true, "Apify API key configured", "INFO",
                Map.of("key", "app.api.apify-key", "configured", true)
            ));
            System.out.println("✅ Apify API key: Configured");
        }
        
        // Entrez Email
        if (entrezEmail == null || entrezEmail.trim().isEmpty() || entrezEmail.equals("your.email@example.com")) {
            validationResults.put("entrez_email", new ValidationResult(
                false, "Entrez email not configured", "WARNING",
                Map.of("key", "app.api.entrez-email", "required", true, "impact", "PubMed/IARC data unavailable")
            ));
            System.out.println("⚠️  Entrez email: Not configured");
        } else {
            validationResults.put("entrez_email", new ValidationResult(
                true, "Entrez email configured", "INFO",
                Map.of("key", "app.api.entrez-email", "configured", true)
            ));
            System.out.println("✅ Entrez email: Configured");
        }
    }
    
    /**
     * Validate database configuration
     */
    private void validateDatabaseConfiguration() {
        System.out.println("🗄️  Validating database configuration...");
        
        // Database URL
        if (databaseUrl == null || databaseUrl.trim().isEmpty()) {
            validationResults.put("database_url", new ValidationResult(
                false, "Database URL not configured", "ERROR",
                Map.of("key", "spring.datasource.url", "required", true, "impact", "Application cannot start")
            ));
            System.out.println("❌ Database URL: Not configured");
        } else {
            validationResults.put("database_url", new ValidationResult(
                true, "Database URL configured", "INFO",
                Map.of("key", "spring.datasource.url", "configured", true, "url", databaseUrl)
            ));
            System.out.println("✅ Database URL: Configured");
        }
        
        // Database Username
        if (databaseUsername == null || databaseUsername.trim().isEmpty()) {
            validationResults.put("database_username", new ValidationResult(
                false, "Database username not configured", "ERROR",
                Map.of("key", "spring.datasource.username", "required", true, "impact", "Database connection failed")
            ));
            System.out.println("❌ Database username: Not configured");
        } else {
            validationResults.put("database_username", new ValidationResult(
                true, "Database username configured", "INFO",
                Map.of("key", "spring.datasource.username", "configured", true)
            ));
            System.out.println("✅ Database username: Configured");
        }
        
        // Database Password
        if (databasePassword == null || databasePassword.trim().isEmpty()) {
            validationResults.put("database_password", new ValidationResult(
                false, "Database password not configured", "ERROR",
                Map.of("key", "spring.datasource.password", "required", true, "impact", "Database connection failed")
            ));
            System.out.println("❌ Database password: Not configured");
        } else {
            validationResults.put("database_password", new ValidationResult(
                true, "Database password configured", "INFO",
                Map.of("key", "spring.datasource.password", "configured", true)
            ));
            System.out.println("✅ Database password: Configured");
        }
    }
    
    /**
     * Validate Redis configuration
     */
    private void validateRedisConfiguration() {
        System.out.println("🔴 Validating Redis configuration...");
        
        // Redis Host
        if (redisHost == null || redisHost.trim().isEmpty()) {
            validationResults.put("redis_host", new ValidationResult(
                false, "Redis host not configured", "WARNING",
                Map.of("key", "spring.redis.host", "required", false, "impact", "Caching disabled")
            ));
            System.out.println("⚠️  Redis host: Not configured (caching disabled)");
        } else {
            validationResults.put("redis_host", new ValidationResult(
                true, "Redis host configured", "INFO",
                Map.of("key", "spring.redis.host", "configured", true, "host", redisHost)
            ));
            System.out.println("✅ Redis host: Configured (" + redisHost + ")");
        }
        
        // Redis Port
        if (redisPort <= 0 || redisPort > 65535) {
            validationResults.put("redis_port", new ValidationResult(
                false, "Redis port invalid", "WARNING",
                Map.of("key", "spring.redis.port", "required", false, "impact", "Caching disabled", "port", redisPort)
            ));
            System.out.println("⚠️  Redis port: Invalid (" + redisPort + ")");
        } else {
            validationResults.put("redis_port", new ValidationResult(
                true, "Redis port configured", "INFO",
                Map.of("key", "spring.redis.port", "configured", true, "port", redisPort)
            ));
            System.out.println("✅ Redis port: Configured (" + redisPort + ")");
        }
    }
    
    /**
     * Validate Ollama configuration
     */
    private void validateOllamaConfiguration() {
        System.out.println("🤖 Validating Ollama configuration...");
        
        // Ollama Base URL
        if (ollamaBaseUrl == null || ollamaBaseUrl.trim().isEmpty()) {
            validationResults.put("ollama_base_url", new ValidationResult(
                false, "Ollama base URL not configured", "WARNING",
                Map.of("key", "app.ollama.base-url", "required", false, "impact", "AI features disabled")
            ));
            System.out.println("⚠️  Ollama base URL: Not configured (AI features disabled)");
        } else {
            validationResults.put("ollama_base_url", new ValidationResult(
                true, "Ollama base URL configured", "INFO",
                Map.of("key", "app.ollama.base-url", "configured", true, "url", ollamaBaseUrl)
            ));
            System.out.println("✅ Ollama base URL: Configured (" + ollamaBaseUrl + ")");
        }
        
        // Ollama Model
        if (ollamaModel == null || ollamaModel.trim().isEmpty()) {
            validationResults.put("ollama_model", new ValidationResult(
                false, "Ollama model not configured", "WARNING",
                Map.of("key", "app.ollama.model", "required", false, "impact", "AI features disabled")
            ));
            System.out.println("⚠️  Ollama model: Not configured");
        } else {
            validationResults.put("ollama_model", new ValidationResult(
                true, "Ollama model configured", "INFO",
                Map.of("key", "app.ollama.model", "configured", true, "model", ollamaModel)
            ));
            System.out.println("✅ Ollama model: Configured (" + ollamaModel + ")");
        }
        
        // Ollama Vision Model
        if (ollamaVisionModel == null || ollamaVisionModel.trim().isEmpty()) {
            validationResults.put("ollama_vision_model", new ValidationResult(
                false, "Ollama vision model not configured", "WARNING",
                Map.of("key", "app.ollama.vision-model", "required", false, "impact", "OCR features disabled")
            ));
            System.out.println("⚠️  Ollama vision model: Not configured");
        } else {
            validationResults.put("ollama_vision_model", new ValidationResult(
                true, "Ollama vision model configured", "INFO",
                Map.of("key", "app.ollama.vision-model", "configured", true, "model", ollamaVisionModel)
            ));
            System.out.println("✅ Ollama vision model: Configured (" + ollamaVisionModel + ")");
        }
    }
    
    /**
     * Validate logging configuration
     */
    private void validateLoggingConfiguration() {
        System.out.println("📝 Validating logging configuration...");
        
        // Log Level
        List<String> validLogLevels = List.of("TRACE", "DEBUG", "INFO", "WARN", "ERROR", "FATAL");
        if (logLevel == null || logLevel.trim().isEmpty() || !validLogLevels.contains(logLevel.toUpperCase())) {
            validationResults.put("log_level", new ValidationResult(
                false, "Invalid log level", "WARNING",
                Map.of("key", "app.logging.level", "required", false, "impact", "Using default log level", "level", logLevel)
            ));
            System.out.println("⚠️  Log level: Invalid (" + logLevel + ")");
        } else {
            validationResults.put("log_level", new ValidationResult(
                true, "Log level configured", "INFO",
                Map.of("key", "app.logging.level", "configured", true, "level", logLevel)
            ));
            System.out.println("✅ Log level: Configured (" + logLevel + ")");
        }
        
        // Backend Log Path
        if (backendLogPath == null || backendLogPath.trim().isEmpty()) {
            validationResults.put("backend_log_path", new ValidationResult(
                false, "Backend log path not configured", "WARNING",
                Map.of("key", "app.logging.backend-path", "required", false, "impact", "Using default log path")
            ));
            System.out.println("⚠️  Backend log path: Not configured");
        } else {
            validationResults.put("backend_log_path", new ValidationResult(
                true, "Backend log path configured", "INFO",
                Map.of("key", "app.logging.backend-path", "configured", true, "path", backendLogPath)
            ));
            System.out.println("✅ Backend log path: Configured (" + backendLogPath + ")");
        }
    }
    
    /**
     * Validate security configuration
     */
    private void validateSecurityConfiguration() {
        System.out.println("🔒 Validating security configuration...");
        
        // Check for security-related properties
        String[] securityProperties = {
            "spring.security.oauth2.client.registration.google.client-id",
            "spring.security.oauth2.client.registration.google.client-secret",
            "jwt.secret",
            "jwt.expiration"
        };
        
        for (String property : securityProperties) {
            String value = environment.getProperty(property);
            if (value == null || value.trim().isEmpty()) {
                validationResults.put("security_" + property.replace(".", "_"), new ValidationResult(
                    false, "Security property not configured", "WARNING",
                    Map.of("key", property, "required", false, "impact", "Security feature disabled")
                ));
                System.out.println("⚠️  " + property + ": Not configured");
            } else {
                validationResults.put("security_" + property.replace(".", "_"), new ValidationResult(
                    true, "Security property configured", "INFO",
                    Map.of("key", property, "configured", true)
                ));
                System.out.println("✅ " + property + ": Configured");
            }
        }
    }
    
    /**
     * Validate performance configuration
     */
    private void validatePerformanceConfiguration() {
        System.out.println("⚡ Validating performance configuration...");
        
        // Check for performance-related properties
        String[] performanceProperties = {
            "spring.jpa.hibernate.ddl-auto",
            "spring.jpa.show-sql",
            "spring.jpa.properties.hibernate.jdbc.batch_size",
            "spring.jpa.properties.hibernate.order_inserts",
            "spring.jpa.properties.hibernate.order_updates"
        };
        
        for (String property : performanceProperties) {
            String value = environment.getProperty(property);
            if (value == null || value.trim().isEmpty()) {
                validationResults.put("performance_" + property.replace(".", "_"), new ValidationResult(
                    false, "Performance property not configured", "INFO",
                    Map.of("key", property, "required", false, "impact", "Using default performance settings")
                ));
                System.out.println("ℹ️  " + property + ": Not configured (using defaults)");
            } else {
                validationResults.put("performance_" + property.replace(".", "_"), new ValidationResult(
                    true, "Performance property configured", "INFO",
                    Map.of("key", property, "configured", true, "value", value)
                ));
                System.out.println("✅ " + property + ": Configured (" + value + ")");
            }
        }
    }
    
    /**
     * Print validation summary
     */
    private void printValidationSummary() {
        System.out.println("\n📊 Environment Validation Summary");
        System.out.println("=".repeat(40));
        
        long totalValidations = validationResults.size();
        long validCount = validationResults.values().stream()
            .mapToLong(result -> result.isValid() ? 1 : 0)
            .sum();
        
        long errorCount = validationResults.values().stream()
            .mapToLong(result -> "ERROR".equals(result.getSeverity()) ? 1 : 0)
            .sum();
        
        long warningCount = validationResults.values().stream()
            .mapToLong(result -> "WARNING".equals(result.getSeverity()) ? 1 : 0)
            .sum();
        
        System.out.println("Total Validations: " + totalValidations);
        System.out.println("Valid: " + validCount);
        System.out.println("Warnings: " + warningCount);
        System.out.println("Errors: " + errorCount);
        
        if (errorCount > 0) {
            System.out.println("\n❌ Critical Issues:");
            validationResults.entrySet().stream()
                .filter(entry -> "ERROR".equals(entry.getValue().getSeverity()))
                .forEach(entry -> {
                    ValidationResult result = entry.getValue();
                    System.out.println("   • " + entry.getKey() + ": " + result.getMessage());
                });
        }
        
        if (warningCount > 0) {
            System.out.println("\n⚠️  Warnings:");
            validationResults.entrySet().stream()
                .filter(entry -> "WARNING".equals(entry.getValue().getSeverity()))
                .forEach(entry -> {
                    ValidationResult result = entry.getValue();
                    System.out.println("   • " + entry.getKey() + ": " + result.getMessage());
                });
        }
        
        if (errorCount == 0) {
            System.out.println("\n🎉 Environment validation passed! Application can start.");
        } else {
            System.out.println("\n❌ Environment validation failed! Please fix critical issues before starting.");
        }
    }
    
    /**
     * Get validation results
     */
    public Map<String, ValidationResult> getValidationResults() {
        return new HashMap<>(validationResults);
    }
    
    /**
     * Check if environment is valid for startup
     */
    public boolean isEnvironmentValid() {
        return validationResults.values().stream()
            .noneMatch(result -> "ERROR".equals(result.getSeverity()));
    }
    
    /**
     * Get critical issues
     */
    public List<ValidationResult> getCriticalIssues() {
        return validationResults.values().stream()
            .filter(result -> "ERROR".equals(result.getSeverity()))
            .collect(Collectors.toList());
    }
    
    /**
     * Get warnings
     */
    public List<ValidationResult> getWarnings() {
        return validationResults.values().stream()
            .filter(result -> "WARNING".equals(result.getSeverity()))
            .collect(Collectors.toList());
    }
}