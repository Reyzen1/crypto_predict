# backend/app/tasks/scheduler.py
"""
Task Scheduler Utilities
Provides utilities for managing and controlling background task schedules
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from celery import current_app
from celery.schedules import crontab
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Setup logging
logger = logging.getLogger(__name__)


class TaskScheduler:
    """
    Task scheduler utility class for managing Celery periodic tasks
    """
    
    def __init__(self):
        """Initialize task scheduler"""
        self.celery_app = current_app
        
    def get_schedule_info(self) -> Dict[str, Any]:
        """
        Get information about all scheduled tasks
        
        Returns:
            dict: Schedule information
        """
        try:
            schedule = self.celery_app.conf.beat_schedule
            
            schedule_info = {}
            for task_name, task_config in schedule.items():
                schedule_info[task_name] = {
                    "task": task_config["task"],
                    "schedule": str(task_config["schedule"]),
                    "options": task_config.get("options", {}),
                    "enabled": True  # All tasks are enabled by default
                }
            
            return {
                "status": "success",
                "schedule_count": len(schedule_info),
                "schedules": schedule_info,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get schedule info: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_active_tasks(self) -> Dict[str, Any]:
        """
        Get information about currently active tasks
        
        Returns:
            dict: Active tasks information
        """
        try:
            # Get active tasks from Celery inspect
            inspect = self.celery_app.control.inspect()
            
            active_tasks = inspect.active()
            scheduled_tasks = inspect.scheduled()
            reserved_tasks = inspect.reserved()
            
            return {
                "status": "success",
                "active_tasks": active_tasks or {},
                "scheduled_tasks": scheduled_tasks or {},
                "reserved_tasks": reserved_tasks or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get active tasks: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def revoke_task(self, task_id: str, terminate: bool = False) -> Dict[str, Any]:
        """
        Revoke a specific task
        
        Args:
            task_id: ID of task to revoke
            terminate: Whether to terminate the task immediately
            
        Returns:
            dict: Revocation result
        """
        try:
            self.celery_app.control.revoke(task_id, terminate=terminate)
            
            return {
                "status": "success",
                "message": f"Task {task_id} revoked",
                "task_id": task_id,
                "terminated": terminate,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to revoke task {task_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "task_id": task_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def purge_queue(self, queue_name: str = "default") -> Dict[str, Any]:
        """
        Purge all tasks from a specific queue
        
        Args:
            queue_name: Name of queue to purge
            
        Returns:
            dict: Purge result
        """
        try:
            result = self.celery_app.control.purge()
            
            return {
                "status": "success",
                "message": f"Queue {queue_name} purged",
                "queue": queue_name,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to purge queue {queue_name}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "queue": queue_name,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """
        Get statistics about Celery workers
        
        Returns:
            dict: Worker statistics
        """
        try:
            inspect = self.celery_app.control.inspect()
            
            stats = inspect.stats()
            registered_tasks = inspect.registered()
            
            return {
                "status": "success",
                "worker_stats": stats or {},
                "registered_tasks": registered_tasks or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get worker stats: {e}")
            return {
                "status": "error", 
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def schedule_one_time_task(self, task_name: str, eta: datetime, **kwargs) -> Dict[str, Any]:
        """
        Schedule a one-time task to run at a specific time
        
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
                    "timestamp": datetime.utcnow().isoformat()
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
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to schedule task {task_name}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "task_name": task_name,
                "timestamp": datetime.utcnow().isoformat()
            }


# Global scheduler instance
task_scheduler = TaskScheduler()


def get_next_run_times() -> Dict[str, Any]:
    """
    Calculate next run times for all scheduled tasks
    
    Returns:
        dict: Next run times for each task
    """
    try:
        now = datetime.utcnow()
        next_runs = {}
        
        # Define schedule patterns and their next run calculation
        schedules = {
            "sync-prices-every-5-minutes": {
                "interval": 300,  # 5 minutes
                "next_run": now + timedelta(seconds=300 - (now.timestamp() % 300))
            },
            "sync-historical-every-hour": {
                "pattern": "every hour at minute 0",
                "next_run": now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            },
            "discover-new-cryptos-daily": {
                "pattern": "daily at 2:00 AM",
                "next_run": now.replace(hour=2, minute=0, second=0, microsecond=0) + timedelta(days=1)
            },
            "cleanup-old-data-weekly": {
                "pattern": "weekly on Sunday at 3:00 AM", 
                "next_run": now.replace(hour=3, minute=0, second=0, microsecond=0) + timedelta(days=7-now.weekday())
            }
        }
        
        for task_name, schedule_info in schedules.items():
            next_runs[task_name] = {
                "next_run": schedule_info["next_run"].isoformat(),
                "time_until": str(schedule_info["next_run"] - now),
                "pattern": schedule_info.get("pattern", f"every {schedule_info.get('interval', 'unknown')} seconds")
            }
        
        return {
            "status": "success",
            "current_time": now.isoformat(),
            "next_runs": next_runs,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate next run times: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }