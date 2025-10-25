# CI/CD Pipeline Guide

## Overview

This guide covers the comprehensive CI/CD pipeline implementation for MommyShops, including automated testing, security scanning, and deployment workflows.

## Pipeline Architecture

### Workflow Structure
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Python Tests  │    │   Java Tests    │    │  Security Scan  │
│                 │    │                 │    │                 │
│ • Unit Tests    │    │ • Unit Tests    │    │ • Bandit        │
│ • Integration   │    │ • Integration   │    │ • Safety        │
│ • E2E Tests     │    │ • E2E Tests     │    │ • Semgrep       │
│ • Linting       │    │ • Checkstyle    │    │ • Trivy         │
│ • Security      │    │ • SpotBugs      │    │ • CodeQL        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │    Deploy       │
                    │                 │
                    │ • Build Images  │
                    │ • Push to GHCR  │
                    │ • Deploy Staging│
                    │ • Deploy Prod   │
                    │ • Health Checks │
                    └─────────────────┘
```

## Workflows

### 1. Python Tests (`python-tests.yml`)

#### Triggers
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Changes to Python backend files

#### Jobs
1. **Test Matrix**
   - Python versions: 3.9, 3.10, 3.11
   - Services: PostgreSQL, Redis
   - Steps: Linting, Security, Tests, Coverage

2. **Integration Tests**
   - Python 3.11
   - Full service stack
   - Integration test suite

3. **E2E Tests**
   - Python 3.11
   - End-to-end test scenarios
   - Full application testing

#### Services
```yaml
services:
  postgres:
    image: postgres:13
    env:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: mommyshops_test
    ports:
      - 5432:5432

  redis:
    image: redis:6
    ports:
      - 6379:6379
```

#### Steps
1. **Setup**
   - Checkout code
   - Set up Python environment
   - Cache dependencies
   - Set environment variables

2. **Linting**
   - Flake8 (style and complexity)
   - Black (code formatting)
   - isort (import sorting)
   - mypy (type checking)

3. **Security**
   - Bandit (security linter)
   - Safety (dependency vulnerabilities)

4. **Testing**
   - pytest with coverage
   - Integration tests
   - E2E tests

### 2. Java Tests (`java-tests.yml`)

#### Triggers
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Changes to Java backend files

#### Jobs
1. **Test Matrix**
   - Java versions: 11, 17, 21
   - Services: PostgreSQL, Redis
   - Steps: Checkstyle, SpotBugs, Tests

2. **Integration Tests**
   - Java 17
   - Full service stack
   - Integration test suite

3. **E2E Tests**
   - Java 17
   - End-to-end test scenarios
   - Full application testing

#### Steps
1. **Setup**
   - Checkout code
   - Set up Java environment
   - Cache Maven dependencies
   - Set environment variables

2. **Code Quality**
   - Checkstyle (code style)
   - SpotBugs (bug detection)

3. **Testing**
   - Maven test execution
   - Integration tests
   - E2E tests

### 3. Security Scan (`security.yml`)

#### Triggers
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Weekly schedule (Monday 2 AM)

#### Jobs
1. **Python Security**
   - Bandit (security linter)
   - Safety (dependency check)
   - Semgrep (static analysis)

2. **Java Security**
   - SpotBugs (security analysis)
   - OWASP Dependency Check

3. **Docker Security**
   - Trivy vulnerability scanner
   - Container image analysis

4. **CodeQL Analysis**
   - Static code analysis
   - Security vulnerability detection

5. **Dependency Review**
   - License compliance
   - Vulnerability assessment

6. **Secret Scan**
   - TruffleHog secret detection
   - Credential scanning

### 4. Deploy (`deploy.yml`)

#### Triggers
- Push to `main` branch
- Manual workflow dispatch

#### Jobs
1. **Build and Push**
   - Build Docker images
   - Push to GitHub Container Registry
   - Multi-platform support

2. **Deploy Staging**
   - Deploy to staging environment
   - Health checks
   - Smoke tests

3. **Deploy Production**
   - Deploy to production environment
   - Health checks
   - Notifications

4. **Security Scan**
   - Trivy vulnerability scanner
   - Container security analysis

5. **Performance Test**
   - Load testing
   - Performance benchmarks

## Configuration

### Environment Variables

#### Python Backend
```yaml
DATABASE_URL: postgresql://postgres:postgres@localhost:5432/mommyshops_test
DB_USERNAME: postgres
DB_PASSWORD: postgres
REDIS_HOST: localhost
REDIS_PORT: 6379
JWT_SECRET: test-secret-key-for-github-actions
ENVIRONMENT: test
```

#### Java Backend
```yaml
SPRING_DATASOURCE_URL: jdbc:postgresql://localhost:5432/mommyshops_test
SPRING_DATASOURCE_USERNAME: postgres
SPRING_DATASOURCE_PASSWORD: postgres
SPRING_REDIS_HOST: localhost
SPRING_REDIS_PORT: 6379
JWT_SECRET: test-secret-key-for-github-actions
SPRING_PROFILES_ACTIVE: test
```

### Secrets

#### Required Secrets
- `GITHUB_TOKEN`: Automatically provided
- `DOCKER_USERNAME`: Docker registry username
- `DOCKER_PASSWORD`: Docker registry password
- `KUBECONFIG`: Kubernetes configuration
- `SLACK_WEBHOOK`: Slack notification webhook

#### Optional Secrets
- `CODECOV_TOKEN`: Code coverage token
- `SONAR_TOKEN`: SonarQube token
- `NOTIFICATION_EMAIL`: Email notifications

## Docker Configuration

### Python Backend Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Java Backend Dockerfile
```dockerfile
FROM openjdk:17-jdk-slim

WORKDIR /app

COPY target/*.jar app.jar

EXPOSE 8080

CMD ["java", "-jar", "app.jar"]
```

## Deployment Strategies

### Staging Deployment
1. **Automatic**
   - Triggered on push to `main`
   - Deploy to staging environment
   - Run health checks
   - Notify team

2. **Manual**
   - Workflow dispatch
   - Select staging environment
   - Deploy with approval

### Production Deployment
1. **Manual Only**
   - Workflow dispatch required
   - Production environment approval
   - Health checks and monitoring
   - Rollback capability

## Monitoring and Alerting

### Health Checks
```bash
# Application health
curl -f http://staging.mommyshops.com/health

# Database health
curl -f http://staging.mommyshops.com/api/database/health

# Redis health
curl -f http://staging.mommyshops.com/api/redis/health
```

### Metrics
- **Build Success Rate**: Track build success/failure rates
- **Test Coverage**: Monitor code coverage trends
- **Security Issues**: Track security vulnerabilities
- **Deployment Frequency**: Monitor deployment frequency
- **Lead Time**: Track time from commit to deployment

### Alerts
- **Build Failures**: Immediate notification
- **Security Issues**: High severity alerts
- **Deployment Failures**: Production deployment alerts
- **Performance Degradation**: Performance threshold alerts

## Best Practices

### 1. Branch Strategy
- **main**: Production-ready code
- **develop**: Integration branch
- **feature/***: Feature development
- **hotfix/***: Critical fixes

### 2. Commit Messages
```
feat: add new feature
fix: bug fix
docs: documentation update
style: code formatting
refactor: code refactoring
test: add tests
chore: maintenance tasks
```

### 3. Pull Request Process
1. Create feature branch
2. Implement changes
3. Add tests
4. Update documentation
5. Create pull request
6. Code review
7. Merge to develop
8. Deploy to staging
9. Merge to main
10. Deploy to production

### 4. Testing Strategy
- **Unit Tests**: Fast, isolated tests
- **Integration Tests**: Service integration
- **E2E Tests**: Full application testing
- **Performance Tests**: Load and stress testing
- **Security Tests**: Vulnerability scanning

### 5. Security Practices
- **Dependency Scanning**: Regular vulnerability checks
- **Secret Management**: Secure secret handling
- **Container Security**: Image vulnerability scanning
- **Code Analysis**: Static security analysis
- **License Compliance**: License compatibility checks

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check environment variables
   - Verify service dependencies
   - Review error logs
   - Check resource limits

2. **Test Failures**
   - Review test output
   - Check test data
   - Verify test environment
   - Update test expectations

3. **Deployment Issues**
   - Check deployment logs
   - Verify environment configuration
   - Check service health
   - Review resource usage

4. **Security Issues**
   - Review security scan results
   - Update dependencies
   - Fix vulnerabilities
   - Re-scan after fixes

### Debugging

1. **Enable Debug Logging**
   ```yaml
   - name: Enable debug logging
     run: |
       echo "ACTIONS_STEP_DEBUG=true" >> $GITHUB_ENV
   ```

2. **Check Service Status**
   ```bash
   # Check PostgreSQL
   pg_isready -h localhost -p 5432
   
   # Check Redis
   redis-cli ping
   ```

3. **Review Logs**
   ```bash
   # Check application logs
   docker logs <container_name>
   
   # Check service logs
   kubectl logs <pod_name>
   ```

## Conclusion

This CI/CD pipeline provides comprehensive automation for testing, security, and deployment. Regular monitoring and maintenance ensure optimal performance and reliability.
