# File: backend\app\models\market\regime.py
# SQLAlchemy model for regime data

from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, JSON, Index
from sqlalchemy.sql import func

from app.core.database import Base

class MarketRegimeAnalysis(Base):
    """
    Market regime analysis and classification
    Tracks overall market state: Bull/Bear/Neutral/Volatile
    """
    __tablename__ = "market_regime_analysis"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Market regime classification
    regime = Column(String(10), nullable=False, index=True)  # bull, bear, sideways, volatile
    confidence_score = Column(DECIMAL(5, 4), nullable=False, index=True)
    
    # Regime characteristics
    risk_level = Column(String(10), nullable=False, index=True)  # low, medium, high, extreme
    trend_strength = Column(DECIMAL(5, 4))
    recommended_exposure = Column(DECIMAL(5, 4))
    
    # Analysis data from database
    indicators = Column(JSON, default={})
    analysis_data = Column(JSON, default={})
    market_context = Column(JSON, default={})
    
    # Timestamps
    analysis_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<MarketRegimeAnalysis(regime={self.regime}, confidence={self.confidence_score})>"

# Performance indexes
Index('idx_market_regime_regime', MarketRegimeAnalysis.regime, MarketRegimeAnalysis.confidence_score.desc())
