# File: backend\app\models\watchlist\suggestion.py
# SQLAlchemy model for suggestion data

from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, ForeignKey, JSON, Text, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import timedelta

from app.core.database import Base

class AISuggestion(Base):
    """
    AI-generated suggestions for watchlist management
    """
    __tablename__ = "ai_suggestions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Crypto reference
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False, index=True)
    
    # Suggestion details
    suggestion_type = Column(String(20), nullable=False, index=True)  # add_tier1, add_tier2, remove, tier_change
    current_tier = Column(String(10))      # Current watchlist tier
    suggested_tier = Column(String(10))    # Suggested watchlist tier
    
    # AI scoring
    confidence_score = Column(DECIMAL(5, 4), nullable=False, index=True)
    priority_score = Column(DECIMAL(5, 2), default=50, index=True)  # 0-100
    
    # AI analysis
    reasoning = Column(JSON, default={})          # AI reasoning and explanation
    analysis_data = Column(JSON, default={})     # Supporting analysis
    supporting_metrics = Column(JSON, default={})
    risk_assessment = Column(JSON, default={})
    
    # Model information
    model_version = Column(String(50))
    data_sources = Column(JSON, default={})
    
    # Review status
    status = Column(String(20), default='pending', index=True)  # pending, approved, rejected, expired
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    review_notes = Column(Text)
    
    # Timestamps
    expires_at = Column(DateTime(timezone=True), default=lambda: func.now() + timedelta(days=7))
    suggested_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    cryptocurrency = relationship("Cryptocurrency", back_populates="ai_suggestions")
    reviewer = relationship("User")
    reviews = relationship("SuggestionReview", back_populates="suggestion")
    
    def __repr__(self):
        return f"<AISuggestion(id={self.id}, type={self.suggestion_type}, crypto_id={self.crypto_id})>"

# Performance indexes
Index('idx_ai_suggestions_status', AISuggestion.status, AISuggestion.priority_score.desc(), AISuggestion.suggested_at.desc())
Index('idx_ai_suggestions_crypto', AISuggestion.crypto_id, AISuggestion.status)
Index('idx_ai_suggestions_type', AISuggestion.suggestion_type, AISuggestion.confidence_score.desc())
Index('idx_ai_suggestions_expires', AISuggestion.expires_at).where(AISuggestion.status == 'pending')
