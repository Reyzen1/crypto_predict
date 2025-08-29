# File: backend\app\models\watchlist\watchlist.py
# SQLAlchemy model for watchlist data

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, DECIMAL, Text, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base

class Watchlist(Base):
    """
    Watchlist containers for different user types and purposes
    """
    __tablename__ = "watchlists"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User reference (nullable for system watchlists)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    
    # Watchlist identification
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False, index=True)  # 'default', 'personal'
    description = Column(Text)
    
    # Watchlist settings
    max_items = Column(Integer, default=50)
    is_active = Column(Boolean, default=True, index=True)
    is_public = Column(Boolean, default=False)
    settings = Column(JSON, default=dict)
    performance_metrics = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="watchlists")
    items = relationship("WatchlistItem", back_populates="watchlist", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Watchlist(id={self.id}, name={self.name}, type={self.type})>"

class WatchlistItem(Base):
    """
    Individual cryptocurrency items within watchlists
    """
    __tablename__ = "watchlist_items"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    watchlist_id = Column(Integer, ForeignKey("watchlists.id"), nullable=False, index=True)
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False, index=True)
    
    # Item properties
    score = Column(DECIMAL(5, 2), default=0)  # AI-calculated score 0-100
    rank_position = Column(Integer)           # Position ranking within watchlist
    status = Column(String(20), default='active')  # active, paused, removed
    
    # Analysis data
    selection_criteria = Column(JSON, default=dict)  # Criteria used for selection
    performance_metrics = Column(JSON, default=dict)
    risk_metrics = Column(JSON, default=dict)
    ai_analysis = Column(JSON, default=dict)
    
    # Management info
    added_by_user_id = Column(Integer, ForeignKey("users.id"))
    added_reason = Column(Text)
    
    # Timestamps
    last_updated_score = Column(DateTime(timezone=True), server_default=func.now())
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    watchlist = relationship("Watchlist", back_populates="items")
    cryptocurrency = relationship("Cryptocurrency", back_populates="watchlist_items")
    added_by_user = relationship("User")
    
    def __repr__(self):
        return f"<WatchlistItem(id={self.id}, watchlist_id={self.watchlist_id}, crypto_id={self.crypto_id})>"

# Constraints and indexes
UniqueConstraint('watchlist_id', 'crypto_id', name='watchlist_items_watchlist_id_crypto_id_key')
Index('idx_watchlist_items_watchlist', WatchlistItem.watchlist_id, WatchlistItem.status, WatchlistItem.score.desc())
Index('idx_watchlist_items_score', WatchlistItem.score.desc(), WatchlistItem.watchlist_id)
Index('idx_watchlist_items_rank', WatchlistItem.watchlist_id, WatchlistItem.rank_position)
