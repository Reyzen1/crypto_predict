# File: ./backend/app/schemas/user.py
# User-related Pydantic schemas for authentication and user management

from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, validator
from datetime import datetime
import re

from app.schemas.common import BaseSchema


class UserBase(BaseSchema):
    """Base user schema with common fields"""
    
    email: EmailStr = Field(description="User's email address")
    first_name: Optional[str] = Field(
        default=None, 
        min_length=1, 
        max_length=50, 
        description="User's first name"
    )
    last_name: Optional[str] = Field(
        default=None, 
        min_length=1, 
        max_length=50, 
        description="User's last name"
    )


class UserRegister(UserBase):
    """Schema for user registration"""
    
    password: str = Field(
        min_length=8, 
        max_length=100, 
        description="User's password (min 8 characters)"
    )
    confirm_password: str = Field(
        min_length=8, 
        max_length=100, 
        description="Password confirmation"
    )
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        # Check for at least one digit
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Validate that password and confirm_password match"""
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    
    email: EmailStr = Field(description="User's email address")
    password: str = Field(min_length=1, description="User's password")


class UserUpdate(BaseModel):
    """Schema for user profile updates"""
    
    first_name: Optional[str] = Field(
        default=None, 
        min_length=1, 
        max_length=50, 
        description="User's first name"
    )
    last_name: Optional[str] = Field(
        default=None, 
        min_length=1, 
        max_length=50, 
        description="User's last name"
    )


class UserPasswordChange(BaseModel):
    """Schema for password change"""
    
    current_password: str = Field(min_length=1, description="Current password")
    new_password: str = Field(
        min_length=8, 
        max_length=100, 
        description="New password (min 8 characters)"
    )
    confirm_new_password: str = Field(
        min_length=8, 
        max_length=100, 
        description="New password confirmation"
    )
    
    @validator('new_password')
    def validate_new_password_strength(cls, v):
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        # Check for at least one digit
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        return v
    
    @validator('confirm_new_password')
    def new_passwords_match(cls, v, values):
        """Validate that new_password and confirm_new_password match"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('New passwords do not match')
        return v


class UserResponse(UserBase):
    """Schema for user data in API responses"""
    
    id: int = Field(description="User's unique identifier")
    is_active: bool = Field(description="Whether the user account is active")
    is_verified: bool = Field(description="Whether the user email is verified")
    created_at: datetime = Field(description="Account creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class UserSummary(BaseSchema):
    """Schema for user summary (minimal info)"""
    
    id: int = Field(description="User's unique identifier")
    email: EmailStr = Field(description="User's email address")
    first_name: Optional[str] = Field(description="User's first name")
    last_name: Optional[str] = Field(description="User's last name")
    is_active: bool = Field(description="Whether the user account is active")
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts) if parts else self.email


class UserWithStats(UserResponse):
    """Schema for user data with statistics"""
    
    total_predictions: int = Field(default=0, description="Total number of predictions made")
    total_portfolios: int = Field(default=0, description="Total number of portfolio entries")
    last_prediction_date: Optional[datetime] = Field(
        default=None, 
        description="Date of last prediction"
    )
    last_login_date: Optional[datetime] = Field(
        default=None, 
        description="Date of last login"
    )


class Token(BaseModel):
    """Schema for JWT tokens"""
    
    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Token expiration time in seconds")


class TokenData(BaseModel):
    """Schema for token payload data"""
    
    user_id: int = Field(description="User ID from token")
    email: str = Field(description="User email from token")
    exp: int = Field(description="Token expiration timestamp")


class UserPreferences(BaseModel):
    """Schema for user preferences and settings"""
    
    email_notifications: bool = Field(default=True, description="Enable email notifications")
    push_notifications: bool = Field(default=True, description="Enable push notifications")
    default_currency: str = Field(default="USD", description="Default currency for display")
    timezone: str = Field(default="UTC", description="User's timezone")
    theme: str = Field(default="light", description="UI theme preference")
    
    @validator('default_currency')
    def validate_currency(cls, v):
        """Validate currency code"""
        valid_currencies = ["USD", "EUR", "GBP", "JPY", "BTC", "ETH"]
        if v.upper() not in valid_currencies:
            raise ValueError(f'Currency must be one of: {", ".join(valid_currencies)}')
        return v.upper()
    
    @validator('theme')
    def validate_theme(cls, v):
        """Validate theme option"""
        valid_themes = ["light", "dark", "auto"]
        if v.lower() not in valid_themes:
            raise ValueError(f'Theme must be one of: {", ".join(valid_themes)}')
        return v.lower()