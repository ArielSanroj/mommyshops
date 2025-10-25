# MommyShops API Reference

## 🚀 Overview

The MommyShops API provides comprehensive ingredient analysis and product safety evaluation services. This API is designed to help users make informed decisions about cosmetic and personal care products.

## 🔗 Base URLs

- **Development**: `http://localhost:8000` (Python) / `http://localhost:8080` (Java)
- **Production**: `https://api.mommyshops.com`

## 🔐 Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## 📊 Rate Limiting

- **Standard**: 60 requests per minute
- **Analysis**: 5 requests per minute (slower due to AI processing)
- **Burst**: 10 requests per minute

## 🚨 Error Handling

All endpoints return standardized error responses:

```json
{
    "success": false,
    "error": "Error message",
    "error_code": "ERROR_CODE",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

## 📋 Endpoints

### Python Backend (Port 8000)

#### Analysis Endpoints

##### POST `/analyze-image`
Analyze product ingredients from an uploaded image.

**Request**:
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `file` (file, required): Product image file (JPG, PNG, WebP, max 5MB)
  - `user_need` (string, optional): User's skin type or concern

**Response**:
```json
{
    "success": true,
    "product_name": "Anti-Aging Serum",
    "ingredients_details": [
        {
            "name": "Hyaluronic Acid",
            "risk_level": "low",
            "eco_score": 85.0,
            "benefits": "Hydrating, plumping",
            "risks_detailed": "None known",
            "sources": "EWG, FDA"
        }
    ],
    "avg_eco_score": 85.0,
    "suitability": "excellent",
    "recommendations": "This product is excellent for sensitive skin",
    "analysis_id": "analysis_123",
    "processing_time_ms": 1500
}
```

##### POST `/analyze-text`
Analyze product ingredients from text input.

**Request**:
```json
{
    "text": "Aqua, Glycerin, Hyaluronic Acid, Niacinamide",
    "user_need": "sensitive skin"
}
```

**Response**: Same as `/analyze-image`

##### POST `/ingredients/analyze`
Analyze a list of specific ingredients.

**Request**:
```json
{
    "ingredients": ["Hyaluronic Acid", "Niacinamide", "Retinol"],
    "user_need": "sensitive skin"
}
```

**Response**: Same as `/analyze-image`

#### Health Endpoints

##### GET `/health`
System health check.

**Response**:
```json
{
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00Z",
    "service": "python-backend",
    "version": "3.0.1",
    "components": {
        "database": "healthy",
        "ollama": "healthy",
        "external_apis": "healthy"
    }
}
```

##### GET `/java/health`
Health check optimized for Java integration.

**Response**: Same as `/health`

#### Ollama AI Endpoints

##### GET `/ollama/status`
Check Ollama AI service status.

**Response**:
```json
{
    "available": true,
    "model": "llama3.2",
    "version": "0.1.0"
}
```

##### POST `/ollama/analyze`
Analyze ingredients using AI.

**Request**:
```json
{
    "ingredients": ["Hyaluronic Acid", "Niacinamide"],
    "user_conditions": ["sensitive skin"]
}
```

**Response**:
```json
{
    "success": true,
    "content": "AI analysis result",
    "alternatives": ["Alternative 1", "Alternative 2"]
}
```

##### POST `/ollama/alternatives`
Get AI-powered ingredient alternatives.

**Request**:
```json
{
    "problematic_ingredients": ["Sodium Lauryl Sulfate", "Parabens"],
    "user_conditions": ["sensitive skin", "eczema"]
}
```

**Response**:
```json
[
    "Alternative 1",
    "Alternative 2",
    "Alternative 3"
]
```

### Java Backend (Port 8080)

#### Analysis Endpoints

##### POST `/api/analysis/analyze-product`
Analyze product from text (calls Python backend).

**Request**:
```json
{
    "text": "Aqua, Glycerin, Hyaluronic Acid, Niacinamide",
    "user_need": "sensitive skin"
}
```

**Response**: Same as Python `/analyze-text`

##### POST `/api/analysis/analyze-image`
Analyze product from image (calls Python backend).

**Request**: Same as Python `/analyze-image`

**Response**: Same as Python `/analyze-image`

#### Substitution Endpoints

##### POST `/api/substitution/analyze`
Analyze ingredients for substitution.

**Request**:
```json
{
    "ingredients": ["Sodium Lauryl Sulfate", "Parabens"],
    "user_conditions": ["sensitive skin"]
}
```

**Response**:
```json
{
    "success": true,
    "analysis_id": "sub_123",
    "problematic_ingredients": [
        {
            "name": "Sodium Lauryl Sulfate",
            "risk_level": "high",
            "alternatives": ["Sodium Lauryl Sulfoacetate", "Cocamidopropyl Betaine"]
        }
    ],
    "recommendations": "Consider alternatives for sensitive skin"
}
```

##### POST `/api/substitution/alternatives`
Get ingredient alternatives.

**Request**:
```json
{
    "problematic_ingredients": ["Sodium Lauryl Sulfate", "Parabens"],
    "user_conditions": ["sensitive skin", "eczema"]
}
```

**Response**:
```json
[
    "Sodium Lauryl Sulfoacetate",
    "Cocamidopropyl Betaine",
    "Decyl Glucoside"
]
```

##### POST `/api/substitution/batch-analyze`
Batch analyze multiple ingredients.

**Request**:
```json
{
    "ingredients_lists": [
        ["Ingredient 1", "Ingredient 2"],
        ["Ingredient 3", "Ingredient 4"]
    ],
    "user_conditions": ["sensitive skin"]
}
```

**Response**:
```json
[
    {
        "success": true,
        "ingredients": ["Ingredient 1", "Ingredient 2"],
        "analysis": "Analysis result"
    },
    {
        "success": true,
        "ingredients": ["Ingredient 3", "Ingredient 4"],
        "analysis": "Analysis result"
    }
]
```

##### POST `/api/substitution/enhance-recommendations`
Enhance recommendations using AI.

**Request**:
```json
{
    "ingredients": ["Sodium Lauryl Sulfate", "Parabens"],
    "user_conditions": ["sensitive skin"],
    "preferences": ["natural", "organic"]
}
```

**Response**:
```json
{
    "success": true,
    "enhanced_recommendations": [
        {
            "ingredient": "Sodium Lauryl Sulfate",
            "alternatives": [
                {
                    "name": "Sodium Lauryl Sulfoacetate",
                    "reason": "Gentler for sensitive skin",
                    "eco_score": 85.0
                }
            ]
        }
    ]
}
```

##### POST `/api/substitution/quick-substitute`
Quick substitution lookup.

**Request**:
```json
{
    "ingredient": "Sodium Lauryl Sulfate",
    "user_conditions": ["sensitive skin"],
    "max_substitutes": 5
}
```

**Response**:
```json
{
    "success": true,
    "ingredient": "Sodium Lauryl Sulfate",
    "alternatives": [
        "Sodium Lauryl Sulfoacetate",
        "Cocamidopropyl Betaine",
        "Decyl Glucoside"
    ]
}
```

##### POST `/api/substitution/integrate-with-routine-analysis`
Integrate substitution with routine analysis.

**Request**:
```json
{
    "routine_data": {
        "morning": ["Product 1", "Product 2"],
        "evening": ["Product 3", "Product 4"]
    },
    "user_conditions": ["sensitive skin"]
}
```

**Response**:
```json
{
    "success": true,
    "routine_analysis": {
        "morning": {
            "products": ["Product 1", "Product 2"],
            "suitability": "good",
            "recommendations": "Consider alternatives for sensitive skin"
        },
        "evening": {
            "products": ["Product 3", "Product 4"],
            "suitability": "excellent",
            "recommendations": "Perfect for sensitive skin"
        }
    }
}
```

#### Health Endpoints

##### GET `/api/health`
Comprehensive system health check.

**Response**:
```json
{
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00Z",
    "service": "java-backend",
    "version": "3.0.1",
    "components": {
        "database": "healthy",
        "python_backend": "healthy",
        "redis": "healthy",
        "external_apis": "healthy"
    },
    "metrics": {
        "uptime": "7d 12h 30m",
        "memory_usage": "45%",
        "cpu_usage": "23%"
    }
}
```

##### GET `/api/health/quick`
Quick health check.

**Response**:
```json
{
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

##### GET `/api/health/detailed`
Detailed health check with metrics.

**Response**:
```json
{
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00Z",
    "components": {
        "database": {
            "status": "healthy",
            "response_time_ms": 15,
            "connections": 5
        },
        "python_backend": {
            "status": "healthy",
            "response_time_ms": 120,
            "version": "3.0.1"
        },
        "redis": {
            "status": "healthy",
            "response_time_ms": 8,
            "memory_usage": "32%"
        }
    },
    "metrics": {
        "uptime": "7d 12h 30m",
        "memory_usage": "45%",
        "cpu_usage": "23%",
        "request_count": 1250,
        "error_rate": "0.2%"
    }
}
```

##### GET `/api/health/component/{component}`
Check specific component health.

**Parameters**:
- `component`: Component name (database, python_backend, redis, external_apis)

**Response**:
```json
{
    "component": "database",
    "status": "healthy",
    "response_time_ms": 15,
    "connections": 5,
    "last_check": "2024-01-01T00:00:00Z"
}
```

##### GET `/api/health/environment`
Environment information.

**Response**:
```json
{
    "environment": "production",
    "version": "3.0.1",
    "java_version": "17.0.2",
    "spring_version": "3.0.1",
    "build_time": "2024-01-01T00:00:00Z"
}
```

##### GET `/api/health/apis`
External API health status.

**Response**:
```json
{
    "external_apis": {
        "ewg": "healthy",
        "fda": "healthy",
        "cosing": "healthy",
        "pubchem": "healthy"
    },
    "last_check": "2024-01-01T00:00:00Z"
}
```

##### GET `/api/health/cache`
Cache health status.

**Response**:
```json
{
    "cache": {
        "redis": "healthy",
        "hit_rate": "85%",
        "memory_usage": "32%"
    },
    "last_check": "2024-01-01T00:00:00Z"
}
```

##### GET `/api/health/logging`
Logging system health.

**Response**:
```json
{
    "logging": {
        "status": "healthy",
        "log_level": "INFO",
        "log_files": ["application.log", "error.log"],
        "disk_usage": "15%"
    },
    "last_check": "2024-01-01T00:00:00Z"
}
```

##### POST `/api/health/cache/clear`
Clear cache.

**Response**:
```json
{
    "success": true,
    "message": "Cache cleared successfully",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

##### GET `/api/health/info`
System information.

**Response**:
```json
{
    "system": {
        "os": "Linux",
        "architecture": "x86_64",
        "java_version": "17.0.2",
        "spring_version": "3.0.1",
        "memory": {
            "total": "8GB",
            "used": "3.6GB",
            "free": "4.4GB"
        },
        "disk": {
            "total": "100GB",
            "used": "45GB",
            "free": "55GB"
        }
    },
    "application": {
        "name": "MommyShops",
        "version": "3.0.1",
        "build_time": "2024-01-01T00:00:00Z",
        "uptime": "7d 12h 30m"
    }
}
```

#### Ollama AI Endpoints

##### GET `/api/ollama/health`
Ollama AI service health.

**Response**:
```json
{
    "status": "healthy",
    "available": true,
    "model": "llama3.2",
    "version": "0.1.0",
    "response_time_ms": 45
}
```

##### GET `/api/ollama/models`
Available AI models.

**Response**:
```json
{
    "models": [
        {
            "name": "llama3.2",
            "version": "0.1.0",
            "size": "7B",
            "status": "available"
        }
    ],
    "default_model": "llama3.2"
}
```

## 🔧 Integration Examples

### Python to Java Communication

```python
import requests

# Analyze product through Java backend
response = requests.post(
    "http://localhost:8080/api/analysis/analyze-product",
    json={
        "text": "Aqua, Glycerin, Hyaluronic Acid, Niacinamide",
        "user_need": "sensitive skin"
    }
)

result = response.json()
print(f"Analysis success: {result['success']}")
print(f"Eco score: {result['avg_eco_score']}")
```

### Java to Python Communication

```java
@Autowired
private PythonBackendClient pythonBackendClient;

public Mono<ProductAnalysisResponse> analyzeProduct(String text, String userNeed) {
    return pythonBackendClient.analyzeText(text, userNeed)
        .doOnSuccess(response -> log.info("Analysis completed: {}", response.isSuccess()))
        .doOnError(error -> log.error("Analysis failed: {}", error.getMessage()));
}
```

## 📊 Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Rate Limit Exceeded |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

## 🔍 Error Codes

| Code | Description |
|------|-------------|
| INVALID_INPUT | Invalid input data |
| FILE_TOO_LARGE | File size exceeds limit |
| INVALID_IMAGE | Invalid image format |
| RATE_LIMIT_EXCEEDED | Rate limit exceeded |
| SERVICE_UNAVAILABLE | Service temporarily unavailable |
| AUTHENTICATION_FAILED | Authentication failed |
| AUTHORIZATION_FAILED | Authorization failed |

## 📈 Monitoring

### Health Checks
- **Java**: `GET /api/health`
- **Python**: `GET /health`
- **Integration**: `GET /api/health/detailed`

### Metrics
- **Request Rate**: Requests per minute
- **Response Time**: Average response time
- **Error Rate**: Percentage of failed requests
- **Uptime**: Service availability

### Logging
- **Level**: INFO, WARN, ERROR
- **Format**: JSON structured logging
- **Retention**: 30 days
- **Rotation**: Daily

## 🚀 Getting Started

### 1. Authentication
```bash
# Get JWT token
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

### 2. Analyze Product
```bash
# Analyze text
curl -X POST http://localhost:8080/api/analysis/analyze-product \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{"text": "Aqua, Glycerin, Hyaluronic Acid", "user_need": "sensitive skin"}'
```

### 3. Check Health
```bash
# Check system health
curl http://localhost:8080/api/health
```

## 📚 SDKs and Libraries

### Python
```bash
pip install mommyshops-api
```

### Java
```xml
<dependency>
    <groupId>com.mommyshops</groupId>
    <artifactId>api-client</artifactId>
    <version>3.0.1</version>
</dependency>
```

### JavaScript
```bash
npm install @mommyshops/api-client
```

## 🆘 Support

- **Email**: support@mommyshops.com
- **Documentation**: https://docs.mommyshops.com
- **Status**: https://status.mommyshops.com
- **GitHub**: https://github.com/mommyshops/api

---

**Last Updated**: December 2024  
**Version**: 3.0.1  
**Maintainer**: CTO Team
