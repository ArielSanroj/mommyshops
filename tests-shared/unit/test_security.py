"""
Unit tests for security utilities
"""

import pytest
from fastapi import HTTPException, UploadFile
from backend.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    validate_password_strength,
    sanitize_filename,
    hash_data
)


class TestPasswordHashing:
    """Tests for password hashing"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert verify_password("WrongPassword!", hashed) is False


class TestJWTTokens:
    """Tests for JWT token operations"""
    
    def test_create_access_token(self):
        """Test JWT token creation"""
        data = {"sub": "test@example.com", "user_id": 1}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_access_token_valid(self):
        """Test decoding valid JWT token"""
        data = {"sub": "test@example.com", "user_id": 1}
        token = create_access_token(data)
        
        decoded = decode_access_token(token)
        
        assert decoded["sub"] == "test@example.com"
        assert decoded["user_id"] == 1
        assert "exp" in decoded
    
    def test_decode_access_token_invalid(self):
        """Test decoding invalid JWT token"""
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token("invalid.token.here")
        
        assert exc_info.value.status_code == 401


class TestPasswordValidation:
    """Tests for password strength validation"""
    
    def test_validate_strong_password(self):
        """Test validation of strong password"""
        strong_password = "StrongPass123!@#"
        assert validate_password_strength(strong_password) is True
    
    def test_validate_weak_password_too_short(self):
        """Test validation rejects short password"""
        with pytest.raises(HTTPException) as exc_info:
            validate_password_strength("Short1!")
        
        assert "at least 8 characters" in str(exc_info.value.detail)
    
    def test_validate_weak_password_no_uppercase(self):
        """Test validation rejects password without uppercase"""
        with pytest.raises(HTTPException) as exc_info:
            validate_password_strength("lowercase123!")
        
        assert "uppercase" in str(exc_info.value.detail)
    
    def test_validate_weak_password_no_lowercase(self):
        """Test validation rejects password without lowercase"""
        with pytest.raises(HTTPException) as exc_info:
            validate_password_strength("UPPERCASE123!")
        
        assert "lowercase" in str(exc_info.value.detail)
    
    def test_validate_weak_password_no_digit(self):
        """Test validation rejects password without digit"""
        with pytest.raises(HTTPException) as exc_info:
            validate_password_strength("NoDigits!")
        
        assert "number" in str(exc_info.value.detail)
    
    def test_validate_weak_password_no_special(self):
        """Test validation rejects password without special character"""
        with pytest.raises(HTTPException) as exc_info:
            validate_password_strength("NoSpecial123")
        
        assert "special character" in str(exc_info.value.detail)


class TestFilenameSanitization:
    """Tests for filename sanitization"""
    
    def test_sanitize_normal_filename(self):
        """Test sanitization of normal filename"""
        filename = "test_image.png"
        sanitized = sanitize_filename(filename)
        
        assert sanitized == "test_image.png"
    
    def test_sanitize_path_traversal(self):
        """Test sanitization removes path traversal"""
        filename = "../../etc/passwd"
        sanitized = sanitize_filename(filename)
        
        assert ".." not in sanitized
        assert "/" not in sanitized
        assert "\\" not in sanitized
    
    def test_sanitize_dangerous_chars(self):
        """Test sanitization removes dangerous characters"""
        filename = "test<file>:name?.png"
        sanitized = sanitize_filename(filename)
        
        assert "<" not in sanitized
        assert ">" not in sanitized
        assert ":" not in sanitized
        assert "?" not in sanitized


class TestDataHashing:
    """Tests for data hashing"""
    
    def test_hash_data(self):
        """Test SHA-256 hashing"""
        data = "test data"
        hashed = hash_data(data)
        
        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA-256 produces 64 hex characters
    
    def test_hash_data_consistent(self):
        """Test hashing produces consistent results"""
        data = "test data"
        hash1 = hash_data(data)
        hash2 = hash_data(data)
        
        assert hash1 == hash2
    
    def test_hash_data_different_inputs(self):
        """Test different inputs produce different hashes"""
        hash1 = hash_data("data1")
        hash2 = hash_data("data2")
        
        assert hash1 != hash2

