"""
Security configuration for MommyShops backend.
Centralized security settings and environment variable management.
"""

import os
import secrets
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class SecurityLevel(Enum):
    """Security level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityConfig:
    """Security configuration settings"""
    
    # Authentication & Authorization
    jwt_secret: str
    jwt_expiration: int
    jwt_algorithm: str
    password_min_length: int
    password_require_special: bool
    password_require_numbers: bool
    password_require_uppercase: bool
    
    # Rate Limiting
    rate_limit_enabled: bool
    rate_limit_per_minute: int
    rate_limit_window_seconds: int
    rate_limit_per_user: int
    rate_limit_per_ip: int
    
    # CORS Configuration
    cors_enabled: bool
    cors_allowed_origins: List[str]
    cors_allowed_methods: List[str]
    cors_allowed_headers: List[str]
    cors_allow_credentials: bool
    
    # Security Headers
    security_headers_enabled: bool
    hsts_enabled: bool
    hsts_max_age: int
    csp_enabled: bool
    csp_policy: str
    
    # Input Validation
    input_sanitization_enabled: bool
    sql_injection_protection: bool
    xss_protection: bool
    file_upload_validation: bool
    max_file_size: int
    allowed_file_types: List[str]
    
    # Database Security
    db_encryption_enabled: bool
    db_audit_logging: bool
    db_connection_ssl: bool
    db_query_validation: bool
    
    # Monitoring & Logging
    security_audit_logging: bool
    threat_detection_enabled: bool
    suspicious_activity_threshold: int
    failed_login_threshold: int
    
    # CSRF Protection
    csrf_protection_enabled: bool
    csrf_secret: str
    csrf_token_expiration: int
    
    # Session Security
    session_secure: bool
    session_httponly: bool
    session_samesite: str
    session_timeout: int
    
    # API Security
    api_key_required: bool
    api_key_header: str
    api_rate_limit: int
    
    # External API Security
    external_api_timeout: int
    external_api_retry_count: int
    external_api_circuit_breaker: bool
    external_api_rate_limit: int

def load_security_config() -> SecurityConfig:
    """Load security configuration from environment variables"""
    
    # Generate secure secrets if not provided
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret or jwt_secret == "your-secret-key":
        jwt_secret = secrets.token_urlsafe(32)
        print(f"WARNING: JWT_SECRET not set, using generated secret: {jwt_secret}")
    
    csrf_secret = os.getenv("CSRF_SECRET")
    if not csrf_secret:
        csrf_secret = secrets.token_urlsafe(32)
        print(f"WARNING: CSRF_SECRET not set, using generated secret: {csrf_secret}")
    
    # Parse CORS origins
    cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080")
    cors_allowed_origins = [origin.strip() for origin in cors_origins.split(",")]
    
    # Parse CORS methods
    cors_methods = os.getenv("CORS_ALLOWED_METHODS", "GET,POST,PUT,DELETE,OPTIONS")
    cors_allowed_methods = [method.strip() for method in cors_methods.split(",")]
    
    # Parse CORS headers
    cors_headers = os.getenv("CORS_ALLOWED_HEADERS", "Content-Type,Authorization,X-Requested-With")
    cors_allowed_headers = [header.strip() for header in cors_headers.split(",")]
    
    # Parse allowed file types
    file_types = os.getenv("ALLOWED_FILE_TYPES", "image/jpeg,image/png,image/webp,image/gif")
    allowed_file_types = [file_type.strip() for file_type in file_types.split(",")]
    
    return SecurityConfig(
        # Authentication & Authorization
        jwt_secret=jwt_secret,
        jwt_expiration=int(os.getenv("JWT_EXPIRATION", "3600")),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        password_min_length=int(os.getenv("PASSWORD_MIN_LENGTH", "8")),
        password_require_special=os.getenv("PASSWORD_REQUIRE_SPECIAL", "true").lower() == "true",
        password_require_numbers=os.getenv("PASSWORD_REQUIRE_NUMBERS", "true").lower() == "true",
        password_require_uppercase=os.getenv("PASSWORD_REQUIRE_UPPERCASE", "true").lower() == "true",
        
        # Rate Limiting
        rate_limit_enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
        rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "90")),
        rate_limit_window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
        rate_limit_per_user=int(os.getenv("RATE_LIMIT_PER_USER", "180")),
        rate_limit_per_ip=int(os.getenv("RATE_LIMIT_PER_IP", "60")),
        
        # CORS Configuration
        cors_enabled=os.getenv("CORS_ENABLED", "true").lower() == "true",
        cors_allowed_origins=cors_allowed_origins,
        cors_allowed_methods=cors_allowed_methods,
        cors_allowed_headers=cors_allowed_headers,
        cors_allow_credentials=os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true",
        
        # Security Headers
        security_headers_enabled=os.getenv("SECURITY_HEADERS_ENABLED", "true").lower() == "true",
        hsts_enabled=os.getenv("HSTS_ENABLED", "true").lower() == "true",
        hsts_max_age=int(os.getenv("HSTS_MAX_AGE", "31536000")),
        csp_enabled=os.getenv("CSP_ENABLED", "true").lower() == "true",
        csp_policy=os.getenv("CSP_POLICY", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"),
        
        # Input Validation
        input_sanitization_enabled=os.getenv("INPUT_SANITIZATION_ENABLED", "true").lower() == "true",
        sql_injection_protection=os.getenv("SQL_INJECTION_PROTECTION", "true").lower() == "true",
        xss_protection=os.getenv("XSS_PROTECTION", "true").lower() == "true",
        file_upload_validation=os.getenv("FILE_UPLOAD_VALIDATION", "true").lower() == "true",
        max_file_size=int(os.getenv("MAX_FILE_SIZE", "5242880")),  # 5MB
        allowed_file_types=allowed_file_types,
        
        # Database Security
        db_encryption_enabled=os.getenv("DB_ENCRYPTION_ENABLED", "true").lower() == "true",
        db_audit_logging=os.getenv("DB_AUDIT_LOGGING", "true").lower() == "true",
        db_connection_ssl=os.getenv("DB_CONNECTION_SSL", "true").lower() == "true",
        db_query_validation=os.getenv("DB_QUERY_VALIDATION", "true").lower() == "true",
        
        # Monitoring & Logging
        security_audit_logging=os.getenv("SECURITY_AUDIT_LOGGING", "true").lower() == "true",
        threat_detection_enabled=os.getenv("THREAT_DETECTION_ENABLED", "true").lower() == "true",
        suspicious_activity_threshold=int(os.getenv("SUSPICIOUS_ACTIVITY_THRESHOLD", "10")),
        failed_login_threshold=int(os.getenv("FAILED_LOGIN_THRESHOLD", "5")),
        
        # CSRF Protection
        csrf_protection_enabled=os.getenv("CSRF_PROTECTION_ENABLED", "true").lower() == "true",
        csrf_secret=csrf_secret,
        csrf_token_expiration=int(os.getenv("CSRF_TOKEN_EXPIRATION", "3600")),
        
        # Session Security
        session_secure=os.getenv("SESSION_SECURE", "true").lower() == "true",
        session_httponly=os.getenv("SESSION_HTTPONLY", "true").lower() == "true",
        session_samesite=os.getenv("SESSION_SAMESITE", "strict"),
        session_timeout=int(os.getenv("SESSION_TIMEOUT", "3600")),
        
        # API Security
        api_key_required=os.getenv("API_KEY_REQUIRED", "false").lower() == "true",
        api_key_header=os.getenv("API_KEY_HEADER", "X-API-Key"),
        api_rate_limit=int(os.getenv("API_RATE_LIMIT", "1000")),
        
        # External API Security
        external_api_timeout=int(os.getenv("EXTERNAL_API_TIMEOUT", "30")),
        external_api_retry_count=int(os.getenv("EXTERNAL_API_RETRY_COUNT", "3")),
        external_api_circuit_breaker=os.getenv("EXTERNAL_API_CIRCUIT_BREAKER", "true").lower() == "true",
        external_api_rate_limit=int(os.getenv("EXTERNAL_API_RATE_LIMIT", "100")),
    )

def validate_security_config(config: SecurityConfig) -> List[str]:
    """Validate security configuration and return warnings"""
    warnings = []
    
    # Check JWT secret strength
    if len(config.jwt_secret) < 32:
        warnings.append("JWT_SECRET should be at least 32 characters long")
    
    # Check password requirements
    if config.password_min_length < 8:
        warnings.append("PASSWORD_MIN_LENGTH should be at least 8")
    
    # Check CORS configuration
    if "*" in config.cors_allowed_origins:
        warnings.append("CORS_ALLOWED_ORIGINS contains wildcard (*) - consider specific origins")
    
    # Check rate limiting
    if config.rate_limit_per_minute > 1000:
        warnings.append("RATE_LIMIT_PER_MINUTE is very high - consider lowering")
    
    # Check file upload limits
    if config.max_file_size > 50 * 1024 * 1024:  # 50MB
        warnings.append("MAX_FILE_SIZE is very large - consider lowering")
    
    # Check security headers
    if not config.security_headers_enabled:
        warnings.append("SECURITY_HEADERS_ENABLED is disabled - security headers are important")
    
    # Check database security
    if not config.db_connection_ssl:
        warnings.append("DB_CONNECTION_SSL is disabled - database connections should use SSL")
    
    # Check threat detection
    if not config.threat_detection_enabled:
        warnings.append("THREAT_DETECTION_ENABLED is disabled - threat detection is important")
    
    return warnings

def get_security_level(config: SecurityConfig) -> SecurityLevel:
    """Determine security level based on configuration"""
    security_score = 0
    
    # Authentication security
    if len(config.jwt_secret) >= 32:
        security_score += 1
    if config.password_min_length >= 8:
        security_score += 1
    if config.password_require_special:
        security_score += 1
    
    # Rate limiting
    if config.rate_limit_enabled:
        security_score += 1
    if config.rate_limit_per_minute <= 100:
        security_score += 1
    
    # CORS security
    if "*" not in config.cors_allowed_origins:
        security_score += 1
    
    # Security headers
    if config.security_headers_enabled:
        security_score += 1
    if config.hsts_enabled:
        security_score += 1
    if config.csp_enabled:
        security_score += 1
    
    # Input validation
    if config.input_sanitization_enabled:
        security_score += 1
    if config.sql_injection_protection:
        security_score += 1
    if config.xss_protection:
        security_score += 1
    
    # Database security
    if config.db_encryption_enabled:
        security_score += 1
    if config.db_audit_logging:
        security_score += 1
    if config.db_connection_ssl:
        security_score += 1
    
    # Monitoring
    if config.security_audit_logging:
        security_score += 1
    if config.threat_detection_enabled:
        security_score += 1
    
    # CSRF protection
    if config.csrf_protection_enabled:
        security_score += 1
    
    # Determine security level
    if security_score >= 15:
        return SecurityLevel.CRITICAL
    elif security_score >= 12:
        return SecurityLevel.HIGH
    elif security_score >= 8:
        return SecurityLevel.MEDIUM
    else:
        return SecurityLevel.LOW

def generate_security_report(config: SecurityConfig) -> Dict[str, Any]:
    """Generate comprehensive security report"""
    warnings = validate_security_config(config)
    security_level = get_security_level(config)
    
    return {
        "security_level": security_level.value,
        "warnings": warnings,
        "configuration": {
            "authentication": {
                "jwt_secret_length": len(config.jwt_secret),
                "jwt_expiration": config.jwt_expiration,
                "password_requirements": {
                    "min_length": config.password_min_length,
                    "require_special": config.password_require_special,
                    "require_numbers": config.password_require_numbers,
                    "require_uppercase": config.password_require_uppercase
                }
            },
            "rate_limiting": {
                "enabled": config.rate_limit_enabled,
                "per_minute": config.rate_limit_per_minute,
                "per_user": config.rate_limit_per_user,
                "per_ip": config.rate_limit_per_ip
            },
            "cors": {
                "enabled": config.cors_enabled,
                "origins_count": len(config.cors_allowed_origins),
                "has_wildcard": "*" in config.cors_allowed_origins,
                "allow_credentials": config.cors_allow_credentials
            },
            "security_headers": {
                "enabled": config.security_headers_enabled,
                "hsts_enabled": config.hsts_enabled,
                "csp_enabled": config.csp_enabled
            },
            "input_validation": {
                "sanitization_enabled": config.input_sanitization_enabled,
                "sql_injection_protection": config.sql_injection_protection,
                "xss_protection": config.xss_protection,
                "file_upload_validation": config.file_upload_validation,
                "max_file_size": config.max_file_size,
                "allowed_file_types": config.allowed_file_types
            },
            "database_security": {
                "encryption_enabled": config.db_encryption_enabled,
                "audit_logging": config.db_audit_logging,
                "ssl_enabled": config.db_connection_ssl,
                "query_validation": config.db_query_validation
            },
            "monitoring": {
                "audit_logging": config.security_audit_logging,
                "threat_detection": config.threat_detection_enabled,
                "suspicious_activity_threshold": config.suspicious_activity_threshold,
                "failed_login_threshold": config.failed_login_threshold
            },
            "csrf_protection": {
                "enabled": config.csrf_protection_enabled,
                "token_expiration": config.csrf_token_expiration
            }
        },
        "recommendations": _get_security_recommendations(config, security_level)
    }

def _get_security_recommendations(config: SecurityConfig, security_level: SecurityLevel) -> List[str]:
    """Get security recommendations based on configuration"""
    recommendations = []
    
    if security_level == SecurityLevel.LOW:
        recommendations.extend([
            "Enable all security features",
            "Use strong JWT secrets (32+ characters)",
            "Enable security headers",
            "Enable threat detection",
            "Enable database encryption",
            "Enable CSRF protection"
        ])
    elif security_level == SecurityLevel.MEDIUM:
        recommendations.extend([
            "Consider enabling additional security features",
            "Review CORS configuration",
            "Enable database audit logging",
            "Consider stronger password requirements"
        ])
    elif security_level == SecurityLevel.HIGH:
        recommendations.extend([
            "Security configuration is good",
            "Consider regular security audits",
            "Monitor security logs regularly"
        ])
    else:  # CRITICAL
        recommendations.extend([
            "Excellent security configuration",
            "Maintain current security posture",
            "Consider advanced threat detection"
        ])
    
    return recommendations

# Global security configuration instance
_security_config: Optional[SecurityConfig] = None

def get_security_config() -> SecurityConfig:
    """Get global security configuration instance"""
    global _security_config
    if _security_config is None:
        _security_config = load_security_config()
    return _security_config

def reload_security_config():
    """Reload security configuration"""
    global _security_config
    _security_config = load_security_config()
    return _security_config
