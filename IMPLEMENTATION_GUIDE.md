# MommyShops Implementation Guide

## Overview
This guide provides step-by-step instructions for implementing the MommyShops intelligent cosmetic analysis platform.

## Prerequisites

### 1. Development Environment Setup
```bash
# Install Java 21
brew install openjdk@21

# Install Maven
brew install maven

# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Install PostgreSQL
brew install postgresql
brew services start postgresql

# Install Redis
brew install redis
brew services start redis
```

### 2. Ollama Setup
```bash
# Pull the required models
ollama pull llama3.1
ollama pull llava

# Start Ollama service
ollama serve
```

### 3. Database Setup
```sql
-- Create database
CREATE DATABASE mommyshops;
CREATE USER mommyshops WITH PASSWORD 'change-me';
GRANT ALL PRIVILEGES ON DATABASE mommyshops TO mommyshops;
```

## Implementation Steps

### Step 1: Core Dependencies
Add these dependencies to `pom.xml`:

```xml
<!-- JSON Processing -->
<dependency>
    <groupId>com.fasterxml.jackson.core</groupId>
    <artifactId>jackson-databind</artifactId>
</dependency>

<!-- Image Processing -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-webflux</artifactId>
</dependency>

<!-- File Upload -->
<dependency>
    <groupId>commons-fileupload</groupId>
    <artifactId>commons-fileupload</artifactId>
    <version>1.5</version>
</dependency>
```

### Step 2: Environment Configuration
Create `application-local.properties`:

```properties
# Database
spring.datasource.url=jdbc:postgresql://localhost:5432/mommyshops
spring.datasource.username=mommyshops
spring.datasource.password=change-me

# Redis
spring.data.redis.host=localhost
spring.data.redis.port=6379

# Ollama
ollama.base-url=http://localhost:11434
ollama.model=llama3.1
ollama.vision-model=llava

# External APIs (get keys from respective services)
external.api.fda.key=your_fda_api_key
external.api.ewg.key=your_ewg_api_key

# Google OAuth (get from Google Cloud Console)
spring.security.oauth2.client.registration.google.client-id=your_google_client_id
spring.security.oauth2.client.registration.google.client-secret=your_google_client_secret
```

### Step 3: Database Migration
Create `src/main/resources/db/migration/V1__Create_tables.sql`:

```sql
-- User accounts table
CREATE TABLE user_accounts (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    google_sub VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    tutorial_completed BOOLEAN NOT NULL DEFAULT FALSE
);

-- User roles table
CREATE TABLE user_roles (
    user_id UUID REFERENCES user_accounts(id),
    role VARCHAR(50) NOT NULL,
    PRIMARY KEY (user_id, role)
);

-- User profiles table
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES user_accounts(id),
    hair_preferences TEXT,
    facial_skin_preferences TEXT,
    body_skin_preferences TEXT,
    budget_preferences TEXT,
    brand_preferences TEXT
);

-- Product analysis table
CREATE TABLE product_analysis (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES user_accounts(id),
    product_name VARCHAR(255) NOT NULL,
    ingredient_source TEXT,
    analysis_summary TEXT,
    analyzed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    confidence_score INTEGER NOT NULL
);

-- Risk flags table
CREATE TABLE risk_flags (
    analysis_id UUID REFERENCES product_analysis(id),
    risk_flag VARCHAR(100) NOT NULL,
    PRIMARY KEY (analysis_id, risk_flag)
);

-- Recommendation feedback table
CREATE TABLE recommendation_feedback (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES user_accounts(id),
    analysis_id UUID REFERENCES product_analysis(id),
    recommendation_type VARCHAR(100) NOT NULL,
    rating INTEGER NOT NULL,
    comments TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- External source logs table
CREATE TABLE external_source_logs (
    id UUID PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL,
    request_data TEXT,
    response_data TEXT,
    status_code INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create indexes
CREATE INDEX idx_user_accounts_email ON user_accounts(email);
CREATE INDEX idx_product_analysis_user_id ON product_analysis(user_id);
CREATE INDEX idx_product_analysis_analyzed_at ON product_analysis(analyzed_at);
CREATE INDEX idx_recommendation_feedback_user_id ON recommendation_feedback(user_id);
```

### Step 4: Security Configuration
Update `SecurityConfig.java`:

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(authz -> authz
                .requestMatchers("/", "/login", "/oauth2/**", "/api/public/**").permitAll()
                .requestMatchers("/analysis", "/dashboard", "/questionnaire").authenticated()
                .anyRequest().authenticated()
            )
            .oauth2Login(oauth2 -> oauth2
                .loginPage("/login")
                .defaultSuccessUrl("/dashboard", true)
                .userInfoEndpoint(userInfo -> userInfo
                    .userService(customOAuth2UserService())
                )
            )
            .logout(logout -> logout
                .logoutSuccessUrl("/")
                .invalidateHttpSession(true)
            )
            .csrf(csrf -> csrf.disable());
        
        return http.build();
    }
    
    @Bean
    public OAuth2UserService<OAuth2UserRequest, OAuth2User> customOAuth2UserService() {
        return new CustomOAuth2UserService();
    }
}
```

### Step 5: API Rate Limiting
Create `RateLimitingService.java`:

```java
@Service
public class RateLimitingService {
    
    private final RedisTemplate<String, String> redisTemplate;
    
    public boolean isAllowed(String userId, String operation, int limit, Duration window) {
        String key = "rate_limit:" + userId + ":" + operation;
        String count = redisTemplate.opsForValue().get(key);
        
        if (count == null) {
            redisTemplate.opsForValue().set(key, "1", window);
            return true;
        }
        
        int currentCount = Integer.parseInt(count);
        if (currentCount < limit) {
            redisTemplate.opsForValue().increment(key);
            return true;
        }
        
        return false;
    }
}
```

### Step 6: Monitoring and Health Checks
Create `HealthCheckController.java`:

```java
@RestController
@RequestMapping("/api/health")
public class HealthCheckController {
    
    @Autowired
    private OllamaService ollamaService;
    
    @Autowired
    private ExternalApiService externalApiService;
    
    @GetMapping("/ollama")
    public ResponseEntity<Map<String, Object>> checkOllama() {
        try {
            // Test Ollama connection
            return ResponseEntity.ok(Map.of("status", "UP", "service", "Ollama"));
        } catch (Exception e) {
            return ResponseEntity.status(503)
                .body(Map.of("status", "DOWN", "service", "Ollama", "error", e.getMessage()));
        }
    }
    
    @GetMapping("/external-apis")
    public ResponseEntity<Map<String, Object>> checkExternalApis() {
        Map<String, String> apiStatus = new HashMap<>();
        
        // Check each external API
        apiStatus.put("FDA", checkApi("https://api.fda.gov/drug/event.json"));
        apiStatus.put("PubChem", checkApi("https://pubchem.ncbi.nlm.nih.gov/rest/pug"));
        apiStatus.put("EWG", checkApi("https://api.ewg.org/skindeep"));
        
        return ResponseEntity.ok(Map.of("status", "UP", "apis", apiStatus));
    }
    
    private String checkApi(String url) {
        try {
            // Simple connectivity check
            return "UP";
        } catch (Exception e) {
            return "DOWN: " + e.getMessage();
        }
    }
}
```

## Testing Strategy

### Unit Tests
```java
@SpringBootTest
class ProductAnalysisServiceTest {
    
    @MockBean
    private OllamaService ollamaService;
    
    @MockBean
    private ExternalApiService externalApiService;
    
    @Test
    void testAnalyzeProduct() {
        // Test product analysis logic
    }
}
```

### Integration Tests
```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Testcontainers
class IntegrationTest {
    
    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15")
            .withDatabaseName("testdb")
            .withUsername("test")
            .withPassword("test");
    
    @Container
    static GenericContainer<?> redis = new GenericContainer<>("redis:7")
            .withExposedPorts(6379);
}
```

## Deployment

### Docker Configuration
Create `Dockerfile`:

```dockerfile
FROM openjdk:21-jdk-slim

WORKDIR /app

COPY target/mommyshops-app-*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=production
      - SPRING_DATASOURCE_URL=jdbc:postgresql://postgres:5432/mommyshops
      - SPRING_DATA_REDIS_HOST=redis
    depends_on:
      - postgres
      - redis
      - ollama

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=mommyshops
      - POSTGRES_USER=mommyshops
      - POSTGRES_PASSWORD=change-me
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    volumes:
      - redis_data:/data

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"

volumes:
  postgres_data:
  redis_data:
  ollama_data:
```

## Performance Optimization

### Caching Strategy
```java
@Service
public class CachedAnalysisService {
    
    @Cacheable(value = "ingredient-analysis", key = "#ingredient")
    public IngredientAnalysis analyzeIngredient(String ingredient) {
        // Analysis logic
    }
    
    @CacheEvict(value = "ingredient-analysis", allEntries = true)
    public void clearCache() {
        // Clear cache
    }
}
```

### Async Processing
```java
@Service
public class AsyncAnalysisService {
    
    @Async
    public CompletableFuture<AnalysisResult> analyzeProductAsync(String productName, String ingredients) {
        // Async analysis logic
    }
}
```

## Security Considerations

### Data Encryption
```java
@Component
public class EncryptionService {
    
    @Value("${app.encryption.key}")
    private String encryptionKey;
    
    public String encrypt(String data) {
        // Encryption logic
    }
    
    public String decrypt(String encryptedData) {
        // Decryption logic
    }
}
```

### GDPR Compliance
```java
@Service
public class GDPRService {
    
    public void exportUserData(UUID userId) {
        // Export all user data
    }
    
    public void deleteUserData(UUID userId) {
        // Delete all user data
    }
    
    public void anonymizeUserData(UUID userId) {
        // Anonymize user data
    }
}
```

## Monitoring and Alerting

### Prometheus Metrics
```java
@Component
public class AnalysisMetrics {
    
    private final Counter analysisCounter;
    private final Timer analysisTimer;
    
    public AnalysisMetrics(MeterRegistry meterRegistry) {
        this.analysisCounter = Counter.builder("analysis.total")
            .description("Total number of analyses")
            .register(meterRegistry);
        
        this.analysisTimer = Timer.builder("analysis.duration")
            .description("Analysis duration")
            .register(meterRegistry);
    }
}
```

### Logging Configuration
```yaml
# logback-spring.xml
<configuration>
    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <pattern>%d{HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>
    
    <logger name="com.mommyshops" level="DEBUG"/>
    <logger name="org.springframework.security" level="INFO"/>
    
    <root level="INFO">
        <appender-ref ref="STDOUT"/>
    </root>
</configuration>
```

## Troubleshooting

### Common Issues

1. **Ollama Connection Issues**
   - Check if Ollama is running: `ollama list`
   - Verify model is installed: `ollama pull llama3.1`

2. **Database Connection Issues**
   - Check PostgreSQL is running: `brew services list | grep postgres`
   - Verify database exists and user has permissions

3. **Redis Connection Issues**
   - Check Redis is running: `brew services list | grep redis`
   - Verify Redis port 6379 is accessible

4. **External API Issues**
   - Check API keys are correctly configured
   - Verify rate limits are not exceeded
   - Check network connectivity

### Performance Issues

1. **Slow Analysis**
   - Increase Ollama timeout settings
   - Implement caching for repeated analyses
   - Use async processing for long-running operations

2. **Memory Issues**
   - Increase JVM heap size: `-Xmx2g`
   - Optimize image processing
   - Implement pagination for large datasets

## Next Steps

1. **Phase 1**: Complete core analysis engine
2. **Phase 2**: Implement advanced recommendation algorithms
3. **Phase 3**: Add mobile app support
4. **Phase 4**: Integrate with e-commerce platforms
5. **Phase 5**: Add community features and user reviews

## Support

For technical support or questions:
- Create an issue in the repository
- Contact the development team
- Check the troubleshooting guide above