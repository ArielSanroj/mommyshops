"""
CosIng API Store Integration
EU CosIng database via API Store for INCI names, CAS numbers, functions, and restrictions
"""

import asyncio
import httpx
import logging
import os
from typing import Dict, Optional, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CosIngResponse:
    """Standardized CosIng API response format."""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    source: str = "CosIng API Store"
    cached: bool = False

class CosIngClient:
    def __init__(self):
        self.base_url = "https://api.store/eu-institutions-api/directorate-general-for-internal-market-industry-entrepreneurship-and-smes-api/cosmetic-ingredient-database-cosing-ingredients-and-fragrance-inventory-api"
        self.api_key = os.getenv("COSING_API_KEY")  # Optional API key
        self.session = None
        self.rate_limit_delay = 2  # seconds between requests
        
    async def __aenter__(self):
        headers = {
            'User-Agent': 'Mommyshops/1.0',
            'Accept': 'application/json'
        }
        
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        self.session = httpx.AsyncClient(
            timeout=30.0,
            headers=headers
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    async def get_ingredient_data(self, ingredient_name: str) -> CosIngResponse:
        """
        Get ingredient data from CosIng database via API Store
        """
        try:
            await asyncio.sleep(self.rate_limit_delay)  # Rate limiting
            
            # Clean ingredient name for search
            clean_name = ingredient_name.strip().lower()
            
            # Try different search endpoints
            endpoints = [
                f"/ingredients?search={clean_name}",
                f"/ingredients?inci_name={clean_name}",
                f"/ingredients?name={clean_name}",
                f"/search?q={clean_name}"
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
            return CosIngResponse(
                success=False,
                data={},
                error=f"Ingredient '{ingredient_name}' not found in CosIng database",
                source="CosIng API Store"
            )
            
        except Exception as e:
            logger.error(f"CosIng API error for {ingredient_name}: {e}")
            return CosIngResponse(
                success=False,
                data={},
                error=str(e),
                source="CosIng API Store"
            )
    
    def _parse_response(self, data: Dict[str, Any], ingredient_name: str) -> CosIngResponse:
        """
        Parse CosIng API response into standardized format
        """
        try:
            # Handle different response formats
            ingredients = []
            
            if isinstance(data, list):
                ingredients = data
            elif isinstance(data, dict):
                if 'results' in data:
                    ingredients = data['results']
                elif 'ingredients' in data:
                    ingredients = data['ingredients']
                elif 'data' in data:
                    ingredients = data['data']
                else:
                    # Single ingredient response
                    ingredients = [data]
            
            if not ingredients:
                return CosIngResponse(
                    success=False,
                    data={},
                    error="No ingredients found in response",
                    source="CosIng API Store"
                )
            
            # Find best match
            best_match = self._find_best_match(ingredients, ingredient_name)
            
            if not best_match:
                return CosIngResponse(
                    success=False,
                    data={},
                    error="No matching ingredient found",
                    source="CosIng API Store"
                )
            
            # Extract information
            inci_name = best_match.get('inci_name', best_match.get('name', ingredient_name))
            cas_number = best_match.get('cas_number', best_match.get('cas', ''))
            function = best_match.get('function', best_match.get('cosmetic_function', ''))
            restrictions = best_match.get('restrictions', best_match.get('annex', ''))
            
            # Determine risk level based on restrictions
            risk_level = self._determine_risk_level(restrictions)
            
            # Create detailed risks
            risks_detailed = self._create_risks_description(restrictions, cas_number)
            
            # Create benefits description
            benefits = self._create_benefits_description(function, inci_name)
            
            result_data = {
                "benefits": benefits,
                "risks_detailed": risks_detailed,
                "risk_level": risk_level,
                "sources": "CosIng EU",
                "inci_name": inci_name,
                "cas_number": cas_number,
                "function": function,
                "restrictions": restrictions
            }
            
            return CosIngResponse(
                success=True,
                data=result_data,
                source="CosIng API Store"
            )
            
        except Exception as e:
            logger.error(f"Error parsing CosIng response: {e}")
            return CosIngResponse(
                success=False,
                data={},
                error=f"Error parsing response: {str(e)}",
                source="CosIng API Store"
            )
    
    def _find_best_match(self, ingredients: List[Dict], ingredient_name: str) -> Optional[Dict]:
        """Find the best matching ingredient from the list"""
        ingredient_lower = ingredient_name.lower()
        
        # First, try exact match
        for ingredient in ingredients:
            inci_name = ingredient.get('inci_name', ingredient.get('name', '')).lower()
            if inci_name == ingredient_lower:
                return ingredient
        
        # Then, try partial match
        for ingredient in ingredients:
            inci_name = ingredient.get('inci_name', ingredient.get('name', '')).lower()
            if ingredient_lower in inci_name or inci_name in ingredient_lower:
                return ingredient
        
        # Finally, return first ingredient if no match found
        return ingredients[0] if ingredients else None
    
    def _determine_risk_level(self, restrictions: str) -> str:
        """Determine risk level based on EU restrictions"""
        if not restrictions:
            return "seguro"
        
        restrictions_lower = restrictions.lower()
        
        # High risk indicators
        if any(word in restrictions_lower for word in ['prohibited', 'banned', 'annex ii']):
            return "riesgo alto"
        
        # Medium risk indicators
        if any(word in restrictions_lower for word in ['restricted', 'annex iii', 'limit']):
            return "riesgo medio"
        
        # Low risk indicators
        if any(word in restrictions_lower for word in ['allowed', 'permitted', 'safe']):
            return "riesgo bajo"
        
        return "riesgo bajo"  # Default for unknown restrictions
    
    def _create_risks_description(self, restrictions: str, cas_number: str) -> str:
        """Create detailed risks description"""
        risk_parts = []
        
        if restrictions:
            risk_parts.append(f"EU Restrictions: {restrictions}")
        
        if cas_number:
            risk_parts.append(f"CAS Number: {cas_number}")
        
        return "; ".join(risk_parts) if risk_parts else "No EU restrictions identified"
    
    def _create_benefits_description(self, function: str, inci_name: str) -> str:
        """Create benefits description"""
        benefit_parts = []
        
        if function:
            benefit_parts.append(function)
        
        if inci_name:
            benefit_parts.append(f"INCI Name: {inci_name}")
        
        return ", ".join(benefit_parts) if benefit_parts else "Cosmetic ingredient"

# Test function
async def test_cosing_api():
    """Test the CosIng API with sample ingredients"""
    async with CosIngClient() as client:
        test_ingredients = ["retinol", "parabens", "sodium lauryl sulfate", "water"]
        
        for ingredient in test_ingredients:
            print(f"\nTesting CosIng API: {ingredient}")
            result = await client.get_ingredient_data(ingredient)
            print(f"Success: {result.success}")
            if result.success:
                data = result.data
                print(f"INCI Name: {data.get('inci_name', 'N/A')}")
                print(f"CAS Number: {data.get('cas_number', 'N/A')}")
                print(f"Function: {data.get('function', 'N/A')}")
                print(f"Risk Level: {data.get('risk_level', 'N/A')}")
                print(f"Restrictions: {data.get('restrictions', 'N/A')}")
            else:
                print(f"Error: {result.error}")

if __name__ == "__main__":
    asyncio.run(test_cosing_api())