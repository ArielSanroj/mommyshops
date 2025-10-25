"""
Ollama Integration for MommyShops
Provides AI-powered ingredient analysis and recommendations using Ollama models
"""

import os
import logging
from typing import List, Dict, Optional, AsyncGenerator
from ollama import Client, AsyncClient
import asyncio
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class OllamaResponse:
    """Response from Ollama API"""
    content: str
    model: str
    success: bool
    error: Optional[str] = None

class OllamaIntegration:
    """Ollama integration for cosmetic ingredient analysis"""
    
    def __init__(self):
        self.api_key = os.getenv("OLLAMA_API_KEY")
        self.host = os.getenv("OLLAMA_HOST", "https://ollama.com")
        self.default_model = os.getenv("OLLAMA_MODEL", "gpt-oss:120b")
        
        # Initialize clients
        self.client = None
        self.async_client = None
        
        if self.api_key and self.api_key != "your-ollama-api-key-here":
            try:
                self.client = Client(
                    host=self.host,
                    headers={'Authorization': f'Bearer {self.api_key}'}
                )
                self.async_client = AsyncClient(
                    host=self.host,
                    headers={'Authorization': f'Bearer {self.api_key}'}
                )
                logger.info("Ollama integration initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Ollama clients: {e}")
                self.client = None
                self.async_client = None
        else:
            logger.info("OLLAMA_API_KEY not configured. Ollama integration will be disabled.")
    
    def is_available(self) -> bool:
        """Check if Ollama is available and configured"""
        return (self.client is not None and 
                self.async_client is not None and 
                self.api_key is not None and 
                self.api_key != "your-ollama-api-key-here")
    
    async def analyze_ingredients(self, ingredients: List[str], user_conditions: List[str] = None) -> OllamaResponse:
        """
        Analyze cosmetic ingredients using Ollama AI
        
        Args:
            ingredients: List of ingredient names
            user_conditions: User's skin conditions or concerns
            
        Returns:
            OllamaResponse with analysis results
        """
        if not self.is_available():
            return OllamaResponse(
                content="Ollama integration not available",
                model="none",
                success=False,
                error="OLLAMA_API_KEY not configured"
            )
        
        try:
            # Create analysis prompt
            prompt = self._create_ingredient_analysis_prompt(ingredients, user_conditions)
            
            messages = [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
            
            # Get response from Ollama
            response = await self.async_client.chat(
                model=self.default_model,
                messages=messages,
                stream=False
            )
            
            # Handle different response structures
            content = ""
            if isinstance(response, dict):
                if 'message' in response and isinstance(response['message'], dict):
                    content = response['message'].get('content', '')
                elif 'content' in response:
                    content = response['content']
                else:
                    content = str(response)
            else:
                content = str(response)
            
            return OllamaResponse(
                content=content,
                model=self.default_model,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error analyzing ingredients with Ollama: {e}")
            return OllamaResponse(
                content="",
                model=self.default_model,
                success=False,
                error=str(e)
            )
    
    async def suggest_alternatives(self, problematic_ingredients: List[str], user_conditions: List[str] = None) -> OllamaResponse:
        """
        Suggest safer alternatives for problematic ingredients
        
        Args:
            problematic_ingredients: List of ingredients to replace
            user_conditions: User's skin conditions
            
        Returns:
            OllamaResponse with alternative suggestions
        """
        if not self.is_available():
            return OllamaResponse(
                content="Ollama integration not available",
                model="none",
                success=False,
                error="OLLAMA_API_KEY not configured"
            )
        
        try:
            prompt = self._create_alternative_suggestion_prompt(problematic_ingredients, user_conditions)
            
            messages = [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
            
            response = await self.async_client.chat(
                model=self.default_model,
                messages=messages,
                stream=False
            )
            
            # Handle different response structures
            content = ""
            if isinstance(response, dict):
                if 'message' in response and isinstance(response['message'], dict):
                    content = response['message'].get('content', '')
                elif 'content' in response:
                    content = response['content']
                else:
                    content = str(response)
            else:
                content = str(response)
            
            return OllamaResponse(
                content=content,
                model=self.default_model,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error suggesting alternatives with Ollama: {e}")
            return OllamaResponse(
                content="",
                model=self.default_model,
                success=False,
                error=str(e)
            )
    
    async def stream_analysis(self, ingredients: List[str], user_conditions: List[str] = None) -> AsyncGenerator[str, None]:
        """
        Stream ingredient analysis for real-time updates
        
        Args:
            ingredients: List of ingredient names
            user_conditions: User's skin conditions
            
        Yields:
            Chunks of analysis content
        """
        if not self.is_available():
            yield "Ollama integration not available"
            return
        
        try:
            prompt = self._create_ingredient_analysis_prompt(ingredients, user_conditions)
            
            messages = [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
            
            response = await self.async_client.chat(
                model=self.default_model,
                messages=messages,
                stream=True
            )
            
            async for part in response:
                if isinstance(part, dict):
                    if 'message' in part and isinstance(part['message'], dict) and 'content' in part['message']:
                        yield part['message']['content']
                    elif 'content' in part:
                        yield part['content']
                    elif 'delta' in part and isinstance(part['delta'], dict) and 'content' in part['delta']:
                        yield part['delta']['content']
                    
        except Exception as e:
            logger.error(f"Error streaming analysis with Ollama: {e}")
            yield f"Error: {str(e)}"
    
    def _create_ingredient_analysis_prompt(self, ingredients: List[str], user_conditions: List[str] = None) -> str:
        """Create a detailed prompt for ingredient analysis"""
        conditions_text = ""
        if user_conditions:
            conditions_text = f"\n\nUser's skin conditions/concerns: {', '.join(user_conditions)}"
        
        return f"""
You are a cosmetic ingredient expert and dermatologist. Analyze the following cosmetic ingredients and provide detailed information:

Ingredients to analyze: {', '.join(ingredients)}{conditions_text}

Please provide:
1. Safety assessment for each ingredient (Safe/Moderate Risk/High Risk)
2. Potential benefits of each ingredient
3. Potential risks or side effects
4. Skin type compatibility (oily, dry, sensitive, combination, normal)
5. Specific concerns for users with the mentioned conditions
6. Overall product safety score (1-10)
7. Recommendations for use or avoidance

Format your response in a clear, structured way that's easy to understand for consumers.
"""
    
    def _create_alternative_suggestion_prompt(self, problematic_ingredients: List[str], user_conditions: List[str] = None) -> str:
        """Create a prompt for suggesting safer alternatives"""
        conditions_text = ""
        if user_conditions:
            conditions_text = f"\n\nUser's skin conditions/concerns: {', '.join(user_conditions)}"
        
        return f"""
You are a cosmetic ingredient expert. The user wants to avoid these potentially problematic ingredients:

Ingredients to avoid: {', '.join(problematic_ingredients)}{conditions_text}

Please suggest:
1. Safer alternatives for each ingredient
2. Why these alternatives are better
3. Products or ingredient combinations that provide similar benefits
4. Natural or organic alternatives when available
5. Specific recommendations based on the user's skin conditions

Focus on providing practical, actionable alternatives that maintain the desired cosmetic benefits while being safer for the skin.
"""
    
    async def test_connection(self) -> bool:
        """Test the connection to Ollama API"""
        if not self.is_available():
            return False
        
        try:
            test_messages = [
                {
                    'role': 'user',
                    'content': 'Hello, are you working?'
                }
            ]
            
            response = await self.async_client.chat(
                model=self.default_model,
                messages=test_messages,
                stream=False
            )
            
            return response is not None and 'message' in response
            
        except Exception as e:
            logger.error(f"Ollama connection test failed: {e}")
            return False

    async def enhance_ocr_text(self, ocr_text: str) -> OllamaResponse:
        """Enhance OCR text specifically for cosmetic ingredient extraction"""
        if not self.is_available():
            return OllamaResponse(
                content="Ollama integration not available",
                model=self.default_model,
                success=False,
                error="Ollama not configured"
            )
        
        try:
            prompt = f"""
Please analyze this OCR text from a cosmetic product label and extract the ingredient list clearly. 
The text may have OCR errors, so please correct them and provide a clean, properly formatted ingredient list.

OCR Text:
{ocr_text}

Please provide:
1. A corrected and cleaned ingredient list
2. Each ingredient on a separate line
3. Use proper cosmetic ingredient names (INCI names when possible)
4. Remove any non-ingredient text
5. Correct common OCR errors (like "UNFLOWER" → "SUNFLOWER")

Format your response as a simple list of ingredients, one per line.
"""
            
            response = await self.async_client.chat(
                model=self.default_model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Handle different response structures
            content = ""
            if isinstance(response, dict):
                if 'message' in response and isinstance(response['message'], dict):
                    content = response['message'].get('content', '')
                elif 'content' in response:
                    content = response['content']
                else:
                    content = str(response)
            else:
                content = str(response)
            
            return OllamaResponse(
                content=content,
                model=self.default_model,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error enhancing OCR text: {e}")
            return OllamaResponse(
                content="",
                model=self.default_model,
                success=False,
                error=str(e)
            )

    async def analyze_ingredient_safety(self, ingredients: List[str], skin_type: str = "normal") -> OllamaResponse:
        """Analyze ingredient safety with detailed dermatological assessment"""
        if not self.is_available():
            return OllamaResponse(
                content="Ollama integration not available",
                model=self.default_model,
                success=False,
                error="Ollama not configured"
            )
        
        try:
            prompt = f"""
As a dermatologist and cosmetic ingredient expert, analyze these cosmetic ingredients for safety, benefits, and potential concerns for {skin_type} skin:

Ingredients: {', '.join(ingredients)}

Please provide:
1. Safety assessment for each ingredient (Safe/Moderate Risk/High Risk)
2. Main benefits of each ingredient
3. Potential risks or side effects
4. Skin type compatibility (oily, dry, sensitive, combination, normal)
5. Overall safety score (1-10)
6. Specific recommendations for users with sensitive skin or eczema
7. Allergen potential and patch testing recommendations

Format your response in a clear, structured way that's easy to understand for consumers.
"""
            
            response = await self.async_client.chat(
                model=self.default_model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Handle different response structures
            content = ""
            if isinstance(response, dict):
                if 'message' in response and isinstance(response['message'], dict):
                    content = response['message'].get('content', '')
                elif 'content' in response:
                    content = response['content']
                else:
                    content = str(response)
            else:
                content = str(response)
            
            return OllamaResponse(
                content=content,
                model=self.default_model,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error analyzing ingredient safety: {e}")
            return OllamaResponse(
                content="",
                model=self.default_model,
                success=False,
                error=str(e)
            )

# Global instance
ollama_integration = OllamaIntegration()

# Convenience functions
async def analyze_ingredients_with_ollama(ingredients: List[str], user_conditions: List[str] = None) -> OllamaResponse:
    """Analyze ingredients using Ollama"""
    return await ollama_integration.analyze_ingredients(ingredients, user_conditions)

async def suggest_alternatives_with_ollama(problematic_ingredients: List[str], user_conditions: List[str] = None) -> OllamaResponse:
    """Suggest alternatives using Ollama"""
    return await ollama_integration.suggest_alternatives(problematic_ingredients, user_conditions)

async def stream_ingredient_analysis(ingredients: List[str], user_conditions: List[str] = None) -> AsyncGenerator[str, None]:
    """Stream ingredient analysis using Ollama"""
    async for chunk in ollama_integration.stream_analysis(ingredients, user_conditions):
        yield chunk

async def test_ollama_connection() -> bool:
    """Test Ollama connection"""
    return await ollama_integration.test_connection()

async def enhance_ocr_text_with_ollama(ocr_text: str) -> OllamaResponse:
    """Enhance OCR text using Ollama"""
    return await ollama_integration.enhance_ocr_text(ocr_text)

async def analyze_ingredient_safety_with_ollama(ingredients: List[str], skin_type: str = "normal") -> OllamaResponse:
    """Analyze ingredient safety using Ollama"""
    return await ollama_integration.analyze_ingredient_safety(ingredients, skin_type)