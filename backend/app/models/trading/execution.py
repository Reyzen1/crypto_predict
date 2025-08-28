# File: backend\app\models\trading\execution.py
# SQLAlchemy model for execution data

from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, ForeignKey, JSON, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base

class SignalExecution(Base):
    """
    User executions of trading signals with performance tracking
    """
    __tablename__ = "signal_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    signal_id = Column(Integer, ForeignKey("trading_signals.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Execution details
    execution_price = Column(DECIMAL(20, 8))
    position_size = Column(DECIMAL(30, 8))
    position_size_usd = Column(DECIMAL(15, 2))
    portfolio_percentage = Column(DECIMAL(5, 2))
    
    # Order details
    execution_type = Column(String(20), default='manual')  # manual, auto
    order_type = Column(String(20), default='market')     # market, limit
    order_id = Column(String(100))
    fill_type = Column(String(20), default='full')        # full, partial
    status = Column(String(20), default='pending')        # pending, filled, cancelled
    
    # Execution metadata
    execution_details = Column(JSON, default=dict)
    exchange = Column(String(50))
    fees_paid = Column(DECIMAL(15, 8), default=0)
    slippage_percent = Column(DECIMAL(5, 4))
    
    # Performance tracking
    current_pnl = Column(DECIMAL(15, 2))
    realized_pnl = Column(DECIMAL(15, 2))
    max_profit = Column(DECIMAL(15, 2))
    max_drawdown = Column(DECIMAL(15, 2))
    risk_metrics = Column(JSON, default=dict)
    
    # Exit conditions
    stop_loss_triggered = Column(Boolean, default=False)
    take_profit_triggered = Column(Boolean, default=False)
    
    # Timestamps
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    signal = relationship("TradingSignal", back_populates="executions")
    user = relationship("User", back_populates="signal_executions")
    
    def __repr__(self):
        return f"<SignalExecution(id={self.id}, signal_id={self.signal_id}, user_id={self.user_id})>"

# Performance indexes
Index('idx_signal_executions_user', SignalExecution.user_id, SignalExecution.executed_at.desc())
Index('idx_signal_executions_signal', SignalExecution.signal_id, SignalExecution.status)
Index('idx_signal_executions_performance', SignalExecution.realized_pnl.desc(), SignalExecution.executed_at.desc())
