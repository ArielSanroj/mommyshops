# Java-Python Integration Architecture & Endpoint Mapping

## 🏗️ Architecture Overview

### **Java Backend (Spring Boot + Vaadin)**
- **Role**: API Gateway, Business Logic, User Interface, User Management
- **Port**: 8080
- **Responsibilities**:
  - User authentication & authorization
  - Business logic orchestration
  - UI rendering (Vaadin)
  - Data persistence (PostgreSQL)
  - External API integration coordination
  - Rate limiting & security

### **Python Backend (FastAPI)**
- **Role**: AI/ML Processing, OCR, External API Aggregation, Data Processing
- **Port**: 8000
- **Responsibilities**:
  - Image OCR processing
  - AI-powered ingredient analysis
  - External API data aggregation (FDA, EWG, COSING, etc.)
  - Machine learning model inference
  - Natural language processing
  - Data enrichment and processing

## 🔄 Integration Patterns

### 1. **Synchronous HTTP Communication**
- Java calls Python via `PythonBackendClient` using WebClient
- Circuit breaker pattern with Resilience4j
- Retry logic with exponential backoff
- Timeout handling (30s default)

### 2. **Fallback Mechanisms**
- Java has fallback methods for all Python calls
- Graceful degradation when Python services are unavailable
- Local processing alternatives where possible

### 3. **Data Flow**
```
User Request → Java Controller → Python Service → External APIs → Response
     ↓              ↓              ↓              ↓
   Vaadin UI → Business Logic → AI/ML Processing → Data Aggregation
```

## 📋 Complete Endpoint Mapping

### **Java Endpoints (Port 8080)**

#### **Product Analysis**
| Java Endpoint | Method | Purpose | Python Integration |
|---------------|--------|---------|-------------------|
| `/api/analysis/analyze-product` | POST | Full product analysis | Calls Python `/analyze-text` |
| `/api/analysis/analyze-image` | POST | Image analysis | Calls Python `/analyze-image` |

#### **Substitution & Recommendations**
| Java Endpoint | Method | Purpose | Python Integration |
|---------------|--------|---------|-------------------|
| `/api/substitution/analyze` | POST | Ingredient substitution analysis | Calls Python `/ollama/analyze` |
| `/api/substitution/alternatives` | POST | Get ingredient alternatives | Calls Python `/ollama/alternatives` |
| `/api/substitution/batch-analyze` | POST | Batch ingredient analysis | Calls Python `/ollama/analyze` |
| `/api/substitution/enhance-recommendations` | POST | Enhanced recommendations | Calls Python `/ollama/alternatives` |
| `/api/substitution/quick-substitute` | POST | Quick substitution lookup | Calls Python `/ollama/alternatives` |

#### **External API Integration**
| Java Endpoint | Method | Purpose | Python Integration |
|---------------|--------|---------|-------------------|
| `/api/inci/ingredient/{ingredient}` | GET | INCI ingredient lookup | Calls Python external APIs |
| `/api/ewg/ingredient/{ingredient}` | GET | EWG ingredient lookup | Calls Python external APIs |
| `/api/cosing/ingredient/{ingredient}` | GET | COSING ingredient lookup | Calls Python external APIs |

#### **Health & Monitoring**
| Java Endpoint | Method | Purpose | Python Integration |
|---------------|--------|---------|-------------------|
| `/api/health` | GET | System health check | Calls Python `/health` |
| `/api/ollama/health` | GET | Ollama service health | Calls Python `/ollama/status` |

### **Python Endpoints (Port 8000)**

#### **Core Analysis (Java Integration)**
| Python Endpoint | Method | Purpose | Java Integration |
|-----------------|--------|---------|------------------|
| `/java/analyze-image` | POST | Image analysis for Java | Called by Java `/api/analysis/analyze-image` |
| `/java/analyze-text` | POST | Text analysis for Java | Called by Java `/api/analysis/analyze-product` |
| `/java/ingredient-analysis` | POST | Single ingredient analysis | Called by Java substitution endpoints |
| `/java/alternatives` | POST | Get alternatives for Java | Called by Java `/api/substitution/alternatives` |
| `/java/health` | GET | Health check for Java | Called by Java `/api/health` |

#### **Main Analysis Endpoints**
| Python Endpoint | Method | Purpose | Java Integration |
|-----------------|--------|---------|------------------|
| `/analyze-image` | POST | Direct image analysis | Used by Java via `/java/analyze-image` |
| `/analyze-text` | POST | Direct text analysis | Used by Java via `/java/analyze-text` |
| `/ingredients/analyze` | POST | Ingredient analysis | Used by Java substitution endpoints |

#### **Ollama AI Integration**
| Python Endpoint | Method | Purpose | Java Integration |
|-----------------|--------|---------|------------------|
| `/ollama/status` | GET | Ollama service status | Called by Java `/api/ollama/health` |
| `/ollama/analyze` | POST | AI ingredient analysis | Called by Java substitution endpoints |
| `/ollama/alternatives` | POST | AI alternatives generation | Called by Java `/api/substitution/alternatives` |
| `/ollama/analyze/stream` | POST | Streaming AI analysis | Future Java integration |

#### **Authentication & User Management**
| Python Endpoint | Method | Purpose | Java Integration |
|-----------------|--------|---------|------------------|
| `/auth/register` | POST | User registration | Java handles auth, Python for data processing |
| `/auth/token` | POST | Token generation | Java handles auth, Python for data processing |
| `/auth/me` | GET | User profile | Java handles auth, Python for data processing |
| `/firebase/register` | POST | Firebase registration | Java handles auth, Python for data processing |
| `/firebase/login` | POST | Firebase login | Java handles auth, Python for data processing |

#### **Health & Monitoring**
| Python Endpoint | Method | Purpose | Java Integration |
|-----------------|--------|---------|------------------|
| `/health` | GET | System health | Called by Java `/api/health` |
| `/debug/env` | GET | Environment debug | Development only |
| `/debug/simple` | GET | Simple health check | Development only |

## 🔧 Integration Configuration

### **Java Configuration**
```yaml
# application.yml
python:
  backend:
    url: ${PYTHON_BACKEND_URL:http://localhost:8000}
    timeout: ${PYTHON_BACKEND_TIMEOUT:30000}
    retry:
      max-attempts: 3
      delay: 1000
    circuit-breaker:
      failure-rate-threshold: 50
      wait-duration-in-open-state: 30s
```

### **Python Configuration**
```python
# config.py
JAVA_BACKEND_URL = "http://localhost:8080"
JAVA_INTEGRATION_ENABLED = True
JAVA_REQUEST_TIMEOUT = 30
```

## 🚀 Data Flow Examples

### **1. Image Analysis Flow**
```
1. User uploads image via Vaadin UI
2. Java receives request at `/api/analysis/analyze-image`
3. Java calls Python `/java/analyze-image` with image file
4. Python processes image with OCR + AI analysis
5. Python returns structured analysis data
6. Java formats response for Vaadin UI
7. User sees analysis results in UI
```

### **2. Ingredient Substitution Flow**
```
1. User requests alternatives via Vaadin UI
2. Java receives request at `/api/substitution/alternatives`
3. Java calls Python `/java/alternatives` with ingredient list
4. Python uses Ollama AI to generate alternatives
5. Python returns alternative ingredients
6. Java formats response for Vaadin UI
7. User sees alternative suggestions
```

### **3. Health Check Flow**
```
1. Java health endpoint `/api/health` is called
2. Java calls Python `/java/health`
3. Python checks all services (database, Ollama, external APIs)
4. Python returns health status
5. Java aggregates health from all services
6. Returns comprehensive health report
```

## 🛡️ Security & Resilience

### **Circuit Breaker Pattern**
- **Java**: Uses Resilience4j circuit breakers
- **Python**: FastAPI with error handling
- **Fallback**: Java has local processing alternatives

### **Rate Limiting**
- **Java**: Spring Security + custom rate limiting
- **Python**: FastAPI rate limiting middleware
- **Shared**: Redis-based rate limiting

### **Authentication**
- **Java**: Handles all authentication (JWT, Firebase)
- **Python**: Receives authenticated requests from Java
- **Shared**: JWT token validation

## 📊 Monitoring & Observability

### **Metrics**
- Request/response times
- Success/failure rates
- Circuit breaker states
- Python service availability

### **Logging**
- Structured JSON logging
- Correlation IDs across services
- Secret sanitization
- Request/response logging

### **Health Checks**
- Java: `/api/health` (comprehensive)
- Python: `/java/health` (for Java integration)
- Shared: Database, Redis, external APIs

## 🔄 Error Handling

### **Java Error Handling**
```java
@CircuitBreaker(name = "python-backend", fallbackMethod = "analyzeImageFallback")
@Retry(name = "python-backend")
@TimeLimiter(name = "python-backend")
public Mono<ProductAnalysisResponse> analyzeImage(MultipartFile imageFile, String userNeed) {
    // Implementation with error handling
}
```

### **Python Error Handling**
```python
@java_router.post("/analyze-image")
async def java_analyze_image(file: UploadFile, user_need: str):
    try:
        # Processing logic
        return JavaProductAnalysisResponse(success=True, ...)
    except Exception as e:
        logger.error(f"Error in Java image analysis: {e}")
        return JavaProductAnalysisResponse(success=False, error=str(e))
```

## 🚀 Future Enhancements

### **Planned Improvements**
1. **Async Processing**: Celery for long-running tasks
2. **Message Queues**: RabbitMQ/Kafka for decoupled communication
3. **Caching**: Redis for shared cache between services
4. **Streaming**: WebSocket for real-time updates
5. **Microservices**: Split into smaller services

### **Performance Optimizations**
1. **Connection Pooling**: HikariCP for Java, asyncpg for Python
2. **Caching Strategy**: L1 (in-memory), L2 (Redis), L3 (database)
3. **Load Balancing**: Multiple Python instances
4. **Database Optimization**: Indexes, query optimization

## 📝 Development Guidelines

### **Adding New Endpoints**
1. **Java**: Add controller method with proper annotations
2. **Python**: Add endpoint with Java-optimized response format
3. **Integration**: Update `PythonBackendClient` if needed
4. **Testing**: Add integration tests for both sides
5. **Documentation**: Update this mapping document

### **Testing Integration**
1. **Unit Tests**: Test individual endpoints
2. **Integration Tests**: Test Java-Python communication
3. **E2E Tests**: Test complete user workflows
4. **Load Tests**: Test under high load
5. **Chaos Tests**: Test failure scenarios

## 🔍 Troubleshooting

### **Common Issues**
1. **Connection Timeouts**: Check network connectivity
2. **Circuit Breaker Open**: Check Python service health
3. **Authentication Errors**: Check JWT token validity
4. **Data Format Mismatch**: Check response model compatibility

### **Debug Commands**
```bash
# Check Java health
curl http://localhost:8080/api/health

# Check Python health
curl http://localhost:8000/java/health

# Test Java-Python integration
curl -X POST http://localhost:8080/api/analysis/analyze-text \
  -H "Content-Type: application/json" \
  -d '{"text": "test ingredients", "user_need": "sensitive skin"}'
```

---

**Last Updated**: December 2024  
**Version**: 3.0.1  
**Maintainer**: CTO Team
