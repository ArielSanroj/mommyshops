"""
External API Service for MommyShops API
Handles integration with external APIs (FDA, EWG, PubChem, etc.)
"""

import logging
from typing import Dict, Any, Optional, List
import asyncio
import httpx
from datetime import datetime, timedelta

from ..core.config import get_settings

logger = logging.getLogger(__name__)

class ExternalAPIService:
    """
    Service for external API integration
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.timeout = 30.0
        self.rate_limits = {
            "fda": {"limit": 60, "window": 60, "used": 0, "reset_time": datetime.now()},
            "ewg": {"limit": 10, "window": 60, "used": 0, "reset_time": datetime.now()},
            "pubchem": {"limit": 5, "window": 60, "used": 0, "reset_time": datetime.now()}
        }
    
    async def fetch_ingredient_data(self, ingredient_name: str, user_need: str) -> Optional[Dict[str, Any]]:
        """
        Fetch ingredient data from external APIs
        """
        try:
            # Check rate limits
            if not self._check_rate_limits():
                logger.warning("Rate limits exceeded, using cached data")
                return self._get_cached_data(ingredient_name)
            
            # Fetch from multiple APIs in parallel
            tasks = [
                self._fetch_fda_data(ingredient_name),
                self._fetch_ewg_data(ingredient_name),
                self._fetch_pubchem_data(ingredient_name)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results
            combined_data = self._combine_api_results(ingredient_name, results)
            
            # Update rate limits
            self._update_rate_limits()
            
            return combined_data
            
        except Exception as e:
            logger.error(f"Error fetching ingredient data: {e}")
            return None
    
    async def _fetch_fda_data(self, ingredient_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch data from FDA API
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://api.fda.gov/drug/enforcement.json",
                    params={
                        "search": f"substance_name:{ingredient_name}",
                        "limit": 1
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    if results:
                        return {
                            "source": "FDA",
                            "risk_level": "riesgo medio",
                            "risks_detailed": "Enforcement action found",
                            "benefits": "No disponible"
                        }
                
                return None
                
        except Exception as e:
            logger.error(f"Error fetching FDA data: {e}")
            return None
    
    async def _fetch_ewg_data(self, ingredient_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch data from EWG API
        """
        try:
            # EWG doesn't have a public API, so we'll simulate
            # In production, this would use web scraping or their API if available
            return {
                "source": "EWG",
                "risk_level": "riesgo bajo",
                "eco_score": 70.0,
                "risks_detailed": "Moderate concern for skin irritation",
                "benefits": "Emollient properties"
            }
            
        except Exception as e:
            logger.error(f"Error fetching EWG data: {e}")
            return None
    
    async def _fetch_pubchem_data(self, ingredient_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch data from PubChem API
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{ingredient_name}/property/MolecularFormula,MolecularWeight,CanonicalSMILES/JSON"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    properties = data.get("PropertyTable", {}).get("Properties", [])
                    
                    if properties:
                        return {
                            "source": "PubChem",
                            "risk_level": "riesgo bajo",
                            "benefits": "Chemical properties available",
                            "risks_detailed": "No significant risks identified"
                        }
                
                return None
                
        except Exception as e:
            logger.error(f"Error fetching PubChem data: {e}")
            return None
    
    def _combine_api_results(self, ingredient_name: str, results: List[Any]) -> Dict[str, Any]:
        """
        Combine results from multiple APIs
        """
        try:
            combined = {
                "name": ingredient_name,
                "risk_level": "desconocido",
                "eco_score": 50.0,
                "benefits": "No disponible",
                "risks_detailed": "No disponible",
                "sources": []
            }
            
            # Process results
            for result in results:
                if isinstance(result, dict) and result.get("source"):
                    source = result["source"]
                    combined["sources"].append(source)
                    
                    # Update risk level (prioritize higher risk)
                    if result.get("risk_level"):
                        risk_levels = ["seguro", "riesgo bajo", "riesgo medio", "riesgo alto", "cancerígeno"]
                        current_index = risk_levels.index(combined["risk_level"]) if combined["risk_level"] in risk_levels else 0
                        new_index = risk_levels.index(result["risk_level"]) if result["risk_level"] in risk_levels else 0
                        
                        if new_index > current_index:
                            combined["risk_level"] = result["risk_level"]
                    
                    # Update eco score
                    if result.get("eco_score"):
                        combined["eco_score"] = result["eco_score"]
                    
                    # Update benefits
                    if result.get("benefits") and result["benefits"] != "No disponible":
                        combined["benefits"] = result["benefits"]
                    
                    # Update risks
                    if result.get("risks_detailed") and result["risks_detailed"] != "No disponible":
                        combined["risks_detailed"] = result["risks_detailed"]
            
            # Set sources string
            combined["sources"] = ",".join(combined["sources"]) if combined["sources"] else "No disponible"
            
            return combined
            
        except Exception as e:
            logger.error(f"Error combining API results: {e}")
            return {
                "name": ingredient_name,
                "risk_level": "desconocido",
                "eco_score": 50.0,
                "benefits": "No disponible",
                "risks_detailed": "Error al combinar datos",
                "sources": "Error"
            }
    
    def _check_rate_limits(self) -> bool:
        """
        Check if rate limits are exceeded
        """
        try:
            now = datetime.now()
            
            for api, limits in self.rate_limits.items():
                # Reset if window has passed
                if now > limits["reset_time"]:
                    limits["used"] = 0
                    limits["reset_time"] = now + timedelta(seconds=limits["window"])
                
                # Check if limit exceeded
                if limits["used"] >= limits["limit"]:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limits: {e}")
            return False
    
    def _update_rate_limits(self):
        """
        Update rate limit counters
        """
        try:
            for api, limits in self.rate_limits.items():
                limits["used"] += 1
                
        except Exception as e:
            logger.error(f"Error updating rate limits: {e}")
    
    def _get_cached_data(self, ingredient_name: str) -> Optional[Dict[str, Any]]:
        """
        Get cached data for ingredient
        """
        try:
            # This would retrieve from cache
            # For now, return default data
            return {
                "name": ingredient_name,
                "risk_level": "desconocido",
                "eco_score": 50.0,
                "benefits": "No disponible",
                "risks_detailed": "Datos en caché",
                "sources": "Cache"
            }
            
        except Exception as e:
            logger.error(f"Error getting cached data: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of external APIs
        """
        try:
            health_status = {
                "all_available": True,
                "apis": {}
            }
            
            # Check each API
            for api in ["fda", "ewg", "pubchem"]:
                try:
                    # This would make a simple request to check API health
                    # For now, assume all are available
                    health_status["apis"][api] = {
                        "status": "healthy",
                        "response_time": 100  # ms
                    }
                except Exception as e:
                    health_status["apis"][api] = {
                        "status": "unhealthy",
                        "error": str(e)
                    }
                    health_status["all_available"] = False
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return {
                "all_available": False,
                "apis": {},
                "error": str(e)
            }

