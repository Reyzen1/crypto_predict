# backend/app/models/user/activity.py
# User activity model - Activity tracking and audit trail

from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSON, INET
from sqlalchemy.orm import relationship
from ..base import BaseModel, CreatedAtMixin


class UserActivity(BaseModel, CreatedAtMixin):
    """
    User activity model for tracking user actions and audit trail
    
    Uses CreatedAtMixin (only created_at) because activities are immutable
    once created - they represent historical events that should not be modified
    """
    __tablename__ = 'user_activities'
    
    # Core tracking fields
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey('user_sessions.id'), nullable=False, index=True)
    
    # Activity classification
    activity_type = Column(String(50), nullable=False, index=True)
    entity_type = Column(String(50), nullable=True, index=True)
    entity_id = Column(Integer, nullable=True, index=True)
    action = Column(String(50), nullable=False, index=True)
    
    # Detailed information
    details = Column(JSON, nullable=True)
    
    # Security and audit information  
    ip_address = Column(INET, nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="activities")
    session = relationship("UserSession", back_populates="activities")
    
    def __repr__(self):
        return f"<UserActivity(id={self.id}, user_id={self.user_id}, type='{self.activity_type}', action='{self.action}')>"
    
    @classmethod
    def log_activity(cls, session, user_id, session_id, activity_type, action, 
                    entity_type=None, entity_id=None, details=None, 
                    ip_address=None, user_agent=None):
        """
        Convenience method to log user activity
        
        Args:
            session: SQLAlchemy session
            user_id: ID of the user performing the action
            session_id: ID of the user's session
            activity_type: Type of activity (login, watchlist_update, ai_interaction, etc.)
            action: Specific action (create, update, delete, view, etc.)
            entity_type: Type of entity being acted upon (watchlist, asset, etc.)
            entity_id: ID of the specific entity
            details: Additional details as JSON
            ip_address: User's IP address
            user_agent: User's browser/device info
        """
        activity = cls(
            user_id=user_id,
            session_id=session_id,
            activity_type=activity_type,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        session.add(activity)
        return activity