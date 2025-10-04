# 🏗️ Guía de Arquitectura del Backend - MommyShops

## 🎯 **Visión General**

MommyShops es un sistema de análisis de ingredientes cosméticos que combina **OCR avanzado**, **múltiples fuentes de datos**, y **análisis de seguridad** para proporcionar recomendaciones personalizadas sobre productos cosméticos.

---

## 🏛️ **Arquitectura General**

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

### **Stack Tecnológico**
- **Framework**: FastAPI (Python 3.11+)
- **Base de Datos**: PostgreSQL con SQLAlchemy ORM
- **OCR**: Tesseract + pytesseract
- **Procesamiento de Imágenes**: PIL/Pillow + NumPy + SciPy
- **APIs Externas**: httpx (async HTTP client)
- **Logging**: Python logging + structlog
- **Validación**: Pydantic v2

---

## 🔧 **Estructura del Proyecto**

```
mommyshops/
├── main.py                          # Aplicación principal FastAPI
├── database.py                      # Modelos y conexión DB
├── api_utils_production.py          # Utilidades para APIs externas
├── llm_utils.py                     # Integración con OpenAI
├── nemotron_integration.py          # Integración con NVIDIA Nemotron
├── apify_enhanced_scraper.py        # Web scraping avanzado
├── requirements.txt                 # Dependencias Python
├── .env                            # Variables de entorno
├── test_ocr_debug.py               # Script de diagnóstico
├── fix_dependencies.sh             # Script de instalación
└── docs/
    ├── OCR_AND_IMAGE_PROCESSING_GUIDE.md
    └── BACKEND_ARCHITECTURE_GUIDE.md
```

---

## 🚀 **Aplicación Principal (main.py)**

### **Configuración Inicial**
```python
app = FastAPI(
    title="MommyShops - Cosmetic Ingredient Analysis",
    description="Professional cosmetic ingredient safety analysis with 10+ data sources",
    version="2.0.0"
)
```

### **Eventos de Startup**
```python
@app.on_event("startup")
async def startup_event():
    """Configure connection limits on startup."""
    httpx._config.DEFAULT_LIMITS = httpx.Limits(
        max_keepalive_connections=20,
        max_connections=100,
        keepalive_expiry=30.0
    )
```

### **Verificación de Dependencias**
```python
# Check for critical dependencies
try:
    import numpy as np
    from scipy.ndimage import uniform_filter
    ADVANCED_PROCESSING = True
except ImportError:
    ADVANCED_PROCESSING = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
```

---

## 📊 **Modelos de Datos (Pydantic)**

### **Request Models**
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

---

## 🗄️ **Base de Datos (database.py)**

### **Modelo de Ingrediente**
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

### **Conexión y Sesiones**
```python
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### **Funciones de Consulta**
```python
def get_ingredient_data(ingredient_name: str) -> Optional[Dict]:
    """Get ingredient data from local database."""
    
def get_all_ingredients() -> List[Ingredient]:
    """Get all ingredients from database."""
```

---

## 🌐 **APIs Externas (api_utils_production.py)**

### **Fuentes de Datos**
1. **FDA (Food and Drug Administration)**
2. **EWG (Environmental Working Group)**
3. **CIR (Cosmetic Ingredient Review)**
4. **SCCS (Scientific Committee on Consumer Safety)**
5. **ICCR (International Cooperation on Cosmetics Regulation)**
6. **PubChem (NIH)**
7. **INCI Beauty Database**

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

### **Sistema de Caché**
```python
# Caché por archivo JSON
CIR_CACHE_FILE = "cir_cache.json"
EWG_CACHE_FILE = "ewg_cache.json"
SCCS_CACHE_FILE = "sccs_cache.json"
ICCR_CACHE_FILE = "iccr_cache.json"

def load_cache(cache_file: str) -> Dict:
    """Load cache from JSON file."""
    
def save_cache(cache_file: str, data: Dict):
    """Save cache to JSON file."""
```

---

## 🤖 **Integración con LLMs**

### **OpenAI Integration (llm_utils.py)**
```python
async def extract_ingredients_from_text_openai(text: str) -> List[str]:
    """Extract ingredients using OpenAI GPT."""
    
async def enrich_ingredient_data(data: Dict, user_need: str) -> Dict:
    """Enrich ingredient data with OpenAI analysis."""
```

### **NVIDIA Nemotron Integration**
```python
async def analyze_with_nemotron(ingredient: str, image_data: Optional[bytes], user_need: str) -> Dict:
    """Analyze ingredient using NVIDIA Nemotron multimodal AI."""
```

---

## 🔍 **Procesamiento de Imágenes**

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

---

## 🎯 **Endpoints de la API**

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

## 🔒 **Manejo de Errores**

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
```python
logger.info(f"Starting analysis for {file.filename}")
logger.info(f"Image data size: {len(image_data)} bytes")
logger.error(f"Error analyzing image: {e}", exc_info=True)
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

## 📈 **Monitoreo y Métricas**

### **Health Checks**
```python
@app.get("/health")
async def health():
    """Comprehensive health check."""
    health_status = await health_check()
    return {
        "status": "healthy",
        "timestamp": health_status.get("timestamp"),
        "apis": health_status.get("apis", {}),
        "cache_stats": health_status.get("cache_stats", {})
    }
```

### **Estadísticas de Caché**
```python
@app.get("/cache-stats")
async def cache_stats():
    """Get cache performance statistics."""
    stats = get_cache_stats()
    return stats
```

---

## 🚀 **Despliegue y Configuración**

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

- **OCR Guide**: `OCR_AND_IMAGE_PROCESSING_GUIDE.md`
- **API Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`
- **Cache Stats**: `http://localhost:8000/cache-stats`

---

## 🎉 **Conclusión**

El backend de MommyShops está diseñado para ser:
- **Escalable**: Arquitectura modular y asíncrona
- **Robusto**: Manejo de errores y fallbacks múltiples
- **Eficiente**: Optimizaciones de rendimiento y caché
- **Mantenible**: Código bien documentado y testeable
- **Extensible**: Fácil agregar nuevas fuentes de datos

La combinación de **FastAPI**, **procesamiento asíncrono**, **múltiples fuentes de datos**, y **OCR avanzado** proporciona una base sólida para el análisis profesional de ingredientes cosméticos.