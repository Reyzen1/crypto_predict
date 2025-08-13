# File: backend/app/api/api_v1/endpoints/crypto.py
# Cryptocurrency management API endpoints with CRUD operations

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user, get_optional_current_user
from app.schemas.cryptocurrency import (
    CryptocurrencyCreate, CryptocurrencyUpdate, CryptocurrencyResponse,
    CryptocurrencyWithPrice, CryptocurrencyStats
)
from app.schemas.common import (
    SuccessResponse, PaginationParams, PaginatedResponse
)
from app.repositories import cryptocurrency_repository, price_data_repository
from app.models import User


router = APIRouter()

@router.get("/", response_model=PaginatedResponse[CryptocurrencyResponse])
def list_cryptocurrencies_paginated(
    search: Optional[str] = Query(None, description="Search by symbol or name"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records"),
    order_by: str = Query("symbol", description="Field to order by"),
    order_desc: bool = Query(False, description="Descending order"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Any:
    """
    List cryptocurrencies with full pagination
    
    Returns paginated response with metadata.
    Public endpoint - no authentication required.
    """
    try:
        # Get cryptocurrencies with filtering
        if search:
            cryptos = cryptocurrency_repository.search_cryptos(
                db,
                search_term=search,
                skip=skip,
                limit=limit
            )
            total = len(cryptocurrency_repository.search_cryptos(db, search_term=search))
        else:
            if is_active:
                cryptos = cryptocurrency_repository.get_active_cryptos(
                    db,
                    skip=skip,
                    limit=limit
                )
                total = cryptocurrency_repository.count_active_cryptos(db)
            else:
                cryptos = cryptocurrency_repository.get_multi(
                    db,
                    skip=skip,
                    limit=limit
                )
                total = len(cryptocurrency_repository.get_all(db))
        
        # Convert to response format
        crypto_responses = []
        for crypto in cryptos:
            crypto_responses.append(CryptocurrencyResponse(
                id=crypto.id,
                symbol=crypto.symbol,
                name=crypto.name,
                coingecko_id=crypto.coingecko_id,
                binance_symbol=crypto.binance_symbol,
                is_active=crypto.is_active,
                created_at=crypto.created_at,
                updated_at=getattr(crypto, 'updated_at', None)
            ))
        
        return PaginatedResponse.create(
            items=crypto_responses,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cryptocurrencies: {str(e)}"
        )


@router.post("/", response_model=CryptocurrencyResponse, status_code=status.HTTP_201_CREATED)
def create_cryptocurrency(
    crypto_data: CryptocurrencyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create new cryptocurrency (Authenticated users only)
    
    Requires user authentication.
    Checks for duplicate symbols.
    """
    try:
        # Check if cryptocurrency already exists
        existing_crypto = cryptocurrency_repository.get_by_symbol(db, crypto_data.symbol)
        if existing_crypto:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cryptocurrency with symbol {crypto_data.symbol} already exists"
            )
        
        # Create cryptocurrency using your existing repository
        new_crypto = cryptocurrency_repository.create(db, obj_in=crypto_data)
        
        return CryptocurrencyResponse(
            id=new_crypto.id,
            symbol=new_crypto.symbol,
            name=new_crypto.name,
            coingecko_id=new_crypto.coingecko_id,
            binance_symbol=new_crypto.binance_symbol,
            is_active=new_crypto.is_active,
            created_at=new_crypto.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create cryptocurrency"
        )


# =====================================
# SIMPLE LIST ENDPOINT (Frontend Compatible)
# =====================================

@router.get("/list")
def list_cryptocurrencies_simple(
    search: Optional[str] = Query(None, description="Search by symbol or name"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    List cryptocurrencies
    
    Returns simple array format that matches frontend expectations.
    No authentication required.
    """
    try:
        # Get cryptocurrencies based on filters
        if search:
            cryptos = cryptocurrency_repository.search_cryptos(
                db,
                search_term=search,
                skip=skip,
                limit=limit
            )
        else:
            if is_active:
                cryptos = cryptocurrency_repository.get_active_cryptos(
                    db,
                    skip=skip,
                    limit=limit
                )
            else:
                cryptos = cryptocurrency_repository.get_multi(
                    db,
                    skip=skip,
                    limit=limit
                )
        
        # Convert to simple format that frontend expects
        result = []
        for crypto in cryptos:
            result.append({
                "symbol": crypto.symbol,
                "name": crypto.name,
                "status": "active" if crypto.is_active else "inactive"
            })
        
        return result
        
    except Exception as e:
        # Log error for debugging
        print(f"❌ Error in /crypto/list: {str(e)}")
        
        # Return empty list as fallback
        return []


@router.get("/symbol/{symbol}", response_model=CryptocurrencyWithPrice)
def get_cryptocurrency_by_symbol(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Any:
    """
    Get cryptocurrency by symbol with latest price
    
    Public endpoint - no authentication required.
    Returns crypto details with latest price data.
    """
    try:
        # Get cryptocurrency by symbol using your existing repository
        crypto = cryptocurrency_repository.get_by_symbol(db, symbol.upper())
        if not crypto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cryptocurrency with symbol {symbol} not found"
            )
        
        # Get latest price data using your existing repository
        latest_price = price_data_repository.get_latest_price(db, crypto.id)
        
        return CryptocurrencyWithPrice(
            id=crypto.id,
            symbol=crypto.symbol,
            name=crypto.name,
            coingecko_id=crypto.coingecko_id,
            binance_symbol=crypto.binance_symbol,
            is_active=crypto.is_active,
            created_at=crypto.created_at,
            latest_price=float(latest_price.close_price) if latest_price else None,
            latest_price_date=latest_price.timestamp if latest_price else None,
            price_change_24h=0.0,  # Calculate from price history if needed
            market_cap=float(latest_price.market_cap) if latest_price and latest_price.market_cap else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cryptocurrency"
        )


@router.get("/{crypto_id}", response_model=CryptocurrencyResponse)
def get_cryptocurrency_by_id(
    crypto_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Any:
    """
    Get cryptocurrency by ID
    
    Public endpoint - no authentication required.
    """
    try:
        crypto = cryptocurrency_repository.get(db, crypto_id)
        if not crypto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cryptocurrency not found"
            )
        
        return CryptocurrencyResponse(
            id=crypto.id,
            symbol=crypto.symbol,
            name=crypto.name,
            coingecko_id=crypto.coingecko_id,
            binance_symbol=crypto.binance_symbol,
            is_active=crypto.is_active,
            created_at=crypto.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cryptocurrency"
        )


@router.get("/{crypto_id}/latest-price", response_model=dict)
def get_latest_price(
    crypto_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Any:
    """
    Get latest price for cryptocurrency
    
    Public endpoint - no authentication required.
    Returns latest price data from your existing price data repository.
    """
    try:
        # Verify cryptocurrency exists
        crypto = cryptocurrency_repository.get(db, crypto_id)
        if not crypto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cryptocurrency not found"
            )
        
        # Get latest price using your existing repository
        latest_price = price_data_repository.get_latest_price(db, crypto_id)
        if not latest_price:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No price data found for this cryptocurrency"
            )
        
        return {
            "crypto_id": crypto.id,
            "symbol": crypto.symbol,
            "name": crypto.name,
            "latest_price": {
                "open_price": float(latest_price.open_price),
                "high_price": float(latest_price.high_price),
                "low_price": float(latest_price.low_price),
                "close_price": float(latest_price.close_price),
                "volume": float(latest_price.volume) if latest_price.volume else None,
                "market_cap": float(latest_price.market_cap) if latest_price.market_cap else None,
                "timestamp": latest_price.timestamp
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve latest price"
        )


@router.get("/{crypto_id}/stats", response_model=CryptocurrencyStats)
def get_cryptocurrency_stats(
    crypto_id: int,
    days: int = Query(30, description="Number of days for statistics"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Any:
    """
    Get cryptocurrency statistics
    
    Public endpoint - no authentication required.
    Returns price statistics for specified period.
    """
    try:
        # Verify cryptocurrency exists
        crypto = cryptocurrency_repository.get(db, crypto_id)
        if not crypto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cryptocurrency not found"
            )
        
        # Check data availability using your existing repository
        data_check = price_data_repository.check_data_availability(db, crypto_id)
        
        return CryptocurrencyStats(
            id=crypto.id,
            symbol=crypto.symbol,
            name=crypto.name,
            total_data_points=data_check["total_records"],
            data_start_date=data_check["date_range"]["start"] if data_check["date_range"] else None,
            data_end_date=data_check["date_range"]["end"] if data_check["date_range"] else None,
            data_quality=data_check["data_quality"],
            average_volume=0.0,  # Calculate from actual data if needed
            price_volatility=0.0,  # Calculate from actual data if needed
            market_cap_rank=None  # Can be filled from external API
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cryptocurrency statistics"
        )


@router.put("/{crypto_id}", response_model=CryptocurrencyResponse)
def update_cryptocurrency(
    crypto_id: int,
    crypto_update: CryptocurrencyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Update cryptocurrency information
    
    Requires user authentication.
    """
    try:
        # Get cryptocurrency to update
        crypto = cryptocurrency_repository.get(db, crypto_id)
        if not crypto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cryptocurrency not found"
            )
        
        # Update cryptocurrency using your existing repository
        updated_crypto = cryptocurrency_repository.update(
            db, 
            db_obj=crypto, 
            obj_in=crypto_update
        )
        
        return CryptocurrencyResponse(
            id=updated_crypto.id,
            symbol=updated_crypto.symbol,
            name=updated_crypto.name,
            coingecko_id=updated_crypto.coingecko_id,
            binance_symbol=updated_crypto.binance_symbol,
            is_active=updated_crypto.is_active,
            created_at=updated_crypto.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update cryptocurrency"
        )


@router.delete("/{crypto_id}", response_model=SuccessResponse)
def delete_cryptocurrency(
    crypto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Delete cryptocurrency
    
    Requires user authentication.
    Warning: This will also delete related price data and predictions.
    """
    try:
        # Get cryptocurrency to delete
        crypto = cryptocurrency_repository.get(db, crypto_id)
        if not crypto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cryptocurrency not found"
            )
        
        # Delete cryptocurrency using your existing repository
        deleted_crypto = cryptocurrency_repository.delete(db, id=crypto_id)
        
        if not deleted_crypto:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete cryptocurrency"
            )
        
        return SuccessResponse(
            message="Cryptocurrency deleted successfully",
            data={
                "deleted_crypto_id": crypto_id,
                "symbol": crypto.symbol,
                "name": crypto.name
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete cryptocurrency"
        )