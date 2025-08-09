# backend/app/tasks/celery_app.py
"""
Celery Application Configuration - WINDOWS-SAFE VERSION
Main Celery app instance with configuration and task discovery
Enhanced with async/await compatibility - Windows encoding compatible
"""

from celery import Celery
from celery.schedules import crontab
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.celery_config import CeleryConfig, AsyncCeleryConfig

# Enable nest_asyncio as early as possible
try:
    import nest_asyncio
    nest_asyncio.apply()
    print("SUCCESS: nest_asyncio enabled successfully")
except ImportError:
    print("WARNING: nest_asyncio not available - install with: pip install nest-asyncio")
except Exception as e:
    print(f"WARNING: nest_asyncio setup failed: {e}")


def create_celery_app() -> Celery:
    """
    Create and configure Celery application with async support
    
    Returns:
        Celery: Configured Celery application instance with async compatibility
    """
    
    # Create Celery instance with proper app name
    celery_app = Celery("crypto_predict")
    
    # Load configuration from CeleryConfig class
    celery_app.config_from_object(CeleryConfig)
    
    # Apply async-specific configuration
    AsyncCeleryConfig.apply_async_settings(celery_app)
    
    # Configure periodic tasks (Celery Beat) with enhanced scheduling
    celery_app.conf.beat_schedule = {
        # High Priority: Real-time price sync every 5 minutes
        "sync-prices-every-5-minutes": {
            "task": "app.tasks.price_collector.sync_all_prices",
            "schedule": 300.0,  # 5 minutes in seconds
            "options": {
                "queue": "price_data",
                "priority": 8,
                "expires": 240  # Task expires in 4 minutes if not picked up
            }
        },
        
        # Medium Priority: Historical data sync every hour
        "sync-historical-every-hour": {
            "task": "app.tasks.price_collector.sync_historical_data", 
            "schedule": crontab(minute=0),  # Every hour at minute 0
            "options": {
                "queue": "price_data",
                "priority": 6,
                "expires": 3300  # Task expires in 55 minutes
            }
        },
        
        # Low Priority: Discover new cryptocurrencies daily at 2 AM
        "discover-new-cryptos-daily": {
            "task": "app.tasks.price_collector.discover_new_cryptocurrencies",
            "schedule": crontab(hour=2, minute=0),  # 2:00 AM daily
            "options": {
                "queue": "scheduling",
                "priority": 4,
                "expires": 21600  # Task expires in 6 hours
            }
        },
        
        # Lowest Priority: Cleanup old data weekly on Sunday at 3 AM  
        "cleanup-old-data-weekly": {
            "task": "app.tasks.price_collector.cleanup_old_data",
            "schedule": crontab(hour=3, minute=0, day_of_week=0),  # Sunday 3:00 AM
            "options": {
                "queue": "scheduling",
                "priority": 2,
                "expires": 86400  # Task expires in 24 hours
            }
        }
    }
    
    # Auto-discover tasks in the tasks module
    celery_app.autodiscover_tasks([
        "app.tasks.price_collector",
        "app.tasks.scheduler"
    ])
    
    # Add additional async-specific configurations
    _configure_async_settings(celery_app)
    
    return celery_app


def _configure_async_settings(celery_app: Celery) -> None:
    """
    Configure additional async-specific settings for Celery
    
    Args:
        celery_app: Celery application instance to configure
    """
    
    # Set up event loop policy for Windows compatibility
    try:
        import asyncio
        if os.name == 'nt':  # Windows
            # Use SelectorEventLoop on Windows for better compatibility
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            print("SUCCESS: Windows SelectorEventLoopPolicy configured")
    except Exception as e:
        print(f"WARNING: Could not configure event loop policy: {e}")
    
    # Configure worker pool for async tasks
    if os.getenv("ENVIRONMENT") == "development":
        # Development: Use solo pool for easier debugging
        celery_app.conf.worker_pool = "solo"
        print("INFO: Development mode: Using solo worker pool")
    else:
        # Production: Use threads for async compatibility
        celery_app.conf.worker_pool = "threads"
        celery_app.conf.worker_pool_threads = 4
        print("INFO: Production mode: Using threaded worker pool")
    
    # Additional async optimizations
    celery_app.conf.update(
        # Task execution settings for async
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1,  # Better for async tasks
        
        # Connection settings optimized for async
        broker_connection_retry_on_startup=True,
        broker_heartbeat=120,
        broker_heartbeat_checkrate=2.0,
        
        # Memory management for long-running async tasks
        worker_max_tasks_per_child=1000,
        worker_max_memory_per_child=200000,  # 200MB limit
        
        # Enhanced error handling
        task_track_started=True,
        task_send_sent_event=True,
        worker_send_task_events=True
    )


def _setup_signal_handlers(celery_app: Celery) -> None:
    """
    Set up signal handlers for proper async task lifecycle management
    
    Args:
        celery_app: Celery application instance
    """
    
    from celery.signals import task_prerun, task_postrun, task_failure
    
    @task_prerun.connect
    def task_prerun_handler(task_id, task, *args, **kwargs):
        """Handle task pre-run setup for async tasks"""
        print(f"Starting async task: {task.name} [{task_id}]")
    
    @task_postrun.connect
    def task_postrun_handler(task_id, task, *args, **kwargs):
        """Handle task post-run cleanup for async tasks"""
        print(f"Completed async task: {task.name} [{task_id}]")
    
    @task_failure.connect
    def task_failure_handler(task_id, exception, einfo, *args, **kwargs):
        """Handle task failure for async tasks"""
        print(f"Failed async task: {task_id} - {exception}")


# Create the main Celery app instance
celery_app = create_celery_app()

# Set up signal handlers
_setup_signal_handlers(celery_app)


# Enhanced task functions for monitoring and debugging
@celery_app.task(bind=True)
def debug_task(self):
    """
    Debug task for testing Celery functionality with async support
    """
    import asyncio
    
    try:
        # Test async capability
        loop = asyncio.get_event_loop()
        print(f"Debug task running - Loop: {loop}")
        print(f"Request: {self.request!r}")
        
        return {
            "status": "success",
            "message": "Celery with async support is working!",
            "loop_running": loop.is_running(),
            "loop_closed": loop.is_closed()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Debug task failed: {e}"
        }


@celery_app.task
def health_check():
    """
    Enhanced health check task with async environment testing
    
    Returns:
        dict: Health status including async environment info
    """
    import asyncio
    
    try:
        # Test async environment
        loop = asyncio.get_event_loop()
        loop_info = {
            "is_running": loop.is_running(),
            "is_closed": loop.is_closed(),
            "type": str(type(loop))
        }
        
        # Test nest_asyncio
        nest_available = False
        try:
            import nest_asyncio
            nest_available = True
        except ImportError:
            pass
        
        return {
            "status": "healthy",
            "message": "Celery worker with async support is running",
            "broker": celery_app.conf.broker_url,
            "backend": celery_app.conf.result_backend,
            "async_environment": {
                "event_loop": loop_info,
                "nest_asyncio_available": nest_available,
                "worker_pool": celery_app.conf.get("worker_pool", "default")
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Health check failed: {e}",
            "broker": celery_app.conf.broker_url,
            "backend": celery_app.conf.result_backend
        }


@celery_app.task
def test_async_task():
    """
    Test async task execution capability
    
    Returns:
        dict: Test results
    """
    from app.tasks.task_handler import async_task_handler
    
    async def sample_async_operation():
        """Sample async operation for testing"""
        import asyncio
        await asyncio.sleep(0.1)  # Small async delay
        from datetime import datetime
        return {"test": "success", "timestamp": datetime.utcnow().isoformat()}
    
    try:
        import asyncio
        from datetime import datetime
        
        # Test async execution through task handler
        result = async_task_handler.run_async_task(sample_async_operation)
        
        return {
            "status": "success",
            "message": "Async task execution successful",
            "result": result
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Async task execution failed: {e}"
        }


# Export main app instance
app = celery_app

# For backward compatibility
__all__ = ['app', 'celery_app', 'create_celery_app']