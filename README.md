# MommyShops - Intelligent Cosmetic Analysis Platform

A comprehensive platform for analyzing cosmetic ingredients and providing personalized recommendations using AI and machine learning.

## 🚀 Features

- **Dual Backend Architecture**: Python FastAPI + Java Spring Boot
- **AI-Powered Analysis**: Integration with Ollama for ingredient analysis
- **OCR Capabilities**: Extract ingredient lists from product images
- **External API Integration**: FDA, PubChem, and other safety databases
- **User Authentication**: Firebase + Google OAuth2 integration
- **Real-time Monitoring**: Prometheus + Grafana dashboards
- **Scalable Architecture**: Docker containers with load balancing
- **Comprehensive Testing**: Unit, integration, and E2E tests

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Python API    │    │   Java API      │
│   (Streamlit)   │◄──►│   (FastAPI)     │◄──►│   (Spring Boot) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │     Redis       │    │   Prometheus    │
│   Database      │    │     Cache       │    │   Monitoring    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Technology Stack

### Backend Services
- **Python API**: FastAPI, SQLAlchemy, Alembic, Celery
- **Java API**: Spring Boot, JPA, Spring Security
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Message Queue**: Celery with Redis broker

### AI & ML
- **Ollama**: Local LLM for ingredient analysis
- **OCR**: Tesseract for text extraction from images
- **External APIs**: FDA, PubChem, Google Vision

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Load Balancer**: Nginx
- **Monitoring**: Prometheus + Grafana
- **CI/CD**: GitHub Actions

## 📦 Project Structure

```
mommyshops/
├── backend-python/          # Python FastAPI backend
│   ├── app/
│   │   ├── core/           # Core functionality
│   │   ├── database/       # Database models & session
│   │   ├── middleware/     # Custom middleware
│   │   ├── routers/        # API routes
│   │   ├── security/       # Authentication & authorization
│   │   └── services/       # Business logic services
│   ├── data/              # Static data files
│   ├── migrations/        # Alembic database migrations
│   └── requirements.txt   # Python dependencies
├── backend-java/           # Java Spring Boot backend
│   ├── src/main/java/     # Java source code
│   └── pom.xml           # Maven dependencies
├── docs/                  # Documentation
├── monitoring/            # Prometheus & Grafana configs
├── nginx/                # Nginx configuration
├── scripts/              # Utility scripts
└── docker-compose.yml    # Multi-service orchestration
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Java 17+ (for local development)
- Node.js 18+ (for frontend development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/ArielSanroj/mommyshops.git
   cd mommyshops
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Access the services**
   - Python API: http://localhost:8000
   - Java API: http://localhost:8080
   - Frontend: http://localhost:8501
   - API Documentation: http://localhost:8000/docs
   - Grafana: http://localhost:3000 (admin/admin123)
   - Prometheus: http://localhost:9090

### Local Development

1. **Python Backend**
   ```bash
   cd backend-python
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Java Backend**
   ```bash
   cd backend-java
   ./mvnw spring-boot:run
   ```

3. **Database Setup**
   ```bash
   # Run migrations
   cd backend-python
   alembic upgrade head
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Database
DATABASE_URL=postgresql://mommyshops:secure_password_123@localhost:5432/mommyshops
POSTGRES_DB=mommyshops
POSTGRES_USER=mommyshops
POSTGRES_PASSWORD=secure_password_123

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Security
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_EXPIRATION=3600

# External APIs
FDA_API_KEY=your-fda-api-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# Environment
ENVIRONMENT=development
DEBUG=true
```

### Docker Configuration

The application uses Docker Compose for orchestration. Key services:

- **postgres**: PostgreSQL database
- **redis**: Redis cache and message broker
- **python-backend**: FastAPI application
- **java-backend**: Spring Boot application
- **celery-worker**: Background task processor
- **celery-beat**: Task scheduler
- **prometheus**: Metrics collection
- **grafana**: Monitoring dashboards
- **nginx**: Load balancer and reverse proxy

## 📊 API Documentation

### Python API (FastAPI)

- **Base URL**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Java API (Spring Boot)

- **Base URL**: http://localhost:8080
- **Actuator**: http://localhost:8080/actuator
- **Health Check**: http://localhost:8080/actuator/health

### Key Endpoints

#### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user

#### Analysis
- `POST /analysis/text` - Analyze text for ingredients
- `POST /analysis/image` - Analyze image for ingredients
- `POST /analysis/ingredients` - Analyze ingredient list

#### Health & Monitoring
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed system metrics
- `GET /health/metrics` - Prometheus metrics

## 🧪 Testing

### Running Tests

```bash
# Python tests
cd backend-python
pytest tests/ -v --cov=app --cov-report=html

# Java tests
cd backend-java
./mvnw test

# Integration tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

### Test Coverage

- **Python**: Target 80%+ coverage
- **Java**: Target 80%+ coverage
- **Integration**: End-to-end API testing

## 📈 Monitoring & Observability

### Metrics

- **Application Metrics**: Request rates, response times, error rates
- **System Metrics**: CPU, memory, disk usage
- **Database Metrics**: Connection pool, query performance
- **Cache Metrics**: Hit rates, memory usage

### Dashboards

- **Application Overview**: Key performance indicators
- **Infrastructure**: System resource usage
- **Business Metrics**: User activity, analysis requests

### Alerting

Configure alerts for:
- High error rates (>5%)
- High response times (>2s)
- Database connection issues
- Cache failures
- Disk space warnings

## 🔒 Security

### Authentication & Authorization

- **JWT Tokens**: Secure API access
- **OAuth2**: Google authentication
- **Firebase**: User management
- **Rate Limiting**: Prevent abuse

### Security Headers

- **CORS**: Configured for production domains
- **HSTS**: HTTPS enforcement
- **XSS Protection**: Content Security Policy
- **CSRF**: Cross-site request forgery protection

### Input Validation

- **Pydantic Models**: Request/response validation
- **File Upload**: Size and type restrictions
- **SQL Injection**: Parameterized queries
- **XSS Prevention**: Input sanitization

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**
   ```bash
   export ENVIRONMENT=production
   export DEBUG=false
   export REQUIRE_HTTPS=true
   ```

2. **Database Migration**
   ```bash
   alembic upgrade head
   ```

3. **Start Services**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Scaling

- **Horizontal Scaling**: Multiple container instances
- **Load Balancing**: Nginx round-robin
- **Database**: Read replicas for read-heavy workloads
- **Cache**: Redis cluster for high availability

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use Black for code formatting
- Write comprehensive tests
- Update documentation
- Follow conventional commits

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** - Modern Python web framework
- **Spring Boot** - Java application framework
- **Ollama** - Local LLM integration
- **PostgreSQL** - Reliable database
- **Redis** - High-performance cache
- **Docker** - Containerization platform

## 📞 Support

For support and questions:

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/ArielSanroj/mommyshops/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ArielSanroj/mommyshops/discussions)

---

**MommyShops** - Making cosmetic choices safer and more informed through AI-powered analysis.
