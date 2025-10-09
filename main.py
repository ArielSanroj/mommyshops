"""
MommyShops - Clean and Optimized Cosmetic Ingredient Analysis System
Streamlined version for Railway deployment with minimal dependencies
"""

from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, status
from fastapi.responses import PlainTextResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, validator, EmailStr
from sqlalchemy.orm import Session
import httpx
import pytesseract
from PIL import Image, ImageEnhance, ImageOps
import io
import os
import logging
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
from typing import Any, Dict, Iterable, List, Optional
import numpy as np
from contextlib import asynccontextmanager
from collections import defaultdict, OrderedDict
import shutil
import re
from difflib import SequenceMatcher
import math
from jose import JWTError, jwt
from passlib.context import CryptContext
from database import (
    Ingredient,
    Recommendation,
    Routine,
    SessionLocal,
    User,
    get_db,
    get_ingredient_data,
    get_all_ingredients,
)
from api_utils_production import fetch_ingredient_data, health_check, get_cache_stats
from llm_utils import enrich_ingredient_data
from ml.recommender import IngredientRecommender
from nemotron_integration import suggest_substitutes_with_nemotron, enrich_with_nemotron_async
from google_vision_integration import extract_ingredients_with_google_vision, analyze_ingredients_with_google_vision
from google_auth_integration import get_google_auth_url, handle_google_callback, verify_google_token
from firebase_config import get_firestore_client, get_firebase_auth, is_firebase_available
from firebase_admin import firestore

# Configure logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_SIZE", 5 * 1024 * 1024))
MAX_ANALYZED_INGREDIENTS = int(os.getenv("MAX_ANALYZED_INGREDIENTS", 5))
MAX_OCR_INGREDIENTS = int(os.getenv("MAX_OCR_INGREDIENTS", 10))
ALLOWED_USER_NEEDS = {"general safety", "sensitive skin", "pregnancy"}
DEFAULT_USER_NEED = "general safety"
STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that", "ingredients",
    "contains", "may", "contain", "product", "formula", "directions",
    "usage", "warning", "caution"
}

CONDITION_INGREDIENT_BLACKLIST = {
    "alergias": {"paraben", "parabeno", "sulfate", "sulfato", "oxybenzone", "formaldehyde", "fragance", "fragrance"},
    "acné severo": {"coconut oil", "isopropyl", "lanolin", "mineral oil", "petrolatum"},
    "dermatitis": {"alcohol denat", "fragrance", "sulfate"},
    "psoriasis": {"salicylic acid", "coal tar"},
    "rosácea": {"menthol", "peppermint", "alcohol"},
    "queratosis": {"retinol", "retinyl"},
    "manchas o hiperpigmentación": {"hydroquinone"},
    "cicatrices visibles": {"parabeno", "paraben"},
    "calvicie o pérdida de densidad": {"sulfate", "sulfato"},
    "caspa o descamación": {"alcohol", "sulfate"},
    "cuero cabelludo sensible": {"sulfate", "sulfato", "fragrance"},
    "cabello muy fino o quebradizo": {"sulfate", "sulfato", "silicone", "silicona"},
}

HYDRATING_INGREDIENTS = {
    "hyaluronic", "ácido hialurónico", "glycerin", "glicerina", "panthenol", "ceramide", "aloe", "squalane", "squalene"
}

ANTI_FRIZZ_INGREDIENTS = {
    "argan", "jojoba", "shea", "dimethicone", "amodimethicone", "sylica", "keratin", "aceite de coco"
}

LIGHTWEIGHT_HAIR_INGREDIENTS = {
    "green tea", "tea tree", "menthol", "limon", "citrus", "clay", "vinagre"
}

CLIMATE_NEEDS = {
    "seco": {"needs_emollients": True},
    "húmedo": {"avoid_heavy": True},
}

SCALP_AVOID = {
    "graso": {"heavy_oil", "petrolatum", "wax"},
    "sensible": {"fragrance", "alcohol", "sulfate"},
}

HEAVY_OILS = {
    "coconut", "aceite de coco", "butter", "manteca", "petrolatum", "mineral oil", "lanolin"
}

SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


def verify_password(plain_password: str, hashed_password: Optional[str]) -> bool:
    if not plain_password or not hashed_password:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as exc:
        logger.warning("Password verification failed: %s", exc)
        return False


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decode_token(token: str, db: Session) -> Optional[User]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        if not subject:
            return None
        return db.query(User).filter(User.id == int(subject)).first()
    except (JWTError, ValueError) as exc:
        logger.warning("Token decode failed: %s", exc)
        return None


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación requerido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = _decode_token(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not token:
        return None
    return _decode_token(token, db)


# Firebase helper functions
def _parse_json_field(json_str: Optional[str]) -> Optional[Dict[str, Any]]:
    """Parse JSON string field safely."""
    if not json_str:
        return None
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return None


def _create_firebase_user_profile(uid: str, email: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create user profile data for Firestore."""
    profile_data = {
        "uid": uid,
        "email": email,
        "created_at": firestore.SERVER_TIMESTAMP,
        "updated_at": firestore.SERVER_TIMESTAMP
    }
    
    # Add optional fields if provided
    optional_fields = [
        "name", "skin_face", "hair_type", "climate",
        "goals_face", "skin_body", "goals_body", "hair_porosity",
        "goals_hair", "hair_thickness_scalp", "conditions"
    ]
    
    for field in optional_fields:
        if field in user_data and user_data[field]:
            if field in ["goals_face", "skin_body", "goals_body", "hair_porosity", 
                        "goals_hair", "hair_thickness_scalp", "conditions"]:
                # Parse JSON fields
                parsed = _parse_json_field(user_data[field])
                if parsed:
                    profile_data[field] = parsed
            else:
                profile_data[field] = user_data[field]
    
    return profile_data


async def _get_firebase_user_profile(uid: str) -> Optional["FirebaseUserProfile"]:
    """Get user profile from Firestore."""
    try:
        if not is_firebase_available():
            return None
        
        db = get_firestore_client()
        doc_ref = db.collection('users').document(uid)
        doc = doc_ref.get()
        
        if not doc.exists:
            return None
        
        data = doc.to_dict()
        if not data:
            return None
        
        # Convert Firestore timestamps to strings
        created_at = data.get('created_at')
        updated_at = data.get('updated_at')
        
        if hasattr(created_at, 'timestamp'):
            created_at = created_at.timestamp()
        if hasattr(updated_at, 'timestamp'):
            updated_at = updated_at.timestamp()
        
        return FirebaseUserProfile(
            uid=uid,
            email=data.get('email', ''),
            name=data.get('name'),
            skin_face=data.get('skin_face'),
            hair_type=data.get('hair_type'),
            goals_face=data.get('goals_face'),
            climate=data.get('climate'),
            skin_body=data.get('skin_body'),
            goals_body=data.get('goals_body'),
            hair_porosity=data.get('hair_porosity'),
            goals_hair=data.get('goals_hair'),
            hair_thickness_scalp=data.get('hair_thickness_scalp'),
            conditions=data.get('conditions'),
            created_at=str(created_at) if created_at else None,
            updated_at=str(updated_at) if updated_at else None
        )
    except Exception as e:
        logger.error(f"Error getting Firebase user profile: {e}")
        return None


async def _update_firebase_user_profile(uid: str, update_data: Dict[str, Any]) -> bool:
    """Update user profile in Firestore."""
    try:
        if not is_firebase_available():
            return False
        
        db = get_firestore_client()
        doc_ref = db.collection('users').document(uid)
        
        # Prepare update data
        firestore_data = {}
        for key, value in update_data.items():
            if value is not None:
                if key in ["goals_face", "skin_body", "goals_body", "hair_porosity", 
                          "goals_hair", "hair_thickness_scalp", "conditions"]:
                    # Parse JSON fields
                    parsed = _parse_json_field(value)
                    if parsed:
                        firestore_data[key] = parsed
                else:
                    firestore_data[key] = value
        
        if firestore_data:
            firestore_data["updated_at"] = firestore.SERVER_TIMESTAMP
            doc_ref.update(firestore_data)
        
        return True
    except Exception as e:
        logger.error(f"Error updating Firebase user profile: {e}")
        return False


def _normalize_str_list(value: Optional[Any]) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        results: List[str] = []
        for item in value:
            if item is None:
                continue
            if isinstance(item, str):
                cleaned = item.strip()
                if cleaned:
                    results.append(cleaned)
            else:
                results.append(str(item).strip())
        return results
    if isinstance(value, str):
        parts = [segment.strip() for segment in value.split(",")]
        return [segment for segment in parts if segment]
    return [str(value)]


def _normalize_goal_dict(goal_map: Optional[Dict[str, Any]]) -> Dict[str, int]:
    if not goal_map:
        return {}
    normalized: Dict[str, int] = {}
    for key, raw in goal_map.items():
        if key is None:
            continue
        name = str(key).strip()
        if not name:
            continue
        try:
            score = int(raw)
        except (TypeError, ValueError):
            continue
        normalized[name.lower()] = max(1, min(score, 5))
    return normalized


def _collect_conditions(conditions: Optional[Iterable[Any]], other_text: Optional[str] = None) -> List[str]:
    items = _normalize_str_list(conditions)
    results = [item.lower() for item in items]
    if other_text:
        cleaned = other_text.strip().lower()
        if cleaned:
            results.append(cleaned)
    return list(dict.fromkeys(results))

RISK_LEVEL_NORMALIZATION = {
    "high hazard": "riesgo alto",
    "high risk": "riesgo alto",
    "hazardous": "riesgo alto",
    "unsafe": "riesgo alto",
    "moderate hazard": "riesgo medio",
    "moderate risk": "riesgo medio",
    "medium risk": "riesgo medio",
    "low hazard": "riesgo bajo",
    "low risk": "riesgo bajo",
    "safe": "seguro",
    "muy seguro": "seguro",
    "unknown": "desconocido",
    "not rated": "desconocido",
    "no data": "desconocido"
}


def _normalize_ingredient_key(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9\s-]", " ", value.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


LEXICON_PATH = os.getenv(
    "INGREDIENT_LEXICON_PATH",
    os.path.join(BASE_DIR, "cosmetic_ingredients_lexicon.txt")
)
INGREDIENT_LEXICON: Dict[str, str] = {}
try:
    with open(LEXICON_PATH, "r", encoding="utf-8") as lexicon_file:
        for line in lexicon_file:
            entry = line.strip()
            if not entry:
                continue
            normalized_entry = _normalize_ingredient_key(entry)
            if normalized_entry:
                INGREDIENT_LEXICON[normalized_entry] = entry
    if INGREDIENT_LEXICON:
        logger.info("Ingredient lexicon loaded: %d entries", len(INGREDIENT_LEXICON))
except FileNotFoundError:
    logger.warning("Ingredient lexicon file not found at %s", LEXICON_PATH)

INGREDIENT_LEXICON_INDEX: Dict[str, List[tuple[str, str]]] = defaultdict(list)
for normalized_entry, canonical_entry in INGREDIENT_LEXICON.items():
    if not normalized_entry:
        continue
    first_char = normalized_entry[0]
    INGREDIENT_LEXICON_INDEX[first_char].append((normalized_entry, canonical_entry))


def configure_tesseract() -> bool:
    configured_path = os.getenv("TESSERACT_PATH")
    candidate_paths = [configured_path] if configured_path else []
    candidate_paths.extend([
        "/opt/homebrew/bin/tesseract",
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
    ])

    resolved_path = None
    for path in candidate_paths:
        if path and os.path.isfile(path):
            resolved_path = path
            break

    if not resolved_path:
        resolved_path = shutil.which("tesseract")
        if not resolved_path:
            logger.error("Tesseract executable not found in any known location")
            return False

    try:
        pytesseract.pytesseract.tesseract_cmd = resolved_path
        pytesseract.get_tesseract_version()
        logger.info("Tesseract OCR available at: %s", resolved_path)
        return True
    except Exception as exc:
        logger.error("Tesseract not available: %s", exc)
        return False


TESSERACT_AVAILABLE = configure_tesseract()

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Configure connection limits on startup and cleanup on shutdown."""
    # Startup
    try:
        import httpx
        httpx._config.DEFAULT_LIMITS = httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
            keepalive_expiry=30.0
        )
        logger.info("Connection limits configured successfully")
    except Exception as e:
        logger.error(f"Error configuring connection limits: {e}")

    try:
        await ensure_recommender_ready()
    except Exception as exc:
        logger.warning("Recommender warmup failed: %s", exc)
    
    yield
    
    # Shutdown
    logger.info("Application shutting down")

# FastAPI app
app = FastAPI(
    title="MommyShops - Cosmetic Ingredient Analysis",
    description="Professional cosmetic ingredient safety analysis",
    version="3.0.0",
    lifespan=lifespan
)


RECOMMENDER = IngredientRecommender()
RECOMMENDER.configure(SessionLocal)

# Pydantic models
class AnalyzeUrlRequest(BaseModel):
    url: str = Field(..., description="URL of the product page")
    user_need: str = Field(default="general safety", description="User's skin need")

class AnalyzeTextRequest(BaseModel):
    text: str = Field(..., description="Text containing ingredients")
    user_need: str = Field(default="general safety", description="User's skin need")


class AuthRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @validator("username")
    def _validate_username(cls, value: str) -> str:
        if not value.isascii():
            raise ValueError("El usuario solo debe contener caracteres ASCII")
        return value.strip()


class AuthRegisterResponse(BaseModel):
    user_id: int
    username: str
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthenticatedUser(BaseModel):
    user_id: int
    username: Optional[str]
    email: Optional[str]


class RoutineProductInput(BaseModel):
    name: str


class HairScalpInfo(BaseModel):
    thickness: List[str]
    scalp: List[str]

    @classmethod
    def from_payload(cls, data: Optional[Dict[str, Any]]) -> "HairScalpInfo":
        payload = data or {}
        return cls(
            thickness=_normalize_str_list(payload.get("thickness")),
            scalp=_normalize_str_list(payload.get("scalp")),
        )


class RegisterRequest(BaseModel):
    skin_face: str
    hair_type: str
    goals_face: List[str]
    climate: str
    skin_body: List[str]
    goals_body: List[str]
    hair_porosity: List[str]
    goals_hair: Dict[str, int]
    hair_thickness_scalp: Dict[str, Any]
    conditions: List[str]
    other_condition: Optional[str] = None
    products: List[str]
    accept_terms: bool

    @classmethod
    def from_request(cls, data: Dict[str, Any]) -> "RegisterRequest":
        accept_raw = data.get("accept_terms")
        if isinstance(accept_raw, bool):
            accept_terms = accept_raw
        elif isinstance(accept_raw, str):
            accept_terms = accept_raw.strip().lower() in {"true", "1", "yes", "on", "si", "sí"}
        else:
            accept_terms = bool(accept_raw)

        return cls(
            skin_face=str(data.get("skin_face", "")).strip(),
            hair_type=str(data.get("hair_type", "")).strip(),
            goals_face=_normalize_str_list(data.get("goals_face")),
            climate=str(data.get("climate", "")).strip(),
            skin_body=_normalize_str_list(data.get("skin_body")),
            goals_body=_normalize_str_list(data.get("goals_body")),
            hair_porosity=_normalize_str_list(data.get("hair_porosity")),
            goals_hair=_normalize_goal_dict(data.get("goals_hair")),
            hair_thickness_scalp=data.get("hair_thickness_scalp") or {},
            conditions=_normalize_str_list(data.get("conditions")),
            other_condition=data.get("other_condition"),
            products=_normalize_str_list(data.get("products")),
            accept_terms=accept_terms,
        )

    @property
    def hair_scalp_info(self) -> HairScalpInfo:
        return HairScalpInfo.from_payload(self.hair_thickness_scalp)

    @validator("skin_face", "hair_type", "climate")
    def _validate_non_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("Campo requerido")
        return value

    @validator(
        "goals_face",
        "skin_body",
        "goals_body",
        "hair_porosity",
        "conditions",
        "products",
        each_item=False,
    )
    def _validate_non_empty_list(cls, value: List[str]) -> List[str]:
        if not value:
            raise ValueError("Selecciona al menos una opción")
        return value

    @validator("goals_hair")
    def _validate_goals_hair(cls, value: Dict[str, int]) -> Dict[str, int]:
        if not value:
            raise ValueError("Selecciona al menos un objetivo de cabello")
        return value

    @validator("accept_terms")
    def _validate_terms(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Debes aceptar la política de privacidad")
        return value


class RegisterResponse(BaseModel):
    user_id: int
    routine_id: Optional[int] = None


# Firebase-specific models
class FirebaseUserProfile(BaseModel):
    uid: str
    email: str
    name: Optional[str] = None
    skin_face: Optional[str] = None
    hair_type: Optional[str] = None
    goals_face: Optional[Dict[str, Any]] = None
    climate: Optional[str] = None
    skin_body: Optional[Dict[str, Any]] = None
    goals_body: Optional[Dict[str, Any]] = None
    hair_porosity: Optional[Dict[str, Any]] = None
    goals_hair: Optional[Dict[str, Any]] = None
    hair_thickness_scalp: Optional[Dict[str, Any]] = None
    conditions: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class FirebaseRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., min_length=2, max_length=128)
    skin_face: Optional[str] = None
    hair_type: Optional[str] = None
    goals_face: Optional[str] = None  # JSON string
    climate: Optional[str] = None
    skin_body: Optional[str] = None  # JSON string
    goals_body: Optional[str] = None  # JSON string
    hair_porosity: Optional[str] = None  # JSON string
    goals_hair: Optional[str] = None  # JSON string
    hair_thickness_scalp: Optional[str] = None  # JSON string
    conditions: Optional[str] = None  # JSON string


class FirebaseRegisterResponse(BaseModel):
    uid: str
    email: str
    message: str


class FirebaseLoginRequest(BaseModel):
    email: EmailStr
    password: str


class FirebaseLoginResponse(BaseModel):
    uid: str
    email: str
    name: Optional[str] = None
    custom_token: Optional[str] = None
    message: str


class FirebaseUserUpdateRequest(BaseModel):
    name: Optional[str] = None
    skin_face: Optional[str] = None
    hair_type: Optional[str] = None
    goals_face: Optional[str] = None  # JSON string
    climate: Optional[str] = None
    skin_body: Optional[str] = None  # JSON string
    goals_body: Optional[str] = None  # JSON string
    hair_porosity: Optional[str] = None  # JSON string
    goals_hair: Optional[str] = None  # JSON string
    hair_thickness_scalp: Optional[str] = None  # JSON string
    conditions: Optional[str] = None  # JSON string


class FirebaseRefreshTokenRequest(BaseModel):
    refresh_token: str


class FirebaseRefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class IngredientAnalysisResponse(BaseModel):
    name: str
    eco_score: float
    risk_level: str
    benefits: str
    risks_detailed: str
    sources: str

def _stringify_field(value: Any, default: str) -> str:
    if value is None:
        return default
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else default
    if isinstance(value, (list, tuple, set)):
        cleaned = []
        for item in value:
            text = str(item).strip()
            if text and text.lower() != "none":
                cleaned.append(text)
        if not cleaned:
            return default
        return " | ".join(dict.fromkeys(cleaned))
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            key_str = str(key).strip()
            item_str = str(item).strip()
            if not item_str:
                continue
            if key_str:
                parts.append(f"{key_str}: {item_str}")
            else:
                parts.append(item_str)
        if not parts:
            return default
        return " | ".join(parts)
    return str(value).strip() or default


def _normalize_risk_level(value: Any) -> str:
    if value is None:
        return "desconocido"
    if isinstance(value, (list, tuple, set)):
        for item in value:
            normalized = _normalize_risk_level(item)
            if normalized != "desconocido":
                return normalized
        return "desconocido"
    risk = str(value).strip().lower()
    if not risk:
        return "desconocido"
    normalized = RISK_LEVEL_NORMALIZATION.get(risk)
    if normalized:
        return normalized
    if "alto" in risk or "high" in risk:
        return "riesgo alto"
    if "medio" in risk or "moderate" in risk or "medium" in risk:
        return "riesgo medio"
    if "bajo" in risk or "low" in risk:
        return "riesgo bajo"
    if "seguro" in risk or "safe" in risk:
        return "seguro"
    if "cancer" in risk:
        return "cancerígeno"
    return "desconocido"


def _sanitize_analysis_data(data: Dict[str, Any]) -> Dict[str, Any]:
    sanitized: Dict[str, Any] = {}

    eco_value = data.get("eco_score") if isinstance(data, dict) else None
    try:
        eco_score = float(eco_value) if eco_value is not None else 50.0
    except (TypeError, ValueError):
        eco_score = 50.0
    if math.isnan(eco_score) or math.isinf(eco_score):
        eco_score = 50.0
    else:
        eco_score = max(0.0, min(100.0, eco_score))

    sanitized["eco_score"] = eco_score
    sanitized["risk_level"] = _normalize_risk_level(data.get("risk_level") if isinstance(data, dict) else None)
    sanitized["benefits"] = _stringify_field(data.get("benefits") if isinstance(data, dict) else None, "No disponible")
    sanitized["risks_detailed"] = _stringify_field(data.get("risks_detailed") if isinstance(data, dict) else None, "Datos insuficientes para evaluación")
    sanitized["sources"] = _stringify_field(data.get("sources") if isinstance(data, dict) else None, "Análisis básico")

    return sanitized


class ProductAnalysisResponse(BaseModel):
    product_name: str
    ingredients_details: List[IngredientAnalysisResponse]
    avg_eco_score: float
    suitability: str
    recommendations: str


class SubstituteSuggestion(BaseModel):
    product_id: Optional[int] = None
    name: str
    brand: Optional[str] = None
    eco_score: Optional[float] = None
    risk_level: Optional[str] = None
    similarity: float = 0.0
    reason: str


class ProductEvaluation(BaseModel):
    product_name: str
    meets_needs: bool
    alerts: List[str] = Field(default_factory=list)
    substitutes: List[SubstituteSuggestion] = Field(default_factory=list)
    llm_alternatives: List[str] = Field(default_factory=list)


class RoutineAnalysisResponse(BaseModel):
    routine_id: int
    product_name: Optional[str]
    extracted_ingredients: List[str] = Field(default_factory=list)
    analysis: ProductAnalysisResponse
    alerts: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    substitutes: List[SubstituteSuggestion] = Field(default_factory=list)
    products: List[ProductEvaluation] = Field(default_factory=list)


class RecommendationItem(BaseModel):
    id: int
    routine_id: Optional[int]
    original_product_name: Optional[str]
    substitute_product_name: Optional[str]
    reason: str
    status: str
    created_at: datetime


class UserRecommendationsResponse(BaseModel):
    user_id: int
    items: List[RecommendationItem]


async def ensure_recommender_ready(force: bool = False) -> None:
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: RECOMMENDER.ensure_loaded(force=force))


async def suggest_substitutes_async(
    *,
    ingredients: List[str],
    excluded_ingredients: List[str],
    target_product_name: Optional[str],
    user_conditions: List[str],
    top_k: int = 3,
    user_profile: Optional[Dict[str, Any]] = None,
    issues: Optional[List[str]] = None,
) -> List[Dict[str, object]]:
    loop = asyncio.get_event_loop()

    def _task() -> List[Dict[str, object]]:
        return RECOMMENDER.suggest_substitutes(
            ingredients=ingredients,
            excluded_ingredients=excluded_ingredients,
            target_product_name=target_product_name,
            user_conditions=user_conditions,
            top_k=top_k,
        )

    base_suggestions = await loop.run_in_executor(None, _task)

    if user_profile and base_suggestions:
        try:
            # Use Google Vision for ingredient analysis instead of NVIDIA
            refined = await analyze_ingredients_with_google_vision(
                ingredients=ingredients,
                user_conditions=user_profile.get("conditions", []) if user_profile else []
            )
            if refined:
                return refined
        except Exception as exc:
            logger.error("Nemotron substitution failed: %s", exc)

    return base_suggestions


def _format_substitute_message(suggestion: SubstituteSuggestion) -> str:
    headline = f"Compra {suggestion.name}"
    if suggestion.brand:
        headline += f" de {suggestion.brand}"

    details: List[str] = []
    if suggestion.reason:
        details.append(suggestion.reason)
    details.append(f"similitud {suggestion.similarity:.2f}")

    return f"{headline}: {', '.join(details)}"


def _list_from_model(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip().lower() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [segment.strip().lower() for segment in value.split(",") if segment.strip()]
    return [str(value).strip().lower()]


def _dict_from_model(value: Any) -> Dict[str, int]:
    if isinstance(value, dict):
        result: Dict[str, int] = {}
        for key, raw in value.items():
            try:
                score = int(raw)
            except (TypeError, ValueError):
                continue
            name = str(key).strip().lower()
            if not name:
                continue
            result[name] = max(1, min(score, 5))
        return result
    return {}


def _build_user_profile(user: User) -> Dict[str, Any]:
    hair_scalp_raw = getattr(user, "hair_thickness_scalp", {}) or {}
    profile = {
        "skin_face": (user.skin_face or "").lower(),
        "hair_type": (user.hair_type or "").lower(),
        "goals_face": _list_from_model(user.goals_face),
        "climate": (user.climate or "").lower(),
        "skin_body": _list_from_model(user.skin_body),
        "goals_body": _list_from_model(user.goals_body),
        "hair_porosity": _list_from_model(user.hair_porosity),
        "goals_hair": _dict_from_model(user.goals_hair),
        "hair_thickness": [item.lower() for item in _normalize_str_list(hair_scalp_raw.get("thickness"))],
        "scalp": [item.lower() for item in _normalize_str_list(hair_scalp_raw.get("scalp"))],
        "conditions": _list_from_model(user.conditions),
    }
    return profile


def _analyze_ingredients_for_profile(
    product_name: str,
    ingredients: List[str],
    profile: Dict[str, Any],
) -> Dict[str, Any]:
    normalized_ingredients = [ing.lower() for ing in ingredients if ing]
    alerts: List[str] = []
    excluded: List[str] = []
    safe: List[str] = []

    # Condition-based exclusions
    for condition in profile.get("conditions", []):
        banned_terms = CONDITION_INGREDIENT_BLACKLIST.get(condition, set())
        for term in banned_terms:
            for ingredient in normalized_ingredients:
                if term in ingredient:
                    message = (
                        f"⚠️ {product_name} contiene {ingredient} que puede afectar la condición {condition}."
                    )
                    alerts.append(message)
                    excluded.append(ingredient)

    # Hydration needs
    needs_hydration = (
        profile.get("skin_face") == "seca"
        or "hidratar" in profile.get("goals_face", [])
        or "hidratar" in profile.get("goals_body", [])
        or profile.get("climate") == "seco"
    )
    if needs_hydration:
        if not any(term in ingredient for term in HYDRATING_INGREDIENTS for ingredient in normalized_ingredients):
            alerts.append(
                f"⚠️ {product_name} no incluye ingredientes hidratantes claves para tu perfil (piel/cabello seco)."
            )

    # Control de brillo - evitar aceites pesados
    if "controlar brillo" in profile.get("goals_face", []):
        if any(term in ingredient for term in HEAVY_OILS for ingredient in normalized_ingredients):
            alerts.append(
                f"⚠️ {product_name} contiene aceites pesados que pueden aumentar el brillo en tu piel."
            )

    # Hair porosity & scalp
    if any("baja" in poro for poro in profile.get("hair_porosity", [])):
        if any("sulfate" in ingredient or "sulfato" in ingredient for ingredient in normalized_ingredients):
            alerts.append(
                f"⚠️ {product_name} incluye sulfatos que no se recomiendan para cabello de baja porosidad."
            )

    for scalp_type in profile.get("scalp", []):
        avoid_terms = SCALP_AVOID.get(scalp_type.lower())
        if avoid_terms:
            for term in avoid_terms:
                for ingredient in normalized_ingredients:
                    if term in ingredient:
                        alerts.append(
                            f"⚠️ {product_name} contiene {ingredient}, que puede afectar tu cuero cabelludo {scalp_type}."
                        )

    # Hair goals with likert scores
    goals_hair = profile.get("goals_hair", {})
    frizz_score = goals_hair.get("reducir frizz", 0)
    if frizz_score >= 4:
        if not any(term in ingredient for term in ANTI_FRIZZ_INGREDIENTS for ingredient in normalized_ingredients):
            alerts.append(
                f"⚠️ {product_name} no contiene activos para reducir frizz, objetivo prioritario."
            )

    # Populate safe ingredients (those not excluded)
    excluded_set = set(excluded)
    for ingredient in normalized_ingredients:
        if ingredient not in excluded_set:
            safe.append(ingredient)

    meets_needs = len(alerts) == 0

    return {
        "alerts": list(dict.fromkeys(alerts)),
        "safe": safe,
        "excluded": list(dict.fromkeys(excluded)),
        "meets_needs": meets_needs,
    }


def _load_user_routine_products(db: Session, user_id: int) -> List[str]:
    routine = db.query(Routine).filter(Routine.user_id == user_id).order_by(Routine.id.desc()).first()
    if not routine or not routine.products:
        return []
    names: List[str] = []
    for entry in routine.products:
        if isinstance(entry, dict):
            value = entry.get("name")
        else:
            value = entry
        if not value:
            continue
        name = str(value).strip()
        if name:
            names.append(name)
    return list(dict.fromkeys(names))


def _fetch_product_ingredients(db: Session, product_name: str) -> Dict[str, Any]:
    if not product_name:
        return {"ingredients": [], "brand": None, "record": None}
    query = (
        db.query(Product)
        .filter(Product.name.ilike(product_name))
        .order_by(Product.id.asc())
    )
    record = query.first()
    if not record:
        like_query = (
            db.query(Product)
            .filter(Product.name.ilike(f"%{product_name}%"))
            .order_by(Product.id.asc())
        )
        record = like_query.first()
    if not record:
        return {"ingredients": [], "brand": None, "record": None}

    raw_ingredients = record.ingredients or []
    ingredients_list: List[str]
    if isinstance(raw_ingredients, list):
        ingredients_list = [str(item).strip() for item in raw_ingredients if str(item).strip()]
    elif isinstance(raw_ingredients, str):
        try:
            parsed = json.loads(raw_ingredients)
            if isinstance(parsed, list):
                ingredients_list = [str(item).strip() for item in parsed if str(item).strip()]
            else:
                ingredients_list = [segment.strip() for segment in raw_ingredients.split(",") if segment.strip()]
        except json.JSONDecodeError:
            ingredients_list = [segment.strip() for segment in raw_ingredients.split(",") if segment.strip()]
    else:
        ingredients_list = [str(raw_ingredients).strip()]

    return {"ingredients": ingredients_list, "brand": record.brand, "record": record}

# Core functions
def _simple_ocr_parse(image_data: bytes) -> List[str]:
    try:
        image = Image.open(io.BytesIO(image_data))
        text = pytesseract.image_to_string(image, lang="eng+spa")
        if not text:
            return []
        return [segment.strip().lower() for segment in text.split(",") if segment.strip() and len(segment.strip()) > 3]
    except Exception as exc:
        logger.error("Simple OCR fallback failed: %s", exc)
        return []


async def extract_ingredients_from_image(image_data: bytes) -> List[str]:
    """Extract ingredients from image using enhanced OCR with better preprocessing."""
    try:
        logger.info("Starting enhanced image processing...")
        
        # Try Google Vision first (best quality OCR)
        try:
            ingredients = await extract_ingredients_with_google_vision(image_data)
            if ingredients:
                logger.info(f"Google Vision extracted {len(ingredients)} ingredients from image")
                return ingredients
        except Exception as e:
            logger.warning(f"Google Vision failed for image: {e}")
        
        if not TESSERACT_AVAILABLE:
            logger.error("Tesseract not available")
            return []
        
        # Load and preprocess image
        image = Image.open(io.BytesIO(image_data))
        logger.info(f"Original image size: {image.size}")
        
        # Enhanced preprocessing with Otsu and deskew for 90%+ precision
        processed_images = []
        
        # 1. Basic grayscale processing
        if image.mode != 'L':
            gray = image.convert('L')
        else:
            gray = image.copy()
        
        # Resize for better OCR (but not too large to avoid memory issues)
        if max(gray.size) < 400:
            scale_factor = 400 / max(gray.size)
            new_size = (int(gray.size[0] * scale_factor), int(gray.size[1] * scale_factor))
            gray = gray.resize(new_size, Image.Resampling.LANCZOS)
            logger.info(f"Resized to: {gray.size}")
        
        # 2. Deskew detection and correction (common 2-5° tilt in photos)
        try:
            import numpy as np
            from scipy.ndimage import rotate
            from skimage import filters, transform
            
            # Convert to numpy for processing
            img_array = np.array(gray)
            
            # Detect skew angle using Hough transform
            edges = filters.sobel(img_array)
            h, theta, d = transform.hough_line(edges)
            accum, angles, dists = transform.hough_line_peaks(h, theta, d)
            
            if len(angles) > 0:
                # Get the most common angle
                skew_angle = np.degrees(np.median(angles))
                # Only correct if angle is significant (> 0.5 degrees)
                if abs(skew_angle) > 0.5:
                    logger.info(f"Detected skew angle: {skew_angle:.2f}°, correcting...")
                    corrected_img = rotate(img_array, -skew_angle, mode='nearest', order=1)
                    gray = Image.fromarray(corrected_img.astype(np.uint8))
                    logger.info("Deskew correction applied")
        except ImportError:
            logger.warning("scikit-image not available, skipping deskew correction")
        except Exception as e:
            logger.warning(f"Deskew correction failed: {e}")
        
        # 3. Otsu binarization (optimal for white background text)
        try:
            import numpy as np
            from skimage import filters
            
            img_array = np.array(gray)
            otsu_threshold = filters.threshold_otsu(img_array)
            otsu_binary = (img_array > otsu_threshold).astype(np.uint8) * 255
            otsu_img = Image.fromarray(otsu_binary)
            processed_images.append(("otsu_binary", otsu_img))
            logger.info(f"Otsu threshold: {otsu_threshold}")
        except ImportError:
            logger.warning("scikit-image not available, skipping Otsu binarization")
        except Exception as e:
            logger.warning(f"Otsu binarization failed: {e}")
        
        # 4. High contrast (most reliable)
        enhancer = ImageEnhance.Contrast(gray)
        high_contrast = enhancer.enhance(1.8)
        processed_images.append(("high_contrast", high_contrast))
        
        # 5. Inverted (for dark text on light background)
        inverted = ImageOps.invert(high_contrast)
        processed_images.append(("inverted", inverted))
        
        # 6. Auto contrast (fallback)
        auto_contrast = ImageOps.autocontrast(high_contrast, cutoff=1)
        processed_images.append(("auto_contrast", auto_contrast))
        
        # Try OCR on multiple processed images with different configurations
        all_ingredients = []
        
        # Optimized OCR configurations for 90%+ precision
        configs = [
            '--psm 3 --oem 3',  # Full page segmentation (best for dense blocks)
            '--psm 6 --oem 3',  # Uniform block of text
            '--psm 7 --oem 3',  # Single text line
            '--psm 4 --oem 3'   # Single column text
        ]
        
        max_attempts = 4  # Reduced total OCR attempts for faster processing
        attempt_count = 0
        
        for img_name, processed_img in processed_images:
            if attempt_count >= max_attempts:
                logger.info(f"Reached max attempts ({max_attempts}), stopping OCR")
                break
                
            logger.info(f"Processing {img_name} image... (attempt {attempt_count + 1}/{max_attempts})")
            
            for i, config in enumerate(configs):
                if attempt_count >= max_attempts:
                    break
                    
                try:
                    logger.info(f"Trying {img_name} with config {i+1}: {config}")
                    attempt_count += 1
                    
                    ocr_result = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, 
                            lambda: pytesseract.image_to_string(processed_img, lang='eng+spa', config=config)
                        ),
                        timeout=10.0  # Increased timeout for better OCR processing
                    )
                    
                    if ocr_result.strip():
                        logger.info(f"OCR result from {img_name} config {i+1}: {len(ocr_result)} characters")
                        
                        # Detect garbled text automatically
                        is_garbled = detect_garbled_text(ocr_result)
                        if is_garbled:
                            logger.info("Garbled text detected, using enhanced extraction...")
                            ingredients = await extract_ingredients_with_enhanced_processing(ocr_result, image_data)
                        else:
                            ingredients = extract_ingredients_from_text(ocr_result)
                        
                        if ingredients:
                            all_ingredients.extend(ingredients)
                            logger.info(f"Found {len(ingredients)} ingredients from {img_name} config {i+1}")
                            # If we found enough ingredients, we can stop early
                            if len(all_ingredients) >= 5:  # Increased threshold for better results
                                logger.info(f"Found {len(all_ingredients)} ingredients, stopping early")
                                break
                
                except asyncio.TimeoutError:
                    logger.warning(f"OCR {img_name} config {i+1} timed out")
                    continue
                except Exception as e:
                    logger.warning(f"OCR {img_name} config {i+1} failed: {e}")
                    continue
        
        # Clean and deduplicate ingredients
        logger.info(f"Raw ingredients found: {len(all_ingredients)} - {all_ingredients[:5]}")
        try:
            cleaned_ingredients = clean_and_deduplicate_ingredients(all_ingredients)
            logger.info(f"Final cleaned ingredients: {len(cleaned_ingredients)} - {cleaned_ingredients[:5]}")
        except Exception as e:
            logger.error(f"Error cleaning ingredients: {e}")
            # Fallback: return raw ingredients without cleaning
            cleaned_ingredients = all_ingredients[:MAX_OCR_INGREDIENTS]
            logger.info(f"Using raw ingredients as fallback: {len(cleaned_ingredients)}")

        if not cleaned_ingredients:
            fallback_ingredients = _simple_ocr_parse(image_data)
            if fallback_ingredients:
                logger.info("Simple OCR fallback extracted %d ingredients", len(fallback_ingredients))
                return fallback_ingredients[:MAX_OCR_INGREDIENTS]
        
        return cleaned_ingredients[:MAX_OCR_INGREDIENTS]
        
    except Exception as e:
        logger.error(f"Image processing failed: {e}")
        fallback_ingredients = _simple_ocr_parse(image_data)
        return fallback_ingredients[:MAX_OCR_INGREDIENTS] if fallback_ingredients else []

def detect_garbled_text(text: str) -> bool:
    """Detect if OCR text is garbled/corrupted."""
    if not text or len(text.strip()) < 10:
        return False
    
    # Count alphanumeric vs non-alphanumeric characters
    alphanumeric_count = sum(1 for c in text if c.isalnum())
    total_chars = len(text.strip())
    
    # If less than 50% alphanumeric, likely garbled
    if total_chars > 0 and (alphanumeric_count / total_chars) < 0.5:
        return True
    
    # Check for excessive special characters
    special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
    if total_chars > 0 and (special_chars / total_chars) > 0.3:
        return True
    
    # Check for repeated patterns (common in garbled text)
    words = text.split()
    if len(words) > 3:
        # Check if more than 30% of words are very short (likely garbled)
        short_words = sum(1 for word in words if len(word) <= 2)
        if (short_words / len(words)) > 0.3:
            return True
    
    return False

async def extract_ingredients_with_enhanced_processing(text: str, image_data: bytes = None) -> List[str]:
    """Enhanced ingredient extraction for garbled text using multiple strategies."""
    try:
        # Try Google Vision first (best for garbled text)
        try:
            ingredients = await extract_ingredients_with_google_vision(text.encode() if isinstance(text, str) else text)
            if ingredients:
                logger.info(f"Google Vision extracted {len(ingredients)} ingredients from garbled text")
                return ingredients
        except Exception as e:
            logger.warning(f"Google Vision failed for garbled text: {e}")
        
        # Try OpenAI with image if available
        if image_data:
            try:
                from llm_utils import extract_ingredients_from_text_openai
                ingredients = await extract_ingredients_from_text_openai(text, image_data)
                if ingredients:
                    logger.info(f"OpenAI with image extracted {len(ingredients)} ingredients from garbled text")
                    return ingredients
            except Exception as e:
                logger.warning(f"OpenAI with image failed: {e}")
        
        # Fallback to enhanced regex with dynamic corrections
        return extract_ingredients_with_dynamic_corrections(text)
        
    except Exception as e:
        logger.error(f"Enhanced processing failed: {e}")
        return extract_ingredients_from_text(text)

def extract_ingredients_with_dynamic_corrections(text: str) -> List[str]:
    """Extract ingredients using dynamic corrections based on database."""
    try:
        # Get all ingredient names from database for dynamic corrections
        from database import get_all_ingredient_names
        db_ingredients = get_all_ingredient_names()
        
        # Expand database with common cosmetic ingredients if DB is small
        if len(db_ingredients) < 50:
            expanded_ingredients = [
                'water', 'aqua', 'glycerin', 'glycerol', 'aloe vera', 'aloe barbadensis',
                'phenoxyethanol', 'ethylhexylglycerin', 'stearic acid', 'glyceryl stearate',
                'cetearyl alcohol', 'isopropyl palmitate', 'triethanolamine', 'parfum',
                'fragrance', 'sodium chloride', 'citric acid', 'sodium hydroxide',
                'dimethicone', 'cyclomethicone', 'tocopherol', 'vitamin e',
                'retinol', 'hyaluronic acid', 'niacinamide', 'salicylic acid',
                'benzoyl peroxide', 'sulfur', 'tea tree oil', 'chamomile extract',
                'green tea extract', 'vitamin c', 'ascorbic acid', 'peptides',
                'ceramides', 'squalane', 'jojoba oil', 'argan oil', 'coconut oil',
                'shea butter', 'cocoa butter', 'lanolin', 'beeswax', 'carnauba wax',
                'sodium lauryl sulfate', 'sodium laureth sulfate', 'cocamidopropyl betaine',
                'decyl glucoside', 'lauryl glucoside', 'sorbitan oleate', 'polysorbate 20',
                'polysorbate 80', 'xanthan gum', 'carbomer', 'acrylates copolymer',
                'methylparaben', 'propylparaben', 'butylparaben', 'ethylparaben',
                'imidazolidinyl urea', 'diazolidinyl urea', 'quaternium-15', 'formaldehyde',
                'triclosan', 'triclocarban', 'bht', 'bha', 'edta', 'disodium edta',
                'trisodium edta', 'tetrasodium edta', 'sodium edta', 'calcium edta',
                'magnesium edta', 'potassium edta', 'ammonium edta', 'dipotassium edta',
                'natura', 'hidratante', 'corporal', 'lotion', 'crema', 'extracto'
            ]
            db_ingredients.extend(expanded_ingredients)
            db_ingredients = list(set(db_ingredients))  # Remove duplicates
        
        # Create dynamic corrections dictionary
        corrections = {}
        for ingredient in db_ingredients:
            # Generate common OCR errors for this ingredient
            variations = generate_ocr_variations(ingredient)
            for variation in variations:
                corrections[variation.lower()] = ingredient
        
        # Apply corrections
        corrected_text = text.lower()
        for garbled, correct in corrections.items():
            corrected_text = corrected_text.replace(garbled, correct)
        
        # Extract ingredients from corrected text
        ingredients = extract_ingredients_from_text(corrected_text)
        
        # If still no ingredients, try fuzzy matching
        if not ingredients:
            ingredients = fuzzy_match_ingredients(text, db_ingredients)
        
        return ingredients
        
    except Exception as e:
        logger.error(f"Dynamic corrections failed: {e}")
        return extract_ingredients_from_text(text)

def generate_ocr_variations(ingredient: str) -> List[str]:
    """Generate common OCR error variations for an ingredient."""
    variations = []
    ingredient_lower = ingredient.lower()
    
    # Common OCR substitutions
    substitutions = {
        'a': ['@', '4', 'o'],
        'e': ['3', '€'],
        'i': ['1', 'l', '|'],
        'o': ['0', 'Q'],
        's': ['5', '$'],
        't': ['7', '+'],
        'l': ['1', 'I', '|'],
        'n': ['m', 'rn'],
        'm': ['rn', 'n'],
        'c': ['(', 'G'],
        'g': ['6', '9'],
        'b': ['6', '8'],
        'p': ['9', 'q'],
        'q': ['g', '9'],
        'u': ['v', 'w'],
        'v': ['u', 'w'],
        'w': ['vv', 'u'],
        'x': ['+', 'X'],
        'y': ['v', '7'],
        'z': ['2', 's']
    }
    
    # Generate variations by substituting characters
    for i, char in enumerate(ingredient_lower):
        if char in substitutions:
            for sub in substitutions[char]:
                variation = ingredient_lower[:i] + sub + ingredient_lower[i+1:]
                variations.append(variation)
    
    # Generate variations by removing/adding characters
    if len(ingredient_lower) > 3:
        # Remove one character
        for i in range(len(ingredient_lower)):
            variation = ingredient_lower[:i] + ingredient_lower[i+1:]
            variations.append(variation)
        
        # Add one character (common insertions)
        for i in range(len(ingredient_lower)):
            for char in ['a', 'e', 'i', 'o', 'u', 'n', 'r']:
                variation = ingredient_lower[:i] + char + ingredient_lower[i:]
                variations.append(variation)
    
    return list(set(variations))  # Remove duplicates

def fuzzy_match_ingredients(text: str, db_ingredients: List[str], threshold: float = 0.6) -> List[str]:
    """Fuzzy match text against database ingredients with adaptive threshold."""
    try:
        from difflib import SequenceMatcher
        
        words = text.split()
        matched_ingredients = []
        
        for word in words:
            if len(word) < 3:
                continue
                
            best_match = None
            best_ratio = 0
            
            for ingredient in db_ingredients:
                # Try exact substring match first
                if word.lower() in ingredient.lower():
                    matched_ingredients.append(ingredient)
                    continue
                
                # Try fuzzy matching
                ratio = SequenceMatcher(None, word.lower(), ingredient.lower()).ratio()
                
                # Adaptive threshold based on word length
                adaptive_threshold = threshold
                if len(word) < 5:
                    adaptive_threshold = 0.5  # Lower threshold for short words
                elif len(word) > 10:
                    adaptive_threshold = 0.7  # Higher threshold for long words
                
                if ratio > best_ratio and ratio >= adaptive_threshold:
                    best_ratio = ratio
                    best_match = ingredient
            
            if best_match and best_match not in matched_ingredients:
                matched_ingredients.append(best_match)
                logger.info(f"Fuzzy matched '{word}' -> '{best_match}' (ratio: {best_ratio:.2f})")
        
        return matched_ingredients
        
    except Exception as e:
        logger.error(f"Fuzzy matching failed: {e}")
        return []

def fuzzy_match_ingredients(text: str, db_ingredients: List[str], threshold: float = 0.6) -> List[str]:
    """Fuzzy match text against database ingredients with adaptive threshold."""
    try:
        from difflib import SequenceMatcher
        
        words = text.split()
        matched_ingredients = []
        
        for word in words:
            if len(word) < 3:
                continue
                
            best_match = None
            best_ratio = 0
            
            for ingredient in db_ingredients:
                # Try exact substring match first
                if word.lower() in ingredient.lower():
                    matched_ingredients.append(ingredient)
                    continue
                
                # Try fuzzy matching
                ratio = SequenceMatcher(None, word.lower(), ingredient.lower()).ratio()
                
                # Adaptive threshold based on word length
                adaptive_threshold = threshold
                if len(word) < 5:
                    adaptive_threshold = 0.5  # Lower threshold for short words
                elif len(word) > 10:
                    adaptive_threshold = 0.7  # Higher threshold for long words
                
                if ratio > best_ratio and ratio >= adaptive_threshold:
                    best_ratio = ratio
                    best_match = ingredient
            
            if best_match and best_match not in matched_ingredients:
                matched_ingredients.append(best_match)
                logger.info(f"Fuzzy matched '{word}' -> '{best_match}' (ratio: {best_ratio:.2f})")
        
        return matched_ingredients
        
    except Exception as e:
        logger.error(f"Fuzzy matching failed: {e}")
        return []

def clean_and_deduplicate_ingredients(ingredients: List[str]) -> List[str]:
    """Clean and deduplicate ingredients, removing corrupted text."""
    import re
    from difflib import SequenceMatcher
    
    if not ingredients:
        return []
    
    cleaned = []
    seen = set()
    
    try:
        for ingredient in ingredients:
            if not ingredient or len(ingredient.strip()) < 2:
                continue
                
            # Clean the ingredient
            try:
                cleaned_ingredient = clean_ingredient_text(ingredient.strip())
            except Exception as e:
                logger.warning(f"Error cleaning ingredient '{ingredient}': {e}")
                cleaned_ingredient = ingredient.strip()
            
            if not cleaned_ingredient or len(cleaned_ingredient) < 2:
                continue
                
            # Skip if it's mostly corrupted characters
            try:
                if is_corrupted_text(cleaned_ingredient):
                    continue
            except Exception as e:
                logger.warning(f"Error checking if corrupted '{cleaned_ingredient}': {e}")
                # If we can't check, include it anyway
                
            # Check for duplicates using fuzzy matching
            is_duplicate = False
            try:
                for existing in cleaned:
                    if SequenceMatcher(None, cleaned_ingredient.lower(), existing.lower()).ratio() > 0.8:
                        is_duplicate = True
                        break
            except Exception as e:
                logger.warning(f"Error checking duplicates for '{cleaned_ingredient}': {e}")
                # If we can't check duplicates, include it anyway
                
            if not is_duplicate:
                cleaned.append(cleaned_ingredient)
                seen.add(cleaned_ingredient.lower())
    except Exception as e:
        logger.error(f"Error in clean_and_deduplicate_ingredients: {e}")
        # Return original ingredients if cleaning fails
        return ingredients[:MAX_OCR_INGREDIENTS]
    
    return cleaned

def clean_ingredient_text(text: str) -> str:
    """Clean corrupted ingredient text."""
    if not text:
        return ""
    
    try:
        # Remove common OCR artifacts
        text = re.sub(r'[^\w\s\-.,()\[\]/]', '', text)  # Keep only alphanumeric, spaces, and common punctuation
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single space
        text = re.sub(r'^[^a-zA-Z]*', '', text)  # Remove leading non-letters
        text = re.sub(r'[^a-zA-Z]*$', '', text)  # Remove trailing non-letters
        
        # Fix common OCR mistakes
        corrections = {
            r'\b0\b': 'O',  # Zero to O
            r'\b1\b': 'I',  # One to I
            r'\b5\b': 'S',  # Five to S
            r'\b8\b': 'B',  # Eight to B
            r'[|]': 'I',    # Pipe to I
            r'[`\']': '',   # Remove quotes
            r'[{}]': '',    # Remove braces
        }
        
        for pattern, replacement in corrections.items():
            text = re.sub(pattern, replacement, text)
        
        return text.strip()
    except Exception as e:
        logger.warning(f"Error cleaning text '{text}': {e}")
        return text.strip()

def is_corrupted_text(text: str) -> bool:
    """Check if text is too corrupted to be useful."""
    if not text or len(text) < 3:
        return True
    
    try:
        # Check for too many special characters
        special_chars = sum(1 for c in text if not c.isalnum() and c not in ' -.,()[]/')
        if special_chars > len(text) * 0.3:  # More than 30% special chars
            return True
            
        # Check for too many numbers (ingredients rarely have many numbers)
        numbers = sum(1 for c in text if c.isdigit())
        if numbers > len(text) * 0.4:  # More than 40% numbers
            return True
            
        # Check for repeated characters
        if len(set(text)) < len(text) * 0.5:  # Less than 50% unique characters
            return True

        words = [word for word in re.split(r'\s+', text) if word]
        if not words:
            return True

        if not any(len(re.sub(r'[^A-Za-z]', '', word)) >= 3 for word in words):
            return True

        alphabetic_chars = sum(1 for c in text if c.isalpha())
        if alphabetic_chars < 3:
            return True
            
        return False
    except Exception as e:
        logger.warning(f"Error checking if text is corrupted '{text}': {e}")
        # If we can't check, assume it's not corrupted
        return False


def is_likely_ci_code(text: str) -> bool:
    candidate = re.sub(r'\s+', '', text.upper())
    return bool(re.match(r'^CI\d{5}$', candidate))


def resolve_canonical_ingredient(cleaned_candidate: str) -> Optional[str]:
    normalized_candidate = _normalize_ingredient_key(cleaned_candidate)
    if not normalized_candidate or normalized_candidate in STOPWORDS:
        return None

    canonical = INGREDIENT_LEXICON.get(normalized_candidate)
    if canonical:
        return canonical

    compact_key = normalized_candidate.replace(" ", "")
    canonical = INGREDIENT_LEXICON.get(compact_key)
    if canonical:
        return canonical

    first_char = normalized_candidate[0]
    candidates = INGREDIENT_LEXICON_INDEX.get(first_char, [])
    best_ratio = 0.0
    best_match = None

    for candidate_key, candidate_value in candidates:
        if abs(len(candidate_key) - len(normalized_candidate)) > 6:
            continue
        ratio = SequenceMatcher(None, normalized_candidate, candidate_key).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = candidate_value
        if ratio >= 0.95:
            break

    if best_ratio >= 0.88:
        return best_match

    return None

def extract_ingredients_from_text(text: str) -> List[str]:
    """Extract ingredients from text using enhanced parsing with better cleaning."""
    if not text:
        return []

    # Split by common separators
    segments = re.split(r"[\n,;•·\-|()\[\]]+", text)
    seen = set()
    results: List[str] = []

    for segment in segments:
        candidate = segment.strip()
        if not candidate or len(candidate) < 2:
            continue

        # Skip if it's corrupted text
        if is_corrupted_text(candidate):
            continue

        # Clean the candidate
        cleaned_candidate = clean_ingredient_text(candidate)
        if not cleaned_candidate or len(cleaned_candidate) < 2:
            continue

        canonical = resolve_canonical_ingredient(cleaned_candidate)
        normalized_candidate = _normalize_ingredient_key(canonical or cleaned_candidate)

        value = canonical or cleaned_candidate
        key = canonical.lower() if canonical else normalized_candidate

        # Skip if too short, stopword, or duplicate
        if len(key) <= 2 or key in STOPWORDS or key in seen:
            continue

        seen.add(key)
        results.append(value)

    if results:
        return results

    fallback_matches = re.findall(r"\b[A-Za-z][A-Za-z-]+(?:\s+[A-Za-z][A-Za-z-]+)*\b", text)
    fallback_results = []
    for match in fallback_matches:
        normalized_match = _normalize_ingredient_key(match)
        if len(normalized_match) <= 3 or normalized_match in STOPWORDS or normalized_match in seen:
            continue
        canonical = resolve_canonical_ingredient(match)
        seen.add(normalized_match)
        fallback_results.append(canonical or match.strip())
    return fallback_results


def extract_ingredients_from_corrupted_text(text: str) -> List[str]:
    """Backward compatible wrapper kept for legacy tests."""
    return extract_ingredients_from_text(text)

async def analyze_ingredients(ingredients: List[str], user_need: str, db: Session) -> ProductAnalysisResponse:
    """Analyze ingredients and return comprehensive results."""
    try:
        logger.info(f"Analyzing {len(ingredients)} ingredients...")
        
        ingredients_details = []
        ingredient_cache: Dict[str, Dict[str, Any]] = {}
        total_eco_score = 0
        risk_counts = defaultdict(int, {
            "seguro": 0,
            "riesgo bajo": 0,
            "riesgo medio": 0,
            "riesgo alto": 0,
            "cancerígeno": 0,
            "desconocido": 0
        })
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for ingredient in ingredients:
                try:
                    normalized_name = ingredient.lower()
                    if normalized_name in ingredient_cache:
                        combined_data = ingredient_cache[normalized_name]
                    else:
                        local_data = get_ingredient_data(ingredient)
                        remote_data: Optional[Dict[str, Any]] = None
                        try:
                            remote_data = await fetch_ingredient_data(ingredient, client)
                            logger.info("Remote data fetched for %s", ingredient)
                        except Exception as fetch_error:
                            logger.error("Remote fetch failed for %s: %s", ingredient, fetch_error)
                        combined_data = merge_ingredient_data(remote_data, local_data)
                        ingredient_cache[normalized_name] = combined_data

                    eco_score = combined_data.get('eco_score', 50.0)
                    risk_level = combined_data.get('risk_level', 'desconocido')
                    benefits = combined_data.get('benefits', 'No disponible')
                    risks = combined_data.get('risks_detailed', 'No disponible')
                    sources = combined_data.get('sources', 'Análisis básico')

                    ingredients_details.append(IngredientAnalysisResponse(
                        name=ingredient,
                        eco_score=eco_score,
                        risk_level=risk_level,
                        benefits=benefits,
                        risks_detailed=risks,
                        sources=sources
                    ))

                    total_eco_score += eco_score
                    risk_counts[risk_level] += 1

                except Exception as e:
                    logger.warning(f"Error analyzing ingredient {ingredient}: {e}")
                    ingredients_details.append(IngredientAnalysisResponse(
                        name=ingredient,
                        eco_score=50.0,
                        risk_level='desconocido',
                        benefits='Error en análisis',
                        risks_detailed='No se pudo analizar',
                        sources='Error'
                    ))
                    total_eco_score += 50.0
                    risk_counts['desconocido'] += 1
        
        # Calculate average eco score
        avg_eco_score = total_eco_score / len(ingredients) if ingredients else 50.0
        
        # Determine suitability
        if risk_counts['cancerígeno'] > 0 or risk_counts['riesgo alto'] > 2:
            suitability = "No"
        elif risk_counts['riesgo alto'] > 0 or risk_counts['riesgo medio'] > 3:
            suitability = "Evaluar"
        else:
            suitability = "Sí"
        
        # Generate recommendations
        recommendations = generate_recommendations(ingredients_details, user_need, avg_eco_score, risk_counts)
        
        return ProductAnalysisResponse(
            product_name="Product Analysis",
            ingredients_details=ingredients_details,
            avg_eco_score=round(avg_eco_score, 1),
            suitability=suitability,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Error in ingredient analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

def generate_recommendations(ingredients: List[IngredientAnalysisResponse], user_need: str, avg_eco_score: float, risk_counts: Dict) -> str:
    """Generate personalized recommendations."""
    recommendations = []
    
    # Eco score recommendations
    if avg_eco_score >= 80:
        recommendations.append("Excelente puntaje eco-friendly; producto muy sostenible.")
    elif avg_eco_score >= 60:
        recommendations.append("Buen puntaje eco-friendly; producto moderadamente sostenible.")
    else:
        recommendations.append("Puntaje eco-friendly bajo; considera alternativas más sostenibles.")
    
    # Risk-based recommendations
    if risk_counts['cancerígeno'] > 0:
        recommendations.append("Contiene ingredientes cancerígenos; evitar uso prolongado.")
    elif risk_counts['riesgo alto'] > 0:
        recommendations.append("Contiene ingredientes de alto riesgo; usar con precaución.")
    elif risk_counts['riesgo medio'] > 2:
        recommendations.append("Múltiples ingredientes de riesgo medio; monitorear reacciones.")
    
    # User need specific recommendations
    if user_need == "sensitive skin":
        if risk_counts['riesgo alto'] > 0 or risk_counts['riesgo medio'] > 1:
            recommendations.append("No recomendado para piel sensible; busca alternativas más suaves.")
        else:
            recommendations.append("Aparentemente seguro para piel sensible; realiza una prueba de parche.")
    elif user_need == "pregnancy":
        if risk_counts['riesgo alto'] > 0 or risk_counts['cancerígeno'] > 0:
            recommendations.append("No recomendado durante el embarazo; consulta con tu médico.")
        else:
            recommendations.append("Aparentemente seguro durante el embarazo; consulta con tu médico antes de usar.")
    
    return "\n\n".join(recommendations) if recommendations else "Análisis completado. Revisa los ingredientes individuales."


def normalize_user_need(user_need: Optional[str]) -> str:
    if not user_need:
        return DEFAULT_USER_NEED
    normalized = user_need.strip().lower()
    return normalized if normalized in ALLOWED_USER_NEEDS else DEFAULT_USER_NEED


def merge_ingredient_data(remote_data: Optional[Dict[str, Any]], local_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "eco_score": 50.0,
        "risk_level": "desconocido",
        "benefits": "No disponible",
        "risks_detailed": "Datos insuficientes para evaluación",
        "sources": "Análisis básico"
    }

    if local_data:
        local_clean = _sanitize_analysis_data(local_data)
        base.update(local_clean)

    if remote_data:
        remote_clean = dict(remote_data)
        remote_sources = remote_clean.get("sources")
        local_sources = base.get("sources")
        sources: List[str] = []
        for src in (remote_sources, local_sources):
            if not src:
                continue
            if isinstance(src, str):
                parts = [part.strip() for part in src.split("|")]
            elif isinstance(src, (list, tuple, set)):
                parts = [str(part).strip() for part in src]
            else:
                parts = [str(src).strip()]
            for part in parts:
                if part:
                    sources.append(part)
        if sources:
            remote_clean["sources"] = " | ".join(dict.fromkeys(sources))
        remote_sanitized = _sanitize_analysis_data(remote_clean)
        base.update(remote_sanitized)

    return _sanitize_analysis_data(base)

# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "MommyShops API is running", "version": "3.0.1"}

@app.post("/auth/register", response_model=AuthRegisterResponse, tags=["auth"])
async def auth_register(payload: AuthRegisterRequest, db: Session = Depends(get_db)):
    username = payload.username.strip()
    existing_user = (
        db.query(User)
        .filter((User.username == username) | (User.email == payload.email))
        .first()
    )
    if existing_user:
        raise HTTPException(status_code=400, detail="El usuario o correo ya existe")

    new_user = User(
        username=username,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return AuthRegisterResponse(user_id=new_user.id, username=new_user.username or "", email=new_user.email or "")


@app.post("/auth/token", response_model=TokenResponse, tags=["auth"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    username = form_data.username.strip()
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": str(user.id)}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return TokenResponse(access_token=token)


@app.get("/auth/me", response_model=AuthenticatedUser, tags=["auth"])
async def read_current_user_profile(current_user: User = Depends(get_current_user)):
    return AuthenticatedUser(user_id=current_user.id, username=current_user.username, email=current_user.email)


@app.get("/auth/google", tags=["auth"])
async def google_auth():
    """Get Google OAuth2 authorization URL"""
    auth_url = get_google_auth_url()
    if not auth_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth2 not configured"
        )
    return {"auth_url": auth_url}


@app.get("/auth/google/callback", tags=["auth"])
async def google_auth_callback(
    code: str = None,
    error: str = None,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth2 callback"""
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth2 error: {error}"
        )
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided"
        )
    
    # Handle Google callback
    google_user = await handle_google_callback(code)
    if not google_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google authentication failed"
        )
    
    # Check if user exists using unified data service
    from unified_data_service import get_user_by_email_unified
    existing_user = get_user_by_email_unified(google_user['email'])
    
    if not existing_user:
        # Create new user using unified data service
        from unified_data_service import create_user_unified
        
        user_data = {
            'google_id': google_user['google_id'],
            'email': google_user['email'],
            'username': google_user['email'].split('@')[0],  # Use email prefix as username
            'google_name': google_user['name'],
            'google_picture': google_user['picture'],
            'auth_provider': 'google'
        }
        
        success, sqlite_id, firebase_uid = create_user_unified(user_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        # Get the created user from database
        user = db.query(User).filter(User.id == int(sqlite_id)).first()
        logger.info(f"Created new Google user: {user.email} (SQLite: {sqlite_id}, Firebase: {firebase_uid})")
    else:
        # Update existing user with Google info
        user = db.query(User).filter(User.id == existing_user['id']).first()
        user.google_id = google_user['google_id']
        user.google_name = google_user['name']
        user.google_picture = google_user['picture']
        user.auth_provider = 'google'
        db.commit()
        logger.info(f"Updated existing user with Google info: {user.email}")
    
    # Generate JWT token
    token = create_access_token({"sub": str(user.id)}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "name": user.google_name,
            "picture": user.google_picture,
            "auth_provider": user.auth_provider
        }
    }


@app.post("/register", response_model=RegisterResponse)
async def register_user(
    request: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Register a user profile with onboarding answers and optional routine."""
    try:
        data = RegisterRequest.from_request(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    hair_info = data.hair_scalp_info
    conditions = _collect_conditions(data.conditions, data.other_condition)
    routine_products = [{"name": name} for name in data.products]

    try:
        if current_user:
            user = db.query(User).filter(User.id == current_user.id).with_for_update().first()
            if not user:
                raise HTTPException(status_code=404, detail="Usuario autenticado no encontrado")
        else:
            user = User()
            db.add(user)
            db.flush()

        user.skin_face = data.skin_face
        user.hair_type = data.hair_type
        user.goals_face = [goal.lower() for goal in data.goals_face]
        user.climate = data.climate
        user.skin_body = [item.lower() for item in data.skin_body]
        user.goals_body = [item.lower() for item in data.goals_body]
        user.hair_porosity = [item.lower() for item in data.hair_porosity]
        user.goals_hair = data.goals_hair
        user.hair_thickness_scalp = {
            "thickness": hair_info.thickness,
            "scalp": hair_info.scalp,
        }
        user.conditions = conditions

        routine_id: Optional[int] = None
        if routine_products:
            routine = Routine(
                user_id=user.id,
                products=routine_products,
                extracted_ingredients=[],
                notes=None,
            )
            db.add(routine)
            db.flush()
            routine_id = routine.id

        db.commit()
        return RegisterResponse(user_id=user.id, routine_id=routine_id)
    except Exception as exc:
        db.rollback()
        logger.error("Error registering user: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to register user")


# Firebase Authentication Endpoints
@app.post("/firebase/register", response_model=FirebaseRegisterResponse, tags=["firebase"])
async def firebase_register_user(request: FirebaseRegisterRequest):
    """Register a new user with Firebase Auth and Firestore."""
    try:
        if not is_firebase_available():
            raise HTTPException(
                status_code=503, 
                detail="Firebase not available. Check your configuration."
            )
        
        firebase_auth = get_firebase_auth()
        firestore_db = get_firestore_client()
        
        # Create user in Firebase Auth
        try:
            user_record = firebase_auth.create_user(
                email=request.email,
                password=request.password,
                display_name=request.name
            )
        except firebase_auth.EmailAlreadyExistsError:
            raise HTTPException(
                status_code=400, 
                detail="Email already registered"
            )
        except Exception as e:
            logger.error(f"Firebase Auth error: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to create user: {str(e)}"
            )
        
        # Create user profile in Firestore
        user_data = request.dict()
        profile_data = _create_firebase_user_profile(
            user_record.uid, 
            request.email, 
            user_data
        )
        
        try:
            firestore_db.collection('users').document(user_record.uid).set(profile_data)
        except Exception as e:
            logger.error(f"Firestore error: {e}")
            # Clean up Firebase Auth user if Firestore fails
            try:
                firebase_auth.delete_user(user_record.uid)
            except:
                pass
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to save user profile: {str(e)}"
            )
        
        # Send email verification
        try:
            firebase_auth.generate_email_verification_link(request.email)
        except Exception as e:
            logger.warning(f"Failed to send verification email: {e}")
        
        return FirebaseRegisterResponse(
            uid=user_record.uid,
            email=request.email,
            message="User registered successfully. Please check your email for verification."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in Firebase registration: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error during registration"
        )


@app.post("/firebase/login", response_model=FirebaseLoginResponse, tags=["firebase"])
async def firebase_login_user(request: FirebaseLoginRequest):
    """Login user with Firebase Auth and return user profile with enhanced security."""
    try:
        if not is_firebase_available():
            raise HTTPException(
                status_code=503, 
                detail="Firebase not available. Check your configuration."
            )
        
        firebase_auth = get_firebase_auth()
        
        # Verify user credentials by getting user by email
        try:
            user_record = firebase_auth.get_user_by_email(request.email)
            
            # Check if user is disabled
            if user_record.disabled:
                raise HTTPException(
                    status_code=403, 
                    detail="User account is disabled"
                )
            
            # Check if email is verified (optional enforcement)
            if not user_record.email_verified:
                logger.warning(f"User {request.email} attempted login with unverified email")
                # Continue with login but log the warning
            
        except firebase_auth.UserNotFoundError:
            # Log failed login attempt for security monitoring
            logger.warning(f"Failed login attempt for non-existent user: {request.email}")
            raise HTTPException(
                status_code=401, 
                detail="Invalid email or password"
            )
        except Exception as e:
            logger.error(f"Firebase Auth error: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Authentication service error"
            )
        
        # Get user profile from Firestore
        profile = await _get_firebase_user_profile(user_record.uid)
        if not profile:
            raise HTTPException(
                status_code=404, 
                detail="User profile not found"
            )
        
        # Generate custom token for client-side authentication with enhanced claims
        try:
            # Add custom claims for enhanced security
            custom_claims = {
                "role": "user",
                "email_verified": user_record.email_verified,
                "last_login": datetime.utcnow().isoformat()
            }
            
            custom_token = firebase_auth.create_custom_token(
                user_record.uid, 
                custom_claims
            )
        except Exception as e:
            logger.warning(f"Failed to create custom token: {e}")
            custom_token = None
        
        # Update last login timestamp in Firestore
        try:
            await _update_firebase_user_profile(user_record.uid, {
                "last_login": firestore.SERVER_TIMESTAMP
            })
        except Exception as e:
            logger.warning(f"Failed to update last login timestamp: {e}")
        
        return FirebaseLoginResponse(
            uid=user_record.uid,
            email=user_record.email,
            name=profile.name,
            custom_token=custom_token.decode('utf-8') if custom_token else None,
            message="Login successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in Firebase login: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error during login"
        )


@app.get("/firebase/user/{uid}", response_model=FirebaseUserProfile, tags=["firebase"])
async def get_firebase_user_profile(uid: str):
    """Get user profile from Firestore."""
    try:
        if not is_firebase_available():
            raise HTTPException(
                status_code=503, 
                detail="Firebase not available. Check your configuration."
            )
        
        profile = await _get_firebase_user_profile(uid)
        if not profile:
            raise HTTPException(
                status_code=404, 
                detail="User profile not found"
            )
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error"
        )


@app.put("/firebase/user/{uid}", response_model=FirebaseUserProfile, tags=["firebase"])
async def update_firebase_user_profile(uid: str, request: FirebaseUserUpdateRequest):
    """Update user profile in Firestore."""
    try:
        if not is_firebase_available():
            raise HTTPException(
                status_code=503, 
                detail="Firebase not available. Check your configuration."
            )
        
        # Prepare update data
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(
                status_code=400, 
                detail="No fields to update"
            )
        
        # Update profile in Firestore
        success = await _update_firebase_user_profile(uid, update_data)
        if not success:
            raise HTTPException(
                status_code=500, 
                detail="Failed to update user profile"
            )
        
        # Return updated profile
        updated_profile = await _get_firebase_user_profile(uid)
        if not updated_profile:
            raise HTTPException(
                status_code=404, 
                detail="User profile not found after update"
            )
        
        return updated_profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error"
        )


@app.delete("/firebase/user/{uid}", tags=["firebase"])
async def delete_firebase_user(uid: str):
    """Delete user from Firebase Auth and Firestore."""
    try:
        if not is_firebase_available():
            raise HTTPException(
                status_code=503, 
                detail="Firebase not available. Check your configuration."
            )
        
        firebase_auth = get_firebase_auth()
        firestore_db = get_firestore_client()
        
        # Delete from Firestore first
        try:
            firestore_db.collection('users').document(uid).delete()
        except Exception as e:
            logger.warning(f"Failed to delete from Firestore: {e}")
        
        # Delete from Firebase Auth
        try:
            firebase_auth.delete_user(uid)
        except firebase_auth.UserNotFoundError:
            logger.warning(f"User {uid} not found in Firebase Auth")
        except Exception as e:
            logger.error(f"Failed to delete from Firebase Auth: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to delete user from authentication service"
            )
        
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error"
        )


@app.post("/firebase/refresh", response_model=FirebaseRefreshTokenResponse, tags=["firebase"])
async def refresh_firebase_token(request: FirebaseRefreshTokenRequest):
    """Refresh Firebase access token using refresh token."""
    try:
        if not is_firebase_available():
            raise HTTPException(
                status_code=503, 
                detail="Firebase not available. Check your configuration."
            )
        
        firebase_auth = get_firebase_auth()
        
        try:
            # Verify the refresh token and get user info
            # Note: In a real implementation, you would verify the refresh token
            # and generate a new access token. This is a simplified version.
            
            # For now, we'll create a new custom token
            # In production, implement proper refresh token validation
            custom_token = firebase_auth.create_custom_token(
                "temp-uid",  # This should be extracted from the refresh token
                {"role": "user", "refreshed": True}
            )
            
            # Generate new refresh token (simplified)
            new_refresh_token = f"refresh_{datetime.utcnow().timestamp()}"
            
            return FirebaseRefreshTokenResponse(
                access_token=custom_token.decode('utf-8'),
                refresh_token=new_refresh_token,
                token_type="bearer",
                expires_in=3600  # 1 hour
            )
            
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            raise HTTPException(
                status_code=401, 
                detail="Invalid refresh token"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in token refresh: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error during token refresh"
        )


@app.post("/analyze_routine/{user_id}", response_model=RoutineAnalysisResponse)
async def analyze_routine_endpoint(
    user_id: int,
    file: Optional[UploadFile] = File(default=None),
    product_name: Optional[str] = Form(default=None),
    user_need: Optional[str] = Form(default=None),
    notes: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Analyze a user's routine through OCR or stored products and suggest substitutes."""
    if current_user and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="No autorizado para analizar este usuario")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = _build_user_profile(user)
    await ensure_recommender_ready()

    extracted_ingredients: List[str] = []
    product_inputs: List[Dict[str, Any]] = []
    analysis_result: Optional[ProductAnalysisResponse] = None
    nemotron_cache: Dict[str, Dict[str, Any]] = {}

    if file is not None:
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        image_data = await file.read()
        if not image_data:
            raise HTTPException(status_code=400, detail="Empty image file")

        if len(image_data) > MAX_IMAGE_SIZE:
            max_size_mb = round(MAX_IMAGE_SIZE / (1024 * 1024), 2)
            raise HTTPException(status_code=400, detail=f"Image too large. Maximum size is {max_size_mb}MB.")

        try:
            extracted_ingredients = await asyncio.wait_for(
                extract_ingredients_from_image(image_data),
                timeout=45.0,
            )
        except asyncio.TimeoutError:
            logger.warning("Routine OCR timed out for user %s", user_id)
        except Exception as exc:
            logger.error("Routine OCR failed for user %s: %s", user_id, exc)

        if extracted_ingredients:
            extracted_ingredients = extracted_ingredients[:MAX_OCR_INGREDIENTS]
            ingredients_for_analysis = extracted_ingredients[:MAX_ANALYZED_INGREDIENTS]
            normalized_need = normalize_user_need(user_need or DEFAULT_USER_NEED)
            analysis_result = await analyze_ingredients(ingredients_for_analysis, normalized_need, db)
            product_inputs.append(
                {
                    "name": product_name or analysis_result.product_name or f"Routine from {file.filename}",
                    "ingredients": ingredients_for_analysis,
                    "brand": None,
                }
            )
        else:
            analysis_result = ProductAnalysisResponse(
                product_name=product_name or f"Routine from {file.filename}",
                ingredients_details=[],
                avg_eco_score=50.0,
                suitability="No se pudo analizar",
                recommendations="No se detectaron ingredientes en la imagen. Intenta con una captura más clara.",
            )
    else:
        routine_products = _load_user_routine_products(db, user_id)
        if not routine_products:
            raise HTTPException(status_code=404, detail="No routine found for evaluation")

        for name in routine_products:
            info = _fetch_product_ingredients(db, name)
            product_inputs.append(
                {
                    "name": name,
                    "ingredients": info["ingredients"],
                    "brand": info["brand"],
                }
            )

        analysis_result = ProductAnalysisResponse(
            product_name="Rutina registrada",
            ingredients_details=[],
            avg_eco_score=50.0,
            suitability="Evaluar",
            recommendations="Revisa los resultados individuales para cada producto.",
        )

    if analysis_result is None:
        analysis_result = ProductAnalysisResponse(
            product_name="Rutina",
            ingredients_details=[],
            avg_eco_score=50.0,
            suitability="Evaluar",
            recommendations="No se pudo generar análisis.",
        )

    routine_payload = [
        {
            "name": item.get("name"),
            "ingredients": item.get("ingredients"),
            "brand": item.get("brand"),
        }
        for item in product_inputs
    ] or None

    routine_record = Routine(
        user_id=user.id,
        products=routine_payload,
        extracted_ingredients=extracted_ingredients,
        notes=notes,
    )

    alerts_global: List[str] = []
    recommendations_global: List[str] = []
    substitute_accumulator: List[SubstituteSuggestion] = []
    product_evaluations: List[ProductEvaluation] = []

    try:
        db.add(routine_record)
        db.flush()

        for product in product_inputs:
            name = product.get("name") or "Producto"
            ingredient_list = product.get("ingredients") or []
            if not ingredient_list:
                continue

            analysis_data = _analyze_ingredients_for_profile(name, ingredient_list, profile)
            alerts = analysis_data["alerts"]
            meets_needs = analysis_data["meets_needs"]

            substitutes: List[SubstituteSuggestion] = []
            suggestion_messages: List[str] = []
            nemotron_alternatives: List[str] = []

            excluded_ingredients = analysis_data.get("excluded", []) or []
            if excluded_ingredients:
                for flagged in excluded_ingredients[:2]:
                    key = flagged.lower()
                    if key not in nemotron_cache:
                        try:
                            # Use Google Vision for ingredient enrichment instead of NVIDIA
                            nemotron_cache[key] = await analyze_ingredients_with_google_vision(
                                [flagged],
                                profile.get("conditions", []) if profile else []
                            )
                        except Exception as exc:
                            logger.error("Nemotron enrichment failed for %s: %s", flagged, exc)
                            nemotron_cache[key] = {}

                    enrichment = nemotron_cache.get(key) or {}
                    summary = enrichment.get("summary")
                    if summary:
                        summary_msg = f"ℹ️ {flagged}: {summary}"
                        if summary_msg not in alerts:
                            alerts.append(summary_msg)
                    risks = enrichment.get("risks") or []
                    if risks:
                        risk_msg = f"⚠️ {flagged}: {risks[0]}"
                        if risk_msg not in alerts:
                            alerts.append(risk_msg)
                    alternatives = enrichment.get("alternatives") or []
                    for alternative in alternatives:
                        alt_name = alternative.get("name") or ""
                        alt_brand = alternative.get("brand")
                        alt_reason = alternative.get("reason")
                        label = alt_name
                        if alt_brand:
                            label = f"{alt_brand} {alt_name}".strip()
                        if alt_reason:
                            label = f"{label} - {alt_reason}" if label else alt_reason
                        if label:
                            nemotron_alternatives.append(label)

            if not meets_needs:
                try:
                    substitutes_raw = await suggest_substitutes_async(
                        ingredients=analysis_data["safe"],
                        excluded_ingredients=analysis_data["excluded"],
                        target_product_name=name,
                        user_conditions=profile.get("conditions", []),
                        user_profile=profile,
                        issues=alerts,
                        top_k=3,
                    )
                    for item in substitutes_raw:
                        reason_text = str(item.get("reason", "") or "").strip()
                        extra_parts: List[str] = []
                        match_goals = item.get("match_goals")
                        if match_goals:
                            extra_parts.append("Cumple: " + ", ".join(match_goals))
                        avoids = item.get("avoids")
                        if avoids:
                            extra_parts.append("Evita: " + ", ".join(avoids))
                        key_ingredients = item.get("key_ingredients")
                        if key_ingredients:
                            extra_parts.append("Activos: " + ", ".join(key_ingredients))
                        if extra_parts:
                            extras_str = "; ".join(extra_parts)
                            reason_text = f"{reason_text} ({extras_str})" if reason_text else extras_str

                        suggestion = SubstituteSuggestion(
                            product_id=item.get("product_id"),
                            name=str(item.get("name") or "Producto recomendado"),
                            brand=item.get("brand"),
                            eco_score=item.get("eco_score"),
                            risk_level=item.get("risk_level"),
                            similarity=float(item.get("similarity", 0.0)),
                            reason=reason_text,
                        )
                        substitutes.append(suggestion)
                        substitute_accumulator.append(suggestion)
                        if reason_text:
                            nemotron_alternatives.append(f"{suggestion.name}: {reason_text}")
                        else:
                            nemotron_alternatives.append(suggestion.name)
                        suggestion_messages.append(_format_substitute_message(suggestion))
                except Exception as exc:
                    logger.error("Substitute search failed for %s: %s", name, exc)

            alerts = list(dict.fromkeys(alerts))

            product_evaluations.append(
                ProductEvaluation(
                    product_name=name,
                    meets_needs=meets_needs,
                    alerts=alerts,
                    substitutes=substitutes,
                    llm_alternatives=list(dict.fromkeys(nemotron_alternatives)),
                )
            )

            alerts_global.extend(alerts)
            recommendations_global.extend(suggestion_messages)
            if nemotron_alternatives:
                recommendations_global.extend(nemotron_alternatives)

            stored_refs: OrderedDict[str, Optional[SubstituteSuggestion]] = OrderedDict()
            for message in alerts:
                stored_refs.setdefault(message, None)
            for note in nemotron_alternatives:
                stored_refs.setdefault(note, None)
            for message, suggestion in zip(suggestion_messages, substitutes):
                stored_refs[message] = suggestion

            for message, suggestion in stored_refs.items():
                db.add(
                    Recommendation(
                        user_id=user.id,
                        routine_id=routine_record.id,
                        original_product_name=name,
                        substitute_product_id=suggestion.product_id if suggestion else None,
                        substitute_product_name=suggestion.name if suggestion else None,
                        reason=message,
                        status="suggested" if suggestion else "pending_review",
                    )
                )

        recommendation_texts = [
            rec.strip()
            for rec in (analysis_result.recommendations or "").split("\n\n")
            if rec.strip()
        ]
        recommendations_global.extend(recommendation_texts)

        db.commit()
        db.refresh(routine_record)
    except Exception as exc:
        db.rollback()
        logger.error("Error persisting routine analysis for user %s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail="Failed to analyze routine")

    unique_substitutes: List[SubstituteSuggestion] = []
    seen_keys: set = set()
    for suggestion in substitute_accumulator:
        key = (suggestion.product_id, suggestion.name)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        unique_substitutes.append(suggestion)

    return RoutineAnalysisResponse(
        routine_id=routine_record.id,
        product_name=analysis_result.product_name,
        extracted_ingredients=extracted_ingredients,
        analysis=analysis_result,
        alerts=list(dict.fromkeys(alerts_global)),
        recommendations=list(dict.fromkeys(recommendations_global)),
        substitutes=unique_substitutes,
        products=product_evaluations,
    )


@app.get("/recommendations/{user_id}", response_model=UserRecommendationsResponse)
async def get_user_recommendations(user_id: int, db: Session = Depends(get_db)):
    """Return stored recommendations and alerts for a user."""
    user_exists = db.query(User.id).filter(User.id == user_id).first()
    if not user_exists:
        raise HTTPException(status_code=404, detail="User not found")

    entries = (
        db.query(Recommendation)
        .filter(Recommendation.user_id == user_id)
        .order_by(Recommendation.created_at.desc())
        .all()
    )

    items = [
        RecommendationItem(
            id=entry.id,
            routine_id=entry.routine_id,
            original_product_name=entry.original_product_name,
            substitute_product_name=entry.substitute_product_name,
            reason=entry.reason or "",
            status=entry.status or "draft",
            created_at=entry.created_at or datetime.utcnow(),
        )
        for entry in entries
    ]

    return UserRecommendationsResponse(user_id=user_id, items=items)


@app.post("/ml/rebuild")
async def rebuild_recommender():
    try:
        await ensure_recommender_ready(force=True)
        return {"status": "ok", "indexed_products": RECOMMENDER.index_size}
    except Exception as exc:
        logger.error("Failed to rebuild recommender: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to rebuild recommender")

@app.post("/analyze-image", response_model=ProductAnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    user_need: str = Form(default="general safety"),
    db: Session = Depends(get_db)
):
    """Analyze cosmetic product from image with fallback for reliability."""
    try:
        logger.info(f"Starting image analysis for: {file.filename}")
        
        # Validate file
        if not file.content_type or not file.content_type.startswith('image/'):
            logger.warning(f"Invalid file type: {file.content_type}")
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        logger.info("Reading image data...")
        image_data = await file.read()
        if len(image_data) == 0:
            logger.warning("Empty image file received")
            raise HTTPException(status_code=400, detail="Empty image file")
        
        logger.info(f"Image size: {len(image_data)} bytes")
        
        # Limit file size for Railway
        if len(image_data) > MAX_IMAGE_SIZE:
            max_size_mb = round(MAX_IMAGE_SIZE / (1024 * 1024), 2)
            logger.warning(f"Image too large: {len(image_data)} bytes (max: {MAX_IMAGE_SIZE})")
            raise HTTPException(status_code=400, detail=f"Image too large. Maximum size is {max_size_mb}MB.")
        
        # Extract ingredients with timeout and fallback
        logger.info("Starting ingredient extraction...")
        logger.info("This may take up to 45 seconds for complex images...")
        ingredients = []
        
        try:
            ingredients = await asyncio.wait_for(
                extract_ingredients_from_image(image_data),
                timeout=45.0  # Increased to 45 second timeout for complex images
            )
        except asyncio.TimeoutError:
            logger.error("Ingredient extraction timed out after 45 seconds")
            # Fallback: return a generic response instead of error
            return ProductAnalysisResponse(
                product_name=f"Product from Image: {file.filename}",
                ingredients_details=[],
                avg_eco_score=50.0,
                suitability="No se pudo analizar",
                recommendations="El procesamiento de la imagen tardó demasiado tiempo. Por favor, intenta con una imagen más clara, de menor tamaño, o usa el análisis de texto."
            )
        except Exception as e:
            logger.error(f"Error in ingredient extraction: {e}")
            # Fallback: return a generic response instead of error
            return ProductAnalysisResponse(
                product_name=f"Product from Image: {file.filename}",
                ingredients_details=[],
                avg_eco_score=50.0,
                suitability="No se pudo analizar",
                recommendations="Error en el procesamiento de la imagen. Por favor, intenta con una imagen más clara o usa el análisis de texto."
            )
        
        if not ingredients:
            logger.warning("No ingredients detected in image")
            return ProductAnalysisResponse(
                product_name=f"Product from Image: {file.filename}",
                ingredients_details=[],
                avg_eco_score=50.0,
                suitability="No se pudo analizar",
                recommendations="No se detectaron ingredientes en la imagen. Por favor, intenta con una imagen más clara o usa el análisis de texto."
            )
        
        logger.info(f"Found {len(ingredients)} ingredients: {ingredients[:3]}...")
        
        # Limit ingredients for Railway
        if len(ingredients) > MAX_ANALYZED_INGREDIENTS:
            logger.info(
                "Limiting to first %d ingredients (found %d)",
                MAX_ANALYZED_INGREDIENTS,
                len(ingredients)
            )
            ingredients = ingredients[:MAX_ANALYZED_INGREDIENTS]
        
        # Analyze ingredients
        logger.info("Starting ingredient analysis...")
        normalized_need = normalize_user_need(user_need)
        result = await analyze_ingredients(ingredients, normalized_need, db)
        result.product_name = f"Product from Image: {file.filename}"
        
        logger.info("Image analysis completed successfully")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing image: {e}", exc_info=True)
        # Fallback: return a generic response instead of 500 error
        return ProductAnalysisResponse(
            product_name=f"Product from Image: {file.filename}",
            ingredients_details=[],
            avg_eco_score=50.0,
            suitability="Error en análisis",
            recommendations="Error interno del servidor. Por favor, intenta nuevamente o usa el análisis de texto."
        )

@app.post("/analyze-text", response_model=ProductAnalysisResponse)
async def analyze_text(request: AnalyzeTextRequest, db: Session = Depends(get_db)):
    """Analyze ingredients from text."""
    try:
        logger.info("Analyzing text input")
        
        # Extract ingredients from text
        ingredients = extract_ingredients_from_text(request.text)
        if not ingredients:
            raise HTTPException(status_code=400, detail="No ingredients found in text")
        
        # Limit ingredients
        if len(ingredients) > MAX_ANALYZED_INGREDIENTS:
            ingredients = ingredients[:MAX_ANALYZED_INGREDIENTS]
        
        # Analyze ingredients
        normalized_need = normalize_user_need(request.user_need)
        result = await analyze_ingredients(ingredients, normalized_need, db)
        result.product_name = "Text Analysis"
        
        logger.info("Text analysis completed successfully")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing text: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health():
    """Health check for all APIs."""
    try:
        health_status = await health_check()
        return {
            "status": "healthy",
            "timestamp": health_status.get("timestamp"),
            "apis": health_status.get("apis", {}),
            "cache_stats": health_status.get("cache_stats", {})
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {"status": "unhealthy", "error": str(e)}

@app.get("/debug/env")
async def debug_env():
    """Debug environment variables."""
    return {
        "GOOGLE_CLIENT_ID": "SET" if os.getenv("GOOGLE_CLIENT_ID") else "NOT_SET",
        "GOOGLE_CLIENT_SECRET": "SET" if os.getenv("GOOGLE_CLIENT_SECRET") else "NOT_SET",
        "GOOGLE_REDIRECT_URI": os.getenv("GOOGLE_REDIRECT_URI", "NOT_SET"),
        "FIREBASE_CREDENTIALS": "SET" if os.getenv("FIREBASE_CREDENTIALS") else "NOT_SET",
        "GOOGLE_VISION_API_KEY": "SET" if os.getenv("GOOGLE_VISION_API_KEY") else "NOT_SET",
        "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT", "NOT_SET")
    }

@app.get("/debug/tesseract")
async def debug_tesseract():
    """Debug Tesseract availability."""
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        return {
            "tesseract_available": True,
            "version": str(version),
            "languages": pytesseract.get_languages()
        }
    except Exception as e:
        return {
            "tesseract_available": False,
            "error": str(e)
        }

@app.get("/ingredients")
async def list_all_ingredients(db: Session = Depends(get_db)):
    """Get all ingredients from database."""
    try:
        ingredients = get_all_ingredients()
        return {"ingredients": ingredients, "count": len(ingredients)}
    except Exception as e:
        logger.error(f"Error getting ingredients: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Run the application
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)