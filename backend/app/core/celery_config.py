# backend/app/core/celery_config.py
"""
Celery Configuration Settings - Updated to Fix Warnings
Provides centralized configuration for Celery background tasks with proper settings
"""

from typing import Dict, Any
import os
from kombu import Exchange, Queue


class CeleryConfig:
    """
    Celery configuration class containing all settings for background tasks
    Updated to fix deprecation warnings
    """
    
    # Redis Broker Configuration
    broker_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    result_backend: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Task Serialization
    task_serializer: str = "json"
    result_serializer: str = "json"
    accept_content: list = ["json"]
    
    # Timezone Configuration
    timezone: str = "UTC"
    enable_utc: bool = True
    
    # Broker Connection Settings (FIX FOR WARNINGS)
    broker_connection_retry_on_startup: bool = True
    broker_connection_retry: bool = True
    broker_connection_max_retries: int = 10
    
    # Task Routing
    task_routes: Dict[str, Dict[str, Any]] = {
        "app.tasks.price_collector.*": {"queue": "price_data"},
        "app.tasks.scheduler.*": {"queue": "scheduling"},
    }
    
    # Queue Configuration
    task_default_queue: str = "default"
    task_queues = (
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("price_data", Exchange("price_data"), routing_key="price_data"),
        Queue("scheduling", Exchange("scheduling"), routing_key="scheduling"),
    )
    
    # Worker Configuration
    worker_prefetch_multiplier: int = 1
    task_acks_late: bool = True
    task_reject_on_worker_lost: bool = True
    
    # Task Execution Settings
    task_always_eager: bool = False  # Set to True for testing
    task_eager_propagates: bool = False
    task_ignore_result: bool = False
    
    # Result Backend Settings
    result_expires: int = 3600  # 1 hour
    result_persistent: bool = True
    result_backend_db: int = 0  # Redis database number
    
    # Retry Configuration
    task_retry_delay: int = 60  # 1 minute
    task_max_retries: int = 3
    
    # Monitoring and Logging
    worker_send_task_events: bool = True
    task_send_sent_event: bool = True
    worker_log_format: str = "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
    worker_task_log_format: str = "[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s"
    
    # Performance Settings
    worker_disable_rate_limits: bool = False
    task_compression: str = "gzip"
    result_compression: str = "gzip"
    
    # Security Settings
    task_reject_on_worker_lost: bool = True
    task_acks_late: bool = True
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """
        Get configuration as dictionary for Celery app
        
        Returns:
            dict: Configuration dictionary
        """
        return {
            key: value for key, value in cls.__dict__.items()
            if not key.startswith('_') and not callable(value)
        }