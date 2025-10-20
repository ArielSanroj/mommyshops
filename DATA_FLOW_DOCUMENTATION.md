# MommyShops Data Flow Documentation

## System Overview
MommyShops is an intelligent cosmetic analysis platform that processes product ingredients through multiple input methods, analyzes them using AI and external APIs, and provides personalized recommendations for safer, eco-friendly alternatives.

## File Structure & Responsibilities

### 🏗️ **Core Application Structure**

```
mommyshops-app/
├── src/main/java/com/mommyshops/
│   ├── config/                          # Configuration classes
│   │   ├── MommyshopsApplication.java   # Main Spring Boot application
│   │   ├── SecurityConfig.java          # OAuth2 and security configuration
│   │   ├── WebClientConfig.java         # HTTP client configuration
│   │   ├── GlobalCorsConfig.java        # CORS configuration
│   │   └── ExternalApiConfig.java       # External API configuration
│   │
│   ├── auth/                           # Authentication & Authorization
│   │   ├── domain/
│   │   │   └── UserAccount.java         # User account entity
│   │   ├── repository/
│   │   │   └── UserAccountRepository.java # User data access
│   │   └── service/
│   │       └── AuthService.java         # Authentication business logic
│   │
│   ├── profile/                        # User Personalization
│   │   ├── domain/
│   │   │   └── UserProfile.java         # User preferences entity
│   │   ├── repository/
│   │   │   └── UserProfileRepository.java # Profile data access
│   │   └── service/
│   │       └── UserProfileService.java  # Profile management logic
│   │
│   ├── analysis/                       # Core Analysis Engine
│   │   ├── domain/
│   │   │   └── ProductAnalysis.java     # Analysis results entity
│   │   ├── repository/
│   │   │   └── ProductAnalysisRepository.java # Analysis data access
│   │   └── service/
│   │       ├── ProductAnalysisService.java    # Main analysis orchestrator
│   │       ├── OCRService.java               # Image text extraction
│   │       └── WebScrapingService.java       # URL content extraction
│   │
│   ├── ai/                             # AI Integration
│   │   └── service/
│   │       └── OllamaService.java       # Local AI model integration
│   │
│   ├── integration/                    # External API Integration
│   │   ├── domain/
│   │   │   └── ExternalSourceLog.java  # API call logging entity
│   │   └── service/
│   │       └── ExternalApiService.java # External API client
│   │
│   ├── recommendation/                 # Recommendation Engine
│   │   ├── domain/
│   │   │   └── RecommendationFeedback.java # User feedback entity
│   │   ├── repository/
│   │   │   └── RecommendationFeedbackRepository.java # Feedback data access
│   │   └── service/
│   │       └── RecommendationService.java # Recommendation logic
│   │
│   ├── frontend/                       # Vaadin Web UI
│   │   ├── layout/
│   │   │   └── MainLayout.java         # Main application layout
│   │   └── view/
│   │       ├── OnboardingView.java     # Tutorial/onboarding
│   │       ├── QuestionnaireView.java  # User preferences form
│   │       ├── AnalysisView.java       # Product analysis interface
│   │       └── DashboardView.java      # Analysis history dashboard
│   │
│   └── common/                         # Shared utilities (empty)
│
└── src/main/resources/
    ├── application.properties          # Application configuration
    └── static/                         # Static web assets
```

## 🔄 **Data Flow Architecture**

### 1. **User Authentication Flow**
```
Browser → Vaadin UI → Spring Security → Google OAuth2 → AuthService → UserAccount (DB)
```

**Files Involved:**
- `SecurityConfig.java` - OAuth2 configuration
- `AuthService.java` - User creation/retrieval logic
- `UserAccount.java` - User data model
- `UserAccountRepository.java` - User data persistence

### 2. **User Profile Creation Flow**
```
QuestionnaireView → UserProfileService → UserProfile (DB) → Personalization Engine
```

**Files Involved:**
- `QuestionnaireView.java` - User input form
- `UserProfileService.java` - Profile management
- `UserProfile.java` - Profile data model
- `UserProfileRepository.java` - Profile persistence

### 3. **Product Analysis Flow**

#### 3.1 Image Analysis Path
```
Image Upload → OCRService → OllamaService → Ingredient List → Analysis Pipeline
```

#### 3.2 URL Analysis Path
```
URL Input → WebScrapingService → OllamaService → Ingredient List → Analysis Pipeline
```

#### 3.3 Manual Input Path
```
Text Input → ProductAnalysisService → Analysis Pipeline
```

**Files Involved:**
- `AnalysisView.java` - Input interface
- `OCRService.java` - Image text extraction
- `WebScrapingService.java` - URL content extraction
- `ProductAnalysisService.java` - Main analysis orchestrator
- `OllamaService.java` - AI-powered ingredient analysis

### 4. **Analysis Pipeline**
```
Ingredient List → OllamaService (AI Analysis) + ExternalApiService (Safety Data) → 
Risk Assessment → Confidence Scoring → ProductAnalysis (DB) → Recommendation Engine
```

**Files Involved:**
- `OllamaService.java` - AI ingredient analysis
- `ExternalApiService.java` - External safety data (FDA, EWG, etc.)
- `ProductAnalysisService.java` - Analysis orchestration
- `ProductAnalysis.java` - Analysis results storage

### 5. **Recommendation Generation Flow**
```
Analysis Results + User Profile → RecommendationService → Substitute Suggestions → 
User Feedback → Feedback Learning Loop
```

**Files Involved:**
- `RecommendationService.java` - Recommendation generation
- `RecommendationFeedback.java` - User feedback storage
- `DashboardView.java` - Results display

## 🔧 **Key Service Interactions**

### **ProductAnalysisService** (Main Orchestrator)
- **Input**: Product name, ingredients, user profile
- **Process**: 
  1. Extracts ingredients (OCR/Scraping/Manual)
  2. Analyzes each ingredient via OllamaService
  3. Enriches with external API data
  4. Calculates safety and eco-friendliness scores
  5. Generates recommendations
- **Output**: Complete analysis with recommendations
- **Dependencies**: OllamaService, ExternalApiService, RecommendationService

### **OllamaService** (AI Engine)
- **Input**: Ingredient name, user profile
- **Process**: 
  1. Sends structured prompts to local Ollama instance
  2. Parses JSON responses
  3. Returns safety/eco scores and risk assessments
- **Output**: Structured ingredient analysis
- **Dependencies**: Local Ollama instance

### **ExternalApiService** (Data Enrichment)
- **Input**: Ingredient name
- **Process**: 
  1. Queries FDA, PubChem, EWG, WHO APIs
  2. Handles rate limiting and errors
  3. Caches responses in Redis
- **Output**: External safety data
- **Dependencies**: Redis cache, external APIs

### **RecommendationService** (Personalization)
- **Input**: Analysis results, user profile
- **Process**: 
  1. Generates substitute suggestions
  2. Applies user preferences and budget constraints
  3. Learns from user feedback
- **Output**: Personalized recommendations
- **Dependencies**: User feedback data

## 🗄️ **Database Schema & Relationships**

### **Core Entities**
1. **UserAccount** - User authentication and basic info
2. **UserProfile** - Detailed user preferences and skin/hair types
3. **ProductAnalysis** - Analysis results and confidence scores
4. **RecommendationFeedback** - User ratings and comments
5. **ExternalSourceLog** - API call logging and monitoring

### **Data Relationships**
```
UserAccount (1) ←→ (1) UserProfile
UserAccount (1) ←→ (N) ProductAnalysis
ProductAnalysis (1) ←→ (N) RecommendationFeedback
```

## 🔄 **Async Processing Flow**

### **Analysis Queue Processing**
```
User Request → Async Queue → Background Processing → WebSocket Updates → UI Refresh
```

**Implementation:**
- Long-running analyses are processed asynchronously
- Progress updates sent via WebSocket to Vaadin UI
- Results stored in database when complete
- User notified via email for complex analyses

## 🛡️ **Security & Data Flow**

### **Authentication Flow**
1. User clicks "Login with Google"
2. Redirected to Google OAuth2
3. Google returns user info
4. AuthService creates/updates UserAccount
5. Session established with Spring Security

### **Data Protection**
- Sensitive data encrypted at rest
- API calls logged for audit
- User consent tracked for GDPR compliance
- Rate limiting prevents abuse

## 📊 **Monitoring & Observability**

### **Metrics Collection**
- Analysis success/failure rates
- API response times
- User engagement metrics
- Error rates and types

### **Logging Strategy**
- Structured JSON logging
- Request/response correlation IDs
- Performance timing logs
- Error stack traces

## 🚀 **Deployment Flow**

### **Development Environment**
1. Local PostgreSQL + Redis
2. Local Ollama instance
3. Spring Boot dev server
4. Vaadin development mode

### **Production Environment**
1. Containerized deployment (Docker)
2. Managed databases (AWS RDS)
3. Managed cache (AWS ElastiCache)
4. Load balancer + auto-scaling
5. Monitoring with Prometheus/Grafana

## 🔧 **Configuration Management**

### **Environment-Specific Configs**
- `application.properties` - Base configuration
- `application-local.properties` - Local development
- `application-prod.properties` - Production settings

### **External Dependencies**
- Ollama (local AI)
- PostgreSQL (data persistence)
- Redis (caching)
- Google OAuth2 (authentication)
- External APIs (FDA, EWG, etc.)

This architecture provides a scalable, maintainable platform for intelligent cosmetic analysis with strong separation of concerns and clear data flow patterns.