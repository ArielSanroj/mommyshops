# Estructura del Proyecto MommyShops

## 📁 Estructura Reorganizada

```
mommyshops/
├── 📁 backend-python/           # Backend Python (FastAPI)
│   ├── 📁 api/                  # API routes
│   │   └── 📁 routes/           # Route modules
│   ├── 📁 core/                 # Core configuration
│   ├── 📁 services/             # Business logic
│   ├── 📁 models/               # Pydantic models
│   ├── 📁 middleware/           # Custom middleware
│   ├── 📁 database/             # Database models
│   ├── 📄 main.py               # FastAPI app entry point
│   ├── 📄 requirements.txt      # Python dependencies
│   └── 📄 Dockerfile            # Python container
│
├── 📁 backend-java/             # Backend Java (Spring Boot)
│   ├── 📁 src/main/java/        # Java source code
│   │   └── 📁 com/mommyshops/   # Package structure
│   ├── 📁 src/test/java/        # Java tests
│   ├── 📁 src/main/resources/   # Configuration files
│   ├── 📄 pom.xml               # Maven dependencies
│   └── 📄 Dockerfile            # Java container
│
├── 📁 tests-shared/              # Shared tests
│   ├── 📁 integration/           # Integration tests
│   ├── 📁 unit/                 # Unit tests
│   └── 📁 e2e/                  # End-to-end tests
│
├── 📁 docs/                     # Documentation
│   ├── 📁 diagrams/              # Architecture diagrams
│   ├── 📄 ARCHITECTURE.md       # System architecture
│   ├── 📄 API_DOCS.md           # API documentation
│   └── 📄 DEPLOYMENT_GUIDE.md   # Deployment guide
│
├── 📁 monitoring/               # Monitoring configuration
│   ├── 📄 prometheus.yml        # Prometheus config
│   └── 📁 grafana/              # Grafana dashboards
│
├── 📁 nginx/                     # Load balancer config
│   └── 📄 nginx.conf            # Nginx configuration
│
├── 📄 docker-compose.yml        # Multi-service orchestration
├── 📄 Makefile                  # Development commands
├── 📄 .pre-commit-config.yaml   # Pre-commit hooks
└── 📄 README.md                  # Project overview
```

## 🏗️ Arquitectura por Capas

### 1. **Frontend Layer**
- **Vaadin UI** (Puerto 8080)
- Responsive design
- Real-time updates
- Progressive Web App (PWA)

### 2. **API Gateway Layer**
- **Java Spring Boot** (Puerto 8080)
- Authentication & Authorization
- Rate limiting
- Request routing
- Business logic

### 3. **AI/ML Processing Layer**
- **Python FastAPI** (Puerto 8000)
- OCR processing
- AI analysis
- External API integration
- Background tasks

### 4. **Data Layer**
- **PostgreSQL** (Puerto 5432) - Primary database
- **Redis** (Puerto 6379) - Caching layer
- **Firebase** - Real-time data & auth

### 5. **Infrastructure Layer**
- **Docker** - Containerization
- **Nginx** - Load balancer
- **Prometheus** - Metrics collection
- **Grafana** - Monitoring dashboards

## 🔄 Flujo de Comunicación

```
User → Vaadin UI → Java Backend → Python Backend → External APIs
  ↓         ↓           ↓              ↓
Cache ← Database ← Analysis ← AI/ML Processing
```

## 📊 Responsabilidades por Stack

### **Java Backend (Business Logic)**
- ✅ User authentication & authorization
- ✅ Business rules & validation
- ✅ API Gateway functionality
- ✅ Rate limiting & security
- ✅ Database operations
- ✅ Cache management (L1)
- ✅ UI rendering (Vaadin)

### **Python Backend (AI/ML)**
- ✅ Image processing & OCR
- ✅ AI analysis (Ollama, Nemotron)
- ✅ External API integration
- ✅ Background tasks (Celery)
- ✅ Cache management (L2)
- ✅ Data processing

## 🚀 Deployment Strategy

### **Development**
```bash
# Start all services
make dev-up

# Run tests
make test

# Code quality
make lint
```

### **Production**
```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# Monitor services
make monitor
```

## 📈 Monitoring & Observability

### **Metrics**
- Request latency & throughput
- Error rates & status codes
- Cache hit/miss ratios
- Database performance
- AI processing times

### **Logging**
- Structured JSON logging
- Secret sanitization
- Request tracing
- Error correlation

### **Health Checks**
- Service availability
- Database connectivity
- External API status
- Cache performance

## 🔧 Development Workflow

### **Code Quality**
- Pre-commit hooks
- Automated testing
- Code coverage (80%+)
- Security scanning
- Performance profiling

### **Testing Strategy**
- Unit tests (80%+ coverage)
- Integration tests
- End-to-end tests
- Performance tests
- Security tests

### **CI/CD Pipeline**
- Automated builds
- Quality gates
- Security scanning
- Deployment automation
- Rollback capabilities

## 📋 Environment Configuration

### **Development**
- Local database
- Mock external APIs
- Debug logging
- Hot reload

### **Production**
- Managed database
- Real external APIs
- Structured logging
- Performance monitoring

## 🎯 Next Steps

1. **Complete Migration**
   - Move remaining files to new structure
   - Update import paths
   - Test all functionality

2. **Performance Optimization**
   - Implement L3 cache
   - Async processing
   - Query optimization

3. **Monitoring Setup**
   - Configure Prometheus
   - Create Grafana dashboards
   - Set up alerts

4. **Documentation**
   - API documentation
   - Deployment guides
   - User manuals
