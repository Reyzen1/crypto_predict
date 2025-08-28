# File: backend\app\models\market\dominance.py
# SQLAlchemy model for dominance data

from sqlalchemy import Column, Integer, DateTime, DECIMAL, JSON, Index
from sqlalchemy.sql import func

from app.core.database import Base

class DominanceData(Base):
    """
    Market dominance tracking for major cryptocurrencies
    """
    __tablename__ = "dominance_data"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Dominance percentages
    btc_dominance = Column(DECIMAL(5, 2), nullable=False, index=True)
    eth_dominance = Column(DECIMAL(5, 2), nullable=False, index=True)  
    alt_dominance = Column(DECIMAL(5, 2), nullable=False)
    stablecoin_dominance = Column(DECIMAL(5, 2), default=0)
    
    # Market data
    total_market_cap = Column(DECIMAL(20, 2))
    total_volume_24h = Column(DECIMAL(20, 2))
    
    # Analysis data
    trend_analysis = Column(JSON, default=dict)
    dominance_changes = Column(JSON, default=dict)
    rotation_signals = Column(JSON, default=dict)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<DominanceData(btc={self.btc_dominance}%, eth={self.eth_dominance}%)>"

# Performance indexes
Index('idx_dominance_btc', DominanceData.btc_dominance.desc(), DominanceData.timestamp.desc())
Index('idx_dominance_eth', DominanceData.eth_dominance.desc(), DominanceData.timestamp.desc())
