"""
Prometheus monitoring middleware for FastAPI
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging

logger = logging.getLogger(__name__)

# Metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

REQUEST_IN_PROGRESS = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed',
    ['method', 'endpoint']
)

ANALYSIS_COUNT = Counter(
    'analysis_total',
    'Total number of product analyses',
    ['analysis_type']
)

ANALYSIS_DURATION = Histogram(
    'analysis_duration_seconds',
    'Product analysis duration in seconds',
    ['analysis_type']
)

OCR_SUCCESS_RATE = Gauge(
    'ocr_success_rate',
    'OCR success rate percentage'
)

EXTERNAL_API_CALLS = Counter(
    'external_api_calls_total',
    'Total external API calls',
    ['api_name', 'status']
)

CACHE_HIT_RATE = Gauge(
    'cache_hit_rate',
    'Cache hit rate percentage',
    ['cache_type']
)

class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect Prometheus metrics
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)
        
        method = request.method
        endpoint = request.url.path
        
        # Track request in progress
        REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()
        
        # Start timer
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            status = response.status_code
            
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
            REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
            
            return response
            
        except Exception as e:
            # Record error
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=500).inc()
            logger.error(f"Request failed: {e}")
            raise
            
        finally:
            # Decrement in-progress counter
            REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()


async def metrics_endpoint(request: Request):
    """
    Endpoint to expose Prometheus metrics
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def track_analysis(analysis_type: str, duration: float):
    """
    Track product analysis metrics
    """
    ANALYSIS_COUNT.labels(analysis_type=analysis_type).inc()
    ANALYSIS_DURATION.labels(analysis_type=analysis_type).observe(duration)


def track_ocr_success_rate(success_count: int, total_count: int):
    """
    Update OCR success rate
    """
    if total_count > 0:
        rate = (success_count / total_count) * 100
        OCR_SUCCESS_RATE.set(rate)


def track_external_api_call(api_name: str, success: bool):
    """
    Track external API calls
    """
    status = "success" if success else "failure"
    EXTERNAL_API_CALLS.labels(api_name=api_name, status=status).inc()


def track_cache_hit_rate(cache_type: str, hits: int, misses: int):
    """
    Update cache hit rate
    """
    total = hits + misses
    if total > 0:
        rate = (hits / total) * 100
        CACHE_HIT_RATE.labels(cache_type=cache_type).set(rate)

