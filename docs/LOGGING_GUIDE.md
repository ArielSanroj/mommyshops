# Structured Logging Guide

## Overview

This guide covers the comprehensive structured logging implementation for MommyShops, including JSON formatting, secret sanitization, and performance monitoring.

## Architecture

### Python Backend (FastAPI)
- **JSON Formatting**: Structured log entries with metadata
- **Secret Sanitization**: Automatic detection and masking of sensitive data
- **Context Management**: Request-scoped logging context
- **Performance Logging**: Automatic performance metrics

### Java Backend (Spring Boot)
- **SLF4J Integration**: Standard logging framework
- **MDC Support**: Mapped Diagnostic Context for request tracking
- **Secret Sanitization**: Pattern-based secret detection
- **Filter Integration**: Request/response logging filters

## Configuration

### Python Configuration

```python
# Logging settings
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/mommyshops/app.log
SERVICE_NAME=mommyshops
SERVICE_VERSION=1.0.0
ENVIRONMENT=production

# Secret sanitization
SECRET_SANITIZATION_ENABLED=true
SECRET_PATTERNS=password,secret,token,key,auth

# Performance logging
PERFORMANCE_LOGGING_ENABLED=true
PERFORMANCE_THRESHOLD_MS=1000
```

### Java Configuration

```properties
# Logging settings
logging.level.com.mommyshops=INFO
logging.level.org.springframework.web=INFO
logging.level.org.hibernate=WARN
logging.level.org.springframework.security=DEBUG

# Log file
logging.file.name=/var/log/mommyshops/app.log
logging.file.max-size=100MB
logging.file.max-history=30

# Log pattern
logging.pattern.console=%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n
logging.pattern.file=%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n

# Secret sanitization
logging.secret-sanitization.enabled=true
logging.secret-sanitization.patterns=password,secret,token,key,auth
```

## Usage

### Python Usage

#### Basic Logging
```python
from core.logging_config import get_logger, setup_logging

# Setup logging
setup_logging(
    service_name="mommyshops",
    version="1.0.0",
    level="INFO",
    log_file="/var/log/mommyshops/app.log"
)

# Get logger
logger = get_logger(__name__)

# Basic logging
logger.info("Application started")
logger.warning("Deprecated API used")
logger.error("Database connection failed")
```

#### Contextual Logging
```python
# Set context
logger.set_context(
    user_id="12345",
    request_id="req-abc-123",
    session_id="sess-xyz-789"
)

# Log with context
logger.info("User action performed", action="login", duration_ms=150)
```

#### Performance Logging
```python
from core.logging_config import log_performance, log_async_performance

@log_performance
def process_data(data):
    # Processing logic
    return result

@log_async_performance
async def async_process_data(data):
    # Async processing logic
    return result
```

#### Error Logging
```python
try:
    result = risky_operation()
except Exception as e:
    logger.log_error(e, error_code="RISKY_OP_FAILED", operation="data_processing")
```

#### Request Logging
```python
# Log HTTP request
logger.log_request(
    method="POST",
    url="/api/analysis",
    status_code=200,
    duration_ms=250,
    user_id="12345"
)
```

### Java Usage

#### Basic Logging
```java
import com.mommyshops.config.LoggingConfig.StructuredLogger;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@RestController
public class AnalysisController {
    
    private static final Logger logger = LoggerFactory.getLogger(AnalysisController.class);
    private final StructuredLogger structuredLogger = new StructuredLogger(AnalysisController.class);
    
    @PostMapping("/api/analysis")
    public ResponseEntity<AnalysisResult> analyzeProduct(@RequestBody ProductRequest request) {
        structuredLogger.info("Starting product analysis for user: {}", request.getUserId());
        
        try {
            AnalysisResult result = analysisService.analyze(request);
            structuredLogger.info("Product analysis completed successfully");
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            structuredLogger.logError("Product analysis failed", e);
            return ResponseEntity.status(500).body(null);
        }
    }
}
```

#### Contextual Logging
```java
import org.slf4j.MDC;

@RestController
public class UserController {
    
    private static final Logger logger = LoggerFactory.getLogger(UserController.class);
    
    @GetMapping("/api/user/{id}")
    public ResponseEntity<User> getUser(@PathVariable String id) {
        // Set context
        MDC.put("userId", id);
        MDC.put("requestId", UUID.randomUUID().toString());
        
        try {
            User user = userService.findById(id);
            logger.info("User retrieved successfully: {}", user.getEmail());
            return ResponseEntity.ok(user);
        } finally {
            // Clear context
            MDC.clear();
        }
    }
}
```

#### Performance Logging
```java
@Service
public class AnalysisService {
    
    private static final Logger logger = LoggerFactory.getLogger(AnalysisService.class);
    
    public AnalysisResult analyze(ProductRequest request) {
        long startTime = System.currentTimeMillis();
        
        try {
            // Analysis logic
            AnalysisResult result = performAnalysis(request);
            
            long duration = System.currentTimeMillis() - startTime;
            logger.info("Analysis completed in {}ms", duration);
            
            return result;
        } catch (Exception e) {
            long duration = System.currentTimeMillis() - startTime;
            logger.error("Analysis failed after {}ms", duration, e);
            throw e;
        }
    }
}
```

## Secret Sanitization

### Python Implementation
```python
from core.logging_config import SecretSanitizer

sanitizer = SecretSanitizer()

# Sanitize data
data = {
    "username": "john_doe",
    "password": "secret123",
    "api_key": "sk-1234567890",
    "token": "bearer_abc123"
}

sanitized_data = sanitizer.sanitize(data)
# Result: {"username": "john_doe", "password": "***", "api_key": "***", "token": "***"}
```

### Java Implementation
```java
import com.mommyshops.config.LoggingConfig.SecretSanitizer;

String logMessage = "User login with password=secret123 and token=bearer_abc123";
String sanitized = SecretSanitizer.sanitize(logMessage);
// Result: "User login with password=\"***\" and token=\"***\""
```

## Log Entry Structure

### Python Log Entry
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "mommyshops.api.routes.analysis",
  "message": "Product analysis completed",
  "service": "mommyshops",
  "version": "1.0.0",
  "environment": "production",
  "request_id": "req-abc-123",
  "user_id": "12345",
  "session_id": "sess-xyz-789",
  "correlation_id": "corr-def-456",
  "duration_ms": 250.5,
  "status_code": 200,
  "method": "POST",
  "url": "/api/analysis",
  "user_agent": "Mozilla/5.0...",
  "ip_address": "192.168.1.100",
  "metadata": {
    "product_id": "prod-123",
    "analysis_type": "ingredient_analysis"
  }
}
```

### Java Log Entry
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "com.mommyshops.controller.AnalysisController",
  "message": "Product analysis completed successfully",
  "request_id": "req-abc-123",
  "user_id": "12345",
  "duration_ms": 250,
  "status_code": 200,
  "method": "POST",
  "url": "/api/analysis"
}
```

## Monitoring and Alerting

### Log Aggregation
- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **Fluentd**: Log collection and forwarding
- **Prometheus**: Metrics collection
- **Grafana**: Visualization and alerting

### Alert Rules
```yaml
# Prometheus alert rules
groups:
  - name: logging
    rules:
      - alert: HighErrorRate
        expr: rate(log_entries{level="ERROR"}[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          
      - alert: SlowResponse
        expr: histogram_quantile(0.95, rate(duration_ms_bucket[5m])) > 5000
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Slow response times detected"
```

### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "MommyShops Logging Dashboard",
    "panels": [
      {
        "title": "Log Levels",
        "type": "stat",
        "targets": [
          {
            "expr": "sum by (level) (rate(log_entries[5m]))"
          }
        ]
      },
      {
        "title": "Response Times",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(duration_ms_bucket[5m]))"
          }
        ]
      }
    ]
  }
}
```

## Best Practices

### 1. Log Levels
- **DEBUG**: Detailed information for debugging
- **INFO**: General information about application flow
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for recoverable errors
- **CRITICAL**: Critical errors that require immediate attention

### 2. Structured Logging
- Use consistent field names
- Include relevant context
- Avoid logging sensitive data
- Use appropriate log levels

### 3. Performance Considerations
- Avoid expensive operations in logging
- Use async logging for high-throughput applications
- Implement log rotation
- Monitor log file sizes

### 4. Security
- Sanitize sensitive data
- Implement log access controls
- Use secure log transmission
- Regular log review

### 5. Monitoring
- Set up log aggregation
- Implement alerting
- Monitor log volume
- Track error rates

## Troubleshooting

### Common Issues

1. **High Log Volume**
   - Adjust log levels
   - Implement log filtering
   - Use async logging
   - Optimize log messages

2. **Missing Context**
   - Ensure MDC is set
   - Check context propagation
   - Verify request tracking
   - Review log configuration

3. **Performance Impact**
   - Use async logging
   - Optimize log messages
   - Implement log sampling
   - Monitor log file I/O

### Debugging

1. **Enable Debug Logging**
   ```python
   # Python
   setup_logging(level="DEBUG")
   ```

   ```properties
   # Java
   logging.level.com.mommyshops=DEBUG
   ```

2. **Check Log Configuration**
   ```python
   # Python
   import logging
   logging.getLogger().setLevel(logging.DEBUG)
   ```

   ```java
   // Java
   Logger logger = LoggerFactory.getLogger(YourClass.class);
   logger.debug("Debug message");
   ```

3. **Verify Secret Sanitization**
   ```python
   # Python
   sanitizer = SecretSanitizer()
   test_data = {"password": "secret123"}
   result = sanitizer.sanitize(test_data)
   print(result)  # Should show "***"
   ```

## Conclusion

This structured logging implementation provides comprehensive logging capabilities with secret sanitization, performance monitoring, and contextual information. Regular monitoring and maintenance ensure optimal logging performance and security.
