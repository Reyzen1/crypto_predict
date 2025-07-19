# File: ./scripts/fix-prediction-schemas.sh
# Fix Pydantic schema issues with model namespace and datetime comparison

#!/bin/bash

set -e

echo "🔧 Fixing Prediction Schema Issues"
echo "=================================="

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "❌ Backend directory not found! Please run from project root."
    exit 1
fi

echo "📝 Updating prediction schemas..."

# Create fixed prediction schemas
cat > backend/app/schemas/prediction.py << 'EOF'
# File: ./backend/app/schemas/prediction.py
# ML prediction related Pydantic schemas - FIXED

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, ConfigDict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json

from app.schemas.common import BaseSchema


class PredictionBase(BaseSchema):
    """Base prediction schema with common fields"""
    
    # Configure model to avoid protected namespace conflicts
    model_config = ConfigDict(protected_namespaces=())
    
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
    target_date: datetime = Field(description="Date/time the prediction is for")
    features_used: Optional[str] = Field(
        default=None, 
        description="JSON string of features used in prediction"
    )
    
    @validator('target_date')
    def validate_target_date(cls, v):
        """Validate that target date is in the future"""
        # Use timezone-aware datetime for comparison
        now = datetime.now(timezone.utc)
        
        # If v is naive, assume it's UTC
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        
        if v <= now:
            raise ValueError('Target date must be in the future')
        return v
    
    @validator('features_used')
    def validate_features_json(cls, v):
        """Validate that features_used is valid JSON"""
        if v is not None:
            try:
                json.loads(v)
            except json.JSONDecodeError:
                raise ValueError('features_used must be valid JSON')
        return v


class PredictionCreate(PredictionBase):
    """Schema for creating new predictions"""
    
    user_id: int = Field(gt=0, description="User ID who requested the prediction")


class PredictionUpdate(BaseModel):
    """Schema for updating predictions"""
    
    model_config = ConfigDict(protected_namespaces=())
    
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
    
    id: int = Field(description="Unique identifier")
    user_id: int = Field(description="User ID")
    created_at: datetime = Field(description="Creation timestamp")


class PredictionWithDetails(PredictionResponse):
    """Schema for prediction with additional details"""
    
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
    
    model_config = ConfigDict(protected_namespaces=())
    
    crypto_id: int = Field(gt=0, description="Cryptocurrency ID")
    prediction_horizon: int = Field(
        ge=1, 
        le=365, 
        description="Prediction horizon in days"
    )
    ml_model_type: str = Field(  # Renamed from model_type
        default="LSTM", 
        description="Type of ML model to use"
    )
    include_confidence: bool = Field(
        default=True, 
        description="Whether to include confidence score"
    )
    
    @validator('ml_model_type')
    def validate_model_type(cls, v):
        """Validate model type"""
        valid_models = ["LSTM", "LINEAR_REGRESSION", "RANDOM_FOREST", "ARIMA", "ENSEMBLE"]
        if v.upper() not in valid_models:
            raise ValueError(f'Model type must be one of: {", ".join(valid_models)}')
        return v.upper()


class PredictionResult(BaseModel):
    """Schema for prediction results"""
    
    model_config = ConfigDict(protected_namespaces=())
    
    crypto_id: int = Field(description="Cryptocurrency ID")
    crypto_symbol: str = Field(description="Cryptocurrency symbol")
    model_name: str = Field(description="Model used for prediction")
    predicted_price: Decimal = Field(description="Predicted price")
    confidence_score: Decimal = Field(description="Confidence score")
    target_date: datetime = Field(description="Target prediction date")
    features_used: List[str] = Field(description="Features used in prediction")
    ml_model_accuracy: Optional[float] = Field(  # Renamed from model_accuracy
        default=None, 
        description="Historical accuracy of the model"
    )
    prediction_id: Optional[int] = Field(
        default=None, 
        description="Saved prediction ID"
    )


class BatchPredictionRequest(BaseModel):
    """Schema for batch prediction requests"""
    
    model_config = ConfigDict(protected_namespaces=())
    
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
    ml_model_type: str = Field(  # Renamed from model_type
        default="LSTM", 
        description="Type of ML model to use"
    )


class BatchPredictionResponse(BaseModel):
    """Schema for batch prediction responses"""
    
    predictions: List[PredictionResult] = Field(description="List of predictions")
    total_requested: int = Field(description="Total predictions requested")
    successful_predictions: int = Field(description="Number of successful predictions")
    failed_predictions: int = Field(description="Number of failed predictions")
    errors: List[Dict[str, Any]] = Field(default=[], description="List of errors")


class ModelPerformance(BaseSchema):
    """Schema for ML model performance metrics"""
    
    model_config = ConfigDict(protected_namespaces=())
    
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
    
    model_config = ConfigDict(protected_namespaces=())
    
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
    
    prediction_id: int = Field(description="Prediction ID")
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
    target_date: datetime = Field(description="Prediction target date")
    is_expired: bool = Field(description="Whether prediction period has passed")


class UserPredictionStats(BaseSchema):
    """Schema for user prediction statistics"""
    
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
    
    user_id: int = Field(description="User ID")
    prediction_id: int = Field(description="Prediction ID")
    alert_type: str = Field(description="Alert type")
    threshold_percentage: float = Field(description="Alert threshold percentage")
    is_active: bool = Field(default=True, description="Whether alert is active")
    
    @validator('alert_type')
    def validate_alert_type(cls, v):
        """Validate alert type"""
        valid_types = ["price_reached", "confidence_changed", "accuracy_update"]
        if v not in valid_types:
            raise ValueError(f'Alert type must be one of: {", ".join(valid_types)}')
        return v


class ModelTrainingRequest(BaseModel):
    """Schema for model training requests"""
    
    model_config = ConfigDict(protected_namespaces=())
    
    crypto_id: int = Field(gt=0, description="Cryptocurrency ID")
    ml_model_type: str = Field(description="Type of model to train")  # Renamed
    training_period_days: int = Field(
        ge=30, 
        le=3650, 
        description="Training period in days"
    )
    hyperparameters: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Model hyperparameters"
    )
    
    @validator('ml_model_type')
    def validate_training_model_type(cls, v):
        """Validate model type for training"""
        valid_models = ["LSTM", "LINEAR_REGRESSION", "RANDOM_FOREST", "ARIMA"]
        if v.upper() not in valid_models:
            raise ValueError(f'Model type must be one of: {", ".join(valid_models)}')
        return v.upper()


class ModelTrainingResponse(BaseModel):
    """Schema for model training responses"""
    
    model_config = ConfigDict(protected_namespaces=())
    
    trained_model_id: str = Field(description="Trained model identifier")  # Renamed
    crypto_id: int = Field(description="Cryptocurrency ID")
    ml_model_type: str = Field(description="Model type")  # Renamed
    training_accuracy: float = Field(description="Training accuracy")
    validation_accuracy: float = Field(description="Validation accuracy")
    training_duration: float = Field(description="Training duration in seconds")
    trained_model_size_mb: float = Field(description="Model size in megabytes")  # Renamed
    training_data_points: int = Field(description="Number of training data points")
    features_used: List[str] = Field(description="Features used in training")
    hyperparameters: Dict[str, Any] = Field(description="Final hyperparameters")
    training_completed_at: datetime = Field(description="Training completion timestamp")
EOF

echo "✅ Prediction schemas fixed!"

echo ""
echo "🔧 Key fixes applied:"
echo "   - Added model_config = ConfigDict(protected_namespaces=()) to avoid conflicts"
echo "   - Fixed datetime comparison using timezone-aware datetime"
echo "   - Renamed conflicting fields:"
echo "     • model_type → ml_model_type"
echo "     • model_accuracy → ml_model_accuracy"
echo "     • model_id → trained_model_id"
echo "     • model_size_mb → trained_model_size_mb"

echo ""
echo "🧪 Now run schema tests again:"
echo "   ./scripts/test-schemas.sh"