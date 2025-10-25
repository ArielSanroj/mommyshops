"""
Enhanced Apify Integration for MommyShops
Professional web scraping using Apify actors for ingredient extraction
"""

import asyncio
import httpx
import logging
import os
import json
import subprocess
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ApifyResponse:
    """Standardized Apify response format."""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    source: str = "Apify"
    cached: bool = False

class ApifyEnhancedScraper:
    def __init__(self):
        self.api_token = os.getenv("APIFY_API_KEY")
        self.base_url = "https://api.apify.com/v2"
        self.session = None
        self.rate_limit_delay = 2  # seconds between requests
        
        if not self.api_token:
            logger.warning("APIFY_API_KEY not found in environment variables")
        
    async def __aenter__(self):
        headers = {
            'User-Agent': 'Mommyshops/1.0',
            'Accept': 'application/json'
        }
        
        if self.api_token:
            headers['Authorization'] = f'Bearer {self.api_token}'
        
        self.session = httpx.AsyncClient(
            timeout=60.0,
            headers=headers
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    async def scrape_product_page(self, url: str, actor_id: str = "apify/website-content-crawler") -> ApifyResponse:
        """
        Scrape product page using Apify actor for ingredient extraction
        """
        if not self.api_token:
            return ApifyResponse(
                success=False,
                data={},
                error="Apify API key not configured",
                source="Apify"
            )
        
        try:
            await asyncio.sleep(self.rate_limit_delay)  # Rate limiting
            
            # Prepare input for the actor
            input_data = {
                "startUrls": [url],
                "maxItems": 1,
                "waitForPageLoad": True,
                "maxConcurrency": 1,
                "extractTextContent": True,
                "extractLinks": False,
                "extractImages": False
            }
            
            # Run the actor
            run_result = await self._run_actor(actor_id, input_data)
            
            if not run_result["success"]:
                return ApifyResponse(
                    success=False,
                    data={},
                    error=run_result["error"],
                    source="Apify"
                )
            
            # Get the results
            results = await self._get_actor_results(run_result["runId"])
            
            if not results["success"]:
                return ApifyResponse(
                    success=False,
                    data={},
                    error=results["error"],
                    source="Apify"
                )
            
            # Parse the results
            parsed_data = self._parse_scraping_results(results["data"], url)
            
            return ApifyResponse(
                success=True,
                data=parsed_data,
                source="Apify"
            )
            
        except Exception as e:
            logger.error(f"Apify scraping error for {url}: {e}")
            return ApifyResponse(
                success=False,
                data={},
                error=str(e),
                source="Apify"
            )
    
    async def _run_actor(self, actor_id: str, input_data: Dict) -> Dict:
        """Run an Apify actor with given input."""
        try:
            url = f"{self.base_url}/acts/{actor_id}/runs"
            
            response = await self.session.post(
                url,
                json=input_data,
                timeout=30.0
            )
            
            if response.status_code == 201:
                run_data = response.json()
                return {
                    "success": True,
                    "runId": run_data["data"]["id"]
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to start actor run: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error running actor: {str(e)}"
            }
    
    async def _get_actor_results(self, run_id: str) -> Dict:
        """Get results from a completed Apify actor run."""
        try:
            # Wait for the run to complete
            max_wait_time = 300  # 5 minutes
            wait_interval = 10   # 10 seconds
            waited = 0
            
            while waited < max_wait_time:
                # Check run status
                status_url = f"{self.base_url}/runs/{run_id}"
                status_response = await self.session.get(status_url)
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    run_status = status_data["data"]["status"]
                    
                    if run_status == "SUCCEEDED":
                        # Get the results
                        results_url = f"{self.base_url}/runs/{run_id}/dataset/items"
                        results_response = await self.session.get(results_url)
                        
                        if results_response.status_code == 200:
                            results_data = results_response.json()
                            return {
                                "success": True,
                                "data": results_data["data"]
                            }
                        else:
                            return {
                                "success": False,
                                "error": f"Failed to get results: {results_response.status_code}"
                            }
                    
                    elif run_status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                        return {
                            "success": False,
                            "error": f"Actor run {run_status.lower()}"
                        }
                    
                    # Still running, wait and check again
                    await asyncio.sleep(wait_interval)
                    waited += wait_interval
                else:
                    return {
                        "success": False,
                        "error": f"Failed to check run status: {status_response.status_code}"
                    }
            
            return {
                "success": False,
                "error": "Actor run timed out"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error getting actor results: {str(e)}"
            }
    
    def _parse_scraping_results(self, results: List[Dict], url: str) -> Dict:
        """Parse Apify scraping results into standardized format."""
        try:
            if not results:
                return {
                    "ingredients": [],
                    "product_name": "Unknown Product",
                    "product_info": {},
                    "scraping_metadata": {
                        "url": url,
                        "method": "Apify Actor",
                        "items_found": 0
                    }
                }
            
            # Get the first result (should be the product page)
            result = results[0]
            
            # Extract ingredients
            ingredients = []
            
            # Try different possible ingredient fields
            ingredient_fields = [
                "ingredients", "ingredientList", "ingredient_list",
                "composition", "components", "activeIngredients",
                "inactiveIngredients", "fullIngredientList"
            ]
            
            for field in ingredient_fields:
                if field in result and result[field]:
                    if isinstance(result[field], list):
                        ingredients.extend(result[field])
                    elif isinstance(result[field], str):
                        # Split by common separators
                        split_ingredients = []
                        for separator in [',', ';', '\n', '|']:
                            if separator in result[field]:
                                split_ingredients = [ing.strip() for ing in result[field].split(separator)]
                                break
                        
                        if not split_ingredients:
                            split_ingredients = [result[field].strip()]
                        
                        ingredients.extend(split_ingredients)
                    break
            
            # Clean and deduplicate ingredients
            cleaned_ingredients = []
            seen = set()
            
            for ingredient in ingredients:
                if isinstance(ingredient, str):
                    clean_ingredient = ingredient.strip().lower()
                    if clean_ingredient and len(clean_ingredient) > 2 and clean_ingredient not in seen:
                        cleaned_ingredients.append(clean_ingredient)
                        seen.add(clean_ingredient)
            
            # Extract product information
            product_info = {
                "name": result.get("title", result.get("productName", "Unknown Product")),
                "brand": result.get("brand", result.get("manufacturer", "")),
                "price": result.get("price", result.get("cost", "")),
                "description": result.get("description", result.get("summary", "")),
                "category": result.get("category", result.get("productType", "")),
                "image_url": result.get("image", result.get("imageUrl", "")),
                "availability": result.get("availability", result.get("inStock", ""))
            }
            
            return {
                "ingredients": cleaned_ingredients,
                "product_name": product_info["name"],
                "product_info": product_info,
                "scraping_metadata": {
                    "url": url,
                    "method": "Apify Actor",
                    "items_found": len(results),
                    "ingredients_extracted": len(cleaned_ingredients),
                    "actor_id": "aYG0l9s7dbB7j3gbS"
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing Apify results: {e}")
            return {
                "ingredients": [],
                "product_name": "Unknown Product",
                "product_info": {},
                "scraping_metadata": {
                    "url": url,
                    "method": "Apify Actor",
                    "error": str(e)
                }
            }
    
    async def scrape_multiple_urls(self, urls: List[str], actor_id: str = "aYG0l9s7dbB7j3gbS") -> List[ApifyResponse]:
        """Scrape multiple URLs in parallel."""
        tasks = []
        
        for url in urls:
            task = self.scrape_product_page(url, actor_id)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error responses
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(ApifyResponse(
                    success=False,
                    data={},
                    error=str(result),
                    source="Apify"
                ))
            else:
                processed_results.append(result)
        
        return processed_results

# CLI-based Apify integration for advanced scraping
class ApifyCLIWrapper:
    """Wrapper for Apify CLI commands."""
    
    def __init__(self):
        self.api_token = os.getenv("APIFY_API_KEY")
        
    async def run_actor_cli(self, actor_id: str, input_data: Dict) -> Dict:
        """Run Apify actor using CLI."""
        try:
            if not self.api_token:
                return {
                    "success": False,
                    "error": "Apify API key not configured"
                }
            
            # Create temporary input file
            input_file = "/tmp/apify_input.json"
            with open(input_file, 'w') as f:
                json.dump(input_data, f)
            
            # Run the actor using CLI
            cmd = [
                "apify", "call", actor_id,
                "--input", input_file,
                "--token", self.api_token
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            # Clean up
            os.remove(input_file)
            
            if result.returncode == 0:
                # Parse the output
                try:
                    output_data = json.loads(result.stdout)
                    return {
                        "success": True,
                        "data": output_data
                    }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "data": {"raw_output": result.stdout}
                    }
            else:
                return {
                    "success": False,
                    "error": f"CLI command failed: {result.stderr}"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "CLI command timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"CLI error: {str(e)}"
            }

# Test function
async def test_apify_integration():
    """Test the Apify integration with sample URLs."""
    async with ApifyEnhancedScraper() as scraper:
        test_urls = [
            "https://www.sephora.com/product/retinol-serum-P123456",
            "https://www.ulta.com/product/hyaluronic-acid-serum-P789012"
        ]
        
        for url in test_urls:
            print(f"\nTesting Apify scraping: {url}")
            result = await scraper.scrape_product_page(url)
            
            if result.success:
                data = result.data
                print(f"✅ Success!")
                print(f"  Product: {data['product_name']}")
                print(f"  Ingredients: {len(data['ingredients'])} found")
                print(f"  Method: {data['scraping_metadata']['method']}")
                if data['ingredients']:
                    print(f"  Sample ingredients: {data['ingredients'][:3]}")
            else:
                print(f"❌ Error: {result.error}")

if __name__ == "__main__":
    asyncio.run(test_apify_integration())