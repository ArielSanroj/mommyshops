# MommyShops - Mapeo de Endpoints

## Resumen Ejecutivo

**Problema Crítico Identificado**: No hay comunicación entre Python (puerto 8000) y Java (puerto 8080). Ambos stacks duplican funcionalidad sin coordinación.

## Python FastAPI Endpoints (Puerto 8000)

### Autenticación y Usuarios
- `POST /auth/register` - Registro de usuarios
- `POST /auth/token` - Login con JWT
- `GET /auth/me` - Información del usuario autenticado
- `GET /auth/google` - OAuth2 Google
- `GET /auth/google/callback` - Callback OAuth2

### Firebase Integration
- `POST /firebase/register` - Registro en Firebase
- `POST /firebase/login` - Login Firebase
- `GET /firebase/user/{uid}` - Obtener perfil de usuario
- `PUT /firebase/user/{uid}` - Actualizar perfil
- `DELETE /firebase/user/{uid}` - Eliminar usuario
- `POST /firebase/refresh` - Refresh token

### Análisis de Productos
- `POST /analyze-image` - Análisis OCR de imágenes
- `POST /analyze-text` - Análisis de texto de ingredientes
- `POST /analyze_routine/{user_id}` - Análisis de rutina de usuario

### Machine Learning
- `POST /ml/rebuild` - Reconstruir modelo ML
- `POST /ingredients/analyze` - Análisis de ingredientes con ML

### Ollama AI Integration
- `GET /ollama/status` - Estado del servicio Ollama
- `POST /ollama/analyze` - Análisis con Ollama
- `POST /ollama/alternatives` - Sugerencias de alternativas
- `POST /ollama/analyze/stream` - Análisis streaming

### Recomendaciones
- `GET /recommendations/{user_id}` - Obtener recomendaciones
- `POST /recommendations/{recommendation_id}/rating` - Rating de recomendaciones

### Utilidades
- `GET /` - Health check básico
- `GET /health` - Health check detallado
- `GET /debug/env` - Variables de entorno
- `GET /debug/simple` - Debug simple
- `GET /debug/tesseract` - Estado de Tesseract
- `GET /ingredients` - Lista de ingredientes

## Java Spring Boot Endpoints (Puerto 8080)

### Análisis de Productos
- `POST /api/analysis/analyze-product` - Análisis completo de producto
- `POST /api/analysis/analyze-image` - Análisis de imagen (DUPLICADO con Python)

### Sustituciones
- `POST /api/substitution/analyze` - Análisis para sustitución
- `POST /api/substitution/alternatives` - Alternativas de ingredientes
- `POST /api/substitution/batch-analyze` - Análisis por lotes
- `POST /api/substitution/enhance-recommendations` - Mejorar recomendaciones
- `GET /api/substitution/health` - Health check sustitución
- `GET /api/substitution/safety-standards` - Estándares de seguridad
- `POST /api/substitution/quick-substitute` - Sustitución rápida
- `POST /api/substitution/integrate-with-routine-analysis` - Integración con rutina

### INCI (International Nomenclature of Cosmetic Ingredients)
- `GET /api/inci/ingredient/{ingredient}` - Información de ingrediente INCI
- `POST /api/inci/calculate` - Cálculo de propiedades INCI
- `GET /api/inci/search/hazard/{hazardLevel}` - Búsqueda por nivel de riesgo
- `GET /api/inci/search/description/{keyword}` - Búsqueda por descripción
- `GET /api/inci/stats` - Estadísticas INCI
- `GET /api/inci/health` - Health check INCI
- `GET /api/inci/test` - Test endpoint
- `GET /api/inci/hazard-levels` - Niveles de riesgo disponibles

### EWG (Environmental Working Group)
- `GET /api/ewg/ingredient/{ingredient}` - Información EWG de ingrediente
- `POST /api/ewg/ingredients` - Análisis múltiple EWG
- `GET /api/ewg/health` - Health check EWG
- `GET /api/ewg/test` - Test endpoint

### COSING (Cosmetic Ingredient Database)
- `GET /api/cosing/ingredient/{ingredient}` - Información COSING
- `POST /api/cosing/ingredients` - Análisis múltiple COSING
- `GET /api/cosing/search/function/{function}` - Búsqueda por función
- `GET /api/cosing/search/restriction/{restriction}` - Búsqueda por restricción
- `GET /api/cosing/search/annex/{annex}` - Búsqueda por anexo
- `GET /api/cosing/stats` - Estadísticas COSING
- `GET /api/cosing/health` - Health check COSING
- `GET /api/cosing/test` - Test endpoint

### Health Checks
- `GET /api/health` - Health check principal
- `GET /api/health/quick` - Health check rápido
- `GET /api/health/detailed` - Health check detallado
- `GET /api/health/component/{component}` - Health check de componente específico
- `GET /api/health/environment` - Variables de entorno
- `GET /api/health/apis` - Estado de APIs externas
- `GET /api/health/cache` - Estado del cache
- `GET /api/health/logging` - Estado del logging
- `POST /api/health/cache/clear` - Limpiar cache
- `GET /api/health/info` - Información del sistema

### Ollama AI
- `GET /api/ollama/health` - Health check Ollama
- `GET /api/ollama/models` - Modelos disponibles

### Testing
- `POST /api/test/analyze-image` - Test de análisis de imagen

## Duplicaciones Identificadas

### 🔴 CRÍTICAS
1. **Análisis de imagen**: 
   - Python: `POST /analyze-image`
   - Java: `POST /api/analysis/analyze-image`
   - **Problema**: Misma funcionalidad, diferentes implementaciones

2. **Health checks**:
   - Python: `GET /health`
   - Java: `GET /api/health`
   - **Problema**: Información duplicada, sin sincronización

### 🟡 MEDIAS
3. **Análisis de ingredientes**:
   - Python: `POST /ingredients/analyze`
   - Java: `POST /api/substitution/analyze`
   - **Problema**: Lógica similar, diferentes enfoques

4. **Ollama integration**:
   - Python: `POST /ollama/analyze`
   - Java: `GET /api/ollama/health`
   - **Problema**: Python maneja análisis, Java solo monitoreo

## Propuesta de Arquitectura

### Responsabilidades por Stack

**Python (Puerto 8000) - "AI & Data Processing"**
- ✅ OCR y procesamiento de imágenes
- ✅ Integración con APIs externas (FDA, EWG, PubChem, etc.)
- ✅ Machine Learning y Ollama AI
- ✅ Scraping de datos externos
- ✅ Firebase integration

**Java (Puerto 8080) - "Business Logic & API Gateway"**
- ✅ Autenticación y autorización
- ✅ Gestión de usuarios y perfiles
- ✅ Lógica de negocio (recomendaciones, sustituciones)
- ✅ Base de datos principal (PostgreSQL)
- ✅ Cache y rate limiting
- ✅ Frontend (Vaadin)

### Comunicación Propuesta

```
Frontend (Vaadin) → Java (8080) → Python (8000) → APIs Externas
                  ←              ←
```

**Flujos principales:**
1. **Análisis de imagen**: Frontend → Java → Python (OCR) → Java (procesamiento) → Frontend
2. **Consulta de ingrediente**: Frontend → Java → Python (APIs externas) → Java (lógica) → Frontend
3. **Recomendaciones**: Frontend → Java (ML local) → Python (Ollama) → Java → Frontend

## Próximos Pasos

1. **Implementar PythonBackendClient en Java**
2. **Crear endpoints específicos en Python para Java**
3. **Eliminar duplicaciones**
4. **Configurar circuit breakers bidireccionales**
5. **Implementar health checks coordinados**

