#!/usr/bin/env python3
"""
Download and process COSING database
"""

import requests
import csv
import json
import re
from io import StringIO

def download_cosing_data():
    """Download COSING data from various sources"""
    
    print("📥 Downloading COSING Database")
    print("=" * 40)
    
    # Try different sources
    sources = [
        "https://data.europa.eu/data/datasets/cosmetic-ingredient-database-ingredients-and-fragrance-inventory?locale=en",
        "https://web.archive.org/web/20220926233955/https://ec.europa.eu/growth/tools-databases/cosing/pdf/COSING_Ingredients-Fragrance_Inventory_v2.csv",
        "https://single-market-economy.ec.europa.eu/sectors/cosmetics/cosmetic-ingredient-database_en"
    ]
    
    for i, url in enumerate(sources, 1):
        print(f"\n🔍 Trying source {i}: {url}")
        
        try:
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                content = response.text
                
                # Check if it's CSV content
                if content.strip().startswith('INCI') or 'INCI' in content[:1000]:
                    print("✅ Found CSV content!")
                    return content
                else:
                    print("❌ Not CSV content (HTML page)")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n⚠️  Could not download real CSV, creating sample data...")
    return create_sample_cosing_data()

def create_sample_cosing_data():
    """Create sample COSING data for testing"""
    
    sample_data = [
        {
            "INCI": "Sodium Laureth Sulfate",
            "CAS": "9004-82-4",
            "Function": "Surfactant",
            "Restrictions": "Maximum 1% in leave-on products",
            "Annex": "Annex III",
            "Status": "Approved"
        },
        {
            "INCI": "Phenoxyethanol",
            "CAS": "122-99-6", 
            "Function": "Preservative",
            "Restrictions": "Maximum 1% in all products",
            "Annex": "Annex V",
            "Status": "Approved"
        },
        {
            "INCI": "Benzyl Alcohol",
            "CAS": "100-51-6",
            "Function": "Solvent, Preservative",
            "Restrictions": "Maximum 1% in leave-on products",
            "Annex": "Annex V",
            "Status": "Approved"
        },
        {
            "INCI": "Aloe Barbadensis Leaf Juice",
            "CAS": "94349-62-9",
            "Function": "Skin conditioning",
            "Restrictions": "None",
            "Annex": "None",
            "Status": "Approved"
        },
        {
            "INCI": "Aqua",
            "CAS": "7732-18-5",
            "Function": "Solvent",
            "Restrictions": "None",
            "Annex": "None",
            "Status": "Approved"
        },
        {
            "INCI": "Propylene Glycol",
            "CAS": "57-55-6",
            "Function": "Humectant, Solvent",
            "Restrictions": "Maximum 5% in leave-on products",
            "Annex": "Annex III",
            "Status": "Approved"
        },
        {
            "INCI": "Parfum",
            "CAS": "N/A",
            "Function": "Fragrance",
            "Restrictions": "Must comply with IFRA standards",
            "Annex": "Annex III",
            "Status": "Approved"
        },
        {
            "INCI": "Sodium Chloride",
            "CAS": "7647-14-5",
            "Function": "Viscosity controlling",
            "Restrictions": "None",
            "Annex": "None",
            "Status": "Approved"
        },
        {
            "INCI": "Ethylhexylglycerin",
            "CAS": "70445-33-9",
            "Function": "Preservative",
            "Restrictions": "Maximum 0.5% in all products",
            "Annex": "Annex V",
            "Status": "Approved"
        },
        {
            "INCI": "Melaleuca Alternifolia Leaf Oil",
            "CAS": "68647-73-4",
            "Function": "Fragrance, Antimicrobial",
            "Restrictions": "Maximum 0.1% in leave-on products",
            "Annex": "Annex III",
            "Status": "Approved"
        }
    ]
    
    return sample_data

def process_cosing_data(data):
    """Process COSING data and create searchable database"""
    
    print("\n🔄 Processing COSING Data")
    print("=" * 30)
    
    if isinstance(data, str):
        # Try to parse as CSV
        try:
            csv_reader = csv.DictReader(StringIO(data))
            ingredients = list(csv_reader)
            print(f"✅ Parsed CSV with {len(ingredients)} ingredients")
        except:
            print("❌ Could not parse as CSV")
            return None
    else:
        # Use sample data
        ingredients = data
        print(f"✅ Using sample data with {len(ingredients)} ingredients")
    
    # Create searchable database
    database = {}
    
    for ingredient in ingredients:
        inci_name = ingredient.get('INCI', '').lower()
        if inci_name:
            database[inci_name] = {
                'INCI': ingredient.get('INCI', ''),
                'CAS': ingredient.get('CAS', ''),
                'Function': ingredient.get('Function', ''),
                'Restrictions': ingredient.get('Restrictions', ''),
                'Annex': ingredient.get('Annex', ''),
                'Status': ingredient.get('Status', '')
            }
    
    return database

def test_cosing_search(database):
    """Test COSING search functionality"""
    
    print("\n🧪 Testing COSING Search")
    print("=" * 25)
    
    test_ingredients = [
        "sodium laureth sulfate",
        "phenoxyethanol",
        "benzyl alcohol", 
        "aloe barbadensis leaf juice",
        "aqua",
        "propylene glycol",
        "parfum",
        "sodium chloride",
        "ethylhexylglycerin",
        "melaleuca alternifolia leaf oil"
    ]
    
    results = {}
    
    for ingredient in test_ingredients:
        if ingredient in database:
            results[ingredient] = database[ingredient]
            print(f"✅ Found: {ingredient}")
        else:
            # Try partial match
            found = False
            for key in database.keys():
                if ingredient in key or key in ingredient:
                    results[ingredient] = database[key]
                    print(f"✅ Found (partial): {ingredient} -> {key}")
                    found = True
                    break
            
            if not found:
                print(f"❌ Not found: {ingredient}")
    
    return results

def main():
    """Main function"""
    
    print("🧪 COSING Database Downloader and Processor")
    print("=" * 50)
    
    # Download data
    data = download_cosing_data()
    
    # Process data
    database = process_cosing_data(data)
    
    if database:
        # Test search
        results = test_cosing_search(database)
        
        # Save results
        with open('cosing_database.json', 'w') as f:
            json.dump(database, f, indent=2)
        
        print(f"\n💾 Database saved to cosing_database.json")
        print(f"📊 Total ingredients: {len(database)}")
        print(f"✅ Search results: {len(results)}")
        
        return database
    else:
        print("❌ Failed to create database")
        return None

if __name__ == "__main__":
    main()