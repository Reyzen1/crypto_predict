# File: backend/app/models/__init__.py
# Fixed models configuration to resolve SQLAlchemy relationship conflicts
# This file properly handles model relationships and imports

from app.core.database import Base

# Import User model first (it has the main relationships)
from app.models.user import User

# Create other models with proper relationships
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql.sqltypes import Numeric  
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

class Cryptocurrency(Base):
    """Cryptocurrency model with proper relationships"""
    __tablename__ = "cryptocurrencies"
    
    # Primary fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    coingecko_id = Column(String(50), nullable=True)
    binance_symbol = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships - back reference to related models
    price_data = relationship("PriceData", back_populates="cryptocurrency", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="cryptocurrency", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Cryptocurrency(id={self.id}, symbol='{self.symbol}', name='{self.name}')>"


class PriceData(Base):
    """Price data model with proper relationships"""
    __tablename__ = "price_data"
    
    # Primary fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    open_price = Column(Numeric(20, 8), nullable=False)
    high_price = Column(Numeric(20, 8), nullable=False)
    low_price = Column(Numeric(20, 8), nullable=False)
    close_price = Column(Numeric(20, 8), nullable=False)
    volume = Column(Numeric(20, 8), nullable=False)
    market_cap = Column(Numeric(20, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    cryptocurrency = relationship("Cryptocurrency", back_populates="price_data")

    def __repr__(self):
        return f"<PriceData(id={self.id}, crypto_id={self.crypto_id}, close_price={self.close_price})>"


class Prediction(Base):
    """Prediction model with proper relationships"""
    __tablename__ = "predictions"
    
    # Primary fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False)
    predicted_price = Column(Numeric(20, 8), nullable=False)
    confidence_score = Column(Numeric(5, 4), nullable=True)
    model_version = Column(String(50), nullable=True)
    prediction_date = Column(DateTime(timezone=True), nullable=True)  # Target prediction date
    features_used = Column(Text, nullable=True)  # JSON string of features used
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="predictions")
    cryptocurrency = relationship("Cryptocurrency", back_populates="predictions")

    def __repr__(self):
        return f"<Prediction(id={self.id}, user_id={self.user_id}, predicted_price={self.predicted_price})>"


# Export all models for proper import
__all__ = [
    "Base",
    "User", 
    "Cryptocurrency",
    "PriceData", 
    "Prediction"
]