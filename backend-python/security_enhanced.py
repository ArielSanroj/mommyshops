"""
Enhanced security utilities for MommyShops backend.
Extends the existing security.py with advanced features.
"""

import os
import re
import time
import html
import secrets
import hashlib
import hmac
from collections import defaultdict, deque
from typing import Deque, Dict, Optional, Any
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, UploadFile
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
import logging

# Security audit logger
audit_logger = logging.getLogger("security_audit")

class InputSanitizer:
    """Input sanitization to prevent XSS and injection attacks"""
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """Sanitize user input to prevent XSS"""
        if not isinstance(value, str):
            return str(value)
        # Remove null bytes and control characters
        value = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', value)
        # HTML escape
        value = html.escape(value.strip())
        return value
    
    @staticmethod
    def validate_sql_input(value: str) -> bool:
        """Validate SQL input to prevent injection"""
        if not isinstance(value, str):
            return True
        
        dangerous_patterns = [
            r';\s*drop\s+', r';\s*delete\s+', r';\s*insert\s+', r';\s*update\s+',
            r';\s*create\s+', r';\s*alter\s+', r';\s*exec\s+', r';\s*execute\s+',
            r'union\s+select', r'--', r'/\*', r'\*/', r'xp_', r'sp_'
        ]
        
        value_lower = value.lower()
        return not any(re.search(pattern, value_lower) for pattern in dangerous_patterns)
    
    @staticmethod
    def validate_file_upload(file: UploadFile) -> bool:
        """Validate file uploads for security"""
        if not file:
            return False
            
        # Check file type
        allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
        if file.content_type not in allowed_types:
            raise HTTPException(400, "Invalid file type. Only images are allowed.")
        
        # Check file size (5MB max)
        max_size = 5 * 1024 * 1024
        if hasattr(file, 'size') and file.size > max_size:
            raise HTTPException(400, "File too large. Maximum size is 5MB.")
        
        # Check file extension
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        if hasattr(file, 'filename'):
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in allowed_extensions:
                raise HTTPException(400, "Invalid file extension.")
        
        return True

class CSRFProtection:
    """CSRF protection implementation"""
    
    def __init__(self):
        self.secret_key = os.getenv("CSRF_SECRET", secrets.token_urlsafe(32))
        self.tokens: Dict[str, str] = {}
    
    def generate_csrf_token(self, user_id: str) -> str:
        """Generate CSRF token for user"""
        timestamp = str(int(time.time()))
        data = f"{user_id}:{timestamp}"
        token = hmac.new(
            self.secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Store token with expiration
        self.tokens[user_id] = token
        return token
    
    def validate_csrf_token(self, token: str, user_id: str) -> bool:
        """Validate CSRF token"""
        if user_id not in self.tokens:
            return False
        
        stored_token = self.tokens[user_id]
        return hmac.compare_digest(token, stored_token)
    
    def revoke_token(self, user_id: str):
        """Revoke CSRF token for user"""
        self.tokens.pop(user_id, None)

class SecurityHeaders:
    """Security headers implementation"""
    
    @staticmethod
    def add_security_headers(response: Response):
        """Add comprehensive security headers"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

class SecurityAuditLogger:
    """Security audit logging"""
    
    def __init__(self):
        self.audit_logger = audit_logger
    
    def log_auth_attempt(self, user_id: str, ip: str, success: bool, endpoint: str = None):
        """Log authentication attempts"""
        self.audit_logger.info({
            "event": "auth_attempt",
            "user_id": user_id,
            "ip": ip,
            "success": success,
            "endpoint": endpoint,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def log_rate_limit_hit(self, ip: str, endpoint: str, limit: int):
        """Log rate limit violations"""
        self.audit_logger.warning({
            "event": "rate_limit_hit",
            "ip": ip,
            "endpoint": endpoint,
            "limit": limit,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def log_security_event(self, event_type: str, details: dict):
        """Log general security events"""
        self.audit_logger.warning({
            "event": "security_event",
            "event_type": event_type,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def log_suspicious_activity(self, ip: str, activity: str, details: dict):
        """Log suspicious activity"""
        self.audit_logger.error({
            "event": "suspicious_activity",
            "ip": ip,
            "activity": activity,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })

class AdvancedRateLimiter(BaseHTTPMiddleware):
    """Advanced rate limiter with per-user and per-IP limits"""
    
    def __init__(self, app, limit: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.limit = max(1, limit)
        self.window = max(1, window_seconds)
        self._requests: Dict[str, Deque[float]] = defaultdict(deque)
        self.audit_logger = SecurityAuditLogger()
        
        # Per-user limits (higher for authenticated users)
        self.user_limits: Dict[str, int] = {}
        self.ip_limits: Dict[str, int] = {}
    
    async def dispatch(self, request: Request, call_next) -> Response:
        client_id = self._resolve_client_id(request)
        user_id = getattr(request.state, 'user_id', None)
        
        # Determine rate limit
        if user_id:
            limit = self._get_user_limit(user_id)
        else:
            limit = self._get_ip_limit(client_id)
        
        now = time.time()
        bucket = self._requests[client_id]
        
        # Clean old requests
        while bucket and now - bucket[0] > self.window:
            bucket.popleft()
        
        # Check rate limit
        if len(bucket) >= limit:
            self.audit_logger.log_rate_limit_hit(
                client_id, 
                str(request.url), 
                limit
            )
            
            retry_after = max(1, int(self.window - (now - bucket[0])))
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": retry_after,
                    "limit": limit,
                    "window": self.window
                },
                headers={"Retry-After": str(retry_after)},
            )
        
        bucket.append(now)
        response = await call_next(request)
        
        # Add security headers
        SecurityHeaders.add_security_headers(response)
        
        return response
    
    def _resolve_client_id(self, request: Request) -> str:
        """Resolve client ID from request"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host or "unknown"
        return "unknown"
    
    def _get_user_limit(self, user_id: str) -> int:
        """Get rate limit for specific user"""
        return self.user_limits.get(user_id, self.limit * 2)  # 2x limit for authenticated users
    
    def _get_ip_limit(self, ip: str) -> int:
        """Get rate limit for specific IP"""
        return self.ip_limits.get(ip, self.limit)
    
    def set_user_limit(self, user_id: str, limit: int):
        """Set custom rate limit for user"""
        self.user_limits[user_id] = limit
    
    def set_ip_limit(self, ip: str, limit: int):
        """Set custom rate limit for IP"""
        self.ip_limits[ip] = limit

class ThreatDetection:
    """Basic threat detection system"""
    
    def __init__(self):
        self.suspicious_ips: Dict[str, int] = defaultdict(int)
        self.failed_logins: Dict[str, int] = defaultdict(int)
        self.audit_logger = SecurityAuditLogger()
    
    def check_suspicious_activity(self, ip: str, user_id: str = None, endpoint: str = None) -> bool:
        """Check for suspicious activity patterns"""
        # Check for too many failed logins
        if self.failed_logins[ip] > 5:
            self.audit_logger.log_suspicious_activity(
                ip, "excessive_failed_logins", 
                {"count": self.failed_logins[ip]}
            )
            return True
        
        # Check for rapid requests from same IP
        if self.suspicious_ips[ip] > 10:
            self.audit_logger.log_suspicious_activity(
                ip, "rapid_requests", 
                {"count": self.suspicious_ips[ip]}
            )
            return True
        
        return False
    
    def record_failed_login(self, ip: str):
        """Record failed login attempt"""
        self.failed_logins[ip] += 1
    
    def record_suspicious_request(self, ip: str):
        """Record suspicious request"""
        self.suspicious_ips[ip] += 1
    
    def reset_counters(self, ip: str):
        """Reset counters for IP"""
        self.failed_logins.pop(ip, None)
        self.suspicious_ips.pop(ip, None)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.sanitizer = InputSanitizer()
        self.csrf = CSRFProtection()
        self.audit_logger = SecurityAuditLogger()
        self.threat_detection = ThreatDetection()
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Get client info
        client_ip = self._get_client_ip(request)
        
        # Check for suspicious activity
        if self.threat_detection.check_suspicious_activity(client_ip):
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied due to suspicious activity"}
            )
        
        # Sanitize request data
        if hasattr(request, 'json') and request.json:
            self._sanitize_request_data(request)
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        SecurityHeaders.add_security_headers(response)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host or "unknown"
        return "unknown"
    
    def _sanitize_request_data(self, request: Request):
        """Sanitize request data"""
        # This would need to be implemented based on your request structure
        pass

def configure_enhanced_security(app) -> None:
    """Configure enhanced security features"""
    
    # Rate limiting
    minute_limit = int(os.getenv("RATE_LIMIT_PER_MINUTE", "90"))
    window_seconds = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    
    app.add_middleware(
        AdvancedRateLimiter,
        limit=minute_limit,
        window_seconds=window_seconds,
    )
    
    # Security middleware
    app.add_middleware(SecurityMiddleware)
    
    # Configure audit logging
    audit_handler = logging.StreamHandler()
    audit_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(logging.INFO)

# Security utilities for use in endpoints
def validate_and_sanitize_input(data: dict) -> dict:
    """Validate and sanitize input data"""
    sanitizer = InputSanitizer()
    sanitized_data = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            sanitized_data[key] = sanitizer.sanitize_string(value)
        else:
            sanitized_data[key] = value
    
    return sanitized_data

def check_csrf_token(token: str, user_id: str) -> bool:
    """Check CSRF token validity"""
    csrf = CSRFProtection()
    return csrf.validate_csrf_token(token, user_id)

def log_security_event(event_type: str, details: dict):
    """Log security event"""
    audit_logger = SecurityAuditLogger()
    audit_logger.log_security_event(event_type, details)
