# File: backend/app/schemas/prediction_api.py
# Prediction API schemas for real-time and batch predictions

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum

from .common import BaseSchema


class PredictionTimeframe(str, Enum):
    """Prediction timeframe options"""
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    HOUR_12 = "12h"
    DAY_1 = "24h"
    DAY_3 = "3d"
    WEEK_1 = "7d"


class PredictionRequest(BaseSchema):
    """Schema for single prediction request"""
    
    crypto_symbol: str = Field(..., description="Cryptocurrency symbol (BTC, ETH, etc.)")
    timeframe: PredictionTimeframe = Field(default=PredictionTimeframe.DAY_1, description="Prediction timeframe")
    include_confidence: bool = Field(default=True, description="Include confidence score")
    include_technical_analysis: bool = Field(default=False, description="Include technical indicators")
    
    @validator('crypto_symbol')
    @classmethod
    def validate_crypto_symbol(cls, v):
        return v.upper().strip()


class PredictionResponse(BaseSchema):
    """Schema for prediction response"""
    
    crypto_symbol: str = Field(..., description="Cryptocurrency symbol")
    current_price: Decimal = Field(..., description="Current price")
    predicted_price: Decimal = Field(..., description="Predicted price")
    price_change: Decimal = Field(..., description="Predicted price change")
    price_change_percent: float = Field(..., description="Predicted price change percentage")
    confidence_score: Optional[float] = Field(None, description="Prediction confidence (0-100)")
    timeframe: str = Field(..., description="Prediction timeframe")
    prediction_timestamp: datetime = Field(..., description="When prediction was made")
    valid_until: datetime = Field(..., description="Prediction validity period")
    model_id: str = Field(..., description="Model used for prediction")
    technical_indicators: Optional[Dict[str, Any]] = Field(None, description="Technical analysis data")


class BatchPredictionRequest(BaseSchema):
    """Schema for batch prediction request"""
    
    crypto_symbols: List[str] = Field(..., min_items=1, max_items=10, description="List of crypto symbols")
    timeframe: PredictionTimeframe = Field(default=PredictionTimeframe.DAY_1, description="Prediction timeframe")
    include_confidence: bool = Field(default=True, description="Include confidence scores")
    
    @validator('crypto_symbols')
    @classmethod
    def validate_symbols(cls, v):
        return [symbol.upper().strip() for symbol in v]


class BatchPredictionResponse(BaseSchema):
    """Schema for batch prediction response"""
    
    predictions: List[PredictionResponse] = Field(..., description="List of predictions")
    total_requested: int = Field(..., description="Total symbols requested")
    successful_predictions: int = Field(..., description="Number of successful predictions")
    failed_symbols: List[str] = Field(default=[], description="Symbols that failed to predict")
    batch_timestamp: datetime = Field(..., description="Batch processing timestamp")


class PredictionHistoryRequest(BaseSchema):
    """Schema for prediction history request"""
    
    crypto_symbol: Optional[str] = Field(None, description="Filter by crypto symbol")
    start_date: Optional[datetime] = Field(None, description="Start date filter")
    end_date: Optional[datetime] = Field(None, description="End date filter")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum number of results")
    include_accuracy: bool = Field(default=True, description="Include accuracy metrics")


class PredictionHistoryItem(BaseSchema):
    """Schema for single prediction history item"""
    
    prediction_id: str = Field(..., description="Prediction identifier")
    crypto_symbol: str = Field(..., description="Cryptocurrency symbol")
    predicted_price: Decimal = Field(..., description="Predicted price")
    actual_price: Optional[Decimal] = Field(None, description="Actual price (if available)")
    prediction_accuracy: Optional[float] = Field(None, description="Prediction accuracy percentage")
    confidence_score: Optional[float] = Field(None, description="Original confidence score")
    timeframe: str = Field(..., description="Prediction timeframe")
    created_at: datetime = Field(..., description="Prediction creation time")
    model_id: str = Field(..., description="Model used")


class PredictionHistoryResponse(BaseSchema):
    """Schema for prediction history response"""
    
    predictions: List[PredictionHistoryItem] = Field(..., description="List of historical predictions")
    total_count: int = Field(..., description="Total predictions matching criteria")
    accuracy_stats: Optional[Dict[str, float]] = Field(None, description="Overall accuracy statistics")
    crypto_symbol: Optional[str] = Field(None, description="Filtered crypto symbol")


class ModelPerformanceRequest(BaseSchema):
    """Schema for model performance request"""
    
    crypto_symbol: Optional[str] = Field(None, description="Filter by crypto symbol")
    model_id: Optional[str] = Field(None, description="Filter by specific model")
    days_back: int = Field(default=30, ge=1, le=365, description="Performance period in days")


class ModelPerformanceResponse(BaseSchema):
    """Schema for model performance response"""
    
    model_id: str = Field(..., description="Model identifier")
    crypto_symbol: str = Field(..., description="Cryptocurrency symbol")
    total_predictions: int = Field(..., description="Total predictions made")
    accurate_predictions: int = Field(..., description="Number of accurate predictions")
    accuracy_percentage: float = Field(..., description="Overall accuracy percentage")
    average_confidence: float = Field(..., description="Average confidence score")
    performance_period_days: int = Field(..., description="Performance measurement period")
    performance_metrics: Dict[str, float] = Field(..., description="Detailed performance metrics")
    last_updated: datetime = Field(..., description="Last performance calculation")


class PredictionErrorResponse(BaseSchema):
    """Schema for prediction error response"""
    
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Human readable error message")
    crypto_symbol: Optional[str] = Field(None, description="Symbol that caused error")
    timestamp: datetime = Field(..., description="Error timestamp")
    retry_after: Optional[int] = Field(None, description="Retry after seconds")