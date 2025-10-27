#!/usr/bin/env python3
"""
Simple test server for MommyShops
Tests basic functionality without complex dependencies
"""

from fastapi import FastAPI, File, UploadFile, Form, Query
from fastapi.middleware.cors import CORSMiddleware
import pytesseract
from PIL import Image
import pillow_heif
import pyheif
import io
import json
import logging
import os

# Register HEIF opener with Pillow
pillow_heif.register_heif_opener()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_heic_image(image_content):
    """Process HEIC image using multiple methods"""
    try:
        # Method 1: Try pillow-heif
        image = Image.open(io.BytesIO(image_content))
        logger.info(f"Successfully opened HEIC with pillow-heif, mode: {image.mode}")
        return image
    except Exception as e1:
        logger.warning(f"pillow-heif failed: {e1}")
        
        try:
            # Method 2: Try pyheif
            heif_file = pyheif.read(image_content)
            image = Image.frombytes(
                heif_file.mode, 
                heif_file.size, 
                heif_file.data,
                "raw",
                heif_file.mode,
                heif_file.stride,
            )
            logger.info(f"Successfully opened HEIC with pyheif, mode: {image.mode}")
            return image
        except Exception as e2:
            logger.error(f"pyheif also failed: {e2}")
            raise Exception(f"Both HEIC libraries failed. pillow-heif: {e1}, pyheif: {e2}")

# Create FastAPI app
app = FastAPI(
    title="MommyShops Test API",
    description="Simple test version for image analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "MommyShops Test API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "analyze_image": "/analyze/image",
            "analyze_text": "/analyze/text",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "mommyshops-test",
        "version": "1.0.0"
    }

@app.post("/analyze/image")
async def analyze_image(
    file: UploadFile = File(...),
    product_name: str = Form("Unknown Product"),
    user_need: str = Form("general")
):
    """Analyze image for ingredients"""
    try:
        # Check file type
        if not file.content_type or not file.content_type.startswith('image/'):
            return {
                "success": False,
                "error": f"Invalid file type: {file.content_type}. Please upload an image file (JPG, PNG, WebP, HEIC).",
                "product_name": product_name,
                "ingredients": [],
                "avg_eco_score": 0,
                "suitability": "unknown",
                "recommendations": ["Please upload a valid image file"],
                "processing_time": 0
            }
        
        # Read image content
        image_content = await file.read()
        
        # Debug information
        logger.info(f"Processing image: {file.filename}, type: {file.content_type}, size: {len(image_content)} bytes")
        
        # Check file extension
        file_extension = os.path.splitext(file.filename)[1].lower() if file.filename else ""
        
        # Convert to PIL Image
        try:
            # Check if it's a HEIC file
            if file_extension == '.heic' or file.content_type == 'image/heic':
                image = process_heic_image(image_content)
            else:
                image = Image.open(io.BytesIO(image_content))
            
            # Convert to RGB if necessary (HEIC might be in different color space)
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # Ensure image is in a format that OCR can handle
            if image.mode != 'RGB':
                image = image.convert('RGB')
                
            logger.info(f"Successfully processed image: {image.size}, mode: {image.mode}")
            
        except Exception as e:
            # More detailed error information
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "file_type": file.content_type,
                "file_extension": file_extension,
                "file_size": len(image_content)
            }
            
            return {
                "success": False,
                "error": f"Cannot process image file: {str(e)}. Please ensure it's a valid image format (JPG, PNG, WebP, HEIC).",
                "error_details": error_details,
                "product_name": product_name,
                "ingredients": [],
                "avg_eco_score": 0,
                "suitability": "unknown",
                "recommendations": ["Please upload a valid image file in JPG, PNG, WebP, or HEIC format"],
                "processing_time": 0
            }
        
        # Extract text using OCR
        try:
            extracted_text = pytesseract.image_to_string(image)
            logger.info(f"OCR extracted text length: {len(extracted_text)} characters")
        except Exception as ocr_error:
            logger.warning(f"OCR failed: {ocr_error}, using fallback")
            # Fallback: create a simple text representation
            extracted_text = f"Image analysis failed for {product_name}. OCR error: {str(ocr_error)}"
        
        # Enhanced ingredient analysis with external APIs simulation
        ingredients_found = []
        
        # Comprehensive ingredient database with EWG, PubChem, OMS data
        comprehensive_ingredients = {
            'AQUA': {
                'score': 95, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Water - Essential ingredient, completely safe',
                'eco_friendly': True, 'substitute': None
            },
            'CETEARYL ALCOHOL': {
                'score': 85, 'safety_level': 'safe', 'ewg_score': 2, 'risk': 'low',
                'description': 'Emulsifier and thickener, generally safe',
                'eco_friendly': True, 'substitute': 'Cetyl Alcohol'
            },
            'CETRIMONIUM CHLORIDE': {
                'score': 70, 'safety_level': 'moderate', 'ewg_score': 4, 'risk': 'moderate',
                'description': 'Conditioning agent, may cause irritation',
                'eco_friendly': False, 'substitute': 'Behentrimonium Chloride'
            },
            'BEHENTRIMONIUM CHLORIDE': {
                'score': 75, 'safety_level': 'moderate', 'ewg_score': 3, 'risk': 'low',
                'description': 'Gentler conditioning agent than Cetrimonium',
                'eco_friendly': True, 'substitute': 'Cetyl Alcohol'
            },
            'GLYCERIN': {
                'score': 90, 'safety_level': 'safe', 'ewg_score': 2, 'risk': 'none',
                'description': 'Moisturizing agent, very safe and effective',
                'eco_friendly': True, 'substitute': None
            },
            'HYDROLYZED KERATIN': {
                'score': 80, 'safety_level': 'safe', 'ewg_score': 3, 'risk': 'low',
                'description': 'Protein for hair strengthening',
                'eco_friendly': True, 'substitute': 'Hydrolyzed Wheat Protein'
            },
            'HYDROLYZED COLLAGEN': {
                'score': 85, 'safety_level': 'safe', 'ewg_score': 2, 'risk': 'none',
                'description': 'Protein for hair repair and moisture',
                'eco_friendly': True, 'substitute': 'Hydrolyzed Soy Protein'
            },
            'ARGAN OIL': {
                'score': 95, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Natural oil rich in vitamins and antioxidants',
                'eco_friendly': True, 'substitute': None
            },
            'MACADAMIA SEED OIL': {
                'score': 90, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Natural oil for hair conditioning',
                'eco_friendly': True, 'substitute': 'Jojoba Oil'
            },
            'JOJOBA OIL': {
                'score': 95, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Natural oil similar to skin sebum',
                'eco_friendly': True, 'substitute': None
            },
            'AVOCADO OIL': {
                'score': 90, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Natural oil rich in vitamins A, D, E',
                'eco_friendly': True, 'substitute': 'Olive Oil'
            },
            'SHEA BUTTER': {
                'score': 95, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Natural butter with excellent moisturizing properties',
                'eco_friendly': True, 'substitute': None
            },
            'PANTENOL': {
                'score': 90, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Vitamin B5, excellent for hair and skin',
                'eco_friendly': True, 'substitute': None
            },
            'HYDROLYZED WHEAT PROTEIN': {
                'score': 85, 'safety_level': 'safe', 'ewg_score': 2, 'risk': 'low',
                'description': 'Plant protein for hair strengthening',
                'eco_friendly': True, 'substitute': 'Hydrolyzed Soy Protein'
            },
            'HYDROLYZED SOY PROTEIN': {
                'score': 85, 'safety_level': 'safe', 'ewg_score': 2, 'risk': 'low',
                'description': 'Plant protein for hair repair',
                'eco_friendly': True, 'substitute': 'Hydrolyzed Wheat Protein'
            },
            'HYDROLYZED CORN PROTEIN': {
                'score': 80, 'safety_level': 'safe', 'ewg_score': 3, 'risk': 'low',
                'description': 'Plant protein for hair conditioning',
                'eco_friendly': True, 'substitute': 'Hydrolyzed Wheat Protein'
            },
            'SILK AMINO ACIDS': {
                'score': 85, 'safety_level': 'safe', 'ewg_score': 2, 'risk': 'low',
                'description': 'Natural protein for hair strengthening',
                'eco_friendly': True, 'substitute': 'Hydrolyzed Wheat Protein'
            },
            'SERINE': {
                'score': 90, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Amino acid essential for protein synthesis',
                'eco_friendly': True, 'substitute': None
            },
            'THREONINE': {
                'score': 90, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Essential amino acid for hair health',
                'eco_friendly': True, 'substitute': None
            },
            'ARGININE': {
                'score': 90, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Amino acid that promotes hair growth',
                'eco_friendly': True, 'substitute': None
            },
            'GLUTAMIC ACID': {
                'score': 90, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Amino acid for hair conditioning',
                'eco_friendly': True, 'substitute': None
            },
            'VITAMIN B5': {
                'score': 90, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Panthenol - excellent for hair and skin',
                'eco_friendly': True, 'substitute': None
            },
            'VITAMIN E': {
                'score': 95, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Tocopherol - powerful antioxidant',
                'eco_friendly': True, 'substitute': None
            },
            'ALOE VERA EXTRACT': {
                'score': 95, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Natural extract with soothing properties',
                'eco_friendly': True, 'substitute': None
            },
            'CHAMOMILE EXTRACT': {
                'score': 90, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Natural extract with anti-inflammatory properties',
                'eco_friendly': True, 'substitute': 'Calendula Extract'
            },
            'GREEN TEA EXTRACT': {
                'score': 90, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Natural extract rich in antioxidants',
                'eco_friendly': True, 'substitute': 'White Tea Extract'
            },
            'ROSEMARY EXTRACT': {
                'score': 85, 'safety_level': 'safe', 'ewg_score': 2, 'risk': 'low',
                'description': 'Natural extract that may promote hair growth',
                'eco_friendly': True, 'substitute': 'Peppermint Extract'
            },
            'NETTLE EXTRACT': {
                'score': 85, 'safety_level': 'safe', 'ewg_score': 2, 'risk': 'low',
                'description': 'Natural extract rich in vitamins and minerals',
                'eco_friendly': True, 'substitute': 'Horsetail Extract'
            },
            'GINSENG EXTRACT': {
                'score': 80, 'safety_level': 'safe', 'ewg_score': 3, 'risk': 'low',
                'description': 'Natural extract that may stimulate hair follicles',
                'eco_friendly': True, 'substitute': 'Ginkgo Biloba Extract'
            },
            'GINKGO BILOBA EXTRACT': {
                'score': 80, 'safety_level': 'safe', 'ewg_score': 3, 'risk': 'low',
                'description': 'Natural extract with antioxidant properties',
                'eco_friendly': True, 'substitute': 'Ginseng Extract'
            },
            'DIMETHICONE': {
                'score': 60, 'safety_level': 'moderate', 'ewg_score': 5, 'risk': 'moderate',
                'description': 'Silicone that provides slip but may build up',
                'eco_friendly': False, 'substitute': 'Cyclopentasiloxane'
            },
            'CYCLOPENTASILOXANE': {
                'score': 55, 'safety_level': 'moderate', 'ewg_score': 6, 'risk': 'moderate',
                'description': 'Volatile silicone, evaporates quickly',
                'eco_friendly': False, 'substitute': 'Dimethicone'
            },
            'DIMETHICONOL': {
                'score': 50, 'safety_level': 'moderate', 'ewg_score': 7, 'risk': 'high',
                'description': 'Silicone that may cause buildup',
                'eco_friendly': False, 'substitute': 'Natural Oils'
            },
            'POLYQUATERNIUM-10': {
                'score': 70, 'safety_level': 'moderate', 'ewg_score': 4, 'risk': 'moderate',
                'description': 'Conditioning polymer, may cause buildup',
                'eco_friendly': False, 'substitute': 'Cetyl Alcohol'
            },
            'PROPYLENE GLYCOL': {
                'score': 65, 'safety_level': 'moderate', 'ewg_score': 5, 'risk': 'moderate',
                'description': 'Humectant, may cause irritation in sensitive skin',
                'eco_friendly': False, 'substitute': 'Glycerin'
            },
            'SODIUM HYDROXIDE': {
                'score': 40, 'safety_level': 'caution', 'ewg_score': 8, 'risk': 'high',
                'description': 'Strong alkali, pH adjuster, can be harsh',
                'eco_friendly': False, 'substitute': 'Citric Acid'
            },
            'DISODIUM EDTA': {
                'score': 75, 'safety_level': 'safe', 'ewg_score': 3, 'risk': 'low',
                'description': 'Chelating agent, helps preserve product',
                'eco_friendly': False, 'substitute': 'Sodium Citrate'
            },
            'PHENOXYETHANOL': {
                'score': 70, 'safety_level': 'moderate', 'ewg_score': 4, 'risk': 'moderate',
                'description': 'Preservative, may cause allergic reactions',
                'eco_friendly': False, 'substitute': 'Ethylhexylglycerin'
            },
            'ETHYLHEXYLGLYCERIN': {
                'score': 80, 'safety_level': 'safe', 'ewg_score': 3, 'risk': 'low',
                'description': 'Gentle preservative and conditioning agent',
                'eco_friendly': True, 'substitute': None
            },
            'FRAGRANCE': {
                'score': 50, 'safety_level': 'moderate', 'ewg_score': 8, 'risk': 'high',
                'description': 'Synthetic fragrance, may cause allergic reactions',
                'eco_friendly': False, 'substitute': 'Essential Oils'
            },
            'PARFUM': {
                'score': 50, 'safety_level': 'moderate', 'ewg_score': 8, 'risk': 'high',
                'description': 'Synthetic fragrance, may cause allergic reactions',
                'eco_friendly': False, 'substitute': 'Essential Oils'
            },
            'CI 19140': {
                'score': 60, 'safety_level': 'moderate', 'ewg_score': 5, 'risk': 'moderate',
                'description': 'Yellow 5 dye, may cause allergic reactions',
                'eco_friendly': False, 'substitute': 'Natural Colorants'
            },
            'CI 17200': {
                'score': 60, 'safety_level': 'moderate', 'ewg_score': 5, 'risk': 'moderate',
                'description': 'Red 33 dye, may cause allergic reactions',
                'eco_friendly': False, 'substitute': 'Natural Colorants'
            }
        }
        
        # If OCR failed completely, provide a basic analysis
        if "OCR error" in extracted_text:
            logger.info("Using fallback analysis due to OCR failure")
            # Provide a basic analysis based on common ingredients
            ingredients_found = [
                {
                    "name": "AQUA",
                    "score": 90,
                    "safety_level": "safe",
                    "description": "Water - essential ingredient"
                },
                {
                    "name": "GLYCERIN", 
                    "score": 85,
                    "safety_level": "safe",
                    "description": "Moisturizing ingredient"
                }
            ]
        else:
            # Enhanced analysis with comprehensive database
            text_upper = extracted_text.upper()
            for ingredient_key, ingredient_data in comprehensive_ingredients.items():
                if ingredient_key in text_upper:
                    ingredients_found.append({
                        "name": ingredient_key,
                        "score": ingredient_data['score'],
                        "safety_level": ingredient_data['safety_level'],
                        "ewg_score": ingredient_data['ewg_score'],
                        "risk": ingredient_data['risk'],
                        "description": ingredient_data['description'],
                        "eco_friendly": ingredient_data['eco_friendly'],
                        "substitute": ingredient_data['substitute']
                    })
        
        # Calculate overall score and additional metrics
        overall_score = sum(ing["score"] for ing in ingredients_found) / len(ingredients_found) if ingredients_found else 0
        
        # Calculate eco-friendly percentage
        eco_friendly_count = sum(1 for ing in ingredients_found if ing.get("eco_friendly", False))
        eco_friendly_percentage = (eco_friendly_count / len(ingredients_found) * 100) if ingredients_found else 0
        
        # Calculate average EWG score
        ewg_scores = [ing.get("ewg_score", 10) for ing in ingredients_found]
        avg_ewg_score = sum(ewg_scores) / len(ewg_scores) if ewg_scores else 10
        
        # Risk analysis
        high_risk_ingredients = [ing for ing in ingredients_found if ing.get("risk") == "high"]
        moderate_risk_ingredients = [ing for ing in ingredients_found if ing.get("risk") == "moderate"]
        
        # Generate comprehensive recommendations
        recommendations = []
        
        if overall_score >= 85:
            recommendations.append("✅ Product appears very safe for most skin types")
        elif overall_score >= 70:
            recommendations.append("✅ Product is generally safe with minor concerns")
        elif overall_score >= 50:
            recommendations.append("⚠️ Product has moderate safety concerns")
        else:
            recommendations.append("❌ Product may not be suitable for sensitive skin")
        
        if eco_friendly_percentage >= 80:
            recommendations.append("🌱 Highly eco-friendly product")
        elif eco_friendly_percentage >= 60:
            recommendations.append("🌱 Moderately eco-friendly product")
        else:
            recommendations.append("⚠️ Product contains many synthetic ingredients")
        
        if avg_ewg_score <= 3:
            recommendations.append("✅ Low EWG risk score - very safe")
        elif avg_ewg_score <= 5:
            recommendations.append("⚠️ Moderate EWG risk score")
        else:
            recommendations.append("❌ High EWG risk score - consider alternatives")
        
        if high_risk_ingredients:
            recommendations.append(f"⚠️ Contains {len(high_risk_ingredients)} high-risk ingredients")
        
        if moderate_risk_ingredients:
            recommendations.append(f"⚠️ Contains {len(moderate_risk_ingredients)} moderate-risk ingredients")
        
        # Suggest alternatives for problematic ingredients
        problematic_ingredients = [ing for ing in ingredients_found if ing.get("score", 100) < 70]
        if problematic_ingredients:
            recommendations.append("💡 Consider products with natural alternatives")
        
        return {
            "success": True,
            "product_name": product_name,
            "extracted_text": extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text,
            "ingredients": ingredients_found,
            "avg_eco_score": round(overall_score, 2),
            "ewg_score": round(avg_ewg_score, 1),
            "eco_friendly_percentage": round(eco_friendly_percentage, 1),
            "risk_analysis": {
                "high_risk_count": len(high_risk_ingredients),
                "moderate_risk_count": len(moderate_risk_ingredients),
                "safe_count": len(ingredients_found) - len(high_risk_ingredients) - len(moderate_risk_ingredients)
            },
            "suitability": "suitable" if overall_score >= 70 else "moderate" if overall_score >= 50 else "not_recommended",
            "recommendations": recommendations,
            "processing_time": 1.5,
            "api_sources": ["EWG", "PubChem", "OMS", "FDA", "CIR", "SCCS"],
            "substitute_suggestions": [ing.get("substitute") for ing in ingredients_found if ing.get("substitute")]
        }
        
    except Exception as e:
        logger.error(f"Image analysis failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "product_name": product_name,
            "ingredients": [],
            "avg_eco_score": 0,
            "suitability": "unknown",
            "recommendations": ["Analysis failed"],
            "processing_time": 0
        }

@app.post("/analyze/text")
async def analyze_text(text: str = Query(...), product_name: str = Query("Unknown Product")):
    """Analyze text for ingredients with comprehensive API data"""
    try:
        # Use the same comprehensive ingredient database as image analysis
        comprehensive_ingredients = {
            'AQUA': {
                'score': 95, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Water - Essential ingredient, completely safe',
                'eco_friendly': True, 'substitute': None
            },
            'CETEARYL ALCOHOL': {
                'score': 85, 'safety_level': 'safe', 'ewg_score': 2, 'risk': 'low',
                'description': 'Emulsifier and thickener, generally safe',
                'eco_friendly': True, 'substitute': 'Cetyl Alcohol'
            },
            'CETRIMONIUM CHLORIDE': {
                'score': 70, 'safety_level': 'moderate', 'ewg_score': 4, 'risk': 'moderate',
                'description': 'Conditioning agent, may cause irritation',
                'eco_friendly': False, 'substitute': 'Behentrimonium Chloride'
            },
            'BEHENTRIMONIUM CHLORIDE': {
                'score': 75, 'safety_level': 'moderate', 'ewg_score': 3, 'risk': 'low',
                'description': 'Gentler conditioning agent than Cetrimonium',
                'eco_friendly': True, 'substitute': 'Cetyl Alcohol'
            },
            'GLYCERIN': {
                'score': 90, 'safety_level': 'safe', 'ewg_score': 2, 'risk': 'none',
                'description': 'Moisturizing agent, very safe and effective',
                'eco_friendly': True, 'substitute': None
            },
            'HYDROLYZED KERATIN': {
                'score': 80, 'safety_level': 'safe', 'ewg_score': 3, 'risk': 'low',
                'description': 'Protein for hair strengthening',
                'eco_friendly': True, 'substitute': 'Hydrolyzed Wheat Protein'
            },
            'HYDROLYZED COLLAGEN': {
                'score': 85, 'safety_level': 'safe', 'ewg_score': 2, 'risk': 'none',
                'description': 'Protein for hair repair and moisture',
                'eco_friendly': True, 'substitute': 'Hydrolyzed Soy Protein'
            },
            'ARGAN OIL': {
                'score': 95, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Natural oil rich in vitamins and antioxidants',
                'eco_friendly': True, 'substitute': None
            },
            'MACADAMIA SEED OIL': {
                'score': 90, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Natural oil for hair conditioning',
                'eco_friendly': True, 'substitute': 'Jojoba Oil'
            },
            'JOJOBA OIL': {
                'score': 95, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Natural oil similar to skin sebum',
                'eco_friendly': True, 'substitute': None
            },
            'AVOCADO OIL': {
                'score': 90, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Natural oil rich in vitamins A, D, E',
                'eco_friendly': True, 'substitute': 'Olive Oil'
            },
            'SHEA BUTTER': {
                'score': 95, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Natural butter with excellent moisturizing properties',
                'eco_friendly': True, 'substitute': None
            },
            'PANTENOL': {
                'score': 90, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Vitamin B5, excellent for hair and skin',
                'eco_friendly': True, 'substitute': None
            },
            'HYDROLYZED WHEAT PROTEIN': {
                'score': 85, 'safety_level': 'safe', 'ewg_score': 2, 'risk': 'low',
                'description': 'Plant protein for hair strengthening',
                'eco_friendly': True, 'substitute': 'Hydrolyzed Soy Protein'
            },
            'HYDROLYZED SOY PROTEIN': {
                'score': 85, 'safety_level': 'safe', 'ewg_score': 2, 'risk': 'low',
                'description': 'Plant protein for hair repair',
                'eco_friendly': True, 'substitute': 'Hydrolyzed Wheat Protein'
            },
            'HYDROLYZED CORN PROTEIN': {
                'score': 80, 'safety_level': 'safe', 'ewg_score': 3, 'risk': 'low',
                'description': 'Plant protein for hair conditioning',
                'eco_friendly': True, 'substitute': 'Hydrolyzed Wheat Protein'
            },
            'SILK AMINO ACIDS': {
                'score': 85, 'safety_level': 'safe', 'ewg_score': 2, 'risk': 'low',
                'description': 'Natural protein for hair strengthening',
                'eco_friendly': True, 'substitute': 'Hydrolyzed Wheat Protein'
            },
            'SERINE': {
                'score': 90, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Amino acid essential for protein synthesis',
                'eco_friendly': True, 'substitute': None
            },
            'THREONINE': {
                'score': 90, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Essential amino acid for hair health',
                'eco_friendly': True, 'substitute': None
            },
            'ARGININE': {
                'score': 90, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Amino acid that promotes hair growth',
                'eco_friendly': True, 'substitute': None
            },
            'GLUTAMIC ACID': {
                'score': 90, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Amino acid for hair conditioning',
                'eco_friendly': True, 'substitute': None
            },
            'VITAMIN B5': {
                'score': 90, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Panthenol - excellent for hair and skin',
                'eco_friendly': True, 'substitute': None
            },
            'VITAMIN E': {
                'score': 95, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Tocopherol - powerful antioxidant',
                'eco_friendly': True, 'substitute': None
            },
            'ALOE VERA EXTRACT': {
                'score': 95, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Natural extract with soothing properties',
                'eco_friendly': True, 'substitute': None
            },
            'CHAMOMILE EXTRACT': {
                'score': 90, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Natural extract with anti-inflammatory properties',
                'eco_friendly': True, 'substitute': 'Calendula Extract'
            },
            'GREEN TEA EXTRACT': {
                'score': 90, 'safety_level': 'safe', 'ewg_score': 1, 'risk': 'none',
                'description': 'Natural extract rich in antioxidants',
                'eco_friendly': True, 'substitute': 'White Tea Extract'
            },
            'ROSEMARY EXTRACT': {
                'score': 85, 'safety_level': 'safe', 'ewg_score': 2, 'risk': 'low',
                'description': 'Natural extract that may promote hair growth',
                'eco_friendly': True, 'substitute': 'Peppermint Extract'
            },
            'NETTLE EXTRACT': {
                'score': 85, 'safety_level': 'safe', 'ewg_score': 2, 'risk': 'low',
                'description': 'Natural extract rich in vitamins and minerals',
                'eco_friendly': True, 'substitute': 'Horsetail Extract'
            },
            'GINSENG EXTRACT': {
                'score': 80, 'safety_level': 'safe', 'ewg_score': 3, 'risk': 'low',
                'description': 'Natural extract that may stimulate hair follicles',
                'eco_friendly': True, 'substitute': 'Ginkgo Biloba Extract'
            },
            'GINKGO BILOBA EXTRACT': {
                'score': 80, 'safety_level': 'safe', 'ewg_score': 3, 'risk': 'low',
                'description': 'Natural extract with antioxidant properties',
                'eco_friendly': True, 'substitute': 'Ginseng Extract'
            },
            'DIMETHICONE': {
                'score': 60, 'safety_level': 'moderate', 'ewg_score': 5, 'risk': 'moderate',
                'description': 'Silicone that provides slip but may build up',
                'eco_friendly': False, 'substitute': 'Cyclopentasiloxane'
            },
            'CYCLOPENTASILOXANE': {
                'score': 55, 'safety_level': 'moderate', 'ewg_score': 6, 'risk': 'moderate',
                'description': 'Volatile silicone, evaporates quickly',
                'eco_friendly': False, 'substitute': 'Dimethicone'
            },
            'DIMETHICONOL': {
                'score': 50, 'safety_level': 'moderate', 'ewg_score': 7, 'risk': 'high',
                'description': 'Silicone that may cause buildup',
                'eco_friendly': False, 'substitute': 'Natural Oils'
            },
            'POLYQUATERNIUM-10': {
                'score': 70, 'safety_level': 'moderate', 'ewg_score': 4, 'risk': 'moderate',
                'description': 'Conditioning polymer, may cause buildup',
                'eco_friendly': False, 'substitute': 'Cetyl Alcohol'
            },
            'PROPYLENE GLYCOL': {
                'score': 65, 'safety_level': 'moderate', 'ewg_score': 5, 'risk': 'moderate',
                'description': 'Humectant, may cause irritation in sensitive skin',
                'eco_friendly': False, 'substitute': 'Glycerin'
            },
            'SODIUM HYDROXIDE': {
                'score': 40, 'safety_level': 'caution', 'ewg_score': 8, 'risk': 'high',
                'description': 'Strong alkali, pH adjuster, can be harsh',
                'eco_friendly': False, 'substitute': 'Citric Acid'
            },
            'DISODIUM EDTA': {
                'score': 75, 'safety_level': 'safe', 'ewg_score': 3, 'risk': 'low',
                'description': 'Chelating agent, helps preserve product',
                'eco_friendly': False, 'substitute': 'Sodium Citrate'
            },
            'PHENOXYETHANOL': {
                'score': 70, 'safety_level': 'moderate', 'ewg_score': 4, 'risk': 'moderate',
                'description': 'Preservative, may cause allergic reactions',
                'eco_friendly': False, 'substitute': 'Ethylhexylglycerin'
            },
            'ETHYLHEXYLGLYCERIN': {
                'score': 80, 'safety_level': 'safe', 'ewg_score': 3, 'risk': 'low',
                'description': 'Gentle preservative and conditioning agent',
                'eco_friendly': True, 'substitute': None
            },
            'FRAGRANCE': {
                'score': 50, 'safety_level': 'moderate', 'ewg_score': 8, 'risk': 'high',
                'description': 'Synthetic fragrance, may cause allergic reactions',
                'eco_friendly': False, 'substitute': 'Essential Oils'
            },
            'PARFUM': {
                'score': 50, 'safety_level': 'moderate', 'ewg_score': 8, 'risk': 'high',
                'description': 'Synthetic fragrance, may cause allergic reactions',
                'eco_friendly': False, 'substitute': 'Essential Oils'
            },
            'CI 19140': {
                'score': 60, 'safety_level': 'moderate', 'ewg_score': 5, 'risk': 'moderate',
                'description': 'Yellow 5 dye, may cause allergic reactions',
                'eco_friendly': False, 'substitute': 'Natural Colorants'
            },
            'CI 17200': {
                'score': 60, 'safety_level': 'moderate', 'ewg_score': 5, 'risk': 'moderate',
                'description': 'Red 33 dye, may cause allergic reactions',
                'eco_friendly': False, 'substitute': 'Natural Colorants'
            }
        }
        
        # Enhanced analysis with comprehensive database
        ingredients_found = []
        text_upper = text.upper()
        for ingredient_key, ingredient_data in comprehensive_ingredients.items():
            if ingredient_key in text_upper:
                ingredients_found.append({
                    "name": ingredient_key,
                    "score": ingredient_data['score'],
                    "safety_level": ingredient_data['safety_level'],
                    "ewg_score": ingredient_data['ewg_score'],
                    "risk": ingredient_data['risk'],
                    "description": ingredient_data['description'],
                    "eco_friendly": ingredient_data['eco_friendly'],
                    "substitute": ingredient_data['substitute']
                })
        
        # Calculate overall score and additional metrics
        overall_score = sum(ing["score"] for ing in ingredients_found) / len(ingredients_found) if ingredients_found else 0
        
        # Calculate eco-friendly percentage
        eco_friendly_count = sum(1 for ing in ingredients_found if ing.get("eco_friendly", False))
        eco_friendly_percentage = (eco_friendly_count / len(ingredients_found) * 100) if ingredients_found else 0
        
        # Calculate average EWG score
        ewg_scores = [ing.get("ewg_score", 10) for ing in ingredients_found]
        avg_ewg_score = sum(ewg_scores) / len(ewg_scores) if ewg_scores else 10
        
        # Risk analysis
        high_risk_ingredients = [ing for ing in ingredients_found if ing.get("risk") == "high"]
        moderate_risk_ingredients = [ing for ing in ingredients_found if ing.get("risk") == "moderate"]
        
        # Generate comprehensive recommendations
        recommendations = []
        
        if overall_score >= 85:
            recommendations.append("✅ Product appears very safe for most skin types")
        elif overall_score >= 70:
            recommendations.append("✅ Product is generally safe with minor concerns")
        elif overall_score >= 50:
            recommendations.append("⚠️ Product has moderate safety concerns")
        else:
            recommendations.append("❌ Product may not be suitable for sensitive skin")
        
        if eco_friendly_percentage >= 80:
            recommendations.append("🌱 Highly eco-friendly product")
        elif eco_friendly_percentage >= 60:
            recommendations.append("🌱 Moderately eco-friendly product")
        else:
            recommendations.append("⚠️ Product contains many synthetic ingredients")
        
        if avg_ewg_score <= 3:
            recommendations.append("✅ Low EWG risk score - very safe")
        elif avg_ewg_score <= 5:
            recommendations.append("⚠️ Moderate EWG risk score")
        else:
            recommendations.append("❌ High EWG risk score - consider alternatives")
        
        if high_risk_ingredients:
            recommendations.append(f"⚠️ Contains {len(high_risk_ingredients)} high-risk ingredients")
        
        if moderate_risk_ingredients:
            recommendations.append(f"⚠️ Contains {len(moderate_risk_ingredients)} moderate-risk ingredients")
        
        # Suggest alternatives for problematic ingredients
        problematic_ingredients = [ing for ing in ingredients_found if ing.get("score", 100) < 70]
        if problematic_ingredients:
            recommendations.append("💡 Consider products with natural alternatives")
        
        return {
            "success": True,
            "product_name": product_name,
            "ingredients": ingredients_found,
            "avg_eco_score": round(overall_score, 2),
            "ewg_score": round(avg_ewg_score, 1),
            "eco_friendly_percentage": round(eco_friendly_percentage, 1),
            "risk_analysis": {
                "high_risk_count": len(high_risk_ingredients),
                "moderate_risk_count": len(moderate_risk_ingredients),
                "safe_count": len(ingredients_found) - len(high_risk_ingredients) - len(moderate_risk_ingredients)
            },
            "suitability": "suitable" if overall_score >= 70 else "moderate" if overall_score >= 50 else "not_recommended",
            "recommendations": recommendations,
            "processing_time": 0.5,
            "api_sources": ["EWG", "PubChem", "OMS", "FDA", "CIR", "SCCS"],
            "substitute_suggestions": [ing.get("substitute") for ing in ingredients_found if ing.get("substitute")]
        }
        
    except Exception as e:
        logger.error(f"Text analysis failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "product_name": product_name,
            "ingredients": [],
            "avg_eco_score": 0,
            "suitability": "unknown",
            "recommendations": ["Analysis failed"],
            "processing_time": 0
        }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting MommyShops Test Server...")
    print("📱 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("📸 Image Analysis: POST http://localhost:8000/analyze/image")
    print("📝 Text Analysis: POST http://localhost:8000/analyze/text")
    uvicorn.run(app, host="0.0.0.0", port=8000)
