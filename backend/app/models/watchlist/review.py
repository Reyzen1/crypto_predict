# File: backend\app\models\watchlist\review.py
# SQLAlchemy model for review data

from sqlalchemy import Column, Integer, String, Text, DateTime, DECIMAL, ForeignKey, JSON, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base

class SuggestionReview(Base):
    """
    Admin reviews and actions on AI suggestions
    """
    __tablename__ = "suggestion_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    suggestion_id = Column(Integer, ForeignKey("ai_suggestions.id"), nullable=False, index=True)
    admin_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Review decision
    action = Column(String(10), nullable=False, index=True)  # approved, rejected, modified
    review_notes = Column(Text)
    modifications = Column(JSON, default={})
    
    # Review quality metrics
    confidence_adjustment = Column(DECIMAL(5, 4))  # Admin confidence override
    reviewer_score = Column(DECIMAL(5, 2))         # Admin confidence in decision
    review_time_spent = Column(Integer)            # Time in seconds
    follow_up_required = Column(Boolean, default=False)
    
    # Timestamps
    reviewed_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    suggestion = relationship("AISuggestion", back_populates="reviews")
    admin_user = relationship("User", back_populates="suggestion_reviews")
    
    def __repr__(self):
        return f"<SuggestionReview(id={self.id}, action={self.action}, suggestion_id={self.suggestion_id})>"

# Performance indexes
Index('idx_suggestion_reviews_admin', SuggestionReview.admin_user_id, SuggestionReview.reviewed_at.desc())
Index('idx_suggestion_reviews_action', SuggestionReview.action, SuggestionReview.reviewed_at.desc())
