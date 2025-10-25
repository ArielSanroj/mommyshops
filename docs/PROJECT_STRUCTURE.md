# MommyShops Project Structure

## Overview

This document describes the organized project structure for MommyShops, a comprehensive cosmetic ingredient analysis platform.

## Root Directory Structure

```
mommyshops/
├── backend-python/          # Python FastAPI backend
├── backend-java/            # Java Spring Boot backend
├── tests/                   # Comprehensive test suite
├── docs/                    # Documentation
├── scripts/                 # Utility scripts
├── monitoring/              # Monitoring configuration
├── .github/                 # GitHub Actions workflows
├── requirements.txt         # Python dependencies
├── requirements-test.txt    # Python test dependencies
├── pytest.ini             # Pytest configuration
├── env.example             # Environment variables example
└── README.md               # Project overview
```

## Backend Structure

### Python Backend (`backend-python/`)

```
backend-python/
├── core/                    # Core functionality
│   ├── config.py           # Configuration management
│   ├── database.py         # Database connection
│   ├── database_optimization.py  # DB optimization
│   ├── resilience.py       # API resilience
│   ├── logging_config.py   # Structured logging
│   ├── caching.py          # Caching implementation
│   └── metrics.py          # Prometheus metrics
├── api/                    # API layer
│   ├── routes/             # API routes
│   │   ├── analysis.py     # Analysis endpoints
│   │   ├── database_health.py  # DB health endpoints
│   │   └── analysis_documented.py  # Documented endpoints
│   ├── middleware/         # Middleware
│   └── openapi_config.py   # OpenAPI configuration
├── services/               # Business logic
│   ├── ocr_service.py      # OCR functionality
│   ├── ingredient_service.py  # Ingredient analysis
│   └── analysis_service.py # Product analysis
├── models/                 # Data models
├── utils/                  # Utility functions
├── main.py                 # Application entry point
└── requirements.txt        # Dependencies
```

### Java Backend (`backend-java/`)

```
backend-java/
├── src/
│   ├── main/
│   │   ├── java/com/mommyshops/
│   │   │   ├── controller/     # REST controllers
│   │   │   ├── service/        # Business logic
│   │   │   ├── repository/     # Data access
│   │   │   ├── model/          # Data models
│   │   │   ├── config/         # Configuration
│   │   │   ├── cache/          # Caching
│   │   │   ├── metrics/        # Metrics
│   │   │   └── resilience/     # Resilience patterns
│   │   └── resources/
│   │       ├── application.properties
│   │       └── application-integration.yml
│   └── test/
│       └── java/com/mommyshops/
│           ├── controller/     # Controller tests
│           ├── service/        # Service tests
│           └── integration/    # Integration tests
├── pom.xml                 # Maven configuration
└── Dockerfile             # Container configuration
```

## Test Structure (`tests/`)

```
tests/
├── unit/                   # Unit tests
│   ├── services/          # Service unit tests
│   └── api/               # API unit tests
├── integration/           # Integration tests
│   ├── test_java_python_integration.py
│   └── test_database_integration.py
├── e2e/                   # End-to-end tests
│   └── test_complete_analysis_flow.py
├── conftest.py           # Test configuration
└── fixtures/             # Test fixtures
```

## Documentation (`docs/`)

```
docs/
├── api/                   # API documentation
│   ├── API_REFERENCE.md
│   └── openapi.yaml
├── architecture/         # Architecture docs
│   ├── ARCHITECTURE.md
│   └── SYSTEM_DESIGN.md
├── deployment/           # Deployment docs
│   ├── DEPLOYMENT_GUIDE.md
│   └── DOCKER_GUIDE.md
├── testing/              # Testing docs
│   ├── TESTING_GUIDE.md
│   └── TEST_STRATEGY.md
├── monitoring/           # Monitoring docs
│   ├── MONITORING_GUIDE.md
│   └── METRICS_GUIDE.md
├── security/             # Security docs
│   ├── SECURITY_GUIDE.md
│   └── SECURITY_CRITICAL_FIXES.md
├── database/             # Database docs
│   ├── DATABASE_OPTIMIZATION_GUIDE.md
│   └── DATABASE_SCHEMA.md
├── resilience/           # Resilience docs
│   └── RESILIENCE_GUIDE.md
├── logging/              # Logging docs
│   └── LOGGING_GUIDE.md
├── ci-cd/               # CI/CD docs
│   └── CI_CD_GUIDE.md
└── user/               # User docs
    ├── USER_GUIDE.md
    └── API_USAGE.md
```

## Scripts (`scripts/`)

```
scripts/
├── setup/               # Setup scripts
│   ├── setup_development.sh
│   ├── setup_production.sh
│   └── setup_monitoring.sh
├── deployment/          # Deployment scripts
│   ├── deploy_staging.sh
│   ├── deploy_production.sh
│   └── rollback.sh
├── maintenance/         # Maintenance scripts
│   ├── backup_database.sh
│   ├── cleanup_logs.sh
│   └── update_dependencies.sh
├── testing/            # Testing scripts
│   ├── run_tests.py
│   ├── run_integration_tests.py
│   └── run_e2e_tests.py
└── monitoring/         # Monitoring scripts
    ├── health_check.sh
    ├── performance_test.sh
    └── security_scan.sh
```

## Monitoring (`monitoring/`)

```
monitoring/
├── grafana/             # Grafana dashboards
│   └── dashboards/
│       └── mommyshops-overview.json
├── prometheus/          # Prometheus configuration
│   ├── prometheus.yml
│   └── rules/
├── alertmanager/       # Alertmanager configuration
│   └── alertmanager.yml
└── docker/             # Monitoring Docker setup
    └── docker-compose.monitoring.yml
```

## GitHub Actions (`.github/workflows/`)

```
.github/workflows/
├── python-tests.yml    # Python test workflow
├── java-tests.yml      # Java test workflow
├── deploy.yml         # Deployment workflow
├── security.yml       # Security scan workflow
└── performance.yml     # Performance test workflow
```

## Configuration Files

### Root Level
- `requirements.txt` - Python dependencies
- `requirements-test.txt` - Python test dependencies
- `pytest.ini` - Pytest configuration
- `env.example` - Environment variables template
- `README.md` - Project overview

### Python Backend
- `backend-python/requirements.txt` - Python dependencies
- `backend-python/main.py` - Application entry point
- `backend-python/core/config.py` - Configuration management

### Java Backend
- `backend-java/pom.xml` - Maven configuration
- `backend-java/src/main/resources/application.properties` - Spring configuration
- `backend-java/Dockerfile` - Container configuration

## Key Features by Directory

### Core Functionality
- **Configuration Management**: Centralized config with environment variables
- **Database Optimization**: Connection pooling, indexing, query optimization
- **Resilience**: Circuit breakers, retry logic, caching
- **Logging**: Structured JSON logging with secret sanitization
- **Metrics**: Prometheus metrics and Grafana dashboards

### API Layer
- **REST Endpoints**: Comprehensive API with OpenAPI documentation
- **Health Checks**: Database, Redis, and application health
- **Authentication**: JWT-based authentication
- **Rate Limiting**: API rate limiting and throttling

### Services
- **OCR Service**: Image text extraction
- **Ingredient Service**: Ingredient analysis and scoring
- **Analysis Service**: Product analysis and recommendations

### Testing
- **Unit Tests**: Comprehensive unit test coverage
- **Integration Tests**: Service integration testing
- **E2E Tests**: End-to-end testing
- **Performance Tests**: Load and stress testing

### Monitoring
- **Health Monitoring**: Application and service health
- **Performance Monitoring**: Metrics and dashboards
- **Security Monitoring**: Vulnerability scanning
- **Log Aggregation**: Centralized logging

## Best Practices

### 1. Directory Organization
- **Separation of Concerns**: Clear separation between layers
- **Modular Structure**: Modular and maintainable code
- **Consistent Naming**: Consistent naming conventions
- **Documentation**: Comprehensive documentation

### 2. Code Organization
- **Single Responsibility**: Each module has a single responsibility
- **Dependency Injection**: Loose coupling between components
- **Error Handling**: Comprehensive error handling
- **Logging**: Structured logging throughout

### 3. Testing Strategy
- **Test Coverage**: High test coverage (80%+)
- **Test Types**: Unit, integration, and E2E tests
- **Test Data**: Isolated test data and fixtures
- **Test Automation**: Automated test execution

### 4. Deployment
- **Containerization**: Docker containers for all services
- **Environment Management**: Environment-specific configurations
- **Health Checks**: Comprehensive health checking
- **Rollback Strategy**: Safe rollback procedures

## Maintenance

### Regular Tasks
- **Dependency Updates**: Regular dependency updates
- **Security Scanning**: Regular security vulnerability scanning
- **Performance Monitoring**: Continuous performance monitoring
- **Log Rotation**: Regular log cleanup and rotation

### Monitoring
- **Health Checks**: Regular health check monitoring
- **Performance Metrics**: Continuous performance monitoring
- **Error Tracking**: Error rate and pattern monitoring
- **Resource Usage**: Resource utilization monitoring

## Conclusion

This organized project structure provides a solid foundation for the MommyShops platform, with clear separation of concerns, comprehensive testing, and robust monitoring capabilities.
