# backend/app/models/macro/metrics_snapshot.py
# Metrics snapshot model - Market-wide data collection

from sqlalchemy import Column, String, Integer, Numeric, DateTime, Boolean, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from ..base import BaseModel, CreatedAtMixin
from ..mixins import DataQualityMixin, ValidationMixin


class MetricsSnapshot(BaseModel, CreatedAtMixin, DataQualityMixin, ValidationMixin):
    """
    Metrics snapshot for market-wide data collection
    
    Uses CreatedAtMixin (only created_at) because snapshots are immutable
    point-in-time records of market conditions
    """
    __tablename__ = 'metrics_snapshot'
    
    # Core Snapshot Info
    snapshot_time = Column(DateTime(timezone=True), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)
    btc_price_usd = Column(Numeric(18,8), nullable=False)
    
    # Technical Indicators
    rsi_14 = Column(Numeric(5,2), nullable=True)
    sma_200 = Column(Numeric(30,8), nullable=True)
    ema_200 = Column(Numeric(30,8), nullable=True)
    
    # Market Sentiment
    fear_greed_index = Column(Numeric(5,2), nullable=True)
    google_trends_score = Column(Numeric(5,2), nullable=True)
    
    # Derivatives & Futures
    funding_rate_btc = Column(Numeric(10,6), nullable=True)
    open_interest_btc = Column(Numeric(30,2), nullable=True)
    
    # On-chain & Whale Flows
    whale_netflow_24h = Column(Numeric(30,2), nullable=True)
    active_addresses_btc = Column(Integer, nullable=True)
    
    # Composite & Health
    altcoin_dominance = Column(Numeric(5,2), nullable=True)
    liquidity_score = Column(Numeric(10,6), nullable=True)
    
    # Cycle & Returns
    halving_countdown_days = Column(Integer, nullable=True)
    weekly_return = Column(Numeric(5,4), nullable=True)
    monthly_return = Column(Numeric(5,4), nullable=True)
    
    # Dominance & Total Market-Cap
    btc_dominance = Column(Numeric(5,2), nullable=True)
    eth_dominance = Column(Numeric(5,2), nullable=True)
    usdt_dominance = Column(Numeric(5,2), nullable=True)
    total = Column(Numeric(18,2), nullable=True)
    
    # Intermarket Levels
    sp500 = Column(Numeric(10,2), nullable=True)
    gold = Column(Numeric(10,2), nullable=True)
    dxy = Column(Numeric(10,2), nullable=True)
    
    # Liquidations
    liquidations_long = Column(Numeric(30,2), nullable=True)
    liquidations_short = Column(Numeric(30,2), nullable=True)
    liquidation_zones = Column(JSON, nullable=True)
    
    # Extended Metrics
    extended_metrics = Column(JSON, nullable=True, default={})
    
    # Enhanced Core Metrics
    btc_eth_correlation_30d = Column(Numeric(6,4), nullable=True)
    btc_sp500_correlation_30d = Column(Numeric(6,4), nullable=True)
    us_10y_yield = Column(Numeric(8,4), nullable=True)
    vix_index = Column(Numeric(8,4), nullable=True)
    
    # Market Breadth & Quality
    crypto_market_breadth = Column(Numeric(6,2), nullable=True)
    new_highs_24h = Column(Integer, nullable=True)
    new_lows_24h = Column(Integer, nullable=True)
    momentum_index = Column(Numeric(8,4), nullable=True)
    
    # Data Quality & Metadata
    data_quality_flags = Column(JSON, nullable=True, default={})
    snapshot_version = Column(String(50), nullable=True)
    has_anomalies = Column(Boolean, nullable=False, default=False)
    
    # Performance Timing
    data_collection_started = Column(DateTime(timezone=True), nullable=True)
    data_collection_completed = Column(DateTime(timezone=True), nullable=True)
    
    # Constraints and Indexes
    __table_args__ = (
        # Unique constraints
        UniqueConstraint('snapshot_time', 'timeframe', name='unique_snapshot_time_timeframe'),
        
        # Check constraints
        CheckConstraint('fear_greed_index IS NULL OR fear_greed_index BETWEEN 0 AND 100', name='chk_fear_greed_range'),
        CheckConstraint('btc_dominance BETWEEN 0 AND 100', name='chk_dominance_range'),
        CheckConstraint('btc_price_usd > 0', name='chk_btc_price_positive'),
        CheckConstraint('collection_duration_ms IS NULL OR collection_duration_ms >= 0', name='chk_collection_duration'),
        
        # Performance indexes
        Index('idx_metrics_snapshot_time_desc', 'snapshot_time', postgresql_using='btree'),
        Index('idx_metrics_timeframe_time', 'timeframe', 'snapshot_time'),
        Index('idx_metrics_btc_price', 'btc_price_usd'),
        Index('idx_metrics_created_at', 'created_at'),
        Index('idx_metrics_fear_greed', 'fear_greed_index'),
        Index('idx_metrics_dominance', 'btc_dominance'),
        Index('idx_metrics_quality_score', 'data_quality_score'),
        Index('idx_metrics_has_anomalies', 'has_anomalies'),
        Index('idx_metrics_time_range', 'snapshot_time', 'timeframe', 'btc_price_usd'),
        Index('idx_metrics_correlation_btc_eth', 'btc_eth_correlation_30d'),
        Index('idx_metrics_correlation_btc_sp500', 'btc_sp500_correlation_30d'),
    )
    
    def __repr__(self):
        return f"<MetricsSnapshot(id={self.id}, time={self.snapshot_time}, btc_price={self.btc_price_usd})>"
    
    @property
    def market_regime_simple(self):
        """Simple market regime based on basic indicators"""
        if self.fear_greed_index:
            if self.fear_greed_index > 75:
                return "extreme_greed"
            elif self.fear_greed_index > 55:
                return "greed"
            elif self.fear_greed_index > 45:
                return "neutral"
            elif self.fear_greed_index > 25:
                return "fear"
            else:
                return "extreme_fear"
        return "unknown"
    
    @property
    def is_high_quality(self) -> bool:
        """Check if snapshot has high data quality"""
        return self.data_quality_score >= 90 and not self.has_anomalies
    
    @property
    def collection_time_ms(self) -> int:
        """Calculate data collection time in milliseconds"""
        if self.data_collection_started and self.data_collection_completed:
            delta = self.data_collection_completed - self.data_collection_started
            return int(delta.total_seconds() * 1000)
        return 0
    
    @property
    def market_stress_level(self) -> str:
        """Calculate market stress level based on multiple indicators"""
        stress_score = 0
        
        # VIX contribution
        if self.vix_index:
            if self.vix_index > 30:
                stress_score += 2
            elif self.vix_index > 20:
                stress_score += 1
        
        # Fear & Greed contribution
        if self.fear_greed_index:
            if self.fear_greed_index < 20 or self.fear_greed_index > 80:
                stress_score += 2
            elif self.fear_greed_index < 30 or self.fear_greed_index > 70:
                stress_score += 1
        
        # Liquidations contribution
        if self.liquidations_long and self.liquidations_short:
            total_liq = float(self.liquidations_long) + float(self.liquidations_short)
            if total_liq > 1000000000:  # $1B+
                stress_score += 2
            elif total_liq > 500000000:  # $500M+
                stress_score += 1
        
        if stress_score >= 4:
            return "high"
        elif stress_score >= 2:
            return "medium"
        else:
            return "low"
    
    @classmethod
    def get_latest_snapshot(cls, session, timeframe: str = "1d"):
        """Get the most recent snapshot for a timeframe"""
        return session.query(cls).filter(
            cls.timeframe == timeframe
        ).order_by(cls.snapshot_time.desc()).first()
    
    @classmethod
    def get_snapshots_range(cls, session, start_time, end_time, timeframe: str = "1d"):
        """Get snapshots within a time range"""
        return session.query(cls).filter(
            cls.snapshot_time.between(start_time, end_time),
            cls.timeframe == timeframe
        ).order_by(cls.snapshot_time.asc()).all()
    
    @classmethod
    def get_high_quality_snapshots(cls, session, min_quality_score: int = 90):
        """Get high quality snapshots"""
        return session.query(cls).filter(
            cls.data_quality_score >= min_quality_score,
            cls.has_anomalies == False
        ).order_by(cls.snapshot_time.desc()).all()
    
    def to_dict(self) -> dict:
        """Convert snapshot to dictionary"""
        return {
            'id': self.id,
            'snapshot_time': self.snapshot_time.isoformat() if self.snapshot_time else None,
            'timeframe': self.timeframe,
            'btc_price_usd': float(self.btc_price_usd) if self.btc_price_usd else None,
            'fear_greed_index': float(self.fear_greed_index) if self.fear_greed_index else None,
            'rsi_14': float(self.rsi_14) if self.rsi_14 else None,
            'btc_dominance': float(self.btc_dominance) if self.btc_dominance else None,
            'market_regime': self.market_regime_simple,
            'stress_level': self.market_stress_level,
            'data_quality_score': self.data_quality_score,
            'has_anomalies': self.has_anomalies,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    # Relationships (defined here to avoid circular imports)
    regime_analyses = relationship("AIRegimeAnalysis", back_populates="metrics_snapshot")