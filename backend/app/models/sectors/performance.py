# File: backend\app\models\sectors\performance.py
# SQLAlchemy model for performance data

from sqlalchemy import Column, Integer, ForeignKey, DateTime, DECIMAL, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base

class SectorPerformance(Base):
    """
    Real-time and historical performance data for crypto sectors
    """
    __tablename__ = "sector_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Sector reference
    sector_id = Column(Integer, ForeignKey("crypto_sectors.id"), nullable=False, index=True)
    
    # Performance metrics
    performance_1h = Column(DECIMAL(8, 4))
    performance_24h = Column(DECIMAL(8, 4))
    performance_7d = Column(DECIMAL(8, 4))
    performance_30d = Column(DECIMAL(8, 4))
    performance_90d = Column(DECIMAL(8, 4))
    
    # Volume and market cap changes
    volume_change_24h = Column(DECIMAL(8, 4))
    market_cap_change_24h = Column(DECIMAL(8, 4))
    
    # Totals
    market_cap_total = Column(DECIMAL(20, 2))
    volume_total_24h = Column(DECIMAL(20, 2))
    asset_count = Column(Integer, default=0)
    
    # Top/worst performers
    top_performer_id = Column(Integer, ForeignKey("cryptocurrencies.id"))
    worst_performer_id = Column(Integer, ForeignKey("cryptocurrencies.id"))
    
    # Analysis metrics
    performance_metrics = Column(JSON, default=dict)
    momentum_score = Column(DECIMAL(5, 4))    # -1 to 1
    relative_strength = Column(DECIMAL(5, 4)) # vs overall market
    
    # Timestamps
    analysis_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    sector = relationship("CryptoSector", back_populates="performance_records")
    top_performer = relationship("Cryptocurrency", foreign_keys=[top_performer_id])
    worst_performer = relationship("Cryptocurrency", foreign_keys=[worst_performer_id])
    
    def __repr__(self):
        return f"<SectorPerformance(sector_id={self.sector_id}, 24h={self.performance_24h}%)>"

# Performance indexes
Index('idx_sector_perf_sector_time', SectorPerformance.sector_id, SectorPerformance.analysis_time.desc())
Index('idx_sector_perf_performance', SectorPerformance.performance_24h.desc(), SectorPerformance.analysis_time.desc())
Index('idx_sector_perf_momentum', SectorPerformance.momentum_score.desc(), SectorPerformance.analysis_time.desc())
