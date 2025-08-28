# File: backend\app\models\core\crypto.py
# SQLAlchemy model for crypto data

from sqlalchemy import Column, Integer, String, Boolean, DateTime, DECIMAL, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base
from sqlalchemy import Text

class Cryptocurrency(Base):
    """
    Cryptocurrency master data
    Enhanced from Phase 1 with sector mapping and watchlist tier support
    """
    __tablename__ = "cryptocurrencies"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic identification
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    coingecko_id = Column(String(50), unique=True, index=True)
    
    # Market data
    market_cap_rank = Column(Integer, index=True)
    current_price = Column(DECIMAL(20, 8))
    market_cap = Column(DECIMAL(30, 2))
    total_volume = Column(DECIMAL(30, 2))
    circulating_supply = Column(DECIMAL(30, 2))
    total_supply = Column(DECIMAL(30, 2))
    max_supply = Column(DECIMAL(30, 2))
    
    # Metadata
    description = Column(Text)
    website_url = Column(String(255))
    blockchain_site = Column(String(255))
    
    # Phase 2 enhancements
    sector_id = Column(Integer, ForeignKey("crypto_sectors.id"), index=True)
    watchlist_tier = Column(String(10), nullable=False, default='none', index=True)  # tier1, tier2, none
    
    # Status flags
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    is_supported = Column(Boolean, nullable=False, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_data_update = Column(DateTime(timezone=True), index=True)
    
    # Relationships
    price_data = relationship("PriceData", back_populates="cryptocurrency", lazy="dynamic")
    predictions = relationship("Prediction", back_populates="cryptocurrency", lazy="dynamic")
    sector = relationship("CryptoSector", back_populates="cryptocurrencies")
    sector_mappings = relationship("CryptoSectorMapping", back_populates="cryptocurrency")
    watchlist_items = relationship("WatchlistItem", back_populates="cryptocurrency")
    ai_suggestions = relationship("AISuggestion", back_populates="cryptocurrency")
    trading_signals = relationship("TradingSignal", back_populates="cryptocurrency")
    
    def __repr__(self):
        return f"<Cryptocurrency(id={self.id}, symbol={self.symbol}, name={self.name})>"

# Performance indexes matching database
Index('idx_cryptocurrencies_sector', Cryptocurrency.sector_id, Cryptocurrency.is_active)
Index('idx_cryptocurrencies_tier', Cryptocurrency.watchlist_tier, Cryptocurrency.is_active)
Index('idx_cryptocurrencies_market_cap', Cryptocurrency.market_cap.desc())
Index('idx_cryptocurrencies_volume', Cryptocurrency.total_volume.desc())
Index('idx_cryptocurrencies_price_change', Cryptocurrency.current_price, Cryptocurrency.updated_at.desc())
