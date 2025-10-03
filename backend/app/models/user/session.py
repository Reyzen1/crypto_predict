# backend/app/models/user/session.py
# User session model - Authentication session management

from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSON, INET
from sqlalchemy.orm import relationship
from ..base import BaseModel, TimestampMixin


class UserSession(BaseModel, TimestampMixin):
    """
    User session model for authentication and session management
    
    Uses TimestampMixin (both created_at and updated_at) because sessions
    need updated_at for tracking last activity via last_used_at updates
    """
    __tablename__ = 'user_sessions'
    
    # Core session data
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), nullable=True, index=True)
    
    # Device and location tracking
    device_info = Column(JSON, nullable=True)
    ip_address = Column(INET, nullable=True)
    
    # Session status and timing
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    activities = relationship("UserActivity", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"
    
    @property
    def is_expired(self):
        """Check if session is expired"""
        from datetime import datetime, timezone
        return self.expires_at < datetime.now(timezone.utc)
    
    @property
    def is_valid(self):
        """Check if session is valid (active and not expired)"""
        return self.is_active and not self.is_expired
    
    def update_last_used(self):
        """Update the last_used_at timestamp"""
        from datetime import datetime, timezone
        self.last_used_at = datetime.now(timezone.utc)