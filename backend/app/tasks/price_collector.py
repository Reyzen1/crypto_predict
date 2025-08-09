# backend/app/tasks/price_collector.py
"""
Price Collection Background Tasks - WINDOWS-SAFE VERSION
Automated tasks for cryptocurrency data collection and synchronization
"""

from celery import shared_task
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import the new async task handler
from app.tasks.task_handler import celery_async_task, async_task_handler

from app.services.data_sync import DataSyncService
from app.services.external_api import ExternalAPIService
from app.repositories import cryptocurrency_repository, price_data_repository
from app.core.database import SessionLocal

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_services() -> tuple:
    """
    Get service instances for database operations
    
    Returns:
        tuple: (data_sync_service, external_api_service, crypto_repo, price_repo, db_session)
    """
    try:
        # Get database session
        db_session = SessionLocal()
        
        # Use global repository instances (no session parameter needed)
        crypto_repo = cryptocurrency_repository
        price_repo = price_data_repository
        
        # Initialize services 
        external_api_service = ExternalAPIService()
        data_sync_service = DataSyncService()
        
        return data_sync_service, external_api_service, crypto_repo, price_repo, db_session
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


# Async wrapper functions for data sync operations
@celery_async_task
async def _async_sync_all_prices() -> Dict[str, Any]:
    """
    Async wrapper for sync_all_prices operation
    
    Returns:
        dict: Synchronization result
    """
    try:
        logger.info("Starting cryptocurrency price sync")
        data_sync_service, external_api_service, crypto_repo, price_repo, db_session = get_services()
        
        try:
            # Perform price synchronization
            result = await data_sync_service.sync_current_prices()
            logger.info(f"Price sync completed: {result}")
            return result
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"Price sync failed: {e}")
        return {
            "success": 0,
            "failed": 2,  # Assuming BTC and ETH at minimum
            "error": str(e),
            "message": "Price sync failed"
        }


@celery_async_task  
async def _async_sync_historical_data(days: int = 30) -> Dict[str, Any]:
    """
    Async wrapper for historical data synchronization
    
    Args:
        days: Number of days of historical data to sync
        
    Returns:
        dict: Synchronization result
    """
    try:
        logger.info(f"Starting historical data sync for {days} days")
        data_sync_service, external_api_service, crypto_repo, price_repo, db_session = get_services()
        
        try:
            # Perform historical data sync
            result = await data_sync_service.sync_historical_data(days=days)
            logger.info(f"Historical sync completed: {result}")
            return result
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"Historical sync failed: {e}")
        return {
            "success": 0,
            "failed": 1,
            "error": str(e),
            "message": "Historical sync failed"
        }


@celery_async_task
async def _async_discover_new_cryptocurrencies() -> Dict[str, Any]:
    """
    Async wrapper for cryptocurrency discovery
    
    Returns:
        dict: Discovery result
    """
    try:
        logger.info("Starting new cryptocurrency discovery")
        data_sync_service, external_api_service, crypto_repo, price_repo, db_session = get_services()
        
        try:
            # Perform cryptocurrency discovery
            result = await data_sync_service.discover_new_cryptocurrencies()
            logger.info(f"Discovery completed: {result}")
            return result
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        return {
            "success": 0,
            "failed": 1,
            "error": str(e),
            "message": "Discovery failed"
        }


@celery_async_task
async def _async_cleanup_old_data(days_to_keep: int = 365) -> Dict[str, Any]:
    """
    Async wrapper for data cleanup
    
    Args:
        days_to_keep: Number of days to keep in database
        
    Returns:
        dict: Cleanup result
    """
    try:
        logger.info(f"Starting data cleanup (keeping {days_to_keep} days)")
        data_sync_service, external_api_service, crypto_repo, price_repo, db_session = get_services()
        
        try:
            # Perform data cleanup
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Delete old price data
            deleted_prices = price_repo.delete_old_data(db_session, cutoff_date)
            
            result = {
                "success": True,
                "deleted_records": deleted_prices,
                "cutoff_date": cutoff_date.isoformat(),
                "message": f"Cleanup completed: {deleted_prices} records deleted"
            }
            
            logger.info(f"Cleanup completed: {result}")
            return result
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Cleanup failed"
        }


# Celery shared tasks (sync versions that call async wrappers)
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_all_prices(self) -> Dict[str, Any]:
    """
    Sync current prices for all cryptocurrencies
    
    This task runs every 5 minutes to keep price data up-to-date
    
    Returns:
        dict: Synchronization result with task metadata
    """
    task_id = self.request.id
    logger.info(f"Starting sync_all_prices task {task_id}")
    
    try:
        # Execute async operation using task handler
        result = _async_sync_all_prices()
        
        # Add task metadata
        result.update({
            "task_id": task_id,
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"sync_all_prices completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"sync_all_prices failed: {str(e)}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying sync_all_prices (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        # Final failure
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e),
            "retries": self.request.retries,
            "timestamp": datetime.utcnow().isoformat()
        }


@shared_task(bind=True, max_retries=3, default_retry_delay=180)  
def sync_historical_data(self, days: int = 30) -> Dict[str, Any]:
    """
    Sync historical data for all cryptocurrencies
    
    This task runs every hour to backfill historical data
    
    Args:
        days: Number of days of historical data to sync
        
    Returns:
        dict: Synchronization result with task metadata
    """
    task_id = self.request.id
    logger.info(f"Starting sync_historical_data task {task_id} for {days} days")
    
    try:
        # Execute async operation using task handler  
        result = _async_sync_historical_data(days)
        
        # Add task metadata
        result.update({
            "task_id": task_id,
            "status": "completed", 
            "days_synced": days,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"sync_historical_data completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"sync_historical_data failed: {str(e)}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying sync_historical_data (attempt {self.request.retries + 1})")
            raise self.retry(countdown=180 * (self.request.retries + 1))
        
        # Final failure
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e),
            "retries": self.request.retries,
            "timestamp": datetime.utcnow().isoformat()
        }


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def discover_new_cryptocurrencies(self) -> Dict[str, Any]:
    """
    Discover and add new cryptocurrencies to the database
    
    This task runs daily to find new cryptocurrencies
    
    Returns:
        dict: Discovery result with task metadata
    """
    task_id = self.request.id
    logger.info(f"Starting discover_new_cryptocurrencies task {task_id}")
    
    try:
        # Execute async operation using task handler
        result = _async_discover_new_cryptocurrencies()
        
        # Add task metadata
        result.update({
            "task_id": task_id,
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"discover_new_cryptocurrencies completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"discover_new_cryptocurrencies failed: {str(e)}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying discover_new_cryptocurrencies (attempt {self.request.retries + 1})")
            raise self.retry(countdown=300 * (self.request.retries + 1))
        
        # Final failure
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e),
            "retries": self.request.retries,
            "timestamp": datetime.utcnow().isoformat()
        }


@shared_task(bind=True, max_retries=2, default_retry_delay=600)
def cleanup_old_data(self, days_to_keep: int = 365) -> Dict[str, Any]:
    """
    Clean up old data from the database
    
    This task runs weekly to maintain database size
    
    Args:
        days_to_keep: Number of days to keep in database
        
    Returns:
        dict: Cleanup result with task metadata
    """
    task_id = self.request.id
    logger.info(f"Starting cleanup_old_data task {task_id} (keeping {days_to_keep} days)")
    
    try:
        # Execute async operation using task handler
        result = _async_cleanup_old_data(days_to_keep)
        
        # Add task metadata
        result.update({
            "task_id": task_id,
            "status": "completed",
            "days_kept": days_to_keep,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"cleanup_old_data completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"cleanup_old_data failed: {str(e)}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying cleanup_old_data (attempt {self.request.retries + 1})")
            raise self.retry(countdown=600 * (self.request.retries + 1))
        
        # Final failure
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e),
            "retries": self.request.retries,
            "timestamp": datetime.utcnow().isoformat()
        }


# Additional utility tasks
@shared_task(bind=True)
def sync_specific_cryptocurrency(self, symbol: str, days: int = 7) -> Dict[str, Any]:
    """
    Sync data for a specific cryptocurrency
    
    Args:
        symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
        days: Number of days of historical data to sync
        
    Returns:
        dict: Sync result with task metadata
    """
    task_id = self.request.id
    logger.info(f"Starting sync_specific_cryptocurrency task {task_id} for {symbol}")
    
    try:
        # This could be implemented as needed
        result = {
            "success": True,
            "symbol": symbol,
            "message": f"Sync for {symbol} not yet implemented"
        }
        
        # Add task metadata
        result.update({
            "task_id": task_id,
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return result
        
    except Exception as e:
        logger.error(f"sync_specific_cryptocurrency failed: {str(e)}")
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@shared_task
def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get status of a specific task
    
    Args:
        task_id: Task ID to check
        
    Returns:
        dict: Task status information
    """
    try:
        from celery.result import AsyncResult
        
        result = AsyncResult(task_id)
        
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "task_id": task_id,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Export task functions
__all__ = [
    'sync_all_prices',
    'sync_historical_data', 
    'discover_new_cryptocurrencies',
    'cleanup_old_data',
    'sync_specific_cryptocurrency',
    'get_task_status'
]