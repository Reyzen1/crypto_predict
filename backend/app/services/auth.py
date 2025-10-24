# File: backend/app/services/auth.py
# FIXED Authentication service - Added missing expires_in field

from typing import Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import User
from app.schemas.user import UserRegister, UserLogin, Token
from app.repositories.user.user_repository import UserRepository
from app.core.security import security
import logging

# Custom logger for auth access
logger = logging.getLogger(__name__)

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
        user_repo = UserRepository(db)
        existing_user = user_repo.get_by_email(user_data.email)
        if existing_user:
            detail_text=f"Email already registered: {user_data.email}"
            logger.warning(f"❌ HTTP_400_BAD_REQUEST Registration failed: {detail_text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail_text
            )
        
        # Hash password
        password_hash = security.hash_password(user_data.password)
        
        try:
            user_in = {
                "email": user_data.email.strip().lower(),
                "password_hash": password_hash,
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "is_active": True,
                "is_verified": False,
                "role": "public"  # Set default role based on UserRole enum
            }
            
            # Use the correct method name
            user_repo = UserRepository(db)
            user = user_repo.create_user(user_in)
            
            if not user:
                raise Exception("Failed to create user")
                
        except Exception as e:
            detail_text=f"Failed to create user: {user_data.email}"
            logger.warning(f"❌ HTTP_400_BAD_REQUEST Registration failed: {detail_text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail_text
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
                "is_verified": getattr(user, "is_verified", False),
                "created_at": getattr(user, "created_at", None)
            },
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 30 * 60  
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
        # Get user by email using repository
        user_repo = UserRepository(db)
        user = user_repo.get_by_email(login_data.email)
        if not user:
            detail_text=f"Invalid email or password: {login_data.email}"
            logger.warning(f"🔐 HTTP_401_UNAUTHORIZED: {detail_text}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=detail_text
            )
        
        # Verify password
        if not security.verify_password(login_data.password, user.password_hash):
            detail_text=f"Invalid email or password: {login_data.email}"
            logger.warning(f"🔐 HTTP_401_UNAUTHORIZED: {detail_text}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=detail_text
            )
        
        # Check if user is active
        if not user.is_active:
            detail_text=f"User account is disabled: {login_data.email}"
            logger.warning(f"🔐 HTTP_401_UNAUTHORIZED: {detail_text}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=detail_text
            )
        
        # Generate tokens
        token_data = {"user_id": user.id, "email": user.email}
        access_token = security.create_access_token(token_data)
        refresh_token = security.create_refresh_token(token_data)
        
        # Update last login time using repository method
        try:
            user_repo.update_last_login(user.id)
        except:
            pass  # Ignore last login update errors
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
                "is_verified": getattr(user, "is_verified", False),
                "created_at": getattr(user, "created_at", None)
            },
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 30 * 60
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
            detail_text=f"Invalid refresh token: refresh_token={refresh_token}"
            logger.warning(f"🔐 HTTP_401_UNAUTHORIZED: {detail_text}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=detail_text
            )
        
        # Get user using repository
        user_id = payload.get("user_id")
        user_repo = UserRepository(db)
        user = user_repo.get(user_id)
        if not user or not user.is_active:
            detail_text=f"User not found or inactive: user_id={user_id}"
            logger.warning(f"🔐 HTTP_401_UNAUTHORIZED: {detail_text}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=detail_text
            )

        
        # Generate new access token
        token_data = {"user_id": user.id, "email": user.email}
        new_access_token = security.create_access_token(token_data)
        
        return Token(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=30 * 60
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
        user_repo = UserRepository(db)
        user = user_repo.get(user_id)
        if not user:
            detail_text=f"User not found: user_id={user_id}"
            logger.warning(f"🔐 HTTP_404_NOT_FOUND: {detail_text}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail_text
            )
        
        # Use repository's verify_user method
        success = user_repo.verify_user(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to verify user"
            )
        
        return user_repo.get(user_id)

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
        if not security.verify_password(current_password, user.password_hash):
            detail_text=f"Password is incorrect: {user.email}"
            logger.warning(f"🔐 HTTP_400_BAD_REQUEST: {detail_text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail_text
            )
        
        # Hash new password
        new_password_hash = security.hash_password(new_password)
        
        # Update password using repository
        user_repo = UserRepository(db)
        updates = {"password_hash": new_password_hash}
        result = user_repo.batch_update_users([user.id], updates)
        
        return result['success'] > 0


# Global auth service instance
auth_service = AuthService()