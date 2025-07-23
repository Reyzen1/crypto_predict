# File: backend/app/api/api_v1/endpoints/auth.py
# Fixed authentication endpoints to handle form data and JSON

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.schemas.user import (
    UserRegister, UserLogin, UserResponse, AuthResponse, TokenResponse
)
from app.schemas.common import SuccessResponse
from app.services.auth import auth_service
from app.models import User

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
) -> Any:
    """
    User registration
    
    Creates a new user account with email and password.
    Returns user data and authentication tokens.
    """
    try:
        return auth_service.register_user(db, user_data)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e) 
        )


@router.post("/login", response_model=AuthResponse)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    User login with OAuth2 form data
    
    Authenticates user with email/password and returns JWT tokens.
    Accepts both form data and JSON.
    """
    try:
        # Create UserLogin from form data
        login_data = UserLogin(
            email=form_data.username,  # OAuth2 uses 'username' field for email
            password=form_data.password
        )
        return auth_service.authenticate_user(db, login_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/login-json", response_model=AuthResponse)
def login_user_json(
    login_data: UserLogin,
    db: Session = Depends(get_db)
) -> Any:
    """
    User login with JSON data
    
    Alternative login endpoint that accepts JSON instead of form data.
    """
    try:
        return auth_service.authenticate_user(db, login_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(
    refresh_token: str = Form(...),
    db: Session = Depends(get_db)
) -> Any:
    """
    Refresh access token
    
    Uses refresh token to generate a new access token.
    """
    try:
        return auth_service.refresh_access_token(db, refresh_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout", response_model=SuccessResponse)
def logout_user(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    User logout
    
    Logout current user. In a real application, you might want to
    invalidate the refresh token or maintain a blacklist.
    """
    return SuccessResponse(
        message="Logout successful",
        data={"user_id": current_user.id}
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user information
    
    Returns the profile information of the currently authenticated user.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )