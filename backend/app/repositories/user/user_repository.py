# backend/app/repositories/user/user.py
# Repository for user management

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, timedelta
import logging

from ..base_repository import BaseRepository
from app.models.user.user import User

# Setup logger
logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """
    Repository for user management with authentication and profile operations
    """
    
    def __init__(self, db: Session):
        super().__init__(User, db)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        try:
            if not email or not email.strip():
                return None
            return self.db.query(User).filter(User.email == email.strip().lower()).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by email {email}: {str(e)}")
            return None
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username - Not available since User model doesn't have username field"""
        logger.warning("get_by_username called but User model doesn't have username field")
        return None
    
    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get active users with pagination"""
        try:
            if skip < 0 or limit <= 0 or limit > 1000:
                return []
            return self.db.query(User).filter(
                User.is_active == True,
                User.is_deleted == False
            ).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting active users: {str(e)}")
            return []
    
    def get_verified_users(self) -> List[User]:
        """Get verified users"""
        try:
            return self.db.query(User).filter(
                User.is_verified == True,
                User.is_active == True,
                User.is_deleted == False
            ).order_by(User.created_at.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting verified users: {str(e)}")
            return []
    
    def search_users(self, query: str, limit: int = 20) -> List[User]:
        """Search users by name, email, or username"""
        try:
            if not query or not query.strip() or len(query.strip()) < 2:
                return []
            if limit <= 0 or limit > 100:
                limit = 20
            
            search_term = query.strip()
            return self.db.query(User).filter(
                User.is_deleted == False,
                or_(
                    User.first_name.ilike(f'%{search_term}%'),
                    User.last_name.ilike(f'%{search_term}%'),
                    User.email.ilike(f'%{search_term}%')
                )
            ).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error searching users with query '{query}': {str(e)}")
            return []
    
    def get_users_by_role(self, role: str) -> List[User]:
        """Get users by role"""
        try:
            if not role or not role.strip():
                return []
            return self.db.query(User).filter(
                User.role == role.strip(),
                User.is_active == True,
                User.is_deleted == False
            ).order_by(User.created_at.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting users by role '{role}': {str(e)}")
            return []
    
    def get_recent_registrations(self, days: int = 30) -> List[User]:
        """Get users registered in recent days"""
        try:
            if days <= 0 or days > 365:
                days = 30
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            return self.db.query(User).filter(
                User.created_at >= cutoff_date,
                User.is_deleted == False
            ).order_by(User.created_at.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting recent registrations for {days} days: {str(e)}")
            return []
    
    def get_inactive_users(self, days: int = 90) -> List[User]:
        """Get users inactive for specified days"""
        try:
            if days <= 0 or days > 1095:  # Max 3 years
                days = 90
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            return self.db.query(User).filter(
                or_(
                    User.last_login < cutoff_date,
                    User.last_login.is_(None)
                ),
                User.is_active == True,
                User.is_deleted == False
            ).order_by(User.last_login.asc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting inactive users for {days} days: {str(e)}")
            return []
    
    def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp"""
        try:
            if not user_id or user_id <= 0:
                return False
                
            user = self.get(user_id)
            if not user or user.is_deleted:
                return False
            
            user.last_login = datetime.utcnow()
            user.login_count = (user.login_count or 0) + 1
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error updating last login for user {user_id}: {str(e)}")
            self.db.rollback()
            return False
    
    def update_preferences(self, user_id: int, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        try:
            if not user_id or user_id <= 0 or not isinstance(preferences, dict):
                return False
                
            user = self.get(user_id)
            if not user or user.is_deleted:
                return False
            
            if not user.preferences:
                user.preferences = {}
            
            # Validate preferences data
            if len(str(preferences)) > 10000:  # Limit size
                logger.warning(f"Preferences data too large for user {user_id}")
                return False
            
            user.preferences.update(preferences)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error updating preferences for user {user_id}: {str(e)}")
            self.db.rollback()
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating preferences for user {user_id}: {str(e)}")
            return False
    
    def soft_delete_user(self, user_id: int, reason: str = None) -> bool:
        """Soft delete a user"""
        try:
            if not user_id or user_id <= 0:
                return False
                
            user = self.get(user_id)
            if not user or user.is_deleted:
                return False
            
            user.is_deleted = True
            user.deleted_at = datetime.utcnow()
            user.is_active = False
            
            if reason and reason.strip():
                if not user.metadata:
                    user.metadata = {}
                user.metadata['deletion_reason'] = reason.strip()[:500]  # Limit length
                user.metadata['deleted_by'] = 'system'  # Could be passed as parameter
            
            self.db.commit()
            logger.info(f"User {user_id} soft deleted. Reason: {reason}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error soft deleting user {user_id}: {str(e)}")
            self.db.rollback()
            return False
    
    def verify_user(self, user_id: int) -> bool:
        """Verify a user account"""
        try:
            if not user_id or user_id <= 0:
                return False
                
            user = self.get(user_id)
            if not user or user.is_deleted or user.is_verified:
                return False
            
            user.is_verified = True
            # Note: email_verified_at field doesn't exist in User model
            self.db.commit()
            logger.info(f"User {user_id} verified successfully")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error verifying user {user_id}: {str(e)}")
            self.db.rollback()
            return False
    
    def deactivate_user(self, user_id: int, reason: str = None) -> bool:
        """Deactivate a user account"""
        try:
            if not user_id or user_id <= 0:
                return False
                
            user = self.get(user_id)
            if not user or user.is_deleted or not user.is_active:
                return False
            
            user.is_active = False
            
            if reason and reason.strip():
                if not user.metadata:
                    user.metadata = {}
                user.metadata['deactivation_reason'] = reason.strip()[:500]
                user.metadata['deactivated_at'] = datetime.utcnow().isoformat()
                user.metadata['deactivated_by'] = 'system'
            
            self.db.commit()
            logger.info(f"User {user_id} deactivated. Reason: {reason}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error deactivating user {user_id}: {str(e)}")
            self.db.rollback()
            return False
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            total_users = self.db.query(func.count(User.id)).filter(
                User.is_deleted == False
            ).scalar() or 0
            
            active_users = self.db.query(func.count(User.id)).filter(
                User.is_active == True,
                User.is_deleted == False
            ).scalar() or 0
            
            verified_users = self.db.query(func.count(User.id)).filter(
                User.is_verified == True,
                User.is_deleted == False
            ).scalar() or 0
            
            recent_logins = self.db.query(func.count(User.id)).filter(
                User.last_login >= datetime.utcnow() - timedelta(days=30),
                User.is_deleted == False
            ).scalar() or 0
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'verified_users': verified_users,
                'recent_active_users': recent_logins,
                'verification_rate': round((verified_users / total_users * 100) if total_users > 0 else 0, 2),
                'activity_rate': round((recent_logins / active_users * 100) if active_users > 0 else 0, 2)
            }
        except SQLAlchemyError as e:
            logger.error(f"Error getting user statistics: {str(e)}")
            return {
                'total_users': 0,
                'active_users': 0,
                'verified_users': 0,
                'recent_active_users': 0,
                'verification_rate': 0,
                'activity_rate': 0
            }
    
    def create_user(self, user_data: Dict[str, Any]) -> Optional[User]:
        """Create user with comprehensive error handling"""
        try:
            # Validate required fields
            required_fields = ['email']
            for field in required_fields:
                if not user_data.get(field) or not user_data[field].strip():
                    logger.warning(f"Missing required field: {field}")
                    return None
            
            # Check for existing user
            existing_email = self.get_by_email(user_data['email'])
            if existing_email:
                logger.warning(f"User with email {user_data['email']} already exists")
                return None
            
            # Username check removed since User model doesn't have username field
            
            # Create new user
            user = User(**user_data)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"User created successfully: {user.email}")
            return user
            
        except IntegrityError as e:
            logger.error(f"Integrity error creating user: {str(e)}")
            self.db.rollback()
            return None
        except SQLAlchemyError as e:
            logger.error(f"Database error creating user: {str(e)}")
            self.db.rollback()
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating user: {str(e)}")
            self.db.rollback()
            return None
    
    def batch_update_users(self, user_ids: List[int], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Batch update multiple users with error tracking"""
        if not user_ids or not updates:
            return {'success': 0, 'failed': 0, 'errors': []}
        
        success_count = 0
        failed_count = 0
        errors = []
        
        for user_id in user_ids:
            try:
                user = self.get(user_id)
                if not user or user.is_deleted:
                    failed_count += 1
                    errors.append(f"User {user_id} not found or deleted")
                    continue
                
                # Apply updates
                for key, value in updates.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                
                self.db.commit()
                success_count += 1
                
            except SQLAlchemyError as e:
                logger.error(f"Error updating user {user_id}: {str(e)}")
                self.db.rollback()
                failed_count += 1
                errors.append(f"User {user_id}: {str(e)}")
        
        return {
            'success': success_count,
            'failed': failed_count,
            'errors': errors
        }
    
    def validate_user_data(self, user_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate user data and return validation errors"""
        errors = {}
        
        # Email validation
        email = user_data.get('email', '')
        if not email or not email.strip():
            errors.setdefault('email', []).append('Email is required')
        elif '@' not in email or '.' not in email.split('@')[-1]:
            errors.setdefault('email', []).append('Invalid email format')
        elif len(email) > 255:
            errors.setdefault('email', []).append('Email too long (max 255 characters)')
        
        # Username validation removed since User model doesn't have username field
        
        # Password validation (if provided)
        password = user_data.get('password', '')
        if password and len(password) < 8:
            errors.setdefault('password', []).append('Password must be at least 8 characters')
        
        return errors
