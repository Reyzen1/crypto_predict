# backend/app/models/user/user.py
# User model - Core user management and authentication

from sqlalchemy import Column, String, Boolean, Integer, Text, Numeric, DateTime, ForeignKey, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSON, INET
from sqlalchemy.orm import relationship
from ..base import BaseModel, TimestampMixin
from ..mixins import ActiveMixin, SoftDeleteMixin, UserPreferencesMixin
from ..enums import UserRole


class User(BaseModel, TimestampMixin, ActiveMixin, SoftDeleteMixin, UserPreferencesMixin):
    """
    User model with complete user management functionality
    
    Combines multiple mixins for comprehensive user tracking:
    - TimestampMixin: created_at, updated_at
    - ActiveMixin: is_active
    - SoftDeleteMixin: deleted_at, deleted_by
    - UserPreferencesMixin: preferences, timezone, language
    """
    __tablename__ = 'users'
    
    # Basic Information
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    role = Column(String(20), nullable=False, default=UserRole.PUBLIC)
    
    # Verification & Security
    is_verified = Column(Boolean, nullable=False, default=False)
    login_count = Column(Integer, nullable=False, default=0)
    bio = Column(Text, nullable=True)
    profile_picture_url = Column(String(500), nullable=True)
    
    # Password Reset
    reset_password_token = Column(String(255), nullable=True)
    reset_password_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Email Verification  
    email_verification_token = Column(String(255), nullable=True)
    email_verification_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Security & Login Tracking
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    lockout_expires = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Referral System
    referral_code = Column(String(50), unique=True, nullable=True)
    referred_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    referral_count = Column(Integer, nullable=False, default=0)
    
    # Monetization & Subscription
    account_balance = Column(Numeric(15,2), nullable=False, default=0)
    subscription_plan = Column(String(20), nullable=False, default='free')
    subscription_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Admin Notes
    notes = Column(Text, nullable=True)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    activities = relationship("UserActivity", back_populates="user", cascade="all, delete-orphan")
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    watchlists = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    
    # Self-referential relationship for referrals
    referrer = relationship("User", remote_side=[id], backref="referred_users")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
    
    @property
    def full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.email.split('@')[0]
    
    @property
    def is_locked(self):
        """Check if user account is locked"""
        from datetime import datetime, timezone
        return (self.lockout_expires and 
                self.lockout_expires > datetime.now(timezone.utc))
    
    @property
    def is_subscription_active(self):
        """Check if user's subscription is active"""
        if self.subscription_plan == 'free':
            return True
        from datetime import datetime, timezone
        return (self.subscription_expires_at and 
                self.subscription_expires_at > datetime.now(timezone.utc))
    
    # Constraints and Indexes
    __table_args__ = (
        # Unique constraints
        UniqueConstraint('email', name='unique_user_email'),
        UniqueConstraint('referral_code', name='unique_referral_code'),
        
        # Check constraints
        CheckConstraint("role IN ('admin', 'premium', 'public')", name='chk_user_role_valid'),
        CheckConstraint('failed_login_attempts >= 0', name='chk_failed_attempts_positive'),
        CheckConstraint('referral_count >= 0', name='chk_referral_count_positive'),
        CheckConstraint('account_balance >= 0', name='chk_account_balance_positive'),
        CheckConstraint('login_count >= 0', name='chk_login_count_positive'),
        CheckConstraint("subscription_plan IN ('free', 'basic', 'premium', 'enterprise')", name='chk_subscription_plan_valid'),
        
        # Performance indexes
        Index('idx_user_email', 'email'),
        Index('idx_user_role', 'role'),
        Index('idx_user_active', 'is_active'),
        Index('idx_user_verified', 'is_verified'),
        Index('idx_user_created_at', 'created_at'),
        Index('idx_user_last_login', 'last_login'),
        Index('idx_user_subscription', 'subscription_plan', 'subscription_expires_at'),
        Index('idx_user_referral_code', 'referral_code'),
        Index('idx_user_referred_by', 'referred_by'),
        Index('idx_user_deleted', 'deleted_at'),
        Index('idx_user_lockout', 'lockout_expires'),
        Index('idx_user_reset_token', 'reset_password_token'),
        Index('idx_user_verification_token', 'email_verification_token'),
    )
    
    @classmethod
    def get_by_email(cls, session, email: str):
        """Get user by email address"""
        return session.query(cls).filter(cls.email == email).first()
    
    @classmethod
    def get_active_users(cls, session):
        """Get all active users"""
        return session.query(cls).filter(
            cls.is_active == True,
            cls.deleted_at.is_(None)
        ).all()
    
    @classmethod
    def get_by_referral_code(cls, session, referral_code: str):
        """Get user by referral code"""
        return session.query(cls).filter(
            cls.referral_code == referral_code
        ).first()
    
    @classmethod
    def get_premium_users(cls, session):
        """Get users with active premium subscriptions"""
        from datetime import datetime, timezone
        return session.query(cls).filter(
            cls.subscription_plan.in_(['basic', 'premium', 'enterprise']),
            cls.subscription_expires_at > datetime.now(timezone.utc)
        ).all()
    
    def increment_login_count(self):
        """Increment login count and update last login"""
        from datetime import datetime, timezone
        self.login_count += 1
        self.last_login = datetime.now(timezone.utc)
        self.failed_login_attempts = 0  # Reset on successful login
    
    def increment_failed_login(self):
        """Increment failed login attempts"""
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            from datetime import datetime, timezone, timedelta
            self.lockout_expires = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    def unlock_account(self):
        """Unlock user account"""
        self.failed_login_attempts = 0
        self.lockout_expires = None
    
    def generate_referral_code(self):
        """Generate unique referral code"""
        import string
        import random
        
        if not self.referral_code:
            # Generate 8-character alphanumeric code
            characters = string.ascii_uppercase + string.digits
            self.referral_code = ''.join(random.choice(characters) for _ in range(8))
    
    def add_referral(self):
        """Increment referral count"""
        self.referral_count += 1
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'bio': self.bio,
            'profile_picture_url': self.profile_picture_url,
            'login_count': self.login_count,
            'referral_code': self.referral_code,
            'referral_count': self.referral_count,
            'subscription_plan': self.subscription_plan,
            'is_subscription_active': self.is_subscription_active,
            'preferences': self.preferences,
            'timezone': self.timezone,
            'language': self.language,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        if include_sensitive:
            data.update({
                'account_balance': float(self.account_balance) if self.account_balance else 0,
                'subscription_expires_at': self.subscription_expires_at.isoformat() if self.subscription_expires_at else None,
                'failed_login_attempts': self.failed_login_attempts,
                'is_locked': self.is_locked,
                'notes': self.notes
            })
        
        return data