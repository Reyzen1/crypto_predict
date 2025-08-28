# File: backend/app/core/auth/persona_auth.py
# Persona-Based Authentication Enhancement 
# Extends existing authentication system with persona-specific permissions
# Compatible with existing User model and security framework

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import logging
from functools import wraps
from enum import Enum

# Import existing authentication components
from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models import User

# Import persona detection
from app.services.personas.persona_detector import PersonaDetector, PersonaType

logger = logging.getLogger(__name__)

# ========================================
# PERSONA PERMISSION DEFINITIONS
# ========================================

class PermissionLevel(str, Enum):
    """Permission levels for different actions"""
    PUBLIC = "public"          # No authentication required
    USER = "user"             # Any authenticated user
    PROFESSIONAL = "professional"  # Professional or higher
    ADMIN = "admin"           # Admin only
    SUPERUSER = "superuser"   # System superuser only

class PersonaPermissions:
    """
    Define permissions for each persona type
    Based on User Journey Maps and pain point analysis
    """
    
    # Admin permissions (محمدرضا persona)
    ADMIN_PERMISSIONS = {
        # System management
        "view_system_dashboard": True,
        "manage_watchlist_bulk": True,
        "review_ai_suggestions": True,
        "modify_system_parameters": True,
        "access_user_analytics": True,
        "manage_user_permissions": True,
        "view_system_health": True,
        "export_system_data": True,
        
        # AI and prediction management
        "override_ai_decisions": True,
        "modify_confidence_thresholds": True,
        "access_model_performance": True,
        "retrain_models": True,
        
        # Advanced features
        "bulk_operations": True,
        "advanced_reporting": True,
        "system_configuration": True,
        "audit_logs": True
    }
    
    # Professional permissions (سارا persona)
    PROFESSIONAL_PERMISSIONS = {
        # Trading and analysis
        "access_realtime_signals": True,
        "view_advanced_analytics": True,
        "customize_dashboard": True,
        "set_custom_alerts": True,
        "access_risk_analysis": True,
        "view_performance_metrics": True,
        "export_trading_data": True,
        
        # API access
        "api_high_rate_limit": True,
        "api_priority_processing": True,
        "webhook_notifications": True,
        
        # Advanced features (limited)
        "bulk_operations": False,  # Limited bulk operations only
        "advanced_reporting": False,
        "system_configuration": False,
        "modify_system_parameters": False
    }
    
    # Casual permissions (علی persona)
    CASUAL_PERMISSIONS = {
        # Basic functionality
        "view_simple_dashboard": True,
        "make_predictions": True,
        "access_educational_content": True,
        "view_learning_progress": True,
        "basic_portfolio_tracking": True,
        
        # Guided features
        "guided_investment_help": True,
        "risk_assessment_basic": True,
        "beginner_tutorials": True,
        
        # Restricted features
        "access_realtime_signals": False,
        "view_advanced_analytics": False,
        "customize_dashboard": False,
        "bulk_operations": False,
        "api_access": False,
        "advanced_reporting": False,
        "system_configuration": False
    }
    
    @classmethod
    def get_permissions_for_persona(cls, persona: PersonaType) -> Dict[str, bool]:
        """Get permissions dictionary for a specific persona"""
        permission_map = {
            PersonaType.ADMIN: cls.ADMIN_PERMISSIONS,
            PersonaType.PROFESSIONAL: cls.PROFESSIONAL_PERMISSIONS,
            PersonaType.CASUAL: cls.CASUAL_PERMISSIONS
        }
        return permission_map.get(persona, cls.CASUAL_PERMISSIONS)

# ========================================
# PERSONA AUTHENTICATION SERVICE
# ========================================

class PersonaAuthService:
    """
    Enhanced authentication service with persona-based permissions
    Integrates with existing authentication while adding persona context
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.persona_detector = PersonaDetector(db)
        
        # Cache for persona detection (reduces database queries)
        self._persona_cache: Dict[int, tuple] = {}  # user_id -> (persona, timestamp)
        self._cache_ttl = timedelta(minutes=30)  # Cache personas for 30 minutes
    
    async def get_user_persona_cached(self, user: User) -> PersonaType:
        """Get user persona with caching for performance"""
        current_time = datetime.utcnow()
        
        # Check cache first
        if user.id in self._persona_cache:
            cached_persona, cached_time = self._persona_cache[user.id]
            if current_time - cached_time < self._cache_ttl:
                return cached_persona
        
        # Detect persona and cache result
        persona = await self.persona_detector.detect_persona(user)
        self._persona_cache[user.id] = (persona, current_time)
        
        return persona
    
    async def check_permission(self, user: User, permission: str) -> bool:
        """Check if user has specific permission based on their persona"""
        try:
            # Get user's persona
            persona = await self.get_user_persona_cached(user)
            
            # Get permissions for this persona
            permissions = PersonaPermissions.get_permissions_for_persona(persona)
            
            # Check specific permission
            has_permission = permissions.get(permission, False)
            
            # Admin override: superusers always have permission
            if user.is_superuser and not has_permission:
                has_permission = True
                logger.info(f"Superuser {user.id} granted permission '{permission}' via admin override")
            
            logger.debug(f"Permission check for user {user.id} ({persona.value}): {permission} = {has_permission}")
            return has_permission
            
        except Exception as e:
            logger.error(f"Error checking permission '{permission}' for user {user.id}: {str(e)}")
            # Fail securely: deny permission on error
            return False
    
    async def get_user_permissions(self, user: User) -> Dict[str, bool]:
        """Get all permissions for a user"""
        try:
            persona = await self.get_user_persona_cached(user)
            permissions = PersonaPermissions.get_permissions_for_persona(persona)
            
            # Apply superuser override
            if user.is_superuser:
                # Superusers get all admin permissions
                enhanced_permissions = permissions.copy()
                enhanced_permissions.update(PersonaPermissions.ADMIN_PERMISSIONS)
                return enhanced_permissions
            
            return permissions
            
        except Exception as e:
            logger.error(f"Error getting permissions for user {user.id}: {str(e)}")
            # Return minimal permissions on error
            return {"view_simple_dashboard": True}
    
    async def validate_persona_access(self, user: User, required_persona: PersonaType) -> bool:
        """Validate that user has access level of required persona or higher"""
        try:
            user_persona = await self.get_user_persona_cached(user)
            
            # Define persona hierarchy (higher index = more permissions)
            persona_hierarchy = [PersonaType.CASUAL, PersonaType.PROFESSIONAL, PersonaType.ADMIN]
            
            user_level = persona_hierarchy.index(user_persona)
            required_level = persona_hierarchy.index(required_persona)
            
            # User must have same or higher level
            has_access = user_level >= required_level
            
            # Superuser override
            if user.is_superuser and not has_access:
                has_access = True
                logger.info(f"Superuser {user.id} granted access via admin override")
            
            return has_access
            
        except ValueError:
            logger.error(f"Invalid persona type in hierarchy check")
            return False
        except Exception as e:
            logger.error(f"Error validating persona access: {str(e)}")
            return False
    
    def clear_persona_cache(self, user_id: Optional[int] = None):
        """Clear persona cache for specific user or all users"""
        if user_id:
            self._persona_cache.pop(user_id, None)
            logger.debug(f"Cleared persona cache for user {user_id}")
        else:
            self._persona_cache.clear()
            logger.debug("Cleared all persona cache")

# ========================================
# PERSONA-AWARE DEPENDENCIES
# ========================================

# ========================================
# PERSONA-AWARE DEPENDENCIES - GLOBAL FUNCTIONS FIRST
# ========================================

def get_persona_auth_service(db: Session = Depends(get_db)) -> PersonaAuthService:
    """Dependency to get PersonaAuthService instance"""
    return PersonaAuthService(db)

async def get_current_user_with_persona(
    current_user: User = Depends(get_current_active_user),
    auth_service: PersonaAuthService = Depends(get_persona_auth_service)
) -> tuple[User, PersonaType]:
    """Get current user with their detected persona"""
    persona = await auth_service.get_user_persona_cached(current_user)
    return current_user, persona

def require_permission(permission: str):
    """Dependency factory for permission-based access control"""
    async def permission_dependency(
        user_persona: tuple[User, PersonaType] = Depends(get_current_user_with_persona),
        auth_service: PersonaAuthService = Depends(get_persona_auth_service)
    ) -> User:
        user, persona = user_persona
        
        has_permission = await auth_service.check_permission(user, permission)
        if not has_permission:
            logger.warning(f"User {user.id} ({persona.value}) denied access to permission '{permission}'")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: '{permission}' required"
            )
        
        return user
    
    return permission_dependency

def require_persona(required_persona: PersonaType):
    """Dependency factory for persona-level access control"""
    async def persona_dependency(
        user_persona: tuple[User, PersonaType] = Depends(get_current_user_with_persona),
        auth_service: PersonaAuthService = Depends(get_persona_auth_service)
    ) -> User:
        user, user_persona_type = user_persona
        
        has_access = await auth_service.validate_persona_access(user, required_persona)
        if not has_access:
            logger.warning(f"User {user.id} ({user_persona_type.value}) denied access, requires {required_persona.value}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: {required_persona.value} level required"
            )
        
        return user
    
    return persona_dependency

# Convenience dependencies for common persona requirements
async def get_admin_user(
    user: User = Depends(require_persona(PersonaType.ADMIN))
) -> User:
    """Dependency for admin-only endpoints"""
    return user

async def get_professional_user(
    user: User = Depends(require_persona(PersonaType.PROFESSIONAL))
) -> User:
    """Dependency for professional-level endpoints (includes admins)"""
    return user

async def get_user_with_bulk_operations(
    user: User = Depends(require_permission("bulk_operations"))
) -> User:
    """Dependency for endpoints requiring bulk operations permission"""
    return user

async def get_user_with_realtime_signals(
    user: User = Depends(require_permission("access_realtime_signals"))
) -> User:
    """Dependency for real-time signals access"""
    return user

class PersonaAuthDependencies:
    """
    FastAPI dependencies for persona-based authentication
    Extends existing authentication with persona-specific access control
    """
    
    # Reference the global functions
    get_persona_auth_service = staticmethod(get_persona_auth_service)
    get_current_user_with_persona = staticmethod(get_current_user_with_persona)
    require_permission = staticmethod(require_permission)
    require_persona = staticmethod(require_persona)
    get_admin_user = staticmethod(get_admin_user)
    get_professional_user = staticmethod(get_professional_user)
    get_user_with_bulk_operations = staticmethod(get_user_with_bulk_operations)
    get_user_with_realtime_signals = staticmethod(get_user_with_realtime_signals)

# Create global instance of dependencies for import - Updated references
get_persona_auth_service = get_persona_auth_service
get_current_user_with_persona = get_current_user_with_persona
require_permission = require_permission
require_persona = require_persona
get_admin_user = get_admin_user
get_professional_user = get_professional_user
get_user_with_bulk_operations = get_user_with_bulk_operations
get_user_with_realtime_signals = get_user_with_realtime_signals

# ========================================
# PERSONA PERMISSION MIDDLEWARE
# ========================================

class PersonaPermissionMiddleware:
    """
    Middleware for automatic persona-based permission enforcement
    Can be applied globally or to specific route groups
    """
    
    def __init__(self, db_session_factory: Callable[[], Session]):
        self.db_session_factory = db_session_factory
    
    async def __call__(self, request: Request, call_next):
        """Process request with persona permission checking"""
        # Only apply to API routes
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        
        # Skip for public endpoints
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)
        
        # Get user from existing authentication
        try:
            # This would integrate with existing auth middleware
            # For now, we'll skip automatic enforcement and rely on explicit dependencies
            pass
        except Exception as e:
            logger.error(f"Error in persona permission middleware: {str(e)}")
        
        return await call_next(request)
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public (no auth required)"""
        public_patterns = [
            "/api/v1/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/docs",
            "/openapi.json"
        ]
        return any(path.startswith(pattern) for pattern in public_patterns)

# ========================================
# PERSONA CONTEXT MANAGER
# ========================================

class PersonaContext:
    """
    Context manager for persona-aware operations
    Provides convenient access to user persona and permissions
    """
    
    def __init__(self, user: User, db: Session):
        self.user = user
        self.db = db
        self._auth_service = PersonaAuthService(db)
        self._persona: Optional[PersonaType] = None
        self._permissions: Optional[Dict[str, bool]] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self._persona = await self._auth_service.get_user_persona_cached(self.user)
        self._permissions = await self._auth_service.get_user_permissions(self.user)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        # Cleanup if needed
        pass
    
    @property
    def persona(self) -> PersonaType:
        """Get user's persona"""
        if self._persona is None:
            raise RuntimeError("PersonaContext not properly initialized")
        return self._persona
    
    @property
    def permissions(self) -> Dict[str, bool]:
        """Get user's permissions"""
        if self._permissions is None:
            raise RuntimeError("PersonaContext not properly initialized")
        return self._permissions
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        return self.permissions.get(permission, False)
    
    def is_admin(self) -> bool:
        """Check if user is admin persona"""
        return self.persona == PersonaType.ADMIN
    
    def is_professional(self) -> bool:
        """Check if user is professional or admin persona"""
        return self.persona in [PersonaType.PROFESSIONAL, PersonaType.ADMIN]
    
    def is_casual(self) -> bool:
        """Check if user is casual persona (but not exclusively)"""
        return self.persona == PersonaType.CASUAL
    
    def get_response_optimization(self) -> Dict[str, Any]:
        """Get response optimization settings for this persona"""
        optimization_settings = {
            PersonaType.ADMIN: {
                "detail_level": "maximum",
                "include_metadata": True,
                "cache_duration_seconds": 300,  # 5 minutes
                "include_debug_info": True
            },
            PersonaType.PROFESSIONAL: {
                "detail_level": "high", 
                "include_metadata": False,  # Skip for speed
                "cache_duration_seconds": 30,   # 30 seconds for freshness
                "optimize_for_speed": True,
                "max_response_time_ms": 500
            },
            PersonaType.CASUAL: {
                "detail_level": "simplified",
                "include_metadata": False,
                "cache_duration_seconds": 600,  # 10 minutes
                "include_educational_content": True,
                "use_simple_language": True
            }
        }
        return optimization_settings.get(self.persona, optimization_settings[PersonaType.CASUAL])

# ========================================
# UTILITY FUNCTIONS
# ========================================

async def get_persona_context(user: User, db: Session) -> PersonaContext:
    """Utility function to get persona context for a user"""
    context = PersonaContext(user, db)
    await context.__aenter__()
    return context

def persona_required(required_persona: PersonaType):
    """Decorator for functions requiring specific persona level"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This would be used in non-FastAPI contexts
            # Extract user and db from arguments (implementation depends on usage)
            user = kwargs.get('user') or (args[0] if args and isinstance(args[0], User) else None)
            db = kwargs.get('db')
            
            if not user or not db:
                raise ValueError("User and database session required for persona checking")
            
            auth_service = PersonaAuthService(db)
            has_access = await auth_service.validate_persona_access(user, required_persona)
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: {required_persona.value} level required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def permission_required(permission: str):
    """Decorator for functions requiring specific permission"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get('user') or (args[0] if args and isinstance(args[0], User) else None)
            db = kwargs.get('db')
            
            if not user or not db:
                raise ValueError("User and database session required for permission checking")
            
            auth_service = PersonaAuthService(db)
            has_permission = await auth_service.check_permission(user, permission)
            
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions: '{permission}' required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# ========================================
# INTEGRATION HELPERS
# ========================================

class PersonaAuthIntegration:
    """
    Integration helpers for persona authentication
    Assists with migrating existing endpoints to persona-based auth
    """
    
    @staticmethod
    def upgrade_endpoint_auth(
        original_dependency: Callable,
        required_permission: Optional[str] = None,
        required_persona: Optional[PersonaType] = None
    ):
        """
        Upgrade existing endpoint authentication with persona support
        
        Usage:
        @router.get("/admin/dashboard")
        async def admin_dashboard(
            user: User = Depends(
                PersonaAuthIntegration.upgrade_endpoint_auth(
                    get_current_active_user, 
                    required_persona=PersonaType.ADMIN
                )
            )
        ):
        """
        if required_permission and required_persona:
            raise ValueError("Cannot specify both permission and persona requirements")
        
        if required_permission:
            return require_permission(required_permission)
        elif required_persona:
            return require_persona(required_persona)
        else:
            # Just add persona detection without additional restrictions
            return get_current_user_with_persona
    
    @staticmethod
    async def check_backward_compatibility(user: User, db: Session) -> Dict[str, Any]:
        """Check compatibility with existing authentication patterns"""
        try:
            auth_service = PersonaAuthService(db)
            persona = await auth_service.get_user_persona_cached(user)
            permissions = await auth_service.get_user_permissions(user)
            
            return {
                "user_id": user.id,
                "detected_persona": persona.value,
                "is_superuser": user.is_superuser,
                "is_verified": user.is_verified,
                "permissions_count": len([p for p, enabled in permissions.items() if enabled]),
                "high_level_permissions": user.is_superuser or persona == PersonaType.ADMIN,
                "compatibility_status": "full",
                "migration_needed": False
            }
            
        except Exception as e:
            logger.error(f"Compatibility check failed: {str(e)}")
            return {
                "compatibility_status": "error",
                "migration_needed": True,
                "error": str(e)
            }