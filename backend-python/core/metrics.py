"""
Comprehensive metrics and monitoring for MommyShops
Implements Prometheus metrics, health checks, and performance monitoring
"""

import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from functools import wraps
import asyncio
from datetime import datetime, timedelta

# Prometheus metrics
try:
    from prometheus_client import (
        Counter, Histogram, Gauge, Summary, Info,
        CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST,
        start_http_server, push_to_gateway
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Create dummy classes for when prometheus_client is not available
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def time(self): return self
        def __enter__(self): return self
        def __exit__(self, *args): pass
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def dec(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    class Summary:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def time(self): return self
        def __enter__(self): return self
        def __exit__(self, *args): pass
    class Info:
        def __init__(self, *args, **kwargs): pass
        def info(self, *args, **kwargs): pass

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Metric type enumeration"""
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    GAUGE = "gauge"
    SUMMARY = "summary"
    INFO = "info"

@dataclass
class MetricConfig:
    """Metric configuration"""
    enabled: bool = True
    prometheus_enabled: bool = True
    pushgateway_enabled: bool = False
    pushgateway_url: str = "http://localhost:9091"
    pushgateway_job: str = "mommyshops"
    push_interval: int = 60  # seconds
    http_server_port: int = 8001
    http_server_enabled: bool = True

class MetricsCollector:
    """Comprehensive metrics collector for MommyShops"""
    
    def __init__(self, config: MetricConfig):
        self.config = config
        self.registry = CollectorRegistry() if PROMETHEUS_AVAILABLE else None
        self._metrics: Dict[str, Any] = {}
        self._start_time = time.time()
        self._init_metrics()
    
    def _init_metrics(self):
        """Initialize all metrics"""
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus client not available, using dummy metrics")
            return
        
        # Application metrics
        self._metrics['app_info'] = Info(
            'mommyshops_app_info',
            'Application information',
            registry=self.registry
        )
        
        # Request metrics
        self._metrics['http_requests_total'] = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self._metrics['http_request_duration'] = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint'],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
            registry=self.registry
        )
        
        # Analysis metrics
        self._metrics['analysis_requests_total'] = Counter(
            'analysis_requests_total',
            'Total analysis requests',
            ['analysis_type', 'user_need'],
            registry=self.registry
        )
        
        self._metrics['analysis_duration'] = Histogram(
            'analysis_duration_seconds',
            'Analysis processing duration',
            ['analysis_type'],
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
            registry=self.registry
        )
        
        self._metrics['analysis_success_rate'] = Gauge(
            'analysis_success_rate',
            'Analysis success rate',
            ['analysis_type'],
            registry=self.registry
        )
        
        # Ingredient metrics
        self._metrics['ingredient_analysis_total'] = Counter(
            'ingredient_analysis_total',
            'Total ingredient analyses',
            ['ingredient_name', 'risk_level'],
            registry=self.registry
        )
        
        self._metrics['ingredient_eco_score'] = Histogram(
            'ingredient_eco_score',
            'Ingredient eco scores',
            ['ingredient_name'],
            buckets=[0, 20, 40, 60, 80, 100],
            registry=self.registry
        )
        
        # Cache metrics
        self._metrics['cache_operations_total'] = Counter(
            'cache_operations_total',
            'Total cache operations',
            ['operation', 'cache_level', 'result'],
            registry=self.registry
        )
        
        self._metrics['cache_hit_rate'] = Gauge(
            'cache_hit_rate',
            'Cache hit rate',
            ['cache_level'],
            registry=self.registry
        )
        
        self._metrics['cache_size'] = Gauge(
            'cache_size',
            'Cache size',
            ['cache_level'],
            registry=self.registry
        )
        
        # External API metrics
        self._metrics['external_api_requests_total'] = Counter(
            'external_api_requests_total',
            'Total external API requests',
            ['api_name', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self._metrics['external_api_duration'] = Histogram(
            'external_api_duration_seconds',
            'External API request duration',
            ['api_name', 'endpoint'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            registry=self.registry
        )
        
        # OCR metrics
        self._metrics['ocr_requests_total'] = Counter(
            'ocr_requests_total',
            'Total OCR requests',
            ['image_type', 'status'],
            registry=self.registry
        )
        
        self._metrics['ocr_duration'] = Histogram(
            'ocr_duration_seconds',
            'OCR processing duration',
            ['image_type'],
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0],
            registry=self.registry
        )
        
        self._metrics['ocr_confidence'] = Histogram(
            'ocr_confidence',
            'OCR confidence scores',
            ['image_type'],
            buckets=[0.1, 0.3, 0.5, 0.7, 0.9, 1.0],
            registry=self.registry
        )
        
        # Ollama AI metrics
        self._metrics['ollama_requests_total'] = Counter(
            'ollama_requests_total',
            'Total Ollama requests',
            ['model', 'operation', 'status'],
            registry=self.registry
        )
        
        self._metrics['ollama_duration'] = Histogram(
            'ollama_duration_seconds',
            'Ollama processing duration',
            ['model', 'operation'],
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0],
            registry=self.registry
        )
        
        # Database metrics
        self._metrics['database_queries_total'] = Counter(
            'database_queries_total',
            'Total database queries',
            ['operation', 'table', 'status'],
            registry=self.registry
        )
        
        self._metrics['database_duration'] = Histogram(
            'database_duration_seconds',
            'Database query duration',
            ['operation', 'table'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
            registry=self.registry
        )
        
        # System metrics
        self._metrics['memory_usage'] = Gauge(
            'memory_usage_bytes',
            'Memory usage in bytes',
            ['type'],
            registry=self.registry
        )
        
        self._metrics['cpu_usage'] = Gauge(
            'cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )
        
        self._metrics['active_connections'] = Gauge(
            'active_connections',
            'Active connections',
            ['connection_type'],
            registry=self.registry
        )
        
        # Error metrics
        self._metrics['errors_total'] = Counter(
            'errors_total',
            'Total errors',
            ['error_type', 'component', 'severity'],
            registry=self.registry
        )
        
        # Business metrics
        self._metrics['users_total'] = Gauge(
            'users_total',
            'Total number of users',
            registry=self.registry
        )
        
        self._metrics['products_analyzed_total'] = Counter(
            'products_analyzed_total',
            'Total products analyzed',
            ['analysis_type'],
            registry=self.registry
        )
        
        self._metrics['ingredients_analyzed_total'] = Counter(
            'ingredients_analyzed_total',
            'Total ingredients analyzed',
            registry=self.registry
        )
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        if not self.config.enabled:
            return
        
        self._metrics['http_requests_total'].labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        self._metrics['http_request_duration'].labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_analysis_request(self, analysis_type: str, user_need: str, duration: float, success: bool):
        """Record analysis request metrics"""
        if not self.config.enabled:
            return
        
        self._metrics['analysis_requests_total'].labels(
            analysis_type=analysis_type,
            user_need=user_need
        ).inc()
        
        self._metrics['analysis_duration'].labels(
            analysis_type=analysis_type
        ).observe(duration)
        
        # Update success rate
        # This is a simplified implementation
        # In production, you'd want to track success/failure over time
        if success:
            self._metrics['analysis_success_rate'].labels(
                analysis_type=analysis_type
            ).set(1.0)
        else:
            self._metrics['analysis_success_rate'].labels(
                analysis_type=analysis_type
            ).set(0.0)
    
    def record_ingredient_analysis(self, ingredient_name: str, risk_level: str, eco_score: float):
        """Record ingredient analysis metrics"""
        if not self.config.enabled:
            return
        
        self._metrics['ingredient_analysis_total'].labels(
            ingredient_name=ingredient_name,
            risk_level=risk_level
        ).inc()
        
        self._metrics['ingredient_eco_score'].labels(
            ingredient_name=ingredient_name
        ).observe(eco_score)
    
    def record_cache_operation(self, operation: str, cache_level: str, result: str):
        """Record cache operation metrics"""
        if not self.config.enabled:
            return
        
        self._metrics['cache_operations_total'].labels(
            operation=operation,
            cache_level=cache_level,
            result=result
        ).inc()
    
    def record_external_api_request(self, api_name: str, endpoint: str, status: str, duration: float):
        """Record external API request metrics"""
        if not self.config.enabled:
            return
        
        self._metrics['external_api_requests_total'].labels(
            api_name=api_name,
            endpoint=endpoint,
            status=status
        ).inc()
        
        self._metrics['external_api_duration'].labels(
            api_name=api_name,
            endpoint=endpoint
        ).observe(duration)
    
    def record_ocr_request(self, image_type: str, status: str, duration: float, confidence: float):
        """Record OCR request metrics"""
        if not self.config.enabled:
            return
        
        self._metrics['ocr_requests_total'].labels(
            image_type=image_type,
            status=status
        ).inc()
        
        self._metrics['ocr_duration'].labels(
            image_type=image_type
        ).observe(duration)
        
        self._metrics['ocr_confidence'].labels(
            image_type=image_type
        ).observe(confidence)
    
    def record_ollama_request(self, model: str, operation: str, status: str, duration: float):
        """Record Ollama request metrics"""
        if not self.config.enabled:
            return
        
        self._metrics['ollama_requests_total'].labels(
            model=model,
            operation=operation,
            status=status
        ).inc()
        
        self._metrics['ollama_duration'].labels(
            model=model,
            operation=operation
        ).observe(duration)
    
    def record_database_query(self, operation: str, table: str, status: str, duration: float):
        """Record database query metrics"""
        if not self.config.enabled:
            return
        
        self._metrics['database_queries_total'].labels(
            operation=operation,
            table=table,
            status=status
        ).inc()
        
        self._metrics['database_duration'].labels(
            operation=operation,
            table=table
        ).observe(duration)
    
    def record_error(self, error_type: str, component: str, severity: str):
        """Record error metrics"""
        if not self.config.enabled:
            return
        
        self._metrics['errors_total'].labels(
            error_type=error_type,
            component=component,
            severity=severity
        ).inc()
    
    def update_system_metrics(self, memory_usage: int, cpu_usage: float, active_connections: int):
        """Update system metrics"""
        if not self.config.enabled:
            return
        
        self._metrics['memory_usage'].labels(type='heap').set(memory_usage)
        self._metrics['cpu_usage'].set(cpu_usage)
        self._metrics['active_connections'].labels(connection_type='http').set(active_connections)
    
    def update_business_metrics(self, users_total: int, products_analyzed: int, ingredients_analyzed: int):
        """Update business metrics"""
        if not self.config.enabled:
            return
        
        self._metrics['users_total'].set(users_total)
        self._metrics['products_analyzed_total'].labels(analysis_type='all').inc(products_analyzed)
        self._metrics['ingredients_analyzed_total'].inc(ingredients_analyzed)
    
    def get_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        if not PROMETHEUS_AVAILABLE:
            return "# Prometheus client not available\n"
        
        return generate_latest(self.registry)
    
    def start_http_server(self):
        """Start HTTP server for metrics"""
        if not self.config.http_server_enabled or not PROMETHEUS_AVAILABLE:
            return
        
        try:
            start_http_server(self.config.http_server_port)
            logger.info(f"Metrics server started on port {self.config.http_server_port}")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
    
    def push_metrics(self):
        """Push metrics to Pushgateway"""
        if not self.config.pushgateway_enabled or not PROMETHEUS_AVAILABLE:
            return
        
        try:
            push_to_gateway(
                self.config.pushgateway_url,
                job=self.config.pushgateway_job,
                registry=self.registry
            )
            logger.debug("Metrics pushed to Pushgateway")
        except Exception as e:
            logger.error(f"Failed to push metrics: {e}")

# Global metrics collector
_metrics_collector: Optional[MetricsCollector] = None

def get_metrics_collector() -> Optional[MetricsCollector]:
    """Get global metrics collector"""
    return _metrics_collector

def init_metrics(config: MetricConfig) -> MetricsCollector:
    """Initialize global metrics collector"""
    global _metrics_collector
    _metrics_collector = MetricsCollector(config)
    return _metrics_collector

# Decorators for automatic metrics collection

def track_http_request(func):
    """Decorator to track HTTP requests"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        status_code = 200
        
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time
            collector = get_metrics_collector()
            if collector:
                # Extract method and endpoint from function
                method = "GET"  # Default, would be extracted from request
                endpoint = func.__name__
                collector.record_http_request(method, endpoint, status_code, duration)
    
    return wrapper

def track_analysis(func):
    """Decorator to track analysis requests"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        success = True
        
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            success = False
            raise
        finally:
            duration = time.time() - start_time
            collector = get_metrics_collector()
            if collector:
                analysis_type = func.__name__
                user_need = kwargs.get('user_need', 'unknown')
                collector.record_analysis_request(analysis_type, user_need, duration, success)
    
    return wrapper

def track_cache_operation(operation: str, cache_level: str):
    """Decorator to track cache operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = "success"
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                result = "error"
                raise
            finally:
                collector = get_metrics_collector()
                if collector:
                    collector.record_cache_operation(operation, cache_level, result)
        
        return wrapper
    return decorator

def track_external_api(api_name: str, endpoint: str):
    """Decorator to track external API requests"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                collector = get_metrics_collector()
                if collector:
                    collector.record_external_api_request(api_name, endpoint, status, duration)
        
        return wrapper
    return decorator

# Health check functions
def check_health() -> Dict[str, Any]:
    """Check system health"""
    health = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time() - (_metrics_collector._start_time if _metrics_collector else time.time()),
        "components": {}
    }
    
    # Check metrics collector
    if _metrics_collector:
        health["components"]["metrics"] = "healthy"
    else:
        health["components"]["metrics"] = "unhealthy"
    
    return health

def get_metrics_summary() -> Dict[str, Any]:
    """Get metrics summary"""
    if not _metrics_collector:
        return {}
    
    return {
        "uptime": time.time() - _metrics_collector._start_time,
        "metrics_count": len(_metrics_collector._metrics),
        "prometheus_available": PROMETHEUS_AVAILABLE,
        "config": {
            "enabled": _metrics_collector.config.enabled,
            "prometheus_enabled": _metrics_collector.config.prometheus_enabled,
            "pushgateway_enabled": _metrics_collector.config.pushgateway_enabled
        }
    }
