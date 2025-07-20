# File: ./backend/app/services/data_sync.py
# Background data synchronization service

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.external_api import external_api_service
from app.repositories import cryptocurrency_repository, price_data_repository
from app.core.config import settings

logger = logging.getLogger(__name__)


class DataSyncService:
    """
    Background data synchronization service
    
    Handles automated data collection and synchronization from external APIs.
    Provides scheduling, error handling, and monitoring for data sync operations.
    """
    
    def __init__(self):
        self.is_running = False
        self.sync_tasks: Dict[str, asyncio.Task] = {}
        self.last_sync_times: Dict[str, datetime] = {}
        self.sync_intervals = {
            "price_sync": 300,      # 5 minutes for price updates
            "historical_sync": 3600, # 1 hour for historical data
            "discovery_sync": 86400  # 24 hours for new crypto discovery
        }
    
    async def start_background_sync(self) -> None:
        """
        Start background data synchronization tasks
        """
        if self.is_running:
            logger.warning("Background sync is already running")
            return
        
        self.is_running = True
        logger.info("Starting background data synchronization")
        
        # Start different sync tasks
        self.sync_tasks["price_sync"] = asyncio.create_task(
            self._price_sync_loop()
        )
        self.sync_tasks["historical_sync"] = asyncio.create_task(
            self._historical_sync_loop()
        )
        self.sync_tasks["discovery_sync"] = asyncio.create_task(
            self._discovery_sync_loop()
        )
        
        logger.info("Background sync tasks started")
    
    async def stop_background_sync(self) -> None:
        """
        Stop background data synchronization tasks
        """
        if not self.is_running:
            logger.warning("Background sync is not running")
            return
        
        self.is_running = False
        logger.info("Stopping background data synchronization")
        
        # Cancel all running tasks
        for task_name, task in self.sync_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Cancelled sync task: {task_name}")
        
        self.sync_tasks.clear()
        logger.info("Background sync tasks stopped")
    
    async def _price_sync_loop(self) -> None:
        """
        Background loop for price synchronization
        """
        logger.info("Starting price sync loop")
        
        while self.is_running:
            try:
                await self.sync_current_prices()
                await asyncio.sleep(self.sync_intervals["price_sync"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in price sync loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def _historical_sync_loop(self) -> None:
        """
        Background loop for historical data synchronization
        """
        logger.info("Starting historical sync loop")
        
        while self.is_running:
            try:
                await self.sync_historical_data()
                await asyncio.sleep(self.sync_intervals["historical_sync"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in historical sync loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    async def _discovery_sync_loop(self) -> None:
        """
        Background loop for new cryptocurrency discovery
        """
        logger.info("Starting discovery sync loop")
        
        while self.is_running:
            try:
                await self.discover_new_cryptocurrencies()
                await asyncio.sleep(self.sync_intervals["discovery_sync"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in discovery sync loop: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retry
    
    async def sync_current_prices(self, crypto_symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Synchronize current cryptocurrency prices
        
        Args:
            crypto_symbols: List of symbols to sync (default: all active)
            
        Returns:
            dict: Sync results
        """
        logger.info("Starting current price synchronization")
        
        try:
            # Create database session
            db = SessionLocal()
            
            try:
                # Perform price sync
                result = await external_api_service.sync_cryptocurrency_prices(
                    db=db,
                    crypto_symbols=crypto_symbols,
                    save_to_db=True
                )
                
                # Update last sync time
                self.last_sync_times["price_sync"] = datetime.utcnow()
                
                logger.info(f"Price sync completed: {result}")
                return result
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Current price sync failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Current price sync failed"
            }
    
    async def sync_historical_data(self, days: int = 7) -> Dict[str, Any]:
        """
        Synchronize historical data for all active cryptocurrencies
        
        Args:
            days: Number of days of historical data to sync
            
        Returns:
            dict: Sync results
        """
        logger.info(f"Starting historical data synchronization ({days} days)")
        
        try:
            # Create database session
            db = SessionLocal()
            
            try:
                # Get active cryptocurrencies
                active_cryptos = cryptocurrency_repository.get_active(db)
                
                results = {
                    "success": 0,
                    "failed": 0,
                    "cryptos": []
                }
                
                for crypto in active_cryptos:
                    try:
                        # Check if we need to sync historical data
                        latest_data = price_data_repository.get_latest_price(db, crypto.id)
                        
                        # Skip if we have recent data (within last hour)
                        if latest_data and latest_data.created_at > datetime.utcnow() - timedelta(hours=1):
                            continue
                        
                        # Sync historical data
                        result = await external_api_service.sync_historical_data(
                            db=db,
                            crypto_symbol=crypto.symbol,
                            days=days,
                            save_to_db=True
                        )
                        
                        if result.get("success"):
                            results["success"] += 1
                        else:
                            results["failed"] += 1
                        
                        results["cryptos"].append({
                            "symbol": crypto.symbol,
                            "success": result.get("success", False),
                            "saved_records": result.get("saved_records", 0)
                        })
                        
                        # Small delay to avoid overwhelming the API
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"Failed to sync historical data for {crypto.symbol}: {e}")
                        results["failed"] += 1
                
                # Update last sync time
                self.last_sync_times["historical_sync"] = datetime.utcnow()
                
                logger.info(f"Historical sync completed: {results}")
                return results
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Historical data sync failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Historical data sync failed"
            }
    
    async def discover_new_cryptocurrencies(self) -> Dict[str, Any]:
        """
        Discover and add new cryptocurrencies
        
        Returns:
            dict: Discovery results
        """
        logger.info("Starting new cryptocurrency discovery")
        
        try:
            # Create database session
            db = SessionLocal()
            
            try:
                # Perform cryptocurrency discovery
                result = await external_api_service.discover_new_cryptocurrencies(
                    db=db,
                    save_to_db=True
                )
                
                # Update last sync time
                self.last_sync_times["discovery_sync"] = datetime.utcnow()
                
                logger.info(f"Cryptocurrency discovery completed: {result}")
                return result
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Cryptocurrency discovery failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Cryptocurrency discovery failed"
            }
    
    async def manual_sync_all(self) -> Dict[str, Any]:
        """
        Manually trigger all sync operations
        
        Returns:
            dict: Combined sync results
        """
        logger.info("Starting manual sync of all data")
        
        results = {
            "price_sync": None,
            "historical_sync": None,
            "discovery_sync": None,
            "overall_success": False
        }
        
        try:
            # Run all sync operations
            results["price_sync"] = await self.sync_current_prices()
            await asyncio.sleep(5)  # Brief delay between operations
            
            results["historical_sync"] = await self.sync_historical_data()
            await asyncio.sleep(5)
            
            results["discovery_sync"] = await self.discover_new_cryptocurrencies()
            
            # Check overall success
            success_count = sum(1 for result in results.values() 
                              if isinstance(result, dict) and result.get("success"))
            results["overall_success"] = success_count >= 2  # At least 2 operations successful
            
            logger.info(f"Manual sync completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Manual sync failed: {e}")
            results["error"] = str(e)
            return results
    
    async def get_sync_status(self) -> Dict[str, Any]:
        """
        Get status of background sync operations
        
        Returns:
            dict: Sync status information
        """
        status = {
            "is_running": self.is_running,
            "active_tasks": len([task for task in self.sync_tasks.values() if not task.done()]),
            "last_sync_times": {
                key: value.isoformat() if value else None 
                for key, value in self.last_sync_times.items()
            },
            "sync_intervals": self.sync_intervals,
            "tasks": {}
        }
        
        # Check individual task status
        for task_name, task in self.sync_tasks.items():
            status["tasks"][task_name] = {
                "running": not task.done(),
                "cancelled": task.cancelled() if task.done() else False,
                "exception": str(task.exception()) if task.done() and task.exception() else None
            }
        
        return status
    
    async def force_sync_cryptocurrency(self, crypto_symbol: str, days: int = 30) -> Dict[str, Any]:
        """
        Force synchronization of a specific cryptocurrency
        
        Args:
            crypto_symbol: Cryptocurrency symbol to sync
            days: Days of historical data to sync
            
        Returns:
            dict: Sync results
        """
        logger.info(f"Force syncing cryptocurrency: {crypto_symbol}")
        
        try:
            # Create database session
            db = SessionLocal()
            
            try:
                results = {
                    "symbol": crypto_symbol,
                    "price_sync": None,
                    "historical_sync": None,
                    "success": False
                }
                
                # Sync current prices
                price_result = await external_api_service.sync_cryptocurrency_prices(
                    db=db,
                    crypto_symbols=[crypto_symbol],
                    save_to_db=True
                )
                results["price_sync"] = price_result
                
                # Small delay
                await asyncio.sleep(2)
                
                # Sync historical data
                historical_result = await external_api_service.sync_historical_data(
                    db=db,
                    crypto_symbol=crypto_symbol,
                    days=days,
                    save_to_db=True
                )
                results["historical_sync"] = historical_result
                
                # Check success
                results["success"] = (
                    price_result.get("success", 0) > 0 and 
                    historical_result.get("success", False)
                )
                
                logger.info(f"Force sync completed for {crypto_symbol}: {results}")
                return results
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Force sync failed for {crypto_symbol}: {e}")
            return {
                "symbol": crypto_symbol,
                "success": False,
                "error": str(e),
                "message": f"Force sync failed for {crypto_symbol}"
            }
    
    async def cleanup_old_data(self, days_to_keep: int = 365) -> Dict[str, Any]:
        """
        Clean up old price data to manage database size
        
        Args:
            days_to_keep: Number of days of data to keep
            
        Returns:
            dict: Cleanup results
        """
        logger.info(f"Starting data cleanup (keeping {days_to_keep} days)")
        
        try:
            # Create database session
            db = SessionLocal()
            
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
                
                # Delete old price data
                deleted_count = price_data_repository.delete_before_date(db, cutoff_date)
                
                logger.info(f"Data cleanup completed: deleted {deleted_count} old records")
                
                return {
                    "success": True,
                    "deleted_records": deleted_count,
                    "cutoff_date": cutoff_date.isoformat(),
                    "days_kept": days_to_keep,
                    "message": f"Cleaned up {deleted_count} old price records"
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Data cleanup failed"
            }
    
    async def validate_data_integrity(self) -> Dict[str, Any]:
        """
        Validate data integrity and consistency
        
        Returns:
            dict: Validation results
        """
        logger.info("Starting data integrity validation")
        
        try:
            # Create database session
            db = SessionLocal()
            
            try:
                results = {
                    "overall_health": "good",
                    "issues": [],
                    "statistics": {},
                    "recommendations": []
                }
                
                # Get database statistics
                total_cryptos = cryptocurrency_repository.count_total(db)
                active_cryptos = len(cryptocurrency_repository.get_active(db))
                total_price_records = price_data_repository.count_total(db)
                
                results["statistics"] = {
                    "total_cryptocurrencies": total_cryptos,
                    "active_cryptocurrencies": active_cryptos,
                    "total_price_records": total_price_records,
                    "price_records_per_crypto": total_price_records / max(active_cryptos, 1)
                }
                
                # Check for issues
                
                # 1. Check for cryptocurrencies without recent price data
                cryptos_without_recent_data = []
                active_cryptos_list = cryptocurrency_repository.get_active(db)
                
                for crypto in active_cryptos_list:
                    latest_price = price_data_repository.get_latest_price(db, crypto.id)
                    if not latest_price or latest_price.created_at < datetime.utcnow() - timedelta(hours=6):
                        cryptos_without_recent_data.append(crypto.symbol)
                
                if cryptos_without_recent_data:
                    results["issues"].append({
                        "type": "stale_data",
                        "description": "Cryptocurrencies without recent price data",
                        "affected": cryptos_without_recent_data,
                        "count": len(cryptos_without_recent_data)
                    })
                
                # 2. Check for cryptocurrencies with insufficient historical data
                cryptos_with_little_data = []
                
                for crypto in active_cryptos_list:
                    data_count = price_data_repository.count_by_crypto(db, crypto.id)
                    if data_count < 100:  # Less than 100 price records
                        cryptos_with_little_data.append({
                            "symbol": crypto.symbol,
                            "record_count": data_count
                        })
                
                if cryptos_with_little_data:
                    results["issues"].append({
                        "type": "insufficient_data",
                        "description": "Cryptocurrencies with insufficient historical data",
                        "affected": cryptos_with_little_data,
                        "count": len(cryptos_with_little_data)
                    })
                
                # 3. Check for data gaps
                data_gaps = []
                for crypto in active_cryptos_list[:5]:  # Check top 5 cryptos
                    gap_analysis = price_data_repository.check_data_availability(db, crypto.id)
                    if gap_analysis.get("data_quality") != "Good":
                        data_gaps.append({
                            "symbol": crypto.symbol,
                            "quality": gap_analysis.get("data_quality"),
                            "total_records": gap_analysis.get("total_records")
                        })
                
                if data_gaps:
                    results["issues"].append({
                        "type": "data_gaps",
                        "description": "Cryptocurrencies with data quality issues",
                        "affected": data_gaps,
                        "count": len(data_gaps)
                    })
                
                # Generate recommendations
                if cryptos_without_recent_data:
                    results["recommendations"].append(
                        f"Run price sync for: {', '.join(cryptos_without_recent_data[:5])}"
                    )
                
                if cryptos_with_little_data:
                    results["recommendations"].append(
                        "Run historical data sync for cryptocurrencies with insufficient data"
                    )
                
                if len(results["issues"]) == 0:
                    results["overall_health"] = "excellent"
                elif len(results["issues"]) <= 2:
                    results["overall_health"] = "good"
                else:
                    results["overall_health"] = "needs_attention"
                
                logger.info(f"Data integrity validation completed: {results['overall_health']}")
                return results
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Data integrity validation failed: {e}")
            return {
                "overall_health": "error",
                "error": str(e),
                "message": "Data integrity validation failed"
            }


# Global service instance
data_sync_service = DataSyncService()