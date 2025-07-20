# File: backend/app/api/api_v1/endpoints/auth.py
# Authentication API endpoints

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.schemas.user import UserRegister, UserLogin, UserResponse, Token, UserPasswordChange
from app.schemas.common import SuccessResponse
from app.services.auth import auth_service
from app.models import User


router = APIRouter()


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user
    
    Creates a new user account with email and password.
    Returns user data and authentication tokens.
    """
    try:
        result = auth_service.register_user(db, user_data)
        return {
            "message": "User registered successfully",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=dict)
def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db)
) -> Any:
    """
    User login
    
    Authenticate user with email and password.
    Returns user data and authentication tokens.
    """
    try:
        result = auth_service.authenticate_user(db, login_data)
        return {
            "message": "Login successful",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_token: str = Body(..., embed=True),
    db: Session = Depends(get_db)
) -> Any:
    """
    Refresh access token
    
    Generate a new access token using a valid refresh token.
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


@router.post("/change-password", response_model=SuccessResponse)
def change_password(
    password_data: UserPasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Change user password
    
    Change the password for the currently authenticated user.
    Requires current password for security.
    """
    try:
        auth_service.change_password(
            db,
            current_user,
            password_data.current_password,
            password_data.new_password
        )
        return SuccessResponse(
            message="Password changed successfully",
            data={"user_id": current_user.id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.post("/verify-email/{user_id}", response_model=SuccessResponse)
def verify_user_email(
    user_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    Verify user email
    
    Mark a user's email as verified. In a real application,
    this would require a verification token sent via email.
    """
    try:
        user = auth_service.verify_user_email(db, user_id)
        return SuccessResponse(
            message="Email verified successfully",
            data={
                "user_id": user.id,
                "email": user.email,
                "is_verified": user.is_verified
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )