# MommyShops Testing Guide

## 🧪 Overview

This guide covers the comprehensive testing strategy for the MommyShops project, including unit tests, integration tests, and end-to-end tests for both Python and Java backends.

## 📋 Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── services/           # Service layer tests
│   ├── api/                # API route tests
│   └── core/               # Core functionality tests
├── integration/            # Integration tests
│   ├── test_java_python_integration.py
│   └── test_database_operations.py
├── e2e/                    # End-to-end tests
│   ├── test_complete_analysis_flow.py
│   └── test_user_journey.py
└── conftest.py            # Test configuration and fixtures
```

## 🚀 Quick Start

### Prerequisites

1. **Python Environment**
   ```bash
   pip install -r requirements-test.txt
   ```

2. **Java Environment**
   ```bash
   cd backend-java
   mvn clean install
   ```

3. **Services Running**
   - Python backend: `http://localhost:8000`
   - Java backend: `http://localhost:8080`
   - Redis: `localhost:6379`
   - PostgreSQL: `localhost:5432`

### Running Tests

#### All Tests
```bash
python scripts/run_tests.py --type all
```

#### Unit Tests Only
```bash
python scripts/run_tests.py --type unit
```

#### Integration Tests Only
```bash
python scripts/run_tests.py --type integration
```

#### E2E Tests Only
```bash
python scripts/run_tests.py --type e2e
```

#### With Coverage
```bash
python scripts/run_tests.py --type all --coverage 85
```

#### With Security Scan
```bash
python scripts/run_tests.py --type all --security
```

#### With Performance Tests
```bash
python scripts/run_tests.py --type all --performance
```

## 🔧 Test Configuration

### Python Tests (pytest)

**Configuration**: `pytest.ini`
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --color=yes
    --durations=10
    --cov=backend-python
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --cov-fail-under=80

markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow tests
    external: Tests that require external services
    java: Tests that require Java backend
    python: Tests that require Python backend
    ollama: Tests that require Ollama service
    database: Tests that require database
    redis: Tests that require Redis
    api: API tests
    auth: Authentication tests
    analysis: Analysis tests
    ocr: OCR tests
    ml: Machine learning tests
```

### Java Tests (Maven)

**Configuration**: `pom.xml`
```xml
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-surefire-plugin</artifactId>
    <version>3.0.0</version>
    <configuration>
        <includes>
            <include>**/*Test.java</include>
        </includes>
        <excludes>
            <exclude>**/*IntegrationTest.java</exclude>
        </excludes>
    </configuration>
</plugin>

<plugin>
    <groupId>org.jacoco</groupId>
    <artifactId>jacoco-maven-plugin</artifactId>
    <version>0.8.8</version>
    <executions>
        <execution>
            <goals>
                <goal>prepare-agent</goal>
            </goals>
        </execution>
        <execution>
            <id>report</id>
            <phase>test</phase>
            <goals>
                <goal>report</goal>
            </goals>
        </execution>
    </executions>
</plugin>
```

## 📊 Test Types

### 1. Unit Tests

**Purpose**: Test individual components in isolation

**Python Unit Tests**:
```python
@pytest.mark.unit
@pytest.mark.ocr
def test_extract_text_success(self, ocr_service):
    """Test successful text extraction"""
    result = ocr_service.extract_text("test_image.jpg")
    assert result == "Aqua, Glycerin, Hyaluronic Acid"
```

**Java Unit Tests**:
```java
@Test
void testAnalyzeProductSuccess() {
    when(pythonBackendClient.analyzeText(anyString(), anyString()))
            .thenReturn(Mono.just(testResponse));
    
    Mono<ProductAnalysisResponse> result = productAnalysisService
            .analyzeProduct(testRequest, "test-user-123");
    
    StepVerifier.create(result)
            .assertNext(response -> {
                assertTrue(response.isSuccess());
                assertEquals("Test Product", response.getProductName());
            })
            .verifyComplete();
}
```

### 2. Integration Tests

**Purpose**: Test communication between services

**Java-Python Integration**:
```python
@pytest.mark.integration
def test_java_python_communication(self, java_base_url):
    """Test direct Java to Python communication"""
    response = requests.post(
        f"{java_base_url}/api/analysis/analyze-product",
        json={"text": "Aqua, Glycerin", "user_need": "sensitive skin"}
    )
    assert response.status_code == 200
    assert response.json()["success"] == True
```

### 3. End-to-End Tests

**Purpose**: Test complete user workflows

**Complete Analysis Flow**:
```python
@pytest.mark.e2e
@pytest.mark.slow
def test_complete_image_analysis_flow(self, java_base_url, test_image_data):
    """Test complete image analysis flow"""
    # Step 1: Upload image
    response = requests.post(
        f"{java_base_url}/api/analysis/analyze-image",
        files={"file": ("test.jpg", test_image_data, "image/jpeg")},
        data={"user_need": "sensitive skin"}
    )
    
    assert response.status_code == 200
    analysis_data = response.json()
    
    # Verify complete response structure
    assert "success" in analysis_data
    assert "ingredients_details" in analysis_data
    assert "avg_eco_score" in analysis_data
    assert "suitability" in analysis_data
    assert "recommendations" in analysis_data
```

## 🎯 Test Coverage

### Target Coverage: 80%+

**Python Coverage**:
```bash
pytest --cov=backend-python --cov-report=html --cov-fail-under=80
```

**Java Coverage**:
```bash
mvn test jacoco:report
```

### Coverage Reports

- **HTML Report**: `htmlcov/index.html`
- **JSON Report**: `coverage.json`
- **Terminal Report**: Console output with missing lines

## 🔒 Security Testing

### Bandit Security Scan
```bash
bandit -r backend-python/ -f json -o security-report.json
```

### Safety Dependency Scan
```bash
safety check --json --output safety-report.json
```

### Security Test Examples
```python
@pytest.mark.security
def test_sql_injection_prevention(self, client):
    """Test SQL injection prevention"""
    malicious_input = "'; DROP TABLE users; --"
    response = client.post("/api/analysis/analyze-product", json={
        "text": malicious_input,
        "user_need": "general"
    })
    # Should handle safely without database damage
    assert response.status_code == 200
```

## ⚡ Performance Testing

### Load Testing
```bash
locust -f tests/performance/locustfile.py --host=http://localhost:8080
```

### Benchmark Tests
```python
@pytest.mark.benchmark
def test_analysis_performance(self, client, benchmark):
    """Test analysis performance"""
    def run_analysis():
        response = client.post("/api/analysis/analyze-product", json={
            "text": "Aqua, Glycerin, Hyaluronic Acid",
            "user_need": "sensitive skin"
        })
        return response.status_code == 200
    
    result = benchmark(run_analysis)
    assert result == True
```

## 🧪 Test Fixtures

### Python Fixtures
```python
@pytest.fixture
def test_user(db_session):
    """Create test user"""
    user = User(
        id="test-user-123",
        email="test@example.com",
        name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def mock_ollama():
    """Mock Ollama service"""
    mock_ollama = AsyncMock()
    mock_ollama.analyze_ingredients.return_value = {
        "success": True,
        "content": "Test analysis result"
    }
    return mock_ollama
```

### Java Fixtures
```java
@BeforeEach
void setUp() {
    testRequest = new ProductAnalysisRequest();
    testRequest.setText("Aqua, Glycerin, Hyaluronic Acid");
    testRequest.setUserNeed("sensitive skin");
    
    testResponse = new ProductAnalysisResponse();
    testResponse.setSuccess(true);
    testResponse.setProductName("Test Product");
}
```

## 🚨 Error Handling Tests

### Python Error Handling
```python
def test_analyze_text_invalid_data(self, client):
    """Test text analysis with invalid data"""
    response = client.post("/analyze-text", json={})
    assert response.status_code == 422

def test_analyze_text_empty_text(self, client):
    """Test text analysis with empty text"""
    response = client.post("/analyze-text", json={
        "text": "", "user_need": "general"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == False
    assert "error" in data
```

### Java Error Handling
```java
@Test
void testAnalyzeProductWithEmptyText() {
    testRequest.setText("");
    when(pythonBackendClient.analyzeText(anyString(), anyString()))
            .thenReturn(Mono.just(testResponse));
    
    Mono<ProductAnalysisResponse> result = productAnalysisService
            .analyzeProduct(testRequest, "test-user-123");
    
    StepVerifier.create(result)
            .assertNext(response -> {
                assertFalse(response.isSuccess());
                assertNotNull(response.getError());
            })
            .verifyComplete();
}
```

## 📈 Test Metrics

### Key Metrics to Track

1. **Coverage Percentage**: Target 80%+
2. **Test Execution Time**: < 5 minutes for full suite
3. **Test Success Rate**: 100% for unit tests
4. **Integration Test Success**: 95%+ for integration tests
5. **E2E Test Success**: 90%+ for E2E tests

### Performance Benchmarks

1. **API Response Time**: < 2 seconds for analysis
2. **Image Processing Time**: < 10 seconds for OCR
3. **Database Query Time**: < 100ms for simple queries
4. **Memory Usage**: < 512MB for test execution

## 🔄 Continuous Integration

### GitHub Actions Workflow
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements-test.txt
      - name: Run tests
        run: python scripts/run_tests.py --type all --coverage 80
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 🐛 Debugging Tests

### Common Issues

1. **Import Errors**: Check Python path and module structure
2. **Database Connection**: Ensure test database is running
3. **Service Dependencies**: Mock external services for unit tests
4. **Timeout Issues**: Increase timeout for slow tests
5. **Memory Issues**: Use smaller test datasets

### Debug Commands

```bash
# Run specific test with verbose output
pytest tests/unit/services/test_ocr_service.py -v -s

# Run tests with debugging
pytest --pdb tests/unit/

# Run tests with coverage and debugging
pytest --cov=backend-python --cov-report=html --pdb

# Run Java tests with debugging
mvn test -Dtest=ProductAnalysisServiceTest -Dmaven.surefire.debug
```

## 📚 Best Practices

### Test Writing

1. **Arrange-Act-Assert**: Structure tests clearly
2. **Single Responsibility**: One test per scenario
3. **Descriptive Names**: Use clear, descriptive test names
4. **Independent Tests**: Tests should not depend on each other
5. **Fast Tests**: Unit tests should be fast (< 1 second)

### Test Data

1. **Use Fixtures**: Create reusable test data
2. **Mock External Services**: Don't depend on external APIs
3. **Clean Up**: Clean up test data after tests
4. **Realistic Data**: Use realistic test data when possible

### Test Organization

1. **Group Related Tests**: Use test classes and modules
2. **Use Markers**: Mark tests by type and requirements
3. **Separate Concerns**: Unit, integration, and E2E tests separately
4. **Documentation**: Document complex test scenarios

## 🎯 Test Goals

### Short Term (1-2 weeks)
- [ ] Achieve 80%+ code coverage
- [ ] All unit tests passing
- [ ] Integration tests working
- [ ] E2E tests for critical paths

### Medium Term (1-2 months)
- [ ] 90%+ code coverage
- [ ] Performance benchmarks
- [ ] Security testing automation
- [ ] Load testing implementation

### Long Term (3-6 months)
- [ ] 95%+ code coverage
- [ ] Automated test execution
- [ ] Test data management
- [ ] Advanced testing strategies

---

**Last Updated**: December 2024  
**Version**: 3.0.1  
**Maintainer**: CTO Team
