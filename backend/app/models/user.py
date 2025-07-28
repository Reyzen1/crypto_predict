# File: backend/app/models/user.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from passlib.context import CryptContext
from app.core.database import Base

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    """User model for authentication and user management"""
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # User credentials
    email = Column(String(255), unique=True, index=True, nullable=False)
    # username = Column(String(50), unique=True, index=True, nullable=False)  # COMMENTED OUT - تعلیق شده
    password_hash = Column(String(255), nullable=False)
    
    # User information
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    
    # User status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # User preferences (JSON stored as text for MVP)
    preferences = Column(Text, nullable=True)  # JSON string
    
    # Relationships
    predictions = relationship("Prediction", back_populates="user")
    
    def verify_password(self, plain_password: str) -> bool:
        """Verify a plain password against the hashed password"""
        return pwd_context.verify(plain_password, self.password_hash)
    
    def set_password(self, plain_password: str) -> None:
        """Set the user's password (hashed)"""
        self.password_hash = pwd_context.hash(plain_password)
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.email
    
    @property
    def username(self) -> str:
        """Username property for backward compatibility - use email"""
        return self.email
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"