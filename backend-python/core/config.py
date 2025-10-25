"""
Configuration management for MommyShops API
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import secrets

class Settings(BaseSettings):
    """
    Application settings
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Database
    DATABASE_URL: str = Field(default="", env="DATABASE_URL")
    DB_USERNAME: str = Field(default="", env="DB_USERNAME")
    DB_PASSWORD: str = Field(default="", env="DB_PASSWORD")
    
    # Redis
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Python Backend
    PYTHON_BACKEND_URL: str = Field(default="http://localhost:8000", env="PYTHON_BACKEND_URL")
    PYTHON_BACKEND_TIMEOUT: int = Field(default=30000, env="PYTHON_BACKEND_TIMEOUT")
    
    # External APIs
    FDA_API_KEY: Optional[str] = Field(default=None, env="FDA_API_KEY")
    EWG_API_KEY: Optional[str] = Field(default=None, env="EWG_API_KEY")
    GOOGLE_CLIENT_ID: Optional[str] = Field(default=None, env="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(default=None, env="GOOGLE_CLIENT_SECRET")
    
    # Ollama
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    OLLAMA_MODEL: str = Field(default="llama3.1", env="OLLAMA_MODEL")
    OLLAMA_VISION_MODEL: str = Field(default="llava", env="OLLAMA_VISION_MODEL")
    OLLAMA_TIMEOUT: int = Field(default=120, env="OLLAMA_TIMEOUT")
    
    # Analysis
    ANALYSIS_CONFIDENCE_THRESHOLD: int = Field(default=70, env="ANALYSIS_CONFIDENCE_THRESHOLD")
    ANALYSIS_MAX_INGREDIENTS: int = Field(default=50, env="ANALYSIS_MAX_INGREDIENTS")
    
    # Logging
    SHOW_SQL: bool = Field(default=False, env="SHOW_SQL")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Security
    JWT_SECRET: str = Field(default_factory=lambda: secrets.token_urlsafe(32), env="JWT_SECRET")
    JWT_EXPIRATION: int = Field(default=3600, env="JWT_EXPIRATION")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    
    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Ensure JWT secret is strong enough"""
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return v
    
    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL is provided"""
        if not v:
            raise ValueError("DATABASE_URL must be provided in environment variables")
        return v
    
    # CORS
    CORS_ORIGINS: str = Field(default="http://localhost:8080,http://localhost:3000", env="CORS_ORIGINS")
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    CORS_ALLOW_METHODS: str = Field(default="GET,POST,PUT,DELETE,OPTIONS", env="CORS_ALLOW_METHODS")
    
    # Trusted Hosts
    TRUSTED_HOSTS: str = Field(default="localhost,127.0.0.1", env="TRUSTED_HOSTS")
    
    # File Upload
    MAX_UPLOAD_SIZE: int = Field(default=5242880, env="MAX_UPLOAD_SIZE")  # 5MB
    ALLOWED_IMAGE_EXTENSIONS: str = Field(default=".jpg,.jpeg,.png,.webp", env="ALLOWED_IMAGE_EXTENSIONS")
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    HEALTH_CHECK_ENABLED: bool = Field(default=True, env="HEALTH_CHECK_ENABLED")
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_BURST: int = Field(default=10, env="RATE_LIMIT_BURST")

# Global settings instance
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """
    Get application settings
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

