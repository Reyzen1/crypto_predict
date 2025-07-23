# File: ./backend/app/core/deps.py
# FastAPI dependencies for authentication 

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import security
from app.models import User
from app.repositories import user_repository


# Security scheme for JWT token - FIXED with auto_error=False
security_scheme = HTTPBearer(auto_error=False)


def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from JWT token
    
    Args:
        credentials: JWT token from Authorization header
        db: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    # FIXED: Check if credentials is None
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from credentials
    token = credentials.credentials
    
    # Verify token and get payload
    try:
        payload = security.verify_token(token, token_type="access")
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user ID from token
    user_id: int = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database using your existing repository
    user = user_repository.get(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user_from_token)
) -> User:
    """
    Get current active user (additional validation)
    
    Args:
        current_user: User from token validation
        
    Returns:
        User: Active user
        
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current verified user (email verified)
    
    Args:
        current_user: Active user
        
    Returns:
        User: Verified user
        
    Raises:
        HTTPException: If user email is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User email not verified"
        )
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user optionally (for endpoints that work with/without auth)
    
    FIXED: Properly handles None credentials without raising errors
    
    Args:
        credentials: Optional JWT token
        db: Database session
        
    Returns:
        Optional[User]: User if authenticated, None otherwise
    """
    if credentials is None:
        return None
    
    try:
        # Extract token from credentials
        token = credentials.credentials
        
        # Verify token and get payload
        payload = security.verify_token(token, token_type="access")
        
        # Get user ID from token
        user_id: int = payload.get("user_id")
        if user_id is None:
            return None
        
        # Get user from database using your existing repository
        user = user_repository.get(db, user_id)
        if user is None or not user.is_active:
            return None
        
        return user
        
    except HTTPException:
        # If token verification fails, return None (don't raise error)
        return None
    except Exception:
        # Any other error, return None (don't raise error)
        return None


# Pagination dependency
class PaginationParams:
    """Pagination parameters for list endpoints"""
    
    def __init__(
        self,
        skip: int = 0,
        limit: int = 100
    ):
        self.skip = max(0, skip)  # Ensure skip is not negative
        self.limit = min(max(1, limit), 1000)  # Ensure limit is between 1 and 1000