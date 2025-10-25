"""
Structured JSON logging with secret sanitization
"""

import json
import logging
import re
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import traceback
import sys

class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: str
    level: str
    logger: str
    message: str
    service: str
    version: str
    environment: str
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    duration_ms: Optional[float] = None
    status_code: Optional[int] = None
    method: Optional[str] = None
    url: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class SecretSanitizer:
    """Secret sanitization utility"""
    
    def __init__(self):
        # Common secret patterns
        self.secret_patterns = [
            r'password["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'passwd["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'pwd["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'secret["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'token["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'key["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'api_key["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'access_token["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'refresh_token["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'auth["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'authorization["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'jwt["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'bearer["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'credential["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'private_key["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'public_key["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.secret_patterns]
    
    def sanitize(self, data: Any) -> Any:
        """Sanitize data by replacing secrets with placeholders"""
        if isinstance(data, str):
            return self._sanitize_string(data)
        elif isinstance(data, dict):
            return self._sanitize_dict(data)
        elif isinstance(data, list):
            return self._sanitize_list(data)
        else:
            return data
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize string by replacing secrets"""
        sanitized = text
        
        for pattern in self.compiled_patterns:
            sanitized = pattern.sub(r'\1', sanitized)
            # Replace with placeholder
            sanitized = re.sub(
                r'password["\']?\s*[:=]\s*["\']?[^"\'\s]+',
                'password="***"',
                sanitized,
                flags=re.IGNORECASE
            )
            sanitized = re.sub(
                r'secret["\']?\s*[:=]\s*["\']?[^"\'\s]+',
                'secret="***"',
                sanitized,
                flags=re.IGNORECASE
            )
            sanitized = re.sub(
                r'token["\']?\s*[:=]\s*["\']?[^"\'\s]+',
                'token="***"',
                sanitized,
                flags=re.IGNORECASE
            )
            sanitized = re.sub(
                r'key["\']?\s*[:=]\s*["\']?[^"\'\s]+',
                'key="***"',
                sanitized,
                flags=re.IGNORECASE
            )
        
        return sanitized
    
    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize dictionary"""
        sanitized = {}
        
        for key, value in data.items():
            # Check if key indicates a secret
            if self._is_secret_key(key):
                sanitized[key] = "***"
            else:
                sanitized[key] = self.sanitize(value)
        
        return sanitized
    
    def _sanitize_list(self, data: List[Any]) -> List[Any]:
        """Sanitize list"""
        return [self.sanitize(item) for item in data]
    
    def _is_secret_key(self, key: str) -> bool:
        """Check if key indicates a secret"""
        secret_keywords = [
            'password', 'passwd', 'pwd', 'secret', 'token', 'key',
            'api_key', 'access_token', 'refresh_token', 'auth',
            'authorization', 'jwt', 'bearer', 'credential',
            'private_key', 'public_key'
        ]
        
        key_lower = key.lower()
        return any(keyword in key_lower for keyword in secret_keywords)

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def __init__(self, service_name: str = "mommyshops", version: str = "1.0.0"):
        self.service_name = service_name
        self.version = version
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.sanitizer = SecretSanitizer()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        # Create log entry
        log_entry = LogEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            level=record.levelname,
            logger=record.name,
            message=record.getMessage(),
            service=self.service_name,
            version=self.version,
            environment=self.environment,
            request_id=getattr(record, 'request_id', None),
            user_id=getattr(record, 'user_id', None),
            session_id=getattr(record, 'session_id', None),
            correlation_id=getattr(record, 'correlation_id', None),
            duration_ms=getattr(record, 'duration_ms', None),
            status_code=getattr(record, 'status_code', None),
            method=getattr(record, 'method', None),
            url=getattr(record, 'url', None),
            user_agent=getattr(record, 'user_agent', None),
            ip_address=getattr(record, 'ip_address', None),
            error_code=getattr(record, 'error_code', None),
            error_message=getattr(record, 'error_message', None),
            stack_trace=getattr(record, 'stack_trace', None),
            metadata=getattr(record, 'metadata', None)
        )
        
        # Convert to dict and sanitize
        log_dict = asdict(log_entry)
        sanitized_dict = self.sanitizer.sanitize(log_dict)
        
        # Add exception info if present
        if record.exc_info:
            sanitized_dict['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(sanitized_dict, ensure_ascii=False, separators=(',', ':'))

class StructuredLogger:
    """Structured logger with context"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context = {}
    
    def set_context(self, **kwargs):
        """Set logging context"""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear logging context"""
        self.context.clear()
    
    def _log(self, level: LogLevel, message: str, **kwargs):
        """Log with structured data"""
        # Merge context with additional data
        log_data = {**self.context, **kwargs}
        
        # Create log record with extra data
        extra = {}
        for key, value in log_data.items():
            extra[key] = value
        
        # Log with extra data
        getattr(self.logger, level.value.lower())(message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self._log(LogLevel.CRITICAL, message, **kwargs)
    
    def log_request(self, method: str, url: str, status_code: int, duration_ms: float, **kwargs):
        """Log HTTP request"""
        self.info(
            f"{method} {url} - {status_code}",
            method=method,
            url=url,
            status_code=status_code,
            duration_ms=duration_ms,
            **kwargs
        )
    
    def log_error(self, error: Exception, error_code: str = None, **kwargs):
        """Log error with stack trace"""
        self.error(
            f"Error: {str(error)}",
            error_code=error_code or error.__class__.__name__,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            **kwargs
        )
    
    def log_performance(self, operation: str, duration_ms: float, **kwargs):
        """Log performance metrics"""
        self.info(
            f"Performance: {operation} took {duration_ms}ms",
            operation=operation,
            duration_ms=duration_ms,
            **kwargs
        )

def setup_logging(
    service_name: str = "mommyshops",
    version: str = "1.0.0",
    level: str = "INFO",
    log_file: str = None
):
    """Setup structured logging"""
    
    # Create formatter
    formatter = JSONFormatter(service_name, version)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    
    return root_logger

def get_logger(name: str) -> StructuredLogger:
    """Get structured logger"""
    return StructuredLogger(name)

# Global logger instance
logger = get_logger(__name__)

# Logging decorators
def log_function_call(func):
    """Decorator to log function calls"""
    def wrapper(*args, **kwargs):
        logger.info(f"Calling {func.__name__}", function=func.__name__, args=args, kwargs=kwargs)
        try:
            result = func(*args, **kwargs)
            logger.info(f"Function {func.__name__} completed successfully", function=func.__name__)
            return result
        except Exception as e:
            logger.log_error(e, function=func.__name__)
            raise
    return wrapper

def log_async_function_call(func):
    """Decorator to log async function calls"""
    async def wrapper(*args, **kwargs):
        logger.info(f"Calling async {func.__name__}", function=func.__name__, args=args, kwargs=kwargs)
        try:
            result = await func(*args, **kwargs)
            logger.info(f"Async function {func.__name__} completed successfully", function=func.__name__)
            return result
        except Exception as e:
            logger.log_error(e, function=func.__name__)
            raise
    return wrapper

def log_performance(func):
    """Decorator to log function performance"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = (time.time() - start_time) * 1000
            logger.log_performance(func.__name__, duration)
            return result
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.log_performance(f"{func.__name__}_error", duration)
            raise
    return wrapper

def log_async_performance(func):
    """Decorator to log async function performance"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = (time.time() - start_time) * 1000
            logger.log_performance(func.__name__, duration)
            return result
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.log_performance(f"{func.__name__}_error", duration)
            raise
    return wrapper