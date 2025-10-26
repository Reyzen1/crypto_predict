# backend/app/models/asset/asset.py
# Asset model - Cryptocurrency and financial assets

from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, Text, Numeric, DateTime, CheckConstraint, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from ..base import BaseModel, TimestampMixin
from ..mixins import ActiveMixin, AccessTrackingMixin, DataQualityMixin, ExternalIdsMixin
from ..enums import AssetType
import logging

logger = logging.getLogger(__name__)

class Asset(BaseModel, TimestampMixin, ActiveMixin, AccessTrackingMixin, 
           DataQualityMixin, ExternalIdsMixin):
    """
    Asset model for cryptocurrencies and financial instruments
    
    Combines multiple mixins:
    - TimestampMixin: created_at, updated_at
    - ActiveMixin: is_active
    - AccessTrackingMixin: access_count, last_accessed_at
    - DataQualityMixin: data_quality_score, data_source
    - ExternalIdsMixin: external_ids
    """
    __tablename__ = 'assets'
    
    # Basic Asset Information
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    asset_type = Column(String(20), nullable=False, index=True)
    quote_currency = Column(String(10), nullable=True)
    
    # Asset Details
    logo_url = Column(Text, nullable=True)
    links = Column(JSON, nullable=True, default={})
    description = Column(Text, nullable=True)
    
    # Market Data
    market_cap = Column(Numeric(30,2), nullable=True)
    market_cap_rank = Column(Integer, nullable=True, index=True)
    current_price = Column(Numeric(20,8), nullable=True)
    total_volume = Column(Numeric(30,2), nullable=True)
    
    # Supply Information
    circulating_supply = Column(Numeric(30,8), nullable=True)
    total_supply = Column(Numeric(30,8), nullable=True)
    max_supply = Column(Numeric(30,8), nullable=True)
    
    # Price Changes
    price_change_percentage_24h = Column(Numeric(10,4), nullable=True)
    price_change_percentage_7d = Column(Numeric(10,4), nullable=True)
    price_change_percentage_30d = Column(Numeric(10,4), nullable=True)
    
    # All-Time Highs/Lows
    ath = Column(Numeric(20,8), nullable=True)
    ath_date = Column(DateTime(timezone=True), nullable=True)
    atl = Column(Numeric(20,8), nullable=True)
    atl_date = Column(DateTime(timezone=True), nullable=True)
    
    # Usage and Metrics
    metrics_details = Column(JSON, nullable=True, default={})
    timeframe_usage = Column(JSON, nullable=True, default={})
    
    # Timeframe Data Cache (Performance Optimization)
    timeframe_data = Column(JSON, nullable=True, default={}, comment="Cache of available timeframes with count, earliest/latest timestamps")
    """                            
                            Keys = timeframe codes, Values = {count, earliest, latest}
                            Example: {
                                '1h': {'count': 720, 'earliest_time': '2025-09-23T00:00:00Z', 'latest_time': '2025-10-23T12:00:00Z'},
                                '1d': {'count': 30, 'earliest_time': '2025-09-23T00:00:00Z', 'latest_time': '2025-10-23T00:00:00Z'}
                            }
    """

    # System Flags
    is_supported = Column(Boolean, nullable=False, default=True)
    last_price_update = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    price_data = relationship("PriceData", back_populates="asset", cascade="all, delete-orphan")
    price_data_archive = relationship("PriceDataArchive", back_populates="asset", cascade="all, delete-orphan")
    
    # Constraints and Indexes
    __table_args__ = (
        # Unique constraints
        UniqueConstraint('symbol', name='unique_asset_symbol'),
        
        # Check constraints
        CheckConstraint('market_cap IS NULL OR market_cap >= 0', name='chk_market_cap_positive'),
        CheckConstraint('current_price IS NULL OR current_price > 0', name='chk_current_price_positive'),
        CheckConstraint('circulating_supply IS NULL OR circulating_supply >= 0', name='chk_supply_positive'),
        CheckConstraint('total_supply IS NULL OR total_supply >= circulating_supply', name='chk_total_supply_gte_circulating'),
        CheckConstraint('max_supply IS NULL OR max_supply >= total_supply', name='chk_max_supply_gte_total'),
        CheckConstraint('data_quality_score BETWEEN 0 AND 100', name='chk_data_quality'),
        CheckConstraint('market_cap_rank IS NULL OR market_cap_rank > 0', name='chk_market_cap_rank'),
        CheckConstraint("asset_type IN ('crypto', 'stablecoin', 'defi', 'nft', 'index')", name='chk_asset_type_valid'),
        CheckConstraint('access_count >= 0', name='chk_access_count_positive'),
        
        # Performance indexes
        Index('idx_asset_symbol', 'symbol'),
        Index('idx_asset_type', 'asset_type'),
        Index('idx_asset_active', 'is_active'),
        Index('idx_asset_supported', 'is_supported'),
        Index('idx_asset_market_cap_rank', 'market_cap_rank'),
        Index('idx_asset_market_cap', 'market_cap'),
        Index('idx_asset_created_at', 'created_at'),
        Index('idx_asset_last_accessed', 'last_accessed_at'),
        Index('idx_asset_last_price_update', 'last_price_update'),
        Index('idx_asset_data_quality', 'data_quality_score'),
        Index('idx_asset_name_search', 'name', postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'}),
        Index('idx_asset_type_rank', 'asset_type', 'market_cap_rank'),
        Index('idx_asset_active_supported', 'is_active', 'is_supported'),
    )
    
    def __repr__(self):
        return f"<Asset(id={self.id}, symbol='{self.symbol}', name='{self.name}')>"
    
    @property
    def display_name(self):
        """Get display name for UI"""
        return f"{self.name} ({self.symbol})"
    
    @property
    def is_crypto(self):
        """Check if asset is a cryptocurrency"""
        from ..enums import AssetType
        return self.asset_type in [AssetType.CRYPTO.value, AssetType.STABLECOIN.value]
    
    @property
    def is_stablecoin(self):
        """Check if asset is a stablecoin"""
        from ..enums import AssetType
        return self.asset_type == AssetType.STABLECOIN.value
    
    @property
    def market_cap_formatted(self):
        """Get formatted market cap"""
        if not self.market_cap:
            return "N/A"
        
        market_cap = float(self.market_cap)
        if market_cap >= 1e12:
            return f"${market_cap/1e12:.2f}T"
        elif market_cap >= 1e9:
            return f"${market_cap/1e9:.2f}B"
        elif market_cap >= 1e6:
            return f"${market_cap/1e6:.2f}M"
        elif market_cap >= 1e3:
            return f"${market_cap/1e3:.2f}K"
        else:
            return f"${market_cap:.2f}"
    
    @property
    def supply_percentage(self):
        """Calculate circulating supply percentage"""
        if self.max_supply and self.circulating_supply:
            return (float(self.circulating_supply) / float(self.max_supply)) * 100
        return None
    
    @property
    def is_high_quality_data(self):
        """Check if asset has high quality data"""
        return self.data_quality_score >= 90
    
    @property
    def price_trend_24h(self):
        """Get 24h price trend indicator"""
        if not self.price_change_percentage_24h:
            return "neutral"
        
        change = float(self.price_change_percentage_24h)
        if change > 5:
            return "strong_up"
        elif change > 0:
            return "up"
        elif change < -5:
            return "strong_down"
        elif change < 0:
            return "down"
        else:
            return "neutral"
    
    def update_access_stats(self):
        """Update access statistics"""
        from datetime import datetime, timezone
        self.access_count += 1
        self.last_accessed_at = datetime.now(timezone.utc)
    
    def update_price_data(self, price: float, market_cap: float = None, volume: float = None):
        """Update current price and related data"""
        from datetime import datetime, timezone
        
        self.current_price = price
        if market_cap:
            self.market_cap = market_cap
        if volume:
            self.total_volume = volume
        self.last_price_update = datetime.now(timezone.utc)
    
    def set_external_id(self, provider: str, external_id: str):
        """Set external ID for a provider"""
        if not self.external_ids:
            self.external_ids = {}
        self.external_ids[provider] = external_id
    
    def get_external_id(self, provider: str):
        """Get external ID for a provider"""
        if not self.external_ids:
            return None
        return self.external_ids.get(provider)
    
    def get_timeframe_info(self, timeframe: str) -> dict:
        """
        Get timeframe information from cache
        
        Args:
            timeframe: Timeframe identifier
            
        Returns:
            Dictionary with count, earliest_time, latest_time
        """
        if not self.timeframe_data:
            return {'count': 0, 'earliest_time': None, 'latest_time': None}
        
        return self.timeframe_data.get(timeframe, {
            'count': 0, 
            'earliest_time': None, 
            'latest_time': None
        })
    
    def get_all_timeframe_data(self) -> dict:
        """
        Get all timeframe data with aggregatable information
        
        Returns:
            Dictionary with all timeframe data and aggregation capabilities
        """
        from ...repositories.asset.price_data_repository import PriceDataRepository
        
        # Get timeframe hierarchy
        hierarchy = {
            '1m': {'minutes': 1, 'base_timeframe': None},
            '5m': {'minutes': 5, 'base_timeframe': '1m'},
            '15m': {'minutes': 15, 'base_timeframe': '5m'},
            '1h': {'minutes': 60, 'base_timeframe': '15m'},
            '4h': {'minutes': 240, 'base_timeframe': '1h'},
            '1d': {'minutes': 1440, 'base_timeframe': '4h'},
            '1w': {'minutes': 10080, 'base_timeframe': '1d'},
            '1M': {'minutes': 43200, 'base_timeframe': '1w'}
        }
        
        # Function to get aggregatable timeframes
        def get_aggregatable_timeframes(source_timeframe: str) -> list:
            source_minutes = hierarchy.get(source_timeframe, {}).get('minutes', 0)
            if not source_minutes:
                return []
            
            aggregatable = []
            for tf, info in hierarchy.items():
                tf_minutes = info['minutes']
                if tf_minutes > source_minutes and tf_minutes % source_minutes == 0:
                    aggregatable.append(tf)
            
            return sorted(aggregatable, key=lambda x: hierarchy[x]['minutes'])
        
        # Build result with cached data and aggregation info
        result = {}
        for timeframe in hierarchy.keys():
            info = self.get_timeframe_info(timeframe)
            result[timeframe] = {
                'count': info['count'],
                'latest_time': info['latest_time'],
                'earliest_time': info['earliest_time'],
                'can_aggregate_to': get_aggregatable_timeframes(timeframe)
            }
        
        return result
    
    def reset_timeframe_cache(self):
        """Reset timeframe data cache"""
        self.timeframe_data = {}
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(self, 'timeframe_data')
    
    def get_timeframe_data(self, timeframe: str = None):
        """Get timeframe data cache"""
        if not self.timeframe_data:
            return {} if timeframe is None else None
        
        if timeframe:
            return self.timeframe_data.get(timeframe)
        return self.timeframe_data

    def get_earliest_candle_time(self, timeframe: str):
        """
        Get earliest candle time for a specific timeframe from cache
        
        Args:
            timeframe: Target timeframe (e.g., '1h', '1d')
        Returns:
            datetime object or None if not found
        """
        timeframe_info = self.get_timeframe_data(timeframe)
        if not timeframe_info or not timeframe_info.get('earliest_time'):
            return None
        
        try:
            earliest_time_str = timeframe_info['earliest_time']
            if earliest_time_str:
                # Parse and ensure UTC timezone
                dt = datetime.fromisoformat(earliest_time_str.replace('Z', '+00:00'))
                # If somehow no timezone, add UTC
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse earliest_time '{earliest_time_str}': {e}")
            return None

        return None        

    def get_latest_candle_time(self, timeframe: str):
        """
        Get latest candle time for a specific timeframe from cache
        
        Args:
            timeframe: Target timeframe (e.g., '1h', '1d')
            
        Returns:
            datetime object or None if not found
        """
        timeframe_info = self.get_timeframe_data(timeframe)
        if not timeframe_info or not timeframe_info.get('latest_time'):
            return None
        
        try:
            latest_time_str = timeframe_info['latest_time']
            if latest_time_str:
                # Parse and ensure UTC timezone
                dt = datetime.fromisoformat(latest_time_str.replace('Z', '+00:00'))
                # If somehow no timezone, add UTC
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse latest_time '{latest_time_str}': {e}")
            return None
        
        return None
    
    def update_timeframe_data(self, timeframe: str, count, 
                            earliest_time: str = None, latest_time: str = None):
        """
        Update timeframe data cache for performance optimization
        
        Args:
            timeframe: Timeframe identifier (e.g., '1h', '1d')
            count: Number of records for this timeframe (int or str)
            earliest_time: Earliest timestamp in ISO format
            latest_time: Latest timestamp in ISO format
        """
        if not self.timeframe_data:
            self.timeframe_data = {}
        
        # Ensure count is always an integer for consistent comparisons
        try:
            count_int = int(count) if count is not None else 0
        except (ValueError, TypeError):
            count_int = 0
        
        self.timeframe_data[timeframe] = {
            'count': count_int,
            'earliest_time': earliest_time,
            'latest_time': latest_time,
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
        
        # Mark as modified for SQLAlchemy
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(self, 'timeframe_data')
    
    def remove_timeframe_data(self, timeframe: str):
        """Remove timeframe from data cache"""
        if self.timeframe_data and timeframe in self.timeframe_data:
            del self.timeframe_data[timeframe]
    
    def refresh_timeframe_data_from_db(self, session):
        """Refresh timeframe_data cache from price_data table"""
        from .price_data import PriceData
        from sqlalchemy import func
        
        # Query all timeframes with their stats
        timeframe_stats = session.query(
            PriceData.timeframe,
            func.count(PriceData.id).label('count'),
            func.min(PriceData.candle_time).label('earliest_time'),
            func.max(PriceData.candle_time).label('latest_time')
        ).filter(
            PriceData.asset_id == self.id
        ).group_by(PriceData.timeframe).all()
        
        # Update cache
        self.timeframe_data = {}
        for stat in timeframe_stats:
            self.timeframe_data[stat.timeframe] = {
                'count': stat.count,
                'earliest_time': stat.earliest.isoformat() if stat.earliest else None,
                'latest_time': stat.latest.isoformat() if stat.latest else None,
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
    
    @property
    def available_timeframes(self):
        """Get list of available timeframes"""
        if not self.timeframe_data:
            return []
        
        def safe_count(data):
            try:
                return int(data.get('count', 0)) if data.get('count') is not None else 0
            except (ValueError, TypeError):
                return 0
        
        return [tf for tf, data in self.timeframe_data.items() if safe_count(data) > 0]
    
    @property
    def timeframe_summary(self):
        """Get summary of timeframe data"""
        if not self.timeframe_data:
            return {'total_timeframes': 0, 'total_records': 0}
        
        total_records = sum(data.get('count', 0) for data in self.timeframe_data.values())
        active_timeframes = len([tf for tf, data in self.timeframe_data.items() if data.get('count', 0) > 0])
        
        return {
            'total_timeframes': active_timeframes,
            'total_records': total_records,
            'timeframes': list(self.timeframe_data.keys()) if self.timeframe_data else []
        }
    
    @classmethod
    def get_by_symbol(cls, session, symbol: str):
        """Get asset by symbol"""
        return session.query(cls).filter(
            cls.symbol.ilike(symbol.upper())
        ).first()
    
    @classmethod
    def get_active_assets(cls, session, asset_type: str = None):
        """Get active and supported assets"""
        query = session.query(cls).filter(
            cls.is_active == True,
            cls.is_supported == True
        )
        
        if asset_type:
            query = query.filter(cls.asset_type == asset_type)
            
        return query.order_by(cls.market_cap_rank.asc()).all()
    
    @classmethod
    def get_top_assets(cls, session, limit: int = 100):
        """Get top assets by market cap"""
        return session.query(cls).filter(
            cls.is_active == True,
            cls.is_supported == True,
            cls.market_cap_rank.isnot(None)
        ).order_by(cls.market_cap_rank.asc()).limit(limit).all()
    
    @classmethod
    def search_assets(cls, session, search_term: str, limit: int = 20):
        """Search assets by name or symbol"""
        search_pattern = f"%{search_term}%"
        return session.query(cls).filter(
            cls.is_active == True,
            cls.is_supported == True,
            (cls.name.ilike(search_pattern) | cls.symbol.ilike(search_pattern))
        ).order_by(cls.market_cap_rank.asc()).limit(limit).all()
    
    @classmethod
    def get_recently_accessed(cls, session, limit: int = 10):
        """Get recently accessed assets"""
        return session.query(cls).filter(
            cls.last_accessed_at.isnot(None)
        ).order_by(cls.last_accessed_at.desc()).limit(limit).all()
    
    def to_dict(self, include_detailed: bool = False) -> dict:
        """Convert asset to dictionary"""
        data = {
            'id': self.id,
            'symbol': self.symbol,
            'name': self.name,
            'display_name': self.display_name,
            'asset_type': self.asset_type,
            'is_crypto': self.is_crypto,
            'is_stablecoin': self.is_stablecoin,
            'current_price': float(self.current_price) if self.current_price else None,
            'market_cap': float(self.market_cap) if self.market_cap else None,
            'market_cap_formatted': self.market_cap_formatted,
            'market_cap_rank': self.market_cap_rank,
            'price_change_24h': float(self.price_change_percentage_24h) if self.price_change_percentage_24h else None,
            'price_trend_24h': self.price_trend_24h,
            'logo_url': self.logo_url,
            'is_active': self.is_active,
            'is_supported': self.is_supported,
            'data_quality_score': self.data_quality_score,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_detailed:
            data.update({
                'description': self.description,
                'quote_currency': self.quote_currency,
                'total_volume': float(self.total_volume) if self.total_volume else None,
                'circulating_supply': float(self.circulating_supply) if self.circulating_supply else None,
                'total_supply': float(self.total_supply) if self.total_supply else None,
                'max_supply': float(self.max_supply) if self.max_supply else None,
                'supply_percentage': self.supply_percentage,
                'price_change_7d': float(self.price_change_percentage_7d) if self.price_change_percentage_7d else None,
                'price_change_30d': float(self.price_change_percentage_30d) if self.price_change_percentage_30d else None,
                'ath': float(self.ath) if self.ath else None,
                'ath_date': self.ath_date.isoformat() if self.ath_date else None,
                'atl': float(self.atl) if self.atl else None,
                'atl_date': self.atl_date.isoformat() if self.atl_date else None,
                'links': self.links,
                'external_ids': self.external_ids,
                'access_count': self.access_count,
                'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None,
                'last_price_update': self.last_price_update.isoformat() if self.last_price_update else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            })
        
        return data