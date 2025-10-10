# File: backend/app/api/api_v1/endpoints/prices.py
# Price data management API endpoints with CRUD operations

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.database import get_db
from app.core.deps import get_current_active_user, get_optional_current_user, get_current_admin_user
from app.schemas.price_data import (
    PriceDataCreate, PriceDataResponse, PriceDataWithCrypto, OHLCV,
    PriceHistoryRequest, PriceHistoryResponse, PriceStatistics,
    MLDataRequest, MLDataResponse, PriceDataBulkInsert
)
from app.schemas.common import (
    SuccessResponse, PaginationParams, PaginatedResponse
)
from app.repositories import price_data_repository, cryptocurrency_repository
from app.models import User


router = APIRouter()


# Helper functions
def validate_timeframe(timeframe: str) -> str:
    """
    Validate timeframe parameter
    
    Args:
        timeframe: Timeframe string to validate
        
    Returns:
        Validated timeframe string
        
    Raises:
        HTTPException: If timeframe is invalid
    """
    valid_timeframes = ['1h', '4h', '1d']
    if timeframe not in valid_timeframes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid timeframe '{timeframe}'. Must be one of: {valid_timeframes}"
        )
    return timeframe


def get_timeframe_limit(timeframe: str, days: int) -> int:
    """
    Calculate data point limit based on timeframe and days
    
    Args:
        timeframe: Data timeframe (1h, 4h, 1d)
        days: Number of days
        
    Returns:
        Number of expected data points
    """
    timeframe_multipliers = {
        '1h': 24,    # 24 hours per day
        '4h': 6,     # 6 four-hour periods per day  
        '1d': 1      # 1 day per day
    }
    
    return days * timeframe_multipliers.get(timeframe, 1)


@router.get("/", response_model=PaginatedResponse[PriceDataWithCrypto])
def list_price_data(
    pagination: PaginationParams = Depends(),
    crypto_id: Optional[int] = Query(None, description="Filter by cryptocurrency ID"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    timeframe: Optional[str] = Query(None, description="Data timeframe filter (1h, 4h, 1d)"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Any:
    """
    List price data with pagination and filtering including timeframe support
    
    Public endpoint - no authentication required.
    Supports filtering by cryptocurrency, date range, and timeframe.
    """
    try:
        # Validate timeframe if provided
        if timeframe:
            timeframe = validate_timeframe(timeframe)
        
        if crypto_id:
            # Get price history for specific cryptocurrency
            price_data = price_data_repository.get_price_history(
                db,
                crypto_id=crypto_id,
                start_date=start_date,
                end_date=end_date,
                limit=pagination.limit
            )
            total = price_data_repository.count_by_crypto(db, crypto_id)
        else:
            # Get all price data with pagination
            price_data = price_data_repository.get_multi(
                db,
                skip=pagination.skip,
                limit=pagination.limit
            )
            total = len(price_data_repository.get_all(db))
        
        # Convert to response format with crypto info
        price_responses = []
        for price in price_data:
            crypto = cryptocurrency_repository.get(db, price.crypto_id)
            price_responses.append(
                PriceDataWithCrypto(
                    id=price.id,
                    crypto_id=price.crypto_id,
                    crypto_symbol=crypto.symbol if crypto else "UNKNOWN",
                    crypto_name=crypto.name if crypto else "Unknown",
                    timestamp=price.timestamp,
                    open_price=price.open_price,
                    high_price=price.high_price,
                    low_price=price.low_price,
                    close_price=price.close_price,
                    volume=price.volume,
                    market_cap=price.market_cap,
                    created_at=price.created_at
                )
            )
        
        return PaginatedResponse.create(
            items=price_responses,
            total=total,
            skip=pagination.skip,
            limit=pagination.limit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve price data"
        )


@router.post("/", response_model=PriceDataResponse, status_code=status.HTTP_201_CREATED)
def create_price_data(
    price_data: PriceDataCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """
    Create new price data entry
    
    Requires admin authentication.
    Validates cryptocurrency existence.
    """
    try:
        # Verify cryptocurrency exists
        crypto = cryptocurrency_repository.get(db, price_data.crypto_id)
        if not crypto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cryptocurrency not found"
            )
        
        # Create price data using your existing repository
        new_price = price_data_repository.add_price_data(
            db,
            crypto_id=price_data.crypto_id,
            timestamp=price_data.timestamp,
            open_price=price_data.open_price,
            high_price=price_data.high_price,
            low_price=price_data.low_price,
            close_price=price_data.close_price,
            volume=price_data.volume,
            market_cap=price_data.market_cap
        )
        
        return PriceDataResponse(
            id=new_price.id,
            crypto_id=new_price.crypto_id,
            timestamp=new_price.timestamp,
            open_price=new_price.open_price,
            high_price=new_price.high_price,
            low_price=new_price.low_price,
            close_price=new_price.close_price,
            volume=new_price.volume,
            market_cap=new_price.market_cap,
            created_at=new_price.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create price data"
        )


@router.post("/bulk", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
def bulk_create_price_data(
    bulk_data: PriceDataBulkInsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """
    Bulk insert price data
    
    Requires admin authentication.
    Efficient for importing large datasets.
    """
    try:
        # Verify cryptocurrency exists
        crypto = cryptocurrency_repository.get(db, bulk_data.crypto_id)
        if not crypto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cryptocurrency not found"
            )
        
        created_count = 0
        failed_count = 0
        
        # Process each price data entry
        for price_entry in bulk_data.price_data:
            try:
                price_data_repository.add_price_data(
                    db,
                    crypto_id=bulk_data.crypto_id,
                    timestamp=price_entry.timestamp,
                    open_price=price_entry.open_price,
                    high_price=price_entry.high_price,
                    low_price=price_entry.low_price,
                    close_price=price_entry.close_price,
                    volume=price_entry.volume,
                    market_cap=price_entry.market_cap
                )
                created_count += 1
            except Exception:
                failed_count += 1
                continue
        
        return SuccessResponse(
            message=f"Bulk price data insert completed",
            data={
                "crypto_id": bulk_data.crypto_id,
                "total_entries": len(bulk_data.price_data),
                "created_count": created_count,
                "failed_count": failed_count
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk insert price data"
        )


@router.get("/{crypto_id}/history", response_model=PriceHistoryResponse)
def get_price_history(
    crypto_id: int,
    days: int = Query(30, description="Number of days of history"),
    timeframe: str = Query("1d", description="Data timeframe (1h, 4h, 1d)"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Any:
    """
    Get price history for cryptocurrency with timeframe support
    
    Public endpoint - no authentication required.
    Returns OHLCV data for specified period and timeframe.
    Supports 1h (hourly), 4h (4-hourly), 1d (daily) timeframes.
    """
    try:
        # Validate timeframe
        timeframe = validate_timeframe(timeframe)
        
        # Verify cryptocurrency exists
        crypto = cryptocurrency_repository.get(db, crypto_id)
        if not crypto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cryptocurrency not found"
            )
        
        # Calculate date range and expected data points
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        expected_points = get_timeframe_limit(timeframe, days)
        
        # Get price history using your existing repository
        price_history = price_data_repository.get_price_history(
            db,
            crypto_id=crypto_id,
            start_date=start_date,
            end_date=end_date,
            limit=1000  # Limit for performance
        )
        
        if not price_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No price history found for this cryptocurrency"
            )
        
        # Convert to OHLCV format
        ohlcv_data = [
            OHLCV(
                timestamp=price.timestamp,
                open=float(price.open_price),
                high=float(price.high_price),
                low=float(price.low_price),
                close=float(price.close_price),
                volume=float(price.volume) if price.volume else 0.0
            ) for price in price_history
        ]
        
        return PriceHistoryResponse(
            crypto_id=crypto_id,
            symbol=crypto.symbol,
            name=crypto.name,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe,
            data_points=len(ohlcv_data),
            ohlcv_data=ohlcv_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve price history"
        )


@router.get("/{crypto_id}/statistics", response_model=PriceStatistics)
def get_price_statistics(
    crypto_id: int,
    days: int = Query(30, description="Number of days for statistics"),
    timeframe: str = Query("1d", description="Data timeframe (1h, 4h, 1d)"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Any:
    """
    Get price statistics for cryptocurrency with timeframe support
    
    Public endpoint - no authentication required.
    Calculates various price metrics for specified period and timeframe.
    Supports 1h (hourly), 4h (4-hourly), 1d (daily) timeframes.
    """
    try:
        # Validate timeframe
        timeframe = validate_timeframe(timeframe)
        
        # Verify cryptocurrency exists
        crypto = cryptocurrency_repository.get(db, crypto_id)
        if not crypto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cryptocurrency not found"
            )
        
        # Calculate date range and expected data points
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        expected_points = get_timeframe_limit(timeframe, days)
        
        # Get price history for calculations
        price_history = price_data_repository.get_price_history(
            db,
            crypto_id=crypto_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if not price_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No price data found for statistics calculation"
            )
        
        # Calculate statistics
        prices = [float(price.close_price) for price in price_history]
        volumes = [float(price.volume) if price.volume else 0.0 for price in price_history]
        
        current_price = prices[-1] if prices else 0.0
        min_price = min(prices) if prices else 0.0
        max_price = max(prices) if prices else 0.0
        avg_price = sum(prices) / len(prices) if prices else 0.0
        avg_volume = sum(volumes) / len(volumes) if volumes else 0.0
        
        # Calculate price change
        price_change = 0.0
        price_change_percentage = 0.0
        if len(prices) > 1:
            price_change = prices[-1] - prices[0]
            price_change_percentage = (price_change / prices[0]) * 100 if prices[0] > 0 else 0.0
        
        # Calculate volatility (simple standard deviation)
        volatility = 0.0
        if len(prices) > 1:
            variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
            volatility = variance ** 0.5
        
        return PriceStatistics(
            crypto_id=crypto_id,
            symbol=crypto.symbol,
            name=crypto.name,
            period_days=days,
            data_points=len(price_history),
            current_price=current_price,
            min_price=min_price,
            max_price=max_price,
            avg_price=avg_price,
            price_change=price_change,
            price_change_percentage=price_change_percentage,
            volatility=volatility,
            avg_volume=avg_volume,
            start_date=start_date,
            end_date=end_date
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate price statistics"
        )


@router.post("/{crypto_id}/ml-data", response_model=MLDataResponse)
def get_ml_data(
    crypto_id: int,
    ml_request: MLDataRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """
    Get price data formatted for ML training
    
    Requires admin authentication.
    Returns data in format suitable for machine learning models.
    """
    try:
        # Verify cryptocurrency exists
        crypto = cryptocurrency_repository.get(db, crypto_id)
        if not crypto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cryptocurrency not found"
            )
        
        # Get ML-formatted data using your existing repository
        ml_data = price_data_repository.get_ml_data(
            db,
            crypto_id=crypto_id,
            start_date=ml_request.start_date,
            end_date=ml_request.end_date,
            features=ml_request.features
        )
        
        if not ml_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No data found for ML training"
            )
        
        return MLDataResponse(
            crypto_id=crypto_id,
            symbol=crypto.symbol,
            name=crypto.name,
            start_date=ml_request.start_date,
            end_date=ml_request.end_date,
            features=ml_request.features,
            data_points=len(ml_data),
            ml_data=ml_data,
            preprocessing_notes=[
                "Data is in chronological order",
                "Missing values handled by forward fill",
                "Volume data may be null for some entries"
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve ML data"
        )


@router.delete("/{price_id}", response_model=SuccessResponse)
def delete_price_data(
    price_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """
    Delete price data entry
    
    Requires admin authentication.
    Use with caution as this affects historical data.
    """
    try:
        # Get price data to delete
        price_data = price_data_repository.get(db, price_id)
        if not price_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Price data not found"
            )
        
        # Delete price data using your existing repository
        deleted_price = price_data_repository.delete(db, id=price_id)
        
        if not deleted_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete price data"
            )
        
        return SuccessResponse(
            message="Price data deleted successfully",
            data={
                "deleted_price_id": price_id,
                "crypto_id": price_data.crypto_id,
                "timestamp": price_data.timestamp.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete price data"
        )


@router.post("/admin/fetch-asset-data", response_model=SuccessResponse)
async def fetch_asset_price_data(
    asset_id: int = Query(..., description="Asset ID to fetch data for"),
    days: int = Query(30, description="Number of days of historical data", ge=1, le=365),
    timeframe: str = Query("1d", description="Data timeframe (1d, 1h, 4h)"),
    vs_currency: str = Query("usd", description="Base currency"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Fetch and populate price data for a specific asset from CoinGecko
    
    Admin endpoint for populating historical price data.
    Supports multiple timeframes: 1d (daily), 1h (hourly), 4h (4-hourly).
    
    Args:
        asset_id: ID of the asset to fetch data for
        days: Number of days of historical data (1-365)
        timeframe: Data resolution (1d, 1h, 4h)
        vs_currency: Base currency (default: usd)
    
    Returns:
        Operation results with success status and record count
    """
    
    # Validate timeframe
    timeframe = validate_timeframe(timeframe)
    
    try:
        # Import service
        from app.services.price_data_service import get_price_data_service
        
        # Get service instance
        price_service = get_price_data_service(db)
        
        # Populate asset price data
        result = await price_service.populate_asset_price_data(
            asset_id=asset_id,
            days=days,
            timeframe=timeframe,
            vs_currency=vs_currency
        )
        
        if result['success']:
            return SuccessResponse(
                message=result['message'],
                data={
                    "asset_id": result['asset_id'],
                    "records_inserted": result['records_inserted'],
                    "timeframe": result['timeframe'],
                    "period_days": result['period_days']
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('message', 'Failed to fetch price data')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/admin/batch-fetch", response_model=SuccessResponse)
async def batch_fetch_price_data(
    asset_ids: List[int] = Query(..., description="List of asset IDs"),
    timeframe: str = Query("1d", description="Data timeframe"),
    days: int = Query(1, description="Number of days to fetch", ge=1, le=30),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Batch fetch latest price data for multiple assets
    
    Admin endpoint for updating latest prices across multiple assets.
    Useful for daily/hourly data refresh operations.
    """
    
    try:
        # Import service
        from app.services.price_data_service import get_price_data_service
        
        # Get service instance
        price_service = get_price_data_service(db)
        
        # Batch update prices
        result = await price_service.fetch_and_update_latest_prices(
            asset_ids=asset_ids,
            timeframe=timeframe,
            days=days
        )
        
        return SuccessResponse(
            message=f"Batch operation completed: {result['success_count']} successful, {result['failed_count']} failed",
            data={
                "success_count": result['success_count'],
                "failed_count": result['failed_count'],
                "total_assets": result['total_assets'],
                "timeframe": result['timeframe'],
                "errors": result['errors'][:10]  # Limit errors in response
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch operation failed: {str(e)}"
        )


@router.get("/{asset_id}/data-quality", response_model=dict)
def get_asset_data_quality(
    asset_id: int,
    timeframe: str = Query("1d", description="Data timeframe"),
    days: int = Query(7, description="Days to analyze"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get data quality report for an asset
    
    Returns comprehensive data quality metrics including:
    - Completeness score
    - Missing data gaps
    - Data validation results
    """
    try:
        # Import service
        from app.services.price_data_service import get_price_data_service
        
        # Get service instance
        price_service = get_price_data_service(db)
        
        # Get quality report
        quality_report = price_service.get_data_quality_report(
            asset_id=asset_id,
            timeframe=timeframe,
            days=days
        )
        
        # Get data gaps
        data_gaps = price_service.get_price_data_gaps(
            asset_id=asset_id,
            timeframe=timeframe,
            days_back=days
        )
        
        return {
            "asset_id": asset_id,
            "timeframe": timeframe,
            "analysis_period_days": days,
            "quality_report": quality_report,
            "data_gaps": data_gaps,
            "recommendations": _generate_quality_recommendations(quality_report, data_gaps)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quality report: {str(e)}"
        )


def _generate_quality_recommendations(
    quality_report: dict,
    data_gaps: List[dict]
) -> List[str]:
    """Generate recommendations based on data quality analysis"""
    recommendations = []
    
    quality_score = quality_report.get('quality_score', 0)
    
    if quality_score < 70:
        recommendations.append("Data quality is poor. Consider refreshing historical data.")
    
    if quality_report.get('missing_price', 0) > 0:
        recommendations.append("Missing price data detected. Fetch missing records.")
    
    if len(data_gaps) > 5:
        recommendations.append("Multiple data gaps found. Run gap-filling process.")
    
    if quality_report.get('zero_prices', 0) > 0:
        recommendations.append("Zero price values detected. Review data validation rules.")
    
    if not recommendations:
        recommendations.append("Data quality is good. No immediate action required.")
    
    return recommendations


# ============= TASK EXECUTION ENDPOINTS =============

@router.post("/admin/tasks/fetch-daily", status_code=status.HTTP_202_ACCEPTED)
def trigger_daily_price_fetch(
    asset_id: Optional[int] = Body(None, description="Specific asset ID (optional)"),
    timeframe: str = Body("1d", description="Timeframe (1d, 1h, 4h)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """
    Trigger daily price data fetch task manually
    
    Admin only endpoint for manual task execution.
    """
    try:
        from app.tasks.price_collector import fetch_daily_price_data
        
        # Execute task asynchronously
        task = fetch_daily_price_data.delay(
            asset_id=asset_id,
            timeframe=timeframe
        )
        
        return {
            "message": "Daily price fetch task started",
            "task_id": task.id,
            "asset_id": asset_id,
            "timeframe": timeframe,
            "status": "started"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start daily price fetch task: {str(e)}"
        )


@router.post("/admin/tasks/fetch-historical", status_code=status.HTTP_202_ACCEPTED)
def trigger_historical_price_fetch(
    asset_id: int = Body(..., description="Asset ID"),
    timeframe: str = Body("1d", description="Timeframe (1d, 1h, 4h)"),
    days: int = Body(30, description="Number of days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """
    Trigger historical price data fetch task manually
    
    Admin only endpoint for manual historical data collection.
    """
    try:
        from app.tasks.price_collector import fetch_historical_price_data
        
        # Execute task asynchronously
        task = fetch_historical_price_data.delay(
            asset_id=asset_id,
            timeframe=timeframe,
            days=days
        )
        
        return {
            "message": "Historical price fetch task started",
            "task_id": task.id,
            "asset_id": asset_id,
            "timeframe": timeframe,
            "days": days,
            "status": "started"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start historical price fetch task: {str(e)}"
        )


@router.get("/admin/tasks/{task_id}/status")
def get_task_status(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """
    Get status of a price data task
    
    Admin only endpoint for task monitoring.
    """
    try:
        from app.tasks.price_collector import get_task_status as get_status
        
        status_info = get_status(task_id)
        
        return status_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )