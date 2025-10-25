"""
Centralized logging configuration for MommyShops application
Structured logging with JSON format for production
"""

import json
import logging
import logging.config
import os
import sys
from typing import Dict, Any
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
                "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
                "created", "msecs", "relativeCreated", "thread", "threadName",
                "processName", "process", "message"
            }:
                log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(environment: str = "development") -> None:
    """
    Setup application logging configuration
    
    Args:
        environment: Environment name (development, production, testing)
    """
    
    # Determine log level based on environment
    log_level = "DEBUG" if environment == "development" else "INFO"
    
    # Configure logging
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JSONFormatter,
            },
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "simple" if environment == "development" else "json",
                "stream": sys.stdout
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            }
        },
        "loggers": {
            "mommyshops": {
                "level": log_level,
                "handlers": ["console", "file"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            }
        },
        "root": {
            "level": "WARNING",
            "handlers": ["console"]
        }
    }
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Apply configuration
    logging.config.dictConfig(logging_config)
    
    # Log startup message
    logger = logging.getLogger("mommyshops")
    logger.info(f"Logging configured for {environment} environment")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with proper configuration
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(f"mommyshops.{name}")


def log_request(request_id: str, method: str, path: str, status_code: int, duration: float) -> None:
    """
    Log HTTP request details
    
    Args:
        request_id: Unique request ID
        method: HTTP method
        path: Request path
        status_code: Response status code
        duration: Request duration in seconds
    """
    logger = get_logger("requests")
    logger.info(
        "HTTP request completed",
        extra={
            "request_id": request_id,
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration * 1000, 2)
        }
    )


def log_error(error: Exception, context: Dict[str, Any] = None) -> None:
    """
    Log error with context
    
    Args:
        error: Exception instance
        context: Additional context information
    """
    logger = get_logger("errors")
    logger.error(
        f"Error occurred: {str(error)}",
        exc_info=True,
        extra=context or {}
    )
