# File: backend/app/models/price_data_fixed.py
# PriceData model that EXACTLY matches your database columns

from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class PriceData(Base):
    """
    Price data model - EXACTLY matching your actual database structure
    
    Based on your database inspection:
    - id (integer, not null)
    - crypto_id (integer, not null)
    - timestamp (timestamp with timezone, not null)
    - open_price (numeric, not null)
    - high_price (numeric, not null)  
    - low_price (numeric, not null)
    - close_price (numeric, not null)
    - volume (numeric, nullable)
    - market_cap (numeric, nullable)
    - created_at (timestamp with timezone, nullable)
    """
    
    __tablename__ = "price_data"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to cryptocurrency
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False, index=True)
    
    # Timestamp (UTC) - exactly as in your DB
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # OHLCV data - exactly as in your DB
    open_price = Column(Numeric(precision=20, scale=8), nullable=False)
    high_price = Column(Numeric(precision=20, scale=8), nullable=False)
    low_price = Column(Numeric(precision=20, scale=8), nullable=False)
    close_price = Column(Numeric(precision=20, scale=8), nullable=False)
    volume = Column(Numeric(precision=30, scale=8), nullable=True)  # nullable in your DB
    
    # Market data - exactly as in your DB
    market_cap = Column(Numeric(precision=30, scale=2), nullable=True)  # nullable in your DB
    
    # Timestamp - exactly as in your DB
    created_at = Column(DateTime(timezone=True), nullable=True)  # nullable in your DB
    
    # Relationships
    cryptocurrency = relationship("Cryptocurrency", back_populates="price_data")
    
    # Basic indexes for performance
    __table_args__ = (
        Index('idx_price_crypto_timestamp', 'crypto_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<PriceData(crypto_id={self.crypto_id}, timestamp={self.timestamp}, close_price={self.close_price})>"