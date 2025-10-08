"""Ingredient-based product recommendation engine used during routine analysis."""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Dict, Iterable, List, Optional, Sequence

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover - handled via fallback
    SentenceTransformer = None  # type: ignore

from database import Product


logger = logging.getLogger(__name__)


def _normalize_list(value: Optional[Iterable]) -> List[str]:
    if not value:
        return []
    normalized: List[str] = []
    for item in value:
        if item is None:
            continue
        if isinstance(item, str):
            cleaned = item.strip()
            if not cleaned:
                continue
            normalized.append(cleaned)
        else:
            normalized.append(str(item))
    return normalized


@dataclass
class ProductMetadata:
    product_id: Optional[int]
    name: str
    brand: Optional[str]
    eco_score: Optional[float]
    risk_level: Optional[str]
    ingredients: List[str]
    category: Optional[str]


class IngredientRecommender:
    """Provides substitute product suggestions using ingredient similarity."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        cache_ttl_minutes: int = 30,
        min_eco_score: float = 70.0,
    ) -> None:
        self.model_name = model_name
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.min_eco_score = min_eco_score
        self.session_factory: Optional[Callable[[], object]] = None

        self._sentence_model: Optional[SentenceTransformer] = None
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._strategy: Optional[str] = None
        self._product_matrix: Optional[np.ndarray] = None
        self._product_meta: List[ProductMetadata] = []
        self._last_loaded_at: Optional[datetime] = None
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Configuration and cache management
    # ------------------------------------------------------------------
    def configure(self, session_factory: Callable[[], object]) -> None:
        self.session_factory = session_factory

    def ensure_loaded(self, force: bool = False) -> None:
        """Load product embeddings if the cache is stale."""

        if self.session_factory is None:
            logger.warning("IngredientRecommender has no session factory configured")
            return

        with self._lock:
            if not force and self._is_cache_fresh():
                return

            try:
                session = self.session_factory()
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Unable to create session for recommender: %s", exc)
                return

            try:
                products: Sequence[Product] = session.query(Product).all()  # type: ignore[attr-defined]
            finally:
                try:
                    session.close()  # type: ignore[union-attr]
                except Exception:  # pragma: no cover - defensive
                    pass

            if not products:
                logger.info("No products available to build recommendation index")
                self._product_matrix = None
                self._product_meta = []
                self._last_loaded_at = datetime.utcnow()
                return

            texts: List[str] = []
            metadata: List[ProductMetadata] = []

            for product in products:
                ingredient_list = self._parse_ingredients(product.ingredients)
                text = self._compose_product_text(product, ingredient_list)
                texts.append(text)
                metadata.append(
                    ProductMetadata(
                        product_id=getattr(product, "id", None),
                        name=(product.name or "Producto desconocido"),
                        brand=product.brand,
                        eco_score=product.eco_score,
                        risk_level=product.risk_level,
                        ingredients=ingredient_list,
                        category=product.category,
                    )
                )

            matrix, strategy = self._encode_corpus(texts)

            if matrix is None:
                logger.warning("Failed to build product embedding matrix")
                return

            self._product_matrix = matrix
            self._product_meta = metadata
            self._strategy = strategy
            self._last_loaded_at = datetime.utcnow()
            logger.info(
                "Loaded %d products into recommendation index using %s",
                len(metadata),
                strategy,
            )

    def rebuild(self) -> None:
        self.ensure_loaded(force=True)

    def _is_cache_fresh(self) -> bool:
        if self._product_matrix is None or self._last_loaded_at is None:
            return False
        return datetime.utcnow() - self._last_loaded_at < self.cache_ttl

    # ------------------------------------------------------------------
    # Encoding helpers
    # ------------------------------------------------------------------
    def _parse_ingredients(self, value: object) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [item.strip() for item in value if isinstance(item, str)]
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            try:
                parsed = json.loads(stripped)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except json.JSONDecodeError:
                pass
            return [segment.strip() for segment in stripped.replace("|", ",").split(",") if segment.strip()]
        return [str(value)]

    def _compose_product_text(self, product: Product, ingredients: List[str]) -> str:
        parts = [product.name or "", product.brand or "", product.category or ""]
        parts.extend(ingredients)
        return " ".join(part for part in parts if part).lower()

    def _ensure_sentence_model(self) -> Optional[SentenceTransformer]:
        if SentenceTransformer is None:
            return None
        if self._sentence_model is None:
            try:
                self._sentence_model = SentenceTransformer(self.model_name)
            except Exception as exc:  # pragma: no cover - model load failure
                logger.error("Failed to load sentence transformer: %s", exc)
                self._sentence_model = None
        return self._sentence_model

    def _encode_corpus(self, texts: List[str]) -> tuple[Optional[np.ndarray], Optional[str]]:
        if not texts:
            return None, None

        model = self._ensure_sentence_model()
        if model is not None:
            try:
                embeddings = model.encode(texts, normalize_embeddings=True)
                return np.asarray(embeddings), "sentence-transformer"
            except Exception as exc:  # pragma: no cover - runtime failure
                logger.error("SentenceTransformer encoding failed: %s", exc)

        # Fallback to TF-IDF
        vectorizer = TfidfVectorizer(max_features=4096, ngram_range=(1, 2))
        matrix = vectorizer.fit_transform(texts)
        self._vectorizer = vectorizer
        return matrix, "tfidf"

    def _encode_query(self, text: str):
        model = self._ensure_sentence_model()
        if model is not None and self._strategy == "sentence-transformer":
            return model.encode([text], normalize_embeddings=True)
        if self._vectorizer is None:
            return None
        return self._vectorizer.transform([text])

    # ------------------------------------------------------------------
    # Public recommendation API
    # ------------------------------------------------------------------
    def suggest_substitutes(
        self,
        *,
        ingredients: Sequence[str],
        excluded_ingredients: Sequence[str],
        target_product_name: Optional[str],
        user_conditions: Sequence[str],
        top_k: int = 3,
    ) -> List[Dict[str, object]]:
        self.ensure_loaded()

        if not self._product_matrix or not self._product_meta:
            return []

        safe_ingredients = _normalize_list(ingredients)
        excluded_normalized = {item.lower() for item in _normalize_list(excluded_ingredients)}

        if not safe_ingredients and not target_product_name:
            return []

        query_parts = safe_ingredients.copy()
        if target_product_name:
            query_parts.append(target_product_name)
        query_text = " ".join(query_parts).lower()
        if not query_text:
            return []

        query_vector = self._encode_query(query_text)
        if query_vector is None:
            logger.warning("Unable to encode query text for recommendations")
            return []

        similarity_scores = cosine_similarity(query_vector, self._product_matrix).ravel()
        order = np.argsort(similarity_scores)[::-1]

        allowed_risks = {"", "seguro", "riesgo bajo"}
        user_condition_set = {c.lower() for c in _normalize_list(user_conditions)}
        suggestions: List[Dict[str, object]] = []

        for index in order:
            meta = self._product_meta[index]
            score = float(similarity_scores[index])
            if score <= 0:
                continue

            if target_product_name and meta.name.lower() == target_product_name.lower():
                continue

            if meta.eco_score is not None and meta.eco_score < self.min_eco_score:
                continue

            risk = (meta.risk_level or "").lower()
            if risk not in allowed_risks:
                continue

            ingredient_set = {item.lower() for item in meta.ingredients}
            if ingredient_set and excluded_normalized.intersection(ingredient_set):
                continue

            # If user has specific conditions, require overlap with safe ingredients
            if user_condition_set and safe_ingredients:
                safe_lower = {item.lower() for item in safe_ingredients}
                if ingredient_set and not ingredient_set.intersection(safe_lower):
                    continue

            reason_parts = []
            if meta.eco_score is not None:
                reason_parts.append(f"Eco-score {meta.eco_score:.0f}/100")
            if meta.risk_level:
                reason_parts.append(f"riesgo {meta.risk_level}")
            if excluded_normalized:
                reason_parts.append("sin los ingredientes observados de alto riesgo")
            if meta.category:
                reason_parts.append(f"categoría {meta.category}")

            suggestions.append(
                {
                    "product_id": meta.product_id,
                    "name": meta.name,
                    "brand": meta.brand,
                    "eco_score": meta.eco_score,
                    "risk_level": meta.risk_level,
                    "similarity": round(score, 4),
                    "reason": ", ".join(reason_parts) if reason_parts else "Compatibilidad alta",
                    "ingredients": meta.ingredients,
                    "category": meta.category,
                }
            )

            if len(suggestions) >= top_k:
                break

        return suggestions

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------
    @property
    def index_size(self) -> int:
        return len(self._product_meta)


__all__ = ["IngredientRecommender"]
