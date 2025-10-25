# MommyShops Production Deployment Guide

## 🚀 **Overview**

This guide provides comprehensive instructions for deploying MommyShops in a production environment, including unified startup/health checks, hardened API orchestration, and environment validation based on the Python `start.py`, `api_utils_production.py`, and `substitution_endpoints.py` functionality.

## 🏗️ **Architecture Components**

### **Core Production Services**

#### **1. ProductionApiUtils**
- **Purpose**: Production-ready API utilities with rate limiting and circuit breakers
- **Features**: 
  - Rate limiting for external API calls
  - Circuit breaker pattern for resilience
  - Thread-safe caching with TTL
  - Retry logic with exponential backoff
  - Comprehensive error handling

#### **2. StartupHealthCheckService**
- **Purpose**: Unified startup and health check system
- **Features**:
  - Comprehensive component health monitoring
  - Database connectivity validation
  - External API health checks
  - Performance monitoring
  - Security validation

#### **3. EnvironmentValidationService**
- **Purpose**: Environment validation and configuration management
- **Features**:
  - API key validation
  - Database configuration validation
  - Redis configuration validation
  - Ollama configuration validation
  - Security configuration validation

#### **4. ProductionLoggingService**
- **Purpose**: Production-grade logging and monitoring
- **Features**:
  - Structured JSON logging
  - Performance metrics tracking
  - Error rate monitoring
  - Security event logging
  - Cache operation logging

#### **5. HealthCheckController**
- **Purpose**: REST endpoints for health monitoring
- **Features**:
  - Overall health check
  - Component-specific health checks
  - Environment validation endpoints
  - API health monitoring
  - Cache and logging health checks

## 🔧 **Installation and Setup**

### **Prerequisites**

- **Java 21+**: Required for Spring Boot 3.4.0
- **Maven 3.8+**: For building the application
- **Docker**: For PostgreSQL and Redis containers
- **Ollama**: For AI/ML features (optional but recommended)

### **Quick Setup**

```bash
# 1. Clone the repository
git clone <repository-url>
cd mommyshops

# 2. Run the setup script
chmod +x setup-production-environment.sh
./setup-production-environment.sh

# 3. Update environment variables
nano .env

# 4. Start the application
./start-production.sh
```

### **Manual Setup**

#### **1. Install Java 21**

**macOS:**
```bash
brew install openjdk@21
export JAVA_HOME=$(/usr/libexec/java_home -v 21)
```

**Linux:**
```bash
sudo apt-get update
sudo apt-get install openjdk-21-jdk
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
```

#### **2. Install Maven**

**macOS:**
```bash
brew install maven
```

**Linux:**
```bash
sudo apt-get install maven
```

#### **3. Install Docker**

**macOS:**
- Download Docker Desktop from https://www.docker.com/products/docker-desktop

**Linux:**
```bash
sudo apt-get install docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

#### **4. Install Ollama**

```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &
ollama pull llama3.1
ollama pull llava
```

## ⚙️ **Configuration**

### **Environment Variables**

Create a `.env` file with the following configuration:

```bash
# Database Configuration
DATABASE_URL=jdbc:postgresql://localhost:5432/mommyshops_prod
DATABASE_USERNAME=mommyshops
DATABASE_PASSWORD=your_secure_password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
OLLAMA_VISION_MODEL=llava

# API Keys (Replace with your actual keys)
FDA_API_KEY=your_fda_api_key_here
EWG_API_KEY=your_ewg_api_key_here
INCI_BEAUTY_API_KEY=your_inci_beauty_api_key_here
COSING_API_KEY=your_cosing_api_key_here
ENTREZ_EMAIL=your.email@example.com
APIFY_API_KEY=your_apify_api_key_here

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# JWT Configuration
JWT_SECRET=your_jwt_secret_key_here
JWT_EXPIRATION=86400000

# Logging Configuration
LOG_LEVEL=INFO
BACKEND_LOG_PATH=logs/backend.log
LOG_MAX_FILE_SIZE=10MB
LOG_MAX_FILES=10

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Server Configuration
SERVER_PORT=8080
```

### **Production Configuration**

The application uses `application-production.yml` for production-specific settings:

```yaml
spring:
  profiles:
    active: production
  
  datasource:
    url: ${DATABASE_URL:jdbc:postgresql://localhost:5432/mommyshops_prod}
    username: ${DATABASE_USERNAME:mommyshops}
    password: ${DATABASE_PASSWORD:your_secure_password}
    hikari:
      maximum-pool-size: 20
      minimum-idle: 5
      connection-timeout: 30000
      idle-timeout: 600000
      max-lifetime: 1800000
      leak-detection-threshold: 60000
  
  jpa:
    hibernate:
      ddl-auto: validate
    show-sql: false
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQLDialect
        jdbc:
          batch_size: 25
        order_inserts: true
        order_updates: true
        batch_versioned_data: true

app:
  api:
    fda-key: ${FDA_API_KEY:}
    ewg-key: ${EWG_API_KEY:}
    inci-beauty-key: ${INCI_BEAUTY_API_KEY:}
    cosing-key: ${COSING_API_KEY:}
    entrez-email: ${ENTREZ_EMAIL:your.email@example.com}
    apify-key: ${APIFY_API_KEY:}
  
  ollama:
    base-url: ${OLLAMA_BASE_URL:http://localhost:11434}
    model: ${OLLAMA_MODEL:llama3.1}
    vision-model: ${OLLAMA_VISION_MODEL:llava}
    timeout: 30000
    max-retries: 3
```

## 🚀 **Deployment**

### **Using the Startup Script**

```bash
# Start the application
./start-production.sh

# Stop the application
./stop-production.sh

# Stop and clean logs
./stop-production.sh --clean-logs
```

### **Manual Deployment**

#### **1. Build the Application**

```bash
mvn clean package -DskipTests
```

#### **2. Start Required Services**

```bash
# Start PostgreSQL
docker run -d \
  --name mommyshops-postgres \
  -e POSTGRES_DB=mommyshops_prod \
  -e POSTGRES_USER=mommyshops \
  -e POSTGRES_PASSWORD=mommyshops123 \
  -p 5432:5432 \
  postgres:15-alpine

# Start Redis
docker run -d \
  --name mommyshops-redis \
  -p 6379:6379 \
  redis:7-alpine

# Start Ollama
ollama serve &
ollama pull llama3.1
ollama pull llava
```

#### **3. Run the Application**

```bash
export SPRING_PROFILES_ACTIVE=production
java -Xms512m -Xmx2g -XX:+UseG1GC -XX:+UseStringDeduplication -XX:+OptimizeStringConcat -jar target/mommyshops-app-*.jar
```

### **Docker Deployment**

#### **1. Create Dockerfile**

```dockerfile
FROM openjdk:21-jdk-slim

WORKDIR /app

COPY target/mommyshops-app-*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-Xms512m", "-Xmx2g", "-XX:+UseG1GC", "-XX:+UseStringDeduplication", "-XX:+OptimizeStringConcat", "-jar", "app.jar"]
```

#### **2. Create docker-compose.yml**

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=production
      - DATABASE_URL=jdbc:postgresql://postgres:5432/mommyshops_prod
      - DATABASE_USERNAME=mommyshops
      - DATABASE_PASSWORD=mommyshops123
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - postgres
      - redis
      - ollama

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=mommyshops_prod
      - POSTGRES_USER=mommyshops
      - POSTGRES_PASSWORD=mommyshops123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  postgres_data:
  redis_data:
  ollama_data:
```

#### **3. Deploy with Docker Compose**

```bash
docker-compose up -d
```

## 🔍 **Health Monitoring**

### **Health Check Endpoints**

#### **Overall Health Check**
```bash
curl http://localhost:8080/api/health
```

#### **Quick Health Check**
```bash
curl http://localhost:8080/api/health/quick
```

#### **Detailed Health Check**
```bash
curl http://localhost:8080/api/health/detailed
```

#### **Component-Specific Health Check**
```bash
curl http://localhost:8080/api/health/component/database
curl http://localhost:8080/api/health/component/external_apis
curl http://localhost:8080/api/health/component/cache
```

#### **Environment Validation**
```bash
curl http://localhost:8080/api/health/environment
```

#### **API Health Check**
```bash
curl http://localhost:8080/api/health/apis
```

### **Health Check Response Format**

```json
{
  "status": "healthy",
  "healthy": true,
  "message": "All systems operational",
  "timestamp": 1703123456789,
  "uptime": 3600000,
  "version": "1.0.0",
  "components": {
    "database": {
      "status": "healthy",
      "healthy": true,
      "message": "Database connection successful",
      "response_time": 45,
      "last_checked": "2023-12-21T10:30:45Z",
      "details": {
        "user_accounts": 150,
        "product_analyses": 1250,
        "recommendation_feedback": 89
      }
    },
    "external_apis": {
      "status": "healthy",
      "healthy": true,
      "message": "External API health check completed",
      "response_time": 1200,
      "last_checked": "2023-12-21T10:30:45Z",
      "details": {
        "fda": {
          "status": "healthy",
          "response_time": 250
        },
        "pubchem": {
          "status": "healthy",
          "response_time": 180
        }
      }
    }
  }
}
```

## 📊 **Monitoring and Logging**

### **Log Files**

- **Application Logs**: `logs/mommyshops.log`
- **Backend Logs**: `logs/backend.log`
- **Access Logs**: `logs/access.log`

### **Log Levels**

- **TRACE**: Detailed debugging information
- **DEBUG**: Debug information
- **INFO**: General information
- **WARN**: Warning messages
- **ERROR**: Error messages
- **FATAL**: Fatal error messages

### **Structured Logging**

The application uses structured JSON logging for better monitoring:

```json
{
  "timestamp": "2023-12-21T10:30:45.123Z",
  "logger": "mommyshops.api_utils",
  "level": "INFO",
  "message": "API call successful",
  "context": {
    "api": "fda",
    "endpoint": "/drug/event.json",
    "response_time_ms": 250,
    "success": true
  }
}
```

### **Performance Metrics**

The application tracks various performance metrics:

- **API Response Times**: Tracked per API endpoint
- **Database Query Times**: Tracked per query type
- **Cache Hit Rates**: Tracked per cache type
- **Error Rates**: Tracked per component
- **Memory Usage**: Tracked continuously
- **CPU Usage**: Tracked continuously

### **Monitoring Endpoints**

#### **Application Info**
```bash
curl http://localhost:8080/api/health/info
```

#### **Cache Statistics**
```bash
curl http://localhost:8080/api/health/cache
```

#### **Logging Statistics**
```bash
curl http://localhost:8080/api/health/logging
```

#### **Clear Cache**
```bash
curl -X POST http://localhost:8080/api/health/cache/clear
```

## 🔒 **Security**

### **Authentication**

- **Google OAuth2**: Primary authentication method
- **JWT Tokens**: For API authentication
- **Session Management**: Secure session handling

### **Authorization**

- **Role-Based Access Control**: User roles and permissions
- **API Security**: Rate limiting and authentication
- **Data Protection**: Encrypted sensitive data

### **Security Headers**

- **CORS**: Configurable cross-origin resource sharing
- **CSRF Protection**: Cross-site request forgery protection
- **XSS Protection**: Cross-site scripting protection
- **Content Security Policy**: Content security policy headers

## 🚨 **Troubleshooting**

### **Common Issues**

#### **1. Application Won't Start**

**Symptoms**: Application fails to start or crashes immediately

**Solutions**:
- Check Java version (must be 21+)
- Verify environment variables
- Check port availability
- Review application logs

```bash
# Check Java version
java -version

# Check port availability
lsof -i :8080

# Check logs
tail -f logs/mommyshops.log
```

#### **2. Database Connection Issues**

**Symptoms**: Database connection errors

**Solutions**:
- Verify PostgreSQL is running
- Check database credentials
- Verify network connectivity

```bash
# Check PostgreSQL status
docker ps | grep postgres

# Test database connection
psql -h localhost -U mommyshops -d mommyshops_prod
```

#### **3. Redis Connection Issues**

**Symptoms**: Redis connection errors

**Solutions**:
- Verify Redis is running
- Check Redis configuration
- Verify network connectivity

```bash
# Check Redis status
docker ps | grep redis

# Test Redis connection
redis-cli ping
```

#### **4. Ollama Issues**

**Symptoms**: AI features not working

**Solutions**:
- Verify Ollama is running
- Check model availability
- Verify network connectivity

```bash
# Check Ollama status
curl http://localhost:11434/api/version

# Check available models
ollama list
```

#### **5. External API Issues**

**Symptoms**: External API calls failing

**Solutions**:
- Check API keys
- Verify network connectivity
- Check rate limits
- Review API health status

```bash
# Check API health
curl http://localhost:8080/api/health/apis

# Check specific API
curl http://localhost:8080/api/health/component/external_apis
```

### **Performance Issues**

#### **1. Slow Response Times**

**Solutions**:
- Check database performance
- Verify cache configuration
- Monitor memory usage
- Check external API response times

#### **2. High Memory Usage**

**Solutions**:
- Increase heap size
- Check for memory leaks
- Optimize database queries
- Review cache configuration

#### **3. High CPU Usage**

**Solutions**:
- Check for infinite loops
- Optimize algorithms
- Review thread pool configuration
- Monitor external API calls

### **Log Analysis**

#### **1. Error Logs**

```bash
# Filter error logs
grep "ERROR" logs/mommyshops.log

# Filter specific errors
grep "Database connection failed" logs/mommyshops.log
```

#### **2. Performance Logs**

```bash
# Filter performance logs
grep "Performance metric" logs/mommyshops.log

# Filter slow queries
grep "response_time_ms" logs/mommyshops.log | grep -E "[0-9]{4,}"
```

#### **3. Security Logs**

```bash
# Filter security events
grep "Security event" logs/mommyshops.log

# Filter authentication logs
grep "Authentication" logs/mommyshops.log
```

## 📈 **Performance Optimization**

### **JVM Tuning**

```bash
# Production JVM options
export JAVA_OPTS="-Xms512m -Xmx2g -XX:+UseG1GC -XX:+UseStringDeduplication -XX:+OptimizeStringConcat"

# High-performance JVM options
export JAVA_OPTS="-Xms1g -Xmx4g -XX:+UseG1GC -XX:+UseStringDeduplication -XX:+OptimizeStringConcat -XX:+UseCompressedOops -XX:+UseCompressedClassPointers"
```

### **Database Optimization**

- **Connection Pooling**: Configure HikariCP settings
- **Query Optimization**: Use proper indexes
- **Batch Processing**: Enable batch operations
- **Connection Timeouts**: Set appropriate timeouts

### **Cache Optimization**

- **TTL Configuration**: Set appropriate cache TTL
- **Cache Size**: Configure maximum cache size
- **Eviction Policy**: Use appropriate eviction policy
- **Memory Usage**: Monitor cache memory usage

### **API Optimization**

- **Rate Limiting**: Configure appropriate rate limits
- **Circuit Breakers**: Set appropriate thresholds
- **Retry Logic**: Configure retry parameters
- **Timeout Settings**: Set appropriate timeouts

## 🔄 **Backup and Recovery**

### **Database Backup**

```bash
# Create database backup
docker exec mommyshops-postgres pg_dump -U mommyshops mommyshops_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database backup
docker exec -i mommyshops-postgres psql -U mommyshops mommyshops_prod < backup_20231221_103045.sql
```

### **Application Backup**

```bash
# Create application backup
tar -czf mommyshops_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
  target/mommyshops-app-*.jar \
  logs/ \
  data/ \
  config/ \
  .env
```

### **Recovery Procedures**

1. **Stop the application**
2. **Restore database backup**
3. **Restore application files**
4. **Update configuration**
5. **Start the application**
6. **Verify functionality**

## 📚 **Additional Resources**

### **Documentation**

- **API Documentation**: http://localhost:8080/api/docs
- **Health Check API**: http://localhost:8080/api/health
- **Metrics**: http://localhost:8080/actuator/metrics
- **Prometheus**: http://localhost:8080/actuator/prometheus

### **Monitoring Tools**

- **Application Metrics**: Spring Boot Actuator
- **JVM Metrics**: Micrometer
- **Database Metrics**: HikariCP
- **Cache Metrics**: Spring Cache
- **Custom Metrics**: ProductionLoggingService

### **Support**

- **Logs**: Check application logs for detailed information
- **Health Checks**: Use health check endpoints for status
- **Metrics**: Monitor application metrics for performance
- **Documentation**: Refer to this guide for troubleshooting

---

**🎉 MommyShops Production Deployment Guide - Complete!**

This guide provides everything needed to deploy and maintain MommyShops in a production environment with comprehensive health monitoring, logging, and troubleshooting capabilities.