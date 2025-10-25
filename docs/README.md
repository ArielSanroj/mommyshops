# MommyShops - Cosmetic Ingredient Safety Analysis Platform

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Java](https://img.shields.io/badge/Java-17+-orange.svg)](https://www.oracle.com/java/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.2+-brightgreen.svg)](https://spring.io/projects/spring-boot)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Tabla de Contenidos

- [Descripción](#descripción)
- [Arquitectura](#arquitectura)
- [Características Principales](#características-principales)
- [Requisitos del Sistema](#requisitos-del-sistema)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Testing](#testing)
- [Documentación API](#documentación-api)
- [Contribución](#contribución)
- [Licencia](#licencia)

## 🎯 Descripción

**MommyShops** es una plataforma profesional de análisis de seguridad de ingredientes cosméticos que combina:

- 🔬 **OCR avanzado** para extraer ingredientes de imágenes de productos
- 🤖 **Inteligencia Artificial** (Ollama, NVIDIA Nemotron) para análisis semántico
- 🌍 **APIs externas** (FDA, EWG, PubChem, COSING, IARC, INVIMA) para datos científicos
- 📊 **Machine Learning** para recomendaciones personalizadas
- 🔒 **Seguridad de nivel empresarial** con autenticación JWT y Firebase

### Problema que Resuelve

Los consumidores conscientes necesitan entender la seguridad de los ingredientes en productos cosméticos, pero:
- Las etiquetas son difíciles de leer
- Los ingredientes tienen nombres técnicos complejos (nomenclatura INCI)
- La información de seguridad está dispersa en múltiples fuentes
- No hay recomendaciones personalizadas según tipo de piel o condiciones especiales

**MommyShops** soluciona esto proporcionando análisis instantáneo, comprensible y personalizado.

## 🏗️ Arquitectura

### Stack Tecnológico

#### Backend Python (Puerto 8000) - "AI & Data Processing"
- **Framework**: FastAPI 0.109+
- **OCR**: Tesseract, Google Vision API
- **AI/ML**: Ollama (Llama 3.1, LLaVA), NVIDIA Nemotron
- **Base de Datos**: PostgreSQL (SQLAlchemy ORM)
- **Cache**: Redis
- **Autenticación**: Firebase Admin SDK, JWT

#### Backend Java (Puerto 8080) - "Business Logic & API Gateway"
- **Framework**: Spring Boot 3.2+
- **Frontend**: Vaadin Flow
- **Cliente HTTP**: WebClient (Spring WebFlux)
- **Base de Datos**: PostgreSQL (JPA/Hibernate)
- **Cache**: Caffeine, Redis
- **Seguridad**: Spring Security, JWT

### Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Vaadin)                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP/REST
┌──────────────────────────▼──────────────────────────────────────┐
│              JAVA BACKEND (Spring Boot - :8080)                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ • API Gateway                                             │  │
│  │ • Business Logic                                          │  │
│  │ • Authentication & Authorization                          │  │
│  │ • Rate Limiting & Circuit Breakers                        │  │
│  │ • User Management                                         │  │
│  └────────────────┬─────────────────────────────────────────┘  │
└───────────────────┼────────────────────────────────────────────┘
                    │ WebClient (HTTP)
┌───────────────────▼────────────────────────────────────────────┐
│           PYTHON BACKEND (FastAPI - :8000)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ • OCR Processing (Tesseract, Google Vision)              │  │
│  │ • AI/ML Analysis (Ollama, Nemotron)                      │  │
│  │ • External API Integration                                │  │
│  │ • Data Enrichment & Scraping                             │  │
│  │ • Firebase Sync                                           │  │
│  └────────────────┬─────────────────────────────────────────┘  │
└───────────────────┼────────────────────────────────────────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
    ┌────▼─────┐         ┌────▼──────┐
    │PostgreSQL│         │  Firebase  │
    │          │         │ Firestore  │
    └──────────┘         └───────────┘
         │
    ┌────▼─────┐
    │  Redis   │
    │  Cache   │
    └──────────┘
```

### Flujos de Datos Principales

#### 1. Análisis de Imagen de Producto
```
Usuario → Vaadin → Java → Python (OCR) → Python (APIs externas) → 
Python (AI Analysis) → Java (Business Logic) → Vaadin → Usuario
```

#### 2. Consulta de Ingrediente
```
Usuario → Vaadin → Java (Cache check) → Python (API calls) → 
Java (Store in cache) → Vaadin → Usuario
```

#### 3. Recomendaciones Personalizadas
```
Usuario → Vaadin → Java (Profile) → Python (ML Model) → 
Python (Ollama AI) → Java (Format) → Vaadin → Usuario
```

## ✨ Características Principales

### 🔍 Análisis de Productos

- **OCR Multimodal**: Extracción de texto de imágenes con múltiples engines
- **Análisis de Ingredientes**: Información detallada de cada componente
- **Scoring de Seguridad**: Puntuación EWG (1-10) y niveles de riesgo
- **Restricciones Regulatorias**: Verificación según COSING, FDA, INVIMA

### 🤖 Inteligencia Artificial

- **Ollama Local**: Análisis semántico con Llama 3.1
- **NVIDIA Nemotron**: Análisis multimodal de imágenes
- **Recomendaciones Personalizadas**: Basadas en perfil de usuario y condiciones especiales

### 🔒 Seguridad

- **Autenticación Multi-Factor**: JWT + Firebase Authentication
- **CORS Restrictivo**: Orígenes configurables
- **Rate Limiting**: 100 req/min, 10 req/seg burst
- **Validación de Archivos**: Tipo MIME real, tamaño máximo, extensiones permitidas
- **Sanitización de Logs**: Secretos y passwords automáticamente redactados
- **Password Policies**: Requisitos de complejidad (8+ chars, upper, lower, digit, special)

### 📊 Datos y APIs

Integración con más de 10 fuentes de datos científicos:

- **FDA** (Food and Drug Administration)
- **EWG** (Environmental Working Group)
- **PubChem** (Chemical Database)
- **COSING** (EU Cosmetic Ingredients Database)
- **IARC** (International Agency for Research on Cancer)
- **INVIMA** (Instituto Nacional de Vigilancia de Medicamentos - Colombia)
- **Skin Deep Database**
- **Google Vision API**

## 📦 Requisitos del Sistema

### Software

- **Python**: 3.9 o superior
- **Java**: 17 o superior (LTS)
- **PostgreSQL**: 13 o superior
- **Redis**: 6 o superior (opcional, recomendado)
- **Tesseract OCR**: 4.1 o superior
- **Maven**: 3.8 o superior
- **Node.js**: 16+ (para Vaadin frontend)

### Hardware (Recomendado)

- **CPU**: 4+ cores
- **RAM**: 8GB+ (16GB recomendado con Ollama)
- **Disco**: 20GB+ libre
- **GPU**: Opcional (acelera Ollama y ML)

### Servicios Externos (Opcionales)

- **Firebase**: Para autenticación y Firestore
- **Ollama**: Para análisis AI local
- **Google Cloud**: Para Vision API

## 🚀 Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/yourusername/mommyshops.git
cd mommyshops
```

### 2. Configurar PostgreSQL

```bash
# Crear base de datos
createdb mommyshops

# O usando SQL
psql -U postgres
CREATE DATABASE mommyshops;
CREATE USER mommyshops WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE mommyshops TO mommyshops;
```

### 3. Backend Python

```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Instalar Tesseract OCR
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-spa

# macOS
brew install tesseract tesseract-lang

# Windows
# Descargar de https://github.com/UB-Mannheim/tesseract/wiki
```

### 4. Backend Java

```bash
cd mommyshops-app

# Compilar y empaquetar
mvn clean install -DskipTests

# O ejecutar directamente
mvn spring-boot:run
```

### 5. Configurar Variables de Entorno

Copiar `.env.example` a `.env` y configurar:

```bash
cp env.example .env
nano .env  # O tu editor preferido
```

Ver sección [Configuración](#configuración) para detalles.

### 6. Inicializar Base de Datos

```bash
# Python - crear tablas
python -c "from backend.core.database import create_tables; create_tables()"

# Java - las migraciones se ejecutan automáticamente con Hibernate
```

### 7. Iniciar Servicios

#### Terminal 1 - Python Backend
```bash
cd /workspaces/mommyshops
source venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Terminal 2 - Java Backend
```bash
cd mommyshops-app
mvn spring-boot:run
```

#### Terminal 3 - Redis (opcional pero recomendado)
```bash
redis-server
```

#### Terminal 4 - Ollama (opcional)
```bash
ollama serve
ollama pull llama3.1
ollama pull llava
```

### 8. Verificar Instalación

```bash
# Python Backend Health Check
curl http://localhost:8000/health

# Java Backend Health Check
curl http://localhost:8080/api/health

# Frontend (Vaadin)
open http://localhost:8080
```

## ⚙️ Configuración

### Variables de Entorno Principales

#### Base de Datos

```env
DATABASE_URL=postgresql://mommyshops:password@localhost:5432/mommyshops
DB_USERNAME=mommyshops
DB_PASSWORD=your_secure_password
```

#### Redis

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=optional_password
```

#### Seguridad

```env
JWT_SECRET=your_very_secure_random_secret_key_min_32_chars
JWT_EXPIRATION=3600
JWT_ALGORITHM=HS256
```

#### CORS

```env
CORS_ORIGINS=http://localhost:8080,http://localhost:3000
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
TRUSTED_HOSTS=localhost,127.0.0.1
```

#### APIs Externas

```env
FDA_API_KEY=your_fda_api_key
EWG_API_KEY=your_ewg_api_key
GOOGLE_VISION_API_KEY=your_google_vision_key
```

#### Firebase (Opcional)

```env
FIREBASE_CREDENTIALS={"type":"service_account","project_id":"..."}
# O
FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/firebase-service-account.json
```

#### Ollama

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
OLLAMA_VISION_MODEL=llava
OLLAMA_TIMEOUT=120
```

#### File Upload

```env
MAX_UPLOAD_SIZE=5242880  # 5MB
ALLOWED_IMAGE_EXTENSIONS=.jpg,.jpeg,.png,.webp
```

### Configuración de Java (application.properties)

Ver archivo: `mommyshops-app/src/main/resources/application.properties`

Propiedades importantes:

```properties
# Database
spring.datasource.url=jdbc:postgresql://localhost:5432/mommyshops
spring.jpa.hibernate.ddl-auto=validate  # NUNCA usar 'create' en producción

# Python Backend
python.backend.url=http://localhost:8000
python.backend.timeout=30000

# Ollama
ollama.base.url=http://localhost:11434
```

## 🎮 Uso

### API REST - Python Backend

#### Analizar Imagen de Producto

```bash
curl -X POST http://localhost:8000/java-integration/analyze-image \
  -F "file=@product_image.jpg" \
  -F "user_need=sensitive skin"
```

#### Analizar Texto de Ingredientes

```bash
curl -X POST http://localhost:8000/analyze-text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Aqua, Glycerin, Sodium Chloride",
    "user_need": "acne prone skin"
  }'
```

### API REST - Java Backend

#### Obtener Información de Ingrediente (INCI)

```bash
curl http://localhost:8080/api/inci/ingredient/Aqua
```

#### Análisis con Sustituciones

```bash
curl -X POST http://localhost:8080/api/substitution/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "ingredients": ["Paraben", "Sodium Lauryl Sulfate"],
    "userProfile": {
      "skinType": "sensitive",
      "concerns": ["irritation"]
    }
  }'
```

### Frontend Vaadin

Acceder a: `http://localhost:8080`

1. **Registro/Login**: Crear cuenta o iniciar sesión
2. **Subir Imagen**: Fotografiar o subir imagen de producto
3. **Ver Análisis**: Resultados detallados con scoring y recomendaciones
4. **Explorar Ingredientes**: Buscar ingredientes específicos
5. **Perfil**: Configurar tipo de piel y preferencias

## 🧪 Testing

### Tests Python

```bash
# Ejecutar todos los tests con coverage
pytest

# Tests específicos
pytest tests/unit/
pytest tests/integration/
pytest tests/unit/test_security.py

# Con coverage detallado
pytest --cov=backend --cov-report=html
open htmlcov/index.html

# Tests por markers
pytest -m unit  # Solo unit tests
pytest -m integration  # Solo integration tests
```

### Tests Java

```bash
cd mommyshops-app

# Ejecutar todos los tests
mvn test

# Con coverage
mvn clean test jacoco:report

# Ver reporte
open target/site/jacoco/index.html

# Tests específicos
mvn test -Dtest=ProductAnalysisControllerTest
```

### Coverage Mínimo Requerido

- **Python**: 80%+
- **Java**: 70%+

## 📚 Documentación API

### Documentación Interactiva

- **Python FastAPI**: http://localhost:8000/docs (Swagger UI)
- **Python ReDoc**: http://localhost:8000/redoc
- **Java REST**: http://localhost:8080/swagger-ui.html (si configurado)

### Endpoints Principales

Ver documentación completa en: [docs/ENDPOINTS_MAPPING.md](docs/ENDPOINTS_MAPPING.md)

#### Python Endpoints

- `POST /java-integration/analyze-image` - Análisis de imagen (para Java)
- `POST /analyze-text` - Análisis de texto
- `GET /health` - Health check
- `POST /auth/register` - Registro de usuario
- `POST /auth/token` - Login JWT

#### Java Endpoints

- `POST /api/analysis/analyze-product` - Análisis completo
- `GET /api/inci/ingredient/{name}` - Información INCI
- `POST /api/substitution/alternatives` - Alternativas
- `GET /api/health` - Health check completo

## 🏗️ Estructura del Proyecto

```
mommyshops/
├── backend/                    # Backend Python (FastAPI)
│   ├── api/
│   │   └── routes/            # Endpoints organizados
│   │       ├── auth.py
│   │       ├── analysis.py
│   │       ├── ollama.py
│   │       └── health.py
│   ├── core/                  # Configuración central
│   │   ├── config.py          # Settings
│   │   ├── security.py        # Seguridad (JWT, passwords)
│   │   ├── database.py        # ORM
│   │   └── logging_config.py  # Logs con sanitización
│   ├── services/              # Lógica de negocio
│   │   ├── ocr_service.py
│   │   ├── ingredient_service.py
│   │   ├── ml_service.py
│   │   ├── ollama_service.py
│   │   └── sync_service.py    # Dual-write Firebase/PG
│   ├── models/                # Pydantic models
│   │   ├── requests.py
│   │   └── responses.py
│   ├── middleware/            # Middleware custom
│   │   └── rate_limit.py
│   └── main.py                # Entry point
├── mommyshops-app/            # Backend Java (Spring Boot + Vaadin)
│   ├── src/main/java/com/mommyshops/
│   │   ├── controller/        # REST Controllers
│   │   ├── service/           # Business logic
│   │   ├── repository/        # JPA Repositories
│   │   ├── domain/            # Entities & DTOs
│   │   ├── config/            # Spring Config
│   │   ├── integration/       # External services
│   │   │   └── client/
│   │   │       └── PythonBackendClient.java
│   │   └── security/          # Spring Security
│   └── src/main/resources/
│       └── application.properties
├── tests/                     # Tests Python
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── docs/                      # Documentación
│   ├── ARCHITECTURE.md
│   ├── ENDPOINTS_MAPPING.md
│   └── API_DOCS.md
├── config/                    # Configuración
│   ├── application.yml
│   ├── application-dev.yml
│   └── application-prod.yml
├── requirements.txt           # Dependencias Python
├── pytest.ini                 # Configuración pytest
├── pyproject.toml             # Python project config
├── .env.example               # Variables de entorno ejemplo
└── README.md                  # Este archivo
```

## 🤝 Contribución

### Flujo de Trabajo

1. Fork del repositorio
2. Crear branch feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

### Estándares de Código

#### Python
- **Estilo**: PEP 8, Black formatter
- **Imports**: isort
- **Type hints**: Obligatorios
- **Docstrings**: Google style
- **Linting**: flake8, pylint, mypy

#### Java
- **Estilo**: Google Java Style Guide
- **Formatter**: google-java-format
- **Linting**: Checkstyle
- **Tests**: JUnit 5, Mockito

### Pre-commit Hooks

```bash
# Instalar pre-commit
pip install pre-commit

# Instalar hooks
pre-commit install

# Ejecutar manualmente
pre-commit run --all-files
```

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver archivo [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

- [FastAPI](https://fastapi.tiangolo.com/)
- [Spring Boot](https://spring.io/projects/spring-boot)
- [Vaadin](https://vaadin.com/)
- [Ollama](https://ollama.ai/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- Comunidades de Open Source

## 📞 Contacto

**Proyecto**: MommyShops  
**Mantenedor**: [Tu Nombre]  
**Email**: contact@mommyshops.com  
**Website**: https://mommyshops.com

## 🗺️ Roadmap

### v3.1 (Próxima Versión)
- [ ] Soporte para más idiomas (OCR multilenguaje)
- [ ] App móvil (React Native)
- [ ] Análisis por voz
- [ ] Comparador de productos

### v3.2
- [ ] Blockchain para trazabilidad
- [ ] Integración con e-commerce
- [ ] API pública para terceros
- [ ] Dashboard analytics

### v4.0
- [ ] Microservicios completos
- [ ] Kubernetes deployment
- [ ] GraphQL API
- [ ] ML model marketplace

---

**Made with ❤️ for conscious consumers**


