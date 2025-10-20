# 🔥 Firebase Data Structure Analysis - MommyShops

> **Actualización 2025-03**: la capa de datos unificó la normalización de ingredientes (`normalize_ingredient_name`). Toda escritura hacia Firestore debe usar los nombres canónicos que expone `database.get_ingredient_data` para preparar el futuro motor de recomendaciones.
>
> `managed_session(commit=True)` garantiza commits/rollbacks consistentes antes de sincronizar con Firebase, mientras que el caché thread-safe en `api_utils_production` normaliza las claves (`proveedor:ingrediente`) y elimina artefactos (`µg`, `1mg`, caracteres griegos) detectados por OCR. La prueba `test_firebase_integration.py::test_session_manager` confirma este flujo dual. El filtro de medidas ahora descarta proporciones como `µg/L` y `ppm`, asegurando que Firestore sólo reciba nombres de ingredientes limpios.

## 📊 Current Data Collection Status

### ✅ **What We SHOULD Have in Firebase:**

#### **1. Users Collection (`/users/{userId}`)**
```json
{
  "uid": "firebase-user-id",
  "email": "user@example.com",
  "username": "username",
  "name": "Full Name",
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "last_login": "timestamp",
  
  // Profile Data (from onboarding questionnaire)
  "skin_face": "oily|dry|combination|sensitive|normal",
  "hair_type": "straight|wavy|curly|coily",
  "climate": "tropical|temperate|dry|humid|cold",
  
  // Goals (JSON objects)
  "goals_face": {
    "anti_aging": true,
    "acne_treatment": false,
    "hydration": true,
    "brightening": false
  },
  "skin_body": {
    "type": "oily|dry|combination",
    "concerns": ["cellulite", "stretch_marks"]
  },
  "goals_body": {
    "moisturizing": true,
    "firming": false,
    "exfoliation": true
  },
  "hair_porosity": {
    "level": "low|medium|high",
    "texture": "fine|medium|coarse"
  },
  "goals_hair": {
    "growth": true,
    "strength": false,
    "moisture": true,
    "color_protection": false
  },
  "hair_thickness_scalp": {
    "density": "thin|medium|thick",
    "scalp_condition": "normal|oily|dry|sensitive"
  },
  "conditions": [
    "eczema",
    "psoriasis",
    "rosacea",
    "acne",
    "sensitive_skin"
  ]
}
```

#### **2. Analysis Results Collection (`/analysis_results/{resultId}`)**
```json
{
  "user_id": "firebase-user-id",
  "created_at": "timestamp",
  "product_name": "Product Name",
  "ingredients": ["ingredient1", "ingredient2"],
  "analysis_type": "image_ocr|manual_input|url_scraping",
  "image_url": "optional-image-url",
  
  // Analysis Results
  "safety_score": 8.5,
  "ingredient_analysis": {
    "safe_ingredients": ["ingredient1", "ingredient2"],
    "concerning_ingredients": ["ingredient3"],
    "unknown_ingredients": ["ingredient4"]
  },
  "recommendations": [
    {
      "ingredient": "ingredient3",
      "substitute": "safer_alternative",
      "reason": "Potential skin irritant"
    }
  ],
  "alerts": [
    "Contains potential allergens",
    "Not suitable for sensitive skin"
  ],
  "suggestions": [
    "Consider patch testing",
    "Look for fragrance-free alternatives"
  ]
}
```

#### **3. Routines Collection (`/routines/{routineId}`)**
```json
{
  "user_id": "firebase-user-id",
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "name": "Morning Routine",
  "products": [
    {
      "name": "Gentle Cleanser",
      "category": "cleanser",
      "step": 1
    },
    {
      "name": "Moisturizer",
      "category": "moisturizer", 
      "step": 2
    }
  ],
  "is_active": true
}
```

#### **4. Recommendations Collection (`/recommendations/{recommendationId}`)**
```json
{
  "user_id": "firebase-user-id",
  "created_at": "timestamp",
  "product_name": "Original Product",
  "recommended_products": [
    {
      "name": "Recommended Product",
      "reason": "Safer ingredients",
      "match_score": 0.85
    }
  ],
  "analysis_id": "analysis-result-id"
}
```

#### **5. Products Collection (`/products/{productId}`)**
```json
{
  "name": "Product Name",
  "brand": "Brand Name",
  "category": "cleanser|moisturizer|serum|etc",
  "ingredients": ["ingredient1", "ingredient2"],
  "safety_score": 8.5,
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

#### **6. Ingredients Collection (`/ingredients/{ingredientId}`)**
```json
{
  "name": "Ingredient Name",
  "inci_name": "INCI Name",
  "safety_score": 7.5,
  "function": "Emollient|Surfactant|Preservative",
  "risks": ["Potential irritant"],
  "benefits": ["Moisturizing"],
  "sources": ["EWG", "CIR", "SCCS"],
  "created_at": "timestamp"
}
```

- 📌 **Nota**: `name` y `inci_name` deben provenir del caché normalizado (por ejemplo `get_ingredient_data(...)['name']`) para evitar duplicados y alinear la base con SQLite.

#### **7. Analytics Collection (`/analytics/{eventId}`)**
```json
{
  "user_id": "firebase-user-id",
  "event_type": "product_analysis|routine_created|recommendation_viewed",
  "event_data": {
    "product_name": "Product Name",
    "analysis_type": "image_ocr"
  },
  "timestamp": "timestamp",
  "session_id": "session-id"
}
```

## ❌ **Current Status:**

### **What We DON'T Have in Firebase:**
- ❌ **0 users** in Firebase (user is in SQLite only)
- ❌ **0 analysis results** in Firebase
- ❌ **0 routines** in Firebase
- ❌ **0 recommendations** in Firebase
- ❌ **Firebase not properly configured**

### **What We DO Have:**
- ✅ **1 user** in SQLite database (majoagonpi@gmail.com)
- ✅ **Google OAuth** working (but saving to SQLite)
- ✅ **Firebase configuration** code ready
- ✅ **Data models** defined
- ✅ **Security rules** configured

## 🚀 **What We Should Migrate to Firebase:**

### **1. User Data Migration**
```python
# Current SQLite User → Firebase User
{
  "id": 1,
  "username": "majoagonpi", 
  "email": "majoagonpi@gmail.com",
  "google_id": "google-oauth-id",
  "auth_provider": "google"
}
# Should become:
{
  "uid": "firebase-generated-uid",
  "email": "majoagonpi@gmail.com",
  "username": "majoagonpi",
  "google_id": "google-oauth-id",
  "auth_provider": "google",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### **2. Complete User Profiles**
- **Skin type** (face and body)
- **Hair characteristics** (type, porosity, thickness)
- **Goals** (face, body, hair)
- **Climate** and **conditions**
- **Routine preferences**

### **3. Analysis History**
- **Product analyses** performed
- **Ingredient safety scores**
- **Recommendations** given
- **Images** analyzed

### **4. User Behavior Analytics**
- **Product analysis frequency**
- **Most analyzed ingredients**
- **Recommendation acceptance rate**
- **Feature usage patterns**

## 🔧 **Next Steps to Implement:**

1. **Fix Firebase Configuration**
   - Set up proper service account credentials
   - Test Firebase connectivity

2. **Migrate Existing User**
   - Move majoagonpi@gmail.com from SQLite to Firebase
   - Preserve Google OAuth connection

3. **Implement Data Collection**
   - User onboarding questionnaire
   - Product analysis tracking
   - Recommendation system

4. **Set Up Analytics**
   - User behavior tracking
   - Feature usage metrics
   - Product analysis statistics

## 📈 **Benefits of Firebase Migration:**

- **Real-time synchronization** across devices
- **Better scalability** for multiple users
- **Advanced analytics** and insights
- **Offline support** with sync
- **Better security** with Firebase Auth
- **Easier maintenance** and updates

## 🎯 **Priority Data to Collect:**

1. **User Profile Data** (from onboarding)
2. **Product Analysis Results** (main feature)
3. **User Preferences** (for recommendations)
4. **Usage Analytics** (for product improvement)
5. **Routine Management** (user workflows)