"""
Production-ready API utilities for MommyShops MVP
"""
import asyncio
import copy
import json
import logging
import os
import re
import ssl
import threading
import time
import urllib.request
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

import httpx
import pandas as pd
from Bio import Entrez
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Import scrapers and APIs
from cir_scraper import CIRScraper
from sccs_scraper import SCCSScraper
from iccr_scraper import ICCRScraper
from inci_beauty_api import INCIClient
from cosing_api_store import CosIngClient
from ewg_scraper import EWGScraper

# Import Ollama integration
try:
    from ollama_integration import (
        ollama_integration,
        analyze_ingredient_safety_with_ollama,
        enhance_ocr_text_with_ollama
    )
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("Ollama integration not available")

load_dotenv()

_STANDARD_LOG_KEYS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
}


class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # pragma: no cover - logging helper
        payload = {
            "timestamp": self.formatTime(record, self.datefmt) if self.datefmt else self.formatTime(record),
            "logger": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _STANDARD_LOG_KEYS and not key.startswith("_")
        }
        if extras:
            payload["context"] = extras
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


# Configure logging
logger = logging.getLogger("mommyshops.api_utils")
if not logger.handlers:
    backend_log_path = Path(os.getenv("BACKEND_LOG_PATH", Path(__file__).resolve().parent / "backend.log"))
    try:
        backend_log_path.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(backend_log_path)
        handler.setFormatter(_JSONFormatter())
        logger.addHandler(handler)
    except Exception as log_exc:  # pragma: no cover - logging fallback
        logging.getLogger(__name__).warning("Failed to attach api_utils logger handler", exc_info=log_exc)
logger.setLevel(logging.INFO)
logger.propagate = False

_NORMALIZATION_PATTERN = re.compile(r"[^a-z0-9]+")
_SHARED_NORMALIZER = None
_SHARED_NORMALIZER_INITIALIZED = False


@lru_cache(maxsize=2048)
def _fallback_normalize(value: Optional[str]) -> str:
    if not value:
        return ""
    lowered = str(value).strip().lower()
    if not lowered:
        return ""
    normalized = _NORMALIZATION_PATTERN.sub(" ", lowered)
    return re.sub(r"\s+", " ", normalized).strip()


def _get_shared_normalizer():
    global _SHARED_NORMALIZER_INITIALIZED, _SHARED_NORMALIZER
    if not _SHARED_NORMALIZER_INITIALIZED:
        try:
            from database import normalize_ingredient_name as shared_normalizer  # type: ignore import
            _SHARED_NORMALIZER = shared_normalizer
            logger.debug("Successfully imported shared normalizer from database")
        except Exception as e:
            logger.warning(f"Failed to import shared normalizer from database: {e}. Using fallback normalizer.")
            _SHARED_NORMALIZER = None
        _SHARED_NORMALIZER_INITIALIZED = True
    return _SHARED_NORMALIZER


@lru_cache(maxsize=2048)
def _normalize_ingredient_name(value: Optional[str]) -> str:
    normalizer = _get_shared_normalizer()
    if normalizer:
        return normalizer(value)
    return _fallback_normalize(value)

# Configure SSL context for Entrez
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
urllib.request.install_opener(urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_context)))

# Configuration
EWG_API_KEY = os.getenv("EWG_API_KEY", "your_ewg_api_key_here")
ENTREZ_EMAIL = os.getenv("ENTREZ_EMAIL", "your.email@example.com")
APIFY_API_KEY = os.getenv("APIFY_API_KEY", "your_apify_api_key_here")
INCI_BEAUTY_API_KEY = os.getenv("INCI_BEAUTY_API_KEY", "your_inci_beauty_api_key_here")
COSING_API_KEY = os.getenv("COSING_API_KEY", "your_cosing_api_key_here")

# Rate limiting configuration
RATE_LIMITS = {
    "fda": {"requests_per_minute": 60, "requests_per_hour": 1000},
    "pubchem": {"requests_per_minute": 5, "requests_per_hour": 100},
    "ewg": {"requests_per_minute": 10, "requests_per_hour": 200},
    "invima": {"requests_per_minute": 30, "requests_per_hour": 500},
    "iarc": {"requests_per_minute": 3, "requests_per_hour": 50},
    "cir": {"requests_per_minute": 15, "requests_per_hour": 300},
    "sccs": {"requests_per_minute": 15, "requests_per_hour": 300},
    "iccr": {"requests_per_minute": 15, "requests_per_hour": 300},
    "inci_beauty": {"requests_per_minute": 30, "requests_per_hour": 1000},
    "cosing": {"requests_per_minute": 20, "requests_per_hour": 500}
}

# Timeout configuration - Increased for better reliability
TIMEOUTS = {
    "default": 45.0,  # Increased from 30.0
    "fda": 20.0,      # Increased from 15.0
    "pubchem": 25.0,  # Increased from 20.0
    "ewg": 20.0,      # Increased from 15.0
    "invima": 30.0,   # Increased from 25.0
    "iarc": 15.0,     # Increased from 10.0
    "cir": 25.0,      # Increased from 20.0
    "sccs": 25.0,     # Increased from 20.0
    "iccr": 25.0,     # Increased from 20.0
    "inci_beauty": 20.0,  # Increased from 15.0
    "cosing": 25.0    # Increased from 20.0
}

@dataclass
class APIResponse:
    """Standardized API response format."""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    source: str = ""
    cached: bool = False
    retry_count: int = 0

class RateLimiter:
    """Rate limiter for API calls."""
    
    def __init__(self, requests_per_minute: int, requests_per_hour: int):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.minute_requests = []
        self.hour_requests = []
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire permission to make a request."""
        async with self._lock:
            now = time.time()
            
            # Clean old requests
            self.minute_requests = [req_time for req_time in self.minute_requests if now - req_time < 60]
            self.hour_requests = [req_time for req_time in self.hour_requests if now - req_time < 3600]
            
            # Check limits
            if len(self.minute_requests) >= self.requests_per_minute:
                sleep_time = 60 - (now - self.minute_requests[0])
                logger.warning(f"Rate limit exceeded, sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
                return await self.acquire()
            
            if len(self.hour_requests) >= self.requests_per_hour:
                sleep_time = 3600 - (now - self.hour_requests[0])
                logger.warning(f"Hourly rate limit exceeded, sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
                return await self.acquire()
            
            # Record this request
            self.minute_requests.append(now)
            self.hour_requests.append(now)

class CircuitBreaker:
    """Circuit breaker pattern for API resilience."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.error(f"Circuit breaker opened for {func.__name__}")
            
            raise e

class APICache:
    """Thread-safe in-memory cache for API responses with TTL handling."""

    def __init__(self, ttl: int = 3600):  # 1 hour TTL by default
        self.ttl = ttl
        self._store: Dict[str, Tuple[Dict[str, Any], float]] = {}
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        now = time.time()
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                self._misses += 1
                return None

            payload, expires_at = entry
            if expires_at <= now:
                self._evictions += 1
                self._misses += 1
                self._store.pop(key, None)
                return None

            self._hits += 1
            return copy.deepcopy(payload)

    def set(self, key: str, data: Dict[str, Any]) -> None:
        expires_at = time.time() + self.ttl
        with self._lock:
            self._store[key] = (copy.deepcopy(data), expires_at)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "ttl": self.ttl,
                "size": len(self._store),
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
            }

    def keys(self) -> List[str]:
        with self._lock:
            return list(self._store.keys())

# Global instances
rate_limiters = {
    "fda": RateLimiter(**RATE_LIMITS["fda"]),
    "pubchem": RateLimiter(**RATE_LIMITS["pubchem"]),
    "ewg": RateLimiter(**RATE_LIMITS["ewg"]),
    "invima": RateLimiter(**RATE_LIMITS["invima"]),
    "iarc": RateLimiter(**RATE_LIMITS["iarc"]),
    "cir": RateLimiter(**RATE_LIMITS["cir"]),
    "sccs": RateLimiter(**RATE_LIMITS["sccs"]),
    "iccr": RateLimiter(**RATE_LIMITS["iccr"]),
    "inci_beauty": RateLimiter(**RATE_LIMITS["inci_beauty"]),
    "cosing": RateLimiter(**RATE_LIMITS["cosing"])
}

circuit_breakers = {
    "fda": CircuitBreaker(),
    "pubchem": CircuitBreaker(),
    "ewg": CircuitBreaker(),
    "invima": CircuitBreaker(),
    "iarc": CircuitBreaker(),
    "cir": CircuitBreaker(),
    "sccs": CircuitBreaker(),
    "iccr": CircuitBreaker(),
    "inci_beauty": CircuitBreaker(),
    "cosing": CircuitBreaker()
}

api_cache = APICache()


def _build_default_payload(source: str = "") -> Dict[str, Any]:
    return {
        "benefits": "No disponible",
        "risks_detailed": "No disponible",
        "risk_level": "desconocido",
        "sources": source,
    }


async def _fetch_with_scraper(
    provider_key: str,
    ingredient: str,
    scraper_cls,
    *,
    source_label: str,
    cache_prefix: Optional[str] = None,
) -> APIResponse:
    prefix = cache_prefix or provider_key
    cache_key = _cache_key(prefix, ingredient)
    cached_data = api_cache.get(cache_key)
    if cached_data:
        logger.debug("%s cache hit for %s", source_label, ingredient)
        return APIResponse(success=True, data=cached_data, source=source_label, cached=True)

    async def _scrape():
        async with scraper_cls() as scraper:
            return await scraper.get_ingredient_data(ingredient)

    async def _wrapped_scrape():
        await rate_limiters[provider_key].acquire()
        return await _scrape()

    try:
        result = await circuit_breakers[provider_key].call(_wrapped_scrape)
        if result.get("success"):
            data = result.get("data", {}) or {}
            if data:
                api_cache.set(cache_key, data)
            return APIResponse(success=True, data=data, source=source_label)

        error_message = result.get("error", "Unknown error")
        fallback = _build_default_payload(source_label)
        return APIResponse(success=False, data=fallback, error=error_message, source=source_label)
    except Exception as exc:
        logger.error("%s scraping error for %s: %s", source_label, ingredient, exc)
        fallback = _build_default_payload(source_label)
        return APIResponse(success=False, data=fallback, error=str(exc), source=source_label)


async def _fetch_with_client(
    provider_key: str,
    ingredient: str,
    client_cls,
    *,
    source_label: str,
    cache_prefix: Optional[str] = None,
) -> APIResponse:
    prefix = cache_prefix or provider_key
    cache_key = _cache_key(prefix, ingredient)
    cached_data = api_cache.get(cache_key)
    if cached_data:
        logger.debug("%s cache hit for %s", source_label, ingredient)
        return APIResponse(success=True, data=cached_data, source=source_label, cached=True)

    async def _call_client():
        async with client_cls() as client:
            return await client.get_ingredient_data(ingredient)

    async def _wrapped_call():
        await rate_limiters[provider_key].acquire()
        return await _call_client()

    try:
        result = await circuit_breakers[provider_key].call(_wrapped_call)
        if getattr(result, "success", False):
            data = dict(getattr(result, "data", {}) or {})
            if data:
                api_cache.set(cache_key, data)
            source_name = getattr(result, "source", source_label)
            return APIResponse(success=True, data=data, source=source_name)

        error_message = getattr(result, "error", "Unknown error")
        source_name = getattr(result, "source", source_label)
        fallback = _build_default_payload(source_name)
        return APIResponse(success=False, data=fallback, error=error_message, source=source_name)
    except Exception as exc:
        logger.error("%s client error for %s: %s", source_label, ingredient, exc)
        fallback = _build_default_payload(source_label)
        return APIResponse(success=False, data=fallback, error=str(exc), source=source_label)


def _cache_key(prefix: str, ingredient: str) -> str:
    normalized = normalize_ingredient_name(ingredient)
    return f"{prefix}:{normalized}" if normalized else f"{prefix}:{ingredient.strip().lower()}"


def _merge_sources(*values: Optional[str]) -> str:
    seen: Dict[str, None] = {}
    for value in values:
        if not value:
            continue
        fragments = [fragment.strip() for fragment in str(value).split(",") if fragment.strip()]
        for fragment in fragments:
            if fragment not in seen:
                seen[fragment] = None
    return ",".join(seen.keys())


_EMPTY_FIELD_MARKERS = {"", "no disponible", "desconocido", "datos insuficientes para evaluación"}


def _first_non_placeholder(responses: Dict[str, APIResponse], order: List[str], field: str) -> Optional[Any]:
    for provider in order:
        response = responses.get(provider)
        if not response:
            continue
        value = response.data.get(field)
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped or stripped.lower() in _EMPTY_FIELD_MARKERS:
                continue
            return value
        if value is None:
            continue
        return value
    return None


def _normalize_text_field(value: Any, default: str) -> str:
    if value is None:
        return default
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else default
    if isinstance(value, (list, tuple, set)):
        parts = [str(item).strip() for item in value if str(item).strip()]
        return ", ".join(parts) if parts else default
    if isinstance(value, dict):
        parts = [f"{key}: {val}" for key, val in value.items() if val is not None]
        return ", ".join(parts) if parts else default
    return str(value)


RISK_PRIORITY_ORDER = [
    "IARC",
    "FDA",
    "CIR",
    "SCCS",
    "INVIMA",
    "EWG",
    "ICCR",
    "INCI Beauty",
    "CosIng API",
    "CosIng CSV",
]

BENEFITS_PRIORITY_ORDER = [
    "INCI Beauty",
    "CIR",
    "SCCS",
    "CosIng API",
    "PubChem",
    "CosIng CSV",
]

RISK_DETAILS_PRIORITY_ORDER = [
    "IARC",
    "FDA",
    "CIR",
    "SCCS",
    "EWG",
    "INVIMA",
    "ICCR",
    "INCI Beauty",
    "CosIng API",
    "CosIng CSV",
    "PubChem",
]

async def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    """Retry function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
            await asyncio.sleep(delay)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
)
async def fetch_fda_data(ingredient: str, client: httpx.AsyncClient) -> APIResponse:
    """Fetch FDA adverse event data for cosmetic ingredients using FAERS API."""
    cache_key = _cache_key("fda", ingredient)
    cached_data = api_cache.get(cache_key)
    if cached_data:
        return APIResponse(success=True, data=cached_data, source="FDA", cached=True)
    
    async def _fetch():
        await rate_limiters["fda"].acquire()
        
        # Use FAERS API for cosmetic adverse events
        url = f"https://api.fda.gov/drug/event.json?search=patient.drug.medicinalproduct:{ingredient}&limit=10"
        
        resp = await client.get(url, timeout=TIMEOUTS["fda"])
        resp.raise_for_status()
        data = resp.json()
        
        results = data.get('results', [])
        
        if len(results) > 0:
            # Analyze adverse events
            adverse_events = []
            serious_events = 0
            
            for result in results:
                # Extract adverse event information
                if 'patient' in result:
                    patient_data = result['patient']
                    if 'drug' in patient_data:
                        for drug in patient_data['drug']:
                            if 'medicinalproduct' in drug and ingredient.lower() in drug['medicinalproduct'].lower():
                                # Extract adverse reactions
                                if 'reaction' in patient_data:
                                    for reaction in patient_data['reaction']:
                                        adverse_events.append(reaction.get('reactionmeddrapt', 'Unknown reaction'))
                                
                                # Check if serious
                                if drug.get('serious', '').lower() in ['1', 'yes', 'true']:
                                    serious_events += 1
            
            # Determine risk level based on adverse events
            if serious_events > 0:
                risk_level = "riesgo alto"
            elif len(adverse_events) > 5:
                risk_level = "riesgo medio"
            elif len(adverse_events) > 0:
                risk_level = "riesgo bajo"
            else:
                risk_level = "seguro"
            
            # Create detailed risk description
            unique_events = list(set(adverse_events))[:5]  # Top 5 unique events
            risks_detailed = f"Found {len(results)} adverse event reports. Common reactions: {', '.join(unique_events)}"
            if serious_events > 0:
                risks_detailed += f" ({serious_events} serious events)"
        else:
            risk_level = "seguro"
            risks_detailed = "No adverse events reported"
        
        result_data = {
            "risk_level": risk_level,
            "risks_detailed": risks_detailed,
            "sources": "FDA FAERS"
        }
        
        api_cache.set(cache_key, result_data)
        return APIResponse(success=True, data=result_data, source="FDA")
    
    try:
        data = await _fetch()
        return data
    except Exception as e:
        logger.error(f"FDA FAERS API error for {ingredient}: {e}")
        return APIResponse(
            success=False,
            data={"risk_level": "desconocido", "risks_detailed": "No disponible", "sources": ""},
            error=str(e),
            source="FDA"
        )

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
)
async def fetch_cir_data(ingredient: str) -> APIResponse:
    return await _fetch_with_scraper("cir", ingredient, CIRScraper, source_label="CIR")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
)
async def fetch_sccs_data(ingredient: str) -> APIResponse:
    return await _fetch_with_scraper("sccs", ingredient, SCCSScraper, source_label="SCCS")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
)
async def fetch_iccr_data(ingredient: str) -> APIResponse:
    return await _fetch_with_scraper("iccr", ingredient, ICCRScraper, source_label="ICCR")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
)
async def fetch_inci_beauty_data(ingredient: str) -> APIResponse:
    return await _fetch_with_client("inci_beauty", ingredient, INCIClient, source_label="INCI Beauty")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
)
async def fetch_cosing_api_data(ingredient: str) -> APIResponse:
    return await _fetch_with_client(
        "cosing",
        ingredient,
        CosIngClient,
        source_label="CosIng API",
        cache_prefix="cosing_api",
    )

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
)
async def fetch_pubchem_data(ingredient: str, client: httpx.AsyncClient) -> APIResponse:
    """Fetch chemical data from PubChem."""
    cache_key = _cache_key("pubchem", ingredient)
    cached_data = api_cache.get(cache_key)
    if cached_data:
        return APIResponse(success=True, data=cached_data, source="PubChem", cached=True)
    
    async def _fetch():
        await rate_limiters["pubchem"].acquire()
        
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{ingredient}/property/Description/JSON"
        
        resp = await client.get(url, timeout=TIMEOUTS["pubchem"])
        resp.raise_for_status()
        data = await resp.json()
        
        desc = data.get('PropertyTable', {}).get('Properties', [{}])[0].get('Description', '')
        
        result_data = {
            "benefits": desc or "No disponible",
            "risks_detailed": desc or "No disponible",
            "risk_level": "desconocido",
            "sources": "PubChem"
        }
        
        api_cache.set(cache_key, result_data)
        return APIResponse(success=True, data=result_data, source="PubChem")
    
    try:
        data = await circuit_breakers["pubchem"].call(_fetch)
        return data
    except Exception as e:
        logger.error(f"PubChem API error for {ingredient}: {e}")
        return APIResponse(
            success=False,
            data={"benefits": "No disponible", "risks_detailed": "No disponible", "risk_level": "desconocido", "sources": ""},
            error=str(e),
            source="PubChem"
        )

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
)
async def fetch_ewg_data(ingredient: str, client: httpx.AsyncClient) -> APIResponse:
    """Fetch eco and risk data from EWG Skin Deep using web scraping."""
    cache_key = _cache_key("ewg", ingredient)
    cached_data = api_cache.get(cache_key)
    if cached_data:
        return APIResponse(success=True, data=cached_data, source="EWG", cached=True)
    
    async def _fetch():
        await rate_limiters["ewg"].acquire()
        
        # Import the scraper here to avoid circular imports
        from ewg_scraper import EWGScraper
        
        async with EWGScraper() as scraper:
            result = await scraper.get_ingredient_data(ingredient)
            
            if result["success"]:
                api_cache.set(cache_key, result["data"])
                return APIResponse(success=True, data=result["data"], source="EWG")
            else:
                return APIResponse(
                    success=False,
                    data={"eco_score": 50.0, "risks_detailed": "No disponible", "risk_level": "desconocido", "sources": ""},
                    error=result.get("error", "Unknown error"),
                    source="EWG"
                )
    
    try:
        data = await circuit_breakers["ewg"].call(_fetch)
        return data
    except Exception as e:
        logger.error(f"EWG scraping error for {ingredient}: {e}")
        return APIResponse(
            success=False,
            data={"eco_score": 50.0, "risks_detailed": "No disponible", "risk_level": "desconocido", "sources": ""},
            error=str(e),
            source="EWG"
        )

async def fetch_iarc_data(ingredient: str) -> APIResponse:
    """Fetch carcinogen data from IARC via PubMed using PubChem Power User Gateway search terms."""
    cache_key = _cache_key("iarc", ingredient)
    cached_data = api_cache.get(cache_key)
    if cached_data:
        return APIResponse(success=True, data=cached_data, source="IARC", cached=True)
    
    async def _fetch():
        await rate_limiters["iarc"].acquire()
        
        Entrez.email = ENTREZ_EMAIL
        term = f'("{ingredient}"[MeSH Terms] AND "IARC"[All Fields]) AND ("carcinogen"[MeSH Terms] OR "neoplasms"[MeSH Terms])'
        
        handle = Entrez.esearch(db="pubmed", term=term, retmax=5)
        record = Entrez.read(handle)
        handle.close()
        
        if int(record['Count']) > 0:
            result_data = {
                "risk_level": "cancerígeno",
                "risks_detailed": f"Found {record['Count']} PubMed entries indicating carcinogenicity via PubChem Power User Gateway",
                "sources": "IARC"
            }
        else:
            result_data = {
                "risk_level": "seguro",
                "risks_detailed": "No carcinogenicity data found",
                "sources": "IARC"
            }
        
        api_cache.set(cache_key, result_data)
        return APIResponse(success=True, data=result_data, source="IARC")
    
    try:
        data = await circuit_breakers["iarc"].call(_fetch)
        return data
    except Exception as e:
        logger.error(f"IARC/PubMed error for {ingredient}: {e}")
        return APIResponse(
            success=False,
            data={"risk_level": "desconocido", "risks_detailed": "No disponible", "sources": ""},
            error=str(e),
            source="IARC"
        )

async def fetch_invima_data(ingredient: str, client: httpx.AsyncClient) -> APIResponse:
    """Fetch approval status from INVIMA (Colombia) via scraping."""
    cache_key = _cache_key("invima", ingredient)
    cached_data = api_cache.get(cache_key)
    if cached_data:
        return APIResponse(success=True, data=cached_data, source="INVIMA", cached=True)
    
    async def _fetch():
        await rate_limiters["invima"].acquire()
        
        base_url = "https://consultaregistro.invima.gov.co"
        endpoints = [
            f"{base_url}/Consultas/consultas/consreg_buscprod.jsp",
            f"{base_url}/consulta",
            f"{base_url}/buscar"
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; MommyShopsBot/1.0)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8'
        }
        
        for url in endpoints:
            try:
                resp = await client.get(url, headers=headers, timeout=TIMEOUTS["invima"])
                if resp.status_code == 200:
                    payload = {
                        'grupo': 'COSMETICOS',
                        'busqueda': ingredient,
                        'tipo': 'nombre'
                    }
                    
                    post_resp = await client.post(url, data=payload, headers=headers, timeout=TIMEOUTS["invima"])
                    if post_resp.status_code == 200:
                        soup = BeautifulSoup(await post_resp.aread(), 'html.parser')
                        
                        # Look for result indicators
                        result_indicators = [
                            soup.find_all('div', class_='result-item'),
                            soup.find_all('tr', class_='resultado'),
                            soup.find_all('div', class_='resultado'),
                            soup.find('table', class_='resultados')
                        ]
                        
                        approved = False
                        for indicator in result_indicators:
                            if indicator:
                                if isinstance(indicator, list):
                                    approved = any('vigente' in str(r).lower() or 'aprobado' in str(r).lower() for r in indicator)
                                else:
                                    approved = 'vigente' in str(indicator).lower() or 'aprobado' in str(indicator).lower()
                                break
                        
                        if not approved:
                            page_text = (await post_resp.aread()).decode().lower()
                            approved = any(keyword in page_text for keyword in ['vigente', 'activo', 'aprobado', 'registrado'])
                        
                        await asyncio.sleep(1)  # Respect rate limits
                        
                        result_data = {
                            "risk_level": "seguro" if approved else "riesgo medio",
                            "risks_detailed": f"{'Approved' if approved else 'Not approved'} by INVIMA",
                            "sources": "INVIMA"
                        }
                        
                        api_cache.set(cache_key, result_data)
                        return APIResponse(success=True, data=result_data, source="INVIMA")
                                
            except Exception as e:
                logger.warning(f"INVIMA endpoint {url} failed: {e}")
                continue
        
        # If all endpoints fail
        result_data = {
            "risk_level": "desconocido",
            "risks_detailed": "INVIMA not accessible",
            "sources": ""
        }
        
        return APIResponse(success=False, data=result_data, source="INVIMA", error="All endpoints failed")
    
    try:
        data = await circuit_breakers["invima"].call(_fetch)
        return data
    except Exception as e:
        logger.error(f"INVIMA error for {ingredient}: {e}")
        return APIResponse(
            success=False,
            data={"risk_level": "desconocido", "risks_detailed": "No disponible", "sources": ""},
            error=str(e),
            source="INVIMA"
        )

@lru_cache(maxsize=1000)
def fetch_cosing_data(ingredient: str) -> Dict[str, Any]:
    """Fetch data from COSING CSV with caching."""
    try:
        df = pd.read_csv("cosing.csv")
        match = df[df['INCI'].str.lower() == ingredient.lower()]
        
        if not match.empty:
            return {
                "benefits": match['Function'].iloc[0] or "No disponible",
                "risks_detailed": match['Restrictions'].iloc[0] or "No disponible",
                "risk_level": "riesgo medio" if match['Restrictions'].iloc[0] else "seguro",
                "sources": "COSING"
            }
        
        return {
            "benefits": "No disponible",
            "risks_detailed": "No disponible",
            "risk_level": "desconocido",
            "sources": ""
        }
    except Exception as e:
        logger.error(f"COSING CSV error for {ingredient}: {e}")
        return {
            "benefits": "No disponible",
            "risks_detailed": "No disponible",
            "risk_level": "desconocido",
            "sources": ""
        }

def get_default_ingredient_data(ingredient: str) -> Dict[str, Any]:
    """Provide default data for common cosmetic ingredients when APIs fail."""
    ingredient_key = normalize_ingredient_name(ingredient)
    
    # Datos por defecto para ingredientes comunes
    defaults = {
        # Agua y solventes
        "aqua": {"eco_score": 90.0, "risk_level": "seguro", "benefits": "Solvente base para fórmulas cosméticas, hidrata la piel", "risks_detailed": "Generalmente considerado seguro", "sources": "Default"},
        "water": {"eco_score": 90.0, "risk_level": "seguro", "benefits": "Solvente base para fórmulas cosméticas, hidrata la piel", "risks_detailed": "Generalmente considerado seguro", "sources": "Default"},
        
        # Filtros UV
        "octocrylene": {"eco_score": 40.0, "risk_level": "riesgo medio", "benefits": "Absorbe rayos UVB/UVA, protege contra quemaduras solares", "risks_detailed": "Posible irritante ocular y disruptor endocrino; tóxico para corales", "sources": "Default"},
        "butyl methoxydibenzoylmethane": {"eco_score": 35.0, "risk_level": "riesgo medio", "benefits": "Filtro UV de amplio espectro", "risks_detailed": "Puede causar reacciones alérgicas en piel sensible", "sources": "Default"},
        "ethylhexyl salicylate": {"eco_score": 45.0, "risk_level": "riesgo bajo", "benefits": "Filtro UVB, protege contra quemaduras solares", "risks_detailed": "Generalmente seguro, puede causar irritación leve", "sources": "Default"},
        
        # Siliconas
        "dimethicone": {"eco_score": 60.0, "risk_level": "seguro", "benefits": "Suavizante, mejora la textura y sensación de la piel", "risks_detailed": "Generalmente considerado seguro", "sources": "Default"},
        "polysilicone-15": {"eco_score": 55.0, "risk_level": "seguro", "benefits": "Agente de textura, mejora la aplicación del producto", "risks_detailed": "Generalmente considerado seguro", "sources": "Default"},
        
        # Conservantes
        "parfum": {"eco_score": 30.0, "risk_level": "riesgo bajo", "benefits": "Proporciona aroma agradable al producto", "risks_detailed": "Puede causar alergias o irritación en piel sensible", "sources": "Default"},
        "fragrance": {"eco_score": 30.0, "risk_level": "riesgo bajo", "benefits": "Proporciona aroma agradable al producto", "risks_detailed": "Puede causar alergias o irritación en piel sensible", "sources": "Default"},
        
        # Vitaminas y antioxidantes
        "tocopherol": {"eco_score": 80.0, "risk_level": "seguro", "benefits": "Antioxidante, protege contra radicales libres", "risks_detailed": "Generalmente considerado seguro", "sources": "Default"},
        "ascorbic acid": {"eco_score": 85.0, "risk_level": "seguro", "benefits": "Vitamina C, antioxidante, ilumina la piel", "risks_detailed": "Generalmente seguro, puede causar irritación en altas concentraciones", "sources": "Default"},
        "citric acid": {"eco_score": 80.0, "risk_level": "seguro", "benefits": "Ajusta pH, exfoliante suave", "risks_detailed": "Bajo riesgo, puede irritar en altas concentraciones", "sources": "Default"},
        
        # Emolientes
        "propylene glycol": {"eco_score": 50.0, "risk_level": "riesgo bajo", "benefits": "Hidratante, mejora la penetración de otros ingredientes", "risks_detailed": "Generalmente seguro, puede causar irritación en piel sensible", "sources": "Default"},
        "glycerin": {"eco_score": 85.0, "risk_level": "seguro", "benefits": "Hidratante natural, atrae humedad a la piel", "risks_detailed": "Generalmente considerado seguro", "sources": "Default"},
        
        # Espesantes
        "xanthan gum": {"eco_score": 90.0, "risk_level": "seguro", "benefits": "Espesante natural, mejora la textura del producto", "risks_detailed": "Generalmente considerado seguro", "sources": "Default"},
        "polysorbate 60": {"eco_score": 60.0, "risk_level": "riesgo bajo", "benefits": "Emulsificante, ayuda a mezclar ingredientes", "risks_detailed": "Generalmente seguro", "sources": "Default"},
        
        # Ingredientes adicionales comunes
        "silica": {"eco_score": 70.0, "risk_level": "seguro", "benefits": "Absorbente, mejora la textura del producto", "risks_detailed": "Generalmente considerado seguro", "sources": "Default"},
        "disodium edta": {"eco_score": 60.0, "risk_level": "riesgo bajo", "benefits": "Quelante, estabiliza la fórmula", "risks_detailed": "Generalmente seguro, puede causar irritación leve", "sources": "Default"},
        "polymethyl methacrylate": {"eco_score": 40.0, "risk_level": "riesgo medio", "benefits": "Agente de textura, mejora la aplicación", "risks_detailed": "Puede causar irritación en piel sensible", "sources": "Default"},
        "phenylbenzimidazole sulfonic acid": {"eco_score": 45.0, "risk_level": "riesgo bajo", "benefits": "Filtro UV, protege contra rayos UVA", "risks_detailed": "Generalmente seguro, puede causar irritación leve", "sources": "Default"},
        "hydroxyacetophenone": {"eco_score": 70.0, "risk_level": "seguro", "benefits": "Conservante suave, protege la fórmula", "risks_detailed": "Generalmente considerado seguro", "sources": "Default"},
        "caprylyl glycol": {"eco_score": 75.0, "risk_level": "seguro", "benefits": "Conservante natural, hidratante", "risks_detailed": "Generalmente considerado seguro", "sources": "Default"},
        "peg-8": {"eco_score": 50.0, "risk_level": "riesgo bajo", "benefits": "Emulsificante, mejora la penetración", "risks_detailed": "Generalmente seguro", "sources": "Default"},
        "peg-10 dimethicone": {"eco_score": 55.0, "risk_level": "riesgo bajo", "benefits": "Suavizante, mejora la textura", "risks_detailed": "Generalmente seguro", "sources": "Default"},
        "sodium hyaluronate": {"eco_score": 90.0, "risk_level": "seguro", "benefits": "Hidratante potente, reduce arrugas", "risks_detailed": "Generalmente considerado seguro", "sources": "Default"},
        "ascorbyl palmitate": {"eco_score": 80.0, "risk_level": "seguro", "benefits": "Vitamina C estabilizada, antioxidante", "risks_detailed": "Generalmente considerado seguro", "sources": "Default"},
        "tropolone": {"eco_score": 60.0, "risk_level": "riesgo bajo", "benefits": "Conservante, protege la fórmula", "risks_detailed": "Generalmente seguro", "sources": "Default"},
        "bis-ethylhexyloxyphenol methoxyphenyl triazine": {"eco_score": 40.0, "risk_level": "riesgo medio", "benefits": "Filtro UV de amplio espectro", "risks_detailed": "Puede causar reacciones alérgicas", "sources": "Default"},
        "2-hexanediol": {"eco_score": 70.0, "risk_level": "seguro", "benefits": "Conservante suave, hidratante", "risks_detailed": "Generalmente considerado seguro", "sources": "Default"},
        "1,2-hexanediol": {"eco_score": 70.0, "risk_level": "seguro", "benefits": "Conservante suave, hidratante", "risks_detailed": "Generalmente considerado seguro", "sources": "Default"},
        "propanediol": {"eco_score": 85.0, "risk_level": "seguro", "benefits": "Humectante natural, mejora absorción de ingredientes activos", "risks_detailed": "Bajo riesgo, biodegradable, considerado seguro para piel sensible", "sources": "Default"},
        "propanediol ": {"eco_score": 85.0, "risk_level": "seguro", "benefits": "Humectante natural, mejora absorción de ingredientes activos", "risks_detailed": "Bajo riesgo, biodegradable, considerado seguro para piel sensible", "sources": "Default"},
    }
    
    # Buscar coincidencia exacta o parcial
    for key, data in defaults.items():
        normalized_key = normalize_ingredient_name(key)
        if normalized_key and normalized_key in ingredient_key:
            return data
    
    # Datos por defecto genéricos
    return {
        "eco_score": 50.0,
        "risk_level": "desconocido",
        "benefits": "No disponible",
        "risks_detailed": "No disponible",
        "sources": "Default"
    }

async def fetch_ingredient_data(ingredient: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Aggregate data from all APIs for an ingredient with production-grade error handling."""
    from database import get_ingredient_data  # local import to avoid circular dependency

    normalized_name = _normalize_ingredient_name(ingredient)
    local_data = get_ingredient_data(ingredient)
    if local_data:
        logger.info(
            "Local ingredient record found",
            extra={"ingredient": normalized_name or ingredient, "source": "local"},
        )
    else:
        logger.info(
            "Fetching ingredient from external providers",
            extra={"ingredient": normalized_name or ingredient, "source": "external"},
        )

    provider_specs: List[Tuple[str, Callable[[], Awaitable[APIResponse]]]] = [
        ("FDA", lambda: retry_with_backoff(lambda: fetch_fda_data(ingredient, client))),
        ("PubChem", lambda: retry_with_backoff(lambda: fetch_pubchem_data(ingredient, client))),
        ("EWG", lambda: retry_with_backoff(lambda: fetch_ewg_data(ingredient, client))),
        ("IARC", lambda: retry_with_backoff(lambda: fetch_iarc_data(ingredient))),
        ("INVIMA", lambda: retry_with_backoff(lambda: fetch_invima_data(ingredient, client))),
        ("CIR", lambda: retry_with_backoff(lambda: fetch_cir_data(ingredient))),
        ("SCCS", lambda: retry_with_backoff(lambda: fetch_sccs_data(ingredient))),
        ("ICCR", lambda: retry_with_backoff(lambda: fetch_iccr_data(ingredient))),
        ("INCI Beauty", lambda: retry_with_backoff(lambda: fetch_inci_beauty_data(ingredient))),
        ("CosIng API", lambda: retry_with_backoff(lambda: fetch_cosing_api_data(ingredient))),
    ]

    coroutines = [factory() for _, factory in provider_specs]
    raw_results = await asyncio.gather(*coroutines, return_exceptions=True)

    responses: Dict[str, APIResponse] = {}
    failed_details: Dict[str, str] = {}

    for (provider, _), outcome in zip(provider_specs, raw_results):
        if isinstance(outcome, Exception):
            error_message = str(outcome)
            responses[provider] = APIResponse(
                success=False,
                data=_build_default_payload(provider),
                error=error_message,
                source=provider,
            )
            failed_details[provider] = error_message
            logger.error(
                "Provider call raised exception",
                extra={"provider": provider, "ingredient": normalized_name or ingredient, "error": error_message},
            )
            continue

        if not isinstance(outcome, APIResponse):
            error_message = "Unexpected response type"
            responses[provider] = APIResponse(
                success=False,
                data=_build_default_payload(provider),
                error=error_message,
                source=provider,
            )
            failed_details[provider] = error_message
            logger.error(
                "Provider returned unexpected payload",
                extra={"provider": provider, "ingredient": normalized_name or ingredient},
            )
            continue

        responses[provider] = outcome
        if not outcome.success and outcome.error:
            failed_details[provider] = outcome.error

    cosing_csv_payload = fetch_cosing_data(ingredient)
    responses["CosIng CSV"] = APIResponse(
        success=True,
        data=cosing_csv_payload,
        source="CosIng CSV",
    )

    successful_providers = [name for name, resp in responses.items() if resp.success]
    logger.info(
        "API call summary",
        extra={
            "ingredient": normalized_name or ingredient,
            "successful": successful_providers,
            "failed": failed_details,
        },
    )

    default_data = get_default_ingredient_data(ingredient)

    eco_value = _first_non_placeholder(responses, ["EWG"], "eco_score")
    if eco_value is None:
        eco_value = default_data.get("eco_score", 50.0)
    try:
        eco_score = float(eco_value)
    except (TypeError, ValueError):
        eco_score = float(default_data.get("eco_score", 50.0))
    eco_score = max(0.0, min(100.0, eco_score))

    risk_level = _first_non_placeholder(responses, RISK_PRIORITY_ORDER, "risk_level")
    if not risk_level:
        risk_level = default_data.get("risk_level", "desconocido")

    benefits_value = _first_non_placeholder(responses, BENEFITS_PRIORITY_ORDER, "benefits")
    risks_value = _first_non_placeholder(responses, RISK_DETAILS_PRIORITY_ORDER, "risks_detailed")

    benefits = _normalize_text_field(benefits_value, default_data.get("benefits", "No disponible"))
    risks_detailed = _normalize_text_field(risks_value, default_data.get("risks_detailed", "No disponible"))

    sources = _merge_sources(
        *(resp.data.get("sources") for resp in responses.values()),
        default_data.get("sources"),
    )

    canonical_name = (local_data or {}).get("name") or ingredient

    api_result = {
        "name": canonical_name,
        "eco_score": eco_score,
        "risk_level": risk_level,
        "benefits": benefits,
        "risks_detailed": risks_detailed,
        "sources": sources,
    }

    if local_data:
        combined = {
            "name": canonical_name,
            "eco_score": default_data.get("eco_score", 50.0),
            "risk_level": default_data.get("risk_level", "desconocido"),
            "benefits": default_data.get("benefits", "No disponible"),
            "risks_detailed": default_data.get("risks_detailed", "No disponible"),
            "sources": default_data.get("sources", "Default"),
        }
        combined.update({k: v for k, v in local_data.items() if v is not None})
        combined.update(api_result)
        combined["sources"] = _merge_sources(
            combined.get("sources"),
            local_data.get("sources"),
            api_result.get("sources"),
        )
        return combined

    return api_result

async def health_check() -> Dict[str, Any]:
    """Health check for all APIs."""
    health_status = {}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test FDA FAERS
        try:
            resp = await client.get("https://api.fda.gov/drug/event.json?limit=1")
            health_status["fda"] = {"status": "healthy", "response_time": resp.elapsed.total_seconds(), "api": "FAERS"}
        except Exception as e:
            health_status["fda"] = {"status": "unhealthy", "error": str(e)}
        
        # Test PubChem
        try:
            resp = await client.get("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/water/property/Description/JSON")
            health_status["pubchem"] = {"status": "healthy", "response_time": resp.elapsed.total_seconds()}
        except Exception as e:
            health_status["pubchem"] = {"status": "unhealthy", "error": str(e)}
        
        # Test EWG (web scraping)
        try:
            from ewg_scraper import EWGScraper
            async with EWGScraper() as scraper:
                result = await scraper.get_ingredient_data("water")
                health_status["ewg"] = {"status": "healthy", "method": "web_scraping"}
        except Exception as e:
            health_status["ewg"] = {"status": "unhealthy", "error": str(e)}
        
        # Test INVIMA
        try:
            resp = await client.get("https://consultaregistro.invima.gov.co")
            health_status["invima"] = {"status": "healthy", "response_time": resp.elapsed.total_seconds()}
        except Exception as e:
            health_status["invima"] = {"status": "unhealthy", "error": str(e)}
    
    return health_status

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    stats = api_cache.stats()
    stats["cache_keys"] = api_cache.keys()
    return stats

def clear_cache():
    """Clear API cache."""
    api_cache.clear()
    logger.info("API cache cleared")

# Apify integration for web scraping
async def fetch_apify_data(url: str) -> dict:
    """Use Apify Web Scraper to extract product information."""
    try:
        from apify_client import ApifyClient
        
        client = ApifyClient(APIFY_API_KEY)
        
        # Use Apify Web Scraper actor
        run = client.actor("apify/web-scraper").call(
            run_input={
                "startUrls": [{"url": url}],
                "maxCrawlDepth": 1,
                "maxCrawlPages": 1,
                "extendOutputFunction": r"""
                async ({ data, item, helpers, page, customData, label }) => {
                    const $ = helpers.$;
                    
                    // Extract ingredients from various patterns
                    let ingredients = [];
                    
                    // Look for ingredients in different sections
                    const ingredientSections = [
                        'composition', 'ingredients', 'ingredientes', 'componentes',
                        'product details', 'product information'
                    ];
                    
                    ingredientSections.forEach(section => {
                        const elements = $(`*:contains("${section}")`).nextAll();
                        elements.each((i, el) => {
                            const text = $(el).text().toLowerCase();
                            if (text.includes('aqua') || text.includes('water') || text.includes('octocrylene')) {
                                const ingredientList = text.split(/[,;]/).map(ing => ing.trim()).filter(ing => 
                                    ing.length > 2 && 
                                    !ing.match(/^(ingredients?|composition|ingredientes?|componentes?)$/i) &&
                                    !ing.match(/^(contact|about|company|navigation|follow|policy|cookies)$/i)
                                );
                                ingredients = ingredients.concat(ingredientList);
                            }
                        });
                    });
                    
                    // Remove duplicates and clean
                    ingredients = [...new Set(ingredients)].map(ing => 
                        ing.toLowerCase().replace(/[^\w\s\/\-()]/g, '').trim()
                    ).filter(ing => ing.length > 2);
                    
                    return {
                        url: data.url,
                        title: $('title').text(),
                        ingredients: ingredients,
                        rawText: $('body').text().substring(0, 5000)
                    };
                }
                """
            }
        )
        
        # Get the results
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        
        if items:
            item = items[0]
            logger.info(f"Apify extracted {len(item.get('ingredients', []))} ingredients from {url}")
            return {
                "success": True,
                "ingredients": item.get('ingredients', []),
                "title": item.get('title', ''),
                "raw_text": item.get('rawText', ''),
                "source": "Apify"
            }
        else:
            logger.warning(f"No data extracted by Apify from {url}")
            return {
                "success": False,
                "ingredients": [],
                "error": "No data extracted"
            }
            
    except Exception as e:
        logger.error(f"Apify error for {url}: {e}")
        return {
            "success": False,
            "ingredients": [],
            "error": str(e)
        }


async def enhance_ingredient_analysis_with_ollama(ingredient_data: Dict[str, Any], skin_type: str = "normal") -> Dict[str, Any]:
    """
    Enhance ingredient analysis using Ollama AI for better safety assessment and recommendations
    
    Args:
        ingredient_data: Dictionary containing ingredient information
        skin_type: User's skin type for personalized analysis
        
    Returns:
        Enhanced ingredient data with Ollama analysis
    """
    if not OLLAMA_AVAILABLE or not ollama_integration.is_available():
        logger.warning("Ollama not available for enhanced analysis")
        return ingredient_data
    
    try:
        # Extract ingredient names for analysis
        ingredients = []
        if isinstance(ingredient_data.get('ingredients'), list):
            ingredients = ingredient_data['ingredients']
        elif isinstance(ingredient_data.get('ingredients'), str):
            ingredients = [ingredient_data['ingredients']]
        
        if not ingredients:
            logger.warning("No ingredients found for Ollama analysis")
            return ingredient_data
        
        # Get enhanced safety analysis from Ollama
        ollama_result = await analyze_ingredient_safety_with_ollama(ingredients, skin_type)
        
        if ollama_result.success and ollama_result.content:
            # Add Ollama analysis to the ingredient data
            enhanced_data = ingredient_data.copy()
            enhanced_data['ollama_analysis'] = {
                'content': ollama_result.content,
                'model': ollama_result.model,
                'skin_type': skin_type,
                'timestamp': time.time()
            }
            
            # Try to extract safety score from Ollama response
            safety_score = extract_safety_score_from_ollama(ollama_result.content)
            if safety_score:
                enhanced_data['ollama_safety_score'] = safety_score
            
            logger.info(f"Enhanced analysis completed for {len(ingredients)} ingredients")
            return enhanced_data
        else:
            logger.warning(f"Ollama analysis failed: {ollama_result.error}")
            return ingredient_data
            
    except Exception as e:
        logger.error(f"Error enhancing analysis with Ollama: {e}")
        return ingredient_data


def extract_safety_score_from_ollama(content: str) -> Optional[float]:
    """
    Extract safety score from Ollama response content
    
    Args:
        content: Ollama response content
        
    Returns:
        Safety score if found, None otherwise
    """
    try:
        # Look for patterns like "8/10", "Score: 8", "Safety Score: 8.5", etc.
        import re
        
        # Pattern 1: X/Y format (e.g., "8/10")
        pattern1 = r'(\d+(?:\.\d+)?)\s*/\s*10'
        match1 = re.search(pattern1, content, re.IGNORECASE)
        if match1:
            return float(match1.group(1))
        
        # Pattern 2: "Score: X" format
        pattern2 = r'(?:safety\s+)?score\s*:?\s*(\d+(?:\.\d+)?)'
        match2 = re.search(pattern2, content, re.IGNORECASE)
        if match2:
            return float(match2.group(1))
        
        # Pattern 3: "X out of 10" format
        pattern3 = r'(\d+(?:\.\d+)?)\s+out\s+of\s+10'
        match3 = re.search(pattern3, content, re.IGNORECASE)
        if match3:
            return float(match3.group(1))
        
        return None
        
    except Exception as e:
        logger.warning(f"Error extracting safety score: {e}")
        return None


async def enhance_ocr_with_ollama(ocr_text: str) -> Optional[str]:
    """
    Enhance OCR text using Ollama for better ingredient extraction
    
    Args:
        ocr_text: Raw OCR text from image processing
        
    Returns:
        Enhanced OCR text or None if Ollama is not available
    """
    if not OLLAMA_AVAILABLE or not ollama_integration.is_available():
        logger.warning("Ollama not available for OCR enhancement")
        return None
    
    try:
        ollama_result = await enhance_ocr_text_with_ollama(ocr_text)
        
        if ollama_result.success and ollama_result.content:
            logger.info("OCR text enhanced with Ollama")
            return ollama_result.content
        else:
            logger.warning(f"OCR enhancement failed: {ollama_result.error}")
            return None
            
    except Exception as e:
        logger.error(f"Error enhancing OCR with Ollama: {e}")
        return None


async def get_comprehensive_ingredient_analysis(ingredients: List[str], skin_type: str = "normal") -> Dict[str, Any]:
    """
    Get comprehensive ingredient analysis combining traditional APIs with Ollama AI
    
    Args:
        ingredients: List of ingredient names
        skin_type: User's skin type
        
    Returns:
        Comprehensive analysis results
    """
    try:
        # Get traditional API data
        traditional_data = await fetch_ingredient_data(ingredients[0] if ingredients else "")
        
        # Enhance with Ollama analysis
        enhanced_data = await enhance_ingredient_analysis_with_ollama(traditional_data, skin_type)
        
        # Add metadata
        enhanced_data['analysis_metadata'] = {
            'ingredients_analyzed': len(ingredients),
            'skin_type': skin_type,
            'ollama_enhanced': OLLAMA_AVAILABLE and ollama_integration.is_available(),
            'timestamp': time.time()
        }
        
        return enhanced_data
        
    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {e}")
        return {
            'success': False,
            'error': str(e),
            'ingredients': ingredients
        }