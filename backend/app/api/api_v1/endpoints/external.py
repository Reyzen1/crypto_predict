# File: ./backend/app/api/api_v1/endpoints/external.py
# Manual sync endpoints for external API operations

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.schemas.common import SuccessResponse
from app.services.external_api import external_api_service
from app.services.data_sync import data_sync_service
from app.models import User

router = APIRouter()


@router.post("/sync/prices", response_model=dict)
async def sync_current_prices(
    crypto_symbols: Optional[List[str]] = Body(None, description="List of crypto symbols to sync (optional)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Manually sync current cryptocurrency prices
    
    Fetches current prices from CoinGecko API and saves to database.
    If no symbols provided, syncs all active cryptocurrencies.
    
    **Required**: Authentication
    """
    try:
        result = await external_api_service.sync_cryptocurrency_prices(
            db=db,
            crypto_symbols=crypto_symbols,
            save_to_db=True
        )
        
        return {
            "status": "success",
            "data": result,
            "message": f"Price sync completed: {result.get('success', 0)} successful"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Price sync failed: {str(e)}"
        )


@router.post("/sync/historical/{crypto_symbol}", response_model=dict)
async def sync_historical_data(
    crypto_symbol: str,
    days: int = Query(30, ge=1, le=365, description="Number of days of historical data"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Manually sync historical data for a specific cryptocurrency
    
    Fetches historical price data from CoinGecko API and saves to database.
    
    **Required**: Authentication
    **Parameters**:
    - crypto_symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
    - days: Number of days of historical data (1-365)
    """
    try:
        result = await external_api_service.sync_historical_data(
            db=db,
            crypto_symbol=crypto_symbol.upper(),
            days=days,
            save_to_db=True
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Historical data sync failed")
            )
        
        return {
            "status": "success", 
            "data": result,
            "message": f"Historical data synced for {crypto_symbol}: {result.get('saved_records', 0)} records"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Historical data sync failed: {str(e)}"
        )


@router.post("/discover/new", response_model=dict)
async def discover_new_cryptocurrencies(
    search_queries: Optional[List[str]] = Body(None, description="Custom search queries (optional)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Discover and add new cryptocurrencies from CoinGecko
    
    Searches for cryptocurrencies and adds new ones to the database.
    If no search queries provided, uses default popular cryptocurrencies.
    
    **Required**: Authentication
    """
    try:
        result = await external_api_service.discover_new_cryptocurrencies(
            db=db,
            search_queries=search_queries,
            save_to_db=True
        )
        
        return {
            "status": "success",
            "data": result,
            "message": f"Discovery completed: {result.get('added', 0)} new cryptocurrencies added"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cryptocurrency discovery failed: {str(e)}"
        )


@router.get("/status", response_model=dict)
async def get_external_api_status(
    current_user: Optional[User] = Depends(get_current_active_user)
) -> Any:
    """
    Get status of external APIs
    
    Returns connectivity and health information for external APIs.
    
    **Required**: Authentication (optional for basic status)
    """
    try:
        # Get API status
        api_status = await external_api_service.get_api_status()
        
        # Get sync status if user is authenticated
        sync_status = None
        if current_user:
            sync_status = await data_sync_service.get_sync_status()
        
        return {
            "status": "success",
            "data": {
                "external_apis": api_status,
                "sync_service": sync_status
            },
            "message": "External API status retrieved successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get API status: {str(e)}"
        )


@router.post("/sync/force/{crypto_symbol}", response_model=dict)
async def force_sync_cryptocurrency(
    crypto_symbol: str,
    days: int = Query(30, ge=1, le=365, description="Days of historical data to sync"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Force complete synchronization of a specific cryptocurrency
    
    Performs both current price sync and historical data sync for the specified cryptocurrency.
    Use this when you need to ensure a cryptocurrency has complete and up-to-date data.
    
    **Required**: Authentication
    **Parameters**:
    - crypto_symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
    - days: Number of days of historical data to sync (1-365)
    """
    try:
        result = await data_sync_service.force_sync_cryptocurrency(
            crypto_symbol=crypto_symbol.upper(),
            days=days
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Force sync failed")
            )
        
        return {
            "status": "success",
            "data": result,
            "message": f"Force sync completed for {crypto_symbol}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Force sync failed: {str(e)}"
        )


@router.post("/sync/all", response_model=dict)
async def manual_sync_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Manually trigger all sync operations
    
    Performs complete data synchronization:
    1. Current price sync for all active cryptocurrencies
    2. Historical data sync for cryptocurrencies with missing data
    3. Discovery of new cryptocurrencies
    
    **Required**: Authentication
    **Warning**: This operation may take several minutes to complete
    """
    try:
        result = await data_sync_service.manual_sync_all()
        
        # Check if any operations failed
        failed_operations = []
        for operation, operation_result in result.items():
            if operation != "overall_success" and isinstance(operation_result, dict):
                if not operation_result.get("success"):
                    failed_operations.append(operation)
        
        if failed_operations:
            return {
                "status": "partial_success",
                "data": result,
                "message": f"Sync completed with some failures: {', '.join(failed_operations)}"
            }
        
        return {
            "status": "success",
            "data": result,
            "message": "All sync operations completed successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Manual sync failed: {str(e)}"
        )


@router.post("/validate/{crypto_symbol}", response_model=dict)
async def validate_external_data(
    crypto_symbol: str,
    price_threshold: float = Query(0.05, ge=0.01, le=0.2, description="Price difference threshold (0.01-0.2)"),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Validate external data quality and consistency
    
    Checks data quality by comparing different data sources and looking for inconsistencies.
    
    **Required**: Authentication
    **Parameters**:
    - crypto_symbol: Cryptocurrency symbol to validate
    - price_threshold: Maximum allowed price difference percentage (default: 5%)
    """
    try:
        result = await external_api_service.validate_external_data(
            crypto_symbol=crypto_symbol.upper(),
            price_threshold=price_threshold
        )
        
        validation_status = "success" if result.get("valid") else "warning"
        
        return {
            "status": validation_status,
            "data": result,
            "message": result.get("message", "Data validation completed")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data validation failed: {str(e)}"
        )


@router.get("/sync/status", response_model=dict)
async def get_sync_status(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get background sync service status
    
    Returns detailed information about background sync operations,
    including last sync times, active tasks, and sync intervals.
    
    **Required**: Authentication
    """
    try:
        status = await data_sync_service.get_sync_status()
        
        return {
            "status": "success",
            "data": status,
            "message": "Sync status retrieved successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync status: {str(e)}"
        )


@router.post("/data/cleanup", response_model=dict)
async def cleanup_old_data(
    days_to_keep: int = Query(365, ge=30, le=1095, description="Days of data to keep (30-1095)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Clean up old price data to manage database size
    
    Removes price data older than the specified number of days.
    Use this to manage database size and improve performance.
    
    **Required**: Authentication
    **Parameters**:
    - days_to_keep: Number of days of data to keep (30-1095 days)
    
    **Warning**: This operation permanently deletes old data
    """
    try:
        result = await data_sync_service.cleanup_old_data(days_to_keep=days_to_keep)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Data cleanup failed")
            )
        
        return {
            "status": "success",
            "data": result,
            "message": f"Data cleanup completed: {result.get('deleted_records', 0)} old records removed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data cleanup failed: {str(e)}"
        )


@router.get("/data/integrity", response_model=dict)
async def validate_data_integrity(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Validate data integrity and consistency
    
    Performs comprehensive analysis of data quality, identifies issues,
    and provides recommendations for improvement.
    
    **Required**: Authentication
    """
    try:
        result = await data_sync_service.validate_data_integrity()
        
        status_code = "success"
        if result.get("overall_health") == "needs_attention":
            status_code = "warning"
        elif result.get("overall_health") == "error":
            status_code = "error"
        
        return {
            "status": status_code,
            "data": result,
            "message": f"Data integrity check completed - Overall health: {result.get('overall_health')}"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data integrity validation failed: {str(e)}"
        )