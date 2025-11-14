# backend/app/models/asset/price_data.py
# Price data model - OHLCV and technical indicators

from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, Boolean, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from ..base import BaseModel, TimestampMixin
from ..mixins import ValidationMixin
from ..enums import TimeframeEnum


class PriceData(BaseModel, TimestampMixin, ValidationMixin):
    """
    Price data model for OHLCV data and technical indicators
    
    This is a high-volume table that will be partitioned by candle_time
    Uses TimestampMixin for tracking data updates
    """
    __tablename__ = 'price_data'
    
    # Asset and timeframe
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)
    
    # OHLCV Data
    open_price = Column(Numeric(20,8), nullable=False)
    high_price = Column(Numeric(20,8), nullable=False)
    low_price = Column(Numeric(20,8), nullable=False)
    close_price = Column(Numeric(20,8), nullable=False)
    volume = Column(Numeric(30,2), nullable=False, default=0)
    
    # Additional Market Data
    market_cap = Column(Numeric(30,2), nullable=True)
    trade_count = Column(Integer, nullable=True)
    vwap = Column(Numeric(20,8), nullable=True)
    
    # Technical Indicators (computed asynchronously)
    technical_indicators = Column(JSON, nullable=True)
    
    # Timing
    # Use timezone-aware timestamps (Postgres timestamptz) so datetimes are stored as
    # absolute instants and returned consistently in UTC when the session timezone is UTC.
    candle_time = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Relationships
    asset = relationship("Asset", back_populates="price_data")
    
    # Constraints and Indexes
    __table_args__ = (
        # Unique constraints
        UniqueConstraint('asset_id', 'timeframe', 'candle_time', name='unique_asset_timeframe_candle'),
        
        # Check constraints
        CheckConstraint('low_price <= open_price AND low_price <= close_price AND high_price >= open_price AND high_price >= close_price', name='chk_ohlc_logic'),
        CheckConstraint('open_price > 0 AND high_price > 0 AND low_price > 0 AND close_price > 0', name='chk_prices_positive'),
        CheckConstraint('volume >= 0', name='chk_volume_non_negative'),
        CheckConstraint('trade_count IS NULL OR trade_count >= 0', name='chk_trade_count_positive'),
        CheckConstraint("timeframe IN ('1m', '5m', '15m', '1h', '4h', '1d', '1w', '1M')", name='chk_timeframe_valid'),
        
        # Performance indexes for high-volume time series data
        Index('idx_price_data_asset_id', 'asset_id'),
        Index('idx_price_data_timeframe', 'timeframe'),
        Index('idx_price_data_candle_time', 'candle_time'),
        Index('idx_price_data_created_at', 'created_at'),
        Index('idx_price_data_validated', 'is_validated'),
        
        # Composite indexes for common queries
        Index('idx_price_data_asset_timeframe', 'asset_id', 'timeframe'),
        Index('idx_price_data_asset_time', 'asset_id', 'candle_time'),
        Index('idx_price_data_timeframe_time', 'timeframe', 'candle_time'),
        Index('idx_price_data_asset_tf_time', 'asset_id', 'timeframe', 'candle_time'),
        
        # Price-based indexes for analytics
        Index('idx_price_data_close_price', 'close_price'),
        Index('idx_price_data_volume', 'volume'),
        Index('idx_price_data_asset_close', 'asset_id', 'close_price'),
        
        # Time-range partitioning support (for future partitioning)
        Index('idx_price_data_time_range_1d', 'candle_time', postgresql_where="timeframe = '1d'"),
        Index('idx_price_data_time_range_1h', 'candle_time', postgresql_where="timeframe = '1h'"),
    )
    
    def __repr__(self):
        return f"<PriceData(id={self.id}, asset_id={self.asset_id}, timeframe='{self.timeframe}', time={self.candle_time})>"
    
    @property
    def price_change(self):
        """Calculate price change (absolute)"""
        return self.close_price - self.open_price
    
    @property
    def price_change_pct(self):
        """Calculate price change percentage"""
        if self.open_price and self.open_price > 0:
            return ((self.close_price - self.open_price) / self.open_price) * 100
        return 0
    
    @property
    def is_green_candle(self):
        """Check if candle is green (close > open)"""
        return self.close_price > self.open_price
    
    @property
    def is_red_candle(self):
        """Check if candle is red (close < open)"""
        return self.close_price < self.open_price
    
    @property
    def is_doji(self):
        """Check if candle is doji (open ≈ close)"""
        if self.open_price and self.open_price > 0:
            change_pct = abs(self.price_change_pct)
            return change_pct < 0.1  # Less than 0.1% change
        return False
    
    @property
    def body_size(self):
        """Calculate candle body size (absolute difference between open and close)"""
        return abs(self.close_price - self.open_price)
    
    @property
    def upper_shadow(self):
        """Calculate upper shadow length"""
        return self.high_price - max(self.open_price, self.close_price)
    
    @property
    def lower_shadow(self):
        """Calculate lower shadow length"""
        return min(self.open_price, self.close_price) - self.low_price
    
    @property
    def total_range(self):
        """Calculate total price range (high - low)"""
        return self.high_price - self.low_price
    
    @property
    def body_to_range_ratio(self):
        """Calculate body size to total range ratio"""
        if self.total_range and self.total_range > 0:
            return (self.body_size / self.total_range) * 100
        return 0
    
    @property
    def timeframe_enum(self):
        """Get TimeframeEnum for this price data"""
        timeframe_map = {
            TimeframeEnum.ONE_MINUTE.value: TimeframeEnum.ONE_MINUTE,
            TimeframeEnum.FIVE_MINUTES.value: TimeframeEnum.FIVE_MINUTES,
            TimeframeEnum.FIFTEEN_MINUTES.value: TimeframeEnum.FIFTEEN_MINUTES,
            TimeframeEnum.ONE_HOUR.value: TimeframeEnum.ONE_HOUR,
            TimeframeEnum.FOUR_HOURS.value: TimeframeEnum.FOUR_HOURS,
            TimeframeEnum.ONE_DAY.value: TimeframeEnum.ONE_DAY,
            TimeframeEnum.ONE_WEEK.value: TimeframeEnum.ONE_WEEK,
            TimeframeEnum.ONE_MONTH.value: TimeframeEnum.ONE_MONTH,
        }
        return timeframe_map.get(self.timeframe)
    
    @property
    def candle_type(self):
        """Determine candle type based on OHLC pattern"""
        if self.is_doji:
            return "doji"
        elif self.is_green_candle:
            if self.body_to_range_ratio > 70:
                return "strong_bullish"
            elif self.upper_shadow > self.body_size * 2:
                return "shooting_star"
            else:
                return "bullish"
        else:  # Red candle
            if self.body_to_range_ratio > 70:
                return "strong_bearish"
            elif self.lower_shadow > self.body_size * 2:
                return "hammer"
            else:
                return "bearish"
    
    def set_technical_indicator(self, name: str, value):
        """Set a technical indicator value"""
        if not self.technical_indicators:
            self.technical_indicators = {}
        self.technical_indicators[name] = value
    
    def get_technical_indicator(self, name: str, default=None):
        """Get a technical indicator value"""
        if not self.technical_indicators:
            return default
        return self.technical_indicators.get(name, default)
    
    def validate_ohlc_data(self) -> bool:
        """Validate OHLC data integrity"""
        try:
            # Check basic OHLC logic
            if not (self.low_price <= self.open_price <= self.high_price):
                return False
            if not (self.low_price <= self.close_price <= self.high_price):
                return False
            
            # Check positive values
            if any(price <= 0 for price in [self.open_price, self.high_price, self.low_price, self.close_price]):
                return False
            
            # Check volume
            if self.volume < 0:
                return False
                
            return True
        except (TypeError, ValueError):
            return False
    
    @classmethod
    def get_latest_price(cls, session, asset_id: int, timeframe: str = "1d"):
        """Get the latest price data for an asset and timeframe"""
        return session.query(cls).filter(
            cls.asset_id == asset_id,
            cls.timeframe == timeframe
        ).order_by(cls.candle_time.desc()).first()
    
    @classmethod
    def get_price_range(cls, session, asset_id: int, timeframe: str, start_time, end_time):
        """Get price data within a time range"""
        return session.query(cls).filter(
            cls.asset_id == asset_id,
            cls.timeframe == timeframe,
            cls.candle_time.between(start_time, end_time)
        ).order_by(cls.candle_time.asc()).all()
    
    @classmethod
    def get_recent_candles(cls, session, asset_id: int, timeframe: str, limit: int = 100):
        """Get recent candles for technical analysis"""
        return session.query(cls).filter(
            cls.asset_id == asset_id,
            cls.timeframe == timeframe
        ).order_by(cls.candle_time.desc()).limit(limit).all()
    
    @classmethod
    def get_validated_data(cls, session, asset_id: int = None, timeframe: str = None):
        """Get validated price data"""
        query = session.query(cls).filter(cls.is_validated == True)
        
        if asset_id:
            query = query.filter(cls.asset_id == asset_id)
        if timeframe:
            query = query.filter(cls.timeframe == timeframe)
            
        return query.order_by(cls.candle_time.desc()).all()
    
    @classmethod
    def get_high_volume_candles(cls, session, asset_id: int, timeframe: str, min_volume: float):
        """Get candles with volume above threshold"""
        return session.query(cls).filter(
            cls.asset_id == asset_id,
            cls.timeframe == timeframe,
            cls.volume >= min_volume
        ).order_by(cls.candle_time.desc()).all()
    
    @classmethod
    def calculate_price_statistics(cls, session, asset_id: int, timeframe: str, days: int = 30):
        """Calculate price statistics for the last N days"""
        from datetime import datetime, timedelta, timezone
        
        start_time = datetime.now(timezone.utc) - timedelta(days=days)
        candles = cls.get_price_range(session, asset_id, timeframe, start_time, datetime.now(timezone.utc))
        
        if not candles:
            return None
            
        closes = [float(candle.close_price) for candle in candles]
        volumes = [float(candle.volume) for candle in candles]
        
        return {
            'count': len(candles),
            'high': max(closes),
            'low': min(closes),
            'avg_price': sum(closes) / len(closes),
            'total_volume': sum(volumes),
            'avg_volume': sum(volumes) / len(volumes),
            'first_price': closes[-1] if closes else None,
            'last_price': closes[0] if closes else None,
            'total_return': ((closes[0] - closes[-1]) / closes[-1] * 100) if len(closes) > 1 else 0
        }
    
    def to_dict(self, include_technical: bool = False) -> dict:
        """Convert price data to dictionary"""
        data = {
            'id': self.id,
            'asset_id': self.asset_id,
            'timeframe': self.timeframe,
            'candle_time': self.candle_time.isoformat() if self.candle_time else None,
            'open': float(self.open_price) if self.open_price else None,
            'high': float(self.high_price) if self.high_price else None,
            'low': float(self.low_price) if self.low_price else None,
            'close': float(self.close_price) if self.close_price else None,
            'volume': float(self.volume) if self.volume else 0,
            'price_change': float(self.price_change) if self.price_change else 0,
            'price_change_pct': self.price_change_pct,
            'is_green': self.is_green_candle,
            'candle_type': self.candle_type,
            'is_validated': self.is_validated,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_technical:
            data.update({
                'market_cap': float(self.market_cap) if self.market_cap else None,
                'trade_count': self.trade_count,
                'vwap': float(self.vwap) if self.vwap else None,
                'body_size': float(self.body_size) if self.body_size else 0,
                'upper_shadow': float(self.upper_shadow) if self.upper_shadow else 0,
                'lower_shadow': float(self.lower_shadow) if self.lower_shadow else 0,
                'total_range': float(self.total_range) if self.total_range else 0,
                'body_to_range_ratio': self.body_to_range_ratio,
                'technical_indicators': self.technical_indicators or {},
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            })
        
        return data