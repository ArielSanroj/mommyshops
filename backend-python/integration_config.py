"""
Integration Configuration for Python-Java Communication
This file contains specific settings for Python-Java integration
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

class IntegrationSettings(BaseSettings):
    """
    Integration settings for Python-Java communication
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Java Backend Configuration
    JAVA_BACKEND_URL: str = Field(default="http://localhost:8080", env="JAVA_BACKEND_URL")
    JAVA_INTEGRATION_ENABLED: bool = Field(default=True, env="JAVA_INTEGRATION_ENABLED")
    JAVA_REQUEST_TIMEOUT: int = Field(default=30, env="JAVA_REQUEST_TIMEOUT")
    JAVA_HEALTH_CHECK_INTERVAL: int = Field(default=30, env="JAVA_HEALTH_CHECK_INTERVAL")
    
    # Circuit Breaker Configuration
    CIRCUIT_BREAKER_ENABLED: bool = Field(default=True, env="CIRCUIT_BREAKER_ENABLED")
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = Field(default=5, env="CIRCUIT_BREAKER_FAILURE_THRESHOLD")
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = Field(default=30, env="CIRCUIT_BREAKER_RECOVERY_TIMEOUT")
    
    # Retry Configuration
    RETRY_ENABLED: bool = Field(default=True, env="RETRY_ENABLED")
    RETRY_MAX_ATTEMPTS: int = Field(default=3, env="RETRY_MAX_ATTEMPTS")
    RETRY_DELAY: float = Field(default=1.0, env="RETRY_DELAY")
    RETRY_BACKOFF_MULTIPLIER: float = Field(default=2.0, env="RETRY_BACKOFF_MULTIPLIER")
    RETRY_MAX_DELAY: float = Field(default=10.0, env="RETRY_MAX_DELAY")
    
    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_BURST: int = Field(default=10, env="RATE_LIMIT_BURST")
    
    # Health Check Configuration
    HEALTH_CHECK_ENABLED: bool = Field(default=True, env="HEALTH_CHECK_ENABLED")
    HEALTH_CHECK_INTERVAL: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    HEALTH_CHECK_TIMEOUT: int = Field(default=5, env="HEALTH_CHECK_TIMEOUT")
    
    # Monitoring Configuration
    MONITORING_ENABLED: bool = Field(default=True, env="MONITORING_ENABLED")
    METRICS_ENABLED: bool = Field(default=True, env="METRICS_ENABLED")
    LOGGING_LEVEL: str = Field(default="INFO", env="LOGGING_LEVEL")
    
    # External API Configuration
    EXTERNAL_API_TIMEOUT: int = Field(default=10, env="EXTERNAL_API_TIMEOUT")
    EXTERNAL_API_RETRY_ATTEMPTS: int = Field(default=3, env="EXTERNAL_API_RETRY_ATTEMPTS")
    EXTERNAL_API_CACHE_TTL: int = Field(default=3600, env="EXTERNAL_API_CACHE_TTL")
    
    # Ollama Configuration
    OLLAMA_ENABLED: bool = Field(default=True, env="OLLAMA_ENABLED")
    OLLAMA_URL: str = Field(default="http://localhost:11434", env="OLLAMA_URL")
    OLLAMA_TIMEOUT: int = Field(default=60, env="OLLAMA_TIMEOUT")
    OLLAMA_MODEL: str = Field(default="llama3.2", env="OLLAMA_MODEL")
    
    # Database Configuration
    DATABASE_URL: str = Field(default="", env="DATABASE_URL")
    DB_USERNAME: str = Field(default="", env="DB_USERNAME")
    DB_PASSWORD: str = Field(default="", env="DB_PASSWORD")
    
    # Redis Configuration
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    
    # Security Configuration
    JWT_SECRET: str = Field(default="", env="JWT_SECRET")
    JWT_EXPIRATION: int = Field(default=3600, env="JWT_EXPIRATION")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    
    # CORS Configuration
    CORS_ALLOWED_ORIGINS: str = Field(default="http://localhost:3000,http://localhost:8080", env="CORS_ALLOWED_ORIGINS")
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    CORS_ALLOW_METHODS: str = Field(default="GET,POST,PUT,DELETE,OPTIONS", env="CORS_ALLOW_METHODS")
    
    # File Upload Configuration
    MAX_UPLOAD_SIZE: int = Field(default=5242880, env="MAX_UPLOAD_SIZE")  # 5MB
    ALLOWED_IMAGE_EXTENSIONS: str = Field(default=".jpg,.jpeg,.png,.webp", env="ALLOWED_IMAGE_EXTENSIONS")
    
    # Performance Configuration
    ASYNC_PROCESSING_ENABLED: bool = Field(default=True, env="ASYNC_PROCESSING_ENABLED")
    CELERY_ENABLED: bool = Field(default=True, env="CELERY_ENABLED")
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/1", env="CELERY_RESULT_BACKEND")
    
    # Logging Configuration
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # Integration Test Configuration
    INTEGRATION_TEST_MODE: bool = Field(default=False, env="INTEGRATION_TEST_MODE")
    MOCK_EXTERNAL_APIS: bool = Field(default=False, env="MOCK_EXTERNAL_APIS")
    MOCK_OLLAMA_SERVICE: bool = Field(default=False, env="MOCK_OLLAMA_SERVICE")
    
    @field_validator("JAVA_BACKEND_URL")
    @classmethod
    def validate_java_backend_url(cls, v: str) -> str:
        """Validate Java backend URL"""
        if not v.startswith(("http://", "https://")):
            raise ValueError("JAVA_BACKEND_URL must start with http:// or https://")
        return v
    
    @field_validator("LOGGING_LEVEL")
    @classmethod
    def validate_logging_level(cls, v: str) -> str:
        """Validate logging level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOGGING_LEVEL must be one of {valid_levels}")
        return v.upper()
    
    @field_validator("CORS_ALLOWED_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v: str) -> str:
        """Validate CORS origins"""
        if "*" in v and len(v.split(",")) > 1:
            raise ValueError("Cannot use wildcard with specific origins")
        return v

# Global settings instance
integration_settings = IntegrationSettings()

# Configuration for different environments
def get_integration_config(environment: str = "development") -> IntegrationSettings:
    """
    Get integration configuration for specific environment
    
    Args:
        environment: Environment name (development, testing, production)
        
    Returns:
        IntegrationSettings: Configuration for the environment
    """
    if environment == "testing":
        # Override settings for testing
        test_settings = IntegrationSettings(
            JAVA_BACKEND_URL="http://localhost:8080",
            JAVA_INTEGRATION_ENABLED=True,
            JAVA_REQUEST_TIMEOUT=10,
            CIRCUIT_BREAKER_ENABLED=False,
            RETRY_ENABLED=False,
            RATE_LIMIT_ENABLED=False,
            HEALTH_CHECK_ENABLED=True,
            MONITORING_ENABLED=False,
            METRICS_ENABLED=False,
            LOGGING_LEVEL="DEBUG",
            INTEGRATION_TEST_MODE=True,
            MOCK_EXTERNAL_APIS=True,
            MOCK_OLLAMA_SERVICE=True
        )
        return test_settings
    elif environment == "production":
        # Override settings for production
        prod_settings = IntegrationSettings(
            JAVA_BACKEND_URL=os.getenv("JAVA_BACKEND_URL", "http://localhost:8080"),
            JAVA_INTEGRATION_ENABLED=True,
            JAVA_REQUEST_TIMEOUT=30,
            CIRCUIT_BREAKER_ENABLED=True,
            RETRY_ENABLED=True,
            RATE_LIMIT_ENABLED=True,
            HEALTH_CHECK_ENABLED=True,
            MONITORING_ENABLED=True,
            METRICS_ENABLED=True,
            LOGGING_LEVEL="INFO",
            INTEGRATION_TEST_MODE=False,
            MOCK_EXTERNAL_APIS=False,
            MOCK_OLLAMA_SERVICE=False
        )
        return prod_settings
    else:
        # Default development settings
        return integration_settings

# Export settings
__all__ = ["IntegrationSettings", "integration_settings", "get_integration_config"]
