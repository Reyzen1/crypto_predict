# File: ./backend/app/models/__init__.py
# Database models for CryptoPredict MVP - Integer ID version

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.sql.sqltypes import Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """User model for authentication and user management"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    predictions = relationship("Prediction", back_populates="user")
    portfolios = relationship("Portfolio", back_populates="user")


class Cryptocurrency(Base):
    """Cryptocurrency model for supported coins"""
    __tablename__ = "cryptocurrencies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    coingecko_id = Column(String(50), nullable=True)
    binance_symbol = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    price_data = relationship("PriceData", back_populates="cryptocurrency")
    predictions = relationship("Prediction", back_populates="cryptocurrency")
    portfolios = relationship("Portfolio", back_populates="cryptocurrency")


class PriceData(Base):
    """Price data model for historical cryptocurrency prices"""
    __tablename__ = "price_data"

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

    # Indexes for performance
    __table_args__ = (
        Index('idx_price_data_crypto_timestamp', 'crypto_id', 'timestamp'),
        Index('idx_price_data_timestamp', 'timestamp'),
    )


class Prediction(Base):
    """Predictions model for ML predictions"""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False)
    predicted_price = Column(Numeric(20, 8), nullable=False)
    confidence_score = Column(Numeric(5, 4), nullable=True)
    model_version = Column(String(50), nullable=True)
    prediction_horizon = Column(Integer, nullable=True)
    prediction_date = Column(DateTime(timezone=True), server_default=func.now())
    target_date = Column(DateTime(timezone=True), nullable=False)
    actual_price = Column(Numeric(20, 8), nullable=True)
    is_accurate = Column(Boolean, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="predictions")
    cryptocurrency = relationship("Cryptocurrency", back_populates="predictions")

    # Indexes for performance
    __table_args__ = (
        Index('idx_predictions_user_crypto', 'user_id', 'crypto_id'),
        Index('idx_predictions_target_date', 'target_date'),
        Index('idx_predictions_created_at', 'created_at'),
    )


class Portfolio(Base):
    """Portfolio model for user cryptocurrency holdings"""
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False)
    quantity = Column(Numeric(20, 8), nullable=False)
    average_buy_price = Column(Numeric(20, 8), nullable=True)
    total_invested = Column(Numeric(20, 2), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="portfolios")
    cryptocurrency = relationship("Cryptocurrency", back_populates="portfolios")

    # Unique constraint
    __table_args__ = (
        Index('idx_portfolios_user_crypto', 'user_id', 'crypto_id', unique=True),
    )


# Export models
__all__ = [
    "User",
    "Cryptocurrency", 
    "PriceData",
    "Prediction",
    "Portfolio"
]
