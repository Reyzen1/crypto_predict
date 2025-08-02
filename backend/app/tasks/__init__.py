# File: backend/app/tasks/__init__.py
# Tasks package initialization with ML tasks integration
# Exports all background tasks for easy importing throughout the application

# Import data collection tasks
from .price_collector import (
    sync_all_prices,
    sync_historical_data,
    discover_new_cryptocurrencies,
    cleanup_old_data,
    sync_specific_cryptocurrency,
    get_task_status
)

# Import ML tasks 
from .ml_tasks import (
    auto_train_models,
    generate_scheduled_predictions,
    evaluate_model_performance,
    cleanup_old_predictions,
    start_auto_training,
    start_prediction_generation,
    start_performance_evaluation,
    start_prediction_cleanup,
    get_task_status as get_ml_task_status
)

# Import scheduler and Celery app
from .scheduler import task_scheduler, get_next_run_times, setup_all_periodic_tasks
from .celery_app import celery_app

# Export all task functions and utilities
__all__ = [
    # Data collection tasks
    "sync_all_prices",
    "sync_historical_data", 
    "discover_new_cryptocurrencies",
    "cleanup_old_data",
    "sync_specific_cryptocurrency",
    "get_task_status",
    
    # ML tasks (NEW)
    "auto_train_models",
    "generate_scheduled_predictions", 
    "evaluate_model_performance",
    "cleanup_old_predictions",
    "start_auto_training",
    "start_prediction_generation",
    "start_performance_evaluation",
    "start_prediction_cleanup",
    "get_ml_task_status",
    
    # Task management utilities
    "task_scheduler",
    "get_next_run_times",
    "setup_all_periodic_tasks",
    "celery_app"
]