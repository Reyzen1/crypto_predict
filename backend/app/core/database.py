# File: ./backend/app/core/database.py
# Database configuration and session management for CryptoPredict MVP
# Handles PostgreSQL connection and SQLAlchemy setup

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import redis
import logging

from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SQLAlchemy Engine Configuration
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,          # Validate connections before use
    pool_recycle=300,            # Recycle connections every 5 minutes
    pool_size=20,                # Connection pool size
    max_overflow=0,              # Maximum overflow connections
    echo=settings.DEBUG,         # Log SQL queries in debug mode
)

# Session factory for database operations
SessionLocal = sessionmaker(
    autocommit=False,            # Manual transaction control
    autoflush=False,             # Manual flush control
    bind=engine                  # Bind to our engine
)

# Base class for all database models
Base = declarative_base()

# Redis client for caching
redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,       # Decode byte responses to strings
    socket_connect_timeout=5,    # Connection timeout
    socket_timeout=5,            # Socket timeout
    retry_on_timeout=True        # Retry on timeout
)


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI
    Creates a new database session for each request
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def get_redis() -> redis.Redis:
    """
    Redis client dependency for FastAPI
    Returns the global Redis client instance
    """
    return redis_client


async def check_db_connection() -> bool:
    """
    Check if database connection is healthy
    Returns True if connection is successful
    """
    try:
        db = SessionLocal()
        # Execute a simple query to test connection
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


async def check_redis_connection() -> bool:
    """
    Check if Redis connection is healthy
    Returns True if connection is successful
    """
    try:
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