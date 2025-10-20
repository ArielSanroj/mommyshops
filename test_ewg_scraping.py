#!/usr/bin/env python3
"""
Test script for EWG Skin Deep web scraping
This script tests the EWG scraping functionality before integrating with Java
"""

import requests
from bs4 import BeautifulSoup
import time
import json
import re

def test_ewg_scraping():
    """Test EWG Skin Deep scraping with sample ingredients"""
    
    ingredients = [
        "Sodium Laureth Sulfate",
        "Phenoxyethanol", 
        "Benzyl Alcohol",
        "Aloe Vera",
        "Water"
    ]
    
    results = {}
    
    for ingredient in ingredients:
        print(f"\n🔍 Testing ingredient: {ingredient}")
        
        try:
            # Respect rate limiting - wait 2 seconds between requests
            time.sleep(2)
            
            # Search EWG Skin Deep
            search_url = f"https://www.ewg.org/skindeep/search/?query={ingredient.replace(' ', '+')}"
            
            headers = {
                'User-Agent': 'MommyShops/1.0 (Educational Purpose)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract hazard score
                hazard_score = extract_hazard_score(soup)
                
                # Extract concerns
                concerns = extract_concerns(soup)
                
                # Extract EWG rating
                ewg_rating = extract_ewg_rating(soup)
                
                # Extract data availability
                data_availability = extract_data_availability(soup)
                
                result = {
                    "ingredient": ingredient,
                    "hazardScore": hazard_score,
                    "concerns": concerns,
                    "ewgRating": ewg_rating,
                    "dataAvailability": data_availability,
                    "dataSource": "EWG Skin Deep Database",
                    "status": "SUCCESS"
                }
                
                print(f"✅ Found data: Score={hazard_score}, Rating={ewg_rating}")
                
            else:
                result = {
                    "ingredient": ingredient,
                    "error": f"HTTP {response.status_code}",
                    "status": "ERROR"
                }
                print(f"❌ Error: HTTP {response.status_code}")
                
        except Exception as e:
            result = {
                "ingredient": ingredient,
                "error": str(e),
                "status": "ERROR"
            }
            print(f"❌ Exception: {e}")
        
        results[ingredient] = result
    
    return results

def extract_hazard_score(soup):
    """Extract hazard score from EWG page"""
    # Look for EWG score images and patterns
    score_patterns = [
        r'score=(\d+)',  # score=3, score=2, etc.
        r'hazard.*?score.*?(\d+)',
        r'score.*?(\d+).*?hazard',
        r'rating.*?(\d+)',
        r'(\d+).*?out.*?10'
    ]
    
    # First try to find score in img src attributes
    img_tags = soup.find_all('img', src=True)
    for img in img_tags:
        src = img.get('src', '')
        match = re.search(r'score=(\d+)', src)
        if match:
            return int(match.group(1))
    
    # Then try text patterns
    text = soup.get_text().lower()
    
    for pattern in score_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    return "Not found"

def extract_concerns(soup):
    """Extract health concerns from EWG page"""
    concerns = []
    
    # Common EWG concern patterns
    concern_patterns = [
        "cancer", "reproductive", "developmental", "allergies", 
        "immunotoxicity", "neurotoxicity", "endocrine", "organ",
        "irritation", "sensitization", "toxicity", "skin irritation",
        "eye irritation", "allergic reactions", "hormone disruption"
    ]
    
    text = soup.get_text().lower()
    
    for pattern in concern_patterns:
        if pattern in text:
            concerns.append(pattern)
    
    return concerns

def extract_ewg_rating(soup):
    """Extract EWG rating"""
    # Look for EWG rating patterns
    rating_patterns = [
        r'ewg.*?rating.*?([a-z]+)',
        r'rating.*?([a-z]+)',
        r'verdict.*?([a-z]+)'
    ]
    
    text = soup.get_text().lower()
    
    for pattern in rating_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return "Unknown"

def extract_data_availability(soup):
    """Extract data availability information"""
    data = {
        "studiesAvailable": False,
        "regulatoryData": False,
        "industryData": False
    }
    
    text = soup.get_text().lower()
    
    if "studies" in text:
        data["studiesAvailable"] = True
    if "regulatory" in text:
        data["regulatoryData"] = True
    if "industry" in text:
        data["industryData"] = True
    
    return data

if __name__ == "__main__":
    print("🧪 Testing EWG Skin Deep Web Scraping")
    print("=" * 50)
    
    results = test_ewg_scraping()
    
    print("\n📊 RESULTS SUMMARY")
    print("=" * 30)
    
    for ingredient, result in results.items():
        if result.get("status") == "SUCCESS":
            print(f"✅ {ingredient}: Score={result.get('hazardScore')}, Rating={result.get('ewgRating')}")
        else:
            print(f"❌ {ingredient}: {result.get('error', 'Unknown error')}")
    
    # Save results to JSON
    with open('ewg_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to ewg_test_results.json")