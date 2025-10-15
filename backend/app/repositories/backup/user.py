# File: ./backend/app/repositories/user.py
# User repository with specialized user operations

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import User
from backend.app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User, dict, dict]):
    """
    User repository with specialized operations for user management
    """

    def __init__(self):
        super().__init__(User)

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email address"""
        return db.query(User).filter(User.email == email).first()

    def get_active_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all active users"""
        return (
            db.query(User)
            .filter(User.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_user(
        self, 
        db: Session, 
        *, 
        email: str, 
        password_hash: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        is_active: bool = True,
        is_verified: bool = False
    ) -> User:
        """Create a new user with validation"""
        # Check if email already exists
        existing_user = self.get_by_email(db, email)
        if existing_user:
            raise ValueError(f"User with email {email} already exists")
        
        user_data = {
            "email": email,
            "password_hash": password_hash,
            "first_name": first_name,
            "last_name": last_name,
            "is_active": is_active,
            "is_verified": is_verified
        }
        
        return self.create(db, obj_in=user_data)

    def verify_user(self, db: Session, user_id: int) -> Optional[User]:
        """Mark user as verified"""
        user = self.get(db, user_id)
        if user:
            return self.update(db, db_obj=user, obj_in={"is_verified": True})
        return None

    def count_active_users(self, db: Session) -> int:
        """Count total number of active users"""
        return db.query(User).filter(User.is_active == True).count()

    def search_users(self, db: Session, search_term: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Search users by email, first name, or last name"""
        return (
            db.query(User)
            .filter(
                User.email.ilike(f"%{search_term}%") |
                User.first_name.ilike(f"%{search_term}%") |
                User.last_name.ilike(f"%{search_term}%")
            )
            .offset(skip)
            .limit(limit)
            .all()
        )


# Create global instance
user_repository = UserRepository()
