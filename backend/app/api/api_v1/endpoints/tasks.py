# File: backend/app/api/api_v1/endpoints/tasks.py
# Task Management API Endpoints with ML Tasks Integration
# Provides REST API for managing both data collection and ML background tasks

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timezone
import asyncio

from app.core.deps import get_current_active_user
from app.models.core.user import User

# Import data collection tasks
from app.tasks.price_collector import (
    sync_all_prices,
    sync_historical_data,
    discover_new_cryptocurrencies,
    cleanup_old_data,
    sync_specific_cryptocurrency,
    get_task_status
)

# Import ML tasks 
from app.tasks.ml_tasks import (
    start_auto_training,
    start_prediction_generation,
    start_performance_evaluation,
    start_prediction_cleanup,
    get_task_status as get_ml_task_status
)

# Import scheduler utilities
from app.tasks.scheduler import task_scheduler, get_next_run_times
from app.tasks.celery_app import celery_app

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


# =====================================
# DATA COLLECTION TASK ENDPOINTS (EXISTING)
# =====================================

@router.post("/start", operation_id="start_tasks")
async def start_background_tasks_manually(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Start all background tasks manually
    
    Requires authentication. Initiates all scheduled background tasks
    for data collection and synchronization.
    """
    try:
        logger.info(f"User {current_user.id} starting all background tasks")
        
        # Start data collection tasks
        sync_task_id = sync_all_prices.delay().id
        historical_task_id = sync_historical_data.delay().id
        discovery_task_id = discover_new_cryptocurrencies.delay().id
        
        return {
            "success": True,
            "message": "Background tasks started successfully",
            "tasks": {
                "sync_prices": sync_task_id,
                "sync_historical": historical_task_id,
                "discover_cryptos": discovery_task_id
            },
            "started_by": current_user.email,
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start background tasks: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start tasks: {str(e)}"
        )


@router.post("/sync/prices", operation_id="sync_prices_manually")
async def sync_prices_manually(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Manually trigger price synchronization
    
    Forces immediate price data sync for all active cryptocurrencies.
    """
    try:
        logger.info(f"User {current_user.id} starting manual price sync")
        
        task_id = sync_all_prices.delay().id
        
        return {
            "success": True,
            "message": "Price sync task started",
            "task_id": task_id,
            "task_type": "sync_all_prices",
            "status_endpoint": f"/api/v1/tasks/status/{task_id}",
            "started_by": current_user.email,
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start price sync: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start price sync: {str(e)}"
        )


@router.post("/sync/historical", operation_id="sync_historical_manually")
async def sync_historical_manually(
    days_back: int = 30,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Manually trigger historical data synchronization
    """
    try:
        logger.info(f"User {current_user.id} starting historical sync for {days_back} days")
        
        task_id = sync_historical_data.delay(days_back=days_back).id
        
        return {
            "success": True,
            "message": "Historical sync task started",
            "task_id": task_id,
            "task_type": "sync_historical_data",
            "days_back": days_back,
            "status_endpoint": f"/api/v1/tasks/status/{task_id}",
            "started_by": current_user.email,
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start historical sync: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start historical sync: {str(e)}"
        )


@router.post("/discover", operation_id="discover_cryptocurrencies_manually")
async def discover_cryptocurrencies_manually(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Manually trigger cryptocurrency discovery
    """
    try:
        logger.info(f"User {current_user.id} starting cryptocurrency discovery")
        
        task_id = discover_new_cryptocurrencies.delay().id
        
        return {
            "success": True,
            "message": "Cryptocurrency discovery task started",
            "task_id": task_id,
            "task_type": "discover_new_cryptocurrencies",
            "status_endpoint": f"/api/v1/tasks/status/{task_id}",
            "started_by": current_user.email,
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start discovery: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start discovery: {str(e)}"
        )


@router.post("/cleanup", operation_id="cleanup_old_data_manually")
async def cleanup_old_data_manually(
    days_to_keep: int = 90,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Manually trigger data cleanup
    """
    try:
        if days_to_keep < 7 or days_to_keep > 365:
            raise HTTPException(
                status_code=400,
                detail="days_to_keep must be between 7 and 365"
            )
        
        logger.info(f"User {current_user.id} starting data cleanup (keeping {days_to_keep} days)")
        
        task_id = cleanup_old_data.delay(days_to_keep=days_to_keep).id
        
        return {
            "success": True,
            "message": "Data cleanup task started",
            "task_id": task_id,
            "task_type": "cleanup_old_data",
            "days_to_keep": days_to_keep,
            "status_endpoint": f"/api/v1/tasks/status/{task_id}",
            "started_by": current_user.email,
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start cleanup: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start cleanup: {str(e)}"
        )


# =====================================
# ML TASK ENDPOINTS 
# =====================================

@router.post("/ml/auto-train", operation_id="start_ml_auto_training")
async def start_ml_auto_training(
    force_retrain: bool = False,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Start automatic model training for all cryptocurrencies
    
    Requires authentication. Trains ML models for all active cryptocurrencies.
    This process can take 30-120 minutes depending on the amount of data and
    number of cryptocurrencies.
    """
    try:
        logger.info(f"User {current_user.id} starting auto ML training (force_retrain: {force_retrain})")
        
        # Start the training task
        task_id = start_auto_training(force_retrain=force_retrain)
        
        return {
            "success": True,
            "message": "Auto training task started successfully",
            "task_id": task_id,
            "task_type": "auto_train_models",
            "force_retrain": force_retrain,
            "status_endpoint": f"/api/v1/tasks/ml/status/{task_id}",
            "estimated_duration": "30-120 minutes",
            "started_by": current_user.email,
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start auto training: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start auto training: {str(e)}"
        )


@router.post("/ml/predictions/generate", operation_id="start_prediction_generation")
async def start_prediction_generation(
    crypto_symbols: Optional[List[str]] = None,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Start scheduled prediction generation
    
    Requires authentication. Generates predictions for specified or all cryptocurrencies.
    If crypto_symbols is not provided, predictions will be generated for all active
    cryptocurrencies with trained models.
    """
    try:
        symbols_text = f"for {len(crypto_symbols)} specific cryptocurrencies" if crypto_symbols else "for all cryptocurrencies"
        logger.info(f"User {current_user.id} starting prediction generation {symbols_text}")
        
        # Start the prediction generation task
        task_id = start_prediction_generation(crypto_symbols=crypto_symbols)
        
        return {
            "success": True,
            "message": "Prediction generation task started successfully",
            "task_id": task_id,
            "task_type": "generate_scheduled_predictions",
            "crypto_symbols": crypto_symbols,
            "status_endpoint": f"/api/v1/tasks/ml/status/{task_id}",
            "estimated_duration": "5-15 minutes",
            "started_by": current_user.email,
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start prediction generation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start prediction generation: {str(e)}"
        )


@router.post("/ml/performance/evaluate", operation_id="start_ml_performance_evaluation")
async def start_ml_performance_evaluation(
    crypto_symbol: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Start model performance evaluation
    
    Requires authentication. Evaluates the accuracy and performance of prediction models
    by comparing predictions with actual market prices. If crypto_symbol is not provided,
    all cryptocurrencies will be evaluated.
    """
    try:
        eval_text = f"for {crypto_symbol}" if crypto_symbol else "for all cryptocurrencies"
        logger.info(f"User {current_user.id} starting performance evaluation {eval_text}")
        
        # Start the performance evaluation task
        task_id = start_performance_evaluation(crypto_symbol=crypto_symbol)
        
        return {
            "success": True,
            "message": "Performance evaluation task started successfully",
            "task_id": task_id,
            "task_type": "evaluate_model_performance",
            "crypto_symbol": crypto_symbol,
            "status_endpoint": f"/api/v1/tasks/ml/status/{task_id}",
            "estimated_duration": "10-30 minutes",
            "started_by": current_user.email,
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start performance evaluation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start performance evaluation: {str(e)}"
        )


@router.post("/ml/cleanup", operation_id="start_prediction_cleanup")
async def start_prediction_cleanup(
    days_to_keep: int = 90,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Start prediction data cleanup
    
    Requires authentication. Cleans up old prediction data to manage database size.
    Only predictions older than the specified days will be removed, while preserving
    recent data for analytics and model evaluation.
    """
    try:
        if days_to_keep < 7 or days_to_keep > 365:
            raise HTTPException(
                status_code=400,
                detail="days_to_keep must be between 7 and 365"
            )
        
        logger.info(f"User {current_user.id} starting prediction cleanup (keeping {days_to_keep} days)")
        
        # Start the cleanup task
        task_id = start_prediction_cleanup(days_to_keep=days_to_keep)
        
        return {
            "success": True,
            "message": "Prediction cleanup task started successfully",
            "task_id": task_id,
            "task_type": "cleanup_old_predictions",
            "days_to_keep": days_to_keep,
            "status_endpoint": f"/api/v1/tasks/ml/status/{task_id}",
            "estimated_duration": "5-15 minutes",
            "started_by": current_user.email,
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start prediction cleanup: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start prediction cleanup: {str(e)}"
        )


@router.get("/ml/status/{task_id}", operation_id="get_ml_task_status")
async def get_ml_task_status_endpoint(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get status of ML task
    
    Requires authentication. Returns detailed status of ML background tasks
    including progress, results, and any errors that may have occurred.
    """
    try:
        # Get task status
        task_status = get_ml_task_status(task_id)
        
        return {
            "success": True,
            "task_status": task_status,
            "requested_by": current_user.email,
            "requested_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get ML task status {task_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {str(e)}"
        )


# =====================================
# GENERAL TASK STATUS AND INFO ENDPOINTS
# =====================================

@router.get("/status/{task_id}", operation_id="get_task_status")
async def get_task_status_endpoint(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get status of any background task
    """
    try:
        # Try to get status from data collection tasks first
        task_status = get_task_status(task_id)
        
        return {
            "success": True,
            "task_status": task_status,
            "requested_by": current_user.email,
            "requested_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get task status {task_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.get("/schedule", operation_id="get_task_schedule")
async def get_task_schedule(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get scheduled task information
    
    Returns comprehensive information about all scheduled tasks including
    next run times, schedules, and task categories.
    """
    try:
        logger.info(f"User {current_user.id} requesting task schedule")
        
        # Get next run times for all tasks
        next_runs = get_next_run_times()
        
        # Get schedule info from scheduler
        schedule_info = task_scheduler.get_schedule_info()
        
        return {
            "success": True,
            "message": "Task schedule retrieved successfully",
            "next_runs": next_runs,
            "schedule_info": schedule_info,
            "requested_by": current_user.email,
            "requested_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get task schedule: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task schedule: {str(e)}"
        )


@router.get("/info", operation_id="get_task_info")
async def get_task_info(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get comprehensive task system information
    
    Returns detailed information about available tasks, their purposes,
    schedules, and management endpoints.
    """
    try:
        logger.info(f"User {current_user.id} requesting task info")
        
        # Get Celery worker status
        try:
            inspect = celery_app.control.inspect()
            active_workers = inspect.active()
            worker_stats = inspect.stats()
            
            celery_status = {
                "workers_online": len(active_workers) if active_workers else 0,
                "active_tasks": sum(len(tasks) for tasks in active_workers.values()) if active_workers else 0,
                "worker_stats": worker_stats
            }
        except Exception as e:
            logger.warning(f"Could not get Celery status: {str(e)}")
            celery_status = {
                "workers_online": "unknown",
                "active_tasks": "unknown",
                "error": str(e)
            }
        
        return {
            "success": True,
            "message": "Task system information retrieved successfully",
            "system_info": {
                "celery_status": celery_status,
                "total_task_types": 12,  # 8 data collection + 4 ML tasks
                "data_collection_tasks": 4,
                "ml_tasks": 4
            },
            "available_tasks": {
                # Data Collection Tasks
                "sync_all_prices": {
                    "description": "Synchronize current price data for all cryptocurrencies",
                    "endpoint": "/api/v1/tasks/sync/prices",
                    "method": "POST",
                    "schedule": "Every 5 minutes",
                    "type": "periodic/manual",
                    "estimated_duration": "2-5 minutes",
                    "dependencies": ["External APIs", "Database"],
                    "category": "data_collection"
                },
                "sync_historical_data": {
                    "description": "Synchronize historical price data for backtesting",
                    "endpoint": "/api/v1/tasks/sync/historical",
                    "method": "POST",
                    "schedule": "Every hour",
                    "type": "periodic/manual",
                    "estimated_duration": "5-15 minutes",
                    "dependencies": ["External APIs", "Database"],
                    "category": "data_collection",
                    "parameters": {
                        "days_back": "integer - Number of days to sync (default: 30)"
                    }
                },
                "discover_new_cryptocurrencies": {
                    "description": "Discover and add new cryptocurrencies to the system",
                    "endpoint": "/api/v1/tasks/discover",
                    "method": "POST",
                    "schedule": "Daily at 2:00 AM",
                    "type": "periodic/manual",
                    "estimated_duration": "3-10 minutes",
                    "dependencies": ["External APIs", "Database"],
                    "category": "data_collection"
                },
                "cleanup_old_data": {
                    "description": "Remove old price data to manage database size",
                    "endpoint": "/api/v1/tasks/cleanup",
                    "method": "POST",
                    "schedule": "Weekly on Sunday at 3:00 AM",
                    "type": "periodic/manual",
                    "estimated_duration": "5-20 minutes",
                    "dependencies": ["Database"],
                    "category": "data_collection",
                    "parameters": {
                        "days_to_keep": "integer - Days of data to retain (7-365)"
                    }
                },
                
                # ML Tasks 
                "auto_train_models": {
                    "description": "Automatically train ML models for all cryptocurrencies",
                    "endpoint": "/api/v1/tasks/ml/auto-train",
                    "method": "POST",
                    "schedule": "Weekly on Sunday at 1:00 AM",
                    "type": "periodic/manual",
                    "estimated_duration": "30-120 minutes",
                    "dependencies": ["Database", "Model Storage", "Price Data"],
                    "category": "machine_learning",
                    "parameters": {
                        "force_retrain": "boolean - Force retrain even if models are recent"
                    }
                },
                "generate_scheduled_predictions": {
                    "description": "Generate predictions for all active cryptocurrencies",
                    "endpoint": "/api/v1/tasks/ml/predictions/generate",
                    "method": "POST", 
                    "schedule": "Every 4 hours",
                    "type": "periodic/manual",
                    "estimated_duration": "5-15 minutes",
                    "dependencies": ["Trained Models", "Database", "Price Data"],
                    "category": "machine_learning",
                    "parameters": {
                        "crypto_symbols": "array - Specific cryptocurrencies or null for all"
                    }
                },
                "evaluate_model_performance": {
                    "description": "Evaluate accuracy and performance of prediction models",
                    "endpoint": "/api/v1/tasks/ml/performance/evaluate",
                    "method": "POST",
                    "schedule": "Daily at 6:00 AM", 
                    "type": "periodic/manual",
                    "estimated_duration": "10-30 minutes",
                    "dependencies": ["Database", "Realized Predictions"],
                    "category": "machine_learning",
                    "parameters": {
                        "crypto_symbol": "string - Specific cryptocurrency or null for all"
                    }
                },
                "cleanup_old_predictions": {
                    "description": "Clean up old prediction data to manage database size",
                    "endpoint": "/api/v1/tasks/ml/cleanup",
                    "method": "POST",
                    "schedule": "Weekly on Sunday at 4:00 AM",
                    "type": "periodic/manual", 
                    "estimated_duration": "5-15 minutes",
                    "dependencies": ["Database"],
                    "category": "machine_learning",
                    "parameters": {
                        "days_to_keep": "integer - Days of data to retain (7-365)"
                    }
                }
            },
            "management_endpoints": {
                "get_task_status": "GET /api/v1/tasks/status/{task_id}",
                "get_ml_task_status": "GET /api/v1/tasks/ml/status/{task_id}",
                "get_schedule": "GET /api/v1/tasks/schedule",
                "get_info": "GET /api/v1/tasks/info",
                "start_all_tasks": "POST /api/v1/tasks/start",
                "sync_prices": "POST /api/v1/tasks/sync/prices",
                "sync_historical": "POST /api/v1/tasks/sync/historical",
                "discover_cryptos": "POST /api/v1/tasks/discover",
                "cleanup_data": "POST /api/v1/tasks/cleanup",
                "ml_auto_train": "POST /api/v1/tasks/ml/auto-train",
                "ml_generate_predictions": "POST /api/v1/tasks/ml/predictions/generate", 
                "ml_evaluate_performance": "POST /api/v1/tasks/ml/performance/evaluate",
                "ml_cleanup_predictions": "POST /api/v1/tasks/ml/cleanup"
            },
            "startup_commands": {
                "celery_worker": "celery -A app.tasks.celery_app worker --loglevel=info",
                "celery_beat": "celery -A app.tasks.celery_app beat --loglevel=info",
                "flower_monitoring": "celery -A app.tasks.celery_app flower",
                "ml_worker_only": "celery -A app.tasks.celery_app worker --loglevel=info --queues=ml_tasks",
                "combined_worker": "celery -A app.tasks.celery_app worker --loglevel=info --queues=price_data,ml_tasks"
            },
            "requested_by": current_user.email,
            "requested_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get task info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task info: {str(e)}"
        )