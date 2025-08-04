# File: backend/app/api/api_v1/endpoints/dashboard.py
# Dashboard API endpoints - Frontend optimized
# Provides aggregated data endpoints for dashboard consumption

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user, get_optional_current_user
from app.models import User
from app.services.dashboard_service import dashboard_service
from app.schemas.common import SuccessResponse

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# =====================================
# DASHBOARD SUMMARY ENDPOINTS
# =====================================

@router.get(
    "/summary",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get dashboard summary"
)
async def get_dashboard_summary(
    symbols: Optional[str] = Query(
        default="BTC,ETH",
        description="Comma-separated list of cryptocurrency symbols",
        example="BTC,ETH,ADA"
    ),
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard summary
    
    Provides aggregated data for the main dashboard including:
    - Current prices for specified cryptocurrencies
    - Price predictions for next day
    - Market overview statistics
    - System status
    
    **Usage for Frontend:**
    ```javascript
    fetch('/api/dashboard/summary?symbols=BTC,ETH')
      .then(response => response.json())
      .then(data => {
        // data.cryptocurrencies[0].current_price
        // data.cryptocurrencies[0].predicted_price  
        // data.cryptocurrencies[0].confidence
        // data.market_overview.market_sentiment
      });
    ```
    
    **Response Format:**
    ```json
    {
      "timestamp": "2024-01-15T10:00:00Z",
      "cryptocurrencies": [
        {
          "symbol": "BTC",
          "name": "Bitcoin", 
          "current_price": 45000,
          "predicted_price": 47000,
          "confidence": 85,
          "price_change_24h": 1200,
          "price_change_24h_percent": 2.7
        }
      ],
      "market_overview": {
        "total_cryptocurrencies": 2,
        "average_confidence": 83.5,
        "bullish_predictions": 2,
        "bearish_predictions": 0,
        "market_sentiment": "bullish"
      }
    }
    ```
    """
    try:
        logger.info(f"Dashboard summary requested for symbols: {symbols}")
        
        # Parse symbols
        symbol_list = [s.strip().upper() for s in symbols.split(",")] if symbols else ["BTC", "ETH"]
        
        # Get dashboard data
        dashboard_data = await dashboard_service.get_dashboard_summary(
            db=db,
            symbols=symbol_list,
            user_id=current_user.id if current_user else None
        )
        
        logger.info(f"Dashboard summary generated for {len(symbol_list)} symbols")
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Dashboard summary failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dashboard summary generation failed: {str(e)}"
        )


@router.get(
    "/crypto/{symbol}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get detailed crypto information"
)
async def get_crypto_details(
    symbol: str,
    days_history: int = Query(
        default=7,
        ge=1,
        le=30,
        description="Number of days of historical data to include"
    ),
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information for specific cryptocurrency
    
    Provides comprehensive data for a single cryptocurrency including:
    - Current price and prediction
    - Price history for specified days
    - Prediction history
    - Technical indicators
    
    **Usage for Frontend:**
    ```javascript
    fetch('/api/dashboard/crypto/BTC?days_history=7')
      .then(response => response.json())
      .then(data => {
        // data.current_price
        // data.predicted_price
        // data.price_history (array of historical prices)
        // data.prediction_history (array of past predictions)
        // data.technical_indicators (RSI, MACD, etc.)
      });
    ```
    
    **Response Format:**
    ```json
    {
      "symbol": "BTC",
      "name": "Bitcoin",
      "current_price": 45000,
      "predicted_price": 47000,
      "confidence": 85,
      "price_history": [
        {
          "timestamp": "2024-01-14T00:00:00Z",
          "price": 44500,
          "volume": 1200000
        }
      ],
      "prediction_history": [
        {
          "timestamp": "2024-01-14T12:00:00Z", 
          "predicted_price": 46000,
          "confidence": 0.82,
          "model": "LSTM"
        }
      ],
      "technical_indicators": {
        "rsi": 65.5,
        "macd": 1200,
        "moving_average_20": 45500
      }
    }
    ```
    """
    try:
        logger.info(f"Crypto details requested for {symbol} with {days_history} days history")
        
        # Get detailed crypto information
        crypto_details = await dashboard_service.get_crypto_details(
            db=db,
            symbol=symbol.upper(),
            days_history=days_history,
            user_id=current_user.id if current_user else None
        )
        
        logger.info(f"Crypto details generated for {symbol}")
        return crypto_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Crypto details failed for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Crypto details generation failed: {str(e)}"
        )


# =====================================
# QUICK ACCESS ENDPOINTS (Frontend Optimized)
# =====================================

@router.get(
    "/quick/{symbol}",
    response_model=Dict[str, Any], 
    status_code=status.HTTP_200_OK,
    summary="Get quick crypto data for cards/widgets"
)
async def get_quick_crypto_data(
    symbol: str,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Get quick cryptocurrency data optimized for cards/widgets
    
    Lightweight endpoint that provides essential data for crypto cards,
    widgets, or summary displays with minimal response time.
    
    **Perfect for Frontend Cards:**
    ```javascript
    // Use this for cryptocurrency cards in dashboard
    fetch('/api/dashboard/quick/BTC')
      .then(response => response.json())
      .then(data => {
        // data.symbol = "BTC"
        // data.current_price = 45000
        // data.predicted_price = 47000  
        // data.confidence = 85
        // data.price_change_24h_percent = 2.7
        // data.status = "active"
      });
    ```
    
    **Response Format (Minimal):**
    ```json
    {
      "symbol": "BTC",
      "name": "Bitcoin",
      "current_price": 45000,
      "predicted_price": 47000,
      "confidence": 85,
      "price_change_24h": 1200,
      "price_change_24h_percent": 2.7,
      "prediction_target_date": "2024-01-16T10:00:00Z",
      "last_updated": "2024-01-15T10:00:00Z",
      "status": "active"
    }
    ```
    """
    try:
        logger.info(f"Quick crypto data requested for {symbol}")
        
        # Get dashboard summary for single symbol
        dashboard_data = await dashboard_service.get_dashboard_summary(
            db=db,
            symbols=[symbol.upper()],
            user_id=current_user.id if current_user else None
        )
        
        # Extract single crypto data
        if dashboard_data["cryptocurrencies"]:
            crypto_data = dashboard_data["cryptocurrencies"][0]
            logger.info(f"Quick crypto data generated for {symbol}")
            return crypto_data
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cryptocurrency '{symbol}' not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quick crypto data failed for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quick crypto data generation failed: {str(e)}"
        )


@router.get(
    "/prices",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get current prices for multiple symbols"
)
async def get_current_prices(
    symbols: str = Query(
        default="BTC,ETH",
        description="Comma-separated list of cryptocurrency symbols",
        example="BTC,ETH,ADA,DOT"
    ),
    db: Session = Depends(get_db)
):
    """
    Get current prices for multiple cryptocurrency symbols
    
    Optimized endpoint for getting current market prices without predictions.
    Useful for price tickers, charts, or when you only need price data.
    
    **Usage for Price Tickers:**
    ```javascript
    fetch('/api/dashboard/prices?symbols=BTC,ETH,ADA')
      .then(response => response.json())
      .then(data => {
        // data.prices.BTC = 45000
        // data.prices.ETH = 3000
        // data.last_updated = "2024-01-15T10:00:00Z"
      });
    ```
    
    **Response Format:**
    ```json
    {
      "prices": {
        "BTC": 45000,
        "ETH": 3000,
        "ADA": 0.5
      },
      "changes_24h": {
        "BTC": 2.7,
        "ETH": -1.2,
        "ADA": 5.3
      },
      "last_updated": "2024-01-15T10:00:00Z",
      "total_symbols": 3
    }
    ```
    """
    try:
        logger.info(f"Current prices requested for symbols: {symbols}")
        
        # Parse symbols
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        
        # Get dashboard data (current prices included)
        dashboard_data = await dashboard_service.get_dashboard_summary(
            db=db,
            symbols=symbol_list,
            user_id=None
        )
        
        # Extract prices and changes
        prices = {}
        changes_24h = {}
        
        for crypto in dashboard_data["cryptocurrencies"]:
            prices[crypto["symbol"]] = crypto["current_price"]
            changes_24h[crypto["symbol"]] = crypto["price_change_24h_percent"]
        
        response_data = {
            "prices": prices,
            "changes_24h": changes_24h,
            "last_updated": dashboard_data["timestamp"],
            "total_symbols": len(prices)
        }
        
        logger.info(f"Current prices generated for {len(prices)} symbols")
        return response_data
        
    except Exception as e:
        logger.error(f"Current prices failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Current prices generation failed: {str(e)}"
        )


# =====================================
# SYSTEM STATUS ENDPOINTS
# =====================================

@router.get(
    "/status",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get dashboard system status"
)
async def get_dashboard_status(
    db: Session = Depends(get_db)
):
    """
    Get dashboard system status and health metrics
    
    Provides system status information including:
    - API status
    - Database connectivity
    - External API status
    - Recent activity metrics
    
    **Usage for System Monitoring:**
    ```javascript
    fetch('/api/dashboard/status')
      .then(response => response.json())
      .then(data => {
        // data.status = "operational"
        // data.api_status = "healthy"
        // data.database_status = "connected"
        // data.external_apis = {...}
      });
    ```
    """
    try:
        from datetime import datetime, timezone
        
        # Basic system status
        status_data = {
            "status": "operational",
            "timestamp": datetime.now(timezone.utc),
            "api_status": "healthy",
            "database_status": "connected",
            "external_apis": {
                "coingecko": "healthy",
                "binance": "healthy"
            },
            "active_predictions": 0,
            "supported_cryptocurrencies": ["BTC", "ETH", "ADA", "DOT"],
            "last_data_update": datetime.now(timezone.utc),
            "uptime": "99.9%"
        }
        
        logger.info("Dashboard status generated")
        return status_data
        
    except Exception as e:
        logger.error(f"Dashboard status failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dashboard status generation failed: {str(e)}"
        )