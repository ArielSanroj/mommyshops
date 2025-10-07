"""
Production-ready API utilities for MommyShops MVP
"""
import asyncio
import httpx
import pandas as pd
from Bio import Entrez
import ssl
from bs4 import BeautifulSoup
import logging
import os
import time
from typing import Dict, List, Optional, Any, Tuple
import urllib.request
from dataclasses import dataclass
from functools import lru_cache
import json
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Import scrapers and APIs
from ewg_scraper import EWGScraper
from cir_scraper import CIRScraper
from sccs_scraper import SCCSScraper
from iccr_scraper import ICCRScraper
from inci_beauty_api import INCIClient
from cosing_api_store import CosIngClient

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

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
    """Simple in-memory cache for API responses."""
    
    def __init__(self, ttl: int = 3600):  # 1 hour TTL
        self.cache = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached response."""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return data
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, data: Dict):
        """Cache response."""
        self.cache[key] = (data, time.time())
    
    def clear(self):
        """Clear cache."""
        self.cache.clear()

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
    cache_key = f"fda:{ingredient}"
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
    """Fetch cosmetic ingredient safety data from CIR using web scraping."""
    cache_key = f"cir:{ingredient}"
    cached_data = api_cache.get(cache_key)
    if cached_data:
        return APIResponse(success=True, data=cached_data, source="CIR", cached=True)
    
    async def _fetch():
        await rate_limiters["cir"].acquire()
        
        async with CIRScraper() as scraper:
            result = await scraper.get_ingredient_data(ingredient)
            
            if result["success"]:
                api_cache.set(cache_key, result["data"])
                return APIResponse(success=True, data=result["data"], source="CIR")
            else:
                return APIResponse(
                    success=False,
                    data={"benefits": "No disponible", "risks_detailed": "No disponible", "risk_level": "desconocido", "sources": ""},
                    error=result.get("error", "Unknown error"),
                    source="CIR"
                )
    
    try:
        data = await circuit_breakers["cir"].call(_fetch)
        return data
    except Exception as e:
        logger.error(f"CIR scraping error for {ingredient}: {e}")
        return APIResponse(
            success=False,
            data={"benefits": "No disponible", "risks_detailed": "No disponible", "risk_level": "desconocido", "sources": ""},
            error=str(e),
            source="CIR"
        )

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
)
async def fetch_sccs_data(ingredient: str) -> APIResponse:
    """Fetch cosmetic ingredient safety data from SCCS using web scraping."""
    cache_key = f"sccs:{ingredient}"
    cached_data = api_cache.get(cache_key)
    if cached_data:
        return APIResponse(success=True, data=cached_data, source="SCCS", cached=True)
    
    async def _fetch():
        await rate_limiters["sccs"].acquire()
        
        async with SCCSScraper() as scraper:
            result = await scraper.get_ingredient_data(ingredient)
            
            if result["success"]:
                api_cache.set(cache_key, result["data"])
                return APIResponse(success=True, data=result["data"], source="SCCS")
            else:
                return APIResponse(
                    success=False,
                    data={"benefits": "No disponible", "risks_detailed": "No disponible", "risk_level": "desconocido", "sources": ""},
                    error=result.get("error", "Unknown error"),
                    source="SCCS"
                )
    
    try:
        data = await circuit_breakers["sccs"].call(_fetch)
        return data
    except Exception as e:
        logger.error(f"SCCS scraping error for {ingredient}: {e}")
        return APIResponse(
            success=False,
            data={"benefits": "No disponible", "risks_detailed": "No disponible", "risk_level": "desconocido", "sources": ""},
            error=str(e),
            source="SCCS"
        )

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
)
async def fetch_iccr_data(ingredient: str) -> APIResponse:
    """Fetch cosmetic ingredient safety data from ICCR using web scraping."""
    cache_key = f"iccr:{ingredient}"
    cached_data = api_cache.get(cache_key)
    if cached_data:
        return APIResponse(success=True, data=cached_data, source="ICCR", cached=True)
    
    async def _fetch():
        await rate_limiters["iccr"].acquire()
        
        async with ICCRScraper() as scraper:
            result = await scraper.get_ingredient_data(ingredient)
            
            if result["success"]:
                api_cache.set(cache_key, result["data"])
                return APIResponse(success=True, data=result["data"], source="ICCR")
            else:
                return APIResponse(
                    success=False,
                    data={"benefits": "No disponible", "risks_detailed": "No disponible", "risk_level": "desconocido", "sources": ""},
                    error=result.get("error", "Unknown error"),
                    source="ICCR"
                )
    
    try:
        data = await circuit_breakers["iccr"].call(_fetch)
        return data
    except Exception as e:
        logger.error(f"ICCR scraping error for {ingredient}: {e}")
        return APIResponse(
            success=False,
            data={"benefits": "No disponible", "risks_detailed": "No disponible", "risk_level": "desconocido", "sources": ""},
            error=str(e),
            source="ICCR"
        )

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
)
async def fetch_inci_beauty_data(ingredient: str) -> APIResponse:
    """Fetch ingredient data from INCI Beauty Pro API."""
    cache_key = f"inci_beauty:{ingredient}"
    cached_data = api_cache.get(cache_key)
    if cached_data:
        return APIResponse(success=True, data=cached_data, source="INCI Beauty", cached=True)
    
    async def _fetch():
        await rate_limiters["inci_beauty"].acquire()
        
        async with INCIClient() as client:
            result = await client.get_ingredient_data(ingredient)
            
            if result.success:
                api_cache.set(cache_key, result.data)
                return APIResponse(success=True, data=result.data, source="INCI Beauty")
            else:
                return APIResponse(
                    success=False,
                    data={"benefits": "No disponible", "risks_detailed": "No disponible", "risk_level": "desconocido", "sources": ""},
                    error=result.error,
                    source="INCI Beauty"
                )
    
    try:
        data = await circuit_breakers["inci_beauty"].call(_fetch)
        return data
    except Exception as e:
        logger.error(f"INCI Beauty API error for {ingredient}: {e}")
        return APIResponse(
            success=False,
            data={"benefits": "No disponible", "risks_detailed": "No disponible", "risk_level": "desconocido", "sources": ""},
            error=str(e),
            source="INCI Beauty"
        )

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
)
async def fetch_cosing_api_data(ingredient: str) -> APIResponse:
    """Fetch ingredient data from CosIng API Store."""
    cache_key = f"cosing_api:{ingredient}"
    cached_data = api_cache.get(cache_key)
    if cached_data:
        return APIResponse(success=True, data=cached_data, source="CosIng API", cached=True)
    
    async def _fetch():
        await rate_limiters["cosing"].acquire()
        
        async with CosIngClient() as client:
            result = await client.get_ingredient_data(ingredient)
            
            if result.success:
                api_cache.set(cache_key, result.data)
                return APIResponse(success=True, data=result.data, source="CosIng API")
            else:
                return APIResponse(
                    success=False,
                    data={"benefits": "No disponible", "risks_detailed": "No disponible", "risk_level": "desconocido", "sources": ""},
                    error=result.error,
                    source="CosIng API"
                )
    
    try:
        data = await circuit_breakers["cosing"].call(_fetch)
        return data
    except Exception as e:
        logger.error(f"CosIng API error for {ingredient}: {e}")
        return APIResponse(
            success=False,
            data={"benefits": "No disponible", "risks_detailed": "No disponible", "risk_level": "desconocido", "sources": ""},
            error=str(e),
            source="CosIng API"
        )

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
)
async def fetch_pubchem_data(ingredient: str, client: httpx.AsyncClient) -> APIResponse:
    """Fetch chemical data from PubChem."""
    cache_key = f"pubchem:{ingredient}"
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
    cache_key = f"ewg:{ingredient}"
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
    cache_key = f"iarc:{ingredient}"
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
    cache_key = f"invima:{ingredient}"
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
    ingredient_lower = ingredient.lower()
    
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
        if key in ingredient_lower:
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
    from database import get_ingredient_data
    
    local_data = get_ingredient_data(ingredient)
    if local_data:
        logger.info(f"Found {ingredient} in local database; enriching with external APIs")
    else:
        logger.info(f"Fetching {ingredient} from external APIs...")
    
    # Run API calls in parallel with retry logic
    tasks = [
        retry_with_backoff(lambda: fetch_fda_data(ingredient, client)),
        retry_with_backoff(lambda: fetch_pubchem_data(ingredient, client)),
        retry_with_backoff(lambda: fetch_ewg_data(ingredient, client)),
        retry_with_backoff(lambda: fetch_iarc_data(ingredient)),
        retry_with_backoff(lambda: fetch_invima_data(ingredient, client)),
        retry_with_backoff(lambda: fetch_cir_data(ingredient)),
        retry_with_backoff(lambda: fetch_sccs_data(ingredient)),
        retry_with_backoff(lambda: fetch_iccr_data(ingredient)),
        retry_with_backoff(lambda: fetch_inci_beauty_data(ingredient)),
        retry_with_backoff(lambda: fetch_cosing_api_data(ingredient)),
    ]
    
    # Run parallel tasks
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    fda_data = results[0] if not isinstance(results[0], Exception) else APIResponse(success=False, data={}, error=str(results[0]), source="FDA")
    pubchem_data = results[1] if not isinstance(results[1], Exception) else APIResponse(success=False, data={}, error=str(results[1]), source="PubChem")
    ewg_data = results[2] if not isinstance(results[2], Exception) else APIResponse(success=False, data={}, error=str(results[2]), source="EWG")
    iarc_data = results[3] if not isinstance(results[3], Exception) else APIResponse(success=False, data={}, error=str(results[3]), source="IARC")
    invima_data = results[4] if not isinstance(results[4], Exception) else APIResponse(success=False, data={}, error=str(results[4]), source="INVIMA")
    cir_data = results[5] if not isinstance(results[5], Exception) else APIResponse(success=False, data={}, error=str(results[5]), source="CIR")
    sccs_data = results[6] if not isinstance(results[6], Exception) else APIResponse(success=False, data={}, error=str(results[6]), source="SCCS")
    iccr_data = results[7] if not isinstance(results[7], Exception) else APIResponse(success=False, data={}, error=str(results[7]), source="ICCR")
    inci_beauty_data = results[8] if not isinstance(results[8], Exception) else APIResponse(success=False, data={}, error=str(results[8]), source="INCI Beauty")
    cosing_api_data = results[9] if not isinstance(results[9], Exception) else APIResponse(success=False, data={}, error=str(results[9]), source="CosIng API")
    
    # COSING is synchronous, so call it separately
    cosing_data = fetch_cosing_data(ingredient)

    # Prioritize risk_level: IARC > FDA > CIR > SCCS > INVIMA > EWG > ICCR > INCI Beauty > CosIng API > default
    risk_level = (
        iarc_data.data.get("risk_level", "desconocido") if iarc_data.data.get("risk_level") != "desconocido" else
        fda_data.data.get("risk_level", "desconocido") if fda_data.data.get("risk_level") != "desconocido" else
        cir_data.data.get("risk_level", "desconocido") if cir_data.data.get("risk_level") != "desconocido" else
        sccs_data.data.get("risk_level", "desconocido") if sccs_data.data.get("risk_level") != "desconocido" else
        invima_data.data.get("risk_level", "desconocido") if invima_data.data.get("risk_level") != "desconocido" else
        ewg_data.data.get("risk_level", "desconocido") if ewg_data.data.get("risk_level") != "desconocido" else
        iccr_data.data.get("risk_level", "desconocido") if iccr_data.data.get("risk_level") != "desconocido" else
        inci_beauty_data.data.get("risk_level", "desconocido") if inci_beauty_data.data.get("risk_level") != "desconocido" else
        cosing_api_data.data.get("risk_level", "desconocido") if cosing_api_data.data.get("risk_level") != "desconocido" else
        cosing_data.get("risk_level", "desconocido")
    )

    # Combine sources
    sources = ",".join(filter(None, [
        fda_data.data.get("sources", ""),
        pubchem_data.data.get("sources", ""),
        ewg_data.data.get("sources", ""),
        iarc_data.data.get("sources", ""),
        invima_data.data.get("sources", ""),
        cir_data.data.get("sources", ""),
        sccs_data.data.get("sources", ""),
        iccr_data.data.get("sources", ""),
        inci_beauty_data.data.get("sources", ""),
        cosing_api_data.data.get("sources", ""),
        cosing_data.get("sources", "")
    ]))

    # Log API performance
    successful_apis = [r.source for r in [fda_data, pubchem_data, ewg_data, iarc_data, invima_data, cir_data, sccs_data, iccr_data, inci_beauty_data, cosing_api_data] if r.success]
    failed_apis = [r.source for r in [fda_data, pubchem_data, ewg_data, iarc_data, invima_data, cir_data, sccs_data, iccr_data, inci_beauty_data, cosing_api_data] if not r.success]
    
    logger.info(f"API calls for {ingredient}: Success={successful_apis}, Failed={failed_apis}")

    # Proporcionar datos por defecto más útiles basados en el tipo de ingrediente
    default_data = get_default_ingredient_data(ingredient)
    
    api_result = {
        "name": ingredient,
        "eco_score": ewg_data.data.get("eco_score", default_data["eco_score"]),
        "risk_level": risk_level if risk_level != "desconocido" else default_data["risk_level"],
        "benefits": (
            inci_beauty_data.data.get("benefits") or
            cir_data.data.get("benefits") or
            sccs_data.data.get("benefits") or
            cosing_api_data.data.get("benefits") or
            pubchem_data.data.get("benefits") or 
            cosing_data.get("benefits") or 
            default_data["benefits"]
        ),
        "risks_detailed": (
            iarc_data.data.get("risks_detailed") or
            fda_data.data.get("risks_detailed") or
            cir_data.data.get("risks_detailed") or
            sccs_data.data.get("risks_detailed") or
            ewg_data.data.get("risks_detailed") or
            invima_data.data.get("risks_detailed") or
            iccr_data.data.get("risks_detailed") or
            inci_beauty_data.data.get("risks_detailed") or
            cosing_api_data.data.get("risks_detailed") or
            cosing_data.get("risks_detailed") or
            default_data["risks_detailed"]
        ),
        "sources": sources or default_data["sources"]
    }

    if local_data:
        combined = {
            "name": ingredient,
            "eco_score": default_data["eco_score"],
            "risk_level": default_data["risk_level"],
            "benefits": default_data["benefits"],
            "risks_detailed": default_data["risks_detailed"],
            "sources": default_data["sources"]
        }
        combined.update({k: v for k, v in local_data.items() if v is not None})
        combined.update({k: v for k, v in api_result.items() if v is not None})

        source_candidates = [combined.get("sources"), local_data.get("sources"), api_result.get("sources")]
        sources_clean = [src.strip() for src in source_candidates if src]
        if sources_clean:
            combined["sources"] = ",".join(dict.fromkeys(sources_clean))
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
    return {
        "cache_size": len(api_cache.cache),
        "cache_keys": list(api_cache.cache.keys())
    }

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
                "extendOutputFunction": """
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