# File: backend/app/api/api_v1/endpoints/health.py
# System health monitoring API endpoints

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import psutil
import time
from datetime import datetime

from app.core.database import get_db, get_redis, check_db_connection
from app.core.config import settings
from app.core.deps import get_current_active_user, get_optional_current_user
from app.repositories import user_repository, cryptocurrency_repository, price_data_repository
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
        "timestamp": datetime.utcnow().isoformat(),
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
    
    # Check database health
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
    
    # Check Redis health
    try:
        redis_client = get_redis()
        redis_client.ping()
        health_status["components"]["redis"] = {
            "status": "healthy",
            "message": "Redis connection successful"
        }
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
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get process-specific metrics
        process = psutil.Process()
        process_memory = process.memory_info()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
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
            "process": {
                "memory_mb": round(process_memory.rss / (1024**2), 2),
                "cpu_percent": process.cpu_percent(),
                "threads": process.num_threads(),
                "open_files": len(process.open_files())
            },
            "application": {
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT,
                "debug_mode": settings.DEBUG
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system metrics: {str(e)}"
        )


@router.get("/database")
def get_database_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get detailed database health information
    
    Requires user authentication.
    Returns database connection status and data statistics.
    """
    try:
        start_time = time.time()
        
        # Basic connection test
        db_healthy = check_db_connection()
        connection_time = round((time.time() - start_time) * 1000, 2)
        
        if not db_healthy:
            return {
                "status": "unhealthy",
                "connection_time_ms": connection_time,
                "error": "Database connection failed"
            }
        
        # Get data statistics using your existing repositories
        stats = {}
        
        try:
            # User statistics
            active_users = user_repository.count_active_users(db)
            stats["users"] = {
                "total_active": active_users,
                "status": "healthy"
            }
        except Exception as e:
            stats["users"] = {
                "status": "error",
                "error": str(e)
            }
        
        try:
            # Cryptocurrency statistics
            all_cryptos = cryptocurrency_repository.get_all(db)
            active_cryptos = cryptocurrency_repository.get_active_cryptos(db)
            stats["cryptocurrencies"] = {
                "total": len(all_cryptos),
                "active": len(active_cryptos),
                "status": "healthy"
            }
        except Exception as e:
            stats["cryptocurrencies"] = {
                "status": "error",
                "error": str(e)
            }
        
        try:
            # Price data statistics  
            btc = cryptocurrency_repository.get_by_symbol(db, "BTC")
            if btc:
                btc_data_check = price_data_repository.check_data_availability(db, btc.id)
                stats["price_data"] = {
                    "btc_data_points": btc_data_check["total_records"],
                    "btc_data_quality": btc_data_check["data_quality"],
                    "status": "healthy"
                }
            else:
                stats["price_data"] = {
                    "status": "warning",
                    "message": "No BTC data found"
                }
        except Exception as e:
            stats["price_data"] = {
                "status": "error",
                "error": str(e)
            }
        
        return {
            "status": "healthy",
            "connection_time_ms": connection_time,
            "database_url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "hidden",
            "statistics": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/redis")
def get_redis_health(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get detailed Redis health information
    
    Requires user authentication.
    Returns Redis connection status and basic statistics.
    """
    try:
        start_time = time.time()
        
        # Get Redis client
        redis_client = get_redis()
        
        # Test connection
        redis_client.ping()
        connection_time = round((time.time() - start_time) * 1000, 2)
        
        # Get Redis info
        redis_info = redis_client.info()
        
        return {
            "status": "healthy",
            "connection_time_ms": connection_time,
            "redis_url": settings.REDIS_URL.split("@")[-1] if "@" in settings.REDIS_URL else settings.REDIS_URL,
            "info": {
                "version": redis_info.get("redis_version"),
                "uptime_seconds": redis_info.get("uptime_in_seconds"),
                "connected_clients": redis_info.get("connected_clients"),
                "used_memory_human": redis_info.get("used_memory_human"),
                "total_commands_processed": redis_info.get("total_commands_processed"),
                "keyspace": {
                    key: value for key, value in redis_info.items() 
                    if key.startswith("db")
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/dependencies")
def check_external_dependencies(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Check status of external dependencies and APIs
    
    Requires user authentication.
    Tests connectivity to external services.
    """
    dependencies = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check external APIs (basic connectivity)
    external_apis = [
        {
            "name": "CoinGecko API",
            "url": "https://api.coingecko.com/api/v3/ping",
            "required": True
        },
        {
            "name": "Binance API", 
            "url": "https://api.binance.com/api/v3/ping",
            "required": False
        }
    ]
    
    import httpx
    
    for api in external_apis:
        try:
            start_time = time.time()
            
            with httpx.Client(timeout=5.0) as client:
                response = client.get(api["url"])
                response_time = round((time.time() - start_time) * 1000, 2)
                
                if response.status_code == 200:
                    dependencies["services"][api["name"]] = {
                        "status": "healthy",
                        "response_time_ms": response_time,
                        "status_code": response.status_code
                    }
                else:
                    dependencies["services"][api["name"]] = {
                        "status": "unhealthy",
                        "response_time_ms": response_time,
                        "status_code": response.status_code
                    }
                    if api["required"]:
                        dependencies["status"] = "degraded"
                        
        except Exception as e:
            dependencies["services"][api["name"]] = {
                "status": "unhealthy",
                "error": str(e)
            }
            if api["required"]:
                dependencies["status"] = "degraded"
    
    return dependencies


@router.get("/startup")
def get_startup_checks(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Run startup validation checks
    
    Requires user authentication.
    Validates system configuration and readiness.
    """
    checks = {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
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