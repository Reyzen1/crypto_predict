# File: backend/app/api/api_v1/endpoints/health.py
# System health monitoring API endpoints

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import psutil
import time
from datetime import datetime, timezone

from app.core.database import get_db, get_redis, check_db_connection, check_redis_connection
from app.core.config import settings
from app.core.deps import get_current_active_user, get_optional_current_user
from app.repositories.user.user_repository import UserRepository
from app.repositories.backup.cryptocurrency import cryptocurrency_repository
from app.repositories.backup.price_data import price_data_repository
from app.models import User


router = APIRouter()


@router.get("/health")
def comprehensive_health_check(
    current_user: User = Depends(get_optional_current_user)
) -> Any:
    """
    Comprehensive system health check
    
    Public endpoint - no authentication required.
    Returns detailed health status of all system components.
    """
    start_time = time.time()
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "components": {},
        "response_time_ms": 0
    }
    
    # Check API health
    health_status["components"]["api"] = {
        "status": "healthy",
        "message": "API is running"
    }
    
    # Check database health - FIXED: No await needed
    try:
        db_healthy = check_db_connection()
        health_status["components"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "message": "Database connection successful" if db_healthy else "Database connection failed",
            "url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "hidden"
        }
        if not db_healthy:
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "message": f"Database check failed: {str(e)}"
        }
        health_status["status"] = "degraded"
    
    # Check Redis health - FIXED: No await needed
    try:
        redis_healthy = check_redis_connection()
        health_status["components"]["redis"] = {
            "status": "healthy" if redis_healthy else "unhealthy",
            "message": "Redis connection successful" if redis_healthy else "Redis connection failed"
        }
        if not redis_healthy:
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["redis"] = {
            "status": "unhealthy",
            "message": f"Redis check failed: {str(e)}"
        }
        health_status["status"] = "degraded"
    
    # Calculate response time
    health_status["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    return health_status


@router.get("/metrics")
def get_system_metrics(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get system performance metrics
    
    Requires user authentication.
    Returns system resource usage and performance data.
    """
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Database metrics
        db_session = next(get_db())
        try:
            # Get user count
            user_count = UserRepository.count(db_session)
            
            # Get crypto count
            crypto_count = cryptocurrency_repository.count(db_session)
            
            # Get price data count (last 24 hours)
            recent_prices = price_data_repository.get_recent_count(db_session, hours=24)
            
        finally:
            db_session.close()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system": {
                "cpu_usage_percent": cpu_percent,
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_percent": round((disk.used / disk.total) * 100, 2)
                }
            },
            "database": {
                "total_users": user_count,
                "total_cryptocurrencies": crypto_count,
                "recent_price_updates": recent_prices
            },
            "api": {
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect metrics: {str(e)}"
        )


@router.get("/database")
def database_health_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Detailed database health check
    
    Requires user authentication.
    Returns database connection status and basic statistics.
    """
    try:
        # Test database connection
        db.execute("SELECT 1")
        
        # Get database statistics
        stats = {
            "status": "healthy",
            "message": "Database connection successful",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "statistics": {}
        }
        
        try:
            # Get table counts
            stats["statistics"]["users"] = UserRepository.count(db)
            stats["statistics"]["cryptocurrencies"] = cryptocurrency_repository.count(db)
            stats["statistics"]["price_data_points"] = price_data_repository.count(db)
            
        except Exception as e:
            stats["statistics"]["error"] = f"Could not collect statistics: {str(e)}"
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database health check failed: {str(e)}"
        )


@router.get("/redis")
def redis_health_check(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Detailed Redis health check
    
    Requires user authentication.
    Returns Redis connection status and basic information.
    """
    try:
        redis_client = get_redis()
        if redis_client is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis client not available"
            )
        
        # Test Redis connection
        redis_client.ping()
        
        # Get Redis info
        redis_info = redis_client.info()
        
        return {
            "status": "healthy",
            "message": "Redis connection successful",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "info": {
                "redis_version": redis_info.get("redis_version"),
                "used_memory_human": redis_info.get("used_memory_human"),
                "connected_clients": redis_info.get("connected_clients"),
                "total_commands_processed": redis_info.get("total_commands_processed"),
                "keyspace_hits": redis_info.get("keyspace_hits"),
                "keyspace_misses": redis_info.get("keyspace_misses")
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Redis health check failed: {str(e)}"
        )


@router.get("/detailed")
def detailed_health_check() -> Any:
    """
    Detailed health check with all system components
    
    Public endpoint - no authentication required.
    Performs comprehensive health checks on all system dependencies.
    """
    health_status = {
        "status": "healthy",
        "service": "cryptopredict-backend", 
        "version": settings.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {}
    }
    
    # Database health check - FIXED: No await needed
    try:
        db_healthy = check_db_connection()
        health_status["checks"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "connection": "active" if db_healthy else "failed"
        }
        
        if not db_healthy:
            health_status["status"] = "unhealthy"
            
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # Redis health check - FIXED: No await needed
    try:
        redis_healthy = check_redis_connection()
        health_status["checks"]["redis"] = {
            "status": "healthy" if redis_healthy else "unhealthy",
            "connection": "active" if redis_healthy else "failed"
        }
        
        if not redis_healthy:
            health_status["status"] = "degraded"  # Redis is not critical for basic operation
            
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Configuration health check
    try:
        config_issues = []
        
        if not settings.SECRET_KEY or settings.SECRET_KEY == "your-super-secret-key-change-this-in-production":
            config_issues.append("SECRET_KEY not properly configured")
        
        if not settings.DATABASE_URL:
            config_issues.append("DATABASE_URL not configured")
            
        if not settings.REDIS_URL:
            config_issues.append("REDIS_URL not configured")
        
        health_status["checks"]["configuration"] = {
            "status": "healthy" if not config_issues else "warning",
            "issues": config_issues
        }
        
    except Exception as e:
        health_status["checks"]["configuration"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Environment health check
    try:
        env_warnings = []
        
        if settings.DEBUG and settings.ENVIRONMENT == "production":
            env_warnings.append("DEBUG mode enabled in production")
            
        if settings.SECRET_KEY and len(settings.SECRET_KEY) < 32:
            env_warnings.append("SECRET_KEY should be at least 32 characters")
        
        health_status["checks"]["environment"] = {
            "status": "healthy" if not env_warnings else "warning",
            "warnings": env_warnings,
            "environment": settings.ENVIRONMENT,
            "debug_mode": settings.DEBUG
        }
        
    except Exception as e:
        health_status["checks"]["environment"] = {
            "status": "error",
            "error": str(e)
        }
    
    return health_status


@router.get("/readiness")
def readiness_check() -> Any:
    """
    Readiness check for Kubernetes/container orchestration
    
    Public endpoint - validates that the application is ready to accept traffic.
    Validates system configuration and readiness.
    """
    checks = {
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {}
    }
    
    # Configuration checks
    config_issues = []
    
    if not settings.SECRET_KEY or settings.SECRET_KEY == "your-secret-key-change-this":
        config_issues.append("SECRET_KEY not properly configured")
    
    if not settings.DATABASE_URL:
        config_issues.append("DATABASE_URL not configured")
        
    if not settings.REDIS_URL:
        config_issues.append("REDIS_URL not configured")
    
    checks["checks"]["configuration"] = {
        "status": "healthy" if not config_issues else "warning",
        "issues": config_issues
    }
    
    # Environment checks
    env_warnings = []
    
    if settings.DEBUG and settings.ENVIRONMENT == "production":
        env_warnings.append("DEBUG mode enabled in production")
        
    if settings.SECRET_KEY and len(settings.SECRET_KEY) < 32:
        env_warnings.append("SECRET_KEY should be at least 32 characters")
    
    checks["checks"]["environment"] = {
        "status": "healthy" if not env_warnings else "warning",
        "warnings": env_warnings,
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG
    }
    
    # Set overall status
    if config_issues:
        checks["status"] = "warning"
    
    return checks


@router.get("/liveness")
def liveness_check() -> Any:
    """
    Liveness check for Kubernetes/container orchestration
    
    Public endpoint - simple check to verify the application is alive and responsive.
    Does not check external dependencies.
    """
    return {
        "status": "alive",
        "service": "cryptopredict-backend",
        "version": settings.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime": "running"  # Could be enhanced with actual uptime calculation
    }


@router.get("/startup")
def startup_check() -> Any:
    """
    Startup check for initialization validation
    
    Public endpoint - validates that all required components are initialized.
    """
    startup_status = {
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "initialization": {}
    }
    
    # Check if database tables exist
    try:
        db_session = next(get_db())
        try:
            # Try to query each main table
            UserRepository.count(db_session)
            startup_status["initialization"]["database_tables"] = {
                "status": "ready",
                "message": "All database tables accessible"
            }
        except Exception as e:
            startup_status["initialization"]["database_tables"] = {
                "status": "not_ready",
                "message": f"Database tables not accessible: {str(e)}"
            }
            startup_status["status"] = "not_ready"
        finally:
            db_session.close()
            
    except Exception as e:
        startup_status["initialization"]["database_tables"] = {
            "status": "error",
            "message": f"Database connection failed: {str(e)}"
        }
        startup_status["status"] = "not_ready"
    
    # Check Redis availability
    try:
        redis_healthy = check_redis_connection()
        startup_status["initialization"]["redis_cache"] = {
            "status": "ready" if redis_healthy else "not_ready",
            "message": "Redis cache available" if redis_healthy else "Redis cache not available"
        }
        # Redis is not critical for startup
    except Exception as e:
        startup_status["initialization"]["redis_cache"] = {
            "status": "error",
            "message": f"Redis check failed: {str(e)}"
        }
    
    return startup_status