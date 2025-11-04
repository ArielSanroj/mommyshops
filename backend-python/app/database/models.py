"""
SQLAlchemy models for MommyShops application
Consolidated from the main database.py file
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    ForeignKey,
    JSON,
    DateTime,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

# Create the declarative base
Base = declarative_base()


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
    face_shape = Column(String(64))
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
    custom_products = relationship("CustomProduct", back_populates="user", cascade="all, delete-orphan")

    @property
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.username == "admin" or self.email == "admin@mommyshops.com"


class Routine(Base):
    __tablename__ = "routines"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    products = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="routines")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    brand = Column(String(128))
    category = Column(String(128))
    ingredients = Column(JSON)  # List of ingredient names
    image_url = Column(String(512))
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CustomProduct(Base):
    __tablename__ = "custom_products"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    base_product_name = Column(String(255), nullable=False)
    safe_ingredients = Column(JSON)
    substitutions = Column(JSON)
    profile_snapshot = Column(JSON)
    labs_formula = Column(JSON)
    labs_summary = Column(JSON)
    labs_mockup = Column(JSON)
    price = Column(Float, default=0.0)
    status = Column(String(32), default="draft")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="custom_products")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    routine_id = Column(Integer, ForeignKey("routines.id", ondelete="SET NULL"), nullable=True)
    analysis_data = Column(JSON)
    recommendations = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="recommendations")


class Ingredient(Base):
    __tablename__ = "ingredients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    eco_score = Column(Float)  # 0-100 based on EWG or average
    risk_level = Column(String)  # e.g., "seguro", "cancerígeno"
    description = Column(Text)
    sources = Column(JSON)  # List of sources
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RecommendationFeedback(Base):
    __tablename__ = "recommendation_feedback"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id", ondelete="CASCADE"), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    feedback_type = Column(String(32))  # 'helpful', 'not_helpful', 'irrelevant'
    feedback_text = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
