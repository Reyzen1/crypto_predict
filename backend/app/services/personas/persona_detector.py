# File: backend/app/services/personas/persona_detector.py
# Persona Detection Service 
# Compatible with existing User model and database structure

from enum import Enum
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from app.models import User
from app.core.database import get_db
import logging

logger = logging.getLogger(__name__)

class PersonaType(Enum):
    """
    User persona types based on 01_User_Personas.md design document
    """
    ADMIN = "admin"           # محمدرضا - 35-45 years old, System Manager
    PROFESSIONAL = "professional"  # سارا - 28-40 years old, Professional Trader  
    CASUAL = "casual"        # علی - 25-35 years old, Casual Investor

class PersonaDetector:
    """
    Automatic persona detection service based on user behavior and profile
    Compatible with existing User model from Phase 1
    
    Detection Logic:
    - ADMIN: is_superuser=True OR specific behavior patterns
    - PROFESSIONAL: High activity + advanced feature usage  
    - CASUAL: Default for regular users with basic usage
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    async def detect_persona(self, user: User) -> PersonaType:
        """
        Detect user persona based on existing user data and behavior
        
        Args:
            user: User model instance from existing database
            
        Returns:
            PersonaType: Detected persona type
        """
        try:
            # Admin Detection (محمدرضا profile from design docs)
            if await self._is_admin_persona(user):
                logger.info(f"User {user.id} detected as ADMIN persona")
                return PersonaType.ADMIN
                
            # Professional Detection (سارا profile from design docs)  
            elif await self._is_professional_persona(user):
                logger.info(f"User {user.id} detected as PROFESSIONAL persona")
                return PersonaType.PROFESSIONAL
                
            # Default to Casual (علی profile from design docs)
            else:
                logger.info(f"User {user.id} detected as CASUAL persona")
                return PersonaType.CASUAL
                
        except Exception as e:
            logger.error(f"Error detecting persona for user {user.id}: {str(e)}")
            # Default to casual on error
            return PersonaType.CASUAL
    
    async def _is_admin_persona(self, user: User) -> bool:
        """
        Admin Detection Logic based on existing User model fields
        
        Criteria:
        - is_superuser = True (existing field)
        - High system management activity
        - Admin-specific preferences set
        """
        # Direct admin flag check (existing field)
        if user.is_superuser:
            return True
            
        # Check admin-specific preferences (existing preferences field)
        if user.preferences and isinstance(user.preferences, dict):
            if user.preferences.get('role') == 'admin':
                return True
            if user.preferences.get('admin_features_enabled', False):
                return True
        
        # Check behavioral patterns using existing database
        admin_behavior_score = await self._calculate_admin_behavior_score(user)
        return admin_behavior_score >= 0.7  # 70% threshold for admin behavior
    
    async def _is_professional_persona(self, user: User) -> bool:
        """
        Professional Detection Logic based on user activity patterns
        
        Criteria:
        - High frequency login (>10 times per week)
        - Advanced features usage (from preferences)
        - Multiple predictions made
        """
        # Check professional preferences
        if user.preferences and isinstance(user.preferences, dict):
            if user.preferences.get('user_type') == 'professional':
                return True
            if user.preferences.get('trading_experience', 0) >= 3:  # 3+ years
                return True
        
        # Check activity patterns
        professional_behavior_score = await self._calculate_professional_behavior_score(user)
        return professional_behavior_score >= 0.6  # 60% threshold
    
    async def _calculate_admin_behavior_score(self, user: User) -> float:
        """
        Calculate admin behavior score based on database activity
        Uses existing Prediction model to assess system management behavior
        """
        try:
            # Count predictions made by user (admin users typically make fewer predictions)
            user_predictions = self.db.query(
                text("SELECT COUNT(*) as count FROM predictions WHERE user_id = :user_id")
            ).params(user_id=user.id).fetchone()
            
            prediction_count = user_predictions.count if user_predictions else 0
            
            # Admin scoring logic
            score = 0.0
            
            # Superuser flag gets high score
            if user.is_superuser:
                score += 0.8
            
            # Account age (admins typically have older accounts)
            if user.created_at:
                account_age_days = (datetime.utcnow() - user.created_at).days
                if account_age_days > 90:  # 3+ months old
                    score += 0.2
            
            # Moderate prediction activity (admins don't trade much, they manage)
            if 1 <= prediction_count <= 10:
                score += 0.1
            
            return min(score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Error calculating admin behavior score: {str(e)}")
            return 0.0
    
    async def _calculate_professional_behavior_score(self, user: User) -> float:
        """
        Calculate professional behavior score based on database activity
        """
        try:
            score = 0.0
            
            # High prediction activity indicates professional usage
            user_predictions = self.db.query(
                text("SELECT COUNT(*) as count FROM predictions WHERE user_id = :user_id")
            ).params(user_id=user.id).fetchone()
            
            prediction_count = user_predictions.count if user_predictions else 0
            
            # Professional scoring logic
            if prediction_count > 20:  # High activity
                score += 0.4
            elif prediction_count > 10:  # Moderate activity  
                score += 0.2
            
            # Recent activity (professionals are active users)
            if user.last_login:
                days_since_login = (datetime.utcnow() - user.last_login).days
                if days_since_login < 7:  # Active in last week
                    score += 0.3
                elif days_since_login < 30:  # Active in last month
                    score += 0.1
            
            # Account verification (professionals tend to verify)
            if user.is_verified:
                score += 0.2
            
            # Preferences indicating professional usage
            if user.preferences and isinstance(user.preferences, dict):
                if user.preferences.get('advanced_features', False):
                    score += 0.1
            
            return min(score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Error calculating professional behavior score: {str(e)}")
            return 0.0

    async def get_persona_context(self, user: User) -> Dict[str, Any]:
        """
        Get complete persona context for API responses
        Integrates with existing user data structure
        
        Returns:
            Dict containing persona-specific context data
        """
        persona = await self.detect_persona(user)
        
        base_context = {
            'persona': persona.value,
            'user_id': user.id,
            'user_preferences': user.preferences or {},
            'is_verified': user.is_verified,
            'is_superuser': user.is_superuser,
            'account_age_days': (datetime.utcnow() - user.created_at).days if user.created_at else 0
        }
        
        # Add persona-specific context
        if persona == PersonaType.ADMIN:
            base_context.update(await self._get_admin_context(user))
        elif persona == PersonaType.PROFESSIONAL:
            base_context.update(await self._get_professional_context(user))
        else:
            base_context.update(await self._get_casual_context(user))
            
        return base_context
    
    async def _get_admin_context(self, user: User) -> Dict[str, Any]:
        """
        Admin-specific context (محمدرضا persona from design docs)
        Focuses on system management and efficiency
        """
        # Get system overview data using existing models
        total_users = self.db.query(text("SELECT COUNT(*) as count FROM users")).fetchone().count
        total_predictions = self.db.query(text("SELECT COUNT(*) as count FROM predictions")).fetchone().count
        
        return {
            'system_overview': {
                'total_users': total_users,
                'total_predictions': total_predictions,
                'system_health': 'operational'  # Could integrate with health endpoint
            },
            'admin_capabilities': [
                'bulk_watchlist_management',
                'suggestion_review_system', 
                'performance_monitoring',
                'user_management'
            ],
            'efficiency_focus': True,
            'detail_level': 'maximum',
            'preferred_features': ['dashboard_overview', 'bulk_actions', 'system_metrics']
        }
    
    async def _get_professional_context(self, user: User) -> Dict[str, Any]:
        """
        Professional-specific context (سارا persona from design docs)
        Focuses on speed, accuracy, and trading capabilities
        """
        # Get user's prediction performance using existing Prediction model
        user_predictions_query = self.db.query(
            text("""
                SELECT 
                    COUNT(*) as total_predictions,
                    AVG(confidence_score) as avg_confidence,
                    COUNT(CASE WHEN is_accurate = true THEN 1 END) as accurate_predictions
                FROM predictions 
                WHERE user_id = :user_id
            """)
        ).params(user_id=user.id).fetchone()
        
        total_predictions = user_predictions_query.total_predictions or 0
        avg_confidence = float(user_predictions_query.avg_confidence or 0)
        accurate_predictions = user_predictions_query.accurate_predictions or 0
        
        accuracy_rate = (accurate_predictions / total_predictions * 100) if total_predictions > 0 else 0
        
        return {
            'trading_profile': {
                'total_predictions': total_predictions,
                'accuracy_rate': accuracy_rate,
                'average_confidence': avg_confidence,
                'active_positions': []  # Could be expanded with trading data
            },
            'speed_requirements': {
                'max_response_time_ms': 500,  # Professional users need fast responses
                'real_time_updates': True,
                'cache_preference': 'minimal'  # Professionals want fresh data
            },
            'preferred_timeframes': ['1m', '5m', '15m', '1h'],
            'risk_tolerance': 'moderate_to_high',
            'customization_level': 'advanced',
            'preferred_features': ['real_time_signals', 'risk_analysis', 'performance_tracking']
        }
    
    async def _get_casual_context(self, user: User) -> Dict[str, Any]:
        """
        Casual-specific context (علی persona from design docs)  
        Focuses on simplicity, learning, and guidance
        """
        # Get basic user statistics
        user_prediction_count = self.db.query(
            text("SELECT COUNT(*) as count FROM predictions WHERE user_id = :user_id")
        ).params(user_id=user.id).fetchone().count or 0
        
        # Determine learning progress based on activity
        learning_level = 'beginner'
        if user_prediction_count > 10:
            learning_level = 'intermediate' 
        elif user_prediction_count > 30:
            learning_level = 'advanced'
        
        return {
            'learning_profile': {
                'level': learning_level,
                'predictions_made': user_prediction_count,
                'learning_progress': min(user_prediction_count / 20 * 100, 100),  # Progress to 20 predictions
                'needs_guidance': user_prediction_count < 5
            },
            'simplification_needs': {
                'explanation_level': 'detailed',
                'use_simple_language': True,
                'show_educational_content': True,
                'progressive_disclosure': True
            },
            'confidence_building': {
                'show_success_stories': True,
                'emphasize_learning': True,
                'provide_reassurance': True
            },
            'preferred_features': ['simple_dashboard', 'educational_content', 'guided_decisions']
        }

    async def batch_detect_personas(self, user_ids: List[int]) -> Dict[int, PersonaType]:
        """
        Batch persona detection for multiple users
        Useful for admin dashboards or analytics
        
        Args:
            user_ids: List of user IDs to analyze
            
        Returns:
            Dict mapping user_id to PersonaType
        """
        results = {}
        
        try:
            # Get all users in one query for efficiency
            users = self.db.query(User).filter(User.id.in_(user_ids)).all()
            
            for user in users:
                persona = await self.detect_persona(user)
                results[user.id] = persona
                
        except Exception as e:
            logger.error(f"Error in batch persona detection: {str(e)}")
            
        return results

    def get_persona_statistics(self) -> Dict[str, Any]:
        """
        Get overall persona distribution statistics
        Useful for admin analytics dashboard
        """
        try:
            # Get all users with relevant fields
            all_users = self.db.query(User).all()
            
            persona_counts = {
                'admin': 0,
                'professional': 0, 
                'casual': 0,
                'total': len(all_users)
            }
            
            # This would be expensive for large user bases - consider caching
            for user in all_users[:100]:  # Limit to first 100 for performance
                # Simplified detection for statistics
                if user.is_superuser:
                    persona_counts['admin'] += 1
                elif user.preferences and user.preferences.get('user_type') == 'professional':
                    persona_counts['professional'] += 1
                else:
                    persona_counts['casual'] += 1
            
            return {
                'distribution': persona_counts,
                'percentages': {
                    'admin': (persona_counts['admin'] / max(persona_counts['total'], 1)) * 100,
                    'professional': (persona_counts['professional'] / max(persona_counts['total'], 1)) * 100,
                    'casual': (persona_counts['casual'] / max(persona_counts['total'], 1)) * 100
                },
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting persona statistics: {str(e)}")
            return {'error': 'Unable to calculate statistics'}