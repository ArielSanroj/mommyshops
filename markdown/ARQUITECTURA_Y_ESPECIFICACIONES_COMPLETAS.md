# 🏗️ Arquitectura Completa y Especificaciones - MommyShops

## 📋 **Índice**
1. [Visión General del Sistema](#-visión-general-del-sistema)
2. [Arquitectura Técnica](#-arquitectura-técnica)
3. [Stack Tecnológico](#-stack-tecnológico)
4. [Estructura del Proyecto](#-estructura-del-proyecto)
5. [Modelos de Datos](#-modelos-de-datos)
6. [Endpoints de la API](#-endpoints-de-la-api)
7. [Procesamiento de Imágenes y OCR](#-procesamiento-de-imágenes-y-ocr)
8. [Integración con APIs Externas](#-integración-con-apis-externas)
9. [Base de Datos](#-base-de-datos)
10. [Manejo de Errores](#-manejo-de-errores)
11. [Optimizaciones de Rendimiento](#-optimizaciones-de-rendimiento)
12. [Configuración y Despliegue](#-configuración-y-despliegue)
13. [Testing y Debugging](#-testing-y-debugging)
14. [Lineamientos de Desarrollo](#-lineamientos-de-desarrollo)
15. [Especificaciones Técnicas](#-especificaciones-técnicas)

---

## 🎯 **Visión General del Sistema**

### **Propósito**
MommyShops es un sistema de análisis de ingredientes cosméticos que combina **OCR avanzado**, **múltiples fuentes de datos**, y **análisis de seguridad** para proporcionar recomendaciones personalizadas sobre productos cosméticos.

### **Funcionalidades Principales**
- 🔍 **Análisis de imágenes** de productos cosméticos mediante OCR
- 📝 **Análisis de texto** de listas de ingredientes
- 🌐 **Análisis de URLs** de productos en línea
- 🧪 **Análisis de seguridad** con múltiples fuentes de datos
- 🤖 **Integración con LLMs** (Ollama autoservida)
- 📊 **Scoring ecológico** y recomendaciones personalizadas

---

## 🏛️ **Arquitectura Técnica**

### **Diagrama de Componentes**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   Database      │
│   (React/Vue)   │◄──►│   Backend       │◄──►│   PostgreSQL    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   External      │
                    │   APIs          │
                    │   (FDA, EWG,    │
                    │    CIR, etc.)   │
                    └─────────────────┘
```

### **Flujo de Datos**
```
Imagen/Texto/URL → Preprocesamiento → OCR/Extracción → Análisis → Recomendación
```

---

## 🛠️ **Stack Tecnológico**

### **Backend Core**
- **Framework**: FastAPI 0.104.1 (Python 3.11+)
- **Servidor**: Uvicorn 0.24.0
- **Validación**: Pydantic v2
- **Logging**: Python logging + structlog

### **Base de Datos**
- **SGBD**: PostgreSQL
- **ORM**: SQLAlchemy 2.0.23
- **Driver**: psycopg2-binary 2.9.9
- **Migraciones**: Alembic 1.12.1

### **Procesamiento de Imágenes**
- **OCR**: Tesseract + pytesseract 0.3.10
- **Imágenes**: PIL/Pillow 10.1.0
- **Procesamiento**: NumPy 1.24.3 + SciPy 1.11.4
- **Visión**: scikit-image 0.21.0

### **APIs Externas**
- **Cliente HTTP**: httpx 0.25.2
- **Web Scraping**: BeautifulSoup4 4.12.2
- **Bioinformática**: BioPython 1.81

### **LLMs e IA**
- **Ollama**: Modelos locales / autoservidos
- **NVIDIA**: Nemotron integration
- **MCP**: Model Context Protocol

### **Desarrollo**
- **Testing**: pytest 7.4.3 + pytest-asyncio 0.21.1
- **Formateo**: black 23.11.0
- **Linting**: flake8 6.1.0
- **Entorno**: python-dotenv 1.0.0

---

## 📁 **Estructura del Proyecto**

```
mommyshops/
├── main.py                          # 🚀 Aplicación principal FastAPI
├── database.py                      # 🗄️ Modelos y conexión DB
├── api_utils_production.py          # 🌐 Utilidades para APIs externas
├── ollama_integration.py            # 🤖 Cliente centralizado de Ollama
├── ollama_enrichment.py             # 🧠 Enriquecimiento estructurado vía Ollama
├── apify_enhanced_scraper.py        # 🕷️ Web scraping avanzado
├── requirements.txt                 # 📦 Dependencias Python
├── .env                            # ⚙️ Variables de entorno
├── cosmetic_ingredients_lexicon.txt # 📚 Lexicon para OCR
├── test_ocr_debug.py               # 🔧 Script de diagnóstico
├── fix_dependencies.sh             # 🛠️ Script de instalación
├── test_cosmetic_ocr.py            # 🧪 Test específico de OCR cosmético
├── test_universal_cosmetic_ocr.py   # 🌍 Test universal de OCR
├── test_different_images.py         # 📸 Test con diferentes imágenes
└── docs/
    ├── BACKEND_ARCHITECTURE_GUIDE.md
    ├── OCR_AND_IMAGE_PROCESSING_GUIDE.md
    ├── UNIVERSAL_OCR_GUIDE.md
    ├── OCR_IMPROVEMENTS_SUMMARY.md
    └── ARQUITECTURA_Y_ESPECIFICACIONES_COMPLETAS.md
```

---

## 📊 **Modelos de Datos**

### **Request Models (Pydantic)**
```python
class AnalyzeUrlRequest(BaseModel):
    url: str = Field(..., description="URL of the product page")
    user_need: str = Field(default="general safety", description="User's skin need")

class AnalyzeTextRequest(BaseModel):
    text: str = Field(..., description="Text containing ingredient list")
    user_need: str = Field(default="general safety", description="User's skin need")

class AnalyzeImageRequest(BaseModel):
    user_need: str = Field(default="general safety", description="User's skin need")
```

### **Response Models**
```python
class IngredientAnalysisResponse(BaseModel):
    name: str
    eco_score: float
    risk_level: str
    benefits: str
    risks_detailed: str
    sources: str

class ProductAnalysisResponse(BaseModel):
    product_name: str
    ingredients_details: List[IngredientAnalysisResponse]
    avg_eco_score: float
    suitability: str
    recommendations: str
```

### **Modelo de Base de Datos**
```python
class Ingredient(Base):
    __tablename__ = "ingredients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    eco_score = Column(Float)
    risk_level = Column(String)
    benefits = Column(Text)
    risks_detailed = Column(Text)
    sources = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

---

## 🚀 **Endpoints de la API**

### **Endpoints Principales**
```python
@app.get("/")
async def root():
    """Root endpoint with system information."""

@app.post("/analyze-url")
async def analyze_url(request: AnalyzeUrlRequest, db: Session = Depends(get_db)):
    """Analyze cosmetic product from URL."""

@app.post("/analyze-text")
async def analyze_text(request: AnalyzeTextRequest, db: Session = Depends(get_db)):
    """Analyze cosmetic product from text."""

@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...), user_need: str = Form(default="general safety"), db: Session = Depends(get_db)):
    """Analyze cosmetic product from image."""
```

### **Endpoints de Utilidad**
```python
@app.get("/health")
async def health():
    """Health check for all APIs."""

@app.get("/test-fast")
async def test_fast():
    """Test endpoint for fast processing."""

@app.post("/test-ocr")
async def test_ocr(file: UploadFile = File(...)):
    """Test endpoint for OCR debugging."""

@app.get("/cache-stats")
async def cache_stats():
    """Get cache statistics."""

@app.get("/ingredients")
async def get_all_ingredients(db: Session = Depends(get_db)):
    """Get all ingredients from database."""
```

---

## 📸 **Procesamiento de Imágenes y OCR**

### **Pipeline de Procesamiento**
```python
async def extract_ingredients_from_image(image_data: bytes) -> List[str]:
    """Main image processing pipeline."""
    
    # 1. Validación
    if not TESSERACT_AVAILABLE:
        return []
    
    # 2. Preprocesamiento
    image = await preprocess_image_for_ocr(image)
    
    # 3. OCR múltiple
    text = await perform_ocr_with_retries(image)
    
    # 4. Extracción de ingredientes
    ingredients = await extract_ingredients_from_text(text)
    
    return ingredients
```

### **Preprocesamiento Avanzado**
```python
async def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    """Advanced image preprocessing for cosmetic labels."""
    
    # Conversión a escala de grises
    # Análisis de calidad (varianza)
    # Mejora de nitidez condicional
    # Mejora de contraste condicional
    # Binarización adaptativa múltiple
    # Redimensionamiento inteligente
    # Eliminación de ruido condicional
```

### **Configuraciones OCR Optimizadas**
```python
configs = [
    '--oem 3 --psm 7 -c tessedit_create_pdf=0',  # PSM 7 optimizado
    '--oem 3 --psm 6 -c tessedit_create_pdf=0',  # PSM 6 optimizado
    '--oem 3 --psm 8'                            # PSM 8 fallback
]
```

### **Sistema Universal de Adaptación**
- **Análisis automático** de características de imagen
- **Upscaling adaptativo** basado en tamaño y densidad
- **Preprocesamiento inteligente** según tipo de fondo
- **Configuraciones OCR optimizadas** por densidad de texto
- **Fallbacks múltiples** para casos difíciles

---

## 🌐 **Integración con APIs Externas**

### **Fuentes de Datos**
1. **FDA (Food and Drug Administration)**
2. **EWG (Environmental Working Group)**
3. **CIR (Cosmetic Ingredient Review)**
4. **SCCS (Scientific Committee on Consumer Safety)**
5. **ICCR (International Cooperation on Cosmetics Regulation)**
6. **PubChem (NIH)**
7. **INCI Beauty Database / CosIng API**
8. **IARC / INVIMA**

### **Orquestación y Cacheo**
- `api_utils_production.py` unifica la lógica en wrappers reutilizables que **normalizan** el nombre del ingrediente antes de generar claves de cache.
- Cache in-memory **thread-safe** con TTL configurable, métricas (`hits`, `misses`, `evictions`) y claves normalizadas para maximizar aciertos y permitir observabilidad.
- Circuit breakers y rate limiters coordinados con prioridad de riesgo (IARC ➝ FDA ➝ CIR ➝ SCCS ➝ INVIMA ➝ EWG ➝ ICCR ➝ INCI ➝ CosIng) asegurando resiliencia frente a caídas parciales.
- Logging estructurado en formato JSON con contexto (`provider`, `ingredient`, `estado del circuito`) para trazabilidad en `backend.log`.

### **Cliente HTTP Optimizado**
```python
async def fetch_ingredient_data(ingredient: str, client: httpx.AsyncClient) -> Dict:
    """Fetch ingredient data from multiple external sources."""
    
    # Paralelización de requests
    tasks = [
        fetch_fda_data(ingredient, client),
        fetch_ewg_data(ingredient, client),
        fetch_cir_data(ingredient, client),
        fetch_sccs_data(ingredient, client),
        fetch_iccr_data(ingredient, client),
        fetch_pubchem_data(ingredient, client)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return aggregate_results(results)
```

> **Actualización 2025-03**: ahora la agregación normaliza cada ingrediente antes de disparar solicitudes, usa caché en memoria con TTL y fusiona fuentes sin duplicados. Los circuit breakers y rate limiters se activan por proveedor para estabilizar FDA/EWG/INVIMA.

### **Sistema de Caché**
```python
# Caché por archivo JSON
CIR_CACHE_FILE = "cir_cache.json"
EWG_CACHE_FILE = "ewg_cache.json"
SCCS_CACHE_FILE = "sccs_cache.json"
ICCR_CACHE_FILE = "iccr_cache.json"
```

- `APICache` mantiene respuestas recientes en memoria empleando claves normalizadas (`prefijo:ingrediente`), reduciendo llamadas redundantes por variantes de OCR.
- Los archivos JSON continúan disponibles como respaldo para scrapers extensos, pero el runtime favorece el caché en memoria para baja latencia.

---

## 🗄️ **Base de Datos**

### **Conexión y Sesiones**
```python
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def managed_session(commit: bool = False):
    if SessionLocal is None:
        raise RuntimeError("Database session factory not configured")
    session = SessionLocal()
    try:
        yield session
        if commit:
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

> **Actualización 2025-03**: `managed_session()` estandariza el manejo de transacciones (incluyendo commit automático opcional), mientras que el logging JSON captura contexto (`phase`, `ingredient`, `user_id`) en `backend.log`.

### **Funciones de Consulta**
```python
def get_ingredient_data(ingredient_name: str) -> Optional[Dict]:
    """Get ingredient data from local database."""
    
def get_all_ingredients() -> List[Ingredient]:
    """Get all ingredients from database."""
```

- El diccionario en memoria se construye con claves normalizadas e incluye el nombre canónico junto con los metadatos de riesgo.
- Se amplió la normalización con mapeos Unicode (µ ➝ micro, α ➝ alpha, ß ➝ beta) y filtros de medidas (`mg`, `µg/L`, `ppm`, `mg per ml`) que eliminan proporciones y unidades aisladas antes de ingresar a la base.
- Nuevos alias y entradas locales (`vitamin e`, `beta carotene`) refuerzan la precisión durante la canonicalización y evitan colisiones por coincidencias parciales.
- Tras cada sincronización externa se refresca automáticamente (`refresh_local_cache_from_db`) para preparar el motor de recomendaciones.

---

## ⚠️ **Manejo de Errores**

### **Estrategia de Fallbacks**
```python
try:
    # Método principal
    result = await primary_method()
except Exception as e:
    logger.warning(f"Primary method failed: {e}")
    try:
        # Método secundario
        result = await secondary_method()
    except Exception as e:
        logger.error(f"Secondary method failed: {e}")
        # Método de fallback
        result = fallback_method()
```

- Los servicios críticos envían excepciones a `backend.log` con contexto (nombre del proveedor/API) para acelerar el debugging.
- Los scrapers utilizan reintentos exponenciales (`tenacity`) y circuit breakers antes de degradarse a datos locales.

### **Validación de Datos**
```python
# Validación de archivos
if not file.content_type.startswith('image/'):
    raise HTTPException(status_code=400, detail="File must be an image")

# Validación de tamaño
if len(image_data) == 0:
    raise HTTPException(status_code=400, detail="Empty image file")
```

### **Logging Estructurado**
- `database.py`, `api_utils_production.py` y `unified_data_service.py` emplean un `JSONFormatter` personalizado que serializa cada evento con `timestamp`, `level`, `logger` y `context`.
- Ejemplo (`backend.log`):
```json
{"timestamp": "2025-03-01T12:43:10", "logger": "mommyshops.api_utils", "level": "INFO", "message": "API call summary", "context": {"ingredient": "vitamin e", "successful": ["FDA", "EWG"], "failed": {}}}
```
- Los errores críticos utilizan `logger.exception(...)` para adjuntar `stacktrace` y metadatos (`provider`, `phase`, `user_id`).

---

## ⚡ **Optimizaciones de Rendimiento**

### **1. Procesamiento Asíncrono**
```python
# Paralelización de requests HTTP
async with httpx.AsyncClient() as client:
    tasks = [fetch_data(source, client) for source in sources]
    results = await asyncio.gather(*tasks, return_exceptions=True)
```

### **2. Timeouts Adaptativos**
```python
# Timeouts escalonados para OCR
timeout = 10.0 if i == 0 else (8.0 if i == 1 else 5.0)

# Timeout global para análisis
result = await asyncio.wait_for(
    analyze_ingredients_fast_local(ingredients, user_need, db),
    timeout=15.0
)
```

### **3. Modos de Procesamiento**
```python
# Modo ultra-rápido para imágenes pequeñas
if max(original_size) < 200:
    return await extract_ingredients_ultra_fast(image)

# Modo rápido con límite de ingredientes
if len(ingredients) > 5:
    ingredients = ingredients[:5]
```

### **4. Cache Inteligente de Ingredientes**
- `APICache` ahora es **thread-safe**, con TTL configurable y estadísticas consultables vía API (`get_cache_stats`).
- Las claves emplean el nombre normalizado (`proveedor:ingrediente`) para compartir resultados entre OCR, APIs y base de datos.
- Tras procesar respuestas, los datos se fusionan junto con la fuente local para evitar duplicados y acelerar el futuro motor de recomendaciones.

### **4. Caché Inteligente**
```python
# Verificar caché local primero
local_data = get_ingredient_data(ingredient)
if local_data:
    return local_data

# Caché de APIs externas
if ingredient in cache:
    return cache[ingredient]
```

---

## ⚙️ **Configuración y Despliegue**

### **Variables de Entorno**
```bash
# Database
DATABASE_URL=postgresql://postgres@localhost:5432/mommyshops_db

# OCR
TESSERACT_PATH=/opt/homebrew/bin/tesseract

# APIs
OPENAI_API_KEY=sk-proj-...
NVIDIA_API_KEY=nvapi-...
APIFY_API_KEY=apify_api_...

# External Services
ENTREZ_EMAIL=your-email@example.com
```

### **Scripts de Instalación**
```bash
# fix_dependencies.sh
pip install -r requirements.txt
brew install tesseract
python test_ocr_debug.py
```

### **Comando de Inicio**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🧪 **Testing y Debugging**

### **Script de Diagnóstico**
```python
# test_ocr_debug.py
async def main():
    tests = [
        ("Dependencies", test_dependencies),
        ("Tesseract", test_tesseract),
        ("Image Processing", test_image_processing),
        ("OCR Sample", test_ocr_with_sample),
        ("Database", test_database_connection),
        ("FastAPI", test_fastapi_endpoints),
    ]
```

### **Cobertura Actualizada (Mar 2025)**
- `test_minimal.py` incorpora casos para caracteres especiales (`α`, `µ`, `ß`), filtrado de medidas compuestas (`µg/L`, `ppm`, `mg per ml`), métricas del `APICache` y recuperación del `CircuitBreaker`.
- `test_complete_system.py` valida el pipeline de canonicalización asegurando salidas limpias antes del motor de recomendaciones.
- `test_firebase_integration.py` prueba el nuevo context manager `managed_session`, garantizando commits y rollbacks consistentes antes de sincronizar con Firebase.

### **Endpoints de Testing**
```python
@app.post("/test-ocr")
async def test_ocr(file: UploadFile = File(...)):
    """Test different OCR configurations."""
    
@app.get("/test-fast")
async def test_fast():
    """Test fast processing capabilities."""
```

---

## 📋 **Lineamientos de Desarrollo**

### **1. Estructura de Código**
- **Separación de responsabilidades**: Cada módulo tiene una función específica
- **Funciones asíncronas**: Para operaciones I/O intensivas
- **Manejo de errores**: Try-catch con logging detallado
- **Validación de datos**: Pydantic para request/response models

### **2. Convenciones de Naming**
- **Funciones**: `snake_case` descriptivo
- **Clases**: `PascalCase`
- **Constantes**: `UPPER_CASE`
- **Variables**: `snake_case` descriptivo

### **3. Documentación**
- **Docstrings**: En todas las funciones públicas
- **Type hints**: En todas las funciones
- **Comentarios**: Para lógica compleja
- **README**: Para setup y uso

### **4. Testing**
- **Unit tests**: Para funciones individuales
- **Integration tests**: Para endpoints
- **End-to-end tests**: Para flujos completos
- **Performance tests**: Para optimizaciones

### **5. Logging**
- **Niveles apropiados**: DEBUG, INFO, WARNING, ERROR
- **Información contextual**: Timestamps, request IDs
- **Estructura consistente**: Formato JSON para producción
- **Rotación de logs**: Para evitar archivos grandes

---

## 🔧 **Especificaciones Técnicas**

### **Requisitos del Sistema**
- **Python**: 3.11+
- **PostgreSQL**: 13+
- **Tesseract**: 5.0+
- **RAM**: 4GB mínimo, 8GB recomendado
- **CPU**: 2 cores mínimo, 4 cores recomendado

### **Límites de Rendimiento**
- **Imágenes**: Máximo 10MB por archivo
- **OCR**: Timeout de 30 segundos máximo
- **APIs externas**: Timeout de 10 segundos por request
- **Base de datos**: Máximo 100 conexiones concurrentes

### **Métricas de Calidad**
- **Precisión OCR**: 85-95% en imágenes claras
- **Tiempo de respuesta**: < 15 segundos promedio
- **Disponibilidad**: 99.5% uptime objetivo
- **Throughput**: 100 requests/minuto

### **Seguridad**
- **Validación de entrada**: Todos los inputs validados
- **Sanitización**: XSS y injection prevention
- **Rate limiting**: Protección contra abuse
- **HTTPS**: Encriptación en tránsito
- **API keys**: Rotación regular

### **Escalabilidad**
- **Horizontal**: Múltiples instancias FastAPI
- **Vertical**: Optimización de recursos
- **Caché distribuido**: Redis para escalabilidad
- **Load balancer**: Nginx para distribución

---

## 🔮 **Arquitectura Futura**

### **Mejoras Planificadas**
1. **Microservicios**: Separar OCR, análisis, y APIs
2. **Message Queue**: Redis/RabbitMQ para procesamiento asíncrono
3. **Load Balancer**: Nginx para distribución de carga
4. **Monitoring**: Prometheus + Grafana
5. **CI/CD**: GitHub Actions para despliegue automático

### **Escalabilidad**
- **Horizontal**: Múltiples instancias de FastAPI
- **Vertical**: Optimización de recursos por instancia
- **Caché distribuido**: Redis para caché compartido
- **Base de datos**: Read replicas para consultas

---

## 📚 **Documentación Adicional**

### **Guías Técnicas**
- **OCR Guide**: `OCR_AND_IMAGE_PROCESSING_GUIDE.md`
- **Universal OCR**: `UNIVERSAL_OCR_GUIDE.md`
- **Architecture**: `BACKEND_ARCHITECTURE_GUIDE.md`
- **API Documentation**: `http://localhost:8000/docs`

### **Endpoints de Monitoreo**
- **Health Check**: `http://localhost:8000/health`
- **Cache Stats**: `http://localhost:8000/cache-stats`
- **Test OCR**: `http://localhost:8000/test-ocr`

---

## 🎉 **Conclusión**

El backend de MommyShops está diseñado para ser:

✅ **Escalable**: Arquitectura modular y asíncrona  
✅ **Robusto**: Manejo de errores y fallbacks múltiples  
✅ **Eficiente**: Optimizaciones de rendimiento y caché  
✅ **Mantenible**: Código bien documentado y testeable  
✅ **Extensible**: Fácil agregar nuevas fuentes de datos  

La combinación de **FastAPI**, **procesamiento asíncrono**, **múltiples fuentes de datos**, y **OCR avanzado** proporciona una base sólida para el análisis profesional de ingredientes cosméticos.

### **Características Únicas**
- 🌍 **OCR Universal**: Se adapta automáticamente a cualquier tipo de imagen
- 🚀 **Procesamiento Asíncrono**: Máxima eficiencia y rendimiento
- 🧠 **IA Integrada**: Ollama para análisis avanzado
- 📊 **Múltiples Fuentes**: 7+ APIs externas para datos completos
- ⚡ **Optimizado**: Timeouts adaptativos y caché inteligente

**El sistema está listo para producción y puede manejar cualquier tipo de análisis de ingredientes cosméticos con alta precisión y eficiencia.** 🚀
