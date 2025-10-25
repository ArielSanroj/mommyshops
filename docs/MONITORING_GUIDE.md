# MommyShops Monitoring Guide

## 🚀 Overview

The MommyShops project implements comprehensive monitoring and observability using Prometheus metrics, Grafana dashboards, and health checks. This guide covers the complete monitoring strategy for both Python and Java backends.

## 🏗️ Monitoring Architecture

### Components

1. **Prometheus**: Metrics collection and storage
2. **Grafana**: Visualization and dashboards
3. **Python Backend**: Metrics collection via prometheus_client
4. **Java Backend**: Metrics collection via Micrometer
5. **Health Checks**: Application health monitoring
6. **Alerting**: Automated alerting via Grafana

### Metrics Flow

```
Python Backend → Prometheus → Grafana
Java Backend   → Prometheus → Grafana
Health Checks  → Prometheus → Grafana
```

## 📊 Metrics Categories

### 1. HTTP Request Metrics

#### Python Metrics
```python
# HTTP request counter
http_requests_total{method="GET", endpoint="/health", status_code="200"}

# HTTP request duration histogram
http_request_duration_seconds{method="GET", endpoint="/health"}
```

#### Java Metrics
```java
// HTTP request counter
http_requests_total{method="GET", endpoint="/api/health", status_code="200"}

// HTTP request duration timer
http_request_duration_seconds{method="GET", endpoint="/api/health"}
```

### 2. Analysis Metrics

#### Python Metrics
```python
# Analysis requests counter
analysis_requests_total{analysis_type="image", user_need="sensitive skin"}

# Analysis duration histogram
analysis_duration_seconds{analysis_type="image"}

# Analysis success rate gauge
analysis_success_rate{analysis_type="image"}
```

#### Java Metrics
```java
// Analysis requests counter
analysis_requests_total{analysis_type="text", user_need="sensitive skin"}

// Analysis duration timer
analysis_duration_seconds{analysis_type="text"}

// Analysis success rate gauge
analysis_success_rate{analysis_type="text"}
```

### 3. Ingredient Metrics

#### Python Metrics
```python
# Ingredient analysis counter
ingredient_analysis_total{ingredient_name="Hyaluronic Acid", risk_level="low"}

# Ingredient eco score histogram
ingredient_eco_score{ingredient_name="Hyaluronic Acid"}
```

#### Java Metrics
```java
// Ingredient analysis counter
ingredient_analysis_total{ingredient_name="Hyaluronic Acid", risk_level="low"}

// Ingredient eco score histogram
ingredient_eco_score{ingredient_name="Hyaluronic Acid"}
```

### 4. Cache Metrics

#### Python Metrics
```python
# Cache operations counter
cache_operations_total{operation="get", cache_level="l1", result="hit"}

# Cache hit rate gauge
cache_hit_rate{cache_level="l1"}

# Cache size gauge
cache_size{cache_level="l1"}
```

#### Java Metrics
```java
// Cache operations counter
cache_operations_total{operation="get", cache_level="l1", result="hit"}

// Cache hit rate gauge
cache_hit_rate{cache_level="l1"}

// Cache size gauge
cache_size{cache_level="l1"}
```

### 5. External API Metrics

#### Python Metrics
```python
# External API requests counter
external_api_requests_total{api_name="ewg", endpoint="/ingredient", status="success"}

# External API duration histogram
external_api_duration_seconds{api_name="ewg", endpoint="/ingredient"}
```

#### Java Metrics
```java
// External API requests counter
external_api_requests_total{api_name="ewg", endpoint="/ingredient", status="success"}

// External API duration timer
external_api_duration_seconds{api_name="ewg", endpoint="/ingredient"}
```

### 6. OCR Metrics

#### Python Metrics
```python
# OCR requests counter
ocr_requests_total{image_type="jpg", status="success"}

# OCR duration histogram
ocr_duration_seconds{image_type="jpg"}

# OCR confidence histogram
ocr_confidence{image_type="jpg"}
```

#### Java Metrics
```java
// OCR requests counter
ocr_requests_total{image_type="jpg", status="success"}

// OCR duration timer
ocr_duration_seconds{image_type="jpg"}

// OCR confidence histogram
ocr_confidence{image_type="jpg"}
```

### 7. Ollama AI Metrics

#### Python Metrics
```python
# Ollama requests counter
ollama_requests_total{model="llama3.2", operation="analyze", status="success"}

# Ollama duration histogram
ollama_duration_seconds{model="llama3.2", operation="analyze"}
```

#### Java Metrics
```java
// Ollama requests counter
ollama_requests_total{model="llama3.2", operation="analyze", status="success"}

// Ollama duration timer
ollama_duration_seconds{model="llama3.2", operation="analyze"}
```

### 8. Database Metrics

#### Python Metrics
```python
# Database queries counter
database_queries_total{operation="select", table="ingredients", status="success"}

# Database duration histogram
database_duration_seconds{operation="select", table="ingredients"}
```

#### Java Metrics
```java
// Database queries counter
database_queries_total{operation="select", table="ingredients", status="success"}

// Database duration timer
database_duration_seconds{operation="select", table="ingredients"}
```

### 9. System Metrics

#### Python Metrics
```python
# Memory usage gauge
memory_usage_bytes{type="heap"}

# CPU usage gauge
cpu_usage_percent

# Active connections gauge
active_connections{connection_type="http"}
```

#### Java Metrics
```java
// Memory usage gauge
memory_usage_bytes{type="heap"}

// CPU usage gauge
cpu_usage_percent

// Active connections gauge
active_connections{connection_type="http"}
```

### 10. Error Metrics

#### Python Metrics
```python
# Errors counter
errors_total{error_type="validation", component="analysis", severity="warning"}
```

#### Java Metrics
```java
// Errors counter
errors_total{error_type="validation", component="analysis", severity="warning"}
```

### 11. Business Metrics

#### Python Metrics
```python
# Users total gauge
users_total

# Products analyzed counter
products_analyzed_total{analysis_type="all"}

# Ingredients analyzed counter
ingredients_analyzed_total
```

#### Java Metrics
```java
// Users total gauge
users_total

// Products analyzed counter
products_analyzed_total{analysis_type="all"}

// Ingredients analyzed counter
ingredients_analyzed_total
```

## 🔧 Configuration

### Python Configuration

```python
# core/metrics.py
@dataclass
class MetricConfig:
    enabled: bool = True
    prometheus_enabled: bool = True
    pushgateway_enabled: bool = False
    pushgateway_url: str = "http://localhost:9091"
    pushgateway_job: str = "mommyshops"
    push_interval: int = 60  # seconds
    http_server_port: int = 8001
    http_server_enabled: bool = True
```

### Java Configuration

```yaml
# application.yml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus
  endpoint:
    health:
      show-details: always
  metrics:
    export:
      prometheus:
        enabled: true
    distribution:
      percentiles:
        http_request_duration_seconds: 0.5, 0.95, 0.99
        analysis_duration_seconds: 0.5, 0.95, 0.99
        cache_duration_seconds: 0.5, 0.95, 0.99
```

## 📈 Grafana Dashboards

### 1. MommyShops Overview Dashboard

**Purpose**: High-level overview of system health and performance

**Panels**:
- HTTP Requests Rate
- HTTP Request Duration (50th, 95th, 99th percentiles)
- Analysis Requests
- Analysis Success Rate
- Cache Hit Rate
- Cache Size
- External API Requests
- Error Rate
- System Resources (Memory, CPU)

### 2. Analysis Performance Dashboard

**Purpose**: Detailed analysis performance monitoring

**Panels**:
- Analysis Requests by Type
- Analysis Duration by Type
- Analysis Success Rate by Type
- Ingredient Analysis Count
- Ingredient Eco Score Distribution
- OCR Performance
- Ollama AI Performance

### 3. Cache Performance Dashboard

**Purpose**: Cache performance and efficiency monitoring

**Panels**:
- Cache Hit Rate by Level
- Cache Size by Level
- Cache Operations by Type
- Cache Eviction Rate
- Cache Memory Usage
- Cache Response Time

### 4. External API Dashboard

**Purpose**: External API performance and reliability monitoring

**Panels**:
- API Request Rate by Service
- API Response Time by Service
- API Success Rate by Service
- API Error Rate by Service
- API Timeout Rate by Service
- API Circuit Breaker Status

### 5. System Health Dashboard

**Purpose**: System health and resource monitoring

**Panels**:
- Memory Usage
- CPU Usage
- Disk Usage
- Network I/O
- Active Connections
- Database Connections
- Redis Connections

## 🚨 Alerting Rules

### 1. High Error Rate Alert

```yaml
# prometheus/alerts.yml
- alert: HighErrorRate
  expr: rate(errors_total[5m]) > 0.1
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "High error rate detected"
    description: "Error rate is {{ $value }} errors per second"
```

### 2. High Response Time Alert

```yaml
- alert: HighResponseTime
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 5
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "High response time detected"
    description: "95th percentile response time is {{ $value }} seconds"
```

### 3. Low Cache Hit Rate Alert

```yaml
- alert: LowCacheHitRate
  expr: cache_hit_rate < 0.8
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Low cache hit rate detected"
    description: "Cache hit rate is {{ $value }}%"
```

### 4. High Memory Usage Alert

```yaml
- alert: HighMemoryUsage
  expr: memory_usage_bytes / 1024 / 1024 / 1024 > 4
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "High memory usage detected"
    description: "Memory usage is {{ $value }} GB"
```

### 5. Service Down Alert

```yaml
- alert: ServiceDown
  expr: up == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Service is down"
    description: "Service {{ $labels.instance }} is down"
```

## 🔍 Health Checks

### Python Health Checks

```python
# core/health.py
def check_health() -> Dict[str, Any]:
    """Check system health"""
    health = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time() - start_time,
        "components": {}
    }
    
    # Check database
    try:
        db.session.execute("SELECT 1")
        health["components"]["database"] = "healthy"
    except Exception:
        health["components"]["database"] = "unhealthy"
    
    # Check Redis
    try:
        redis_client.ping()
        health["components"]["redis"] = "healthy"
    except Exception:
        health["components"]["redis"] = "unhealthy"
    
    # Check external APIs
    try:
        # Check EWG API
        response = requests.get("https://www.ewg.org/api", timeout=5)
        health["components"]["ewg_api"] = "healthy" if response.status_code == 200 else "degraded"
    except Exception:
        health["components"]["ewg_api"] = "unhealthy"
    
    return health
```

### Java Health Checks

```java
// HealthCheckController.java
@GetMapping("/api/health")
public ResponseEntity<Map<String, Object>> getHealth() {
    Map<String, Object> health = new HashMap<>();
    health.put("status", "healthy");
    health.put("timestamp", Instant.now().toString());
    health.put("uptime", Duration.between(startTime, Instant.now()).toString());
    
    Map<String, String> components = new HashMap<>();
    
    // Check database
    try {
        jdbcTemplate.queryForObject("SELECT 1", Integer.class);
        components.put("database", "healthy");
    } catch (Exception e) {
        components.put("database", "unhealthy");
    }
    
    // Check Redis
    try {
        redisTemplate.opsForValue().get("health_check");
        components.put("redis", "healthy");
    } catch (Exception e) {
        components.put("redis", "unhealthy");
    }
    
    // Check Python backend
    try {
        pythonBackendClient.checkHealth().block();
        components.put("python_backend", "healthy");
    } catch (Exception e) {
        components.put("python_backend", "unhealthy");
    }
    
    health.put("components", components);
    return ResponseEntity.ok(health);
}
```

## 📊 Monitoring Queries

### Prometheus Queries

#### 1. Request Rate
```promql
rate(http_requests_total[5m])
```

#### 2. Response Time Percentiles
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

#### 3. Error Rate
```promql
rate(errors_total[5m])
```

#### 4. Cache Hit Rate
```promql
cache_hit_rate
```

#### 5. Analysis Success Rate
```promql
analysis_success_rate
```

#### 6. Memory Usage
```promql
memory_usage_bytes
```

#### 7. CPU Usage
```promql
cpu_usage_percent
```

#### 8. Active Connections
```promql
active_connections
```

#### 9. Database Query Rate
```promql
rate(database_queries_total[5m])
```

#### 10. External API Success Rate
```promql
rate(external_api_requests_total{status="success"}[5m]) / rate(external_api_requests_total[5m])
```

## 🛠️ Setup Instructions

### 1. Install Dependencies

#### Python
```bash
pip install prometheus-client
```

#### Java
```xml
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-registry-prometheus</artifactId>
</dependency>
```

### 2. Configure Prometheus

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'mommyshops-python'
    static_configs:
      - targets: ['localhost:8001']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'mommyshops-java'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/actuator/prometheus'
    scrape_interval: 15s
```

### 3. Configure Grafana

```yaml
# grafana.ini
[server]
http_port = 3000

[security]
admin_user = admin
admin_password = admin

[datasources]
[[datasources]]
name = Prometheus
type = prometheus
url = http://localhost:9090
access = proxy
```

### 4. Start Services

```bash
# Start Prometheus
prometheus --config.file=prometheus.yml

# Start Grafana
grafana-server

# Start Python backend with metrics
python -m backend-python.main

# Start Java backend with metrics
java -jar backend-java.jar
```

## 📈 Performance Optimization

### 1. Metrics Collection Optimization

```python
# Python - Optimize metrics collection
def optimize_metrics_collection():
    # Use batch collection for high-frequency metrics
    batch_size = 100
    metrics_buffer = []
    
    def collect_metric(metric_name, value, labels):
        metrics_buffer.append((metric_name, value, labels))
        if len(metrics_buffer) >= batch_size:
            flush_metrics()
    
    def flush_metrics():
        # Batch process metrics
        for metric_name, value, labels in metrics_buffer:
            record_metric(metric_name, value, labels)
        metrics_buffer.clear()
```

### 2. Dashboard Optimization

```json
// Grafana dashboard optimization
{
  "refresh": "30s",
  "time": {
    "from": "now-1h",
    "to": "now"
  },
  "panels": [
    {
      "targets": [
        {
          "expr": "rate(http_requests_total[5m])",
          "interval": "30s"
        }
      ]
    }
  ]
}
```

### 3. Alerting Optimization

```yaml
# Prometheus alerting optimization
global:
  evaluation_interval: 30s

rule_files:
  - "alerts.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - localhost:9093
```

## 🔍 Troubleshooting

### Common Issues

1. **Metrics Not Appearing**
   - Check Prometheus configuration
   - Verify service endpoints
   - Check firewall settings

2. **High Memory Usage**
   - Reduce metrics collection frequency
   - Use metric sampling
   - Implement metric aggregation

3. **Dashboard Performance**
   - Optimize queries
   - Use time ranges
   - Implement caching

4. **Alert Fatigue**
   - Tune alert thresholds
   - Use alert grouping
   - Implement alert suppression

### Debug Commands

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check metrics endpoint
curl http://localhost:8001/metrics

# Check Grafana health
curl http://localhost:3000/api/health

# Check service health
curl http://localhost:8000/health
curl http://localhost:8080/api/health
```

## 📚 Best Practices

### 1. Metric Naming
- Use descriptive names
- Follow naming conventions
- Use consistent labels

### 2. Dashboard Design
- Keep dashboards focused
- Use appropriate visualizations
- Include context and thresholds

### 3. Alerting
- Set appropriate thresholds
- Use alert grouping
- Implement escalation policies

### 4. Performance
- Monitor metrics collection overhead
- Use sampling for high-frequency metrics
- Implement metric aggregation

### 5. Security
- Secure metrics endpoints
- Use authentication
- Implement access controls

---

**Last Updated**: December 2024  
**Version**: 3.0.1  
**Maintainer**: CTO Team
