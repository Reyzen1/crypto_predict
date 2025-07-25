# File: backend/app/core/deps.py
# Fixed core dependencies to handle authentication and database properly

from typing import Optional, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError
import redis
from redis import Redis

from app.core.database import get_db
from app.core.config import settings
from app.models import User
from app.repositories import user_repository

# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


def get_redis() -> Generator[Redis, None, None]:
    """
    Get Redis connection
    """
    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        yield redis_client
    except Exception:
        # For testing, return a mock Redis client
        yield None


def get_current_user_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    Extract JWT token from Authorization header
    """
    if not credentials:
        return None
    
    return credentials.credentials


def get_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(get_current_user_token)
) -> User:
    """
    Get current authenticated user (required authentication)
    
    Raises HTTPException if authentication fails
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id: int = payload.get("sub")
        if user_id is None:
            # Try alternative key formats
            user_id = payload.get("user_id")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = user_repository.get(db=db, id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (must be active)
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
    Get current verified user (must be verified)
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    
    return current_user


def get_optional_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(get_current_user_token)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise
    
    This dependency doesn't raise exceptions - used for optional authentication
    """
    if not token:
        return None
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id: int = payload.get("sub")
        if user_id is None:
            # Try alternative key format
            user_id = payload.get("user_id")
            if user_id is None:
                return None
            
    except JWTError:
        return None
    
    # Get user from database
    try:
        user = user_repository.get(db=db, id=user_id)
        return user if user and user.is_active else None
    except Exception:
        return None


def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current superuser (must be superuser)
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return current_user


# Rate limiting dependency
def get_rate_limit_key(
    request
) -> str:
    """
    Generate rate limit key based on client IP or user ID
    """
    # Get client IP for rate limiting
    client_ip = request.client.host
    return f"rate_limit:{client_ip}"


# Pagination dependency
class PaginationParams:
    """
    Pagination parameters dependency
    """
    def __init__(
        self,
        skip: int = 0,
        limit: int = 20
    ):
        self.skip = max(0, skip)  # Ensure skip is not negative
        self.limit = min(max(1, limit), 100)  # Limit between 1 and 100


# Common query parameters
class CommonQueryParams:
    """
    Common query parameters for filtering and sorting
    """
    def __init__(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_desc: bool = False
    ):
        self.skip = max(0, skip)
        self.limit = min(max(1, limit), 100)
        self.search = search
        self.sort_by = sort_by
        self.sort_desc = sort_desc