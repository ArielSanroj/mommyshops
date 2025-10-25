"""Unified product catalog aggregation service.

This module replaces legacy in-memory sample product catalogs by sourcing
real product data from public APIs (Open Beauty Facts), enriching results with
Apify-powered scraping when credentials are available, and persisting the
records in the relational database for downstream recommendation engines.

The service coordinates three layers of data:

1. **Live APIs** – Open Beauty Facts provides structured product metadata,
   including ingredient disclosures and eco scores.
2. **Apify enrichment** – Optional scraping augments products with additional
   details (description, availability, extra ingredients) to improve quality.
3. **Database persistence** – Every aggregated product is upserted into the
   `products` table so that machine-learning recommenders can index them.

All heavy network operations are asynchronous while database writes run in a
thread pool to keep FastAPI handlers responsive.
"""

from __future__ import annotations

import asyncio
import copy
import json
import logging
import math
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import httpx
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from apify_enhanced_scraper import ApifyEnhancedScraper, ApifyResponse
from api_utils_production import fetch_ingredient_data
from database import (
    SessionLocal,
    Product,
    canonicalize_ingredients,
    get_ingredient_data,
    normalize_ingredient_name,
)

LOGGER_NAME = "mommyshops.product_catalog"
logger = logging.getLogger(LOGGER_NAME)
if not logger.handlers:
    backend_path = os.getenv("BACKEND_LOG_PATH")
    handler: logging.Handler
    if backend_path:
        try:
            os.makedirs(os.path.dirname(backend_path), exist_ok=True)
            handler = logging.FileHandler(backend_path)
        except Exception:  # pragma: no cover - fallback to stdout
            handler = logging.StreamHandler()
    else:
        handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False


RISK_PRIORITY = {
    "cancerígeno": 5,
    "riesgo alto": 4,
    "riesgo medio": 3,
    "riesgo bajo": 2,
    "seguro": 1,
    "desconocido": 0,
}

DEFAULT_CACHE_TTL = 6 * 3600  # 6 hours
OPEN_BEAUTY_FACTS_ENDPOINT = "https://world.openbeautyfacts.org/cgi/search.pl"


@dataclass
class CatalogCandidate:
    name: str
    brand: str
    ingredients: List[str]
    category: Optional[str]
    eco_score: Optional[float]
    risk_level: Optional[str]
    match_score: float
    reason: str
    source: str
    extra_metadata: Dict[str, Any]
    lookup_key: Tuple[str, str]
    product_id: Optional[int] = None
    rating_average: Optional[float] = None
    rating_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "name": self.name,
            "brand": self.brand,
            "ingredients": copy.deepcopy(self.ingredients),
            "category": self.category,
            "eco_score": self.eco_score,
            "risk_level": self.risk_level,
            "match_score": self.match_score,
            "reason": self.reason,
            "source": self.source,
            "extra_metadata": copy.deepcopy(self.extra_metadata),
            "lookup_key": self.lookup_key,
            "rating_average": self.rating_average,
            "rating_count": self.rating_count,
        }


class ProductCatalogService:
    """Aggregate product data from external sources and persist into the DB."""

    def __init__(self) -> None:
        self._cache: Dict[Tuple[str, ...], Tuple[float, List[Dict[str, Any]]]] = {}
        self._apify_enabled = bool(os.getenv("APIFY_API_KEY"))
        self._schema_checked = False

    async def ensure_catalog(
        self,
        query_ingredients: Sequence[str],
        user_conditions: Optional[Sequence[str]] = None,
        *,
        max_products: int = 24,
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Fetch and persist products related to the provided ingredients.

        Returns a tuple `(catalog_updated, candidates)` where `catalog_updated`
        indicates whether new/updated rows were persisted and `candidates`
        contains structured product dictionaries usable as recommendation
        fallbacks when the ML index has insufficient coverage.
        """

        normalized_query = self._normalize_query(query_ingredients)
        if not normalized_query:
            return False, []

        cache_key = tuple(sorted(normalized_query))
        cached = self._cache.get(cache_key)
        if cached and (time.time() - cached[0]) < DEFAULT_CACHE_TTL:
            logger.debug("Product catalog cache hit for %s", cache_key)
            return False, copy.deepcopy(cached[1])

        per_ingredient = max(2, max_products // max(1, len(normalized_query)))
        async with httpx.AsyncClient(timeout=25.0) as client:
            fetched_candidates = await self._collect_from_sources(
                normalized_query,
                client,
                per_ingredient,
            )

            if not fetched_candidates:
                logger.warning("No product data retrieved for query set: %s", normalized_query)
                return False, []

            if self._apify_enabled:
                await self._enrich_with_apify(fetched_candidates)

            await self._compute_metrics(fetched_candidates, normalized_query, client)

        catalog_updated, persisted = await self._persist_async(fetched_candidates)

        lookup_map = {item["lookup_key"]: item for item in persisted}
        enriched_output: List[Dict[str, Any]] = []
        for candidate in fetched_candidates:
            record = lookup_map.get(candidate.lookup_key)
            payload = candidate.to_dict()
            if record:
                payload.update(
                    {
                        "product_id": record.get("product_id"),
                        "eco_score": record.get("eco_score", payload.get("eco_score")),
                        "risk_level": record.get("risk_level", payload.get("risk_level")),
                        "category": record.get("category", payload.get("category")),
                        "rating_average": record.get("rating_average", payload.get("rating_average")),
                        "rating_count": record.get("rating_count", payload.get("rating_count")),
                    }
                )
            enriched_output.append(payload)

        self._cache[cache_key] = (time.time(), copy.deepcopy(enriched_output))
        return catalog_updated, enriched_output

    # ------------------------------------------------------------------
    # Collection layer
    # ------------------------------------------------------------------
    async def _collect_from_sources(
        self,
        normalized_query: Sequence[str],
        client: httpx.AsyncClient,
        per_ingredient: int,
    ) -> List[CatalogCandidate]:
        tasks = [
            self._fetch_open_beauty_facts(client, ingredient, per_ingredient)
            for ingredient in normalized_query
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        candidates: Dict[Tuple[str, str], CatalogCandidate] = {}

        for ingredient, result in zip(normalized_query, results):
            if isinstance(result, Exception):
                logger.warning("Open Beauty Facts fetch failed for %s: %s", ingredient, result)
                continue
            for candidate in result:
                if candidate.lookup_key in candidates:
                    existing = candidates[candidate.lookup_key]
                    merged_ingredients = list(dict.fromkeys(existing.ingredients + candidate.ingredients))
                    existing.ingredients = merged_ingredients
                    existing.extra_metadata.setdefault("sources", set()).add(candidate.source)
                    continue
                candidates[candidate.lookup_key] = candidate

        return list(candidates.values())

    async def _fetch_open_beauty_facts(
        self,
        client: httpx.AsyncClient,
        ingredient: str,
        limit: int,
    ) -> List[CatalogCandidate]:
        params = {
            "action": "process",
            "search_terms": ingredient,
            "search_simple": 1,
            "json": 1,
            "page_size": max(5, limit),
            "fields": "product_name,brands,ingredients_text,ingredients_tags,categories_tags,url,ecoscore_score,stores,countries,code",
        }
        try:
            response = await client.get(OPEN_BEAUTY_FACTS_ENDPOINT, params=params)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:  # pragma: no cover - network failure path
            logger.warning("Open Beauty Facts request failed for %s: %s", ingredient, exc)
            return []

        products = data.get("products") or []
        candidates: List[CatalogCandidate] = []
        for product in products:
            name = (product.get("product_name") or "").strip()
            if not name:
                continue
            raw_brand = (product.get("brands") or "").split(",")[0].strip()
            brand = raw_brand or "Marca desconocida"
            ingredients = self._extract_ingredients(product)
            if not ingredients:
                continue

            category = None
            categories = product.get("categories_tags") or []
            if isinstance(categories, list) and categories:
                category = categories[0].split(":")[-1].replace("-", " ").title()

            ecoscore = product.get("ecoscore_score")
            eco_score = None
            if isinstance(ecoscore, (int, float)):
                eco_score = max(0.0, min(100.0, float(ecoscore)))

            lookup_key = self._build_lookup_key(name, brand)
            reason = f"Coincidencia de ingredientes vía Open Beauty Facts para '{ingredient}'"
            extra_metadata = {
                "open_beauty_facts": {
                    "code": product.get("code"),
                    "url": product.get("url"),
                    "stores": product.get("stores"),
                    "countries": product.get("countries"),
                },
            }

            candidate = CatalogCandidate(
                name=name,
                brand=brand,
                ingredients=ingredients,
                category=category,
                eco_score=eco_score,
                risk_level=None,
                match_score=0.0,
                reason=reason,
                source="open_beauty_facts",
                extra_metadata=extra_metadata,
                lookup_key=lookup_key,
            )
            candidates.append(candidate)

            if len(candidates) >= limit:
                break

        return candidates

    # ------------------------------------------------------------------
    # Enrichment layer
    # ------------------------------------------------------------------
    async def _enrich_with_apify(self, candidates: List[CatalogCandidate]) -> None:
        urls: List[str] = []
        mapping: Dict[str, CatalogCandidate] = {}
        for candidate in candidates:
            obf_meta = candidate.extra_metadata.get("open_beauty_facts", {})
            url = obf_meta.get("url")
            if url and url not in mapping:
                urls.append(url)
                mapping[url] = candidate

        if not urls:
            return

        limit = min(3, len(urls))
        selected_urls = urls[:limit]
        try:
            async with ApifyEnhancedScraper() as scraper:
                responses = await scraper.scrape_multiple_urls(selected_urls)
        except Exception as exc:  # pragma: no cover - network failure path
            logger.warning("Apify enrichment failed: %s", exc)
            return

        for url, response in zip(selected_urls, responses):
            if not response.success:
                logger.debug("Apify response unsuccessful for %s: %s", url, response.error)
                continue

            candidate = mapping.get(url)
            if not candidate:
                continue

            data = response.data or {}
            enriched_ingredients = data.get("ingredients") or []
            if enriched_ingredients:
                merged = list(
                    dict.fromkeys(candidate.ingredients + canonicalize_ingredients(enriched_ingredients))
                )
                candidate.ingredients = merged

            product_info = data.get("product_info") or {}
            if product_info.get("category") and not candidate.category:
                candidate.category = str(product_info.get("category")).strip() or None

            candidate.extra_metadata.setdefault("apify", data)
            candidate.reason += " | Enriquecido con Apify"

    # ------------------------------------------------------------------
    # Metrics & scoring
    # ------------------------------------------------------------------
    async def _compute_metrics(
        self,
        candidates: List[CatalogCandidate],
        normalized_query: Sequence[str],
        client: httpx.AsyncClient,
    ) -> None:
        query_set = {item for item in normalized_query if item}

        for candidate in candidates:
            normalized_ingredients = canonicalize_ingredients(candidate.ingredients)
            candidate.ingredients = normalized_ingredients
            if not normalized_ingredients:
                continue

            eco_scores: List[float] = []
            highest_risk = "desconocido"
            risk_sources: List[str] = []

            for ingredient in normalized_ingredients[:8]:
                data = get_ingredient_data(ingredient)
                fetched = False
                if not data:
                    try:
                        data = await fetch_ingredient_data(ingredient, client)
                        fetched = True
                    except Exception as exc:  # pragma: no cover - network failure path
                        logger.debug("Ingredient data fetch failed for %s: %s", ingredient, exc)
                        data = {}

                if not data:
                    continue

                eco = data.get("eco_score")
                if isinstance(eco, (int, float)) and not math.isinf(eco):
                    eco_scores.append(float(eco))

                risk = str(data.get("risk_level", "desconocido"))
                if RISK_PRIORITY.get(risk.lower(), -1) > RISK_PRIORITY.get(highest_risk, -1):
                    highest_risk = risk.lower()

                if fetched and data.get("sources"):
                    risk_sources.append(str(data.get("sources")))

            if eco_scores:
                candidate.eco_score = round(sum(eco_scores) / len(eco_scores), 1)
            elif candidate.eco_score is not None:
                candidate.eco_score = round(candidate.eco_score, 1)

            if highest_risk != "desconocido":
                candidate.risk_level = highest_risk
            elif candidate.risk_level:
                candidate.risk_level = candidate.risk_level.lower()

            match = 0.0
            ingredient_set = {normalize_ingredient_name(item) for item in normalized_ingredients}
            ingredient_set.discard("")
            if query_set and ingredient_set:
                overlap = ingredient_set.intersection(query_set)
                match = len(overlap) / len(query_set)
            candidate.match_score = round(match, 4)

            if risk_sources:
                candidate.extra_metadata.setdefault("sources", set()).update(risk_sources)

            if not candidate.reason:
                candidate.reason = "Coincidencia de ingredientes"

    # ------------------------------------------------------------------
    # Persistence layer
    # ------------------------------------------------------------------
    async def _persist_async(self, candidates: List[CatalogCandidate]) -> Tuple[bool, List[Dict[str, Any]]]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._persist_sync, candidates)

    def _persist_sync(self, candidates: List[CatalogCandidate]) -> Tuple[bool, List[Dict[str, Any]]]:
        if SessionLocal is None:
            logger.warning("SessionLocal not configured; skipping product persistence")
            return False, [candidate.to_dict() for candidate in candidates]

        session = SessionLocal()
        updated = False
        persisted: List[Dict[str, Any]] = []

        try:
            self._ensure_product_schema(session)
            for candidate in candidates:
                record, changed = self._upsert_product(session, candidate)
                updated = updated or changed
                session.flush()
                persisted.append(self._record_to_dict(record))

            session.commit()
        except Exception as exc:  # pragma: no cover - persistence error path
            session.rollback()
            logger.error("Failed to persist product catalog: %s", exc)
            raise
        finally:
            session.close()

        return updated, persisted

    def _upsert_product(self, session, candidate: CatalogCandidate) -> Tuple[Product, bool]:
        query = (
            session.query(Product)
            .filter(Product.name.ilike(candidate.name))
            .filter(Product.brand.ilike(candidate.brand))
        )
        record: Optional[Product] = query.first()
        created = False

        if record is None:
            record = Product(name=candidate.name, brand=candidate.brand)
            session.add(record)
            created = True

        if candidate.ingredients:
            record.ingredients = candidate.ingredients
        if candidate.category:
            record.category = candidate.category
        if candidate.eco_score is not None:
            record.eco_score = candidate.eco_score
        if candidate.risk_level:
            record.risk_level = candidate.risk_level

        extra_metadata = candidate.extra_metadata or {}
        if extra_metadata:
            stored = record.extra_metadata or {}
            if isinstance(stored, dict):
                merged = {**stored, **self._serialize_metadata(extra_metadata)}
            else:
                merged = self._serialize_metadata(extra_metadata)
            record.extra_metadata = merged

        return record, created

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _normalize_query(self, ingredients: Sequence[str]) -> List[str]:
        normalized: List[str] = []
        seen = set()
        for item in ingredients:
            norm = normalize_ingredient_name(item)
            if not norm or norm in seen:
                continue
            seen.add(norm)
            normalized.append(norm)
        return normalized

    def _extract_ingredients(self, product: Dict[str, Any]) -> List[str]:
        tags = product.get("ingredients_tags")
        ingredients: List[str] = []
        if isinstance(tags, list) and tags:
            for tag in tags:
                if not isinstance(tag, str):
                    continue
                token = tag.split(":")[-1]
                cleaned = token.replace("-", " ").strip()
                if cleaned:
                    ingredients.append(cleaned)
        elif isinstance(product.get("ingredients_text"), str):
            raw_text = product["ingredients_text"]
            segments = [segment.strip() for segment in raw_text.split(",") if segment.strip()]
            ingredients.extend(segments)

        return canonicalize_ingredients(ingredients)

    def _build_lookup_key(self, name: str, brand: str) -> Tuple[str, str]:
        return (name.strip().lower(), (brand or "").strip().lower())

    def _record_to_dict(self, record: Product) -> Dict[str, Any]:
        return {
            "product_id": record.id,
            "name": record.name,
            "brand": record.brand,
            "category": record.category,
            "eco_score": record.eco_score,
            "risk_level": record.risk_level,
            "ingredients": record.ingredients or [],
            "lookup_key": self._build_lookup_key(record.name or "", record.brand or ""),
            "rating_average": record.rating_average,
            "rating_count": record.rating_count,
        }

    def _serialize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        serialized: Dict[str, Any] = {}
        for key, value in metadata.items():
            if isinstance(value, (dict, list, str, int, float, type(None))):
                serialized[key] = value
            else:
                serialized[key] = json.loads(json.dumps(value, default=str))
        return serialized

    def _ensure_product_schema(self, session) -> None:
        if self._schema_checked:
            return

        bind = None
        try:
            bind = session.get_bind()
        except SQLAlchemyError:
            bind = None

        if bind is None:
            self._schema_checked = True
            return

        try:
            inspector = inspect(bind)
            columns = {col["name"] for col in inspector.get_columns("products")}
        except SQLAlchemyError as exc:  # pragma: no cover - inspection failure
            logger.debug("Failed to inspect products table: %s", exc)
            self._schema_checked = True
            return

        statements: List[str] = []
        dialect = bind.dialect.name

        if "ollama_summary" not in columns:
            column_type = "TEXT"
            if dialect == "postgresql":
                column_type = "JSONB"
            elif dialect in {"mysql", "mariadb"}:
                column_type = "JSON"
            statements.append(f"ADD COLUMN ollama_summary {column_type}")

        if "rating_count" not in columns:
            statements.append("ADD COLUMN rating_count INTEGER DEFAULT 0")

        if "rating_average" not in columns:
            statements.append("ADD COLUMN rating_average FLOAT DEFAULT 0.0")

        if statements:
            ddl = text(f"ALTER TABLE products {', '.join(statements)}")
            try:
                with bind.connect() as conn:
                    conn.execute(ddl)
                    conn.commit()
                logger.info("Applied product schema updates (%s)", ", ".join(statements))
            except SQLAlchemyError as exc:  # pragma: no cover - DDL failure
                logger.warning("Unable to update products schema: %s", exc)

        self._schema_checked = True


product_catalog_service = ProductCatalogService()

__all__ = ["ProductCatalogService", "product_catalog_service"]
