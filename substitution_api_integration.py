"""
Integration module for enhanced substitution mapping with existing APIs
Provides seamless integration with the current MommyShops API structure
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from enhanced_substitution_mapping import (
    EnhancedSubstitutionMapper, 
    get_enhanced_substitutes,
    suggest_safer_alternatives
)
from api_utils_production import fetch_ingredient_data
from database import get_ingredient_data

logger = logging.getLogger(__name__)

class SubstitutionAPIIntegration:
    """Integration layer for enhanced substitution mapping with existing APIs"""
    
    def __init__(self):
        self.mapper = EnhancedSubstitutionMapper()
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour cache
    
    async def analyze_and_suggest_substitutes(self, 
                                            ingredients: List[str],
                                            user_conditions: List[str] = None,
                                            include_safety_analysis: bool = True) -> Dict[str, Any]:
        """
        Comprehensive analysis and substitution suggestions using enhanced ML system
        
        Args:
            ingredients: List of ingredients to analyze
            user_conditions: User's skin conditions or concerns
            include_safety_analysis: Whether to include detailed safety analysis
            
        Returns:
            Comprehensive analysis with substitution suggestions
        """
        logger.info(f"Analyzing {len(ingredients)} ingredients for substitutions")
        
        # Step 1: Analyze ingredients for safety issues
        safety_analysis = []
        problematic_ingredients = []
        
        if include_safety_analysis:
            for ingredient in ingredients:
                try:
                    # Get ingredient data from existing API
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        data = await fetch_ingredient_data(ingredient, client)
                    
                    safety_score = self._calculate_quick_safety_score(data)
                    risk_level = data.get('risk_level', 'unknown')
                    eco_score = data.get('eco_score', 50.0)
                    
                    safety_analysis.append({
                        'ingredient': ingredient,
                        'safety_score': safety_score,
                        'risk_level': risk_level,
                        'eco_score': eco_score,
                        'is_problematic': safety_score < 70 or risk_level.lower() in ['high', 'alto'],
                        'sources': data.get('sources', []),
                        'risks_detailed': data.get('risks_detailed', ''),
                        'benefits': data.get('benefits', '')
                    })
                    
                    if safety_score < 70 or risk_level.lower() in ['high', 'alto']:
                        problematic_ingredients.append(ingredient)
                        
                except Exception as e:
                    logger.warning(f"Failed to analyze {ingredient}: {e}")
                    safety_analysis.append({
                        'ingredient': ingredient,
                        'safety_score': 50.0,
                        'risk_level': 'unknown',
                        'eco_score': 50.0,
                        'is_problematic': True,
                        'sources': [],
                        'risks_detailed': 'Analysis failed',
                        'benefits': 'Unknown'
                    })
                    problematic_ingredients.append(ingredient)
        
        # Step 2: Get enhanced substitution recommendations
        substitution_mappings = {}
        if problematic_ingredients:
            try:
                substitution_mappings = await self.mapper.generate_substitution_mapping(
                    problematic_ingredients, 
                    user_conditions
                )
            except Exception as e:
                logger.error(f"Failed to generate substitution mappings: {e}")
        
        # Step 3: Generate product recommendations
        product_recommendations = await self._generate_product_recommendations(
            ingredients, user_conditions
        )
        
        # Step 4: Compile comprehensive response
        response = {
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'total_ingredients': len(ingredients),
            'problematic_ingredients': len(problematic_ingredients),
            'safety_analysis': safety_analysis,
            'substitution_mappings': self._serialize_substitution_mappings(substitution_mappings),
            'product_recommendations': product_recommendations,
            'summary': self._generate_analysis_summary(safety_analysis, substitution_mappings)
        }
        
        return response
    
    def _calculate_quick_safety_score(self, data: Dict) -> float:
        """Calculate a quick safety score from API data"""
        score = 50.0  # Base score
        
        # Risk level scoring
        risk_level = data.get('risk_level', '').lower()
        if risk_level in ['safe', 'seguro']:
            score += 30
        elif risk_level in ['low', 'bajo']:
            score += 20
        elif risk_level in ['moderate', 'moderado']:
            score += 10
        elif risk_level in ['high', 'alto']:
            score -= 20
        
        # Eco score contribution
        eco_score = data.get('eco_score', 50.0)
        if eco_score:
            score += (eco_score - 50) * 0.3
        
        # Source reliability bonus
        sources = data.get('sources', '')
        if 'FDA' in sources:
            score += 10
        if 'CIR' in sources:
            score += 5
        if 'EWG' in sources:
            score += 5
        
        return max(0, min(100, score))
    
    async def _generate_product_recommendations(self, 
                                              ingredients: List[str],
                                              user_conditions: List[str] = None) -> List[Dict[str, Any]]:
        """Generate product recommendations based on safer ingredients"""
        # This would integrate with your existing product recommendation system
        # For now, return a placeholder structure
        return [
            {
                'product_id': 'example_1',
                'name': 'Producto Recomendado 1',
                'brand': 'Marca Segura',
                'eco_score': 85.0,
                'risk_level': 'bajo',
                'reason': 'Contiene ingredientes seguros y ecológicos',
                'ingredients': ['glicerina', 'ácido hialurónico', 'vitamina E'],
                'category': 'hidratante'
            }
        ]
    
    def _serialize_substitution_mappings(self, mappings: Dict) -> Dict[str, Any]:
        """Convert substitution mappings to serializable format"""
        serialized = {}
        for ingredient, mapping in mappings.items():
            serialized[ingredient] = {
                'original': mapping.original,
                'substitutes': [
                    {
                        'ingredient': sub.ingredient,
                        'similarity_score': sub.similarity_score,
                        'safety_improvement': sub.safety_improvement,
                        'functional_similarity': sub.functional_similarity,
                        'eco_improvement': sub.eco_improvement,
                        'risk_reduction': sub.risk_reduction,
                        'reason': sub.reason,
                        'confidence': sub.confidence,
                        'sources': sub.sources
                    }
                    for sub in mapping.substitutes
                ],
                'safety_justification': mapping.safety_justification,
                'functional_equivalence': mapping.functional_equivalence,
                'confidence_score': mapping.confidence_score,
                'last_updated': mapping.last_updated.isoformat()
            }
        return serialized
    
    def _generate_analysis_summary(self, 
                                 safety_analysis: List[Dict],
                                 substitution_mappings: Dict) -> Dict[str, Any]:
        """Generate a summary of the analysis"""
        total_ingredients = len(safety_analysis)
        problematic_count = sum(1 for item in safety_analysis if item['is_problematic'])
        safe_count = total_ingredients - problematic_count
        
        avg_safety_score = sum(item['safety_score'] for item in safety_analysis) / total_ingredients if total_ingredients > 0 else 0
        
        substitution_count = len(substitution_mappings)
        total_substitutes = sum(len(mapping.substitutes) for mapping in substitution_mappings.values())
        
        return {
            'total_ingredients_analyzed': total_ingredients,
            'safe_ingredients': safe_count,
            'problematic_ingredients': problematic_count,
            'average_safety_score': round(avg_safety_score, 1),
            'ingredients_with_substitutes': substitution_count,
            'total_substitute_options': total_substitutes,
            'recommendation': self._generate_recommendation_text(problematic_count, substitution_count)
        }
    
    def _generate_recommendation_text(self, problematic_count: int, substitution_count: int) -> str:
        """Generate human-readable recommendation text"""
        if problematic_count == 0:
            return "Todos los ingredientes son seguros. No se requieren sustituciones."
        elif substitution_count == 0:
            return f"Se encontraron {problematic_count} ingredientes problemáticos, pero no se pudieron encontrar sustitutos seguros."
        else:
            return f"Se encontraron {problematic_count} ingredientes problemáticos con {substitution_count} opciones de sustitución disponibles."

# API Endpoint Functions for integration with FastAPI
async def enhanced_substitute_analysis(ingredients: List[str], 
                                     user_conditions: List[str] = None) -> Dict[str, Any]:
    """API endpoint for enhanced substitution analysis"""
    integration = SubstitutionAPIIntegration()
    return await integration.analyze_and_suggest_substitutes(ingredients, user_conditions)

async def get_safer_alternatives(ingredients: List[str],
                               user_conditions: List[str] = None) -> List[Dict[str, Any]]:
    """API endpoint for getting safer alternatives"""
    return await suggest_safer_alternatives(ingredients, user_conditions)

async def batch_substitute_analysis(ingredient_batches: List[List[str]],
                                  user_conditions: List[str] = None) -> List[Dict[str, Any]]:
    """API endpoint for batch analysis of multiple ingredient lists"""
    integration = SubstitutionAPIIntegration()
    results = []
    
    for batch in ingredient_batches:
        result = await integration.analyze_and_suggest_substitutes(batch, user_conditions)
        results.append(result)
    
    return results

# Integration with existing recommendation system
async def enhance_existing_recommendations(existing_recommendations: List[Dict[str, Any]],
                                         user_conditions: List[str] = None) -> List[Dict[str, Any]]:
    """Enhance existing product recommendations with substitution analysis"""
    enhanced_recommendations = []
    
    for rec in existing_recommendations:
        ingredients = rec.get('ingredients', [])
        if ingredients:
            # Get substitution analysis for this product's ingredients
            substitution_analysis = await get_enhanced_substitutes(ingredients, user_conditions)
            
            # Add substitution data to recommendation
            enhanced_rec = rec.copy()
            enhanced_rec['substitution_analysis'] = substitution_analysis
            enhanced_rec['has_safer_alternatives'] = len(substitution_analysis) > 0
            enhanced_recommendations.append(enhanced_rec)
        else:
            enhanced_recommendations.append(rec)
    
    return enhanced_recommendations

# Utility functions for easy integration
def get_substitution_confidence_score(substitution_mapping: Dict[str, Any]) -> float:
    """Get confidence score for a substitution mapping"""
    return substitution_mapping.get('confidence_score', 0.0)

def get_top_substitutes(substitution_mapping: Dict[str, Any], top_n: int = 3) -> List[Dict[str, Any]]:
    """Get top N substitutes from a substitution mapping"""
    substitutes = substitution_mapping.get('substitutes', [])
    return sorted(substitutes, key=lambda x: x.get('confidence', 0), reverse=True)[:top_n]

def is_ingredient_problematic(safety_analysis: List[Dict[str, Any]], ingredient: str) -> bool:
    """Check if an ingredient is considered problematic"""
    for analysis in safety_analysis:
        if analysis['ingredient'] == ingredient:
            return analysis['is_problematic']
    return False

if __name__ == "__main__":
    # Example usage
    async def main():
        integration = SubstitutionAPIIntegration()
        
        # Test ingredients
        test_ingredients = [
            "sodium lauryl sulfate",
            "parabens", 
            "formaldehyde",
            "glycerin",
            "hyaluronic acid"
        ]
        
        user_conditions = ["sensitive skin", "eczema"]
        
        # Get comprehensive analysis
        result = await integration.analyze_and_suggest_substitutes(
            test_ingredients, 
            user_conditions
        )
        
        print("=== ENHANCED SUBSTITUTION ANALYSIS ===")
        print(f"Total ingredients: {result['summary']['total_ingredients_analyzed']}")
        print(f"Problematic: {result['summary']['problematic_ingredients']}")
        print(f"Safe: {result['summary']['safe_ingredients']}")
        print(f"Average safety score: {result['summary']['average_safety_score']}")
        print(f"Recommendation: {result['summary']['recommendation']}")
        
        print("\n=== SUBSTITUTION MAPPINGS ===")
        for ingredient, mapping in result['substitution_mappings'].items():
            print(f"\n{ingredient}:")
            print(f"  Safety justification: {mapping['safety_justification']}")
            print(f"  Confidence: {mapping['confidence_score']:.2f}")
            print("  Top substitutes:")
            for i, sub in enumerate(mapping['substitutes'][:3], 1):
                print(f"    {i}. {sub['ingredient']} (confidence: {sub['confidence']:.2f})")
                print(f"       Reason: {sub['reason']}")
    
    asyncio.run(main())