# File: backend/app/tasks/scheduler.py
# Task Scheduler Utilities with ML Tasks Integration
# Enhanced scheduler for managing both data collection and ML tasks

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, timezone
import logging
from celery import current_app
from celery.schedules import crontab
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import data collection tasks
from app.tasks.price_collector import (
    sync_all_prices,
    sync_historical_data,
    discover_new_cryptocurrencies,
    cleanup_old_data
)

# Import ML tasks (NEW)
from app.tasks.ml_tasks import (
    auto_train_models,
    generate_scheduled_predictions,
    evaluate_model_performance,
    cleanup_old_predictions
)

# Setup logging
logger = logging.getLogger(__name__)


class TaskScheduler:
    """
    Enhanced task scheduler utility class for managing Celery periodic tasks
    
    Manages both data collection tasks and ML/AI tasks with proper scheduling
    and monitoring capabilities. Provides centralized control over all
    background operations in the CryptoPredict system.
    """
    
    def __init__(self):
        """Initialize task scheduler with Celery app"""
        self.celery_app = current_app
        
    def setup_periodic_tasks(self):
        """
        Configure all periodic tasks for the application
        
        Sets up both data collection and ML tasks with appropriate
        schedules based on operational requirements and resource constraints.
        """
        try:
            logger.info("Setting up periodic tasks...")
            
            # ============= DATA COLLECTION TASKS =============
            
            # Sync prices every 5 minutes for real-time data
            self.celery_app.conf.beat_schedule['sync-prices-every-5-minutes'] = {
                'task': 'price_collector.sync_all_prices',
                'schedule': crontab(minute='*/5'),  # Every 5 minutes
                'options': {'queue': 'price_data'}
            }
            
            # Sync historical data every hour for backfill
            self.celery_app.conf.beat_schedule['sync-historical-every-hour'] = {
                'task': 'price_collector.sync_historical_data',
                'schedule': crontab(minute=0),  # Every hour at minute 0
                'options': {'queue': 'price_data'}
            }
            
            # Discover new cryptocurrencies daily
            self.celery_app.conf.beat_schedule['discover-new-cryptos-daily'] = {
                'task': 'price_collector.discover_new_cryptocurrencies',
                'schedule': crontab(hour=2, minute=0),  # Daily at 2:00 AM
                'options': {'queue': 'price_data'}
            }
            
            # Cleanup old data weekly on Sunday
            self.celery_app.conf.beat_schedule['cleanup-old-data-weekly'] = {
                'task': 'price_collector.cleanup_old_data',
                'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Sunday 3:00 AM
                'options': {'queue': 'price_data'}
            }
            
            # ============= ML TASKS (NEW) =============
            
            # Auto train models - Weekly on Sunday at 1:00 AM
            # Scheduled after data cleanup to ensure fresh data
            self.celery_app.conf.beat_schedule['auto-train-models-weekly'] = {
                'task': 'ml_tasks.auto_train_models',
                'schedule': crontab(hour=1, minute=0, day_of_week=0),  # Sunday 1:00 AM
                'args': [False],  # force_retrain=False
                'options': {'queue': 'ml_tasks'}
            }
            
            # Generate scheduled predictions - Every 4 hours
            # Provides regular prediction updates throughout the day
            self.celery_app.conf.beat_schedule['generate-predictions-4hourly'] = {
                'task': 'ml_tasks.generate_scheduled_predictions',
                'schedule': crontab(minute=0, hour='*/4'),  # Every 4 hours at minute 0
                'options': {'queue': 'ml_tasks'}
            }
            
            # Evaluate model performance - Daily at 6:00 AM
            # Runs after overnight price updates to assess previous day's predictions
            self.celery_app.conf.beat_schedule['evaluate-model-performance-daily'] = {
                'task': 'ml_tasks.evaluate_model_performance',
                'schedule': crontab(hour=6, minute=0),  # Every day at 6:00 AM
                'options': {'queue': 'ml_tasks'}
            }
            
            # Cleanup old predictions - Weekly on Sunday at 4:00 AM
            # Maintains database performance by removing outdated predictions
            self.celery_app.conf.beat_schedule['cleanup-old-predictions-weekly'] = {
                'task': 'ml_tasks.cleanup_old_predictions',
                'schedule': crontab(hour=4, minute=0, day_of_week=0),  # Sunday 4:00 AM
                'args': [90],  # days_to_keep=90
                'options': {'queue': 'ml_tasks'}
            }
            
            # Set timezone for all scheduled tasks
            self.celery_app.conf.timezone = 'UTC'
            
            logger.info("Periodic tasks setup completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup periodic tasks: {str(e)}")
            raise
        
    def get_schedule_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about all scheduled tasks
        
        Returns detailed information about both data collection and ML tasks
        including their schedules, queues, and current status.
        
        Returns:
            dict: Complete schedule information
        """
        try:
            schedule = self.celery_app.conf.beat_schedule
            
            schedule_info = {}
            for task_name, task_config in schedule.items():
                schedule_info[task_name] = {
                    "task": task_config["task"],
                    "schedule": str(task_config["schedule"]),
                    "queue": task_config.get("options", {}).get("queue", "default"),
                    "args": task_config.get("args", []),
                    "kwargs": task_config.get("kwargs", {}),
                    "enabled": True,  # All tasks are enabled by default
                    "category": self._categorize_task(task_config["task"])
                }
            
            return {
                "status": "success",
                "schedule_count": len(schedule_info),
                "schedules": schedule_info,
                "timezone": self.celery_app.conf.timezone,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get schedule info: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _categorize_task(self, task_name: str) -> str:
        """
        Categorize task based on its name
        
        Args:
            task_name: Full task name
            
        Returns:
            str: Task category
        """
        if "price_collector" in task_name:
            return "data_collection"
        elif "ml_tasks" in task_name:
            return "machine_learning"
        else:
            return "general"
    
    def schedule_one_time_task(self, task_name: str, eta: datetime, **kwargs) -> Dict[str, Any]:
        """
        Schedule a one-time task to run at a specific time
        
        Useful for on-demand ML training, data synchronization, or
        maintenance tasks that need to run outside regular schedule.
        
        Args:
            task_name: Name of task to schedule
            eta: When to run the task
            **kwargs: Additional arguments for the task
            
        Returns:
            dict: Scheduling result
        """
        try:
            # Get the actual task function
            task_func = self.celery_app.tasks.get(task_name)
            
            if not task_func:
                return {
                    "status": "error",
                    "error": f"Task {task_name} not found",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            # Schedule the task
            result = task_func.apply_async(eta=eta, kwargs=kwargs)
            
            return {
                "status": "success",
                "message": f"Task {task_name} scheduled",
                "task_id": result.id,
                "task_name": task_name,
                "eta": eta.isoformat(),
                "kwargs": kwargs,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to schedule task {task_name}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "task_name": task_name,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


# =====================================
# HELPER FUNCTIONS FOR SCHEDULE CALCULATION
# =====================================

def _get_next_cron_run(hour: int, minute: int, day_of_week: Optional[int] = None) -> str:
    """
    Calculate next run time for cron-based schedules
    
    Args:
        hour: Hour to run (0-23)
        minute: Minute to run (0-59)
        day_of_week: Day of week (0=Sunday, 6=Saturday), None for daily
        
    Returns:
        str: ISO format next run time
    """
    try:
        now = datetime.now(timezone.utc)
        
        if day_of_week is not None:
            # Weekly schedule
            days_ahead = day_of_week - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            next_run += timedelta(days=days_ahead)
        else:
            # Daily schedule
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        
        return next_run.isoformat()
    except Exception as e:
        logger.error(f"Error calculating next cron run time: {str(e)}")
        return "Unknown"


def _get_next_interval_run(interval_hours: int, minute: int = 0) -> str:
    """
    Calculate next run time for interval-based schedules
    
    Args:
        interval_hours: Hour interval (e.g., 4 for every 4 hours)
        minute: Minute to run at
        
    Returns:
        str: ISO format next run time
    """
    try:
        now = datetime.now(timezone.utc)
        
        # Find the next hour that's divisible by the interval
        current_hour = now.hour
        hours_since_midnight = current_hour
        next_interval_hour = ((hours_since_midnight // interval_hours) + 1) * interval_hours
        
        if next_interval_hour >= 24:
            # Next day
            next_run = now.replace(hour=0, minute=minute, second=0, microsecond=0)
            next_run += timedelta(days=1)
        else:
            next_run = now.replace(hour=next_interval_hour, minute=minute, second=0, microsecond=0)
        
        return next_run.isoformat()
    except Exception as e:
        logger.error(f"Error calculating next interval run time: {str(e)}")
        return "Unknown"


# =====================================
# GLOBAL FUNCTIONS
# =====================================

# Global scheduler instance
task_scheduler = TaskScheduler()


def get_next_run_times() -> Dict[str, Any]:
    """
    Calculate next run times for all scheduled tasks
    
    Provides comprehensive information about when each task will run next,
    including both data collection and ML tasks. Useful for monitoring
    and planning system operations.
    
    Returns:
        dict: Next run times for each task with detailed information
    """
    try:
        now = datetime.now(timezone.utc)
        
        # Calculate next run times for all scheduled tasks
        next_runs = {
            # Data Collection Tasks
            "sync-prices-every-5-minutes": {
                "next_run": _get_next_interval_run(0, now.minute + (5 - now.minute % 5) % 5),
                "pattern": "Every 5 minutes",
                "category": "data_collection",
                "queue": "price_data"
            },
            "sync-historical-every-hour": {
                "next_run": _get_next_cron_run((now.hour + 1) % 24, 0),
                "pattern": "Every hour at minute 0",
                "category": "data_collection", 
                "queue": "price_data"
            },
            "discover-new-cryptos-daily": {
                "next_run": _get_next_cron_run(2, 0),
                "pattern": "Daily at 2:00 AM",
                "category": "data_collection",
                "queue": "price_data"
            },
            "cleanup-old-data-weekly": {
                "next_run": _get_next_cron_run(3, 0, day_of_week=0),
                "pattern": "Weekly on Sunday at 3:00 AM",
                "category": "data_collection",
                "queue": "price_data"
            },
            
            # ML Tasks 
            "auto-train-models-weekly": {
                "next_run": _get_next_cron_run(1, 0, day_of_week=0),
                "pattern": "Weekly on Sunday at 1:00 AM",
                "category": "machine_learning",
                "queue": "ml_tasks"
            },
            "generate-predictions-4hourly": {
                "next_run": _get_next_interval_run(hour_interval=4, minute=0),
                "pattern": "Every 4 hours at minute 0", 
                "category": "machine_learning",
                "queue": "ml_tasks"
            },
            "evaluate-model-performance-daily": {
                "next_run": _get_next_cron_run(6, 0),
                "pattern": "Daily at 6:00 AM",
                "category": "machine_learning",
                "queue": "ml_tasks"
            },
            "cleanup-old-predictions-weekly": {
                "next_run": _get_next_cron_run(4, 0, day_of_week=0),
                "pattern": "Weekly on Sunday at 4:00 AM",
                "category": "machine_learning",
                "queue": "ml_tasks"
            }
        }
        
        # Add time until next run for each task
        for task_name, task_info in next_runs.items():
            try:
                next_run_time = datetime.fromisoformat(task_info["next_run"])
                time_until = next_run_time - now
                task_info["time_until"] = str(time_until)
                task_info["time_until_seconds"] = int(time_until.total_seconds())
            except Exception as e:
                logger.error(f"Error calculating time until for {task_name}: {str(e)}")
                task_info["time_until"] = "Unknown"
                task_info["time_until_seconds"] = 0
        
        return {
            "status": "success",
            "current_time": now.isoformat(),
            "total_tasks": len(next_runs),
            "data_collection_tasks": len([t for t in next_runs.values() if t["category"] == "data_collection"]),
            "ml_tasks": len([t for t in next_runs.values() if t["category"] == "machine_learning"]),
            "next_runs": next_runs,
            "timestamp": now.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate next run times: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


def setup_all_periodic_tasks():
    """
    Convenience function to setup all periodic tasks
    
    This function should be called during application startup to ensure
    all scheduled tasks are properly configured.
    """
    try:
        task_scheduler.setup_periodic_tasks()
        logger.info("All periodic tasks have been setup successfully")
    except Exception as e:
        logger.error(f"Failed to setup periodic tasks: {str(e)}")
        raise


def get_task_categories() -> Dict[str, List[str]]:
    """
    Get tasks organized by category
    
    Returns:
        dict: Tasks grouped by category (data_collection, machine_learning)
    """
    return {
        "data_collection": [
            "sync-prices-every-5-minutes",
            "sync-historical-every-hour", 
            "discover-new-cryptos-daily",
            "cleanup-old-data-weekly"
        ],
        "machine_learning": [
            "auto-train-models-weekly",
            "generate-predictions-4hourly",
            "evaluate-model-performance-daily",
            "cleanup-old-predictions-weekly"
        ]
    }