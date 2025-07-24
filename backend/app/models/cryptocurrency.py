# File: backend/app/models/cryptocurrency.py
# SQLAlchemy model for cryptocurrency data

from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, Text, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Cryptocurrency(Base):
    """
    Cryptocurrency model for storing crypto information
    
    This model stores basic information about cryptocurrencies
    including symbols, names, and API identifiers for external services.
    """
    
    __tablename__ = "cryptocurrencies"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic cryptocurrency information
    symbol = Column(String(10), unique=True, index=True, nullable=False)  # BTC, ETH, etc.
    name = Column(String(100), nullable=False)                            # Bitcoin, Ethereum
    coingecko_id = Column(String(50), unique=True, index=True)           # bitcoin, ethereum
    
    # Market information
    market_cap_rank = Column(Integer, nullable=True)                      # Market cap ranking
    current_price = Column(Numeric(precision=20, scale=8), nullable=True) # Current price in USD
    market_cap = Column(Numeric(precision=30, scale=2), nullable=True)    # Market capitalization
    total_volume = Column(Numeric(precision=30, scale=2), nullable=True)  # 24h trading volume
    
    # Supply information
    circulating_supply = Column(Numeric(precision=30, scale=2), nullable=True)
    total_supply = Column(Numeric(precision=30, scale=2), nullable=True)
    max_supply = Column(Numeric(precision=30, scale=2), nullable=True)
    
    # Additional metadata
    description = Column(Text, nullable=True)                             # Crypto description
    website_url = Column(String(255), nullable=True)                     # Official website
    blockchain_site = Column(String(255), nullable=True)                 # Blockchain explorer
    
    # Status flags
    is_active = Column(Boolean, default=True, nullable=False)             # Is actively tracked
    is_supported = Column(Boolean, default=True, nullable=False)          # Is supported for predictions
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_data_update = Column(DateTime(timezone=True), nullable=True)     # Last price data update
    
    # Relationships
    price_data = relationship("PriceData", back_populates="cryptocurrency", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="cryptocurrency", cascade="all, delete-orphan")
    
    # Database indexes for performance
    __table_args__ = (
        Index('idx_crypto_symbol_active', 'symbol', 'is_active'),
        Index('idx_crypto_rank', 'market_cap_rank'),
        Index('idx_crypto_updated', 'updated_at'),
    )
    
    def __repr__(self):
        return f"<Cryptocurrency(symbol='{self.symbol}', name='{self.name}')>"
    
    @property
    def display_name(self) -> str:
        """Return formatted display name"""
        return f"{self.name} ({self.symbol})"
    
    @property
    def is_price_data_stale(self) -> bool:
        """Check if price data is older than 1 hour"""
        if not self.last_data_update:
            return True
        
        from datetime import datetime, timedelta
        return (datetime.utcnow() - self.last_data_update) > timedelta(hours=1)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'name': self.name,
            'coingecko_id': self.coingecko_id,
            'current_price': float(self.current_price) if self.current_price else None,
            'market_cap': float(self.market_cap) if self.market_cap else None,
            'market_cap_rank': self.market_cap_rank,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }