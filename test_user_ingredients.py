#!/usr/bin/env python3
"""
Test script for analyzing the specific ingredient list provided by the user
"""

import requests
import json
import time

# The ingredient list provided by the user
ingredients_text = """Aqua
Cetearyl Alcohol
Cetrimonium Chloride
Glycerin
Cyclopentasiloxane
Dimethicone
Argania Spinosa Kernel Oil
Hydrolyzed Keratin
Hydrolyzed Collagen
Hydrolyzed Wheat Protein
Hydrolyzed Soy Protein
Panthenol
Tocopherol (Vitamin E)
Niacinamide
Camellia Sinensis Leaf Extract
Rosmarinus Officinalis (Rosemary) Leaf Extract
Thymus Vulgaris (Thyme) Extract
Mentha Piperita (Peppermint) Leaf Extract
Salvia Officinalis (Sage) Leaf Extract
Urtica Dioica (Nettle) Leaf Extract
Equisetum Arvense Extract
Arnica Montana Flower Extract
Chamomilla Recutita (Matricaria) Flower Extract
Aloe Barbadensis Leaf Juice
Sodium Hyaluronate
Hydroxyethylcellulose
Polyquaternium-10
Polyquaternium-7
Propylene Glycol
Disodium EDTA
Phenoxyethanol
Ethylhexylglycerin
Parfum (Fragrance)
CI 19140 (Yellow 5)
CI 17200 (Red 33)"""

def test_text_analysis():
    """Test the text analysis endpoint with the user's ingredient list"""
    
    print("🧪 Testing MommyShops Text Analysis")
    print("=" * 50)
    
    # Prepare the request data
    data = {
        "text": ingredients_text,
        "product_name": "Hair Care Product",
        "user_need": "Hair strengthening and conditioning",
        "notes": "Looking for natural and safe ingredients"
    }
    
    print(f"📝 Analyzing {len(ingredients_text.split())} ingredients...")
    print(f"🔍 Product: {data['product_name']}")
    print(f"💡 User Need: {data['user_need']}")
    print()
    
    try:
        # Make the request to the test server
        response = requests.post(
            "http://localhost:8000/analyze/text",
            params={
                "text": ingredients_text,
                "product_name": data["product_name"]
            },
            timeout=30
        )
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Analysis Successful!")
            print("=" * 50)
            
            # Display results
            print(f"🏷️  Product Name: {result.get('product_name', 'N/A')}")
            print(f"📊 Overall Score: {result.get('avg_eco_score', 'N/A')}")
            print(f"✅ Suitability: {result.get('suitability', 'N/A')}")
            print(f"⏱️  Processing Time: {result.get('processing_time', 'N/A')}s")
            print()
            
            # Display ingredients analysis
            ingredients = result.get('ingredients', [])
            if ingredients:
                print("🧪 Ingredient Analysis:")
                print("-" * 30)
                for i, ingredient in enumerate(ingredients[:10], 1):  # Show first 10
                    name = ingredient.get('name', 'Unknown')
                    score = ingredient.get('score', 'N/A')
                    safety = ingredient.get('safety_level', 'unknown')
                    description = ingredient.get('description', 'No description available')
                    
                    # Color coding for safety
                    if safety == 'safe':
                        safety_emoji = "🟢"
                    elif safety == 'harmful':
                        safety_emoji = "🔴"
                    else:
                        safety_emoji = "🟡"
                    
                    print(f"{i:2d}. {safety_emoji} {name}")
                    print(f"    Score: {score}/100 | Safety: {safety}")
                    print(f"    Description: {description}")
                    print()
                
                if len(ingredients) > 10:
                    print(f"... and {len(ingredients) - 10} more ingredients")
                    print()
            
            # Display recommendations
            recommendations = result.get('recommendations', [])
            if recommendations:
                print("💡 Recommendations:")
                print("-" * 20)
                for i, rec in enumerate(recommendations, 1):
                    print(f"{i}. {rec}")
                print()
            
            return True
            
        else:
            print(f"❌ Analysis Failed!")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

def test_health_check():
    """Test if the server is healthy"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is healthy")
            return True
        else:
            print(f"⚠️  Server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 MommyShops Ingredient Analysis Test")
    print("=" * 50)
    
    # Check server health first
    if not test_health_check():
        print("❌ Server is not responding. Please start the test server first.")
        exit(1)
    
    print()
    
    # Run the analysis test
    success = test_text_analysis()
    
    if success:
        print("🎉 Test completed successfully!")
        print("💡 You can now use the frontend at http://localhost:10888")
    else:
        print("❌ Test failed. Check the server logs for details.")
