#!/usr/bin/env python3
"""
Script para configurar NVIDIA NIM correctamente
Basado en la documentación oficial de NVIDIA
"""

import os
import asyncio
import httpx
import base64
from dotenv import load_dotenv

load_dotenv()

class NIMConfigurator:
    def __init__(self):
        self.api_key = os.getenv('NVIDIA_API_KEY')
        self.base_url = "https://api.nvcf.nvidia.com/v2/nvcf"
        
    async def test_nim_endpoints(self):
        """Test diferentes endpoints de NVIDIA NIM"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Endpoints para probar basados en la documentación
        endpoints = [
            f"{self.base_url}/pexec/functions",
            f"{self.base_url}/infer/functions",
            f"{self.base_url}/pexec/functions/meta/llama-3.1-8b-instruct",
            f"{self.base_url}/infer/functions/meta-llama-3.1-8b-instruct"
        ]
        
        models = [
            "meta/llama-3.1-8b-instruct",
            "meta-llama-3.1-8b-instruct",
            "meta/llama-3_1-8b-instruct",
            "llama-3.1-8b-instruct"
        ]
        
        test_payload = {
            "messages": [
                {
                    "role": "user",
                    "content": "Hello, can you help me extract cosmetic ingredients from a product label?"
                }
            ],
            "max_tokens": 100,
            "temperature": 0.2,
            "top_p": 0.7
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for i, endpoint in enumerate(endpoints):
                model = models[i] if i < len(models) else models[0]
                test_payload["model"] = model
                
                try:
                    print(f"\n🔍 Testing endpoint {i+1}/{len(endpoints)}")
                    print(f"   Endpoint: {endpoint}")
                    print(f"   Model: {model}")
                    
                    response = await client.post(endpoint, headers=headers, json=test_payload)
                    
                    if response.status_code == 200:
                        print(f"✅ SUCCESS! Endpoint {i+1} works")
                        result = response.json()
                        content = result.get('choices', [{}])[0].get('message', {}).get('content')
                        print(f"   Response: {content[:100]}...")
                        return endpoint, model
                    elif response.status_code == 404:
                        print(f"❌ 404 Error - Endpoint not found")
                    else:
                        print(f"❌ HTTP {response.status_code}: {response.text[:100]}...")
                        
                except Exception as e:
                    print(f"❌ Error: {e}")
        
        return None, None
    
    async def test_multimodal_extraction(self, endpoint, model):
        """Test multimodal extraction con imagen"""
        
        # Load test image
        try:
            with open('dense_text_label.png', 'rb') as f:
                image_data = f.read()
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            print(f"📸 Loaded test image: {len(image_data)} bytes")
        except FileNotFoundError:
            print("❌ Test image not found")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Multimodal test message
        test_message = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert in cosmetic ingredient analysis. Extract ALL cosmetic INCI ingredients from product labels."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract ALL cosmetic INCI ingredients from this product label image. Return only comma-separated list."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_b64}"
                            }
                        }
                    ]
                }
            ],
            "model": model,
            "max_tokens": 512,
            "temperature": 0.2,
            "top_p": 0.7
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                print(f"\n🔍 Testing multimodal extraction")
                print(f"   Endpoint: {endpoint}")
                print(f"   Model: {model}")
                
                response = await client.post(endpoint, headers=headers, json=test_message)
                
                if response.status_code == 200:
                    print(f"✅ SUCCESS! Multimodal extraction works")
                    result = response.json()
                    content = result.get('choices', [{}])[0].get('message', {}).get('content')
                    print(f"   Extracted ingredients: {content}")
                    return True
                else:
                    print(f"❌ HTTP {response.status_code}: {response.text[:200]}...")
                    return False
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                return False

async def main():
    """Main configuration function"""
    print("🚀 Configuring NVIDIA NIM Integration")
    print("=" * 50)
    
    configurator = NIMConfigurator()
    
    if not configurator.api_key:
        print("❌ NVIDIA_API_KEY not found in .env")
        return
    
    print(f"🔑 Using API Key: {configurator.api_key[:20]}...")
    
    # Test basic endpoints
    endpoint, model = await configurator.test_nim_endpoints()
    
    if endpoint and model:
        print(f"\n✅ Working configuration found:")
        print(f"   Endpoint: {endpoint}")
        print(f"   Model: {model}")
        
        # Test multimodal extraction
        await configurator.test_multimodal_extraction(endpoint, model)
        
        # Update nemotron_integration.py with working config
        print(f"\n🔧 Updating nemotron_integration.py with working configuration...")
        update_nemotron_config(endpoint, model)
        
    else:
        print("\n❌ No working configuration found")
        print("   Check your API key and NVIDIA NIM deployment")
        print("   You may need to deploy NIM using the provided instructions")

def update_nemotron_config(endpoint, model):
    """Update nemotron_integration.py with working configuration"""
    
    config_content = f'''# Working NVIDIA NIM Configuration
# Generated by setup_nvidia_nim.py

WORKING_ENDPOINT = "{endpoint}"
WORKING_MODEL = "{model}"

# Use these values in nemotron_integration.py
'''
    
    with open('nim_config.txt', 'w') as f:
        f.write(config_content)
    
    print(f"✅ Configuration saved to nim_config.txt")
    print(f"   Endpoint: {endpoint}")
    print(f"   Model: {model}")

if __name__ == "__main__":
    asyncio.run(main())