# MommyShops API Documentation

## Base URLs

- **Python Backend**: `http://localhost:8000`
- **Java Backend**: `http://localhost:8080`
- **Production**: `https://api.mommyshops.com`

## Authentication

All protected endpoints require a JWT token in the Authorization header:

```http
Authorization: Bearer <your_jwt_token>
```

### Obtaining a Token

```http
POST /auth/token
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## Python API Endpoints

### Authentication

#### Register User

```http
POST /auth/register
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Response**: `201 Created`
```json
{
  "id": 1,
  "email": "newuser@example.com",
  "full_name": "John Doe",
  "created_at": "2025-01-24T10:00:00Z"
}
```

#### Login

```http
POST /auth/token
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=SecurePass123!
```

**Response**: `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### Get Current User

```http
GET /auth/me
Authorization: Bearer <token>
```

**Response**: `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true
}
```

### Product Analysis

#### Analyze Image (Java Integration Endpoint)

```http
POST /java-integration/analyze-image
Content-Type: multipart/form-data
Authorization: Bearer <token>

file=@product_image.jpg
user_need=sensitive skin
```

**Response**: `200 OK`
```json
{
  "success": true,
  "productName": "Gentle Face Cream",
  "ingredientsDetails": [
    {
      "name": "Water",
      "ecoScore": 1.0,
      "riskLevel": "low",
      "benefits": "Hydration, solvent",
      "risksDetailed": "None known",
      "sources": "FDA, COSING"
    },
    {
      "name": "Glycerin",
      "ecoScore": 2.0,
      "riskLevel": "low",
      "benefits": "Moisturizer, humectant",
      "risksDetailed": "Rare allergic reactions",
      "sources": "EWG, PubChem"
    }
  ],
  "avgEcoScore": 45.5,
  "suitability": "Suitable for sensitive skin",
  "recommendations": "This product is gentle and appropriate for daily use...",
  "analysisId": "analysis_abc123",
  "processingTimeMs": 2500
}
```

#### Analyze Text

```http
POST /analyze-text
Content-Type: application/json
Authorization: Bearer <token>

{
  "text": "Aqua, Glycerin, Sodium Chloride, Parfum",
  "user_need": "acne prone skin"
}
```

**Response**: `200 OK`
```json
{
  "success": true,
  "ingredients": ["Aqua", "Glycerin", "Sodium Chloride", "Parfum"],
  "analysis": {
    "avg_eco_score": 38.5,
    "high_risk_count": 1,
    "recommendations": "Parfum may cause irritation for acne-prone skin..."
  },
  "details": [ ... ]
}
```

### Ollama AI

#### Check Ollama Status

```http
GET /ollama/status
```

**Response**: `200 OK`
```json
{
  "status": "available",
  "models": ["llama3.1", "llava"],
  "base_url": "http://localhost:11434"
}
```

#### Analyze with Ollama

```http
POST /ollama/analyze
Content-Type: application/json
Authorization: Bearer <token>

{
  "ingredients": ["Parabens", "SLS", "Fragrance"],
  "user_context": {
    "skin_type": "sensitive",
    "concerns": ["irritation", "allergies"]
  }
}
```

**Response**: `200 OK`
```json
{
  "analysis": "Based on your sensitive skin type...",
  "risk_assessment": "Medium to High",
  "alternatives": ["Phenoxyethanol", "Cocamidopropyl Betaine"],
  "confidence": 0.85
}
```

#### Get Alternatives

```http
POST /ollama/alternatives
Content-Type: application/json
Authorization: Bearer <token>

{
  "ingredient": "Sodium Lauryl Sulfate",
  "product_type": "shampoo",
  "user_preferences": ["natural", "gentle"]
}
```

**Response**: `200 OK`
```json
{
  "alternatives": [
    {
      "name": "Cocamidopropyl Betaine",
      "similarity_score": 0.92,
      "benefits": "Gentler surfactant, less irritating",
      "eco_score": 3.0
    },
    {
      "name": "Decyl Glucoside",
      "similarity_score": 0.88,
      "benefits": "Plant-derived, very mild",
      "eco_score": 2.0
    }
  ],
  "reasoning": "These alternatives provide similar cleansing..."
}
```

### Health & Debug

#### Health Check

```http
GET /health
```

**Response**: `200 OK`
```json
{
  "status": "healthy",
  "service": "mommyshops-api",
  "version": "3.0.0",
  "checks": {
    "database": "connected",
    "redis": "connected",
    "ollama": "available"
  }
}
```

## Java API Endpoints

### Product Analysis

#### Analyze Product (Complete)

```http
POST /api/analysis/analyze-product
Content-Type: application/json
Authorization: Bearer <token>

{
  "productName": "Daily Moisturizer",
  "ingredients": ["Water", "Glycerin", "Cetyl Alcohol"],
  "userId": "user123",
  "userProfile": {
    "skinType": "dry",
    "concerns": ["aging", "hydration"]
  }
}
```

**Response**: `200 OK`
```json
{
  "status": "success",
  "productName": "Daily Moisturizer",
  "overallScore": 7.5,
  "ingredientAnalysis": [ ... ],
  "recommendations": "Excellent choice for dry skin...",
  "warnings": [],
  "alternatives": []
}
```

### INCI Database

#### Get Ingredient Information

```http
GET /api/inci/ingredient/Aqua
```

**Response**: `200 OK`
```json
{
  "inciName": "Aqua",
  "commonName": "Water",
  "casNumber": "7732-18-5",
  "function": "Solvent",
  "description": "Universal solvent used in cosmetics",
  "hazardLevel": "NONE",
  "restrictions": [],
  "sources": ["COSING", "FDA"]
}
```

#### Search by Hazard Level

```http
GET /api/inci/search/hazard/HIGH
```

**Response**: `200 OK`
```json
{
  "hazardLevel": "HIGH",
  "count": 45,
  "ingredients": [
    {
      "inciName": "Formaldehyde",
      "hazardLevel": "HIGH",
      "restrictions": ["Banned in EU", "Restricted in US"]
    },
    ...
  ]
}
```

#### INCI Statistics

```http
GET /api/inci/stats
```

**Response**: `200 OK`
```json
{
  "totalIngredients": 15420,
  "byHazardLevel": {
    "NONE": 8500,
    "LOW": 4200,
    "MEDIUM": 2100,
    "HIGH": 520,
    "SEVERE": 100
  },
  "lastUpdated": "2025-01-20T00:00:00Z"
}
```

### EWG Database

#### Get EWG Score

```http
GET /api/ewg/ingredient/Parabens
```

**Response**: `200 OK`
```json
{
  "ingredient": "Parabens",
  "ewgScore": 7,
  "riskLevel": "MODERATE_HIGH",
  "concerns": [
    "Endocrine disruption",
    "Allergies/immunotoxicity"
  ],
  "dataAvailability": "GOOD",
  "sources": ["EWG Skin Deep Database"]
}
```

#### Batch Analysis

```http
POST /api/ewg/ingredients
Content-Type: application/json

{
  "ingredients": ["Water", "Glycerin", "Parabens", "Fragrance"]
}
```

**Response**: `200 OK`
```json
{
  "results": [
    { "ingredient": "Water", "ewgScore": 1, "riskLevel": "LOW" },
    { "ingredient": "Glycerin", "ewgScore": 2, "riskLevel": "LOW" },
    { "ingredient": "Parabens", "ewgScore": 7, "riskLevel": "MODERATE_HIGH" },
    { "ingredient": "Fragrance", "ewgScore": 8, "riskLevel": "HIGH" }
  ],
  "averageScore": 4.5,
  "highRiskCount": 2
}
```

### COSING Database

#### Get COSING Information

```http
GET /api/cosing/ingredient/Glycerin
```

**Response**: `200 OK`
```json
{
  "inciName": "Glycerin",
  "casNumber": "56-81-5",
  "functions": ["Humectant", "Skin conditioning"],
  "restrictions": "None",
  "annexes": [],
  "regulatoryStatus": "APPROVED",
  "region": "EU"
}
```

#### Search by Function

```http
GET /api/cosing/search/function/Humectant
```

**Response**: `200 OK`
```json
{
  "function": "Humectant",
  "count": 234,
  "ingredients": [
    {"inciName": "Glycerin", "commonUse": "Very common"},
    {"inciName": "Hyaluronic Acid", "commonUse": "Common"},
    ...
  ]
}
```

### Substitution & Alternatives

#### Analyze for Substitution

```http
POST /api/substitution/analyze
Content-Type: application/json

{
  "ingredients": ["Sodium Lauryl Sulfate", "Parabens"],
  "productType": "shampoo",
  "userProfile": {
    "preferences": ["natural", "sulfate-free"]
  }
}
```

**Response**: `200 OK`
```json
{
  "analysis": {
    "problematicIngredients": [
      {
        "name": "Sodium Lauryl Sulfate",
        "issues": ["Harsh", "Stripping"],
        "severity": "MEDIUM"
      },
      {
        "name": "Parabens",
        "issues": ["Endocrine disruptor"],
        "severity": "HIGH"
      }
    ],
    "overallRisk": "HIGH"
  },
  "recommendations": [ ... ]
}
```

#### Get Quick Substitute

```http
POST /api/substitution/quick-substitute
Content-Type: application/json

{
  "ingredient": "SLS",
  "category": "surfactant"
}
```

**Response**: `200 OK`
```json
{
  "original": "SLS",
  "substitute": {
    "name": "Cocamidopropyl Betaine",
    "reason": "Gentler surfactant with similar properties",
    "compatibility": 0.92,
    "benefits": ["Less irritating", "Maintains foam"]
  }
}
```

### Health Monitoring

#### Detailed Health Check

```http
GET /api/health/detailed
```

**Response**: `200 OK`
```json
{
  "status": "HEALTHY",
  "timestamp": "2025-01-24T10:30:00Z",
  "components": {
    "database": {
      "status": "UP",
      "responseTime": "5ms",
      "activeConnections": 8
    },
    "pythonBackend": {
      "status": "UP",
      "responseTime": "150ms",
      "lastCheck": "2025-01-24T10:29:50Z"
    },
    "cache": {
      "status": "UP",
      "hitRate": 0.85,
      "size": "1.2GB"
    },
    "externalApis": {
      "fda": "UP",
      "ewg": "UP",
      "cosing": "UP"
    }
  },
  "version": "3.2.0",
  "uptime": "5d 12h 34m"
}
```

#### Check Specific Component

```http
GET /api/health/component/pythonBackend
```

**Response**: `200 OK`
```json
{
  "component": "pythonBackend",
  "status": "UP",
  "details": {
    "url": "http://localhost:8000",
    "responseTime": "150ms",
    "lastCheck": "2025-01-24T10:29:50Z",
    "circuitBreaker": "CLOSED"
  }
}
```

## Error Responses

### Standard Error Format

```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "Validation failed",
    "details": [
      {
        "field": "email",
        "issue": "Invalid email format"
      }
    ],
    "timestamp": "2025-01-24T10:00:00Z",
    "path": "/auth/register"
  }
}
```

### HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200 | OK | Successful request |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid input, validation error |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource already exists (e.g., duplicate email) |
| 413 | Payload Too Large | File size exceeds limit |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily down |

### Common Error Codes

#### Authentication Errors

- `AUTH_TOKEN_EXPIRED`: JWT token has expired
- `AUTH_TOKEN_INVALID`: JWT token is malformed or invalid
- `AUTH_CREDENTIALS_INVALID`: Wrong email/password
- `AUTH_USER_NOT_FOUND`: User doesn't exist

#### Validation Errors

- `VALIDATION_FAILED`: Input validation failed
- `INVALID_FILE_TYPE`: File type not allowed
- `FILE_TOO_LARGE`: File exceeds size limit
- `MISSING_REQUIRED_FIELD`: Required field missing

#### Business Logic Errors

- `INGREDIENT_NOT_FOUND`: Ingredient not in database
- `ANALYSIS_FAILED`: Analysis couldn't be completed
- `OCR_FAILED`: Text extraction failed
- `EXTERNAL_API_ERROR`: External API call failed

#### Rate Limiting

- `RATE_LIMIT_EXCEEDED`: Too many requests

**Response**: `429 Too Many Requests`
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please try again in 45 seconds.",
    "retryAfter": 45,
    "limit": 100,
    "remaining": 0,
    "reset": "2025-01-24T10:01:00Z"
  }
}
```

## Rate Limiting

### Limits

- **General Endpoints**: 100 requests per minute per IP
- **Burst**: 10 requests per second
- **Analysis Endpoints**: 20 requests per minute (higher cost)
- **Health/Public**: Unlimited

### Headers

All responses include rate limit headers:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1706097660
```

## Pagination

For endpoints returning lists:

```http
GET /api/ingredients?page=1&size=20&sort=name,asc
```

**Response**:
```json
{
  "content": [ ... ],
  "page": {
    "number": 1,
    "size": 20,
    "totalElements": 15420,
    "totalPages": 771
  }
}
```

## Filtering & Sorting

### Filtering

```http
GET /api/ingredients?hazardLevel=HIGH&function=Preservative
```

### Sorting

```http
GET /api/ingredients?sort=ewgScore,desc&sort=name,asc
```

## Webhooks (Future)

Register webhooks for events:

```http
POST /api/webhooks
Content-Type: application/json
Authorization: Bearer <token>

{
  "url": "https://your-app.com/webhook",
  "events": ["analysis.completed", "ingredient.updated"],
  "secret": "your_webhook_secret"
}
```

---

**API Documentation v3.0**  
**Last Updated**: 2025-01-24  
**Contact**: api-support@mommyshops.com

