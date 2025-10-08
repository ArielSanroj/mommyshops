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
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from fastapi import HTTPException
import os
import json
import asyncio
import logging
from pathlib import Path
import httpx
from dotenv import load_dotenv
from typing import Any, Dict, Iterable, List, Optional, Tuple
from sqlalchemy.sql import func

load_dotenv()

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
LEXICON_PATH = Path(os.getenv("INGREDIENT_LEXICON_PATH", BASE_DIR / "cosmetic_ingredients_lexicon.txt"))
DEFAULT_SYNC_CONCURRENCY = max(1, int(os.getenv("INGREDIENT_SYNC_CONCURRENCY", "3")))
DEFAULT_SYNC_TIMEOUT = float(os.getenv("INGREDIENT_SYNC_TIMEOUT", "30"))
_LEXICON_CACHE: Optional[List[str]] = None

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
    print("⚠️  DATABASE_URL not found. Using SQLite fallback for development.")
    # Use SQLite as fallback for development
    DATABASE_URL = "sqlite:///./dev_sqlite.db"
else:
    # Check if it's a PostgreSQL URL and if we can connect
    if DATABASE_URL.startswith("postgresql://"):
        try:
            # Test the connection
            test_engine = create_engine(DATABASE_URL)
            with test_engine.connect() as conn:
                pass
            print("✅ PostgreSQL connection successful")
        except Exception as e:
            print(f"⚠️  PostgreSQL connection failed: {e}")
            print("🔄 Falling back to SQLite for development")
            DATABASE_URL = "sqlite:///./dev_sqlite.db"

print(f"Using DATABASE_URL: {DATABASE_URL[:50]}...")  # Log first 50 chars for debugging

try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    print("✅ Database connection configured successfully")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    print("⚠️  App will start but database features will be disabled")
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
    nemotron_summary = Column(JSON)
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="recommendations")
    routine = relationship("Routine")
    original_product = relationship("Product", foreign_keys=[original_product_id], back_populates="recommendations_source")
    substitute_product = relationship("Product", foreign_keys=[substitute_product_id], back_populates="recommendations_substitute")


class Ingredient(Base):
    __tablename__ = "ingredients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    eco_score = Column(Float)  # 0-100 based on EWG or average
    risk_level = Column(String)  # e.g., "seguro", "cancerígeno"
    benefits = Column(Text)  # e.g., "Hidrata la piel"
    risks_detailed = Column(Text)  # e.g., "Puede causar irritación en dosis altas"
    sources = Column(String)  # e.g., "FDA, EWG, PubChem, IARC, INVIMA, COSING"
    nemotron_enrichment = Column(JSON)

def get_db():
    """Get database session with proper error handling."""
    if SessionLocal is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        print(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

async def enrich_ingredients_with_nemotron(
    db: Session,
    ingredient_names: Optional[Iterable[str]] = None,
    user_conditions: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    """Enrich stored ingredients with Nemotron insights (risks, alternatives)."""
    from nemotron_integration import enrich_with_nemotron_async

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
        tasks.append(enrich_with_nemotron_async(ingredient.name, list(user_conditions or [])))

    enriched_payloads = await asyncio.gather(*tasks, return_exceptions=True)

    for ingredient, payload in zip(targets, enriched_payloads):
        if isinstance(payload, Exception):
            logger.error("Nemotron enrichment failed for %s: %s", ingredient.name, payload)
            results["errors"].append({"ingredient": ingredient.name, "error": str(payload)})
            continue

        if payload:
            ingredient.nemotron_enrichment = payload
            results["updated"] += 1

    db.commit()
    return results

def enrich_ingredients_with_nemotron_sync(
    db: Session,
    ingredient_names: Optional[Iterable[str]] = None,
    user_conditions: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    """Synchronous helper for scripts that enforces a fresh event loop."""
    return asyncio.run(
        enrich_ingredients_with_nemotron(db, ingredient_names=ingredient_names, user_conditions=user_conditions)
    )

# Import API functions from api_utils_production
from api_utils_production import fetch_ingredient_data

async def update_database(db: Session):
    """Update database with ingredient data using NVIDIA AI approach."""
    try:
        # Use NVIDIA AI approach for database updates
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
                    print(f"Successfully updated ingredient: {name}")
                except Exception as e:
                    print(f"Error updating {name}: {e}")
                    db.rollback()
                    continue
    except Exception as e:
        print(f"Error in update_database: {e}")

# Comprehensive local ingredient database
# Comprehensive local ingredient database
LOCAL_INGREDIENT_DATABASE = {
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

def get_all_ingredient_names() -> List[str]:
    """Get all ingredient names from the database for dynamic corrections."""
    try:
        with SessionLocal() as db:
            ingredients = db.query(Ingredient.name).all()
            return [ing.name for ing in ingredients]
    except Exception as e:
        logger.error(f"Error getting ingredient names: {e}")
        return []

def get_ingredient_data(ingredient_name: str) -> Optional[Dict]:
    """Get ingredient data from local database with fuzzy matching for garbled OCR text."""
    import logging
    logger = logging.getLogger(__name__)
    
    ingredient_lower = ingredient_name.lower().strip()
    
    # 1. Try exact match first
    if ingredient_lower in LOCAL_INGREDIENT_DATABASE:
        logger.info(f"Exact match found for: {ingredient_name}")
        return LOCAL_INGREDIENT_DATABASE[ingredient_lower]
    
    # 2. Fuzzy matching with fuzzywuzzy (mejor para texto garbled)
    try:
        from fuzzywuzzy import process
        
        # Buscar mejor match usando fuzzy matching
        matches = process.extractOne(ingredient_lower, LOCAL_INGREDIENT_DATABASE.keys())
        
        if matches and matches[1] > 75:  # Umbral de similitud optimizado para ingredientes
            logger.info(f"Fuzzy match found for '{ingredient_name}' -> '{matches[0]}' (similarity: {matches[1]}%)")
            return LOCAL_INGREDIENT_DATABASE[matches[0]]

        # Si no hay match con umbral optimizado, buscar con umbral más bajo
        if matches and matches[1] > 65:  # Umbral más bajo para casos difíciles
            logger.info(f"Weak fuzzy match found for '{ingredient_name}' -> '{matches[0]}' (similarity: {matches[1]}%)")
            return LOCAL_INGREDIENT_DATABASE[matches[0]]
            
    except ImportError:
        logger.warning("Fuzzywuzzy not available, using fallback matching")
    except Exception as e:
        logger.warning(f"Fuzzy matching failed: {e}")
    
    # 3. Fallback: Enhanced partial matching for garbled OCR text
    best_match = None
    best_score = 0
    
    for key, data in LOCAL_INGREDIENT_DATABASE.items():
        score = 0
        
        # Check if ingredient contains key or vice versa
        if key in ingredient_lower:
            score += 10  # High score for substring match
        elif ingredient_lower in key:
            score += 8   # Good score for reverse substring match
        
        # Check for word-by-word matching (important for garbled text)
        ingredient_words = ingredient_lower.split()
        key_words = key.split()
        
        # Count matching words
        matching_words = 0
        for word in ingredient_words:
            if len(word) > 2:  # Only consider words longer than 2 characters
                for key_word in key_words:
                    if word in key_word or key_word in word:
                        matching_words += 1
                        break
        
        if matching_words > 0:
            word_score = (matching_words / len(key_words)) * 15  # Up to 15 points for word matching
            score += word_score
        
        # Check for common cosmetic ingredient patterns
        cosmetic_patterns = {
            'acid': ['acid', 'acido'],
            'alcohol': ['alcohol', 'alcohol'],
            'oil': ['oil', 'aceite'],
            'extract': ['extract', 'extracto'],
            'palmitate': ['palmitate', 'palmitato'],
            'stearate': ['stearate', 'estearato'],
            'glycerin': ['glycerin', 'glicerina'],
            'paraben': ['paraben', 'parabeno'],
            'sulfate': ['sulfate', 'sulfato'],
            'oxide': ['oxide', 'oxido']
        }
        
        for pattern, variations in cosmetic_patterns.items():
            if pattern in key:
                for variation in variations:
                    if variation in ingredient_lower:
                        score += 5  # Bonus for cosmetic pattern match
        
        # Check for common variations and OCR errors
        variations = [
            ingredient_lower.replace(' ', ''),
            ingredient_lower.replace(' ', '-'),
            ingredient_lower.replace(' ', '_'),
            ingredient_lower.replace('(', '').replace(')', ''),
            ingredient_lower.replace('extract', ''),
            ingredient_lower.replace('oil', ''),
            ingredient_lower.replace('acid', ''),
            ingredient_lower.replace('alcohol', ''),
            # Common OCR character substitutions
            ingredient_lower.replace('0', 'o'),
            ingredient_lower.replace('1', 'l'),
            ingredient_lower.replace('5', 's'),
            ingredient_lower.replace('8', 'b'),
        ]
        
        for variation in variations:
            if variation in key or key in variation:
                score += 3  # Lower score for variation match
        
        # Update best match
        if score > best_score:
            best_score = score
            best_match = (key, data)
    
    # Return best match if score is above threshold
    if best_match and best_score >= 5:  # Minimum threshold for partial match
        logger.info(f"Fallback partial match found for '{ingredient_name}' -> '{best_match[0]}' (score: {best_score:.1f})")
        return best_match[1]
    
    logger.info(f"No match found for: {ingredient_name}")
    return None

def get_all_ingredients() -> Dict:
    """Get all ingredients from local database."""
    return LOCAL_INGREDIENT_DATABASE

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

    normalized_key = ingredient_name.strip().lower()
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
        normalized = (record.name or "").strip().lower()
        if not normalized:
            continue
        LOCAL_INGREDIENT_DATABASE[normalized] = {
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