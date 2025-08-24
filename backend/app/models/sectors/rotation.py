# File: backend\app\models\sectors\rotation.py
# SQLAlchemy model for rotation data

from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, JSON, ForeignKey, Index
from sqlalchemy.sql import func

from app.core.database import Base

class SectorRotationAnalysis(Base):
    """
    Analysis of capital rotation patterns between crypto sectors
    """
    __tablename__ = "sector_rotation_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Rotation direction
    from_sector_id = Column(Integer, ForeignKey("crypto_sectors.id"), index=True)
    to_sector_id = Column(Integer, ForeignKey("crypto_sectors.id"), index=True)
    
    # Rotation metrics
    rotation_strength = Column(DECIMAL(5, 4), nullable=False)  # 0-1
    confidence_score = Column(DECIMAL(5, 4), nullable=False)   # 0-1
    capital_flow_estimate = Column(DECIMAL(15, 2))            # USD estimate
    flow_direction = Column(String(10))                        # inflow/outflow/neutral
    
    # Analysis data
    rotation_indicators = Column(JSON, default={})
    market_context = Column(JSON, default={})
    detection_method = Column(String(50), default='volume_price_analysis')
    
    # Timestamps
    analysis_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<SectorRotationAnalysis(from={self.from_sector_id}, to={self.to_sector_id})>"

# Performance indexes
Index('idx_sector_rotation_strength', SectorRotationAnalysis.rotation_strength.desc(), SectorRotationAnalysis.confidence_score.desc())
Index('idx_sector_rotation_from', SectorRotationAnalysis.from_sector_id, SectorRotationAnalysis.analysis_time.desc())
Index('idx_sector_rotation_to', SectorRotationAnalysis.to_sector_id, SectorRotationAnalysis.analysis_time.desc())
