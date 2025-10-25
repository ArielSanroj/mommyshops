"""
Unit tests for configuration management
"""

import pytest
import os
from backend.core.config import get_settings, Settings


class TestSettings:
    """Tests for Settings configuration"""
    
    def test_get_settings_singleton(self):
        """Test settings returns singleton instance"""
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2
    
    def test_default_values(self):
        """Test default configuration values"""
        settings = get_settings()
        
        assert settings.OLLAMA_BASE_URL == "http://localhost:11434"
        assert settings.OLLAMA_MODEL == "llama3.1"
        assert settings.ANALYSIS_CONFIDENCE_THRESHOLD == 70
        assert settings.JWT_ALGORITHM == "HS256"
    
    def test_cors_settings(self):
        """Test CORS configuration"""
        settings = get_settings()
        
        assert hasattr(settings, 'CORS_ORIGINS')
        assert hasattr(settings, 'CORS_ALLOW_CREDENTIALS')
        assert hasattr(settings, 'CORS_ALLOW_METHODS')
    
    def test_security_settings(self):
        """Test security configuration"""
        settings = get_settings()
        
        assert hasattr(settings, 'JWT_SECRET')
        assert hasattr(settings, 'JWT_EXPIRATION')
        assert hasattr(settings, 'JWT_ALGORITHM')
    
    def test_file_upload_settings(self):
        """Test file upload configuration"""
        settings = get_settings()
        
        assert hasattr(settings, 'MAX_UPLOAD_SIZE')
        assert hasattr(settings, 'ALLOWED_IMAGE_EXTENSIONS')
        assert settings.MAX_UPLOAD_SIZE > 0

