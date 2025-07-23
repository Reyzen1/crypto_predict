# File: backend/app/schemas/user.py
# Fixed user schemas to match database schema

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.schemas.common import BaseSchema


class UserBase(BaseSchema):
    """Base user schema with common fields"""
    
    email: EmailStr = Field(description="User email address")
    first_name: Optional[str] = Field(default=None, max_length=100, description="First name")
    last_name: Optional[str] = Field(default=None, max_length=100, description="Last name")


class UserRegister(BaseSchema):
    """Schema for user registration"""
    
    email: EmailStr = Field(description="User email address")
    password: str = Field(min_length=8, max_length=100, description="User password")
    confirm_password: str = Field(min_length=8, max_length=100, description="Password confirmation")
    first_name: Optional[str] = Field(default=None, max_length=100, description="First name")
    last_name: Optional[str] = Field(default=None, max_length=100, description="Last name")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        return v
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        """Ensure passwords match"""
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v


class UserLogin(BaseSchema):
    """Schema for user login - using email as username"""
    
    email: EmailStr = Field(description="User email address")
    password: str = Field(description="User password")


class UserUpdate(BaseSchema):
    """Schema for updating user profile"""
    
    first_name: Optional[str] = Field(default=None, max_length=100, description="First name")
    last_name: Optional[str] = Field(default=None, max_length=100, description="Last name")
    preferences: Optional[str] = Field(default=None, description="User preferences as JSON string")


class UserPasswordChange(BaseSchema):
    """Schema for changing user password"""
    
    current_password: str = Field(description="Current password")
    new_password: str = Field(min_length=8, description="New password")
    confirm_new_password: str = Field(min_length=8, description="New password confirmation")
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        return v
    
    @field_validator('confirm_new_password')
    @classmethod
    def passwords_match(cls, v, info):
        """Ensure passwords match"""
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v


class UserResponse(UserBase):
    """Schema for user data in API responses"""
    
    model_config = {"from_attributes": True}
    
    id: int = Field(description="Unique identifier")
    is_active: bool = Field(description="Account active status")
    is_verified: bool = Field(description="Email verification status")
    created_at: datetime = Field(description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    
    @property
    def username(self) -> str:
        """Username property for backward compatibility"""
        return self.email


class UserProfile(UserResponse):
    """Extended user profile schema"""
    
    last_login: Optional[datetime] = Field(default=None, description="Last login timestamp")
    preferences: Optional[str] = Field(default=None, description="User preferences")
    
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
    last_prediction_date: Optional[datetime] = Field(default=None, description="Date of last prediction")
    last_login_date: Optional[datetime] = Field(default=None, description="Date of last login")


class UserSummary(BaseSchema):
    """Brief user summary for lists"""
    
    id: int = Field(description="User ID")
    email: EmailStr = Field(description="User email")
    first_name: Optional[str] = Field(default=None, description="First name")
    last_name: Optional[str] = Field(default=None, description="Last name")
    is_active: bool = Field(description="Account active status")


class TokenResponse(BaseSchema):
    """Schema for authentication token response"""
    
    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Token expiration time in seconds")


class AuthResponse(BaseSchema):
    """Schema for authentication response with user data"""
    
    user: UserResponse = Field(description="User information")
    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Token expiration time in seconds")


class TokenRefresh(BaseSchema):
    """Schema for token refresh request"""
    
    refresh_token: str = Field(description="Refresh token")


class UserListResponse(BaseSchema):
    """Schema for paginated user list response"""
    
    users: list[UserSummary] = Field(description="List of users")
    total: int = Field(description="Total number of users")
    page: int = Field(description="Current page number")
    per_page: int = Field(description="Items per page")


class UserStats(BaseSchema):
    """Schema for user statistics"""
    
    total_users: int = Field(description="Total number of users")
    active_users: int = Field(description="Number of active users")
    verified_users: int = Field(description="Number of verified users")
    new_users_today: int = Field(description="New users today")
    new_users_this_week: int = Field(description="New users this week")

class Token(BaseModel):
    """Schema for JWT tokens"""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Token expiration time in seconds")