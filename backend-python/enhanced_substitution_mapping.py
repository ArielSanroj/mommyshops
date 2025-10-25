"""
Enhanced Ingredient Substitution Mapping System
Leverages machine learning and multiple cosmetic safety standards for robust ingredient substitution.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Set, Any
from datetime import datetime, timedelta
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import httpx

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from api_utils_production import fetch_ingredient_data
try:
    from database import normalize_ingredient_name, get_ingredient_data
except ImportError:
    # Fallback for testing
    def normalize_ingredient_name(name):
        return name.lower().strip() if name else ""
    
    def get_ingredient_data(name):
        return {}

logger = logging.getLogger(__name__)

RISK_LEVEL_MAP = {
    "cancerigeno": 0.05,
    "cancerígeno": 0.05,
    "cancer": 0.05,
    "cancerous": 0.05,
    "riesgo alto": 0.2,
    "high": 0.2,
    "alto": 0.2,
    "riesgo medio": 0.5,
    "moderate": 0.5,
    "moderado": 0.5,
    "riesgo bajo": 0.75,
    "low": 0.75,
    "bajo": 0.75,
    "seguro": 0.95,
    "safe": 0.95,
    "desconocido": 0.5,
    "unknown": 0.5,
}

@dataclass
class SafetyProfile:
    """Comprehensive safety profile for an ingredient"""
    ingredient: str
    risk_level: str
    eco_score: float
    fda_status: str
    ewg_concerns: List[str]
    cir_status: str
    sccs_status: str
    iccr_status: str
    sources: List[str]
    last_updated: datetime

@dataclass
class SubstitutionCandidate:
    """A potential substitute ingredient with detailed analysis"""
    ingredient: str
    similarity_score: float
    safety_improvement: float
    functional_similarity: float
    eco_improvement: float
    risk_reduction: float
    reason: str
    confidence: float
    sources: List[str]

@dataclass
class SubstitutionMapping:
    """Enhanced substitution mapping with ML-based recommendations"""
    original: str
    substitutes: List[SubstitutionCandidate]
    safety_justification: str
    functional_equivalence: float
    confidence_score: float
    last_updated: datetime

class EnhancedSubstitutionMapper:
    """ML-powered ingredient substitution system using multiple safety standards"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.sentence_model = None
        self.vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 3))
        self.ingredient_embeddings = None
        self.ingredient_safety_profiles = {}
        self.substitution_cache = {}
        self.cluster_labels: Dict[str, int] = {}
        self._kmeans_model: Optional[KMeans] = None
        self._embeddings_dirty = True
        self.safety_standards = {
            'fda': {'weight': 0.3, 'safe_levels': ['approved', 'safe', 'generally recognized as safe']},
            'ewg': {'weight': 0.25, 'safe_levels': ['low hazard', 'no data available']},
            'cir': {'weight': 0.2, 'safe_levels': ['safe', 'safe with qualifications']},
            'sccs': {'weight': 0.15, 'safe_levels': ['safe', 'safe with restrictions']},
            'iccr': {'weight': 0.1, 'safe_levels': ['safe', 'approved']}
        }
        
        # Functional ingredient categories for better matching
        self.functional_categories = {
            'emollients': ['glycerin', 'squalane', 'ceramides', 'hyaluronic acid', 'dimethicone'],
            'humectants': ['glycerin', 'hyaluronic acid', 'sodium hyaluronate', 'panthenol'],
            'emulsifiers': ['lecithin', 'polysorbate', 'cetearyl alcohol', 'glyceryl stearate'],
            'preservatives': ['phenoxyethanol', 'benzyl alcohol', 'sorbic acid', 'potassium sorbate'],
            'antioxidants': ['vitamin e', 'vitamin c', 'ferulic acid', 'resveratrol'],
            'surfactants': ['cocamidopropyl betaine', 'sodium lauryl sulfate', 'decyl glucoside'],
            'fragrance': ['essential oils', 'natural fragrances', 'fragrance-free'],
            'colorants': ['iron oxides', 'titanium dioxide', 'zinc oxide', 'natural colorants']
        }
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the sentence transformer model"""
        if SentenceTransformer is not None:
            try:
                self.sentence_model = SentenceTransformer(self.model_name)
                logger.info(f"Initialized sentence transformer model: {self.model_name}")
            except Exception as e:
                logger.warning(f"Failed to load sentence transformer: {e}")
                self.sentence_model = None
        else:
            logger.info("SentenceTransformer not available, using TF-IDF fallback")
    
    async def build_safety_database(self, ingredients: List[str]) -> Dict[str, SafetyProfile]:
        """Build comprehensive safety database from multiple sources"""
        logger.info(f"Building safety database for {len(ingredients)} ingredients")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            tasks = []
            for ingredient in ingredients:
                task = self._fetch_comprehensive_safety_data(ingredient, client)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch safety data for {ingredients[i]}: {result}")
                continue
            
            if isinstance(result, SafetyProfile):
                self.ingredient_safety_profiles[result.ingredient] = result
        
        logger.info(f"Built safety database with {len(self.ingredient_safety_profiles)} ingredients")
        self._embeddings_dirty = True
        return self.ingredient_safety_profiles
    
    async def _fetch_comprehensive_safety_data(self, ingredient: str, client: httpx.AsyncClient) -> SafetyProfile:
        """Fetch safety data from all available sources"""
        try:
            # Get comprehensive data from your existing API
            data = await fetch_ingredient_data(ingredient, client)
            
            # Extract data from different sources
            fda_status = self._extract_fda_status(data)
            ewg_concerns = self._extract_ewg_concerns(data)
            cir_status = self._extract_cir_status(data)
            sccs_status = self._extract_sccs_status(data)
            iccr_status = self._extract_iccr_status(data)
            
            return SafetyProfile(
                ingredient=ingredient,
                risk_level=data.get('risk_level', 'unknown'),
                eco_score=data.get('eco_score', 50.0),
                fda_status=fda_status,
                ewg_concerns=ewg_concerns,
                cir_status=cir_status,
                sccs_status=sccs_status,
                iccr_status=iccr_status,
                sources=data.get('sources', []),
                last_updated=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Error fetching safety data for {ingredient}: {e}")
            return SafetyProfile(
                ingredient=ingredient,
                risk_level='unknown',
                eco_score=50.0,
                fda_status='unknown',
                ewg_concerns=[],
                cir_status='unknown',
                sccs_status='unknown',
                iccr_status='unknown',
                sources=[],
                last_updated=datetime.utcnow()
            )
    
    def _extract_fda_status(self, data: Dict) -> str:
        """Extract FDA status from API response"""
        sources = data.get('sources', '')
        if 'FDA' in sources:
            return 'approved'
        return 'unknown'
    
    def _extract_ewg_concerns(self, data: Dict) -> List[str]:
        """Extract EWG concerns from API response"""
        concerns = []
        if 'EWG' in data.get('sources', ''):
            risk_level = data.get('risk_level', '').lower()
            if 'high' in risk_level or 'moderate' in risk_level:
                concerns.append(risk_level)
        return concerns
    
    def _extract_cir_status(self, data: Dict) -> str:
        """Extract CIR status from API response"""
        sources = data.get('sources', '')
        if 'CIR' in sources:
            return 'reviewed'
        return 'unknown'
    
    def _extract_sccs_status(self, data: Dict) -> str:
        """Extract SCCS status from API response"""
        sources = data.get('sources', '')
        if 'SCCS' in sources:
            return 'evaluated'
        return 'unknown'
    
    def _extract_iccr_status(self, data: Dict) -> str:
        """Extract ICCR status from API response"""
        sources = data.get('sources', '')
        if 'ICCR' in sources:
            return 'harmonized'
        return 'unknown'
    
    def calculate_safety_score(self, profile: SafetyProfile) -> float:
        """Calculate comprehensive safety score (0-100)"""
        score = 0.0
        total_weight = 0.0
        
        # FDA weight
        if profile.fda_status in self.safety_standards['fda']['safe_levels']:
            score += 100 * self.safety_standards['fda']['weight']
        total_weight += self.safety_standards['fda']['weight']
        
        # EWG weight (inverse of concerns)
        ewg_score = 100
        if profile.ewg_concerns:
            ewg_score = max(0, 100 - len(profile.ewg_concerns) * 20)
        score += ewg_score * self.safety_standards['ewg']['weight']
        total_weight += self.safety_standards['ewg']['weight']
        
        # Eco score weight
        eco_score = profile.eco_score if profile.eco_score else 50
        score += eco_score * 0.2
        total_weight += 0.2
        
        # Risk level weight
        risk_score = 100
        if profile.risk_level.lower() in ['high', 'alto']:
            risk_score = 20
        elif profile.risk_level.lower() in ['moderate', 'moderado']:
            risk_score = 60
        elif profile.risk_level.lower() in ['low', 'bajo']:
            risk_score = 90
        score += risk_score * 0.15
        total_weight += 0.15
        
        return score / total_weight if total_weight > 0 else 50.0
    
    def find_functional_category(self, ingredient: str) -> Optional[str]:
        """Find the functional category of an ingredient"""
        ingredient_lower = ingredient.lower()
        for category, ingredients in self.functional_categories.items():
            for cat_ingredient in ingredients:
                if cat_ingredient in ingredient_lower or ingredient_lower in cat_ingredient:
                    return category
        return None
    
    def calculate_functional_similarity(self, original: str, candidate: str) -> float:
        """Calculate functional similarity between ingredients"""
        orig_category = self.find_functional_category(original)
        cand_category = self.find_functional_category(candidate)
        
        if orig_category == cand_category and orig_category is not None:
            return 1.0
        
        # Use semantic similarity for more nuanced matching
        if self.sentence_model:
            try:
                embeddings = self.sentence_model.encode([original, candidate])
                similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
                return float(similarity)
            except Exception as e:
                logger.warning(f"Error calculating semantic similarity: {e}")
        
        # Fallback to TF-IDF similarity
        try:
            texts = [original, candidate]
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except Exception as e:
            logger.warning(f"Error calculating TF-IDF similarity: {e}")
            return 0.0
    
    async def find_substitutes(self, problematic_ingredient: str, 
                             user_conditions: List[str] = None,
                             max_substitutes: int = 5) -> List[SubstitutionCandidate]:
        """Find ML-powered substitute recommendations"""
        
        # Check cache first
        cache_key = f"{problematic_ingredient}_{hash(tuple(user_conditions or []))}"
        if cache_key in self.substitution_cache:
            cached_data = self.substitution_cache[cache_key]
            if datetime.utcnow() - cached_data['timestamp'] < timedelta(hours=24):
                return cached_data['substitutes']
        
        logger.info(f"Finding substitutes for {problematic_ingredient}")
        
        # Get safety profile for the problematic ingredient
        if problematic_ingredient not in self.ingredient_safety_profiles:
            await self.build_safety_database([problematic_ingredient])
        
        original_profile = self.ingredient_safety_profiles.get(problematic_ingredient)
        if not original_profile:
            logger.warning(f"No safety profile found for {problematic_ingredient}")
            return []
        
        self._ensure_embedding_space()

        # Find candidates from the same functional category
        orig_category = self.find_functional_category(problematic_ingredient)
        candidates: List[str] = []
        
        if orig_category:
            candidates = self.functional_categories[orig_category].copy()
        
        # Add more candidates from safety database
        for ingredient, profile in self.ingredient_safety_profiles.items():
            if ingredient != problematic_ingredient:
                candidates.append(ingredient)
        
        embedding_order: List[str] = []
        embedding_scores: Dict[str, float] = {}
        original_vector = None
        if self.ingredient_embeddings and problematic_ingredient in self.ingredient_embeddings:
            original_vector = self.ingredient_embeddings[problematic_ingredient]
            current_cluster = self.cluster_labels.get(problematic_ingredient)
            ranked: List[Tuple[str, float, bool]] = []
            for name, vector in self.ingredient_embeddings.items():
                if name == problematic_ingredient:
                    continue
                score = self._embedding_similarity(problematic_ingredient, name)
                cluster_match = current_cluster is None or self.cluster_labels.get(name) == current_cluster
                ranked.append((name, score, cluster_match))
            ranked.sort(key=lambda item: (item[2], item[1]), reverse=True)
            embedding_order = [item[0] for item in ranked]
            embedding_scores = {item[0]: item[1] for item in ranked}

        ordered_candidates: List[str] = []
        seen: Set[str] = set()
        for name in embedding_order:
            if name not in seen:
                ordered_candidates.append(name)
                seen.add(name)
        for name in candidates:
            if name not in seen and name != problematic_ingredient:
                ordered_candidates.append(name)
                seen.add(name)

        # Calculate substitution scores for each candidate
        substitution_candidates = []
        
        for candidate in ordered_candidates:
            if candidate == problematic_ingredient:
                continue
                
            candidate_profile = self.ingredient_safety_profiles.get(candidate)
            if not candidate_profile:
                continue
            
            # Calculate various similarity and improvement scores
            functional_sim = self.calculate_functional_similarity(problematic_ingredient, candidate)
            embedding_sim = embedding_scores.get(candidate, 0.0)
            safety_improvement = self.calculate_safety_score(candidate_profile) - self.calculate_safety_score(original_profile)
            eco_improvement = candidate_profile.eco_score - original_profile.eco_score
            
            # Risk reduction (higher is better)
            risk_reduction = 0
            if original_profile.risk_level.lower() in ['high', 'alto'] and candidate_profile.risk_level.lower() in ['low', 'bajo']:
                risk_reduction = 1.0
            elif original_profile.risk_level.lower() in ['moderate', 'moderado'] and candidate_profile.risk_level.lower() in ['low', 'bajo']:
                risk_reduction = 0.7
            
            # Overall similarity score
            similarity_score = (
                functional_sim * 0.5
                + embedding_sim * 0.35
                + min(1.0, max(0.0, safety_improvement / 50)) * 0.15
            )
            
            # Confidence score
            confidence = (
                similarity_score * 0.5
                + min(1.0, max(0.0, safety_improvement / 30)) * 0.25
                + embedding_sim * 0.15
                + risk_reduction * 0.1
            )
            
            # Generate reason
            reason_parts = []
            if functional_sim > 0.7:
                reason_parts.append("funcionalmente similar")
            if embedding_sim > 0.7:
                reason_parts.append("perfil químico similar")
            if safety_improvement > 10:
                reason_parts.append(f"más seguro (+{safety_improvement:.1f} puntos)")
            if eco_improvement > 10:
                reason_parts.append(f"más ecológico (+{eco_improvement:.1f} puntos)")
            if risk_reduction > 0.5:
                reason_parts.append("menor riesgo")
            
            reason = ", ".join(reason_parts) if reason_parts else "alternativa recomendada"
            
            substitution_candidates.append(SubstitutionCandidate(
                ingredient=candidate,
                similarity_score=similarity_score,
                safety_improvement=safety_improvement,
                functional_similarity=functional_sim,
                eco_improvement=eco_improvement,
                risk_reduction=risk_reduction,
                reason=reason,
                confidence=confidence,
                sources=candidate_profile.sources
            ))
        
        # Sort by confidence and similarity
        substitution_candidates.sort(key=lambda x: (x.confidence, x.similarity_score), reverse=True)
        
        # Filter and return top candidates
        top_candidates = substitution_candidates[:max_substitutes]
        
        # Cache results
        self.substitution_cache[cache_key] = {
            'substitutes': top_candidates,
            'timestamp': datetime.utcnow()
        }
        
        return top_candidates
    
    async def generate_substitution_mapping(self, problematic_ingredients: List[str],
                                          user_conditions: List[str] = None) -> Dict[str, SubstitutionMapping]:
        """Generate comprehensive substitution mappings for multiple ingredients"""
        
        logger.info(f"Generating substitution mappings for {len(problematic_ingredients)} ingredients")
        
        # Build safety database for all ingredients
        all_ingredients = set(problematic_ingredients)
        for ingredient in problematic_ingredients:
            orig_category = self.find_functional_category(ingredient)
            if orig_category:
                all_ingredients.update(self.functional_categories[orig_category])
        
        await self.build_safety_database(list(all_ingredients))
        
        # Generate mappings for each problematic ingredient
        mappings = {}
        
        for ingredient in problematic_ingredients:
            substitutes = await self.find_substitutes(ingredient, user_conditions)
            
            if substitutes:
                # Calculate overall functional equivalence
                functional_equivalence = np.mean([sub.functional_similarity for sub in substitutes])
                
                # Calculate overall confidence
                confidence_score = np.mean([sub.confidence for sub in substitutes])
                
                # Generate safety justification
                safety_justification = self._generate_safety_justification(ingredient, substitutes)
                
                mappings[ingredient] = SubstitutionMapping(
                    original=ingredient,
                    substitutes=substitutes,
                    safety_justification=safety_justification,
                    functional_equivalence=functional_equivalence,
                    confidence_score=confidence_score,
                    last_updated=datetime.utcnow()
                )
        
        return mappings
    
    def _generate_safety_justification(self, original: str, substitutes: List[SubstitutionCandidate]) -> str:
        """Generate human-readable safety justification for substitutions"""
        if not substitutes:
            return "No se encontraron sustitutos seguros."
        
        original_profile = self.ingredient_safety_profiles.get(original)
        if not original_profile:
            return "Información de seguridad limitada para el ingrediente original."
        
        justifications = []
        
        # Safety improvements
        safety_improvements = [sub.safety_improvement for sub in substitutes if sub.safety_improvement > 0]
        if safety_improvements:
            avg_improvement = np.mean(safety_improvements)
            justifications.append(f"Los sustitutos son en promedio {avg_improvement:.1f} puntos más seguros")
        
        # Eco improvements
        eco_improvements = [sub.eco_improvement for sub in substitutes if sub.eco_improvement > 0]
        if eco_improvements:
            avg_eco = np.mean(eco_improvements)
            justifications.append(f"Mejora ecológica promedio de {avg_eco:.1f} puntos")
        
        # Risk reduction
        risk_reductions = [sub.risk_reduction for sub in substitutes if sub.risk_reduction > 0]
        if risk_reductions:
            justifications.append("Reducción significativa del riesgo de seguridad")
        
        # Sources
        all_sources = set()
        for sub in substitutes:
            all_sources.update(sub.sources)
        if all_sources:
            justifications.append(f"Basado en datos de {', '.join(sorted(all_sources))}")
        
        return ". ".join(justifications) + "." if justifications else "Sustitutos recomendados basados en similitud funcional."

# Convenience functions for easy integration
async def get_enhanced_substitutes(problematic_ingredients: List[str], 
                                 user_conditions: List[str] = None) -> Dict[str, Any]:
    """Get enhanced substitute recommendations using ML and safety standards"""
    mapper = EnhancedSubstitutionMapper()
    mappings = await mapper.generate_substitution_mapping(problematic_ingredients, user_conditions)
    
    # Convert to serializable format
    result = {}
    for ingredient, mapping in mappings.items():
        result[ingredient] = {
            'original': mapping.original,
            'substitutes': [asdict(sub) for sub in mapping.substitutes],
            'safety_justification': mapping.safety_justification,
            'functional_equivalence': mapping.functional_equivalence,
            'confidence_score': mapping.confidence_score,
            'last_updated': mapping.last_updated.isoformat()
        }
    
    return result

async def suggest_safer_alternatives(ingredients: List[str], 
                                   user_conditions: List[str] = None) -> List[Dict[str, Any]]:
    """Suggest safer alternatives for a list of ingredients"""
    mapper = EnhancedSubstitutionMapper()
    
    # Build safety database
    await mapper.build_safety_database(ingredients)
    
    suggestions = []
    for ingredient in ingredients:
        profile = mapper.ingredient_safety_profiles.get(ingredient)
        if profile and mapper.calculate_safety_score(profile) < 70:  # Low safety score
            substitutes = await mapper.find_substitutes(ingredient, user_conditions)
            if substitutes:
                suggestions.append({
                    'original': ingredient,
                    'safety_score': mapper.calculate_safety_score(profile),
                    'recommended_substitutes': [asdict(sub) for sub in substitutes[:3]],
                    'reason': f"Puntuación de seguridad baja ({mapper.calculate_safety_score(profile):.1f}/100)"
                })
    
    return suggestions

    def _ensure_embedding_space(self) -> None:
        if not self.ingredient_safety_profiles:
            return
        if self.ingredient_embeddings is not None and not self._embeddings_dirty:
            return
        self._build_embedding_space()

    def _build_embedding_space(self) -> None:
        ingredients = list(self.ingredient_safety_profiles.keys())
        if not ingredients:
            self.ingredient_embeddings = None
            self.cluster_labels = {}
            self._kmeans_model = None
            self._embeddings_dirty = False
            return

        texts: List[str] = []
        numeric_features: List[List[float]] = []

        for ingredient in ingredients:
            profile = self.ingredient_safety_profiles[ingredient]
            texts.append(self._profile_text_signature(profile, ingredient))
            numeric_features.append(self._profile_numeric_features(profile))

        tfidf_matrix = self.vectorizer.fit_transform(texts).toarray()
        numeric_array = np.asarray(numeric_features, dtype=np.float32)
        if numeric_array.shape[0] != tfidf_matrix.shape[0]:
            raise ValueError("Mismatch between TF-IDF and numeric feature rows")

        combined = np.hstack([tfidf_matrix, numeric_array]) if numeric_array.size else tfidf_matrix

        if combined.shape[0] > 1 and combined.shape[1] > 10:
            n_components = min(10, combined.shape[0], combined.shape[1])
            if n_components >= 2:
                pca = PCA(n_components=n_components, random_state=42)
                combined = pca.fit_transform(combined)

        normed_vectors: List[np.ndarray] = []
        for row in combined:
            l2 = np.linalg.norm(row)
            normed_vectors.append(row / (l2 + 1e-8))
        normed_matrix = np.asarray(normed_vectors, dtype=np.float32)

        self.ingredient_embeddings = {
            ingredient: normed_matrix[idx]
            for idx, ingredient in enumerate(ingredients)
        }

        if len(ingredients) >= 4:
            n_clusters = min(max(2, len(ingredients) // 4), len(ingredients) - 1)
            if n_clusters >= 2:
                self._kmeans_model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                labels = self._kmeans_model.fit_predict(normed_matrix)
                self.cluster_labels = {
                    ingredient: int(labels[idx])
                    for idx, ingredient in enumerate(ingredients)
                }
            else:
                self._kmeans_model = None
                self.cluster_labels = {ingredient: 0 for ingredient in ingredients}
        else:
            self._kmeans_model = None
            self.cluster_labels = {ingredient: 0 for ingredient in ingredients}

        self._embeddings_dirty = False

    def _profile_text_signature(self, profile: SafetyProfile, ingredient: str) -> str:
        tokens = [ingredient.lower()]
        tokens.append(str(profile.risk_level).lower())
        tokens.append(str(profile.fda_status).lower())
        tokens.append(str(profile.cir_status).lower())
        tokens.append(str(profile.sccs_status).lower())
        tokens.append(str(profile.iccr_status).lower())
        tokens.extend(normalize_ingredient_name(item) for item in profile.ewg_concerns if item)
        if isinstance(profile.sources, (list, tuple, set)):
            tokens.extend(normalize_ingredient_name(item) for item in profile.sources if item)
        elif isinstance(profile.sources, str):
            tokens.extend(normalize_ingredient_name(part) for part in profile.sources.split(',') if part)
        return " ".join(token for token in tokens if token)

    def _profile_numeric_features(self, profile: SafetyProfile) -> List[float]:
        risk_key = normalize_ingredient_name(profile.risk_level)
        risk_value = RISK_LEVEL_MAP.get(risk_key, 0.5)
        eco_norm = float(profile.eco_score or 50.0) / 100.0
        safety_norm = self.calculate_safety_score(profile) / 100.0
        ewg_penalty = min(len(profile.ewg_concerns), 5) / 5.0 if profile.ewg_concerns else 0.0

        def _status_weight(value: str, standard: str) -> float:
            safe_levels = self.safety_standards[standard]['safe_levels']
            return 1.0 if value and value.lower() in [item.lower() for item in safe_levels] else 0.0

        fda_flag = _status_weight(profile.fda_status, 'fda')
        cir_flag = _status_weight(profile.cir_status, 'cir')
        sccs_flag = _status_weight(profile.sccs_status, 'sccs')
        iccr_flag = _status_weight(profile.iccr_status, 'iccr')

        return [eco_norm, safety_norm, risk_value, ewg_penalty, fda_flag, cir_flag, sccs_flag, iccr_flag]

    def _embedding_similarity(self, ingredient_a: str, ingredient_b: str) -> float:
        if not self.ingredient_embeddings:
            return 0.0
        vec_a = self.ingredient_embeddings.get(ingredient_a)
        vec_b = self.ingredient_embeddings.get(ingredient_b)
        if vec_a is None or vec_b is None:
            return 0.0
        sim = float(np.dot(vec_a, vec_b))
        return max(0.0, min(1.0, (sim + 1.0) / 2.0))

if __name__ == "__main__":
    # Example usage
    async def main():
        mapper = EnhancedSubstitutionMapper()
        
        # Test with some problematic ingredients
        problematic = ["sodium lauryl sulfate", "parabens", "formaldehyde"]
        user_conditions = ["sensitive skin", "eczema"]
        
        mappings = await mapper.generate_substitution_mapping(problematic, user_conditions)
        
        for ingredient, mapping in mappings.items():
            print(f"\n=== {ingredient.upper()} ===")
            print(f"Safety Justification: {mapping.safety_justification}")
            print(f"Functional Equivalence: {mapping.functional_equivalence:.2f}")
            print(f"Confidence Score: {mapping.confidence_score:.2f}")
            print("\nTop Substitutes:")
            for i, sub in enumerate(mapping.substitutes[:3], 1):
                print(f"{i}. {sub.ingredient} (confidence: {sub.confidence:.2f})")
                print(f"   Reason: {sub.reason}")
                print(f"   Safety improvement: +{sub.safety_improvement:.1f}")
    
    asyncio.run(main())