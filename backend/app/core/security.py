# File: backend/app/core/security.py
# Security utilities for password hashing and JWT token management

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import secrets

from app.core.config import settings


class SecurityManager:
    """Security manager for password hashing and JWT token operations"""
    
    def __init__(self):
        # Setup bcrypt for password hashing
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # JWT settings
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    def hash_password(self, password: str) -> str:
        """Hash a plain password"""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, password_hash)

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token - FIXED UTC usage"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=self.algorithm)

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token (7 days) - FIXED UTC usage"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=7)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=self.algorithm)

    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token - FIXED UTC usage"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}"
                )
            
            # Check expiration - FIXED: Use timezone-aware datetime
            exp = payload.get("exp")
            if exp is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has no expiration"
                )
            
            # Convert timestamp to timezone-aware datetime
            exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
            if exp_datetime < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
            
            return payload
            
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

    def generate_reset_token(self) -> str:
        """Generate secure token for password reset"""
        return secrets.token_urlsafe(32)


# Global security instance
security = SecurityManager()


# Additional standalone functions for backward compatibility
def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Standalone function to create access token (for backward compatibility) - FIXED UTC usage
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Standalone function to verify password (for backward compatibility)"""
    return security.verify_password(plain_password, password_hash)


def get_password_hash(password: str) -> str:
    """Standalone function to hash password (for backward compatibility)"""
    return security.hash_password(password)