# File: backend/app/api/api_v1/endpoints/tasks.py
"""
Task Management API Endpoints 
Provides REST API for managing background tasks and monitoring
Complete and tested implementation for CryptoPredict MVP - COMPLETELY UNIQUE Operation IDs
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timezone
import asyncio

from app.core.deps import get_current_active_user
from app.models.user import User
from app.tasks.price_collector import (
    sync_all_prices,
    sync_historical_data,
    discover_new_cryptocurrencies,
    cleanup_old_data,
    sync_specific_cryptocurrency,
    get_task_status
)
from app.tasks.scheduler import task_scheduler, get_next_run_times
from app.tasks.celery_app import celery_app

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.post("/start", operation_id="start_tasks")
async def start_background_tasks_manually(  # FIXED: Completely unique function name
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Start all background tasks manually
    
    Requires authentication. Initiates all scheduled background tasks
    for data collection and synchronization.
    
    Returns:
        dict: Summary of started tasks
    """
    try:
        logger.info(f"User {current_user.email} starting background tasks")
        
        # Task mapping for manual execution
        task_map = {
            "sync_prices": {
                "func": sync_all_prices,
                "description": "Synchronize current cryptocurrency prices"
            },
            "sync_historical": {
                "func": sync_historical_data,
                "description": "Synchronize historical price data"
            },
            "discover_new": {
                "func": discover_new_cryptocurrencies,
                "description": "Discover new cryptocurrencies"
            }
        }
        
        started_tasks = []
        
        # Start each task
        for task_name, task_info in task_map.items():
            try:
                result = task_info["func"].delay()
                started_tasks.append({
                    "task_name": task_name,
                    "task_id": result.id,
                    "description": task_info["description"],
                    "status": "started"
                })
            except Exception as e:
                logger.error(f"Failed to start task {task_name}: {e}")
                started_tasks.append({
                    "task_name": task_name,
                    "task_id": None,
                    "description": task_info["description"],
                    "status": "failed",
                    "error": str(e)
                })
        
        return {
            "status": "success",
            "message": "Background tasks started",
            "started_by": current_user.email,
            "tasks": started_tasks,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start background tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start tasks: {str(e)}")


@router.post("/stop", operation_id="stop_tasks")
async def stop_background_tasks_manually(  # FIXED: Completely unique function name
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Stop all running background tasks
    
    Requires authentication. Attempts to gracefully stop all running
    background tasks. This operation may take a few moments to complete.
    
    Returns:
        dict: Summary of stopped tasks
    """
    try:
        logger.info(f"User {current_user.email} stopping background tasks")
        
        # Get active tasks
        active_tasks = celery_app.control.inspect().active()
        
        if not active_tasks:
            return {
                "status": "success",
                "message": "No active tasks to stop",
                "stopped_by": current_user.email,
                "active_tasks": 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # Stop active tasks
        stopped_count = 0
        for worker_name, tasks in active_tasks.items():
            for task in tasks:
                task_id = task.get('id')
                if task_id:
                    celery_app.control.revoke(task_id, terminate=True)
                    stopped_count += 1
        
        return {
            "status": "success",
            "message": f"Stopped {stopped_count} background tasks",
            "stopped_by": current_user.email,
            "stopped_tasks": stopped_count,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to stop background tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop tasks: {str(e)}")


@router.get("/status", operation_id="get_tasks_status")
async def get_background_tasks_status() -> Dict[str, Any]:  # FIXED: Completely unique function name
    """
    Get comprehensive status of all background tasks
    
    No authentication required. Returns detailed information about
    all background tasks including active, scheduled, and completed tasks.
    
    Returns:
        dict: Comprehensive task status information
    """
    try:
        # Get Celery inspector
        inspector = celery_app.control.inspect()
        
        # Get various task states
        active_tasks = inspector.active() or {}
        scheduled_tasks = inspector.scheduled() or {}
        reserved_tasks = inspector.reserved() or {}
        
        # Get stats
        stats = inspector.stats() or {}
        
        # Calculate totals
        total_active = sum(len(tasks) for tasks in active_tasks.values())
        total_scheduled = sum(len(tasks) for tasks in scheduled_tasks.values())
        total_reserved = sum(len(tasks) for tasks in reserved_tasks.values())
        
        return {
            "status": "success",
            "message": "Task status retrieved successfully",
            "summary": {
                "total_active": total_active,
                "total_scheduled": total_scheduled,
                "total_reserved": total_reserved,
                "workers_online": len(stats)
            },
            "active_tasks": active_tasks,
            "scheduled_tasks": scheduled_tasks,
            "reserved_tasks": reserved_tasks,
            "worker_stats": stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.post("/manual/{task_name}", operation_id="run_manual_task")
async def run_background_task_manually(  # FIXED: Completely unique function name
    task_name: str,
    days: Optional[int] = None,
    crypto_symbol: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Execute a specific task manually
    
    Requires authentication. Allows manual execution of specific background tasks
    with optional parameters for customization.
    
    Args:
        task_name: Name of task to execute
        days: Number of days (for historical sync)
        crypto_symbol: Cryptocurrency symbol (for specific sync)
        
    Returns:
        dict: Task execution result
    """
    try:
        # Task mapping
        task_map = {
            "sync_prices": {
                "func": sync_all_prices,
                "description": "Synchronize current cryptocurrency prices"
            },
            "sync_historical": {
                "func": sync_historical_data,
                "description": "Synchronize historical price data"
            },
            "discover_cryptos": {
                "func": discover_new_cryptocurrencies,
                "description": "Discover new cryptocurrencies"
            },
            "sync_specific": {
                "func": sync_specific_cryptocurrency,
                "description": "Synchronize specific cryptocurrency data"
            },
            "cleanup_data": {
                "func": cleanup_old_data,
                "description": "Clean up old price data"
            }
        }
        
        if task_name not in task_map:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown task: {task_name}. Available tasks: {list(task_map.keys())}"
            )
        
        task_info = task_map[task_name]
        task_func = task_info["func"]
        
        # Execute task with appropriate parameters
        if task_name == "sync_historical":
            days = days or 30
            result_task = task_func.delay(days=days)
            parameters = {"days": days}
        elif task_name == "sync_specific":
            if not crypto_symbol:
                raise HTTPException(
                    status_code=400,
                    detail="crypto_symbol parameter is required for sync_specific task"
                )
            result_task = task_func.delay(crypto_symbol=crypto_symbol.upper())
            parameters = {"crypto_symbol": crypto_symbol.upper()}
        elif task_name == "discover_cryptos":
            result_task = task_func.delay(limit=100)
            parameters = {"limit": 100}
        elif task_name == "cleanup_data":
            result_task = task_func.delay(days_to_keep=365)
            parameters = {"days_to_keep": 365}
        else:
            result_task = task_func.delay()
            parameters = {}
        
        return {
            "status": "success",
            "message": f"Task '{task_name}' started manually",
            "task_id": result_task.id,
            "task_name": task_name,
            "description": task_info["description"],
            "parameters": parameters,
            "started_by": current_user.email,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run manual task {task_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run task: {str(e)}")


@router.get("/result/{task_id}", operation_id="get_task_result")
async def fetch_task_execution_result(  # FIXED: Completely unique function name
    task_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get result of a specific task by ID
    
    Requires authentication. Retrieves the execution result, status,
    and metadata for a specific background task.
    
    Args:
        task_id: Unique identifier of the task
        
    Returns:
        dict: Comprehensive task result information
    """
    try:
        # Get task result from Celery
        result = celery_app.AsyncResult(task_id)
        
        # Determine task state description
        state_descriptions = {
            "PENDING": "Task is waiting to be processed",
            "STARTED": "Task has been started and is running",
            "SUCCESS": "Task completed successfully",
            "FAILURE": "Task failed to complete",
            "RETRY": "Task is being retried after failure",
            "REVOKED": "Task was cancelled/revoked"
        }
        
        return {
            "status": "success",
            "task_id": task_id,
            "task_status": result.status,
            "status_description": state_descriptions.get(result.status, "Unknown status"),
            "task_result": result.result if result.ready() else None,
            "task_info": result.info,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None,
            "failed": result.failed() if result.ready() else None,
            "date_done": result.date_done.isoformat() if result.date_done else None,
            "traceback": result.traceback if result.failed() else None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get task result for {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task result: {str(e)}")


@router.delete("/revoke/{task_id}", operation_id="revoke_task")
async def cancel_background_task(  # FIXED: Completely unique function name
    task_id: str,
    terminate: bool = False,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Revoke (cancel) a specific task
    
    Requires authentication. Cancels a running or pending task.
    Use terminate=True to forcefully kill a running task.
    
    Args:
        task_id: Unique identifier of the task to revoke
        terminate: Whether to terminate the task immediately (default: False)
        
    Returns:
        dict: Revocation result
    """
    try:
        logger.info(f"User {current_user.email} revoking task: {task_id}")
        
        # Revoke the task
        result = task_scheduler.revoke_task(task_id, terminate=terminate)
        
        result["revoked_by"] = current_user.email
        result["terminate_used"] = terminate
        return result
        
    except Exception as e:
        logger.error(f"Failed to revoke task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to revoke task: {str(e)}")


@router.post("/purge", operation_id="purge_queue")
async def clear_task_queue(  # FIXED: Completely unique function name
    queue_name: str = "default",
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Purge all tasks from a specific queue
    
    Requires authentication. Removes all pending tasks from the specified queue.
    Use with extreme caution as this will cancel all waiting tasks.
    
    Args:
        queue_name: Name of queue to purge (default: "default")
        
    Returns:
        dict: Purge operation result
    """
    try:
        logger.warning(f"User {current_user.email} purging queue: {queue_name}")
        
        # Purge the queue
        result = task_scheduler.purge_queue(queue_name)
        
        result["purged_by"] = current_user.email
        result["queue_name"] = queue_name
        return result
        
    except Exception as e:
        logger.error(f"Failed to purge queue {queue_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to purge queue: {str(e)}")


@router.get("/schedules", operation_id="get_schedules")
async def retrieve_task_schedules() -> Dict[str, Any]:  # FIXED: Completely unique function name
    """
    Get information about all scheduled tasks
    
    No authentication required. Returns information about periodic task schedules,
    next execution times, and scheduling configuration.
    
    Returns:
        dict: Complete scheduling information
    """
    try:
        # Get next run times for scheduled tasks
        next_runs = get_next_run_times()
        
        # Task schedule information
        schedules = {
            "sync_all_prices": {
                "description": "Synchronize current prices for all cryptocurrencies",
                "schedule": "Every 5 minutes",
                "cron": "*/5 * * * *",
                "queue": "price_data",
                "enabled": True
            },
            "sync_historical_data": {
                "description": "Synchronize historical price data",
                "schedule": "Every hour at minute 0",
                "cron": "0 * * * *",
                "queue": "price_data",
                "enabled": True
            },
            "discover_new_cryptocurrencies": {
                "description": "Discover and add new cryptocurrencies",
                "schedule": "Daily at 2:00 AM",
                "cron": "0 2 * * *",
                "queue": "scheduling",
                "enabled": True
            },
            "cleanup_old_data": {
                "description": "Clean up old price data",
                "schedule": "Weekly on Sunday at 3:00 AM",
                "cron": "0 3 * * 0",
                "queue": "scheduling",
                "enabled": True
            }
        }
        
        return {
            "status": "success",
            "message": "Task schedules retrieved successfully",
            "schedules": schedules,
            "next_execution_times": next_runs,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get task schedules: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get schedules: {str(e)}")


@router.get("/health", operation_id="task_health")
async def monitor_task_system_health() -> Dict[str, Any]:  # FIXED: Completely unique function name
    """
    Check health status of the task system
    
    No authentication required. Performs comprehensive health checks
    on the background task system including Celery workers, Redis broker,
    and task queue status.
    
    Returns:
        dict: Comprehensive health status
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {}
        }
        
        # Check Celery workers
        try:
            inspector = celery_app.control.inspect()
            stats = inspector.stats() or {}
            active_workers = len(stats)
            
            health_status["checks"]["celery_workers"] = {
                "status": "healthy" if active_workers > 0 else "unhealthy",
                "active_workers": active_workers,
                "worker_details": stats
            }
            
            if active_workers == 0:
                health_status["status"] = "unhealthy"
                
        except Exception as e:
            health_status["checks"]["celery_workers"] = {
                "status": "error",
                "error": str(e)
            }
            health_status["status"] = "unhealthy"
        
        # Check Redis broker
        try:
            # Simple broker connectivity test
            from app.core.database import check_redis_connection
            redis_healthy = check_redis_connection()
            
            health_status["checks"]["redis_broker"] = {
                "status": "healthy" if redis_healthy else "unhealthy",
                "connection": "active" if redis_healthy else "failed"
            }
            
            if not redis_healthy:
                health_status["status"] = "unhealthy"
                
        except Exception as e:
            health_status["checks"]["redis_broker"] = {
                "status": "error",
                "error": str(e)
            }
            health_status["status"] = "unhealthy"
        
        # Check task queues
        try:
            inspector = celery_app.control.inspect()
            active_tasks = inspector.active() or {}
            reserved_tasks = inspector.reserved() or {}
            
            total_active = sum(len(tasks) for tasks in active_tasks.values())
            total_reserved = sum(len(tasks) for tasks in reserved_tasks.values())
            
            health_status["checks"]["task_queues"] = {
                "status": "healthy",
                "active_tasks": total_active,
                "reserved_tasks": total_reserved,
                "queue_details": {
                    "active": active_tasks,
                    "reserved": reserved_tasks
                }
            }
            
        except Exception as e:
            health_status["checks"]["task_queues"] = {
                "status": "error",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Failed to check task system health: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.get("/info", operation_id="task_info")
async def get_task_system_information() -> Dict[str, Any]:  # FIXED: Completely unique function name
    """
    Get comprehensive information about the task system
    
    No authentication required. Provides detailed information about available tasks,
    their purposes, scheduling, and system requirements.
    
    Returns:
        dict: Complete task system information
    """
    return {
        "system_info": {
            "name": "CryptoPredict Background Task System",
            "version": "1.0.0",
            "technology": "Celery with Redis broker",
            "purpose": "Automated cryptocurrency data collection and processing"
        },
        "available_tasks": {
            "sync_all_prices": {
                "description": "Synchronize current prices for all active cryptocurrencies",
                "schedule": "Every 5 minutes",
                "type": "periodic",
                "estimated_duration": "30-60 seconds",
                "dependencies": ["CoinGecko API", "Database"]
            },
            "sync_historical_data": {
                "description": "Synchronize historical price data for cryptocurrencies", 
                "schedule": "Every hour at minute 0",
                "type": "periodic",
                "estimated_duration": "2-5 minutes",
                "dependencies": ["CoinGecko API", "Database"]
            },
            "discover_new_cryptocurrencies": {
                "description": "Discover and add new cryptocurrencies to the system",
                "schedule": "Daily at 2:00 AM",
                "type": "periodic",
                "estimated_duration": "1-3 minutes",
                "dependencies": ["CoinGecko API", "Database"]
            },
            "cleanup_old_data": {
                "description": "Clean up old price data to manage database size",
                "schedule": "Weekly on Sunday at 3:00 AM", 
                "type": "periodic",
                "estimated_duration": "5-15 minutes",
                "dependencies": ["Database"]
            },
            "sync_specific_cryptocurrency": {
                "description": "Synchronize data for a specific cryptocurrency",
                "schedule": "On demand (manual execution)",
                "type": "manual",
                "estimated_duration": "10-30 seconds",
                "dependencies": ["CoinGecko API", "Database"]
            }
        },
        "system_requirements": {
            "celery_worker": "Required for task execution",
            "celery_beat": "Required for scheduled tasks", 
            "redis": "Required as message broker and result backend",
            "database": "Required for data persistence",
            "external_apis": "CoinGecko API for cryptocurrency data"
        },
        "startup_commands": {
            "start_workers": "./temp/start-celery.sh",
            "worker_only": "celery -A app.tasks.celery_app worker --loglevel=info",
            "beat_only": "celery -A app.tasks.celery_app beat --loglevel=info",
            "flower_monitoring": "celery -A app.tasks.celery_app flower --port=5555"
        },
        "monitoring": {
            "health_endpoint": "/api/v1/tasks/health",
            "status_endpoint": "/api/v1/tasks/status", 
            "schedules_endpoint": "/api/v1/tasks/schedules",
            "flower_ui": "http://localhost:5555 (if running)"
        },
        "management_endpoints": {
            "start_tasks": "POST /api/v1/tasks/start",
            "stop_tasks": "POST /api/v1/tasks/stop",
            "manual_execution": "POST /api/v1/tasks/manual/{task_name}",
            "task_results": "GET /api/v1/tasks/result/{task_id}",
            "revoke_task": "DELETE /api/v1/tasks/revoke/{task_id}"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }