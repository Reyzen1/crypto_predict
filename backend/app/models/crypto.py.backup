# File: ./backend/app/models/crypto.py
# Cryptocurrency and price data models for CryptoPredict MVP

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Cryptocurrency(Base):
    """Cryptocurrency model for storing coin information"""
    
    __tablename__ = "cryptocurrencies"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Cryptocurrency identifiers
    symbol = Column(String(20), unique=True, index=True, nullable=False)  # BTC, ETH, etc.
    name = Column(String(100), nullable=False)  # Bitcoin, Ethereum, etc.
    coingecko_id = Column(String(50), unique=True, index=True, nullable=True)  # bitcoin, ethereum
    
    # Cryptocurrency information
    description = Column(Text, nullable=True)
    website = Column(String(255), nullable=True)
    logo_url = Column(String(500), nullable=True)
    
    # Market information
    market_cap_rank = Column(Integer, nullable=True)
    max_supply = Column(Float, nullable=True)
    circulating_supply = Column(Float, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_prediction_enabled = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    price_data = relationship("PriceData", back_populates="cryptocurrency")
    predictions = relationship("Prediction", back_populates="cryptocurrency")
    
    def __repr__(self):
        return f"<Cryptocurrency(symbol='{self.symbol}', name='{self.name}')>"


class PriceData(Base):
    """Price data model for storing historical and real-time cryptocurrency prices"""
    
    __tablename__ = "price_data"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to cryptocurrency
    cryptocurrency_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False)
    
    # Price data (OHLCV format)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    
    # Additional market data
    market_cap = Column(Float, nullable=True)
    price_change_24h = Column(Float, nullable=True)
    price_change_percentage_24h = Column(Float, nullable=True)
    volume_24h = Column(Float, nullable=True)
    
    # Data source information
    data_source = Column(String(50), nullable=False)  # coingecko, binance, etc.
    timeframe = Column(String(10), nullable=False)  # 1m, 5m, 1h, 1d, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    cryptocurrency = relationship("Cryptocurrency", back_populates="price_data")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_crypto_timestamp', 'cryptocurrency_id', 'timestamp'),
        Index('idx_crypto_timeframe', 'cryptocurrency_id', 'timeframe'),
        Index('idx_timestamp', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<PriceData(crypto_id={self.cryptocurrency_id}, timestamp='{self.timestamp}', close={self.close_price})>"