"""
Unit tests for ingredient service
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import pytest_asyncio
from backend_python.services.ingredient_service import IngredientService

class TestIngredientService:
    """Test ingredient service functionality"""
    
    @pytest.fixture
    def ingredient_service(self):
        """Create ingredient service instance"""
        return IngredientService()
    
    @pytest.mark.unit
    @pytest.mark.analysis
    def test_ingredient_service_initialization(self, ingredient_service):
        """Test ingredient service initialization"""
        assert ingredient_service is not None
    
    @pytest.mark.unit
    @pytest.mark.analysis
    @patch('backend_python.services.ingredient_service.fetch_ingredient_data')
    def test_analyze_ingredient_success(self, mock_fetch, ingredient_service):
        """Test successful ingredient analysis"""
        # Mock external API response
        mock_fetch.return_value = {
            "name": "Hyaluronic Acid",
            "risk_level": "low",
            "eco_score": 85.0,
            "benefits": "Hydrating",
            "risks": "None known",
            "sources": "EWG, FDA"
        }
        
        result = ingredient_service.analyze_ingredient("Hyaluronic Acid")
        
        assert result["name"] == "Hyaluronic Acid"
        assert result["risk_level"] == "low"
        assert result["eco_score"] == 85.0
        mock_fetch.assert_called_once_with("Hyaluronic Acid")
    
    @pytest.mark.unit
    @pytest.mark.analysis
    @patch('backend_python.services.ingredient_service.fetch_ingredient_data')
    def test_analyze_ingredient_failure(self, mock_fetch, ingredient_service):
        """Test ingredient analysis failure"""
        # Mock external API failure
        mock_fetch.side_effect = Exception("API error")
        
        result = ingredient_service.analyze_ingredient("Unknown Ingredient")
        
        assert result["name"] == "Unknown Ingredient"
        assert result["risk_level"] == "unknown"
        assert result["eco_score"] == 50.0
    
    @pytest.mark.unit
    @pytest.mark.analysis
    def test_analyze_ingredients_batch(self, ingredient_service):
        """Test batch ingredient analysis"""
        ingredients = ["Hyaluronic Acid", "Niacinamide", "Retinol"]
        
        with patch.object(ingredient_service, 'analyze_ingredient') as mock_analyze:
            mock_analyze.side_effect = [
                {"name": "Hyaluronic Acid", "risk_level": "low", "eco_score": 85.0},
                {"name": "Niacinamide", "risk_level": "low", "eco_score": 80.0},
                {"name": "Retinol", "risk_level": "medium", "eco_score": 60.0}
            ]
            
            results = ingredient_service.analyze_ingredients_batch(ingredients)
            
            assert len(results) == 3
            assert results[0]["name"] == "Hyaluronic Acid"
            assert results[1]["name"] == "Niacinamide"
            assert results[2]["name"] == "Retinol"
    
    @pytest.mark.unit
    @pytest.mark.analysis
    def test_calculate_average_eco_score(self, ingredient_service):
        """Test average eco score calculation"""
        ingredients = [
            {"name": "Ingredient 1", "eco_score": 80.0},
            {"name": "Ingredient 2", "eco_score": 70.0},
            {"name": "Ingredient 3", "eco_score": 90.0}
        ]
        
        avg_score = ingredient_service.calculate_average_eco_score(ingredients)
        
        assert avg_score == 80.0
    
    @pytest.mark.unit
    @pytest.mark.analysis
    def test_calculate_average_eco_score_empty(self, ingredient_service):
        """Test average eco score calculation with empty list"""
        ingredients = []
        
        avg_score = ingredient_service.calculate_average_eco_score(ingredients)
        
        assert avg_score == 50.0  # Default value
    
    @pytest.mark.unit
    @pytest.mark.analysis
    def test_determine_suitability(self, ingredient_service):
        """Test suitability determination"""
        # Test good suitability
        ingredients = [
            {"risk_level": "low", "eco_score": 85.0},
            {"risk_level": "low", "eco_score": 80.0}
        ]
        suitability = ingredient_service.determine_suitability(ingredients, "sensitive skin")
        assert suitability in ["excellent", "good"]
        
        # Test poor suitability
        ingredients = [
            {"risk_level": "high", "eco_score": 30.0},
            {"risk_level": "high", "eco_score": 25.0}
        ]
        suitability = ingredient_service.determine_suitability(ingredients, "sensitive skin")
        assert suitability in ["poor", "not recommended"]
    
    @pytest.mark.unit
    @pytest.mark.analysis
    def test_generate_recommendations(self, ingredient_service):
        """Test recommendation generation"""
        ingredients = [
            {"name": "Hyaluronic Acid", "risk_level": "low", "eco_score": 85.0},
            {"name": "Retinol", "risk_level": "medium", "eco_score": 60.0}
        ]
        
        recommendations = ingredient_service.generate_recommendations(ingredients, "sensitive skin")
        
        assert isinstance(recommendations, str)
        assert len(recommendations) > 0
    
    @pytest.mark.unit
    @pytest.mark.analysis
    def test_filter_problematic_ingredients(self, ingredient_service):
        """Test filtering problematic ingredients"""
        ingredients = [
            {"name": "Hyaluronic Acid", "risk_level": "low"},
            {"name": "Sodium Lauryl Sulfate", "risk_level": "high"},
            {"name": "Parabens", "risk_level": "high"},
            {"name": "Niacinamide", "risk_level": "low"}
        ]
        
        problematic = ingredient_service.filter_problematic_ingredients(ingredients)
        
        assert len(problematic) == 2
        assert problematic[0]["name"] == "Sodium Lauryl Sulfate"
        assert problematic[1]["name"] == "Parabens"
    
    @pytest.mark.unit
    @pytest.mark.analysis
    def test_validate_ingredient_name(self, ingredient_service):
        """Test ingredient name validation"""
        # Valid names
        assert ingredient_service.validate_ingredient_name("Hyaluronic Acid") == True
        assert ingredient_service.validate_ingredient_name("Vitamin C") == True
        assert ingredient_service.validate_ingredient_name("Retinol") == True
        
        # Invalid names
        assert ingredient_service.validate_ingredient_name("") == False
        assert ingredient_service.validate_ingredient_name("   ") == False
        assert ingredient_service.validate_ingredient_name("123") == False
    
    @pytest.mark.unit
    @pytest.mark.analysis
    def test_normalize_ingredient_name(self, ingredient_service):
        """Test ingredient name normalization"""
        # Test normalization
        assert ingredient_service.normalize_ingredient_name("  Hyaluronic Acid  ") == "Hyaluronic Acid"
        assert ingredient_service.normalize_ingredient_name("hyaluronic acid") == "Hyaluronic Acid"
        assert ingredient_service.normalize_ingredient_name("HYALURONIC ACID") == "Hyaluronic Acid"
    
    @pytest.mark.unit
    @pytest.mark.analysis
    def test_get_ingredient_synonyms(self, ingredient_service):
        """Test ingredient synonym retrieval"""
        synonyms = ingredient_service.get_ingredient_synonyms("Hyaluronic Acid")
        
        assert isinstance(synonyms, list)
        # Should include common variations
        assert any("hyaluronate" in synonym.lower() for synonym in synonyms)
    
    @pytest.mark.unit
    @pytest.mark.analysis
    def test_categorize_ingredient(self, ingredient_service):
        """Test ingredient categorization"""
        # Test different categories
        humectant = ingredient_service.categorize_ingredient("Hyaluronic Acid")
        assert "humectant" in humectant.lower()
        
        antioxidant = ingredient_service.categorize_ingredient("Vitamin C")
        assert "antioxidant" in antioxidant.lower()
        
        exfoliant = ingredient_service.categorize_ingredient("Salicylic Acid")
        assert "exfoliant" in exfoliant.lower()
