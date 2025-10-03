# backend/app/models/asset/price_data_archive.py
# Price Data Archive Model - Long-term historical price storage with partitioning

from sqlalchemy import Column, String, Integer, Numeric, DateTime, Boolean, ForeignKey, CheckConstraint, Index, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from ..base import BaseModel, CreatedAtMixin
from ..mixins import DataQualityMixin, ValidationMixin
from ..enums import TimeframeEnum


class PriceDataArchive(BaseModel, CreatedAtMixin, DataQualityMixin, ValidationMixin):
    """
    Price Data Archive Model for long-term historical storage
    
    Features:
    - Compressed historical price data storage
    - Partitioning by year/month for performance
    - Data retention policies
    - Quality assessment and validation
    - Aggregated metrics for faster queries
    
    Uses CreatedAtMixin (only created_at) because archived data is immutable
    """
    __tablename__ = 'price_data_archive'
    
    # Foreign Keys
    asset_id = Column(
        Integer, 
        ForeignKey('assets.id', ondelete='CASCADE'), 
        nullable=False,
        comment="Reference to asset"
    )
    
    # Time and Timeframe
    timestamp = Column(
        DateTime(timezone=True), 
        nullable=False, 
        comment="Price data timestamp"
    )
    timeframe = Column(
        String(10), 
        nullable=False, 
        comment="Timeframe: '1m','5m','15m','1h','4h','1d','1w','1M'"
    )
    
    # OHLCV Data (Compressed for archive)
    open_price = Column(
        Numeric(20, 8), 
        nullable=False,
        comment="Opening price"
    )
    high_price = Column(
        Numeric(20, 8), 
        nullable=False,
        comment="Highest price in period"
    )
    low_price = Column(
        Numeric(20, 8), 
        nullable=False,
        comment="Lowest price in period"
    )
    close_price = Column(
        Numeric(20, 8), 
        nullable=False,
        comment="Closing price"
    )
    volume = Column(
        Numeric(30, 8), 
        nullable=True,
        comment="Trading volume in base currency"
    )
    
    # Volume Metrics
    volume_usd = Column(
        Numeric(30, 2), 
        nullable=True,
        comment="Trading volume in USD"
    )
    volume_quote = Column(
        Numeric(30, 8), 
        nullable=True,
        comment="Trading volume in quote currency"
    )
    
    # Market Metrics (Aggregated)
    market_cap_usd = Column(
        Numeric(30, 2), 
        nullable=True,
        comment="Market capitalization in USD"
    )
    price_change_percentage = Column(
        Numeric(10, 4), 
        nullable=True,
        comment="Price change percentage for the period"
    )
    
    # Statistical Metrics
    price_volatility = Column(
        Numeric(10, 6), 
        nullable=True,
        comment="Price volatility measure for the period"
    )
    trade_count = Column(
        Integer, 
        nullable=True,
        comment="Number of trades in the period"
    )
    
    # Archive Metadata
    archive_year = Column(
        Integer, 
        nullable=False,
        comment="Year for partitioning"
    )
    archive_month = Column(
        Integer, 
        nullable=False,
        comment="Month for partitioning (1-12)"
    )
    archive_date = Column(
        DateTime(timezone=True), 
        nullable=False,
        comment="Date when data was archived"
    )
    
    # Data Compression & Storage
    raw_data_hash = Column(
        String(64), 
        nullable=True,
        comment="SHA-256 hash of original raw data for integrity"
    )
    compression_ratio = Column(
        Numeric(6, 4), 
        nullable=True,
        comment="Data compression ratio achieved"
    )
    original_source = Column(
        String(50), 
        nullable=True,
        comment="Original data source before archiving"
    )
    
    # Extended Metadata
    extended_data = Column(
        JSONB, 
        nullable=True,
        comment="Additional archived metrics and metadata"
    )
    
    # Retention Policy
    retention_tier = Column(
        String(20), 
        nullable=False, 
        default='standard',
        comment="Retention tier: 'hot', 'warm', 'cold', 'frozen'"
    )
    expires_at = Column(
        DateTime(timezone=True), 
        nullable=True,
        comment="Data expiration date for retention policy"
    )
    
    # Data Quality & Validation
    anomaly_flags = Column(
        JSONB, 
        nullable=True,
        comment="Detected anomalies and quality issues"
    )
    
    # Relationships
    asset = relationship("Asset", back_populates="price_data_archive")
    
    # Constraints and Indexes
    __table_args__ = (
        # Unique constraints
        UniqueConstraint('asset_id', 'timestamp', 'timeframe', name='unique_archive_asset_time_timeframe'),
        
        # Check constraints
        CheckConstraint('open_price > 0', name='chk_archive_open_price_positive'),
        CheckConstraint('high_price > 0', name='chk_archive_high_price_positive'),
        CheckConstraint('low_price > 0', name='chk_archive_low_price_positive'),
        CheckConstraint('close_price > 0', name='chk_archive_close_price_positive'),
        CheckConstraint('high_price >= low_price', name='chk_archive_high_gte_low'),
        CheckConstraint('high_price >= open_price', name='chk_archive_high_gte_open'),
        CheckConstraint('high_price >= close_price', name='chk_archive_high_gte_close'),
        CheckConstraint('low_price <= open_price', name='chk_archive_low_lte_open'),
        CheckConstraint('low_price <= close_price', name='chk_archive_low_lte_close'),
        CheckConstraint('volume IS NULL OR volume >= 0', name='chk_archive_volume_positive'),
        CheckConstraint('volume_usd IS NULL OR volume_usd >= 0', name='chk_archive_volume_usd_positive'),
        CheckConstraint('trade_count IS NULL OR trade_count >= 0', name='chk_archive_trade_count_positive'),
        CheckConstraint('archive_month BETWEEN 1 AND 12', name='chk_archive_month_valid'),
        CheckConstraint('archive_year >= 2009', name='chk_archive_year_valid'),
        CheckConstraint("timeframe IN ('1m','5m','15m','1h','4h','1d','1w','1M')", name='chk_archive_timeframe_valid'),
        CheckConstraint("retention_tier IN ('hot','warm','cold','frozen')", name='chk_retention_tier_valid'),
        CheckConstraint('data_quality_score BETWEEN 0 AND 100', name='chk_archive_quality_score'),
        
        # Partitioning indexes (for PostgreSQL partitioning)
        Index('idx_archive_partition', 'archive_year', 'archive_month'),
        Index('idx_archive_timestamp', 'timestamp'),
        Index('idx_archive_asset_time', 'asset_id', 'timestamp'),
        Index('idx_archive_timeframe', 'timeframe'),
        Index('idx_archive_asset_timeframe', 'asset_id', 'timeframe'),
        Index('idx_archive_retention', 'retention_tier', 'expires_at'),
        Index('idx_archive_quality', 'data_quality_score'),
        Index('idx_archive_created_at', 'created_at'),
        Index('idx_archive_validated', 'is_validated'),
        Index('idx_archive_source', 'original_source'),
        Index('idx_archive_hash', 'raw_data_hash'),
        Index('idx_archive_year_month_asset', 'archive_year', 'archive_month', 'asset_id'),
        
        # PostgreSQL specific settings for partitioning
        {
            'postgresql_partition_by': 'RANGE (archive_year, archive_month)',
            'postgresql_inherits': 'price_data_archive_base'
        }
    )
    
    def __repr__(self):
        return f"<PriceDataArchive(asset_id={self.asset_id}, timestamp={self.timestamp}, timeframe={self.timeframe})>"
    
    @property
    def timeframe_enum(self):
        """Get TimeframeEnum for timeframe"""
        timeframe_map = {
            TimeframeEnum.ONE_MINUTE.value: TimeframeEnum.ONE_MINUTE,
            TimeframeEnum.FIVE_MINUTES.value: TimeframeEnum.FIVE_MINUTES,
            TimeframeEnum.FIFTEEN_MINUTES.value: TimeframeEnum.FIFTEEN_MINUTES,
            TimeframeEnum.ONE_HOUR.value: TimeframeEnum.ONE_HOUR,
            TimeframeEnum.FOUR_HOURS.value: TimeframeEnum.FOUR_HOURS,
            TimeframeEnum.ONE_DAY.value: TimeframeEnum.ONE_DAY,
            TimeframeEnum.ONE_WEEK.value: TimeframeEnum.ONE_WEEK,
            TimeframeEnum.ONE_MONTH.value: TimeframeEnum.ONE_MONTH
        }
        return timeframe_map.get(self.timeframe)
    
    @property 
    def ohlc_array(self):
        """Get OHLC as array [open, high, low, close]"""
        return [
            float(self.open_price),
            float(self.high_price),
            float(self.low_price),
            float(self.close_price)
        ]
    
    @property
    def price_range(self):
        """Calculate price range (high - low)"""
        return float(self.high_price) - float(self.low_price)
    
    @property
    def price_range_percentage(self):
        """Calculate price range as percentage of open price"""
        if self.open_price:
            return (self.price_range / float(self.open_price)) * 100
        return 0
    
    @property
    def is_bullish_candle(self):
        """Check if candle is bullish (close > open)"""
        return float(self.close_price) > float(self.open_price)
    
    @property
    def is_bearish_candle(self):
        """Check if candle is bearish (close < open)"""
        return float(self.close_price) < float(self.open_price)
    
    @property
    def is_doji_candle(self):
        """Check if candle is doji (close ≈ open)"""
        return abs(float(self.close_price) - float(self.open_price)) / float(self.open_price) < 0.001
    
    @property
    def candle_body_size(self):
        """Calculate candle body size as percentage"""
        return abs(float(self.close_price) - float(self.open_price)) / float(self.open_price) * 100
    
    @property
    def upper_shadow_size(self):
        """Calculate upper shadow size"""
        body_top = max(float(self.open_price), float(self.close_price))
        return float(self.high_price) - body_top
    
    @property
    def lower_shadow_size(self):
        """Calculate lower shadow size"""
        body_bottom = min(float(self.open_price), float(self.close_price))
        return body_bottom - float(self.low_price)
    
    @property
    def is_expired(self):
        """Check if data has expired according to retention policy"""
        if not self.expires_at:
            return False
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_high_quality(self):
        """Check if archived data has high quality"""
        return self.data_quality_score >= 90 and self.is_validated
    
    @classmethod
    def get_by_asset_timeframe(cls, session, asset_id: int, timeframe: str, 
                              start_date=None, end_date=None, limit: int = None):
        """Get archived price data for asset and timeframe"""
        query = session.query(cls).filter(
            cls.asset_id == asset_id,
            cls.timeframe == timeframe
        )
        
        if start_date:
            query = query.filter(cls.timestamp >= start_date)
        if end_date:
            query = query.filter(cls.timestamp <= end_date)
            
        query = query.order_by(cls.timestamp.asc())
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    @classmethod
    def get_by_year_month(cls, session, year: int, month: int = None):
        """Get archived data by year and optionally month"""
        query = session.query(cls).filter(cls.archive_year == year)
        
        if month:
            query = query.filter(cls.archive_month == month)
            
        return query.order_by(cls.timestamp.asc()).all()
    
    @classmethod
    def get_expired_data(cls, session):
        """Get data that has expired according to retention policy"""
        from datetime import datetime, timezone
        return session.query(cls).filter(
            cls.expires_at.isnot(None),
            cls.expires_at <= datetime.now(timezone.utc)
        ).all()
    
    @classmethod
    def get_by_retention_tier(cls, session, tier: str):
        """Get data by retention tier"""
        return session.query(cls).filter(cls.retention_tier == tier).all()
    
    @classmethod
    def get_high_quality_data(cls, session, min_quality: int = 90):
        """Get high quality archived data"""
        return session.query(cls).filter(
            cls.data_quality_score >= min_quality,
            cls.is_validated == True
        ).order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def get_compression_stats(cls, session):
        """Get compression statistics"""
        from sqlalchemy import func
        return session.query(
            func.avg(cls.compression_ratio).label('avg_compression'),
            func.min(cls.compression_ratio).label('min_compression'),
            func.max(cls.compression_ratio).label('max_compression'),
            func.count().label('total_records')
        ).filter(cls.compression_ratio.isnot(None)).first()
    
    def set_retention_policy(self, tier: str, days_to_retain: int):
        """Set retention policy for the data"""
        from datetime import datetime, timezone, timedelta
        
        self.retention_tier = tier
        if days_to_retain > 0:
            self.expires_at = datetime.now(timezone.utc) + timedelta(days=days_to_retain)
        else:
            self.expires_at = None
    
    def calculate_compression_ratio(self, original_size: int, compressed_size: int):
        """Calculate and store compression ratio"""
        if original_size > 0:
            self.compression_ratio = compressed_size / original_size
    
    def generate_data_hash(self, raw_data: str):
        """Generate SHA-256 hash of raw data for integrity"""
        import hashlib
        self.raw_data_hash = hashlib.sha256(raw_data.encode()).hexdigest()
    
    def validate_ohlc_integrity(self) -> bool:
        """Validate OHLC data integrity"""
        try:
            # Basic OHLC validation
            if not all([self.open_price, self.high_price, self.low_price, self.close_price]):
                return False
                
            open_val = float(self.open_price)
            high_val = float(self.high_price)
            low_val = float(self.low_price)
            close_val = float(self.close_price)
            
            # High should be highest, low should be lowest
            if high_val < max(open_val, close_val) or low_val > min(open_val, close_val):
                return False
                
            # Prices should be positive
            if any(price <= 0 for price in [open_val, high_val, low_val, close_val]):
                return False
                
            return True
            
        except (TypeError, ValueError):
            return False
    
    def to_dict(self, include_extended: bool = False) -> dict:
        """Convert archived price data to dictionary"""
        data = {
            'id': self.id,
            'asset_id': self.asset_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'timeframe': self.timeframe,
            'open': float(self.open_price) if self.open_price else None,
            'high': float(self.high_price) if self.high_price else None,
            'low': float(self.low_price) if self.low_price else None,
            'close': float(self.close_price) if self.close_price else None,
            'volume': float(self.volume) if self.volume else None,
            'volume_usd': float(self.volume_usd) if self.volume_usd else None,
            'price_change_percentage': float(self.price_change_percentage) if self.price_change_percentage else None,
            'is_bullish': self.is_bullish_candle,
            'candle_body_size': self.candle_body_size,
            'archive_year': self.archive_year,
            'archive_month': self.archive_month,
            'retention_tier': self.retention_tier,
            'data_quality_score': self.data_quality_score,
            'is_validated': self.is_validated,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_extended:
            data.update({
                'market_cap_usd': float(self.market_cap_usd) if self.market_cap_usd else None,
                'price_volatility': float(self.price_volatility) if self.price_volatility else None,
                'trade_count': self.trade_count,
                'archive_date': self.archive_date.isoformat() if self.archive_date else None,
                'compression_ratio': float(self.compression_ratio) if self.compression_ratio else None,
                'original_source': self.original_source,
                'raw_data_hash': self.raw_data_hash,
                'expires_at': self.expires_at.isoformat() if self.expires_at else None,
                'is_expired': self.is_expired,
                'extended_data': self.extended_data,
                'anomaly_flags': self.anomaly_flags,
                'price_range': self.price_range,
                'upper_shadow_size': self.upper_shadow_size,
                'lower_shadow_size': self.lower_shadow_size
            })
        
        return data