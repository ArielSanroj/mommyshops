#!/usr/bin/env python3
"""
Integration tests for image analysis functionality
Tests OCR, ingredient extraction, and analysis pipeline
"""

import os
import sys
import asyncio
import pytest
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io
import json

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_ocr_analysis import EnhancedOCRAnalysis
from google_vision_integration import GoogleVisionOCR
from product_recognition import ProductRecognitionEngine
from api_utils_production import fetch_ingredient_data
from database import SessionLocal, User
from unified_data_service import analyze_ingredients_unified

class TestImageAnalysisIntegration:
    """Integration tests for image analysis pipeline"""
    
    def setup_method(self):
        """Set up test environment"""
        self.ocr_analyzer = EnhancedOCRAnalysis()
        self.google_vision = GoogleVisionOCR()
        self.product_recognizer = ProductRecognitionEngine()
        
        # Create test image directory
        self.test_images_dir = Path("test_images")
        self.test_images_dir.mkdir(exist_ok=True)
    
    def teardown_method(self):
        """Clean up test environment"""
        # Clean up test images
        if self.test_images_dir.exists():
            for file in self.test_images_dir.glob("*.png"):
                file.unlink()
            self.test_images_dir.rmdir()
    
    def create_test_image(self, text: str, filename: str = "test_ingredients.png") -> str:
        """Create a test image with ingredient text"""
        # Create a white background image
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a default font, fallback to basic if not available
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        # Draw text
        draw.text((50, 50), text, fill='black', font=font)
        
        # Save image
        image_path = self.test_images_dir / filename
        img.save(image_path)
        return str(image_path)
    
    def test_enhanced_ocr_analysis(self):
        """Test enhanced OCR analysis functionality"""
        # Create test image with ingredient list
        ingredient_text = """INGREDIENTS:
        Aqua, Glycerin, Sodium Lauryl Sulfate,
        Cocamidopropyl Betaine, Parfum,
        Methylparaben, Propylparaben"""
        
        image_path = self.create_test_image(ingredient_text, "test_ocr.png")
        
        # Test OCR extraction
        result = self.ocr_analyzer.analyze_image(image_path)
        
        assert result is not None
        assert "ingredients" in result
        assert len(result["ingredients"]) > 0
        
        # Check if key ingredients were detected
        ingredients = [ing.lower() for ing in result["ingredients"]]
        assert any("glycerin" in ing for ing in ingredients)
        assert any("sodium" in ing for ing in ingredients)
    
    def test_google_vision_ocr(self):
        """Test Google Vision OCR integration"""
        if not self.google_vision.api_key:
            pytest.skip("Google Vision API key not configured")
        
        # Create test image
        ingredient_text = """INGREDIENTS:
        Water, Glycerin, Sodium Lauryl Sulfate,
        Cocamidopropyl Betaine, Fragrance"""
        
        image_path = self.create_test_image(ingredient_text, "test_google_vision.png")
        
        # Test Google Vision OCR
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        result = asyncio.run(self.google_vision.extract_text_from_image(image_data))
        
        assert result is not None
        assert len(result) > 0
        
        # Check if text was extracted
        full_text = " ".join(result).lower()
        assert "ingredients" in full_text or "glycerin" in full_text
    
    def test_product_recognition_engine(self):
        """Test product recognition engine"""
        # Create test image with product info
        product_text = """L'OREAL PARIS
        Revitalift Anti-Aging Cream
        INGREDIENTS:
        Aqua, Glycerin, Dimethicone,
        Retinol, Hyaluronic Acid"""
        
        image_path = self.create_test_image(product_text, "test_product.png")
        
        # Test product recognition
        result = asyncio.run(self.product_recognizer.analyze_product_image(image_path))
        
        assert result is not None
        assert result.brand is not None or result.product_name is not None
        assert len(result.ingredients) > 0
    
    def test_ingredient_analysis_pipeline(self):
        """Test complete ingredient analysis pipeline"""
        # Create test image
        ingredient_text = """INGREDIENTS:
        Aqua, Glycerin, Sodium Lauryl Sulfate,
        Methylparaben, Propylparaben"""
        
        image_path = self.create_test_image(ingredient_text, "test_pipeline.png")
        
        # Test OCR
        ocr_result = self.ocr_analyzer.analyze_image(image_path)
        assert ocr_result is not None
        
        # Test ingredient analysis
        ingredients = ocr_result.get("ingredients", [])
        if ingredients:
            # Test unified analysis
            analysis_result = asyncio.run(analyze_ingredients_unified(ingredients))
            assert analysis_result is not None
            assert "ingredients" in analysis_result
    
    def test_api_integration_mock(self):
        """Test API integration with mock data"""
        # Test ingredient data fetching
        test_ingredient = "glycerin"
        
        # This should work even without real API keys (using fallback)
        result = asyncio.run(fetch_ingredient_data(test_ingredient))
        
        # Should return some data structure
        assert result is not None
        assert isinstance(result, dict)
    
    def test_database_integration(self):
        """Test database integration"""
        # Test database connection
        with SessionLocal() as session:
            # Simple query to test connection
            result = session.execute("SELECT 1").scalar()
            assert result == 1
    
    def test_error_handling(self):
        """Test error handling in image analysis"""
        # Test with invalid image path
        invalid_path = "nonexistent_image.png"
        
        result = self.ocr_analyzer.analyze_image(invalid_path)
        assert result is None or "error" in result
    
    def test_multiple_image_formats(self):
        """Test analysis with different image formats"""
        formats = ["png", "jpg", "jpeg"]
        
        for fmt in formats:
            ingredient_text = f"Test ingredients for {fmt}"
            image_path = self.create_test_image(ingredient_text, f"test.{fmt}")
            
            result = self.ocr_analyzer.analyze_image(image_path)
            assert result is not None
    
    def test_large_image_handling(self):
        """Test handling of large images"""
        # Create a larger test image
        img = Image.new('RGB', (2000, 1500), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 32)
        except:
            font = ImageFont.load_default()
        
        draw.text((100, 100), "LARGE IMAGE TEST\nINGREDIENTS:\nAqua, Glycerin", fill='black', font=font)
        
        image_path = self.test_images_dir / "large_test.png"
        img.save(image_path)
        
        result = self.ocr_analyzer.analyze_image(str(image_path))
        assert result is not None

def run_integration_tests():
    """Run all integration tests"""
    print("🧪 Running MommyShops Integration Tests...")
    print("=" * 50)
    
    # Run pytest
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes"
    ])

def run_quick_test():
    """Run a quick functionality test"""
    print("⚡ Quick Integration Test")
    print("-" * 30)
    
    try:
        # Test OCR
        analyzer = EnhancedOCRAnalysis()
        print("✅ Enhanced OCR Analysis: Available")
        
        # Test Google Vision
        google_vision = GoogleVisionOCR()
        if google_vision.api_key:
            print("✅ Google Vision OCR: Configured")
        else:
            print("⚠️  Google Vision OCR: Not configured (API key missing)")
        
        # Test Product Recognition
        recognizer = ProductRecognitionEngine()
        print("✅ Product Recognition Engine: Available")
        
        # Test Database
        with SessionLocal() as session:
            session.execute("SELECT 1")
            print("✅ Database Connection: Working")
        
        print("\n🎉 All core components are available!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MommyShops Integration Tests")
    parser.add_argument("--quick", action="store_true", help="Run quick test only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.quick:
        success = run_quick_test()
        sys.exit(0 if success else 1)
    else:
        run_integration_tests()