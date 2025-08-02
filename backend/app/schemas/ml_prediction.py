# File: backend/app/schemas/prediction.py
# Enhanced Pydantic schemas for ML prediction API endpoints
# Comprehensive schemas for cryptocurrency price prediction system

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum

from app.schemas.common import BaseSchema


class PredictionStatus(str, Enum):
    """
    Prediction job status enumeration
    
    Defines the various states a prediction job can be in during processing.
    Used to track prediction lifecycle from request to completion.
    """
    PENDING = "pending"      # Prediction queued but not started
    RUNNING = "running"      # Prediction currently being processed
    COMPLETED = "completed"  # Prediction successfully completed
    FAILED = "failed"        # Prediction failed due to error
    CANCELLED = "cancelled"  # Prediction cancelled by user or system


class PredictionTimeframe(str, Enum):
    """
    Available prediction timeframes
    
    Defines supported time horizons for price predictions.
    Each timeframe uses different model configurations and features.
    """
    SHORT_TERM = "1h"      # 1 hour - high frequency trading
    MEDIUM_TERM = "24h"    # 24 hours - daily trading decisions  
    LONG_TERM = "7d"       # 7 days - weekly trend analysis
    EXTENDED = "30d"       # 30 days - long-term investment


class ModelType(str, Enum):
    """
    Available model types for predictions
    
    Defines the machine learning models available for generating
    cryptocurrency price predictions. Each has different strengths.
    """
    LSTM = "LSTM"                           # Long Short-Term Memory neural network
    LINEAR_REGRESSION = "LINEAR_REGRESSION" # Simple linear regression
    RANDOM_FOREST = "RANDOM_FOREST"         # Random forest ensemble
    ARIMA = "ARIMA"                         # AutoRegressive Integrated Moving Average
    ENSEMBLE = "ENSEMBLE"                   # Combination of multiple models


class PredictionBase(BaseSchema):
    """
    Base schema for predictions
    
    Contains core fields required for all prediction records.
    Inherits from BaseSchema for consistent validation and serialization.
    Used as foundation for create/update/response schemas.
    """
    
    model_config = ConfigDict(
        protected_namespaces=(),
        from_attributes=True,
        str_strip_whitespace=True
    )
    
    # Core prediction fields
    crypto_id: int = Field(gt=0, description="Cryptocurrency ID from database")
    model_name: str = Field(description="ML model identifier used for prediction")
    predicted_price: Decimal = Field(gt=0, description="Predicted price in USD")
    confidence_score: Decimal = Field(
        ge=0, le=1, 
        description="Model confidence score (0.0 to 1.0)"
    )
    target_datetime: datetime = Field(description="Target date/time for price prediction")
    features_used: Optional[str] = Field(
        default=None, 
        description="JSON string of features/indicators used in prediction"
    )


class PredictionCreate(PredictionBase):
    """
    Schema for creating new predictions
    
    Extends PredictionBase with user association for database creation.
    Used when storing prediction results to database with user tracking.
    """
    
    model_config = ConfigDict(
        protected_namespaces=(),
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    user_id: int = Field(gt=0, description="ID of user who requested the prediction")


class PredictionUpdate(BaseModel):
    """
    Schema for updating existing predictions
    
    Allows partial updates to prediction records.
    All fields are optional to support selective updates.
    """
    
    model_config = ConfigDict(
        protected_namespaces=(),
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    predicted_price: Optional[Decimal] = Field(
        default=None, 
        gt=0, 
        description="Updated predicted price value"
    )
    confidence_score: Optional[Decimal] = Field(
        default=None, 
        ge=0, 
        le=1, 
        description="Updated confidence score"
    )
    features_used: Optional[str] = Field(
        default=None, 
        description="Updated features JSON string"
    )


class PredictionResponse(PredictionBase):
    """
    Schema for prediction data in API responses
    
    Extends PredictionBase with database metadata for API responses.
    Includes creation timestamp and unique identifiers.
    """
    
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True
    )
    
    id: int = Field(description="Unique database identifier")
    user_id: int = Field(description="ID of user who created prediction")
    created_at: datetime = Field(description="Record creation timestamp")


# =====================================
# REQUEST/RESPONSE SCHEMAS (Following ml_training.py pattern)
# =====================================

class PredictionRequest(BaseModel):
    """
    Request to make a cryptocurrency price prediction
    
    Main entry point for prediction API. Allows users to request
    price predictions with specific parameters and configurations.
    Follows the same pattern as TrainingRequest in ml_training.py.
    """
    crypto_symbol: str = Field(..., description="Cryptocurrency symbol (e.g., BTC, ETH)")
    prediction_timeframe: PredictionTimeframe = Field(
        PredictionTimeframe.MEDIUM_TERM, 
        description="Time horizon for prediction"
    )
    model_version: Optional[str] = Field(
        None, 
        description="Specific model version to use (latest if not specified)"
    )
    include_historical_context: Optional[bool] = Field(
        True, 
        description="Include historical price context in prediction analysis"
    )
    custom_config: Optional[Dict[str, Any]] = Field(
        None, 
        description="Custom prediction parameters and model configuration"
    )
    
    @field_validator('crypto_symbol')
    @classmethod
    def validate_crypto_symbol(cls, v):
        """Validate and normalize cryptocurrency symbol"""
        return v.upper().strip()
    
    class Config:
        schema_extra = {
            "example": {
                "crypto_symbol": "BTC",
                "prediction_timeframe": "24h",
                "model_version": "v1.0",
                "include_historical_context": True,
                "custom_config": {
                    "risk_tolerance": "medium",
                    "include_sentiment": True
                }
            }
        }


class PredictionResponseEnhanced(BaseModel):
    """
    Enhanced response for prediction requests
    
    Comprehensive prediction response with detailed analysis.
    Includes price prediction, confidence metrics, and additional
    market context following ml_training.py response pattern.
    """
    # Core prediction results
    prediction_id: str = Field(..., description="Unique prediction identifier")
    crypto_symbol: str = Field(..., description="Cryptocurrency symbol")
    current_price: Decimal = Field(..., description="Current market price at prediction time")
    predicted_price: Decimal = Field(..., description="ML model predicted price")
    price_change_percentage: float = Field(..., description="Predicted price change percentage")
    confidence_score: float = Field(
        ..., 
        ge=0, le=1, 
        description="Model confidence in prediction (0.0 to 1.0)"
    )
    
    # Prediction metadata
    prediction_timeframe: str = Field(..., description="Prediction time horizon")
    valid_until: datetime = Field(..., description="Prediction validity expiration")
    model_used: str = Field(..., description="ML model name used for prediction")
    model_version: str = Field(..., description="Model version identifier")
    
    # Enhanced analysis (optional fields for detailed predictions)
    technical_indicators: Optional[Dict[str, float]] = Field(
        None, 
        description="Technical analysis indicators (RSI, MACD, etc.)"
    )
    market_sentiment: Optional[Dict[str, Any]] = Field(
        None, 
        description="Market sentiment analysis and social indicators"
    )
    historical_accuracy: Optional[float] = Field(
        None, 
        description="Historical accuracy of this model for this crypto"
    )
    risk_assessment: Optional[str] = Field(
        None, 
        description="Risk level assessment (low/medium/high)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "prediction_id": "pred_btc_24h_20240128_143022",
                "crypto_symbol": "BTC",
                "current_price": "42350.50",
                "predicted_price": "43200.75",
                "price_change_percentage": 2.1,
                "confidence_score": 0.78,
                "prediction_timeframe": "24h",
                "valid_until": "2024-01-29T14:30:22Z",
                "model_used": "lstm_ensemble",
                "model_version": "v1.0",
                "risk_assessment": "medium"
            }
        }

class BatchPredictionRequest(BaseModel):
    """
    Schema for batch prediction requests
    
    Allows users to request predictions for multiple cryptocurrencies
    simultaneously. Optimized for portfolio analysis and comparison.
    Includes validation for reasonable batch sizes to prevent abuse.
    """
    
    model_config = ConfigDict(
        protected_namespaces=(),
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    crypto_symbols: List[str] = Field(
        min_length=1, 
        max_length=10, 
        description="List of cryptocurrency symbols (max 10 to prevent overload)"
    )
    prediction_timeframe: PredictionTimeframe = Field(
        PredictionTimeframe.MEDIUM_TERM,
        description="Common prediction timeframe for all cryptocurrencies"
    )
    model_type: ModelType = Field(
        ModelType.LSTM,
        description="ML model type to use for all predictions"
    )
    include_confidence: bool = Field(
        default=True, 
        description="Include confidence scores in results"
    )
    
    @field_validator('crypto_symbols')
    @classmethod
    def validate_symbols(cls, v):
        """Validate and normalize cryptocurrency symbols"""
        return [symbol.upper().strip() for symbol in v]
    
    class Config:
        schema_extra = {
            "example": {
                "crypto_symbols": ["BTC", "ETH", "ADA"],
                "prediction_timeframe": "24h",
                "model_type": "LSTM",
                "include_confidence": True
            }
        }


class BatchPredictionResponse(BaseModel):
    """
    Schema for batch prediction responses
    
    Comprehensive response for batch prediction requests.
    Includes success/failure tracking, performance metrics,
    and detailed results for each requested cryptocurrency.
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True
    )
    
    # Batch metadata
    batch_id: str = Field(..., description="Unique batch prediction identifier")
    total_requested: int = Field(..., description="Total number of predictions requested")
    successful_predictions: int = Field(..., description="Number of successful predictions")
    failed_predictions: int = Field(..., description="Number of failed predictions")
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds")
    
    # Results and errors
    predictions: List[PredictionResponseEnhanced] = Field(
        ..., 
        description="List of successful prediction results"
    )
    errors: List[Dict[str, Any]] = Field(
        default=[], 
        description="List of errors for failed predictions"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "batch_id": "batch_20240128_143022_abc123",
                "total_requested": 3,
                "successful_predictions": 2,
                "failed_predictions": 1,
                "processing_time_ms": 1250.5,
                "predictions": [],
                "errors": [
                    {
                        "crypto_symbol": "INVALID", 
                        "error": "Cryptocurrency symbol not found",
                        "error_code": "SYMBOL_NOT_FOUND"
                    }
                ]
            }
        }


class PredictionHistoryRequest(BaseModel):
    """
    Request for prediction history analysis
    
    Allows users to retrieve and analyze historical predictions
    for specific cryptocurrencies. Supports filtering by time period,
    model type, and realization status for performance analysis.
    """
    crypto_symbol: str = Field(..., description="Cryptocurrency symbol to analyze")
    days_back: Optional[int] = Field(
        30, 
        ge=1, le=365, 
        description="Number of days of history to retrieve (max 1 year)"
    )
    include_realized: Optional[bool] = Field(
        True, 
        description="Include predictions with known outcomes for accuracy analysis"
    )
    model_filter: Optional[str] = Field(
        None, 
        description="Filter results by specific model name"
    )
    
    @field_validator('crypto_symbol')
    @classmethod
    def validate_crypto_symbol(cls, v):
        """Validate and normalize cryptocurrency symbol"""
        return v.upper().strip()
    
    class Config:
        schema_extra = {
            "example": {
                "crypto_symbol": "BTC",
                "days_back": 30,
                "include_realized": True,
                "model_filter": "lstm_ensemble"
            }
        }


class PredictionHistoryItem(BaseModel):
    """
    Individual prediction history record
    
    Represents a single historical prediction with its metadata,
    actual outcome (if available), and accuracy metrics.
    Used for building prediction history responses and analytics.
    """
    # Core prediction data
    prediction_id: str = Field(..., description="Unique prediction identifier")
    predicted_price: Decimal = Field(..., description="Price predicted by model")
    actual_price: Optional[Decimal] = Field(
        None, 
        description="Actual price if prediction period has passed"
    )
    confidence_score: float = Field(..., description="Model confidence at time of prediction")
    
    # Prediction metadata
    model_used: str = Field(..., description="Model identifier used")
    prediction_date: datetime = Field(..., description="When prediction was generated")
    target_date: datetime = Field(..., description="Target date for price prediction")
    
    # Outcome analysis
    accuracy_percentage: Optional[float] = Field(
        None, 
        description="Accuracy percentage if actual outcome is known"
    )
    is_realized: bool = Field(..., description="Whether prediction period has passed")
    
    class Config:
        schema_extra = {
            "example": {
                "prediction_id": "pred_btc_24h_20240127_143022",
                "predicted_price": "42000.00",
                "actual_price": "41850.25",
                "confidence_score": 0.82,
                "model_used": "lstm_ensemble",
                "prediction_date": "2024-01-27T14:30:22Z",
                "target_date": "2024-01-28T14:30:22Z",
                "accuracy_percentage": 99.6,
                "is_realized": True
            }
        }


class PredictionHistoryResponse(BaseModel):
    """
    Response for prediction history requests
    
    Comprehensive response containing historical predictions
    and aggregate statistics for performance analysis.
    Useful for model evaluation and user insights.
    """
    # Request context
    crypto_symbol: str = Field(..., description="Cryptocurrency symbol analyzed")
    
    # Aggregate statistics
    total_predictions: int = Field(..., description="Total predictions found in period")
    realized_predictions: int = Field(..., description="Predictions with known outcomes")
    average_accuracy: Optional[float] = Field(
        None, 
        description="Average accuracy of realized predictions"
    )
    
    # Historical data
    predictions: List[PredictionHistoryItem] = Field(
        ..., 
        description="List of historical predictions"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "crypto_symbol": "BTC",
                "total_predictions": 25,
                "realized_predictions": 20,
                "average_accuracy": 78.5,
                "predictions": []
            }
        }


class ModelPerformanceMetrics(BaseModel):
    """Enhanced model performance metrics"""
    model_name: str = Field(..., description="Model name")
    model_version: str = Field(..., description="Model version")
    crypto_symbol: str = Field(..., description="Cryptocurrency symbol")
    total_predictions: int = Field(..., description="Total predictions made")
    realized_predictions: int = Field(..., description="Predictions with outcomes")
    accuracy_percentage: Optional[float] = Field(None, description="Overall accuracy percentage")
    average_confidence: float = Field(..., description="Average confidence score")
    rmse: Optional[float] = Field(None, description="Root Mean Square Error")
    mae: Optional[float] = Field(None, description="Mean Absolute Error")
    last_updated: datetime = Field(..., description="Last metrics update")
    performance_trend: Optional[Dict[str, float]] = Field(None, description="Performance over time")
    
    class Config:
        schema_extra = {
            "example": {
                "model_name": "lstm_ensemble",
                "model_version": "v1.0",
                "crypto_symbol": "BTC",
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
    alternative_models: Optional[List[ModelPerformanceMetrics]] = Field(
        None, 
        description="Other available models"
    )
    performance_comparison: Optional[Dict[str, Any]] = Field(
        None, 
        description="Performance comparison data"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "crypto_symbol": "BTC",
                "active_model": {
                    "model_name": "lstm_ensemble",
                    "accuracy_percentage": 78.5
                },
                "alternative_models": [],
                "performance_comparison": {
                    "best_model": "lstm_ensemble",
                    "accuracy_range": {"min": 65.2, "max": 82.1}
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
    cache_hit_rate: Optional[float] = Field(None, description="Cache hit rate percentage")
    average_response_time_ms: Optional[float] = Field(None, description="Average response time")
    top_predicted_cryptos: List[Dict[str, Any]] = Field(
        default=[], 
        description="Most predicted cryptocurrencies"
    )
    
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
                "average_response_time_ms": 145.2,
                "top_predicted_cryptos": [
                    {"symbol": "BTC", "count": 850},
                    {"symbol": "ETH", "count": 420}
                ]
            }
        }


class ModelPerformance(BaseSchema):
    """Schema for ML model performance metrics (Legacy)"""
    
    model_config = ConfigDict(
        protected_namespaces=(),
        from_attributes=True,
        str_strip_whitespace=True
    )
    
    model_name: str = Field(description="Model name")
    crypto_id: int = Field(description="Cryptocurrency ID")
    total_predictions: int = Field(description="Total predictions made")
    accurate_predictions: int = Field(description="Number of accurate predictions")
    accuracy_percentage: float = Field(description="Overall accuracy percentage")
    average_error: float = Field(description="Average prediction error")
    rmse: float = Field(description="Root Mean Square Error")
    mae: float = Field(description="Mean Absolute Error")
    last_trained: datetime = Field(description="Last model training timestamp")
    training_data_points: int = Field(description="Number of training data points")


class PredictionResult(BaseModel):
    """Schema for prediction results (Legacy)"""
    
    model_config = ConfigDict(
        protected_namespaces=(),
        str_strip_whitespace=True
    )
    
    crypto_id: int = Field(description="Cryptocurrency ID")
    crypto_symbol: str = Field(description="Cryptocurrency symbol")
    model_name: str = Field(description="Model used for prediction")
    predicted_price: Decimal = Field(description="Predicted price")
    confidence_score: Decimal = Field(description="Confidence score")
    target_datetime: datetime = Field(description="Target prediction date")
    features_used: List[str] = Field(description="Features used in prediction")
    model_accuracy: Optional[float] = Field(
        default=None, 
        description="Historical accuracy of the model"
    )
    prediction_id: Optional[int] = Field(
        default=None, 
        description="Saved prediction ID"
    )


class PredictionAnalytics(BaseSchema):
    """Schema for prediction analytics (Legacy)"""
    
    model_config = ConfigDict(
        protected_namespaces=(),
        from_attributes=True,
        str_strip_whitespace=True
    )
    
    crypto_id: int = Field(description="Cryptocurrency ID")
    crypto_symbol: str = Field(description="Cryptocurrency symbol")
    total_predictions: int = Field(description="Total predictions for this crypto")
    average_confidence: float = Field(description="Average confidence score")
    accuracy_by_horizon: Dict[int, float] = Field(
        description="Accuracy by prediction horizon (days)"
    )
    best_performing_model: str = Field(description="Best performing model")
    worst_performing_model: str = Field(description="Worst performing model")
    prediction_trends: Dict[str, Any] = Field(description="Prediction trend analysis")


class PredictionComparison(BaseModel):
    """Schema for comparing predictions with actual prices (Legacy)"""
    
    model_config = ConfigDict(
        str_strip_whitespace=True
    )
    
    prediction_id: int = Field(description="Prediction ID")
    crypto_symbol: str = Field(description="Cryptocurrency symbol")
    predicted_price: Decimal = Field(description="Predicted price")
    actual_price: Optional[Decimal] = Field(
        default=None, 
        description="Actual price (if available)"
    )
    accuracy_percentage: Optional[float] = Field(
        default=None, 
        description="Accuracy percentage"
    )
    error_amount: Optional[Decimal] = Field(
        default=None, 
        description="Absolute error amount"
    )
    target_datetime: datetime = Field(description="Prediction target datetime")
    is_expired: bool = Field(description="Whether prediction period has passed")


class PredictionWithDetails(PredictionResponse):
    """Schema for prediction with additional details"""
    
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True
    )
    
    crypto_symbol: str = Field(description="Cryptocurrency symbol")
    crypto_name: str = Field(description="Cryptocurrency name")
    user_email: str = Field(description="User email")
    current_price: Optional[Decimal] = Field(
        default=None, 
        description="Current market price at time of viewing"
    )
    price_difference: Optional[Decimal] = Field(
        default=None, 
        description="Difference between predicted and current price"
    )
    accuracy_percentage: Optional[float] = Field(
        default=None, 
        description="Accuracy percentage if target date has passed"
    )


class UserPredictionStats(BaseSchema):
    """Schema for user prediction statistics"""
    
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True
    )
    
    user_id: int = Field(description="User ID")
    total_predictions: int = Field(description="Total predictions made")
    accurate_predictions: int = Field(description="Number of accurate predictions")
    accuracy_rate: float = Field(description="User's prediction accuracy rate")
    favorite_crypto: Optional[str] = Field(
        default=None, 
        description="Most predicted cryptocurrency"
    )
    average_confidence: float = Field(description="Average confidence score")
    prediction_frequency: float = Field(description="Predictions per day")
    best_prediction: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Best prediction details"
    )
    worst_prediction: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Worst prediction details"
    )


class PredictionAlert(BaseSchema):
    """Schema for prediction-based alerts"""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    user_id: int = Field(description="User ID")
    prediction_id: int = Field(description="Prediction ID")
    alert_type: str = Field(description="Alert type")
    threshold_percentage: float = Field(description="Alert threshold percentage")
    is_active: bool = Field(default=True, description="Whether alert is active")
    
    @field_validator('alert_type')
    @classmethod
    def validate_alert_type(cls, v):
        valid_types = ["price_target", "accuracy_threshold", "confidence_drop"]
        if v not in valid_types:
            raise ValueError(f'Alert type must be one of: {", ".join(valid_types)}')
        return v