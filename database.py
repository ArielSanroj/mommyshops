from sqlalchemy import create_engine, Column, Integer, String, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
import json
import httpx
from dotenv import load_dotenv
from typing import Dict, Optional

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo de Ingredientes
class Ingredient(Base):
    __tablename__ = "ingredients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    eco_score = Column(Float)  # 0-100 based on EWG or average
    risk_level = Column(String)  # e.g., "seguro", "cancerígeno"
    benefits = Column(Text)  # e.g., "Hidrata la piel"
    risks_detailed = Column(Text)  # e.g., "Puede causar irritación en dosis altas"
    sources = Column(String)  # e.g., "FDA, EWG, PubChem, IARC, INVIMA, COSING"

def get_db():
    """Get database session with proper error handling."""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        print(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

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

# Crear tablas
Base.metadata.create_all(bind=engine)