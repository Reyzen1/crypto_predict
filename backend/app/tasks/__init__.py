# backend/app/tasks/__init__.py
"""
Background Tasks Package
Contains all Celery tasks for automated data collection and processing
"""

from .celery_app import celery_app
from .price_collector import (
    sync_all_prices,
    sync_historical_data,
    discover_new_cryptocurrencies,
    cleanup_old_data
)

# Export main components
__all__ = [
    "celery_app",
    "sync_all_prices", 
    "sync_historical_data",
    "discover_new_cryptocurrencies",
    "cleanup_old_data"
]