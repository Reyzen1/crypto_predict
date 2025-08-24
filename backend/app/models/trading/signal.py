# File: backend\app\models\trading\signal.py
# SQLAlchemy model for signal data

from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, ForeignKey, JSON, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import timedelta

from app.core.database import Base

class TradingSignal(Base):
    """
    AI-generated trading signals with precise entry/exit timing
    Enhanced to match database schema exactly
    """
    __tablename__ = "trading_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Crypto reference
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False, index=True)
    
    # Signal basics
    signal_type = Column(String(10), nullable=False, index=True)  # buy, sell, hold
    entry_price = Column(DECIMAL(20, 8), nullable=False)
    target_price = Column(DECIMAL(20, 8), nullable=False)
    stop_loss = Column(DECIMAL(20, 8), nullable=False)
    
    # Risk and confidence
    confidence_score = Column(DECIMAL(5, 4), nullable=False, index=True)
    risk_level = Column(String(10), nullable=False)  # low, medium, high
    risk_reward_ratio = Column(DECIMAL(6, 2))
    
    # Timing and position sizing
    time_horizon_hours = Column(Integer, default=24)
    max_drawdown_percent = Column(DECIMAL(5, 2), default=5.0)
    position_size_percent = Column(DECIMAL(5, 2), default=2.0)
    
    # Analysis context
    ai_analysis = Column(JSON, default={})
    market_context = Column(JSON, default={})
    technical_indicators = Column(JSON, default={})
    layer1_context = Column(JSON, default={})
    layer2_context = Column(JSON, default={})
    layer3_context = Column(JSON, default={})
    
    # Model and generation info
    model_name = Column(String(50), nullable=False, default='timing_model_v1')
    model_version = Column(String(20), nullable=False, default='1.0')
    generation_method = Column(String(50), default='ai_analysis')
    data_sources = Column(JSON, default={})
    
    # Status and priority
    status = Column(String(20), default='active')  # active, expired, executed
    priority_level = Column(String(10), default='medium')  # low, medium, high
    
    # Timestamps
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), default=lambda: func.now() + timedelta(days=7))
    activated_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    cryptocurrency = relationship("Cryptocurrency", back_populates="trading_signals")
    executions = relationship("SignalExecution", back_populates="signal")
    
    def __repr__(self):
        return f"<TradingSignal(id={self.id}, type={self.signal_type}, crypto_id={self.crypto_id})>"

# Performance indexes matching database
Index('idx_signals_crypto_status', TradingSignal.crypto_id, TradingSignal.status, TradingSignal.generated_at.desc())
Index('idx_signals_confidence', TradingSignal.confidence_score.desc(), TradingSignal.risk_level, TradingSignal.generated_at.desc())
Index('idx_signals_expires', TradingSignal.expires_at).where(TradingSignal.status == 'active')
Index('idx_signals_type', TradingSignal.signal_type, TradingSignal.status, TradingSignal.generated_at.desc())
