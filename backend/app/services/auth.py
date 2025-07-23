# File: backend/app/services/auth.py
# Authentication service with business logic

from typing import Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import User
from app.schemas.user import UserRegister, UserLogin, Token
from app.repositories import user_repository
from app.core.security import security


class AuthService:
    """Authentication service handling user registration, login, and token management"""

    def register_user(self, db: Session, user_data: UserRegister) -> Dict[str, Any]:
        """
        Register a new user
        
        Args:
            db: Database session
            user_data: User registration data
            
        Returns:
            dict: User data and tokens
            
        Raises:
            HTTPException: If email already exists or validation fails
        """
        # Check if user already exists
        existing_user = user_repository.get_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = security.hash_password(user_data.password)
        
        # Create user using your existing repository
        try:
            user = user_repository.create_user(
                db,
                email=user_data.email,
                hashed_password=hashed_password,
                first_name=user_data.first_name,
                last_name=user_data.last_name
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )
        
        # Generate tokens
        token_data = {"user_id": user.id, "email": user.email}
        access_token = security.create_access_token(token_data)
        refresh_token = security.create_refresh_token(token_data)
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "created_at": user.created_at
            },
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    def authenticate_user(self, db: Session, login_data: UserLogin) -> Dict[str, Any]:
        """
        Authenticate user and return tokens
        
        Args:
            db: Database session
            login_data: User login credentials
            
        Returns:
            dict: User data and tokens
            
        Raises:
            HTTPException: If credentials are invalid
        """
        # Get user by email using your existing repository
        user = user_repository.get_by_email(db, login_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not security.verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled"
            )
        
        # Generate tokens
        token_data = {"user_id": user.id, "email": user.email}
        access_token = security.create_access_token(token_data)
        refresh_token = security.create_refresh_token(token_data)
        
        # Update last login time using your existing repository
        user_repository.update(db, db_obj=user, obj_in={"last_login_date": user.updated_at})
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "created_at": user.created_at
            },
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    def refresh_access_token(self, db: Session, refresh_token: str) -> Token:
        """
        Generate new access token from refresh token
        
        Args:
            db: Database session
            refresh_token: Valid refresh token
            
        Returns:
            Token: New access token
            
        Raises:
            HTTPException: If refresh token is invalid
        """
        # Verify refresh token
        try:
            payload = security.verify_token(refresh_token, token_type="refresh")
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user using your existing repository
        user_id = payload.get("user_id")
        user = user_repository.get(db, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Generate new access token
        token_data = {"user_id": user.id, "email": user.email}
        new_access_token = security.create_access_token(token_data)
        
        return Token(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=30 * 60  # 30 minutes in seconds
        )

    def verify_user_email(self, db: Session, user_id: int) -> User:
        """
        Mark user email as verified using your existing repository
        
        Args:
            db: Database session
            user_id: User ID to verify
            
        Returns:
            User: Updated user
            
        Raises:
            HTTPException: If user not found
        """
        user = user_repository.get(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user_repository.verify_user(db, user_id)

    def change_password(
        self, 
        db: Session, 
        user: User, 
        current_password: str, 
        new_password: str
    ) -> bool:
        """
        Change user password
        
        Args:
            db: Database session
            user: Current user
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            bool: True if password changed successfully
            
        Raises:
            HTTPException: If current password is wrong
        """
        # Verify current password
        if not security.verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_hashed_password = security.hash_password(new_password)
        
        # Update password using your existing repository
        user_repository.update(db, db_obj=user, obj_in={"hashed_password": new_hashed_password})
        
        return True


# Global auth service instance
auth_service = AuthService()