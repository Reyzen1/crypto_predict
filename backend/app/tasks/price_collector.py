# backend/app/tasks/price_collector.py
"""
Price Collection Background Tasks - FIXED VERSION
Automated tasks for cryptocurrency data collection and synchronization
"""

from celery import shared_task
from typing import Dict, List, Any, Optional
import asyncio
import logging
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.services.data_sync import DataSyncService
from app.services.external_api import ExternalAPIService
from app.repositories import cryptocurrency_repository, price_data_repository  # Use global instances
from app.core.database import SessionLocal  # Use SessionLocal instead of get_db

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
        
        # Initialize services (DataSyncService has no parameters based on existing code)
        external_api_service = ExternalAPIService()
        data_sync_service = DataSyncService()  # Fixed: no parameters needed
        
        return data_sync_service, external_api_service, crypto_repo, price_repo, db_session
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_all_prices(self) -> Dict[str, Any]:
    """
    Sync current prices for all cryptocurrencies
    
    This task runs every 5 minutes to keep price data up-to-date
    
    Returns:
        dict: Synchronization results
    """
    task_id = self.request.id
    logger.info(f"Starting sync_all_prices task {task_id}")
    
    try:
        # Get services
        data_sync_service, _, _, _, db_session = get_services()
        
        # Run async sync operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(data_sync_service.sync_current_prices())
            
            # Close database session
            db_session.close()
            
            logger.info(f"sync_all_prices completed: {result}")
            return {
                "task_id": task_id,
                "status": "completed",
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"sync_all_prices failed: {e}")
        
        # Retry logic
        try:
            self.retry(countdown=60 * (self.request.retries + 1))
        except self.MaxRetriesExceededError:
            logger.error(f"sync_all_prices max retries exceeded: {e}")
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def sync_historical_data(self, days: int = 7) -> Dict[str, Any]:
    """
    Sync historical price data for all cryptocurrencies
    
    This task runs hourly to collect historical data
    
    Args:
        days: Number of days of historical data to sync
        
    Returns:
        dict: Synchronization results
    """
    task_id = self.request.id
    logger.info(f"Starting sync_historical_data task {task_id} for {days} days")
    
    try:
        # Get services
        data_sync_service, _, _, _, db_session = get_services()
        
        # Run async sync operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(data_sync_service.sync_historical_data(days=days))
            
            # Close database session
            db_session.close()
            
            logger.info(f"sync_historical_data completed: {result}")
            return {
                "task_id": task_id,
                "status": "completed", 
                "result": result,
                "days_synced": days,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"sync_historical_data failed: {e}")
        
        # Retry logic with exponential backoff
        try:
            countdown = 300 * (2 ** self.request.retries)  # 5, 10, 20 minutes
            self.retry(countdown=countdown)
        except self.MaxRetriesExceededError:
            logger.error(f"sync_historical_data max retries exceeded: {e}")
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


@shared_task(bind=True, max_retries=2, default_retry_delay=600)
def discover_new_cryptocurrencies(self, limit: int = 100) -> Dict[str, Any]:
    """
    Discover and add new cryptocurrencies to the database
    
    This task runs daily to discover new cryptocurrencies
    
    Args:
        limit: Maximum number of cryptocurrencies to discover
        
    Returns:
        dict: Discovery results
    """
    task_id = self.request.id
    logger.info(f"Starting discover_new_cryptocurrencies task {task_id}, limit: {limit}")
    
    try:
        # Get services
        data_sync_service, _, _, _, db_session = get_services()
        
        # Run async discovery operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(data_sync_service.discover_new_cryptocurrencies())
            
            # Close database session
            db_session.close()
            
            logger.info(f"discover_new_cryptocurrencies completed: {result}")
            return {
                "task_id": task_id,
                "status": "completed",
                "result": result,
                "limit": limit,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"discover_new_cryptocurrencies failed: {e}")
        
        # Retry logic
        try:
            countdown = 600 * (self.request.retries + 1)  # 10, 20 minutes
            self.retry(countdown=countdown)
        except self.MaxRetriesExceededError:
            logger.error(f"discover_new_cryptocurrencies max retries exceeded: {e}")
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


@shared_task(bind=True, max_retries=1, default_retry_delay=3600)
def cleanup_old_data(self, days_to_keep: int = 365) -> Dict[str, Any]:
    """
    Clean up old price data to manage database size
    
    This task runs weekly to clean up old data
    
    Args:
        days_to_keep: Number of days of data to keep
        
    Returns:
        dict: Cleanup results
    """
    task_id = self.request.id
    logger.info(f"Starting cleanup_old_data task {task_id}, keeping {days_to_keep} days")
    
    try:
        # Get services
        _, _, _, price_repo, db_session = get_services()
        
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Run cleanup operation (simple implementation)
        # Note: This assumes delete_old_records method exists, if not we'll implement basic cleanup
        try:
            deleted_count = price_repo.delete_old_records(db_session, cutoff_date)
        except AttributeError:
            # Fallback: basic cleanup implementation
            from app.models import PriceData
            deleted_count = db_session.query(PriceData).filter(
                PriceData.timestamp < cutoff_date
            ).count()
            db_session.query(PriceData).filter(
                PriceData.timestamp < cutoff_date
            ).delete()
        
        # Commit changes
        db_session.commit()
        db_session.close()
        
        result = {
            "deleted_records": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
            "days_kept": days_to_keep
        }
        
        logger.info(f"cleanup_old_data completed: {result}")
        return {
            "task_id": task_id,
            "status": "completed",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"cleanup_old_data failed: {e}")
        
        # Retry logic
        try:
            self.retry(countdown=3600)  # 1 hour
        except self.MaxRetriesExceededError:
            logger.error(f"cleanup_old_data max retries exceeded: {e}")
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


@shared_task
def sync_specific_cryptocurrency(crypto_symbol: str, days: int = 30) -> Dict[str, Any]:
    """
    Sync data for a specific cryptocurrency
    
    This is a manual task that can be triggered on-demand
    
    Args:
        crypto_symbol: Symbol of cryptocurrency to sync
        days: Number of days of historical data to sync
        
    Returns:
        dict: Sync results
    """
    logger.info(f"Starting sync_specific_cryptocurrency for {crypto_symbol}")
    
    try:
        # Get services
        data_sync_service, _, _, _, db_session = get_services()
        
        # Run async sync operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                data_sync_service.force_sync_cryptocurrency(crypto_symbol, days)
            )
            
            # Close database session
            db_session.close()
            
            logger.info(f"sync_specific_cryptocurrency completed for {crypto_symbol}: {result}")
            return {
                "status": "completed",
                "result": result,
                "crypto_symbol": crypto_symbol,
                "days": days,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"sync_specific_cryptocurrency failed for {crypto_symbol}: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "crypto_symbol": crypto_symbol,
            "timestamp": datetime.utcnow().isoformat()
        }


@shared_task
def get_task_status() -> Dict[str, Any]:
    """
    Get status of all background tasks
    
    Returns:
        dict: Task status information
    """
    try:
        # This would typically check Celery inspect for active tasks
        # For now, return basic status
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "available_tasks": [
                "sync_all_prices",
                "sync_historical_data", 
                "discover_new_cryptocurrencies",
                "cleanup_old_data",
                "sync_specific_cryptocurrency"
            ]
        }
        
    except Exception as e:
        logger.error(f"get_task_status failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }