# File: backend/app/core/database.py
# Database connection and session management

import os
import logging
from typing import Generator, Optional
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session, declarative_base  # FIXED: Updated import
from sqlalchemy.pool import NullPool
import redis
from redis import Redis

from app.core.config import settings
from app.utils.query_monitor import setup_query_monitoring

# Setup logging
logger = logging.getLogger(__name__)

# Database URL from settings
DATABASE_URL = settings.DATABASE_URL

# Create SQLAlchemy engine with connection pooling
if "sqlite" in DATABASE_URL:
    # SQLite configuration for testing
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=NullPool
    )
    # Setup query monitoring for SQLite
    setup_query_monitoring(engine)
else:
    # PostgreSQL configuration for production
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,  # Recycle connections every hour
        echo=False  # Set to True for SQL query logging
    )

# Setup query monitoring
setup_query_monitoring(engine)

# Auto-enable query monitoring globally
from app.utils.query_monitor import query_monitor
query_monitor.enabled = True
query_monitor.start_time = __import__('time').time()
logger.info("🔍 Query monitoring AUTO-ENABLED globally")

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

# Create declarative base for models - FIXED: Using SQLAlchemy 2.0 import
Base = declarative_base()

# Optional metadata for enhanced table management
metadata = MetaData()

# Redis client setup
redis_client: Optional[Redis] = None

try:
    redis_client = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30
    )
    # Test connection
    redis_client.ping()
    logger.info("Redis connection established successfully")
except Exception as e:
    logger.warning(f"Redis connection failed: {e}")
    redis_client = None


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        if "connection" in str(e).lower() or "timeout" in str(e).lower():
            logger.error(f"🔴 Database connection issue: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def get_redis() -> Optional[Redis]:
    """
    Get Redis client instance
    
    Returns:
        Redis client or None if unavailable
    """
    return redis_client


def check_db_connection() -> bool:
    """
    Check if database connection is healthy - FIXED: Using text() properly
    Returns True if connection is successful
    """
    try:
        from sqlalchemy import text  # Import text function
        
        db = SessionLocal()
        # Execute a simple query to test connection with proper text() wrapper
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


def check_redis_connection() -> bool:
    """
    Check if Redis connection is healthy - FIXED: Made synchronous
    Returns True if connection is successful
    """
    try:
        if redis_client is None:
            return False
        # Test Redis connection with ping
        redis_client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis connection check failed: {e}")
        return False


# Database initialization functions
def init_db() -> None:
    """Initialize database tables"""
    try:
        # Import models to ensure they're registered - fixed import location
        import app.models
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def drop_db() -> None:
    """Drop all database tables (use with caution!)"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise


# Health check functions for monitoring
def get_database_info() -> dict:
    """Get database connection information"""
    return {
        "database_url": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else "local",
        "engine_info": str(engine.url).split("@")[-1] if "@" in str(engine.url) else "local",
        "pool_size": getattr(engine.pool, 'size', 'N/A'),
        "pool_checked_in": getattr(engine.pool, 'checkedin', 'N/A'),
        "pool_checked_out": getattr(engine.pool, 'checkedout', 'N/A'),
        "pool_overflow": getattr(engine.pool, 'overflow', 'N/A'),
    }


def get_redis_info() -> dict:
    """Get Redis connection information"""
    if redis_client is None:
        return {"status": "disconnected", "error": "Redis not available"}
    
    try:
        info = redis_client.info()
        return {
            "status": "connected",
            "redis_version": info.get("redis_version"),
            "used_memory": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
            "total_commands_processed": info.get("total_commands_processed")
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}