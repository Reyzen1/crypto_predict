# File: backend/app/schemas/ml_prediction.py
# Pydantic schemas for ML prediction API endpoints - Based on ml_training.py pattern

from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum


class PredictionStatus(str, Enum):
    """Prediction job status enumeration"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CACHED = "cached"


class PredictionTimeframe(str, Enum):
    """Available prediction timeframes"""
    MINUTES_15 = "15m"
    MINUTES_30 = "30m"
    HOUR_1 = "1h"
    HOURS_4 = "4h"
    HOURS_24 = "24h"
    DAYS_7 = "7d"
    DAYS_30 = "30d"


class PredictionConfigRequest(BaseModel):
    """Configuration for prediction request"""
    timeframe: Optional[PredictionTimeframe] = Field(PredictionTimeframe.HOURS_24, description="Prediction timeframe")
    confidence_threshold: Optional[float] = Field(0.7, ge=0.5, le=0.99, description="Minimum confidence threshold")
    include_technical_indicators: Optional[bool] = Field(True, description="Include technical analysis indicators")
    include_market_sentiment: Optional[bool] = Field(False, description="Include market sentiment analysis")
    use_ensemble_models: Optional[bool] = Field(True, description="Use multiple models for ensemble prediction")
    
    class Config:
        schema_extra = {
            "example": {
                "timeframe": "24h",
                "confidence_threshold": 0.7,
                "include_technical_indicators": True,
                "include_market_sentiment": False,
                "use_ensemble_models": True
            }
        }


class PredictionRequest(BaseModel):
    """Request to make a prediction"""
    crypto_symbol: str = Field(..., description="Cryptocurrency symbol (e.g., BTC)")
    prediction_config: Optional[PredictionConfigRequest] = Field(None, description="Prediction configuration")
    model_version: Optional[str] = Field(None, description="Specific model version to use")
    force_refresh: Optional[bool] = Field(False, description="Force refresh prediction (ignore cache)")
    include_historical_context: Optional[bool] = Field(True, description="Include historical price context")
    
    @validator('crypto_symbol')
    def validate_crypto_symbol(cls, v):
        return v.upper().strip()
    
    class Config:
        schema_extra = {
            "example": {
                "crypto_symbol": "BTC",
                "prediction_config": {
                    "timeframe": "24h",
                    "confidence_threshold": 0.75
                },
                "force_refresh": False,
                "include_historical_context": True
            }
        }


class PredictionResponse(BaseModel):
    """Response from prediction request"""
    prediction_id: str = Field(..., description="Unique prediction identifier")
    crypto_symbol: str = Field(..., description="Cryptocurrency symbol")
    current_price: Decimal = Field(..., description="Current price at prediction time")
    predicted_price: Decimal = Field(..., description="Predicted price")
    price_change: Decimal = Field(..., description="Predicted price change")
    price_change_percentage: float = Field(..., description="Predicted price change percentage")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence (0-1)")
    timeframe: str = Field(..., description="Prediction timeframe")
    model_used: str = Field(..., description="Model used for prediction")
    model_version: str = Field(..., description="Model version used")
    prediction_timestamp: datetime = Field(..., description="When prediction was made")
    valid_until: datetime = Field(..., description="Prediction validity end time")
    
    # Additional context
    technical_indicators: Optional[Dict[str, float]] = Field(None, description="Technical analysis indicators")
    market_sentiment: Optional[Dict[str, Any]] = Field(None, description="Market sentiment data")
    historical_accuracy: Optional[float] = Field(None, description="Historical accuracy of this model")
    risk_assessment: Optional[str] = Field(None, description="Risk level assessment")
    
    class Config:
        schema_extra = {
            "example": {
                "prediction_id": "pred_btc_20240128_143022",
                "crypto_symbol": "BTC",
                "current_price": "42500.00",
                "predicted_price": "43200.00",
                "price_change": "700.00",
                "price_change_percentage": 1.65,
                "confidence_score": 0.82,
                "timeframe": "24h",
                "model_used": "lstm_ensemble",
                "model_version": "1.0",
                "prediction_timestamp": "2024-01-28T14:30:22Z",
                "valid_until": "2024-01-29T14:30:22Z",
                "historical_accuracy": 0.78,
                "risk_assessment": "moderate"
            }
        }


class BatchPredictionRequest(BaseModel):
    """Request for batch predictions"""
    crypto_symbols: List[str] = Field(..., min_items=1, max_items=10, description="List of cryptocurrency symbols")
    prediction_config: Optional[PredictionConfigRequest] = Field(None, description="Shared prediction configuration")
    model_version: Optional[str] = Field(None, description="Specific model version to use for all")
    
    @validator('crypto_symbols')
    def validate_crypto_symbols(cls, v):
        return [symbol.upper().strip() for symbol in v]
    
    class Config:
        schema_extra = {
            "example": {
                "crypto_symbols": ["BTC", "ETH", "ADA"],
                "prediction_config": {
                    "timeframe": "24h",
                    "confidence_threshold": 0.7
                }
            }
        }


class BatchPredictionResponse(BaseModel):
    """Response for batch predictions"""
    batch_id: str = Field(..., description="Batch prediction identifier")
    total_requested: int = Field(..., description="Total predictions requested")
    successful_predictions: int = Field(..., description="Successful predictions count")
    failed_predictions: int = Field(..., description="Failed predictions count")
    predictions: List[PredictionResponse] = Field(..., description="List of predictions")
    processing_time_seconds: float = Field(..., description="Total processing time")
    
    class Config:
        schema_extra = {
            "example": {
                "batch_id": "batch_20240128_143022",
                "total_requested": 3,
                "successful_predictions": 3,
                "failed_predictions": 0,
                "predictions": [],
                "processing_time_seconds": 2.45
            }
        }


class PredictionHistoryRequest(BaseModel):
    """Request for prediction history"""
    crypto_symbol: str = Field(..., description="Cryptocurrency symbol")
    days_back: Optional[int] = Field(7, ge=1, le=90, description="Days to look back")
    model_version: Optional[str] = Field(None, description="Filter by model version")
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum confidence filter")
    limit: Optional[int] = Field(50, ge=1, le=500, description="Maximum records to return")
    
    @validator('crypto_symbol')
    def validate_crypto_symbol(cls, v):
        return v.upper().strip()
    
    class Config:
        schema_extra = {
            "example": {
                "crypto_symbol": "BTC",
                "days_back": 7,
                "min_confidence": 0.7,
                "limit": 50
            }
        }


class PredictionHistoryItem(BaseModel):
    """Single prediction history item"""
    prediction_id: str = Field(..., description="Prediction identifier")
    predicted_price: Decimal = Field(..., description="Predicted price")
    actual_price: Optional[Decimal] = Field(None, description="Actual price (if available)")
    accuracy: Optional[float] = Field(None, description="Prediction accuracy")
    confidence_score: float = Field(..., description="Confidence score")
    model_used: str = Field(..., description="Model used")
    prediction_timestamp: datetime = Field(..., description="When prediction was made")
    is_realized: bool = Field(..., description="Whether prediction outcome is known")
    
    class Config:
        schema_extra = {
            "example": {
                "prediction_id": "pred_btc_20240127_143022",
                "predicted_price": "42800.00",
                "actual_price": "42650.00",
                "accuracy": 0.996,
                "confidence_score": 0.82,
                "model_used": "lstm_ensemble",
                "prediction_timestamp": "2024-01-27T14:30:22Z",
                "is_realized": True
            }
        }


class PredictionHistoryResponse(BaseModel):
    """Response for prediction history"""
    crypto_symbol: str = Field(..., description="Cryptocurrency symbol")
    total_predictions: int = Field(..., description="Total predictions found")
    realized_predictions: int = Field(..., description="Predictions with known outcomes")
    average_accuracy: Optional[float] = Field(None, description="Average accuracy of realized predictions")
    predictions: List[PredictionHistoryItem] = Field(..., description="List of predictions")
    
    class Config:
        schema_extra = {
            "example": {
                "crypto_symbol": "BTC",
                "total_predictions": 25,
                "realized_predictions": 20,
                "average_accuracy": 0.78,
                "predictions": []
            }
        }


class ModelPerformanceMetrics(BaseModel):
    """Model performance metrics"""
    model_name: str = Field(..., description="Model name")
    model_version: str = Field(..., description="Model version")
    total_predictions: int = Field(..., description="Total predictions made")
    realized_predictions: int = Field(..., description="Predictions with outcomes")
    accuracy_percentage: Optional[float] = Field(None, description="Overall accuracy percentage")
    average_confidence: float = Field(..., description="Average confidence score")
    rmse: Optional[float] = Field(None, description="Root Mean Square Error")
    mae: Optional[float] = Field(None, description="Mean Absolute Error")
    last_updated: datetime = Field(..., description="Last metrics update")
    
    class Config:
        schema_extra = {
            "example": {
                "model_name": "lstm_ensemble",
                "model_version": "1.0",
                "total_predictions": 150,
                "realized_predictions": 120,
                "accuracy_percentage": 78.5,
                "average_confidence": 0.76,
                "rmse": 1250.5,
                "mae": 980.2,
                "last_updated": "2024-01-28T14:30:22Z"
            }
        }


class ModelPerformanceResponse(BaseModel):
    """Response for model performance"""
    crypto_symbol: str = Field(..., description="Cryptocurrency symbol")
    active_model: ModelPerformanceMetrics = Field(..., description="Active model performance")
    alternative_models: Optional[List[ModelPerformanceMetrics]] = Field(None, description="Other available models")
    performance_trend: Optional[Dict[str, float]] = Field(None, description="Performance trend over time")
    
    class Config:
        schema_extra = {
            "example": {
                "crypto_symbol": "BTC",
                "active_model": {
                    "model_name": "lstm_ensemble",
                    "accuracy_percentage": 78.5
                },
                "alternative_models": [],
                "performance_trend": {
                    "7_days": 78.5,
                    "30_days": 76.2
                }
            }
        }


class PredictionStatsResponse(BaseModel):
    """Response for prediction statistics"""
    total_predictions_today: int = Field(..., description="Predictions made today")
    total_predictions_week: int = Field(..., description="Predictions made this week")
    total_predictions_all_time: int = Field(..., description="All time predictions")
    active_cryptocurrencies: int = Field(..., description="Cryptocurrencies being predicted")
    active_models: int = Field(..., description="Active models")
    average_confidence: float = Field(..., description="Average confidence across all predictions")
    cache_hit_rate: float = Field(..., description="Cache hit rate percentage")
    average_response_time_ms: float = Field(..., description="Average response time in milliseconds")
    
    class Config:
        schema_extra = {
            "example": {
                "total_predictions_today": 45,
                "total_predictions_week": 210,
                "total_predictions_all_time": 1520,
                "active_cryptocurrencies": 5,
                "active_models": 3,
                "average_confidence": 0.76,
                "cache_hit_rate": 82.5,
                "average_response_time_ms": 145.2
            }
        }