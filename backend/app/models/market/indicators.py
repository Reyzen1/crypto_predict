# File: backend\app\models\market\indicators.py
# SQLAlchemy model for indicators data

from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, JSON, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql import func

from app.core.database import Base

class MacroIndicator(Base):
    """
    Macro economic indicators tracking
    """
    __tablename__ = "macro_indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Indicator identification
    indicator_name = Column(String(50), nullable=False, index=True)
    indicator_category = Column(String(30), nullable=False, default='general', index=True)
    
    # Values
    value = Column(DECIMAL(15, 8), nullable=False)  # Updated field name
    normalized_value = Column(DECIMAL(5, 4))
    
    # Metadata
    timeframe = Column(String(20), nullable=False, default='1d')
    data_source = Column(String(50), nullable=False, index=True)
    meta_data = Column(JSON, default=dict)
    quality_score = Column(DECIMAL(3, 2), default=1.0)

    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<MacroIndicator(name={self.indicator_name}, value={self.value})>"

# Unique constraint and indexes
UniqueConstraint('indicator_name', 'timeframe', 'timestamp', name='macro_indicators_indicator_name_timeframe_timestamp_key')
Index('idx_macro_indicators_name_time', MacroIndicator.indicator_name, MacroIndicator.timestamp.desc())
Index('idx_macro_indicators_category', MacroIndicator.indicator_category, MacroIndicator.timestamp.desc())
Index('idx_macro_indicators_meta_data', MacroIndicator.meta_data, postgresql_using='gin')
