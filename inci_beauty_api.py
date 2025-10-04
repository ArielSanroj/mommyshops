"""
INCI Beauty Pro API Integration
Professional API for 30,000+ cosmetic ingredients with scores, functions, and origins
"""

import asyncio
import httpx
import logging
import os
from typing import Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class INCIResponse:
    """Standardized INCI Beauty API response format."""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    source: str = "INCI Beauty"
    cached: bool = False

class INCIClient:
    def __init__(self):
        self.base_url = "https://api.incibeauty.com"
        self.api_key = os.getenv("INCI_BEAUTY_API_KEY")
        self.session = None
        self.rate_limit_delay = 1  # seconds between requests
        
        if not self.api_key:
            logger.warning("INCI_BEAUTY_API_KEY not found in environment variables")
        
    async def __aenter__(self):
        headers = {
            'User-Agent': 'Mommyshops/1.0',
            'Accept': 'application/json'
        }
        
        if self.api_key and self.api_key != "your_inci_beauty_api_key_here":
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        self.session = httpx.AsyncClient(
            timeout=30.0,
            headers=headers
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    async def get_ingredient_data(self, ingredient_name: str) -> INCIResponse:
        """
        Get comprehensive ingredient data from INCI Beauty Pro API
        """
        if not self.api_key or self.api_key == "your_inci_beauty_api_key_here":
            return INCIResponse(
                success=False,
                data={},
                error="INCI Beauty API key not configured",
                source="INCI Beauty"
            )
        
        try:
            await asyncio.sleep(self.rate_limit_delay)  # Rate limiting
            
            # Clean ingredient name for API
            clean_name = ingredient_name.strip().lower()
            
            # Try different API endpoints
            endpoints = [
                f"/ingredients/{clean_name}",
                f"/ingredients/search?q={clean_name}",
                f"/ingredients/lookup?name={clean_name}"
            ]
            
            for endpoint in endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    response = await self.session.get(url)
                    
                    if response.status_code == 200:
                        data = response.json()
                        return self._parse_response(data, ingredient_name)
                    elif response.status_code == 404:
                        continue  # Try next endpoint
                    else:
                        response.raise_for_status()
                        
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        continue  # Try next endpoint
                    else:
                        raise e
            
            # If no endpoint worked
            return INCIResponse(
                success=False,
                data={},
                error=f"Ingredient '{ingredient_name}' not found in INCI Beauty database",
                source="INCI Beauty"
            )
            
        except Exception as e:
            logger.error(f"INCI Beauty API error for {ingredient_name}: {e}")
            return INCIResponse(
                success=False,
                data={},
                error=str(e),
                source="INCI Beauty"
            )
    
    def _parse_response(self, data: Dict[str, Any], ingredient_name: str) -> INCIResponse:
        """
        Parse INCI Beauty API response into standardized format
        """
        try:
            # Extract basic information
            name = data.get('name', ingredient_name)
            inci_name = data.get('inci_name', name)
            
            # Extract score (convert to 0-100 scale if needed)
            score_raw = data.get('score', 0)
            if isinstance(score_raw, str):
                # Handle score formats like "8/20"
                if '/' in score_raw:
                    numerator, denominator = score_raw.split('/')
                    score = (float(numerator) / float(denominator)) * 100
                else:
                    score = float(score_raw)
            else:
                score = float(score_raw)
            
            # Convert to eco_score (higher score = more eco-friendly)
            eco_score = min(100, max(0, score))
            
            # Extract function/benefits
            function = data.get('function', '')
            if isinstance(function, list):
                function = ', '.join(function)
            
            # Extract origin
            origin = data.get('origin', '')
            if isinstance(origin, list):
                origin = ', '.join(origin)
            
            # Extract concerns
            concerns = data.get('concerns', [])
            if isinstance(concerns, list):
                concerns = ', '.join(concerns)
            
            # Determine risk level based on score and concerns
            risk_level = self._determine_risk_level(score, concerns)
            
            # Create detailed risks
            risks_detailed = self._create_risks_description(concerns, origin, score)
            
            # Create benefits description
            benefits = self._create_benefits_description(function, origin)
            
            result_data = {
                "benefits": benefits,
                "risks_detailed": risks_detailed,
                "risk_level": risk_level,
                "sources": "INCI Beauty Pro",
                "eco_score": eco_score,
                "inci_name": inci_name,
                "origin": origin,
                "function": function,
                "concerns": concerns,
                "raw_score": score_raw
            }
            
            return INCIResponse(
                success=True,
                data=result_data,
                source="INCI Beauty"
            )
            
        except Exception as e:
            logger.error(f"Error parsing INCI Beauty response: {e}")
            return INCIResponse(
                success=False,
                data={},
                error=f"Error parsing response: {str(e)}",
                source="INCI Beauty"
            )
    
    def _determine_risk_level(self, score: float, concerns: str) -> str:
        """Determine risk level based on score and concerns"""
        concerns_lower = concerns.lower() if concerns else ""
        
        # High risk indicators
        if any(word in concerns_lower for word in ['carcinogen', 'toxic', 'severe', 'high']):
            return "riesgo alto"
        
        # Medium risk indicators
        if any(word in concerns_lower for word in ['irritation', 'moderate', 'allergen']):
            return "riesgo medio"
        
        # Score-based assessment
        if score < 30:
            return "riesgo alto"
        elif score < 60:
            return "riesgo medio"
        elif score < 80:
            return "riesgo bajo"
        else:
            return "seguro"
    
    def _create_risks_description(self, concerns: str, origin: str, score: float) -> str:
        """Create detailed risks description"""
        risk_parts = []
        
        if concerns:
            risk_parts.append(f"Concerns: {concerns}")
        
        if origin:
            risk_parts.append(f"Origin: {origin}")
        
        if score < 50:
            risk_parts.append(f"Low safety score: {score}/100")
        
        return "; ".join(risk_parts) if risk_parts else "No specific concerns identified"
    
    def _create_benefits_description(self, function: str, origin: str) -> str:
        """Create benefits description"""
        benefit_parts = []
        
        if function:
            benefit_parts.append(function)
        
        if origin and origin.lower() not in ['synthetic', 'chemical']:
            benefit_parts.append(f"Natural origin: {origin}")
        
        return ", ".join(benefit_parts) if benefit_parts else "Cosmetic ingredient"

# Test function
async def test_inci_beauty():
    """Test the INCI Beauty API with sample ingredients"""
    async with INCIClient() as client:
        test_ingredients = ["retinol", "parabens", "sodium lauryl sulfate", "water"]
        
        for ingredient in test_ingredients:
            print(f"\nTesting INCI Beauty: {ingredient}")
            result = await client.get_ingredient_data(ingredient)
            print(f"Success: {result.success}")
            if result.success:
                data = result.data
                print(f"INCI Name: {data.get('inci_name', 'N/A')}")
                print(f"Score: {data.get('raw_score', 'N/A')}")
                print(f"Eco Score: {data.get('eco_score', 'N/A')}/100")
                print(f"Function: {data.get('function', 'N/A')}")
                print(f"Origin: {data.get('origin', 'N/A')}")
                print(f"Risk Level: {data.get('risk_level', 'N/A')}")
                print(f"Concerns: {data.get('concerns', 'N/A')}")
            else:
                print(f"Error: {result.error}")

if __name__ == "__main__":
    asyncio.run(test_inci_beauty())