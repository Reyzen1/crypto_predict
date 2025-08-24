# File: backend\app\models\trading\risk.py
# SQLAlchemy model for risk data

from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, ForeignKey, JSON, Boolean, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base

class RiskManagement(Base):
    """
    User risk management settings, limits, and current exposure tracking
    """
    __tablename__ = "risk_management"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User reference
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Risk limits
    max_position_size_usd = Column(DECIMAL(15, 2), default=1000)
    max_portfolio_risk_percent = Column(DECIMAL(5, 2), default=2.0)
    max_daily_loss_percent = Column(DECIMAL(5, 2), default=5.0)
    max_concurrent_signals = Column(Integer, default=5)
    
    # Risk rules and settings
    risk_rules = Column(JSON, default={})
    position_sizing_method = Column(String(20), default='fixed_percent')
    
    # Current exposure tracking
    current_exposure_usd = Column(DECIMAL(15, 2), default=0)
    current_portfolio_risk = Column(DECIMAL(5, 2), default=0)
    active_positions_count = Column(Integer, default=0)
    daily_loss_current = Column(DECIMAL(15, 2), default=0)
    
    # Analysis and metrics
    risk_metrics = Column(JSON, default={})
    portfolio_correlation = Column(JSON, default={})
    exposure_by_sector = Column(JSON, default={})
    
    # Performance tracking
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    total_pnl = Column(DECIMAL(15, 2), default=0)
    max_drawdown_history = Column(DECIMAL(15, 2), default=0)
    
    # Risk control flags
    risk_limit_breached = Column(Boolean, default=False)
    auto_stop_trading = Column(Boolean, default=False)
    
    # Risk monitoring
    last_risk_check = Column(DateTime(timezone=True), server_default=func.now())
    risk_warnings = Column(JSON, default=[])
    
    # Timestamps
    last_calculated = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="risk_profiles")
    
    def __repr__(self):
        return f"<RiskManagement(user_id={self.user_id}, exposure=${self.current_exposure_usd})>"

# Constraints and indexes
Index('idx_risk_management_exposure', RiskManagement.current_exposure_usd.desc(), RiskManagement.current_portfolio_risk.desc())
Index('idx_risk_management_limits', RiskManagement.risk_limit_breached, RiskManagement.auto_stop_trading)
