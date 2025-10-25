"""
Pytest configuration and fixtures for MommyShops project
"""

import pytest
import asyncio
import tempfile
import os
import sys
from typing import Generator, AsyncGenerator, Dict, Any
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend-python to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend-python'))

SKIP_MAIN_IMPORT = os.getenv("SKIP_MAIN_IMPORT_FOR_TESTS") in {"1", "true", "yes"}

# Import after path setup
if not SKIP_MAIN_IMPORT:
    try:
        from main import app
        from core.database import get_db, Base
        from core.config import Settings
        from models.user import User
        from models.analysis import ProductAnalysis, IngredientAnalysis
    except ImportError as e:
        print(f"Warning: Could not import modules: {e}")
        app = None
else:
    app = None
    class _DummyMeta:
        @staticmethod
        def create_all(*args, **kwargs):
            return None

        @staticmethod
        def drop_all(*args, **kwargs):
            return None

    class _DummyBase:
        metadata = _DummyMeta()

    Base = _DummyBase

    def get_db():  # pragma: no cover - only used when skipping imports
        raise RuntimeError("Database not available in lightweight test mode")

    class Settings:  # pragma: no cover - used only in lightweight mode
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class User:  # pragma: no cover - minimal placeholder
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class ProductAnalysis:  # pragma: no cover - placeholder
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class IngredientAnalysis:  # pragma: no cover - placeholder
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return engine

@pytest.fixture(scope="session")
def test_db_session(test_engine):
    """Create test database session"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    
    session = TestingSessionLocal()
    yield session
    session.close()
    
    # Drop tables
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session(test_db_session):
    """Create database session for each test"""
    yield test_db_session
    test_db_session.rollback()

@pytest.fixture
def client(test_db_session):
    """Create test client"""
    if app is None:
        pytest.skip("App not available")
    
    def override_get_db():
        yield test_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session):
    """Create test user"""
    user = User(
        id="test-user-123",
        email="test@example.com",
        name="Test User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def test_analysis(db_session, test_user):
    """Create test analysis"""
    analysis = ProductAnalysis(
        id="test-analysis-123",
        user_id=test_user.id,
        product_name="Test Product",
        ingredients=["Aqua", "Glycerin", "Hyaluronic Acid"],
        analysis_result={"suitability": "good", "eco_score": 75.0}
    )
    db_session.add(analysis)
    db_session.commit()
    return analysis

@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    return Settings(
        DATABASE_URL=TEST_DATABASE_URL,
        JWT_SECRET="test-secret-key",
        JWT_EXPIRATION=3600,
        REDIS_HOST="localhost",
        REDIS_PORT=6379,
        OLLAMA_URL="http://localhost:11434",
        JAVA_BACKEND_URL="http://localhost:8080"
    )

@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock_redis = Mock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = True
    mock_redis.exists.return_value = False
    return mock_redis

@pytest.fixture
def mock_ollama():
    """Mock Ollama service"""
    mock_ollama = AsyncMock()
    mock_ollama.analyze_ingredients.return_value = {
        "success": True,
        "content": "Test analysis result",
        "alternatives": ["Alternative 1", "Alternative 2"]
    }
    mock_ollama.suggest_alternatives.return_value = {
        "success": True,
        "alternatives": ["Alternative 1", "Alternative 2"]
    }
    return mock_ollama

@pytest.fixture
def mock_external_api():
    """Mock external API service"""
    mock_api = AsyncMock()
    mock_api.fetch_ingredient_data.return_value = {
        "name": "Hyaluronic Acid",
        "risk_level": "low",
        "eco_score": 85.0,
        "benefits": "Hydrating",
        "risks": "None known",
        "sources": "EWG, FDA"
    }
    return mock_api

@pytest.fixture
def mock_ocr_service():
    """Mock OCR service"""
    mock_ocr = AsyncMock()
    mock_ocr.extract_text.return_value = "Aqua, Glycerin, Hyaluronic Acid, Niacinamide"
    mock_ocr.analyze_image.return_value = {
        "text": "Aqua, Glycerin, Hyaluronic Acid, Niacinamide",
        "confidence": 0.95,
        "ingredients": ["Aqua", "Glycerin", "Hyaluronic Acid", "Niacinamide"]
    }
    return mock_ocr

@pytest.fixture
def test_image_file():
    """Create test image file"""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        # Write fake image data
        f.write(b"fake-image-data")
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    os.unlink(temp_file)

@pytest.fixture
def test_ingredients():
    """Test ingredients data"""
    return [
        "Aqua",
        "Glycerin", 
        "Hyaluronic Acid",
        "Niacinamide",
        "Retinol",
        "Vitamin C"
    ]

@pytest.fixture
def test_analysis_request():
    """Test analysis request data"""
    return {
        "text": "Aqua, Glycerin, Hyaluronic Acid, Niacinamide",
        "user_need": "sensitive skin"
    }

@pytest.fixture
def test_analysis_response():
    """Test analysis response data"""
    return {
        "success": True,
        "product_name": "Test Product",
        "ingredients_details": [
            {
                "name": "Hyaluronic Acid",
                "risk_level": "low",
                "eco_score": 85.0,
                "benefits": "Hydrating",
                "risks_detailed": "None known",
                "sources": "EWG, FDA"
            }
        ],
        "avg_eco_score": 85.0,
        "suitability": "good",
        "recommendations": "Product is suitable for sensitive skin"
    }

@pytest.fixture
def mock_java_backend():
    """Mock Java backend client"""
    mock_java = Mock()
    mock_java.analyze_product.return_value = {
        "success": True,
        "analysis_id": "java-123",
        "processing_time_ms": 1500
    }
    return mock_java

@pytest.fixture
def test_environment():
    """Set up test environment variables"""
    test_env = {
        "TESTING": "true",
        "DATABASE_URL": TEST_DATABASE_URL,
        "JWT_SECRET": "test-secret-key",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "OLLAMA_URL": "http://localhost:11434",
        "JAVA_BACKEND_URL": "http://localhost:8080",
        "PYTHON_BACKEND_URL": "http://localhost:8000"
    }
    
    # Set environment variables
    for key, value in test_env.items():
        os.environ[key] = value
    
    yield test_env
    
    # Cleanup
    for key in test_env.keys():
        os.environ.pop(key, None)

# Pytest markers
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "external: Tests that require external services")
    config.addinivalue_line("markers", "java: Tests that require Java backend")
    config.addinivalue_line("markers", "python: Tests that require Python backend")
    config.addinivalue_line("markers", "ollama: Tests that require Ollama service")
    config.addinivalue_line("markers", "database: Tests that require database")
    config.addinivalue_line("markers", "redis: Tests that require Redis")
    config.addinivalue_line("markers", "api: API tests")
    config.addinivalue_line("markers", "auth: Authentication tests")
    config.addinivalue_line("markers", "analysis: Analysis tests")
    config.addinivalue_line("markers", "ocr: OCR tests")
    config.addinivalue_line("markers", "ml: Machine learning tests")

def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    # Add markers based on test file location
    for item in items:
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # Add markers based on test name
        if "test_java" in item.name:
            item.add_marker(pytest.mark.java)
        if "test_ollama" in item.name:
            item.add_marker(pytest.mark.ollama)
        if "test_ocr" in item.name:
            item.add_marker(pytest.mark.ocr)
        if "test_analysis" in item.name:
            item.add_marker(pytest.mark.analysis)
