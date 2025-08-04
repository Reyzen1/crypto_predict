# File: ./backend/app/schemas/prediction.py
# ML prediction related Pydantic schemas - FIXED for Pydantic V2

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json

from app.schemas.common import BaseSchema


class PredictionBase(BaseSchema):
    """Base prediction schema with common fields"""
    
    model_config = ConfigDict(
        protected_namespaces=(),
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    crypto_id: int = Field(gt=0, description="Cryptocurrency ID")
    model_name: str = Field(
        min_length=1, 
        max_length=50, 
        description="Name of ML model used"
    )
    predicted_price: Decimal = Field(gt=0, description="Predicted price")
    confidence_score: Optional[Decimal] = Field(
        default=None, 
        ge=0, 
        le=1, 
        description="Prediction confidence (0-1)"
    )
    prediction_horizon: int = Field(  
        ge=1, 
        le=365, 
        description="Prediction horizon in hours"
    )
    target_datetime: datetime = Field(description="Date/time the prediction is for")
    features_used: Optional[str] = Field(
        default=None, 
        description="JSON string of features used in prediction"
    )
    
    @field_validator('target_datetime')
    @classmethod
    def validate_target_datetime(cls, v):
        """Validate that target date is in the future"""
        now = datetime.now(timezone.utc)
        
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        
        if v <= now:
            raise ValueError('Target datetime must be in the future')
        return v
    
    @field_validator('features_used')
    @classmethod
    def validate_features_json(cls, v):
        """Validate that features_used is valid JSON"""
        if v is not None:
            try:
                json.loads(v)
            except json.JSONDecodeError:
                raise ValueError('features_used must be valid JSON')
        return v


class PredictionCreate(BaseSchema):
    """Schema for prediction requests"""
    
    model_config = ConfigDict(
        protected_namespaces=(),
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    crypto_id: int = Field(gt=0, description="Cryptocurrency ID")
    prediction_horizon: Optional[int] = Field(
        default=None,
        ge=1, 
        le=365, 
        description="Prediction horizon in days"
    )
    model_type: str = Field(
        default="LSTM", 
        description="Type of ML model to use"
    )
    include_confidence: bool = Field(
        default=True, 
        description="Whether to include confidence score"
    )
    days: Optional[int] = Field(
        default=None,
        ge=1,
        le=365,
        description="Prediction horizon in days (alternative to prediction_horizon)"
    )

    @model_validator(mode='before')
    @classmethod
    def validate_prediction_horizon(cls, values):
        """Handle days to prediction_horizon conversion"""
        if isinstance(values, dict):
            days = values.get('days')
            prediction_horizon = values.get('prediction_horizon')
            
            # If days provided but no prediction_horizon, convert
            if days is not None and not prediction_horizon:
                values['prediction_horizon'] = days * 24
            
            # Ensure at least one is provided
            if not days and not prediction_horizon:
                values['prediction_horizon'] = 24  # Default to 1 day
                
        return values

    @field_validator('model_type')
    @classmethod
    def validate_model_type(cls, v):
        """Validate model type"""
        valid_models = ["LSTM", "LINEAR_REGRESSION", "RANDOM_FOREST", "ARIMA", "ENSEMBLE"]
        if v.upper() not in valid_models:
            raise ValueError(f'Model type must be one of: {", ".join(valid_models)}')
        return v.upper()

class PredictionUpdate(BaseModel):
    """Schema for updating predictions"""
    
    model_config = ConfigDict(
        protected_namespaces=(),
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    predicted_price: Optional[Decimal] = Field(
        default=None, 
        gt=0, 
        description="Updated predicted price"
    )
    confidence_score: Optional[Decimal] = Field(
        default=None, 
        ge=0, 
        le=1, 
        description="Updated confidence score"
    )
    features_used: Optional[str] = Field(
        default=None, 
        description="Updated features JSON"
    )


class PredictionResponse(PredictionBase):
    """Schema for prediction data in API responses"""
    
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True
    )
    
    id: int = Field(description="Unique identifier")
    user_id: int = Field(description="User ID")
    created_at: datetime = Field(description="Creation timestamp")


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


class PredictionRequest(BaseModel):
    """Schema for prediction requests"""
    
    model_config = ConfigDict(
        protected_namespaces=(),
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    crypto_id: int = Field(gt=0, description="Cryptocurrency ID")
    prediction_horizon: int = Field(
        ge=1, 
        le=365, 
        description="Prediction horizon in days"
    )
    model_type: str = Field(
        default="LSTM", 
        description="Type of ML model to use"
    )
    include_confidence: bool = Field(
        default=True, 
        description="Whether to include confidence score"
    )
    days: Optional[int] = Field(
    default=None,
    ge=1,
    le=365,
    description="Prediction horizon in days (alternative to prediction_horizon)"
    )

    @field_validator('days')
    @classmethod 
    def convert_days_to_hours(cls, v, info):
        """Convert days to prediction_horizon if provided"""
        # In Pydantic v2, can't modify other fields in validator
        # This validation logic should be moved to model_validator
        return v

    @model_validator(mode='before')
    @classmethod
    def validate_prediction_horizon(cls, values):
        """Handle days to prediction_horizon conversion"""
        if isinstance(values, dict):
            days = values.get('days')
            prediction_horizon = values.get('prediction_horizon')
            
            # If days provided but no prediction_horizon, convert
            if days is not None and not prediction_horizon:
                values['prediction_horizon'] = days * 24
        
        return values

    @field_validator('model_type')
    @classmethod
    def validate_model_type(cls, v):
        """Validate model type"""
        valid_models = ["LSTM", "LINEAR_REGRESSION", "RANDOM_FOREST", "ARIMA", "ENSEMBLE"]
        if v.upper() not in valid_models:
            raise ValueError(f'Model type must be one of: {", ".join(valid_models)}')
        return v.upper()

class PredictionResult(BaseModel):
    """Schema for prediction results - Enhanced for frontend compatibility"""
    
    model_config = ConfigDict(
        protected_namespaces=(),
        str_strip_whitespace=True
    )
    
    # فیلدهای اصلی ML
    crypto_id: int = Field(description="Cryptocurrency ID")
    crypto_symbol: str = Field(description="Cryptocurrency symbol")
    model_name: str = Field(description="Model used for prediction")
    predicted_price: Decimal = Field(description="Predicted price")
    confidence_score: Decimal = Field(description="Confidence score")
    target_datetime: datetime = Field(description="Target prediction date")
    features_used: List[str] = Field(description="Features used in prediction")
    model_accuracy: Optional[float] = Field(default=None, description="Model accuracy percentage")
    prediction_id: Optional[str] = Field(default=None, description="Prediction job ID")
    
    # frontend compatibility
    current_price: Optional[Decimal] = Field(default=None, description="Current market price")
    confidence: Optional[int] = Field(default=None, description="Confidence as percentage (0-100)")
    symbol: Optional[str] = Field(default=None, description="Crypto symbol (alias for crypto_symbol)")
    timestamp: Optional[datetime] = Field(default=None, description="Prediction timestamp")
    
    @model_validator(mode='after')
    def populate_frontend_fields(self):
        """Populate frontend-specific fields from ML fields"""
        # Set symbol from crypto_symbol
        if not self.symbol and self.crypto_symbol:
            self.symbol = self.crypto_symbol
            
        # Convert confidence_score to percentage
        if not self.confidence and self.confidence_score is not None:
            # اگر confidence_score بین 0-1 است، به درصد تبدیل کن
            if self.confidence_score <= 1:
                self.confidence = int(float(self.confidence_score) * 100)
            else:
                self.confidence = int(float(self.confidence_score))
        
        # Set timestamp if not provided
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc)
            
        return self

        
class BatchPredictionRequest(BaseModel):
    """Schema for batch prediction requests"""
    
    model_config = ConfigDict(
        protected_namespaces=(),
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    crypto_ids: List[int] = Field(
        min_length=1, 
        max_length=10, 
        description="List of cryptocurrency IDs"
    )
    prediction_horizon: int = Field(
        ge=1, 
        le=365, 
        description="Prediction horizon in days"
    )
    model_type: str = Field(
        default="LSTM", 
        description="Type of ML model to use"
    )


class BatchPredictionResponse(BaseModel):
    """Schema for batch prediction responses"""
    
    model_config = ConfigDict(
        str_strip_whitespace=True
    )
    
    predictions: List[PredictionResult] = Field(description="List of predictions")
    total_requested: int = Field(description="Total predictions requested")
    successful_predictions: int = Field(description="Number of successful predictions")
    failed_predictions: int = Field(description="Number of failed predictions")
    errors: List[Dict[str, Any]] = Field(default=[], description="List of errors")


class ModelPerformance(BaseSchema):
    """Schema for ML model performance metrics"""
    
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


class PredictionAnalytics(BaseSchema):
    """Schema for prediction analytics"""
    
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
    """Schema for comparing predictions with actual prices"""
    
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
        """Validate alert type"""
        valid_types = ["price_reached", "confidence_changed", "accuracy_update"]
        if v not in valid_types:
            raise ValueError(f'Alert type must be one of: {", ".join(valid_types)}')
        return v


class ModelTrainingRequest(BaseModel):
    """Schema for model training requests"""
    
    model_config = ConfigDict(
        protected_namespaces=(),
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    crypto_id: int = Field(gt=0, description="Cryptocurrency ID")
    model_type: str = Field(description="Type of model to train")
    training_period_days: int = Field(
        ge=30, 
        le=3650, 
        description="Training period in days"
    )
    hyperparameters: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Model hyperparameters"
    )
    
    @field_validator('model_type')
    @classmethod
    def validate_training_model_type(cls, v):
        """Validate model type for training"""
        valid_models = ["LSTM", "LINEAR_REGRESSION", "RANDOM_FOREST", "ARIMA"]
        if v.upper() not in valid_models:
            raise ValueError(f'Model type must be one of: {", ".join(valid_models)}')
        return v.upper()


class ModelTrainingResponse(BaseModel):
    """Schema for model training responses"""
    
    model_config = ConfigDict(
        protected_namespaces=(),
        str_strip_whitespace=True
    )
    
    model_id: str = Field(description="Trained model identifier")
    crypto_id: int = Field(description="Cryptocurrency ID")
    model_type: str = Field(description="Model type")
    training_accuracy: float = Field(description="Training accuracy")
    validation_accuracy: float = Field(description="Validation accuracy")
    training_duration: float = Field(description="Training duration in seconds")
    model_size_mb: float = Field(description="Model size in megabytes")
    training_data_points: int = Field(description="Number of training data points")
    features_used: List[str] = Field(description="Features used in training")
    hyperparameters: Dict[str, Any] = Field(description="Final hyperparameters")
    training_completed_at: datetime = Field(description="Training completion timestamp")

class SymbolPredictionRequest(BaseSchema):
    """Schema for symbol-based prediction requests (no crypto_id required)"""
    
    model_config = ConfigDict(
        protected_namespaces=(),
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    days: int = Field(
        default=1,
        ge=1,
        le=365, 
        description="Prediction horizon in days"
    )
    model_type: str = Field(
        default="LSTM", 
        description="Type of ML model to use"
    )
    include_confidence: bool = Field(
        default=True, 
        description="Whether to include confidence score"
    )

    @field_validator('model_type')
    @classmethod
    def validate_model_type(cls, v):
        """Validate model type"""
        valid_models = ["LSTM", "LINEAR_REGRESSION", "RANDOM_FOREST", "ARIMA", "ENSEMBLE"]
        if v.upper() not in valid_models:
            raise ValueError(f'Model type must be one of: {", ".join(valid_models)}')
        return v.upper()