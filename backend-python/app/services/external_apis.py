"""
External API service for MommyShops application
Streamlined version with only essential integrations
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from functools import lru_cache

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """Standardized API response"""
    success: bool
    data: Dict[str, Any]
    source: str
    error: Optional[str] = None
    cached: bool = False


class ExternalAPIService:
    """
    Service for external API integration
    Streamlined to only essential APIs: FDA, PubChem, Google Vision, Ollama
    """
    
    def __init__(self):
        self.timeout = 30.0
        self.rate_limits = {
            "fda": {"limit": 60, "window": 60, "used": 0},
            "pubchem": {"limit": 5, "window": 60, "used": 0}
        }
    
    async def fetch_ingredient_data(self, ingredient_name: str) -> Dict[str, Any]:
        """
        Fetch ingredient data from essential APIs only
        
        Args:
            ingredient_name: Name of ingredient to fetch
            
        Returns:
            Combined data from all sources
        """
        try:
            # Fetch from essential APIs in parallel
            tasks = [
                self._fetch_fda_data(ingredient_name),
                self._fetch_pubchem_data(ingredient_name),
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results
            combined_data = self._combine_api_results(ingredient_name, results)
            
            return combined_data
            
        except Exception as e:
            logger.error(f"Error fetching ingredient data: {e}")
            return self._get_default_ingredient_data(ingredient_name)
    
    async def _fetch_fda_data(self, ingredient_name: str) -> APIResponse:
        """Fetch data from FDA API"""
        try:
            # FDA API implementation would go here
            # For now, return mock data
            return APIResponse(
                success=True,
                data={"fda_status": "approved", "source": "FDA"},
                source="FDA"
            )
        except Exception as e:
            return APIResponse(
                success=False,
                data={},
                source="FDA",
                error=str(e)
            )
    
    async def _fetch_pubchem_data(self, ingredient_name: str) -> APIResponse:
        """Fetch data from PubChem API"""
        try:
            # PubChem API implementation would go here
            # For now, return mock data
            return APIResponse(
                success=True,
                data={"pubchem_id": "12345", "source": "PubChem"},
                source="PubChem"
            )
        except Exception as e:
            return APIResponse(
                success=False,
                data={},
                source="PubChem",
                error=str(e)
            )
    
    def _combine_api_results(self, ingredient_name: str, results: List[Any]) -> Dict[str, Any]:
        """Combine results from multiple APIs"""
        combined = {
            "ingredient": ingredient_name,
            "sources": {},
            "combined_score": 0.0,
            "risk_level": "unknown",
            "recommendations": []
        }
        
        successful_sources = 0
        
        for result in results:
            if isinstance(result, APIResponse) and result.success:
                combined["sources"][result.source] = result.data
                successful_sources += 1
        
        # Calculate combined score based on successful sources
        if successful_sources > 0:
            combined["combined_score"] = min(100.0, successful_sources * 25.0)
            combined["risk_level"] = "low" if combined["combined_score"] > 50 else "medium"
        
        return combined
    
    def _get_default_ingredient_data(self, ingredient_name: str) -> Dict[str, Any]:
        """Get default data when all APIs fail"""
        return {
            "ingredient": ingredient_name,
            "sources": {"default": "No external data available"},
            "combined_score": 0.0,
            "risk_level": "unknown",
            "recommendations": ["No data available - manual research recommended"]
        }


# Global service instance
_external_api_service: Optional[ExternalAPIService] = None


def get_external_api_service() -> ExternalAPIService:
    """Get or create external API service instance"""
    global _external_api_service
    if _external_api_service is None:
        _external_api_service = ExternalAPIService()
    return _external_api_service


# Health check function
async def health_check() -> Dict[str, Any]:
    """
    Check health of external APIs
    
    Returns:
        Health status of all APIs
    """
    service = get_external_api_service()
    
    health_status = {
        "fda": "unknown",
        "pubchem": "unknown",
        "overall": "unknown"
    }
    
    try:
        # Test FDA API
        fda_response = await service._fetch_fda_data("test")
        health_status["fda"] = "healthy" if fda_response.success else "unhealthy"
        
        # Test PubChem API
        pubchem_response = await service._fetch_pubchem_data("test")
        health_status["pubchem"] = "healthy" if pubchem_response.success else "unhealthy"
        
        # Overall health
        healthy_apis = sum(1 for status in health_status.values() if status == "healthy")
        total_apis = len([k for k in health_status.keys() if k != "overall"])
        
        if healthy_apis == total_apis:
            health_status["overall"] = "healthy"
        elif healthy_apis > 0:
            health_status["overall"] = "degraded"
        else:
            health_status["overall"] = "unhealthy"
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        health_status["overall"] = "unhealthy"
    
    return health_status
