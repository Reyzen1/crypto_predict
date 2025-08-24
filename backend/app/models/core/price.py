# File: backend\app\models\core\price.py
# SQLAlchemy model for price data

from sqlalchemy import Column, Integer, DateTime, DECIMAL, ForeignKey, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import GIN

from app.core.database import Base

class PriceData(Base):
    """
    Historical price data with technical indicators
    Enhanced from Phase 1 with technical indicators support
    """
    __tablename__ = "price_data"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Crypto reference
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False, index=True)
    
    # OHLCV data
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    open_price = Column(DECIMAL(20, 8), nullable=False)
    high_price = Column(DECIMAL(20, 8), nullable=False)
    low_price = Column(DECIMAL(20, 8), nullable=False)
    close_price = Column(DECIMAL(20, 8), nullable=False)
    volume = Column(DECIMAL(30, 8))
    market_cap = Column(DECIMAL(30, 2))
    
    # Technical indicators (Phase 2 enhancement)
    technical_indicators = Column(JSON, default={})
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    cryptocurrency = relationship("Cryptocurrency", back_populates="price_data")
    
    def __repr__(self):
        return f"<PriceData(id={self.id}, crypto_id={self.crypto_id}, timestamp={self.timestamp})>"

# Performance indexes matching database
Index('idx_price_data_timestamp_desc', PriceData.timestamp.desc())
Index('idx_price_data_crypto_timestamp_desc', PriceData.crypto_id, PriceData.timestamp.desc())
Index('idx_price_data_volume', PriceData.volume.desc(), PriceData.timestamp.desc())
Index('idx_price_data_technical', PriceData.technical_indicators, postgresql_using='gin')
