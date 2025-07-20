# File: backend/app/api/api_v1/endpoints/prices.py
# Price data management API endpoints with CRUD operations

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.database import get_db
from app.core.deps import get_current_active_user, get_optional_current_user
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


@router.get("/", response_model=PaginatedResponse[PriceDataWithCrypto])
def list_price_data(
    pagination: PaginationParams = Depends(),
    crypto_id: Optional[int] = Query(None, description="Filter by cryptocurrency ID"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Any:
    """
    List price data with pagination and filtering
    
    Public endpoint - no authentication required.
    Supports filtering by cryptocurrency and date range.
    """
    try:
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
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create new price data entry
    
    Requires user authentication.
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
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Bulk insert price data
    
    Requires user authentication.
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
    interval: str = Query("1d", description="Data interval (1h, 1d, 1w)"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Any:
    """
    Get price history for cryptocurrency
    
    Public endpoint - no authentication required.
    Returns OHLCV data for specified period.
    """
    try:
        # Verify cryptocurrency exists
        crypto = cryptocurrency_repository.get(db, crypto_id)
        if not crypto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cryptocurrency not found"
            )
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
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
            interval=interval,
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
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Any:
    """
    Get price statistics for cryptocurrency
    
    Public endpoint - no authentication required.
    Calculates various price metrics for specified period.
    """
    try:
        # Verify cryptocurrency exists
        crypto = cryptocurrency_repository.get(db, crypto_id)
        if not crypto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cryptocurrency not found"
            )
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
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
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get price data formatted for ML training
    
    Requires user authentication.
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
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Delete price data entry
    
    Requires user authentication.
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