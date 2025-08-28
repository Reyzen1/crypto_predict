# File: backend\app\models\core\user.py
# SQLAlchemy model for user data

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy_utils import IPAddressType

from app.core.database import Base
from sqlalchemy import DECIMAL

class User(Base):
    """
    Core user model for authentication and authorization
    Enhanced from Phase 1 with role management for Phase 2
    """
    __tablename__ = "users"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile information
    first_name = Column(String(50))
    last_name = Column(String(50))
    
    # Role-based access control (Enhanced for Phase 2)
    role = Column(String(20), nullable=False, default='casual')  # admin, professional, casual
    
    # Status flags
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    is_superuser = Column(Boolean, nullable=False, default=False)
    
    # User preferences (TEXT for compatibility)
    preferences = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    predictions = relationship("Prediction", back_populates="user", lazy="dynamic")
    watchlists = relationship("Watchlist", back_populates="user", lazy="dynamic")
    activities = relationship("UserActivity", back_populates="user", lazy="dynamic")
    notifications = relationship("Notification", back_populates="user", lazy="dynamic")
    risk_profiles = relationship("RiskManagement", back_populates="user", uselist=False)
    ai_models_created = relationship("AIModel", back_populates="creator", lazy="dynamic")
    suggestion_reviews = relationship("SuggestionReview", back_populates="admin_user", lazy="dynamic")
    signal_executions = relationship("SignalExecution", back_populates="user", lazy="dynamic")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

class UserActivity(Base):
    """
    Track user activities for analytics and audit purposes
    Enhanced with all database fields
    """
    __tablename__ = "user_activities"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # User reference
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Activity details
    activity_type = Column(String(50), nullable=False, index=True)
    activity_category = Column(String(30), default='general')
    activity_data = Column(JSON, default=dict)
    
    # Request information
    request_path = Column(String(500))
    request_method = Column(String(10))
    response_status = Column(Integer)
    response_time_ms = Column(DECIMAL(10, 2))
    
    # Session information
    session_id = Column(String(100))
    ip_address = Column(IPAddressType, nullable=True)  # ✅ cross-database
    user_agent = Column(Text)
    
    # Device information
    device_type = Column(String(20))
    browser = Column(String(50))
    location_country = Column(String(2))
    
    # Execution status
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    additional_data = Column(JSON, default=dict)
    
    # Timestamp
    activity_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="activities")
    
    def __repr__(self):
        return f"<UserActivity(id={self.id}, user_id={self.user_id}, type={self.activity_type})>"

# Performance indexes
Index('idx_users_role', User.role, User.is_active)
Index('idx_users_role_active', User.role, User.is_active, User.last_login.desc())
Index('idx_user_activities_user_time', UserActivity.user_id, UserActivity.activity_time.desc())
Index('idx_user_activities_type', UserActivity.activity_type, UserActivity.activity_time.desc())
Index('idx_user_activities_session', UserActivity.session_id, UserActivity.activity_time.desc())
