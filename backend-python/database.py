from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Text,
    ForeignKey,
    JSON,
    DateTime,
    inspect,
    text,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from fastapi import HTTPException
import os
import json
import asyncio
import logging
import re
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher, get_close_matches
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Optional, Tuple

import httpx
from dotenv import load_dotenv
from sqlalchemy.sql import func

# Import Ollama integration
try:
    from ollama_integration import (
        ollama_integration,
        enhance_ocr_text_with_ollama
    )
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("Ollama integration not available")

load_dotenv()

_STANDARD_LOG_KEYS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
}


class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # pragma: no cover - formatting logic
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt) if self.datefmt else self.formatTime(record),
            "logger": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _STANDARD_LOG_KEYS and not key.startswith("_")
        }
        if extras:
            log_record["context"] = extras
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record, ensure_ascii=False)


logger = logging.getLogger("mommyshops.database")
if not logger.handlers:
    backend_log_path = Path(os.getenv("BACKEND_LOG_PATH", Path(__file__).resolve().parent / "backend.log"))
    try:
        backend_log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(backend_log_path)
        formatter = _JSONFormatter()
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as log_exc:  # pragma: no cover - logging setup fallback
        logging.getLogger(__name__).warning("Failed to configure database logger handler", exc_info=log_exc)
logger.setLevel(logging.INFO)
logger.propagate = False

BASE_DIR = Path(__file__).resolve().parent
LEXICON_PATH = Path(os.getenv("INGREDIENT_LEXICON_PATH", BASE_DIR / "cosmetic_ingredients_lexicon.txt"))
DEFAULT_SYNC_CONCURRENCY = max(1, int(os.getenv("INGREDIENT_SYNC_CONCURRENCY", "3")))
DEFAULT_SYNC_TIMEOUT = float(os.getenv("INGREDIENT_SYNC_TIMEOUT", "30"))

_LEXICON_CACHE: Optional[List[str]] = None

_NORMALIZATION_PATTERN = re.compile(r"[^a-z0-9]+")

_MEASUREMENT_TOKENS = {
    "g",
    "gram",
    "grams",
    "mg",
    "milligram",
    "milligrams",
    "kg",
    "mcg",
    "µg",
    "ug",
    "microg",
    "iu",
    "iuu",
    "ppm",
    "ppb",
    "percent",
    "porcentaje",
    "ml",
    "milliliter",
    "millilitre",
    "milliliters",
    "l",
    "liter",
    "litre",
    "liters",
    "dl",
    "cl",
    "oz",
    "ounce",
    "ounces",
}
_MEASUREMENT_CONNECTORS = {"per", "por", "x", "each", "ratio", "sobre"}
_MEASUREMENT_PATTERN = re.compile(
    r"^\d{1,6}(mg|g|kg|mcg|µg|ug|microg|ml|l|dl|cl|oz|iu|ppm|ppb|percent)$"
)

_SPECIAL_CHAR_TRANSLATIONS = {
    ord("µ"): "micro",
    ord("μ"): "micro",
    ord("α"): "alpha",
    ord("β"): "beta",
    ord("γ"): "gamma",
    ord("δ"): "delta",
    ord("θ"): "theta",
    ord("λ"): "lambda",
    ord("ω"): "omega",
    ord("Ω"): "omega",
    ord("®"): "",
    ord("™"): "",
    ord("½"): " 1/2",
    ord("¼"): " 1/4",
    ord("¾"): " 3/4",
    ord("⅛"): " 1/8",
    ord("⅜"): " 3/8",
    ord("⅝"): " 5/8",
    ord("⅞"): " 7/8",
    ord("ß"): "beta",
    ord("œ"): "oe",
    ord("Œ"): "oe",
}


def _strip_accents(value: str) -> str:
    translated = value.translate(_SPECIAL_CHAR_TRANSLATIONS)
    return "".join(
        char for char in unicodedata.normalize("NFKD", translated) if not unicodedata.combining(char)
    )


def _basic_normalize(value: Optional[str]) -> str:
    if not value:
        return ""
    lowered = _strip_accents(str(value).strip().lower())
    if not lowered:
        return ""
    normalized = _NORMALIZATION_PATTERN.sub(" ", lowered)
    return re.sub(r"\s+", " ", normalized).strip()


def _build_synonym_map(raw_map: Dict[str, str]) -> Dict[str, str]:
    aliases: Dict[str, str] = {}
    for raw_key, raw_value in raw_map.items():
        key = _basic_normalize(raw_key)
        value = _basic_normalize(raw_value)
        if not key:
            continue
        aliases[key] = value or key
    return aliases


def _is_numeric_token(token: str) -> bool:
    if not token:
        return False
    if token.isdigit():
        return True
    try:
        float(token)
        return True
    except ValueError:
        return False


def _looks_like_measurement(tokens: List[str], compact: str) -> bool:
    if not tokens:
        return False
    if _MEASUREMENT_PATTERN.match(compact):
        return True
    measurement_tokens = 0
    for token in tokens:
        if token in _MEASUREMENT_TOKENS:
            measurement_tokens += 1
            continue
        if token in _MEASUREMENT_CONNECTORS:
            continue
        if _is_numeric_token(token):
            continue
        # tokens such as "microg" may appear concatenated after normalization
        for unit in _MEASUREMENT_TOKENS:
            if unit and token.endswith(unit):
                measurement_tokens += 1
                break
        else:
            return False
    return measurement_tokens > 0


_RAW_SYNONYMS: Dict[str, str] = {
    "agua": "water",
    "aqua": "water",
    "eau": "water",
    "ácido hialurónico": "hyaluronic acid",
    "acido hialuronico": "hyaluronic acid",
    "hialuronic acid": "hyaluronic acid",
    "ácido salicílico": "salicylic acid",
    "acido salicilico": "salicylic acid",
    "ácido láctico": "lactic acid",
    "acido lactico": "lactic acid",
    "ácido glicólico": "glycolic acid",
    "acido glicolico": "glycolic acid",
    "vitamina c": "vitamin c",
    "ácido ascórbico": "ascorbic acid",
    "acido ascorbico": "ascorbic acid",
    "vitamina e": "vitamin e",
    "niacina": "niacinamide",
    "niacinamida": "niacinamide",
    "nicotinamida": "niacinamide",
    "aceite de coco": "coconut oil",
    "aceite de jojoba": "jojoba oil",
    "aceite de argán": "argan oil",
    "aceite de argan": "argan oil",
    "aceite de girasol": "sunflower seed oil",
    "aceite de oliva": "olive oil",
    "aceite de almendras": "sweet almond oil",
    "aceite mineral": "mineral oil",
    "dióxido de titanio": "titanium dioxide",
    "dioxido de titanio": "titanium dioxide",
    "óxido de zinc": "zinc oxide",
    "oxido de zinc": "zinc oxide",
    "extracto de aloe": "aloe vera",
    "extracto de avena": "avena sativa kernel extract",
    "extracto de camomila": "chamomile extract",
    "manteca de karite": "shea butter",
    "manteca de karité": "shea butter",
    "manteca de cacao": "cocoa butter",
    "pro-vitamina b5": "panthenol",
    "alpha tocopherol": "vitamin e",
    "dl alpha tocopherol": "vitamin e",
    "dl-alpha tocopherol": "vitamin e",
    "tocopheryl acetate": "vitamin e",
    "vitamin e acetate": "vitamin e",
    "vit e acetate": "vitamin e",
    "vitamin e oil": "vitamin e",
    "alpha tocopherol acetate": "vitamin e",
    "alpha-tocopherol": "vitamin e",
    "alpha-tocopherol acetate": "vitamin e",
    "beta carotene": "beta-carotene",
    "ß carotene": "beta-carotene",
    "ß-carotene": "beta-carotene",
}

SYNONYM_ALIASES: Dict[str, str] = _build_synonym_map(_RAW_SYNONYMS)


@lru_cache(maxsize=2048)
def normalize_ingredient_name(value: Optional[str]) -> str:
    """Normalize ingredient names for consistent lookups."""
    normalized = _basic_normalize(value)
    if not normalized:
        return ""
    compact = normalized.replace(" ", "")
    if compact in _MEASUREMENT_TOKENS or normalized in _MEASUREMENT_TOKENS:
        return ""
    tokens = normalized.split()
    if compact.isdigit() or _looks_like_measurement(tokens, compact):
        return ""
    return SYNONYM_ALIASES.get(normalized, normalized)


def normalize_ingredient_names(values: Iterable[str]) -> List[str]:
    """Normalize a collection of ingredient names preserving order."""
    if not values:
        return []
    seen: set[str] = set()
    result: List[str] = []
    for raw in values:
        normalized = normalize_ingredient_name(raw)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


async def normalize_ingredient_name_with_ollama(value: Optional[str]) -> str:
    """
    Enhanced ingredient normalization using Ollama for better accuracy
    
    Args:
        value: Raw ingredient name to normalize
        
    Returns:
        Normalized ingredient name
    """
    if not value or not value.strip():
        return ""
    
    # First try basic normalization
    basic_normalized = normalize_ingredient_name(value)
    if not basic_normalized:
        return ""
    
    # If Ollama is available, try to enhance the normalization
    if OLLAMA_AVAILABLE and ollama_integration.is_available():
        try:
            # Create a prompt for ingredient name correction
            prompt = f"""
Please correct and normalize this cosmetic ingredient name to its proper INCI (International Nomenclature of Cosmetic Ingredients) name:

Ingredient: {value}

Please provide:
1. The correct INCI name
2. If it's already correct, return it as-is
3. If it's a common misspelling, provide the correct spelling
4. If it's a brand name, provide the INCI equivalent

Return only the corrected ingredient name, nothing else.
"""
            
            ollama_result = await enhance_ocr_text_with_ollama(prompt)
            
            if ollama_result.success and ollama_result.content:
                # Extract the corrected name from the response
                corrected_name = _extract_ingredient_from_ollama_response(ollama_result.content)
                if corrected_name and corrected_name != value:
                    logger.info(f"Ollama corrected '{value}' to '{corrected_name}'")
                    # Apply basic normalization to the corrected name
                    return normalize_ingredient_name(corrected_name)
                else:
                    logger.debug(f"Ollama did not suggest changes for '{value}'")
            else:
                logger.warning(f"Ollama normalization failed for '{value}': {ollama_result.error}")
                
        except Exception as e:
            logger.error(f"Error in Ollama ingredient normalization: {e}")
    
    # Return basic normalization if Ollama is not available or fails
    return basic_normalized


def _extract_ingredient_from_ollama_response(content: str) -> Optional[str]:
    """
    Extract ingredient name from Ollama response
    
    Args:
        content: Ollama response content
        
    Returns:
        Extracted ingredient name or None
    """
    try:
        # Clean up the response
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip metadata lines
            if any(pattern in line.lower() for pattern in [
                'model=', 'created_at=', 'done=', 'total_duration=',
                'load_duration=', 'prompt_eval_count=', 'eval_count=',
                'message=', 'role=', 'content=', 'thinking=',
                'images=', 'tool_name=', 'tool_calls='
            ]):
                continue
            
            # Skip common prefixes
            if line.lower().startswith(('ingredient:', 'corrected:', 'inci name:', 'proper name:')):
                line = line.split(':', 1)[1].strip()
            
            # Remove quotes and extra whitespace
            line = line.strip('"\'')
            
            if line and len(line) > 2:
                return line
        
        return None
        
    except Exception as e:
        logger.warning(f"Error extracting ingredient from Ollama response: {e}")
        return None


async def normalize_ingredient_names_with_ollama(values: Iterable[str]) -> List[str]:
    """
    Enhanced normalization of ingredient names using Ollama for better accuracy
    
    Args:
        values: Collection of ingredient names to normalize
        
    Returns:
        List of normalized ingredient names
    """
    if not values:
        return []
    
    seen: set[str] = set()
    result: List[str] = []
    
    for raw in values:
        normalized = await normalize_ingredient_name_with_ollama(raw)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    
    return result


def canonicalize_ingredients(values: Iterable[str]) -> List[str]:
    """Return display-ready canonical ingredient names without duplicates."""
    normalized_entries = normalize_ingredient_names(values)
    canonical: List[str] = []
    seen: set[str] = set()
    for normalized in normalized_entries:
        data = get_ingredient_data(normalized)
        if data:
            display = str(data.get("name") or normalized).strip()
        else:
            display = " ".join(part.capitalize() for part in normalized.split())
        key = display.lower()
        if not key or key in seen:
            continue
        seen.add(key)
        canonical.append(display)
    return canonical

# Get DATABASE_URL with fallback for Railway deployment
DATABASE_URL = os.getenv("DATABASE_URL")

# If DATABASE_URL is not set, try to construct it from individual components
if not DATABASE_URL:
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "mommyshops")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "")
    
    if db_password:
        DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    else:
        DATABASE_URL = f"postgresql://{db_user}@{db_host}:{db_port}/{db_name}"

# Validate DATABASE_URL
if not DATABASE_URL:
    logger.warning("DATABASE_URL not found. Falling back to SQLite for development")
    DATABASE_URL = "sqlite:///./dev_sqlite.db"
else:
    # Check if it's a PostgreSQL URL and if we can connect
    if DATABASE_URL.startswith("postgresql://"):
        try:
            # Test the connection
            test_engine = create_engine(DATABASE_URL)
            with test_engine.connect() as conn:
                pass
            logger.info("PostgreSQL connection successful")
        except Exception as e:
            logger.warning("PostgreSQL connection failed: %s", e)
            logger.warning("Falling back to SQLite for development")
            DATABASE_URL = "sqlite:///./dev_sqlite.db"

logger.info("Using DATABASE_URL: %s...", DATABASE_URL[:50])

try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    logger.info("Database connection configured successfully")
except Exception as e:
    logger.error("Database connection failed: %s", e)
    logger.warning("App will start but database features will be disabled")
    # Create a dummy engine to prevent crashes
    engine = None
    SessionLocal = None
    Base = None

# Domain models


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=True)
    email = Column(String(128), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=True)
    # Google OAuth2 fields
    google_id = Column(String(128), unique=True, index=True, nullable=True)
    google_name = Column(String(128), nullable=True)
    google_picture = Column(String(512), nullable=True)
    auth_provider = Column(String(32), default='local')  # 'local' or 'google'
    firebase_uid = Column(String(128), unique=True, index=True, nullable=True)  # Firebase UID for dual write
    skin_face = Column(String(64))
    hair_type = Column(String(64))
    goals_face = Column(JSON)
    climate = Column(String(64))
    skin_body = Column(JSON)
    goals_body = Column(JSON)
    hair_porosity = Column(JSON)
    goals_hair = Column(JSON)
    hair_thickness_scalp = Column(JSON)
    conditions = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    routines = relationship("Routine", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")


class Routine(Base):
    __tablename__ = "routines"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    products = Column(JSON)
    extracted_ingredients = Column(JSON)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="routines")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    brand = Column(String(128))
    ingredients = Column(JSON)
    category = Column(String(64))
    eco_score = Column(Float)
    risk_level = Column(String(64))
    extra_metadata = Column(JSON)
    ollama_summary = Column(JSON)
    rating_count = Column(Integer, default=0)
    rating_average = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    recommendations_source = relationship(
        "Recommendation",
        back_populates="original_product",
        foreign_keys="Recommendation.original_product_id",
    )
    recommendations_substitute = relationship(
        "Recommendation",
        back_populates="substitute_product",
        foreign_keys="Recommendation.substitute_product_id",
    )


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    routine_id = Column(Integer, ForeignKey("routines.id", ondelete="SET NULL"), nullable=True)
    original_product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    substitute_product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    original_product_name = Column(String(255))
    substitute_product_name = Column(String(255))
    reason = Column(Text)
    status = Column(String(32), server_default="draft")
    rating_count = Column(Integer, default=0)
    rating_average = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="recommendations")
    routine = relationship("Routine")
    original_product = relationship("Product", foreign_keys=[original_product_id], back_populates="recommendations_source")
    substitute_product = relationship("Product", foreign_keys=[substitute_product_id], back_populates="recommendations_substitute")
    feedbacks = relationship("RecommendationFeedback", back_populates="recommendation", cascade="all, delete-orphan")


class Ingredient(Base):
    __tablename__ = "ingredients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    eco_score = Column(Float)  # 0-100 based on EWG or average
    risk_level = Column(String)  # e.g., "seguro", "cancerígeno"
    benefits = Column(Text)  # e.g., "Hidrata la piel"
    risks_detailed = Column(Text)  # e.g., "Puede causar irritación en dosis altas"
    sources = Column(String)  # e.g., "FDA, EWG, PubChem, IARC, INVIMA, COSING"
    ollama_enrichment = Column(JSON)


class RecommendationFeedback(Base):
    __tablename__ = "recommendation_feedback"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id", ondelete="CASCADE"), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    rating = Column(Float, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    recommendation = relationship("Recommendation", back_populates="feedbacks")
    user = relationship("User")

def get_db():
    """Get database session with proper error handling."""
    if SessionLocal is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    db = SessionLocal()
    try:
        yield db
    except Exception as exc:
        logger.exception("Database session error", extra={"phase": "get_db"})
        db.rollback()
        raise
    finally:
        db.close()

async def enrich_ingredients_with_ollama(
    db: Session,
    ingredient_names: Optional[Iterable[str]] = None,
    user_conditions: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    """Enrich stored ingredients with Ollama insights (riesgos, alternativas)."""
    from ollama_enrichment import enrich_ingredient_with_ollama

    if ingredient_names:
        query = db.query(Ingredient).filter(Ingredient.name.in_(ingredient_names))
    else:
        query = db.query(Ingredient)

    targets = query.all()
    if not targets:
        return {"processed": 0, "updated": 0, "errors": []}

    results: Dict[str, Any] = {"processed": 0, "updated": 0, "errors": []}
    tasks = []
    for ingredient in targets:
        results["processed"] += 1
        tasks.append(enrich_ingredient_with_ollama(ingredient.name, list(user_conditions or [])))

    enriched_payloads = await asyncio.gather(*tasks, return_exceptions=True)

    for ingredient, payload in zip(targets, enriched_payloads):
        if isinstance(payload, Exception):
            logger.error("Ollama enrichment failed for %s: %s", ingredient.name, payload)
            results["errors"].append({"ingredient": ingredient.name, "error": str(payload)})
            continue

        if payload:
            ingredient.ollama_enrichment = payload
            results["updated"] += 1

    db.commit()
    return results

def enrich_ingredients_with_ollama_sync(
    db: Session,
    ingredient_names: Optional[Iterable[str]] = None,
    user_conditions: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    """Synchronous helper for scripts that enforces a fresh event loop."""
    return asyncio.run(
        enrich_ingredients_with_ollama(db, ingredient_names=ingredient_names, user_conditions=user_conditions)
    )

# Import API functions from api_utils_production
from api_utils_production import fetch_ingredient_data

async def update_database(db: Session):
    """Update database with ingredient data using Ollama-powered summaries."""
    try:
        # Use Ollama enrichment for database updates
        ingredients_to_fetch = [
            "parabenos", "glicerina", "aqua", "sodium laureth sulfate",
            "cocamidopropyl betaine", "formaldehído", "ftalatos", "retinol",
            "hyaluronic acid", "niacinamide", "salicylic acid"
        ]
        
        async with httpx.AsyncClient() as client:
            for name in ingredients_to_fetch:
                try:
                    # Try to get data from APIs directly
                    data = await fetch_ingredient_data(name, client)
                    
                    db_ing = Ingredient(
                        name=name,
                        eco_score=data.get("eco_score", 50.0),
                        risk_level=data.get("risk_level", "desconocido"),
                        benefits=data.get("benefits", "No disponible"),
                        risks_detailed=data.get("risks_detailed", "No disponible"),
                        sources=data.get("sources", "None")
                    )
                    
                    existing = db.query(Ingredient).filter(Ingredient.name == name).first()
                    if existing:
                        existing.eco_score = db_ing.eco_score
                        existing.risk_level = db_ing.risk_level
                        existing.benefits = db_ing.benefits
                        existing.risks_detailed = db_ing.risks_detailed
                        existing.sources = db_ing.sources
                    else:
                        db.add(db_ing)
                    db.commit()
                    logger.info("Successfully updated ingredient", extra={"ingredient": name})
                except Exception as e:
                    logger.exception("Error updating ingredient", extra={"ingredient": name})
                    db.rollback()
                    continue
    except Exception as e:
        logger.exception("Error in update_database")

# Comprehensive local ingredient database
# Comprehensive local ingredient database
_RAW_LOCAL_INGREDIENT_DATABASE: Dict[str, Dict[str, Any]] = {
    "alpha hydroxy acids": {
        "eco_score": 65.0,
        "risk_level": "riesgo bajo",
        "benefits": "Exfoliante químico, mejora textura, reduce manchas",
        "risks_detailed": "Puede causar irritación, aumenta sensibilidad al sol",
        "sources": "Local Database + FDA + CIR"
    },
    "aqua": {
        "eco_score": 95.0,
        "risk_level": "seguro",
        "benefits": "Hidratante base, solvente natural",
        "risks_detailed": "Ninguno conocido",
        "sources": "Local Database"
    },
    "benzene": {
        "eco_score": 10.0,
        "risk_level": "riesgo alto",
        "benefits": "Solvente industrial",
        "risks_detailed": "Carcinógeno conocido, puede causar leucemia, irritante",
        "sources": "Local Database + IARC + FDA"
    },
    "beta hydroxy acid": {
        "eco_score": 70.0,
        "risk_level": "riesgo bajo",
        "benefits": "Exfoliante químico, trata acné, mejora textura",
        "risks_detailed": "Puede causar irritación, evitar durante embarazo",
        "sources": "Local Database + FDA + CIR"
    },
    "beta carotene": {
        "eco_score": 85.0,
        "risk_level": "seguro",
        "benefits": "Antioxidante, apoyo a la síntesis de vitamina A",
        "risks_detailed": "Generalmente seguro, precaución en fumadores por dosis elevadas",
        "sources": "Local Database + FDA + CIR"
    },
    "ceramides": {
        "eco_score": 90.0,
        "risk_level": "seguro",
        "benefits": "Restaura barrera cutánea, hidrata, protege",
        "risks_detailed": "Muy seguro, componente natural de la piel",
        "sources": "Local Database + FDA + CIR"
    },
    "coal tar": {
        "eco_score": 10.0,
        "risk_level": "riesgo alto",
        "benefits": "Colorante, tratamiento de psoriasis",
        "risks_detailed": "Carcinógeno conocido, puede causar cáncer de piel",
        "sources": "Local Database + IARC + FDA"
    },
    "dimethicone": {
        "eco_score": 60.0,
        "risk_level": "riesgo bajo",
        "benefits": "Suavizante, mejora textura, protege barrera cutánea",
        "risks_detailed": "No biodegradable, puede acumularse en el medio ambiente",
        "sources": "Local Database + FDA + CIR"
    },
    "formaldehyde": {
        "eco_score": 20.0,
        "risk_level": "riesgo alto",
        "benefits": "Conservante, previene crecimiento bacteriano",
        "risks_detailed": "Carcinógeno conocido, irritante de piel y ojos, puede causar alergias",
        "sources": "Local Database + IARC + FDA"
    },
    "glycerin": {
        "eco_score": 85.0,
        "risk_level": "seguro",
        "benefits": "Hidratante intenso, mejora la textura de la piel, suavizante",
        "risks_detailed": "Muy seguro, raramente causa irritación",
        "sources": "Local Database + FDA Approved"
    },
    "hyaluronic acid": {
        "eco_score": 85.0,
        "risk_level": "seguro",
        "benefits": "Hidratante intenso, mejora elasticidad, reduce arrugas",
        "risks_detailed": "Muy seguro, raramente causa irritación",
        "sources": "Local Database + CIR Approved"
    },
    "lanolin": {
        "eco_score": 50.0,
        "risk_level": "riesgo medio",
        "benefits": "Hidratante natural, emoliente",
        "risks_detailed": "Puede causar alergias, derivado de ovejas",
        "sources": "Local Database + FDA + SCCS"
    },
    "lead": {
        "eco_score": 5.0,
        "risk_level": "riesgo alto",
        "benefits": "Colorante (prohibido en cosméticos)",
        "risks_detailed": "Neurotóxico, prohibido en cosméticos en la mayoría de países",
        "sources": "Local Database + FDA + EU Regulations"
    },
    "mercury": {
        "eco_score": 5.0,
        "risk_level": "riesgo alto",
        "benefits": "Conservante (prohibido en cosméticos)",
        "risks_detailed": "Neurotóxico, prohibido en cosméticos en la mayoría de países",
        "sources": "Local Database + FDA + EU Regulations"
    },
    "mineral oil": {
        "eco_score": 40.0,
        "risk_level": "riesgo medio",
        "benefits": "Hidratante, protector, económico",
        "risks_detailed": "Puede ser comedogénico, derivado del petróleo",
        "sources": "Local Database + FDA + SCCS"
    },
    "niacinamide": {
        "eco_score": 80.0,
        "risk_level": "riesgo bajo",
        "benefits": "Regula producción de sebo, mejora textura, antiinflamatorio",
        "risks_detailed": "Puede causar irritación leve en concentraciones altas",
        "sources": "Local Database + FDA + CIR"
    },
    "octocrylene": {
        "eco_score": 35.0,
        "risk_level": "riesgo medio",
        "benefits": "Filtro UVB, protege contra quemaduras solares",
        "risks_detailed": "Posible irritante ocular, disruptor endocrino potencial, tóxico para corales",
        "sources": "Local Database + FDA + SCCS"
    },
    "parabens": {
        "eco_score": 30.0,
        "risk_level": "riesgo medio",
        "benefits": "Conservante efectivo, previene contaminación microbiana",
        "risks_detailed": "Disruptor endocrino potencial, puede interferir con hormonas",
        "sources": "Local Database + FDA + SCCS"
    },
    "peptides": {
        "eco_score": 85.0,
        "risk_level": "seguro",
        "benefits": "Anti-envejecimiento, mejora elasticidad, reduce arrugas",
        "risks_detailed": "Muy seguro, raramente causa efectos adversos",
        "sources": "Local Database + FDA + CIR"
    },
    "phthalates": {
        "eco_score": 20.0,
        "risk_level": "riesgo alto",
        "benefits": "Plastificante, mejora textura",
        "risks_detailed": "Disruptor endocrino, puede afectar desarrollo reproductivo",
        "sources": "Local Database + FDA + SCCS"
    },
    "retinol": {
        "eco_score": 45.0,
        "risk_level": "riesgo medio",
        "benefits": "Anti-envejecimiento, mejora la textura de la piel, reduce arrugas y manchas",
        "risks_detailed": "Evitar durante el embarazo, puede causar irritación y sensibilidad al sol",
        "sources": "Local Database + FDA + CIR"
    },
    "salicylic acid": {
        "eco_score": 70.0,
        "risk_level": "riesgo bajo",
        "benefits": "Exfoliante químico, trata acné, mejora textura",
        "risks_detailed": "Puede causar irritación, evitar durante embarazo",
        "sources": "Local Database + FDA + CIR"
    },
    "sodium lauryl sulfate": {
        "eco_score": 40.0,
        "risk_level": "riesgo medio",
        "benefits": "Agente espumante, limpiador efectivo",
        "risks_detailed": "Puede causar irritación en piel sensible, reseca la piel",
        "sources": "Local Database + FDA + SCCS"
    },
    "squalane": {
        "eco_score": 85.0,
        "risk_level": "seguro",
        "benefits": "Hidratante natural, suavizante, no comedogénico",
        "risks_detailed": "Muy seguro, similar a los lípidos naturales de la piel",
        "sources": "Local Database + FDA + CIR"
    },
    "titanium dioxide": {
        "eco_score": 75.0,
        "risk_level": "riesgo bajo",
        "benefits": "Filtro UV físico, protege contra rayos UVA/UVB",
        "risks_detailed": "Precaución con nanopartículas, puede dejar residuo blanco",
        "sources": "Local Database + FDA + CIR"
    },
    "toluene": {
        "eco_score": 15.0,
        "risk_level": "riesgo alto",
        "benefits": "Solvente industrial",
        "risks_detailed": "Neurotóxico, puede causar daño al sistema nervioso",
        "sources": "Local Database + IARC + FDA"
    },
    "triclosan": {
        "eco_score": 25.0,
        "risk_level": "riesgo alto",
        "benefits": "Antibacteriano, conservante",
        "risks_detailed": "Disruptor endocrino, puede contribuir a resistencia bacteriana",
        "sources": "Local Database + FDA + EWG Research"
    },
    "vitamin c": {
        "eco_score": 75.0,
        "risk_level": "riesgo bajo",
        "benefits": "Antioxidante, ilumina la piel, estimula colágeno",
        "risks_detailed": "Puede causar irritación, inestable con la luz",
        "sources": "Local Database + FDA + CIR"
    },
    "vitamin e": {
        "eco_score": 80.0,
        "risk_level": "seguro",
        "benefits": "Antioxidante liposoluble, protege contra radicales libres",
        "risks_detailed": "Generalmente seguro, puede causar irritación leve en pieles sensibles",
        "sources": "Local Database + FDA + CIR"
    },
    "water": {
        "eco_score": 95.0,
        "risk_level": "seguro",
        "benefits": "Hidratante base, solvente natural",
        "risks_detailed": "Ninguno conocido",
        "sources": "Local Database"
    },
    "zinc oxide": {
        "eco_score": 80.0,
        "risk_level": "riesgo bajo",
        "benefits": "Filtro UV físico, antiinflamatorio, cicatrizante",
        "risks_detailed": "Puede dejar residuo blanco, precaución con nanopartículas",
        "sources": "Local Database + FDA + CIR"
    },
    # Ingredientes adicionales comunes en cosméticos
    "parfum": {
        "eco_score": 30.0,
        "risk_level": "riesgo medio",
        "benefits": "Proporciona aroma agradable al producto",
        "risks_detailed": "Puede causar alergias o irritación en piel sensible. Contiene múltiples alérgenos no divulgados",
        "sources": "Local Database + FDA + SCCS + EWG"
    },
    "citric acid": {
        "eco_score": 80.0,
        "risk_level": "seguro",
        "benefits": "Regulador de pH, exfoliante suave",
        "risks_detailed": "No carcinogénico; irritación rara. Ingrediente natural y biodegradable",
        "sources": "Local Database + FDA + CIR + EWG"
    },
    "cetearyl alcohol": {
        "eco_score": 60.0,
        "risk_level": "riesgo bajo",
        "benefits": "Emulsificante y espesante, mejora textura",
        "risks_detailed": "Generalmente seguro, puede causar irritación leve en piel sensible",
        "sources": "Local Database + FDA + CIR + EWG"
    },
    "cetyl alcohol": {
        "eco_score": 65.0,
        "risk_level": "riesgo bajo",
        "benefits": "Emulsificante, espesante, estabilizador de emulsiones",
        "risks_detailed": "Generalmente seguro, puede causar irritación leve en piel sensible",
        "sources": "Local Database + FDA + CIR + EWG"
    },
    "glyceryl stearate": {
        "eco_score": 70.0,
        "risk_level": "riesgo bajo",
        "benefits": "Emulsificante, estabilizador, suavizante",
        "risks_detailed": "Generalmente seguro, puede causar irritación leve",
        "sources": "Local Database + FDA + CIR + EWG"
    },
    "peg-100 stearate": {
        "eco_score": 50.0,
        "risk_level": "riesgo medio",
        "benefits": "Emulsificante sintético, mejora textura del producto",
        "risks_detailed": "Puede causar irritación, derivado del petróleo",
        "sources": "Local Database + FDA + SCCS + EWG"
    },
    "triethanolamine": {
        "eco_score": 40.0,
        "risk_level": "riesgo medio",
        "benefits": "Regulador de pH, emulsificante",
        "risks_detailed": "Puede causar irritación, evitar contacto con ojos",
        "sources": "Local Database + FDA + CIR + EWG"
    },
    "phenoxyethanol": {
        "eco_score": 40.0,
        "risk_level": "riesgo bajo",
        "benefits": "Conservante efectivo, previene contaminación microbiana",
        "risks_detailed": "Generalmente seguro, puede causar irritación leve en piel sensible en concentraciones >1%",
        "sources": "Local Database + FDA + SCCS + EWG"
    },
    "aloe barbadensis leaf extract": {
        "eco_score": 90.0,
        "risk_level": "seguro",
        "benefits": "Hidratante natural, antiinflamatorio, cicatrizante",
        "risks_detailed": "Muy seguro, raramente causa efectos adversos",
        "sources": "Local Database + FDA + CIR"
    },
    "aloe vera": {
        "eco_score": 90.0,
        "risk_level": "seguro",
        "benefits": "Hidratante natural, antiinflamatorio, cicatrizante",
        "risks_detailed": "Muy seguro, raramente causa efectos adversos",
        "sources": "Local Database + FDA + CIR"
    },
    "cetearyl alcohol": {
        "eco_score": 60.0,
        "risk_level": "riesgo bajo",
        "benefits": "Emulsificante, estabilizador, mejora textura",
        "risks_detailed": "Generalmente seguro, puede causar irritación leve",
        "sources": "Local Database + FDA + CIR"
    },
    "ethylhexylglycerin": {
        "eco_score": 70.0,
        "risk_level": "riesgo bajo",
        "benefits": "Conservante suave, hidratante, mejora penetración",
        "risks_detailed": "Generalmente seguro, raramente causa irritación",
        "sources": "Local Database + FDA + SCCS"
    },
    "acrylates/c10-30 alkyl acrylate crosspolymer": {
        "eco_score": 50.0,
        "risk_level": "riesgo medio",
        "benefits": "Espesante, estabilizador de emulsión",
        "risks_detailed": "Puede causar irritación en piel sensible",
        "sources": "Local Database + FDA + CIR"
    },
    "avena sativa kernel extract": {
        "eco_score": 85.0,
        "risk_level": "seguro",
        "benefits": "Hidratante natural, antiinflamatorio, suavizante",
        "risks_detailed": "Muy seguro, ingrediente natural de avena",
        "sources": "Local Database + FDA + CIR"
    },
    "oat extract": {
        "eco_score": 85.0,
        "risk_level": "seguro",
        "benefits": "Hidratante natural, antiinflamatorio, suavizante",
        "risks_detailed": "Muy seguro, ingrediente natural de avena",
        "sources": "Local Database + FDA + CIR"
    },
    "isopropyl palmitate": {
        "eco_score": 45.0,
        "risk_level": "riesgo medio",
        "benefits": "Emoliente, mejora textura, facilita aplicación",
        "risks_detailed": "Puede ser comedogénico, puede causar irritación. Tóxico en altas dosis para poros",
        "sources": "Local Database + FDA + CIR + EWG"
    },
    "glyceryl stearate": {
        "eco_score": 70.0,
        "risk_level": "riesgo bajo",
        "benefits": "Emulsificante, estabilizador, suavizante",
        "risks_detailed": "Generalmente seguro, puede causar irritación leve",
        "sources": "Local Database + FDA + CIR"
    },
    "peg-100 stearate": {
        "eco_score": 50.0,
        "risk_level": "riesgo medio",
        "benefits": "Emulsificante, mejora textura del producto",
        "risks_detailed": "Puede causar irritación, derivado del petróleo",
        "sources": "Local Database + FDA + SCCS"
    },
    "gossypium herbaceum seed oil": {
        "eco_score": 75.0,
        "risk_level": "riesgo bajo",
        "benefits": "Hidratante natural, emoliente, rico en ácidos grasos",
        "risks_detailed": "Generalmente seguro, aceite de semilla de algodón",
        "sources": "Local Database + FDA + CIR"
    },
    "cotton seed oil": {
        "eco_score": 75.0,
        "risk_level": "riesgo bajo",
        "benefits": "Hidratante natural, emoliente, rico en ácidos grasos",
        "risks_detailed": "Generalmente seguro, aceite de semilla de algodón",
        "sources": "Local Database + FDA + CIR"
    },
    "stearic acid": {
        "eco_score": 60.0,
        "risk_level": "riesgo bajo",
        "benefits": "Emulsificante, estabilizador, suavizante",
        "risks_detailed": "Generalmente seguro, ácido graso natural",
        "sources": "Local Database + FDA + CIR"
    },
    "helianthus annuus seed oil": {
        "eco_score": 85.0,
        "risk_level": "seguro",
        "benefits": "Hidratante natural, rico en vitamina E, antioxidante",
        "risks_detailed": "Muy seguro, aceite de girasol natural",
        "sources": "Local Database + FDA + CIR"
    },
    "sunflower seed oil": {
        "eco_score": 85.0,
        "risk_level": "seguro",
        "benefits": "Hidratante natural, rico en vitamina E, antioxidante",
        "risks_detailed": "Muy seguro, aceite de girasol natural",
        "sources": "Local Database + FDA + CIR"
    },
    "triethanolamine": {
        "eco_score": 40.0,
        "risk_level": "riesgo medio",
        "benefits": "Ajustador de pH, emulsificante",
        "risks_detailed": "Puede causar irritación, evitar en piel sensible",
        "sources": "Local Database + FDA + SCCS"
    },
    "aqua": {
        "eco_score": 95.0,
        "risk_level": "seguro",
        "benefits": "Hidratante base, solvente natural",
        "risks_detailed": "Ninguno conocido",
        "sources": "Local Database"
    },
    "water": {
        "eco_score": 95.0,
        "risk_level": "seguro",
        "benefits": "Hidratante base, solvente natural",
        "risks_detailed": "Ninguno conocido",
        "sources": "Local Database"
    },
    "octocrylene": {
        "eco_score": 35.0,
        "risk_level": "riesgo medio",
        "benefits": "Filtro UVB, protege contra quemaduras solares",
        "risks_detailed": "Posible irritante ocular, disruptor endocrino potencial, tóxico para corales",
        "sources": "Local Database + FDA + SCCS"
    },
    "formaldehyde": {
        "eco_score": 20.0,
        "risk_level": "riesgo alto",
        "benefits": "Conservante, previene crecimiento bacteriano",
        "risks_detailed": "Carcinógeno conocido, irritante de piel y ojos, puede causar alergias",
        "sources": "Local Database + IARC + FDA"
    },
    "benzene": {
        "eco_score": 10.0,
        "risk_level": "riesgo alto",
        "benefits": "Solvente industrial",
        "risks_detailed": "Carcinógeno conocido, puede causar leucemia, irritante",
        "sources": "Local Database + IARC + FDA"
    },
    "parabens": {
        "eco_score": 30.0,
        "risk_level": "riesgo medio",
        "benefits": "Conservante efectivo, previene contaminación microbiana",
        "risks_detailed": "Disruptor endocrino potencial, puede interferir con hormonas",
        "sources": "Local Database + FDA + SCCS"
    },
    "sodium lauryl sulfate": {
        "eco_score": 40.0,
        "risk_level": "riesgo medio",
        "benefits": "Agente espumante, limpiador efectivo",
        "risks_detailed": "Puede causar irritación en piel sensible, reseca la piel",
        "sources": "Local Database + FDA + SCCS"
    },
    "dimethicone": {
        "eco_score": 60.0,
        "risk_level": "riesgo bajo",
        "benefits": "Suavizante, mejora textura, protege barrera cutánea",
        "risks_detailed": "No biodegradable, puede acumularse en el medio ambiente",
        "sources": "Local Database + FDA + CIR"
    },
    "hyaluronic acid": {
        "eco_score": 85.0,
        "risk_level": "seguro",
        "benefits": "Hidratante intenso, mejora elasticidad, reduce arrugas",
        "risks_detailed": "Muy seguro, raramente causa irritación",
        "sources": "Local Database + FDA + CIR"
    },
    "niacinamide": {
        "eco_score": 80.0,
        "risk_level": "riesgo bajo",
        "benefits": "Regula producción de sebo, mejora textura, antiinflamatorio",
        "risks_detailed": "Puede causar irritación leve en concentraciones altas",
        "sources": "Local Database + FDA + CIR"
    },
    "salicylic acid": {
        "eco_score": 70.0,
        "risk_level": "riesgo bajo",
        "benefits": "Exfoliante químico, trata acné, mejora textura",
        "risks_detailed": "Puede causar irritación, evitar durante embarazo",
        "sources": "Local Database + FDA + CIR"
    },
    "titanium dioxide": {
        "eco_score": 75.0,
        "risk_level": "riesgo bajo",
        "benefits": "Filtro UV físico, protege contra rayos UVA/UVB",
        "risks_detailed": "Precaución con nanopartículas, puede dejar residuo blanco",
        "sources": "Local Database + FDA + CIR"
    },
    "zinc oxide": {
        "eco_score": 80.0,
        "risk_level": "riesgo bajo",
        "benefits": "Filtro UV físico, antiinflamatorio, cicatrizante",
        "risks_detailed": "Puede dejar residuo blanco, precaución con nanopartículas",
        "sources": "Local Database + FDA + CIR"
    },
    # Ingredientes adicionales de la imagen específica para mejorar precisión
    "glyceryl stearate": {
        "eco_score": 70.0,
        "risk_level": "riesgo bajo",
        "benefits": "Emulsificante, estabilizador, suavizante",
        "risks_detailed": "Generalmente seguro, puede causar irritación leve",
        "sources": "Local Database + FDA + CIR + EWG"
    },
    "peg-100 stearate": {
        "eco_score": 50.0,
        "risk_level": "riesgo medio",
        "benefits": "Emulsificante sintético, mejora textura del producto",
        "risks_detailed": "Puede causar irritación, derivado del petróleo",
        "sources": "Local Database + FDA + SCCS + EWG"
    },
    "ethylhexylglycerin": {
        "eco_score": 70.0,
        "risk_level": "riesgo bajo",
        "benefits": "Conservante suave, hidratante, mejora penetración",
        "risks_detailed": "Generalmente seguro, raramente causa irritación",
        "sources": "Local Database + FDA + SCCS"
    },
    "isopropyl palmitate": {
        "eco_score": 45.0,
        "risk_level": "riesgo medio",
        "benefits": "Emoliente, mejora textura, facilita aplicación",
        "risks_detailed": "Puede ser comedogénico, puede causar irritación. Tóxico en altas dosis para poros",
        "sources": "Local Database + FDA + CIR + EWG"
    },
    "triethanolamine": {
        "eco_score": 40.0,
        "risk_level": "riesgo medio",
        "benefits": "Regulador de pH, emulsificante",
        "risks_detailed": "Puede causar irritación, evitar contacto con ojos",
        "sources": "Local Database + FDA + CIR + EWG"
    },
    "acrylates/c10-30 alkyl acrylate crosspolymer": {
        "eco_score": 50.0,
        "risk_level": "riesgo medio",
        "benefits": "Espesante, estabilizador de emulsión",
        "risks_detailed": "Puede causar irritación en piel sensible",
        "sources": "Local Database + FDA + CIR"
    },
    "helianthus annuus seed oil": {
        "eco_score": 85.0,
        "risk_level": "seguro",
        "benefits": "Hidratante natural, rico en vitamina E, antioxidante",
        "risks_detailed": "Muy seguro, aceite de girasol natural",
        "sources": "Local Database + FDA + CIR"
    },
    "aloe barbadensis leaf extract": {
        "eco_score": 90.0,
        "risk_level": "seguro",
        "benefits": "Hidratante natural, antiinflamatorio, cicatrizante",
        "risks_detailed": "Muy seguro, raramente causa efectos adversos",
        "sources": "Local Database + FDA + CIR"
    },
    "avena sativa kernel extract": {
        "eco_score": 85.0,
        "risk_level": "seguro",
        "benefits": "Hidratante natural, antiinflamatorio, suavizante",
        "risks_detailed": "Muy seguro, ingrediente natural de avena",
        "sources": "Local Database + FDA + CIR"
    },
    "gossypium herbaceum seed oil": {
        "eco_score": 75.0,
        "risk_level": "riesgo bajo",
        "benefits": "Hidratante natural, emoliente, rico en ácidos grasos",
        "risks_detailed": "Generalmente seguro, aceite de semilla de algodón",
        "sources": "Local Database + FDA + CIR"
    },
    "citric acid": {
        "eco_score": 80.0,
        "risk_level": "seguro",
        "benefits": "Regulador de pH, exfoliante suave",
        "risks_detailed": "No carcinogénico; irritación rara. Ingrediente natural y biodegradable",
        "sources": "Local Database + FDA + CIR + EWG"
    }
}


def _prepare_local_database(raw: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    prepared: Dict[str, Dict[str, Any]] = {}
    for original_name, payload in raw.items():
        normalized = _basic_normalize(original_name)
        if not normalized:
            continue
        entry = {
            "name": payload.get("name", original_name),
            "eco_score": float(payload.get("eco_score", 50.0) or 50.0),
            "risk_level": payload.get("risk_level", "desconocido"),
            "benefits": payload.get("benefits", "No disponible"),
            "risks_detailed": payload.get("risks_detailed", "No disponible"),
            "sources": payload.get("sources", "Local Database"),
        }
        prepared[normalized] = entry
    for alias_key, canonical_key in SYNONYM_ALIASES.items():
        if not canonical_key or alias_key == canonical_key:
            continue
        canonical_entry = prepared.get(canonical_key)
        if not canonical_entry:
            continue
        if alias_key not in prepared:
            prepared[alias_key] = dict(canonical_entry)
    return prepared


LOCAL_INGREDIENT_DATABASE = _prepare_local_database(_RAW_LOCAL_INGREDIENT_DATABASE)

def get_all_ingredient_names() -> List[str]:
    """Get all ingredient names from the database for dynamic corrections."""
    try:
        with SessionLocal() as db:
            ingredients = db.query(Ingredient.name).all()
            if not ingredients:
                return [entry.get("name", key) for key, entry in LOCAL_INGREDIENT_DATABASE.items()]
            return [ing.name for ing in ingredients]
    except Exception as e:
        logger.error("Error getting ingredient names: %s", e)
        return [entry.get("name", key) for key, entry in LOCAL_INGREDIENT_DATABASE.items()]

def get_ingredient_data(ingredient_name: str) -> Optional[Dict[str, Any]]:
    """Return local ingredient data using normalized and fuzzy lookups."""
    if not ingredient_name:
        return None

    normalized = normalize_ingredient_name(ingredient_name)
    if not normalized:
        return None

    exact = LOCAL_INGREDIENT_DATABASE.get(normalized)
    if exact:
        logger.debug("Exact local ingredient match found for '%s'", ingredient_name)
        return dict(exact)

    # Substring lookup for common OCR artifacts
    for key, payload in LOCAL_INGREDIENT_DATABASE.items():
        if normalized in key or key in normalized:
            logger.debug("Substring ingredient match '%s' -> '%s'", ingredient_name, payload.get("name", key))
            return dict(payload)

    candidate_keys = list(LOCAL_INGREDIENT_DATABASE.keys())
    if candidate_keys:
        close_matches = get_close_matches(normalized, candidate_keys, n=3, cutoff=0.68)
        for match in close_matches:
            payload = LOCAL_INGREDIENT_DATABASE.get(match)
            if payload:
                logger.debug("Close match ingredient '%s' -> '%s'", ingredient_name, payload.get("name", match))
                return dict(payload)

        # Manual best-score fallback for noisy OCR segments
        best_key = None
        best_score = 0.0
        for key in candidate_keys:
            ratio = SequenceMatcher(None, normalized, key).ratio()
            if ratio > best_score:
                best_key = key
                best_score = ratio
        if best_key and best_score >= 0.55:
            logger.debug("Sequence match ingredient '%s' -> '%s' (score %.2f)", ingredient_name, best_key, best_score)
            return dict(LOCAL_INGREDIENT_DATABASE[best_key])

    logger.debug("Local ingredient not found for '%s'", ingredient_name)
    return None


def get_all_ingredients() -> Dict[str, Dict[str, Any]]:
    """Get all ingredients from local lookup cache keyed by canonical name."""
    payload: Dict[str, Dict[str, Any]] = {}
    for entry in LOCAL_INGREDIENT_DATABASE.values():
        name = entry.get("name") or ""
        if not name:
            continue
        payload[name] = {
            "eco_score": entry.get("eco_score", 50.0),
            "risk_level": entry.get("risk_level", "desconocido"),
            "benefits": entry.get("benefits", "No disponible"),
            "risks_detailed": entry.get("risks_detailed", "No disponible"),
            "sources": entry.get("sources", "Local Database"),
        }
    return dict(sorted(payload.items(), key=lambda item: item[0]))

async def populate_comprehensive_database():
    """Populate database with comprehensive ingredient data from multiple sources"""
    import asyncio
    from ewg_scraper import EWGScraper
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Comprehensive ingredient list
    comprehensive_ingredients = [
        # Water and solvents
        "water", "aqua", "glycerin", "glycerol", "propylene glycol", "butylene glycol",
        "pentylene glycol", "hexylene glycol", "caprylyl glycol", "ethylhexylglycerin",
        
        # Humectants and moisturizers
        "hyaluronic acid", "sodium hyaluronate", "squalane", "squalene", "ceramides",
        "ceramide np", "ceramide ap", "ceramide eop", "ceramide eos", "ceramide ns",
        "cholesterol", "phytosphingosine", "sphingosine", "urea", "lactic acid",
        "sodium lactate", "panthenol", "pro-vitamin b5", "allantoin", "betaine",
        
        # Oils and butters
        "jojoba oil", "argan oil", "coconut oil", "olive oil", "sunflower oil",
        "safflower oil", "grapeseed oil", "rosehip oil", "evening primrose oil",
        "borage oil", "flaxseed oil", "hemp seed oil", "avocado oil", "sweet almond oil",
        "apricot kernel oil", "macadamia oil", "shea butter", "cocoa butter",
        "mango butter", "kokum butter", "illipe butter", "murumuru butter",
        
        # Vitamins and antioxidants
        "retinol", "retinyl palmitate", "retinyl acetate", "retinyl propionate",
        "vitamin c", "ascorbic acid", "ascorbyl palmitate", "ascorbyl glucoside",
        "magnesium ascorbyl phosphate", "sodium ascorbyl phosphate", "ascorbyl tetraisopalmitate",
        "vitamin e", "tocopherol", "tocopheryl acetate", "tocopheryl linoleate",
        "vitamin a", "vitamin b3", "niacinamide", "nicotinamide", "vitamin b5",
        "pantothenic acid", "panthenol", "vitamin d", "vitamin k", "biotin",
        "folic acid", "coenzyme q10", "ubiquinone", "ferulic acid", "resveratrol",
        "polyphenols", "flavonoids", "carotenoids", "lycopene", "beta-carotene",
        
        # Acids and exfoliants
        "salicylic acid", "glycolic acid", "lactic acid", "malic acid", "tartaric acid",
        "citric acid", "mandelic acid", "azelaic acid", "kojic acid", "phytic acid",
        "alpha hydroxy acid", "beta hydroxy acid", "polyhydroxy acid", "lactobionic acid",
        
        # Peptides and proteins
        "peptides", "copper peptides", "palmitoyl pentapeptide-4", "palmitoyl tripeptide-1",
        "palmitoyl tetrapeptide-7", "palmitoyl hexapeptide-12", "acetyl hexapeptide-8",
        "collagen", "elastin", "keratin", "silk protein", "wheat protein", "soy protein",
        "rice protein", "oat protein", "quinoa protein", "hemp protein",
        
        # Preservatives
        "parabens", "methylparaben", "ethylparaben", "propylparaben", "butylparaben",
        "isobutylparaben", "phenoxyethanol", "benzyl alcohol", "dehydroacetic acid",
        "sodium dehydroacetate", "potassium sorbate", "sodium benzoate", "sorbic acid",
        "caprylyl glycol", "ethylhexylglycerin", "chlorphenesin", "imidazolidinyl urea",
        "diazolidinyl urea", "quaternium-15", "formaldehyde", "formalin",
        
        # Surfactants and cleansers
        "sodium lauryl sulfate", "sodium laureth sulfate", "ammonium lauryl sulfate",
        "cocamidopropyl betaine", "cocamidopropyl hydroxysultaine", "coco-glucoside",
        "decyl glucoside", "lauryl glucoside", "sodium cocoamphoacetate",
        "sodium lauroamphoacetate", "cocamidopropyl dimethylamine", "cocamidopropyl dimethylamine oxide",
        "sorbitan oleate", "polysorbate 20", "polysorbate 80", "polysorbate 60",
        "lecithin", "soy lecithin", "sunflower lecithin", "phospholipids",
        
        # Emulsifiers and stabilizers
        "cetearyl alcohol", "cetyl alcohol", "stearyl alcohol", "behenyl alcohol",
        "glyceryl stearate", "glyceryl distearate", "glyceryl monostearate",
        "peg-100 stearate", "peg-40 stearate", "peg-20 stearate", "stearic acid",
        "palmitic acid", "myristic acid", "lauric acid", "oleic acid", "linoleic acid",
        "arachidonic acid", "eicosapentaenoic acid", "docosahexaenoic acid",
        
        # Silicones
        "dimethicone", "cyclomethicone", "cyclopentasiloxane", "cyclohexasiloxane",
        "phenyl trimethicone", "dimethiconol", "amodimethicone", "beeswax",
        "candelilla wax", "carnauba wax", "rice bran wax", "sunflower wax",
        
        # Colorants and pigments
        "titanium dioxide", "zinc oxide", "iron oxides", "ultramarines", "chromium oxide",
        "mica", "bismuth oxychloride", "pearl powder", "aluminum powder",
        "bronze powder", "copper powder", "gold powder", "silver powder",
        
        # Sunscreens
        "avobenzone", "octinoxate", "oxybenzone", "homosalate", "octisalate",
        "octocrylene", "padimate o", "ensulizole", "sulisobenzone", "dioxybenzone",
        "meradimate", "trolamine salicylate", "cinoxate", "aminobenzoic acid",
        "ethylhexyl methoxycinnamate", "ethylhexyl salicylate", "ethylhexyl triazone",
        "diethylamino hydroxybenzoyl hexyl benzoate", "bis-ethylhexyloxyphenol methoxyphenyl triazine",
        "methylene bis-benzotriazolyl tetramethylbutylphenol", "tris-biphenyl triazine",
        
        # Fragrances and essential oils
        "parfum", "fragrance", "essential oils", "lavender oil", "rose oil",
        "jasmine oil", "ylang ylang oil", "neroli oil", "bergamot oil",
        "lemon oil", "orange oil", "grapefruit oil", "peppermint oil",
        "eucalyptus oil", "tea tree oil", "chamomile oil", "geranium oil",
        "patchouli oil", "sandalwood oil", "cedarwood oil", "frankincense oil",
        "myrrh oil", "vanilla extract", "vanilla absolute", "vanilla oleoresin",
        
        # Plant extracts
        "aloe vera", "aloe barbadensis leaf extract", "chamomile extract",
        "calendula extract", "green tea extract", "white tea extract",
        "black tea extract", "coffee extract", "cocoa extract", "cacao extract",
        "ginkgo biloba extract", "ginseng extract", "echinacea extract",
        "elderberry extract", "elderflower extract", "rosehip extract",
        "sea buckthorn extract", "pomegranate extract", "grape extract",
        "grape seed extract", "pine bark extract", "pycnogenol",
        "centella asiatica extract", "gotu kola extract", "licorice extract",
        "licorice root extract", "turmeric extract", "curcumin", "ginger extract",
        "ginger root extract", "horsetail extract", "nettle extract",
        "dandelion extract", "burdock extract", "milk thistle extract",
        "artichoke extract", "cucumber extract", "tomato extract",
        "carrot extract", "spinach extract", "kale extract", "spirulina extract",
        "chlorella extract", "kelp extract", "seaweed extract", "marine collagen",
        "marine elastin", "pearl extract", "caviar extract", "snail secretion filtrate",
        
        # Minerals and clays
        "kaolin", "bentonite", "fuller's earth", "rhassoul clay", "french green clay",
        "pink clay", "white clay", "yellow clay", "red clay", "black clay",
        "dead sea salt", "himalayan salt", "sea salt", "epsom salt",
        "magnesium chloride", "calcium carbonate", "zinc oxide", "titanium dioxide",
        "iron oxide", "chromium oxide", "ultramarine blue", "ultramarine violet",
        
        # Enzymes and probiotics
        "papain", "bromelain", "protease", "amylase", "lipase", "lactase",
        "probiotics", "lactobacillus", "bifidobacterium", "saccharomyces",
        "fermented ingredients", "kombucha", "kefir", "yogurt extract",
        
        # Preservatives and stabilizers
        "edta", "disodium edta", "trisodium edta", "tetrasodium edta",
        "bht", "bha", "tocopherol", "ascorbic acid", "citric acid",
        "sodium citrate", "potassium citrate", "calcium citrate",
        "magnesium citrate", "zinc citrate", "copper citrate",
        
        # Thickeners and gelling agents
        "xanthan gum", "guar gum", "locust bean gum", "carrageenan",
        "agar", "pectin", "algin", "sodium alginate", "calcium alginate",
        "carbomer", "acrylates copolymer", "acrylates/c10-30 alkyl acrylate crosspolymer",
        "polyacrylamide", "polyquaternium-7", "polyquaternium-10",
        "polyquaternium-11", "polyquaternium-22", "polyquaternium-39",
        "polyquaternium-47", "polyquaternium-67", "polyquaternium-68",
        "polyquaternium-69", "polyquaternium-70", "polyquaternium-71",
        "polyquaternium-72", "polyquaternium-73", "polyquaternium-74",
        "polyquaternium-75", "polyquaternium-76", "polyquaternium-77",
        "polyquaternium-78", "polyquaternium-79", "polyquaternium-80",
        "polyquaternium-81", "polyquaternium-82", "polyquaternium-83",
        "polyquaternium-84", "polyquaternium-85", "polyquaternium-86",
        "polyquaternium-87", "polyquaternium-88", "polyquaternium-89",
        "polyquaternium-90", "polyquaternium-91", "polyquaternium-92",
        "polyquaternium-93", "polyquaternium-94", "polyquaternium-95",
        "polyquaternium-96", "polyquaternium-97", "polyquaternium-98",
        "polyquaternium-99", "polyquaternium-100"
    ]
    
    logger.info(f"Starting comprehensive database population with {len(comprehensive_ingredients)} ingredients")
    
    # Process ingredients in batches
    db = SessionLocal()
    try:
        existing_ingredients = {ing.name.lower() for ing in db.query(Ingredient).all()}
        logger.info(f"Found {len(existing_ingredients)} existing ingredients in database")
        
        processed = 0
        added = 0
        updated = 0
        
        for i in range(0, len(comprehensive_ingredients), 100):  # Process in batches of 100
            batch = comprehensive_ingredients[i:i + 100]
            logger.info(f"Processing batch {i//100 + 1}/{(len(comprehensive_ingredients) + 100 - 1)//100}")
            
            # Process batch concurrently
            tasks = []
            for ingredient_name in batch:
                if ingredient_name.lower() not in existing_ingredients:
                    task = process_ingredient_comprehensive(ingredient_name, db)
                    tasks.append(task)
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Error processing ingredient: {result}")
                    else:
                        if result:
                            added += 1
                        processed += 1
            
            # Commit batch
            db.commit()
            logger.info(f"Batch committed. Added: {added}, Processed: {processed}")
            
            # Rate limiting between batches
            await asyncio.sleep(2)
        
        logger.info(f"Comprehensive database population complete! Added: {added}, Processed: {processed}")
        
    except Exception as e:
        logger.error(f"Error populating database: {e}")
        db.rollback()
    finally:
        db.close()

async def process_ingredient_comprehensive(ingredient_name: str, db) -> bool:
    """Process a single ingredient with comprehensive data"""
    try:
        # Use EWG scraper to get data
        async with EWGScraper() as scraper:
            result = await scraper.get_ingredient_data(ingredient_name)
            
            if result["success"]:
                data = result["data"]
                
                # Check if ingredient already exists
                existing = db.query(Ingredient).filter(
                    Ingredient.name.ilike(ingredient_name)
                ).first()
                
                if existing:
                    # Update existing ingredient
                    existing.eco_score = data.get("eco_score", existing.eco_score)
                    existing.risk_level = data.get("risk_level", existing.risk_level)
                    existing.benefits = data.get("benefits", existing.benefits)
                    existing.risks_detailed = data.get("risks_detailed", existing.risks_detailed)
                    existing.sources = data.get("sources", existing.sources)
                    logger.info(f"Updated ingredient: {ingredient_name}")
                    return True
                else:
                    # Add new ingredient with comprehensive data
                    ingredient = Ingredient(
                        name=ingredient_name,
                        eco_score=data.get("eco_score", 50.0),
                        risk_level=data.get("risk_level", "desconocido"),
                        benefits=data.get("benefits", ""),
                        risks_detailed=data.get("risks_detailed", ""),
                        sources=data.get("sources", "EWG Skin Deep + Comprehensive Database")
                    )
                    db.add(ingredient)
                    logger.info(f"Added ingredient: {ingredient_name}")
                    return True
            else:
                # Add ingredient with default data if EWG fails
                existing = db.query(Ingredient).filter(
                    Ingredient.name.ilike(ingredient_name)
                ).first()
                
                if not existing:
                    ingredient = Ingredient(
                        name=ingredient_name,
                        eco_score=50.0,
                        risk_level="desconocido",
                        benefits="",
                        risks_detailed="No specific data available",
                        sources="Comprehensive Database"
                    )
                    db.add(ingredient)
                    logger.info(f"Added ingredient with default data: {ingredient_name}")
                    return True
                return False
                
    except Exception as e:
        logger.error(f"Error processing ingredient {ingredient_name}: {e}")
        return False

def _load_ingredient_candidates(ingredient_names: Optional[Iterable[str]] = None, limit: Optional[int] = None) -> List[str]:
    """Return a normalized list of ingredient names to sync."""
    global _LEXICON_CACHE

    if ingredient_names is None:
        if _LEXICON_CACHE is None:
            if not LEXICON_PATH.exists():
                logger.warning("Ingredient lexicon not found at %s", LEXICON_PATH)
                _LEXICON_CACHE = []
            else:
                entries: List[str] = []
                with LEXICON_PATH.open("r", encoding="utf-8") as lexicon_file:
                    for line in lexicon_file:
                        candidate = line.strip()
                        if not candidate or candidate.startswith("#"):
                            continue
                        entries.append(candidate)
                _LEXICON_CACHE = list(dict.fromkeys(entries))
        names = list(_LEXICON_CACHE)
    else:
        names = [str(name).strip() for name in ingredient_names if name and str(name).strip()]
        names = list(dict.fromkeys(names))

    if limit and limit > 0:
        names = names[:limit]

    return names


async def sync_external_databases(
    db: Session,
    ingredient_names: Optional[Iterable[str]] = None,
    limit: Optional[int] = None,
    concurrency: int = DEFAULT_SYNC_CONCURRENCY,
    update_local_cache: bool = True
) -> Dict[str, int]:
    """Fetch ingredient data from external APIs and persist it in the local database."""

    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    names = _load_ingredient_candidates(ingredient_names, limit)
    if not names:
        logger.info("No ingredient names provided for synchronization")
        return {"processed": 0, "updated": 0, "errors": 0}

    logger.info("Starting external sync for %d ingredients", len(names))
    summary = {"processed": len(names), "updated": 0, "errors": 0}
    semaphore = asyncio.Semaphore(max(1, concurrency))

    async with httpx.AsyncClient(timeout=DEFAULT_SYNC_TIMEOUT) as client:
        async def fetch_single(ingredient: str) -> Tuple[str, Optional[Dict[str, Any]]]:
            normalized = ingredient.strip()
            if not normalized:
                return ingredient, None
            try:
                async with semaphore:
                    data = await fetch_ingredient_data(normalized, client)
                return normalized, data
            except Exception as exc:
                logger.error("Failed to fetch %s: %s", normalized, exc)
                return normalized, None

        tasks = [fetch_single(name) for name in names]

        for future in asyncio.as_completed(tasks):
            ingredient_name, data = await future
            if not ingredient_name:
                continue
            try:
                if data:
                    updated = _upsert_ingredient_record(db, ingredient_name, data, update_local_cache)
                    if updated:
                        summary["updated"] += 1
                else:
                    summary["errors"] += 1
            except Exception as exc:
                logger.error("Failed to upsert %s: %s", ingredient_name, exc)
                summary["errors"] += 1

    if update_local_cache and 'LOCAL_INGREDIENT_DATABASE' in globals():
        try:
            refresh_local_cache_from_db(db)
        except Exception as exc:
            logger.warning("Unable to refresh in-memory cache after sync: %s", exc)

    logger.info(
        "External sync completed. Processed=%d, Updated=%d, Errors=%d",
        summary["processed"],
        summary["updated"],
        summary["errors"]
    )
    return summary


def _upsert_ingredient_record(
    db: Session,
    ingredient_name: str,
    data: Dict[str, Any],
    update_local_cache: bool = True
) -> bool:
    """Insert or update an ingredient entry in the database and local cache."""

    normalized_key = normalize_ingredient_name(ingredient_name)
    if not normalized_key:
        return False

    eco_score = float(data.get("eco_score", 50.0) or 50.0)
    risk_level = data.get("risk_level") or "desconocido"
    def _stringify(value: Any, default: str) -> str:
        if value is None or value == "":
            return default
        if isinstance(value, (list, dict, tuple, set)):
            try:
                return json.dumps(value, ensure_ascii=False)
            except Exception:
                return str(value)
        return str(value)

    benefits = _stringify(data.get("benefits"), "No disponible")
    risks_detailed = _stringify(data.get("risks_detailed"), "No disponible")
    sources = _stringify(data.get("sources"), "External")

    record = db.query(Ingredient).filter(Ingredient.name == ingredient_name).first()
    if not record:
        record = db.query(Ingredient).filter(Ingredient.name.ilike(ingredient_name)).first()
    if not record:
        record = Ingredient(
            name=ingredient_name,
            eco_score=eco_score,
            risk_level=risk_level,
            benefits=benefits,
            risks_detailed=risks_detailed,
            sources=sources
        )
        db.add(record)
    else:
        record.eco_score = eco_score
        record.risk_level = risk_level
        record.benefits = benefits
        record.risks_detailed = risks_detailed
        record.sources = sources

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("Database commit failed for %s: %s", ingredient_name, exc)
        raise

    if update_local_cache and 'LOCAL_INGREDIENT_DATABASE' in globals():
        LOCAL_INGREDIENT_DATABASE[normalized_key] = {
            "name": ingredient_name,
            "eco_score": eco_score,
            "risk_level": risk_level,
            "benefits": benefits,
            "risks_detailed": risks_detailed,
            "sources": sources
        }

    return True


def refresh_local_cache_from_db(db: Session) -> int:
    """Populate the in-memory ingredient cache from the SQL database."""

    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    if 'LOCAL_INGREDIENT_DATABASE' not in globals():
        return 0

    refreshed = 0
    for record in db.query(Ingredient).all():
        normalized = normalize_ingredient_name(record.name)
        if not normalized:
            continue
        LOCAL_INGREDIENT_DATABASE[normalized] = {
            "name": record.name,
            "eco_score": float(record.eco_score or 50.0),
            "risk_level": record.risk_level or "desconocido",
            "benefits": record.benefits or "No disponible",
            "risks_detailed": record.risks_detailed or "No disponible",
            "sources": record.sources or "External"
        }
        refreshed += 1
    return refreshed


def sync_external_databases_command(
    ingredient_names: Optional[Iterable[str]] = None,
    limit: Optional[int] = None,
    concurrency: int = DEFAULT_SYNC_CONCURRENCY,
    update_local_cache: bool = True
) -> Dict[str, int]:
    """Convenience wrapper to run the async sync routine from synchronous contexts."""

    if SessionLocal is None:
        raise RuntimeError("Database session factory not configured")

    session = SessionLocal()
    try:
        return asyncio.run(
            sync_external_databases(
                session,
                ingredient_names=ingredient_names,
                limit=limit,
                concurrency=concurrency,
                update_local_cache=update_local_cache
            )
        )
    finally:
        session.close()


# Crear tablas
Base.metadata.create_all(bind=engine)


def ensure_recommendation_feedback_schema() -> None:
    """Ensure new recommendation feedback columns/tables exist for legacy DBs."""
    if engine is None:
        return

    try:
        inspector = inspect(engine)
        recommendation_columns = {
            column["name"] for column in inspector.get_columns("recommendations")
        }
    except Exception as exc:  # pragma: no cover - inspection failure
        logger.debug("Recommendation table inspection failed: %s", exc)
        recommendation_columns = set()

    alterations: List[str] = []
    if "rating_count" not in recommendation_columns:
        alterations.append("ADD COLUMN rating_count INTEGER DEFAULT 0")
    if "rating_average" not in recommendation_columns:
        alterations.append("ADD COLUMN rating_average FLOAT DEFAULT 0.0")

    if alterations:
        ddl = f"ALTER TABLE recommendations {', '.join(alterations)}"
        try:
            with engine.begin() as connection:
                connection.execute(text(ddl))
            logger.info("Applied recommendation rating schema updates")
        except Exception as exc:  # pragma: no cover - DDL failure path
            logger.warning("Unable to update recommendations schema: %s", exc)

    try:
        RecommendationFeedback.__table__.create(bind=engine, checkfirst=True)
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to ensure recommendation_feedback table: %s", exc)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sync external cosmetic ingredient data into the local database")
    parser.add_argument("ingredients", nargs="*", help="Specific ingredient names to sync")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of ingredients to sync")
    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_SYNC_CONCURRENCY,
        help="Number of concurrent API requests"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Do not update the in-memory ingredient cache after syncing"
    )

    args = parser.parse_args()
    summary = sync_external_databases_command(
        ingredient_names=args.ingredients or None,
        limit=args.limit,
        concurrency=args.concurrency,
        update_local_cache=not args.no_cache
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
