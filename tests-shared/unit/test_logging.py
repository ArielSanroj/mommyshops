"""
Unit tests for logging configuration and secret sanitization
"""

import pytest
import logging
from backend.core.logging_config import SecretSanitizer, JSONFormatter, get_logger


class TestSecretSanitizer:
    """Tests for secret sanitization in logs"""
    
    def setup_method(self):
        """Setup test"""
        self.sanitizer = SecretSanitizer()
    
    def test_sanitize_password(self):
        """Test password sanitization"""
        text = 'password="MySecretPass123"'
        sanitized = self.sanitizer.sanitize(text)
        
        assert "MySecretPass123" not in sanitized
        assert "REDACTED" in sanitized
    
    def test_sanitize_token(self):
        """Test token sanitization"""
        text = "token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        sanitized = self.sanitizer.sanitize(text)
        
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in sanitized
        assert "REDACTED" in sanitized
    
    def test_sanitize_api_key(self):
        """Test API key sanitization"""
        text = "api_key=sk-1234567890abcdef"
        sanitized = self.sanitizer.sanitize(text)
        
        assert "sk-1234567890abcdef" not in sanitized
        assert "REDACTED" in sanitized
    
    def test_sanitize_database_url(self):
        """Test database URL password sanitization"""
        text = "postgresql://user:secret_pass@localhost:5432/db"
        sanitized = self.sanitizer.sanitize(text)
        
        assert "secret_pass" not in sanitized
        assert "REDACTED" in sanitized
    
    def test_sanitize_dict(self):
        """Test dictionary sanitization"""
        data = {
            "username": "test_user",
            "password": "secret123",
            "api_key": "key123",
            "email": "test@example.com"
        }
        
        sanitized = self.sanitizer.sanitize_dict(data)
        
        assert sanitized["username"] == "test_user"
        assert sanitized["email"] == "test@example.com"
        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["api_key"] == "***REDACTED***"
    
    def test_sanitize_nested_dict(self):
        """Test nested dictionary sanitization"""
        data = {
            "user": {
                "name": "test",
                "password": "secret"
            }
        }
        
        sanitized = self.sanitizer.sanitize_dict(data)
        
        assert sanitized["user"]["name"] == "test"
        assert sanitized["user"]["password"] == "***REDACTED***"
    
    def test_filter_log_record(self):
        """Test log record filtering"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="User logged in with password=secret123",
            args=(),
            exc_info=None
        )
        
        result = self.sanitizer.filter(record)
        
        assert result is True
        assert "secret123" not in record.msg
        assert "REDACTED" in record.msg


class TestJSONFormatter:
    """Tests for JSON log formatter"""
    
    def setup_method(self):
        """Setup test"""
        self.formatter = JSONFormatter()
    
    def test_format_basic_record(self):
        """Test basic log record formatting"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = self.formatter.format(record)
        
        assert '"level":"INFO"' in formatted
        assert '"message":"Test message"' in formatted
        assert '"logger":"test"' in formatted
        assert '"line":42' in formatted
    
    def test_format_with_exception(self):
        """Test log record with exception formatting"""
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Error occurred",
                args=(),
                exc_info=sys.exc_info()
            )
            
            formatted = self.formatter.format(record)
            
            assert '"level":"ERROR"' in formatted
            assert '"exception"' in formatted
            assert "ValueError" in formatted


class TestGetLogger:
    """Tests for get_logger function"""
    
    def test_get_logger(self):
        """Test getting a logger"""
        logger = get_logger("test_logger")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
    
    def test_logger_has_sanitizer(self):
        """Test logger has sanitizer filter"""
        logger = get_logger("test_logger")
        
        has_sanitizer = any(
            isinstance(f, SecretSanitizer) 
            for f in logger.filters
        )
        
        assert has_sanitizer

