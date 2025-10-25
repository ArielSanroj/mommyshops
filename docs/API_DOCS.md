# MommyShops - API Documentation

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

```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}

Response:
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## Rate Limiting

- **Global**: 100 requests per minute
- **Burst**: 10 requests per second
- **Per User**: 1000 requests per hour

Headers in response:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1698765432
Retry-After: 60 (only when limit exceeded)
```

## Common Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 413 | Payload Too Large |
| 429 | Too Many Requests |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

---

## Python Backend API (Port 8000)

### Health & Status

#### GET /health
Health check endpoint

**Response**:
```json
{
  "status": "healthy",
  "service": "mommyshops-api",
  "version": "3.0.0",
  "timestamp": "2025-10-24T10:30:00Z"
}
```

---

### Authentication

#### POST /auth/register
Register a new user

**Request**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Response**:
```json
{
  "success": true,
  "user_id": 123,
  "message": "User registered successfully"
}
```

#### POST /auth/token
Login and obtain JWT token

**Request**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### GET /auth/me
Get current user info (requires authentication)

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "id": 123,
  "email": "user@example.com",
  "full_name": "John Doe",
  "created_at": "2025-10-24T10:00:00Z"
}
```

---

### Product Analysis

#### POST /java-integration/analyze-image
Analyze product image (for Java backend integration)

**Request** (multipart/form-data):
- `file`: Image file (JPG, PNG, WEBP, max 5MB)
- `user_need`: User's specific need (optional)

**cURL Example**:
```bash
curl -X POST http://localhost:8000/java-integration/analyze-image \
  -F "file=@product.jpg" \
  -F "user_need=sensitive skin"
```

**Response**:
```json
{
  "success": true,
  "productName": "Moisturizing Cream",
  "ingredientsDetails": [
    {
      "name": "Water",
      "ecoScore": 1.0,
      "riskLevel": "low",
      "benefits": "Hydration, solvent",
      "risksDetailed": "None known",
      "sources": "EWG, COSING"
    },
    {
      "name": "Glycerin",
      "ecoScore": 2.0,
      "riskLevel": "low",
      "benefits": "Moisturizer, humectant",
      "risksDetailed": "May cause irritation in high concentrations",
      "sources": "EWG, PubChem"
    }
  ],
  "avgEcoScore": 70.5,
  "suitability": "Suitable for sensitive skin",
  "recommendations": "Generally safe product. Patch test recommended.",
  "analysisId": "abc123xyz",
  "processingTimeMs": 5420
}
```

#### POST /analyze-text
Analyze text list of ingredients

**Request**:
```json
{
  "text": "Aqua, Glycerin, Sodium Chloride, Parabens",
  "user_need": "acne prone skin"
}
```

**Response**:
```json
{
  "success": true,
  "ingredients": [
    {
      "name": "Aqua",
      "eco_score": 1.0,
      "risk_level": "low"
    },
    {
      "name": "Parabens",
      "eco_score": 7.0,
      "risk_level": "high",
      "warnings": ["May disrupt hormones", "Avoid during pregnancy"]
    }
  ],
  "overall_score": 4.5,
  "recommendation": "Contains ingredients to avoid for acne-prone skin"
}
```

---

### Ollama AI Integration

#### GET /ollama/status
Check Ollama service status

**Response**:
```json
{
  "status": "available",
  "models": ["llama3.1", "llava"],
  "version": "0.1.10"
}
```

#### POST /ollama/analyze
Analyze ingredients with AI

**Request**:
```json
{
  "ingredients": ["Water", "Glycerin", "Parabens"],
  "user_context": {
    "skin_type": "sensitive",
    "concerns": ["irritation", "hormones"]
  }
}
```

**Response**:
```json
{
  "success": true,
  "analysis": "Based on your sensitive skin...",
  "risk_assessment": "moderate",
  "alternatives": ["Paraben-free preservatives"],
  "personalized_advice": "Consider patch testing..."
}
```

---

### Ingredients

#### GET /ingredients
List all ingredients (paginated)

**Query Parameters**:
- `skip`: Offset (default: 0)
- `limit`: Max results (default: 50, max: 100)
- `search`: Search term (optional)

**Example**:
```bash
GET /ingredients?search=glycerin&limit=10
```

**Response**:
```json
{
  "total": 523,
  "results": [
    {
      "id": 1,
      "name": "Glycerin",
      "inci_name": "Glycerin",
      "eco_score": 2.0,
      "risk_level": "low"
    }
  ],
  "pagination": {
    "skip": 0,
    "limit": 10,
    "total_pages": 53
  }
}
```

---

## Java Backend API (Port 8080)

### Health & Status

#### GET /api/health
Comprehensive health check

**Response**:
```json
{
  "status": "UP",
  "components": {
    "database": {
      "status": "UP",
      "details": {
        "database": "PostgreSQL",
        "validationQuery": "isValid()"
      }
    },
    "redis": {
      "status": "UP"
    },
    "pythonBackend": {
      "status": "UP",
      "responseTime": "45ms"
    }
  }
}
```

---

### Product Analysis

#### POST /api/analysis/analyze-product
Complete product analysis

**Request** (multipart/form-data):
- `file`: Image file
- `productName`: Product name
- `userId`: User ID
- `userNeed`: Specific need (optional)

**Response**:
```json
{
  "status": "success",
  "productName": "Face Cream",
  "analysisSummary": "Generally safe product with 2 ingredients to watch",
  "ewgScore": 3.5,
  "safetyPercentage": 85.0,
  "ecoPercentage": 82.0,
  "suitability": "Suitable with precautions",
  "recommendations": "Patch test recommended for sensitive skin",
  "ingredients": "Water, Glycerin, Phenoxyethanol, Fragrance",
  "analysisId": "xyz789",
  "processingTimeMs": 6200,
  "additionalInfo": "Análisis realizado con Python backend (OCR + AI + APIs externas)"
}
```

---

### INCI Database

#### GET /api/inci/ingredient/{ingredient}
Get INCI information for specific ingredient

**Example**:
```bash
GET /api/inci/ingredient/Aqua
```

**Response**:
```json
{
  "inciName": "Aqua",
  "commonName": "Water",
  "function": "Solvent",
  "hazardLevel": 1,
  "description": "Purified water used as solvent",
  "restrictions": "None",
  "cosmeticUse": true
}
```

#### GET /api/inci/search/hazard/{hazardLevel}
Search ingredients by hazard level

**Parameters**:
- `hazardLevel`: 1 (low) to 10 (high)

**Response**:
```json
{
  "hazardLevel": 8,
  "count": 45,
  "ingredients": [
    {
      "inciName": "Formaldehyde",
      "hazardLevel": 9,
      "warnings": ["Carcinogen", "Sensitizer"]
    }
  ]
}
```

---

### EWG Database

#### GET /api/ewg/ingredient/{ingredient}
Get EWG (Environmental Working Group) data

**Example**:
```bash
GET /api/ewg/ingredient/Parabens
```

**Response**:
```json
{
  "ingredient": "Parabens",
  "ewgScore": 7,
  "concerns": [
    "Endocrine disruption",
    "Allergies/immunotoxicity"
  ],
  "dataAvailability": "GOOD",
  "usage": "Preservative",
  "alternatives": [
    "Phenoxyethanol",
    "Benzyl Alcohol"
  ]
}
```

#### POST /api/ewg/ingredients
Batch EWG lookup

**Request**:
```json
{
  "ingredients": ["Paraben", "Glycerin", "Fragrance"]
}
```

**Response**:
```json
{
  "results": [
    {
      "ingredient": "Paraben",
      "ewgScore": 7,
      "concerns": ["Endocrine disruption"]
    },
    {
      "ingredient": "Glycerin",
      "ewgScore": 2,
      "concerns": []
    }
  ]
}
```

---

### COSING Database

#### GET /api/cosing/ingredient/{ingredient}
Get EU COSING (Cosmetic Ingredient Database) information

**Response**:
```json
{
  "ingredient": "Aqua",
  "inci": "Water",
  "casNumber": "7732-18-5",
  "function": "Solvent",
  "restrictions": "None",
  "prohibitedSubstances": false,
  "annex": null
}
```

---

### Ingredient Substitution

#### POST /api/substitution/analyze
Analyze ingredients and suggest substitutions

**Request**:
```json
{
  "ingredients": [
    "Sodium Lauryl Sulfate",
    "Parabens",
    "Artificial Fragrance"
  ],
  "userProfile": {
    "skinType": "sensitive",
    "concerns": ["irritation", "hormones"],
    "preferences": ["natural", "organic"]
  }
}
```

**Response**:
```json
{
  "analysisId": "sub123",
  "problematicIngredients": [
    {
      "name": "Sodium Lauryl Sulfate",
      "issues": ["Irritation", "Stripping natural oils"],
      "severity": "moderate",
      "alternatives": [
        {
          "name": "Sodium Laureth Sulfate",
          "benefit": "Milder surfactant",
          "score": 3.5
        },
        {
          "name": "Cocamidopropyl Betaine",
          "benefit": "Gentle, derived from coconut",
          "score": 2.0
        }
      ]
    },
    {
      "name": "Parabens",
      "issues": ["Endocrine disruption"],
      "severity": "high",
      "alternatives": [
        {
          "name": "Phenoxyethanol",
          "benefit": "Effective preservative, no hormone disruption",
          "score": 3.0
        }
      ]
    }
  ],
  "overallRecommendation": "Consider reformulation with suggested alternatives",
  "safetySummary": {
    "current": 6.5,
    "improved": 3.2
  }
}
```

#### POST /api/substitution/quick-substitute
Quick substitution for single ingredient

**Request**:
```json
{
  "ingredient": "Paraben",
  "context": "preservative"
}
```

**Response**:
```json
{
  "original": "Paraben",
  "alternatives": [
    {
      "name": "Phenoxyethanol",
      "function": "Preservative",
      "score": 3.0,
      "pros": ["Effective", "Widely accepted"],
      "cons": ["May cause irritation in high concentrations"]
    }
  ]
}
```

---

## Error Responses

### Standard Error Format

```json
{
  "error": "Error type",
  "message": "Human-readable error message",
  "details": {
    "field": "email",
    "reason": "Invalid format"
  },
  "timestamp": "2025-10-24T10:30:00Z",
  "path": "/api/auth/register"
}
```

### Common Errors

#### 400 Bad Request
```json
{
  "error": "Validation Error",
  "message": "Invalid input data",
  "details": {
    "email": "Email format is invalid",
    "password": "Password must be at least 8 characters"
  }
}
```

#### 401 Unauthorized
```json
{
  "error": "Authentication Failed",
  "message": "Invalid or expired token",
  "details": {
    "reason": "Token has expired"
  }
}
```

#### 429 Too Many Requests
```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again in 60 seconds.",
  "retry_after": 60
}
```

#### 413 Payload Too Large
```json
{
  "error": "File too large",
  "message": "File size exceeds maximum allowed size",
  "details": {
    "maxSize": "5MB",
    "yourSize": "8MB"
  }
}
```

---

## Webhooks (Future)

### Product Analysis Complete

**URL**: Your configured webhook URL  
**Method**: POST

**Payload**:
```json
{
  "event": "analysis.completed",
  "timestamp": "2025-10-24T10:30:00Z",
  "data": {
    "analysisId": "abc123",
    "userId": 456,
    "productName": "Face Cream",
    "status": "completed",
    "score": 7.5
  }
}
```

---

## SDKs & Client Libraries

### Python Client

```python
from mommyshops import MommyShopsClient

client = MommyShopsClient(api_key="your_api_key")

# Analyze image
result = client.analyze_image("product.jpg", user_need="sensitive skin")
print(result.safety_score)

# Get ingredient info
ingredient = client.get_ingredient("Glycerin")
print(ingredient.eco_score)
```

### JavaScript/TypeScript Client

```typescript
import { MommyShopsClient } from '@mommyshops/client';

const client = new MommyShopsClient({ apiKey: 'your_api_key' });

// Analyze product
const result = await client.analyzeImage(file, { userNeed: 'sensitive skin' });
console.log(result.safetyPercentage);
```

---

## API Versioning

Current version: **v1**

Version is included in URL:
- `/api/v1/analysis/...`
- `/api/v2/analysis/...` (future)

Breaking changes will result in new major version.

---

## Support

- **Email**: api-support@mommyshops.com
- **Documentation**: https://docs.mommyshops.com
- **Status Page**: https://status.mommyshops.com
- **Discord**: https://discord.gg/mommyshops

---

**Last Updated**: 2025-10-24  
**API Version**: 3.0.0
