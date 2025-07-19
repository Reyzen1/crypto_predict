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

    # Relationships - One user can have many predictions and portfolios
    predictions = relationship("Prediction", back_populates="user", cascade="all, delete-orphan")
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"


class Cryptocurrency(Base):
    """Cryptocurrency model for supported coins"""
    __tablename__ = "cryptocurrencies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    coingecko_id = Column(String(50), nullable=True)  # For CoinGecko API integration
    binance_symbol = Column(String(20), nullable=True)  # For Binance API integration
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships - One crypto can have many price data, predictions, and portfolio entries
    price_data = relationship("PriceData", back_populates="cryptocurrency", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="cryptocurrency", cascade="all, delete-orphan")
    portfolios = relationship("Portfolio", back_populates="cryptocurrency", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Cryptocurrency(id={self.id}, symbol='{self.symbol}', name='{self.name}')>"


class PriceData(Base):
    """Price data model for historical cryptocurrency prices"""
    __tablename__ = "price_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    open_price = Column(Numeric(20, 8), nullable=False)  # Opening price
    high_price = Column(Numeric(20, 8), nullable=False)  # Highest price
    low_price = Column(Numeric(20, 8), nullable=False)   # Lowest price
    close_price = Column(Numeric(20, 8), nullable=False) # Closing price
    volume = Column(Numeric(30, 8), nullable=True)       # Trading volume
    market_cap = Column(Numeric(30, 2), nullable=True)   # Market capitalization
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    cryptocurrency = relationship("Cryptocurrency", back_populates="price_data")

    # Indexes for performance optimization
    __table_args__ = (
        Index('idx_price_data_crypto_timestamp', 'crypto_id', 'timestamp'),
        Index('idx_price_data_timestamp', 'timestamp'),
    )

    def __repr__(self):
        return f"<PriceData(crypto_id={self.crypto_id}, timestamp='{self.timestamp}', close=${self.close_price})>"


class Prediction(Base):
    """Prediction model for ML model predictions"""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False)
    model_name = Column(String(50), nullable=False)        # Name of ML model used
    predicted_price = Column(Numeric(20, 8), nullable=False)
    confidence_score = Column(Numeric(5, 4), nullable=True) # Confidence percentage (0-1)
    target_date = Column(DateTime(timezone=True), nullable=False) # When prediction is for
    features_used = Column(Text, nullable=True)            # JSON string of features used
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="predictions")
    cryptocurrency = relationship("Cryptocurrency", back_populates="predictions")

    # Indexes for performance optimization
    __table_args__ = (
        Index('idx_predictions_user_crypto', 'user_id', 'crypto_id'),
        Index('idx_predictions_target_date', 'target_date'),
        Index('idx_predictions_created_at', 'created_at'),
        Index('idx_predictions_model_name', 'model_name'),
    )

    def __repr__(self):
        return f"<Prediction(user_id={self.user_id}, crypto_id={self.crypto_id}, price=${self.predicted_price})>"


class Portfolio(Base):
    """Portfolio model for user cryptocurrency holdings"""
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False)
    quantity = Column(Numeric(20, 8), nullable=False)       # Amount of crypto held
    average_buy_price = Column(Numeric(20, 8), nullable=True) # Average purchase price
    total_invested = Column(Numeric(20, 2), nullable=True)   # Total amount invested
    notes = Column(Text, nullable=True)                      # User notes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="portfolios")
    cryptocurrency = relationship("Cryptocurrency", back_populates="portfolios")

    # Unique constraint - One portfolio entry per user per crypto
    __table_args__ = (
        Index('idx_portfolios_user_crypto', 'user_id', 'crypto_id', unique=True),
    )

    def __repr__(self):
        return f"<Portfolio(user_id={self.user_id}, crypto_id={self.crypto_id}, quantity={self.quantity})>"


# Export all models for easy importing
__all__ = [
    "User",
    "Cryptocurrency", 
    "PriceData",
    "Prediction",
    "Portfolio"
]
