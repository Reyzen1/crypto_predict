# File: backend/app/models/price_data.py
# SQLAlchemy model for historical price data storage

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class PriceData(Base):
    """
    Price data model for storing historical cryptocurrency prices
    
    This model stores OHLCV (Open, High, Low, Close, Volume) data
    for cryptocurrencies with proper indexing for time-series queries.
    Designed for efficient ML feature extraction and analysis.
    """
    
    __tablename__ = "price_data"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to cryptocurrency
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False, index=True)
    
    # Timestamp (UTC)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # OHLCV data (Open, High, Low, Close, Volume)
    open_price = Column(Numeric(precision=20, scale=8), nullable=False)    # Opening price
    high_price = Column(Numeric(precision=20, scale=8), nullable=False)    # Highest price
    low_price = Column(Numeric(precision=20, scale=8), nullable=False)     # Lowest price
    close_price = Column(Numeric(precision=20, scale=8), nullable=False)   # Closing price
    volume = Column(Numeric(precision=30, scale=8), nullable=False)        # Trading volume
    
    # Additional market data
    market_cap = Column(Numeric(precision=30, scale=2), nullable=True)     # Market cap at time
    total_volume = Column(Numeric(precision=30, scale=2), nullable=True)   # Total volume
    
    # Technical indicators (computed and stored for efficiency)
    sma_20 = Column(Numeric(precision=20, scale=8), nullable=True)         # 20-day Simple Moving Average
    sma_50 = Column(Numeric(precision=20, scale=8), nullable=True)         # 50-day Simple Moving Average
    ema_12 = Column(Numeric(precision=20, scale=8), nullable=True)         # 12-day Exponential Moving Average
    ema_26 = Column(Numeric(precision=20, scale=8), nullable=True)         # 26-day Exponential Moving Average
    rsi = Column(Numeric(precision=5, scale=2), nullable=True)             # Relative Strength Index
    macd = Column(Numeric(precision=20, scale=8), nullable=True)           # MACD line
    macd_signal = Column(Numeric(precision=20, scale=8), nullable=True)    # MACD signal line
    bollinger_upper = Column(Numeric(precision=20, scale=8), nullable=True) # Bollinger upper band
    bollinger_lower = Column(Numeric(precision=20, scale=8), nullable=True) # Bollinger lower band
    
    # Price change metrics
    price_change_1h = Column(Numeric(precision=10, scale=4), nullable=True)  # 1-hour price change %
    price_change_24h = Column(Numeric(precision=10, scale=4), nullable=True) # 24-hour price change %
    price_change_7d = Column(Numeric(precision=10, scale=4), nullable=True)  # 7-day price change %
    
    # Data source and quality
    data_source = Column(String(50), nullable=False, default="coingecko")  # Data source identifier
    data_interval = Column(String(10), nullable=False, default="1h")       # Data interval (1h, 4h, 1d)
    is_validated = Column(Boolean, default=True, nullable=False)           # Data quality flag
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    cryptocurrency = relationship("Cryptocurrency", back_populates="price_data")
    
    # Database indexes for time-series performance
    __table_args__ = (
        # Composite index for efficient time-range queries
        Index('idx_price_crypto_timestamp', 'crypto_id', 'timestamp'),
        # Index for interval-based queries
        Index('idx_price_interval', 'data_interval', 'timestamp'),
        # Index for data source queries
        Index('idx_price_source', 'data_source', 'created_at'),
        # Unique constraint to prevent duplicate data points
        Index('idx_price_unique', 'crypto_id', 'timestamp', 'data_interval', unique=True),
    )
    
    def __repr__(self):
        return f"<PriceData(crypto_id={self.crypto_id}, timestamp='{self.timestamp}', close={self.close_price})>"
    
    @property
    def price_range(self) -> float:
        """Calculate price range (high - low)"""
        return float(self.high_price - self.low_price)
    
    @property
    def price_change(self) -> float:
        """Calculate price change (close - open)"""
        return float(self.close_price - self.open_price)
    
    @property
    def price_change_percent(self) -> float:
        """Calculate price change percentage"""
        if self.open_price == 0:
            return 0.0
        return float((self.close_price - self.open_price) / self.open_price * 100)
    
    @property
    def typical_price(self) -> float:
        """Calculate typical price (H+L+C)/3"""
        return float((self.high_price + self.low_price + self.close_price) / 3)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'crypto_id': self.crypto_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'open_price': float(self.open_price),
            'high_price': float(self.high_price),
            'low_price': float(self.low_price),
            'close_price': float(self.close_price),
            'volume': float(self.volume),
            'price_change_24h': float(self.price_change_24h) if self.price_change_24h else None,
            'data_source': self.data_source,
            'data_interval': self.data_interval
        }
    
    def to_ohlcv(self) -> tuple:
        """Return OHLCV tuple for ML processing"""
        return (
            float(self.open_price),
            float(self.high_price),
            float(self.low_price),
            float(self.close_price),
            float(self.volume)
        )