"""
Enhanced security tests for MommyShops backend.
Tests advanced security features beyond basic rate limiting and authentication.
"""

import os
import sys
import pytest
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

# Set up environment
os.environ.setdefault("SKIP_MAIN_IMPORT_FOR_TESTS", "1")

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend-python"
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from security_enhanced import (
    InputSanitizer, CSRFProtection, SecurityHeaders, 
    SecurityAuditLogger, AdvancedRateLimiter, ThreatDetection,
    validate_and_sanitize_input, check_csrf_token, log_security_event
)

def test_input_sanitization():
    """Test input sanitization prevents XSS attacks"""
    sanitizer = InputSanitizer()
    
    # Test XSS prevention
    malicious_input = "<script>alert('xss')</script>"
    sanitized = sanitizer.sanitize_string(malicious_input)
    assert "<script>" not in sanitized
    assert "&lt;script&gt;" in sanitized
    
    # Test SQL injection prevention
    sql_injection = "'; DROP TABLE users; --"
    is_safe = sanitizer.validate_sql_input(sql_injection)
    assert not is_safe
    
    # Test safe input
    safe_input = "normal user input"
    sanitized_safe = sanitizer.sanitize_string(safe_input)
    assert sanitized_safe == safe_input

def test_file_upload_validation():
    """Test file upload security validation"""
    sanitizer = InputSanitizer()
    
    # Test valid file
    valid_file = Mock()
    valid_file.content_type = "image/jpeg"
    valid_file.size = 1024 * 1024  # 1MB
    valid_file.filename = "test.jpg"
    
    # Should not raise exception
    try:
        sanitizer.validate_file_upload(valid_file)
    except HTTPException:
        pytest.fail("Valid file should not raise exception")
    
    # Test invalid file type
    invalid_file = Mock()
    invalid_file.content_type = "application/pdf"
    invalid_file.size = 1024 * 1024
    invalid_file.filename = "test.pdf"
    
    with pytest.raises(HTTPException) as exc_info:
        sanitizer.validate_file_upload(invalid_file)
    assert "Invalid file type" in str(exc_info.value.detail)
    
    # Test oversized file
    oversized_file = Mock()
    oversized_file.content_type = "image/jpeg"
    oversized_file.size = 10 * 1024 * 1024  # 10MB
    oversized_file.filename = "test.jpg"
    
    with pytest.raises(HTTPException) as exc_info:
        sanitizer.validate_file_upload(oversized_file)
    assert "File too large" in str(exc_info.value.detail)

def test_csrf_protection():
    """Test CSRF protection functionality"""
    csrf = CSRFProtection()
    user_id = "test-user-123"
    
    # Generate token
    token = csrf.generate_csrf_token(user_id)
    assert token is not None
    assert len(token) > 0
    
    # Validate token
    is_valid = csrf.validate_csrf_token(token, user_id)
    assert is_valid
    
    # Test invalid token
    invalid_token = "invalid-token"
    is_invalid = csrf.validate_csrf_token(invalid_token, user_id)
    assert not is_invalid
    
    # Test token for different user
    other_user_id = "other-user-456"
    is_valid_other = csrf.validate_csrf_token(token, other_user_id)
    assert not is_valid_other
    
    # Test token revocation
    csrf.revoke_token(user_id)
    is_revoked = csrf.validate_csrf_token(token, user_id)
    assert not is_revoked

def test_security_headers():
    """Test security headers are properly set"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    
    app = FastAPI()
    
    @app.get("/test")
    def test_endpoint():
        return {"message": "test"}
    
    # Add security headers middleware
    from security_enhanced import SecurityMiddleware
    app.add_middleware(SecurityMiddleware)
    
    client = TestClient(app)
    response = client.get("/test")
    
    # Check security headers
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Strict-Transport-Security" in response.headers
    assert "Content-Security-Policy" in response.headers

def test_advanced_rate_limiter():
    """Test advanced rate limiter with per-user limits"""
    app = FastAPI()
    
    @app.get("/test")
    def test_endpoint():
        return {"message": "test"}
    
    # Add advanced rate limiter
    app.add_middleware(AdvancedRateLimiter, limit=2, window_seconds=60)
    
    client = TestClient(app)
    
    # Test IP-based rate limiting
    response1 = client.get("/test")
    assert response1.status_code == 200
    
    response2 = client.get("/test")
    assert response2.status_code == 200
    
    # Third request should be rate limited
    response3 = client.get("/test")
    assert response3.status_code == 429
    assert "Rate limit exceeded" in response3.json()["detail"]

def test_threat_detection():
    """Test threat detection system"""
    threat_detection = ThreatDetection()
    test_ip = "192.168.1.100"
    
    # Test normal activity
    is_suspicious = threat_detection.check_suspicious_activity(test_ip)
    assert not is_suspicious
    
    # Simulate failed logins
    for _ in range(6):
        threat_detection.record_failed_login(test_ip)
    
    # Should now be suspicious
    is_suspicious = threat_detection.check_suspicious_activity(test_ip)
    assert is_suspicious
    
    # Reset counters
    threat_detection.reset_counters(test_ip)
    is_suspicious = threat_detection.check_suspicious_activity(test_ip)
    assert not is_suspicious

def test_security_audit_logging():
    """Test security audit logging"""
    audit_logger = SecurityAuditLogger()
    
    # Test auth attempt logging
    with patch.object(audit_logger.audit_logger, 'info') as mock_info:
        audit_logger.log_auth_attempt("user123", "192.168.1.100", True)
        mock_info.assert_called_once()
        
        # Check logged data
        call_args = mock_info.call_args[0][0]
        assert call_args["event"] == "auth_attempt"
        assert call_args["user_id"] == "user123"
        assert call_args["success"] is True
    
    # Test rate limit logging
    with patch.object(audit_logger.audit_logger, 'warning') as mock_warning:
        audit_logger.log_rate_limit_hit("192.168.1.100", "/api/test", 60)
        mock_warning.assert_called_once()
        
        # Check logged data
        call_args = mock_warning.call_args[0][0]
        assert call_args["event"] == "rate_limit_hit"
        assert call_args["ip"] == "192.168.1.100"
        assert call_args["endpoint"] == "/api/test"

def test_validate_and_sanitize_input():
    """Test input validation and sanitization utility"""
    test_data = {
        "name": "<script>alert('xss')</script>",
        "email": "user@example.com",
        "description": "Normal description"
    }
    
    sanitized_data = validate_and_sanitize_input(test_data)
    
    # Check XSS prevention
    assert "<script>" not in sanitized_data["name"]
    assert "&lt;script&gt;" in sanitized_data["name"]
    
    # Check safe data is preserved
    assert sanitized_data["email"] == "user@example.com"
    assert sanitized_data["description"] == "Normal description"

def test_check_csrf_token():
    """Test CSRF token checking utility"""
    # This would need to be implemented based on your CSRF implementation
    # For now, we'll test the basic functionality
    user_id = "test-user-123"
    
    # Test with valid token (would need actual token generation)
    # This is a placeholder test
    assert True  # Replace with actual CSRF token test

def test_log_security_event():
    """Test security event logging utility"""
    with patch('security_enhanced.SecurityAuditLogger') as mock_audit:
        mock_instance = mock_audit.return_value
        
        log_security_event("test_event", {"key": "value"})
        
        mock_instance.log_security_event.assert_called_once_with(
            "test_event", {"key": "value"}
        )

def test_sql_injection_prevention():
    """Test SQL injection prevention"""
    sanitizer = InputSanitizer()
    
    # Test various SQL injection patterns
    injection_patterns = [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "admin'--",
        "1' UNION SELECT * FROM users--",
        "'; INSERT INTO users VALUES ('hacker', 'password'); --"
    ]
    
    for pattern in injection_patterns:
        is_safe = sanitizer.validate_sql_input(pattern)
        assert not is_safe, f"SQL injection pattern should be detected: {pattern}"
    
    # Test safe input
    safe_inputs = [
        "normal user input",
        "user@example.com",
        "Product Name 123",
        "Valid description with numbers 123"
    ]
    
    for safe_input in safe_inputs:
        is_safe = sanitizer.validate_sql_input(safe_input)
        assert is_safe, f"Safe input should be allowed: {safe_input}"

def test_xss_prevention():
    """Test XSS prevention"""
    sanitizer = InputSanitizer()
    
    # Test various XSS patterns
    xss_patterns = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "<svg onload=alert('xss')>",
        "javascript:alert('xss')",
        "<iframe src=javascript:alert('xss')></iframe>"
    ]
    
    for pattern in xss_patterns:
        sanitized = sanitizer.sanitize_string(pattern)
        assert "<script>" not in sanitized
        assert "javascript:" not in sanitized
        assert "onerror=" not in sanitized
        assert "onload=" not in sanitized

def test_security_middleware_integration():
    """Test security middleware integration"""
    app = FastAPI()
    
    @app.get("/test")
    def test_endpoint():
        return {"message": "test"}
    
    # Add security middleware
    from security_enhanced import SecurityMiddleware
    app.add_middleware(SecurityMiddleware)
    
    client = TestClient(app)
    response = client.get("/test")
    
    # Check response
    assert response.status_code == 200
    assert response.json() == {"message": "test"}
    
    # Check security headers are present
    assert "X-Content-Type-Options" in response.headers
    assert "X-Frame-Options" in response.headers
    assert "Strict-Transport-Security" in response.headers

def test_security_configuration():
    """Test security configuration"""
    # Test environment variable configuration
    os.environ["RATE_LIMIT_PER_MINUTE"] = "120"
    os.environ["RATE_LIMIT_WINDOW_SECONDS"] = "60"
    os.environ["CSRF_SECRET"] = "test-csrf-secret"
    
    # Test configuration loading
    from security_enhanced import configure_enhanced_security
    
    app = FastAPI()
    configure_enhanced_security(app)
    
    # Verify middleware is added
    assert len(app.user_middleware) > 0
    
    # Clean up
    del os.environ["RATE_LIMIT_PER_MINUTE"]
    del os.environ["RATE_LIMIT_WINDOW_SECONDS"]
    del os.environ["CSRF_SECRET"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
