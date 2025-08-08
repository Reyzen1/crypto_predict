# backend/app/tasks/celery_app.py
"""
Celery Application Configuration
Main Celery app instance with configuration and task discovery
"""

from celery import Celery
from celery.schedules import crontab
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.celery_config import CeleryConfig


def create_celery_app() -> Celery:
    """
    Create and configure Celery application
    
    Returns:
        Celery: Configured Celery application instance
    """
    
    # Create Celery instance
    celery_app = Celery("crypto_predict")
    
    # Load configuration from CeleryConfig class
    celery_app.config_from_object(CeleryConfig)
    
    # Configure periodic tasks (Celery Beat)
    celery_app.conf.beat_schedule = {
        # Sync current prices every 5 minutes
        "sync-prices-every-5-minutes": {
            "task": "app.tasks.price_collector.sync_all_prices",
            "schedule": 300.0,  # 5 minutes in seconds
            "options": {"queue": "price_data"}
        },
        
        # Sync historical data every hour
        "sync-historical-every-hour": {
            "task": "app.tasks.price_collector.sync_historical_data", 
            "schedule": crontab(minute=0),  # Every hour at minute 0
            "options": {"queue": "price_data"}
        },
        
        # Discover new cryptocurrencies daily at 2 AM
        "discover-new-cryptos-daily": {
            "task": "app.tasks.price_collector.discover_new_cryptocurrencies",
            "schedule": crontab(hour=2, minute=0),  # 2:00 AM daily
            "options": {"queue": "scheduling"}
        },
        
        # Cleanup old data weekly on Sunday at 3 AM  
        "cleanup-old-data-weekly": {
            "task": "app.tasks.price_collector.cleanup_old_data",
            "schedule": crontab(hour=3, minute=0, day_of_week=0),  # Sunday 3:00 AM
            "options": {"queue": "scheduling"}
        }
    }
    
    # Auto-discover tasks in the tasks module
    celery_app.autodiscover_tasks([
        "app.tasks.price_collector",
        "app.tasks.scheduler"
    ])
    
    return celery_app


# Create the main Celery app instance
celery_app = create_celery_app()


@celery_app.task(bind=True)
def debug_task(self):
    """
    Debug task for testing Celery functionality
    """
    print(f"Request: {self.request!r}")
    return "Celery is working!"


# Task health check
@celery_app.task
def health_check():
    """
    Simple health check task
    
    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "message": "Celery worker is running",
        "broker": celery_app.conf.broker_url,
        "backend": celery_app.conf.result_backend
    }

app = celery_app

__all__ = ['app', 'celery_app']