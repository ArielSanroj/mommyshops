# Enhanced Ingredient Substitution Mapping System

## Overview

The Enhanced Substitution Mapping System leverages machine learning and multiple cosmetic safety standards to provide intelligent ingredient substitution recommendations. This system builds upon your existing APIs (FDA, EWG, CIR, SCCS, ICCR) to create a robust, ML-powered substitution database.

## Key Features

### 🤖 Machine Learning Integration
- **Sentence Transformers**: Uses `all-MiniLM-L6-v2` for semantic similarity matching
- **TF-IDF Fallback**: Robust text-based similarity when transformers are unavailable
- **Functional Category Matching**: Groups ingredients by cosmetic function (emollients, humectants, etc.)
- **Confidence Scoring**: ML-based confidence assessment for substitution recommendations

### 🛡️ Multi-Standard Safety Analysis
- **FDA**: Regulatory approval and safety (30% weight)
- **EWG**: Eco-friendliness and consumer safety (25% weight)
- **CIR**: Scientific safety assessment (20% weight)
- **SCCS**: EU safety evaluation (15% weight)
- **ICCR**: International harmonization (10% weight)

### 📊 Comprehensive Scoring
- **Safety Score**: 0-100 based on multiple safety standards
- **Functional Similarity**: How well substitutes match original function
- **Eco Improvement**: Environmental impact improvement
- **Risk Reduction**: Safety risk reduction assessment
- **Confidence Score**: Overall recommendation confidence

## Architecture

```
Enhanced Substitution System
├── enhanced_substitution_mapping.py    # Core ML substitution logic
├── substitution_api_integration.py     # API integration layer
├── substitution_endpoints.py          # FastAPI endpoints
└── test_enhanced_substitution.py      # Comprehensive testing
```

## API Endpoints

### 1. Comprehensive Analysis
```http
POST /substitution/analyze
```
Analyzes ingredients and provides substitution recommendations.

**Request:**
```json
{
  "ingredients": ["sodium lauryl sulfate", "parabens"],
  "user_conditions": ["sensitive skin", "eczema"],
  "include_safety_analysis": true
}
```

**Response:**
```json
{
  "analysis_timestamp": "2025-01-27T10:30:00Z",
  "total_ingredients": 2,
  "problematic_ingredients": 2,
  "safety_analysis": [...],
  "substitution_mappings": {
    "sodium lauryl sulfate": {
      "original": "sodium lauryl sulfate",
      "substitutes": [
        {
          "ingredient": "cocamidopropyl betaine",
          "similarity_score": 0.85,
          "safety_improvement": 25.3,
          "functional_similarity": 0.92,
          "eco_improvement": 15.2,
          "risk_reduction": 0.8,
          "reason": "funcionalmente similar, más seguro (+25.3 puntos), más ecológico (+15.2 puntos), menor riesgo",
          "confidence": 0.88,
          "sources": ["FDA", "CIR", "EWG"]
        }
      ],
      "safety_justification": "Los sustitutos son en promedio 25.3 puntos más seguros. Mejora ecológica promedio de 15.2 puntos. Reducción significativa del riesgo de seguridad. Basado en datos de CIR, EWG, FDA.",
      "functional_equivalence": 0.92,
      "confidence_score": 0.88,
      "last_updated": "2025-01-27T10:30:00Z"
    }
  },
  "product_recommendations": [...],
  "summary": {
    "total_ingredients_analyzed": 2,
    "safe_ingredients": 0,
    "problematic_ingredients": 2,
    "average_safety_score": 45.2,
    "ingredients_with_substitutes": 2,
    "total_substitute_options": 6,
    "recommendation": "Se encontraron 2 ingredientes problemáticos con 2 opciones de sustitución disponibles."
  }
}
```

### 2. Safer Alternatives
```http
POST /substitution/alternatives
```
Quick lookup for safer alternatives.

### 3. Batch Analysis
```http
POST /substitution/batch-analyze
```
Analyze multiple ingredient lists simultaneously.

### 4. Health Check
```http
GET /substitution/health
```
Check system health and ML model status.

### 5. Safety Standards Info
```http
GET /substitution/safety-standards
```
Get information about supported safety standards.

## Usage Examples

### Python Integration

```python
from substitution_api_integration import SubstitutionAPIIntegration

# Initialize integration
integration = SubstitutionAPIIntegration()

# Analyze ingredients
result = await integration.analyze_and_suggest_substitutes(
    ingredients=["sodium lauryl sulfate", "parabens"],
    user_conditions=["sensitive skin", "eczema"]
)

# Get safer alternatives
alternatives = await get_safer_alternatives(
    ingredients=["formaldehyde"],
    user_conditions=["allergies"]
)
```

### Direct ML Usage

```python
from enhanced_substitution_mapping import EnhancedSubstitutionMapper

# Initialize mapper
mapper = EnhancedSubstitutionMapper()

# Build safety database
await mapper.build_safety_database(["sodium lauryl sulfate", "parabens"])

# Find substitutes
substitutes = await mapper.find_substitutes(
    "sodium lauryl sulfate",
    user_conditions=["sensitive skin"],
    max_substitutes=5
)
```

## Functional Categories

The system recognizes these cosmetic ingredient categories:

- **Emollients**: Glycerin, squalane, ceramides, hyaluronic acid, dimethicone
- **Humectants**: Glycerin, hyaluronic acid, sodium hyaluronate, panthenol
- **Emulsifiers**: Lecithin, polysorbate, cetearyl alcohol, glyceryl stearate
- **Preservatives**: Phenoxyethanol, benzyl alcohol, sorbic acid, potassium sorbate
- **Antioxidants**: Vitamin E, vitamin C, ferulic acid, resveratrol
- **Surfactants**: Cocamidopropyl betaine, sodium lauryl sulfate, decyl glucoside
- **Fragrance**: Essential oils, natural fragrances, fragrance-free
- **Colorants**: Iron oxides, titanium dioxide, zinc oxide, natural colorants

## Safety Scoring Algorithm

The safety score (0-100) is calculated using:

1. **FDA Status** (30% weight): Approved = +30, Safe = +30, GRAS = +30
2. **EWG Concerns** (25% weight): Inverse of concern count
3. **Eco Score** (20% weight): Direct contribution from eco_score
4. **Risk Level** (15% weight): High = -20, Moderate = +10, Low = +20, Safe = +30
5. **Source Reliability** (10% weight): FDA = +10, CIR = +5, EWG = +5

## Machine Learning Models

### Primary Model
- **Sentence Transformer**: `all-MiniLM-L6-v2`
- **Purpose**: Semantic similarity matching
- **Fallback**: TF-IDF vectorization

### Similarity Calculation
```python
similarity_score = (functional_sim * 0.6 + safety_improvement_factor * 0.4)
confidence = (similarity_score * 0.4 + safety_improvement * 0.3 + risk_reduction * 0.3)
```

## Integration with Existing APIs

The system seamlessly integrates with your existing API infrastructure:

- **api_utils_production.py**: Uses existing `fetch_ingredient_data()`
- **database.py**: Leverages `normalize_ingredient_name()` and `get_ingredient_data()`
- **main.py**: Integrated via FastAPI router
- **Rate Limiting**: Inherits existing circuit breakers and rate limiters

## Testing

Run the comprehensive test suite:

```bash
python test_enhanced_substitution.py
```

Tests include:
- Basic substitution functionality
- Safety analysis
- Functional category matching
- Safety standards integration
- Batch analysis
- API endpoint functionality

## Performance Considerations

### Caching
- **Safety Profiles**: Cached for 1 hour
- **Substitution Mappings**: Cached for 24 hours
- **ML Embeddings**: Cached during session

### Rate Limiting
- Inherits existing API rate limits
- Circuit breakers prevent cascade failures
- Graceful degradation when services are unavailable

### Memory Usage
- Sentence transformer model: ~100MB
- TF-IDF vectorizer: ~50MB
- Safety database: ~10MB per 1000 ingredients

## Configuration

### Environment Variables
```bash
# Existing variables (inherited)
EWG_API_KEY=your_ewg_api_key
OLLAMA_API_KEY=your_ollama_api_key

# ML Model Configuration
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2
SUBSTITUTION_CACHE_TTL=3600
```

### Safety Standard Weights
```python
safety_standards = {
    'fda': {'weight': 0.3, 'safe_levels': ['approved', 'safe', 'generally recognized as safe']},
    'ewg': {'weight': 0.25, 'safe_levels': ['low hazard', 'no data available']},
    'cir': {'weight': 0.2, 'safe_levels': ['safe', 'safe with qualifications']},
    'sccs': {'weight': 0.15, 'safe_levels': ['safe', 'safe with restrictions']},
    'iccr': {'weight': 0.1, 'safe_levels': ['safe', 'approved']}
}
```

## Future Enhancements

### Planned Features
1. **User Preference Learning**: Adapt recommendations based on user feedback
2. **Regional Compliance**: Consider different regulatory requirements by region
3. **Real-time Updates**: Live updates from safety databases
4. **Advanced ML**: Custom models trained on cosmetic ingredient data
5. **Product Integration**: Direct product recommendation integration

### Extensibility
- **Custom Safety Standards**: Easy addition of new safety sources
- **Functional Categories**: Expandable category system
- **Scoring Algorithms**: Pluggable scoring mechanisms
- **ML Models**: Swappable similarity models

## Troubleshooting

### Common Issues

1. **Model Loading Failures**
   - Check sentence-transformers installation
   - Verify model download permissions
   - System falls back to TF-IDF automatically

2. **API Integration Errors**
   - Verify existing API credentials
   - Check rate limiting status
   - Review circuit breaker logs

3. **Memory Issues**
   - Reduce batch sizes
   - Clear caches periodically
   - Monitor memory usage

### Debug Mode
```python
import logging
logging.getLogger("enhanced_substitution_mapping").setLevel(logging.DEBUG)
```

## Support

For issues or questions:
1. Check the test suite output
2. Review API health endpoints
3. Examine application logs
4. Verify API credentials and connectivity

The Enhanced Substitution Mapping System provides a robust, ML-powered foundation for intelligent ingredient substitution while maintaining compatibility with your existing infrastructure.