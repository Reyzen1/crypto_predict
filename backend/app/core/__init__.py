"""
Core application components and utilities.

This module provides the foundational components for the CryptoPredict application,
including configuration, database management, security, dependencies, and utilities.
"""

# Configuration and Settings
from .config import Settings, load_env_file, settings

# Database Components  
from .database import (
    Base,
    engine,
    SessionLocal,
    metadata,
    DATABASE_URL,
    get_db,
    get_redis,
    check_db_connection,
    check_redis_connection,
    init_db,
    drop_db,
    get_database_info,
    get_redis_info
)

# Security Components
from .security import (
    SecurityManager,
    create_access_token,
    verify_password,
    get_password_hash
)

# Dependencies and Authentication
from .deps import (
    get_redis,
    get_current_user_token,
    get_current_user,
    get_current_active_user,
    get_current_verified_user
)

# Celery Configuration
from .celery_config import CeleryConfig, AsyncCeleryConfig

# Rate Limiting
from .rate_limiter import RateLimitConfig, SimpleRateLimiter

# Documentation utilities (if available)
try:
    from .documentation import *
except ImportError:
    pass

__all__ = [
    # Configuration
    "Settings",
    "load_env_file", 
    "settings",
    
    # Database
    "Base",
    "engine",
    "SessionLocal",
    "metadata",
    "DATABASE_URL",
    "get_db",
    "get_redis",
    "check_db_connection",
    "check_redis_connection",
    "init_db",
    "drop_db",
    "get_database_info",
    "get_redis_info",
    
    # Security
    "SecurityManager",
    "create_access_token",
    "verify_password",
    "get_password_hash",
    
    # Dependencies
    "get_current_user_token",
    "get_current_user",
    "get_current_active_user", 
    "get_current_verified_user",
    
    # Celery
    "CeleryConfig",
    "AsyncCeleryConfig",
    
    # Rate Limiting
    "RateLimitConfig",
    "SimpleRateLimiter",
]
