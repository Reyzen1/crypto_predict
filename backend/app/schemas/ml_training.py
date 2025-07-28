# File: backend/app/schemas/ml_training.py
# Pydantic schemas for ML training API endpoints

from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum


class TrainingStatus(str, Enum):
    """Training job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ModelType(str, Enum):
    """Available model types"""
    LSTM = "lstm"
    ARIMA = "arima"
    LINEAR_REGRESSION = "linear_regression"


class TrainingConfigRequest(BaseModel):
    """Configuration for training request"""
    sequence_length: Optional[int] = Field(60, ge=10, le=200, description="Input sequence length")
    lstm_units: Optional[List[int]] = Field([50, 50, 50], description="LSTM layer units")
    epochs: Optional[int] = Field(100, ge=1, le=500, description="Training epochs")
    batch_size: Optional[int] = Field(32, ge=8, le=128, description="Batch size")
    learning_rate: Optional[float] = Field(0.001, ge=0.0001, le=0.1, description="Learning rate")
    dropout_rate: Optional[float] = Field(0.2, ge=0.0, le=0.5, description="Dropout rate")
    validation_split: Optional[float] = Field(0.2, ge=0.1, le=0.3, description="Validation split")
    early_stopping_patience: Optional[int] = Field(10, ge=5, le=50, description="Early stopping patience")
    
    class Config:
        schema_extra = {
            "example": {
                "sequence_length": 60,
                "lstm_units": [50, 50, 50],
                "epochs": 100,
                "batch_size": 32,
                "learning_rate": 0.001,
                "dropout_rate": 0.2,
                "validation_split": 0.2,
                "early_stopping_patience": 10
            }
        }


class TrainingRequest(BaseModel):
    """Request to start training a model"""
    crypto_symbol: str = Field(..., description="Cryptocurrency symbol (e.g., BTC)")
    model_type: ModelType = Field(ModelType.LSTM, description="Type of model to train")
    training_config: Optional[TrainingConfigRequest] = Field(None, description="Training configuration")
    data_days_back: Optional[int] = Field(180, ge=30, le=1000, description="Days of historical data")
    force_retrain: Optional[bool] = Field(False, description="Force retrain even if recent model exists")
    
    @validator('crypto_symbol')
    def validate_crypto_symbol(cls, v):
        return v.upper().strip()
    
    class Config:
        schema_extra = {
            "example": {
                "crypto_symbol": "BTC",
                "model_type": "lstm",
                "data_days_back": 180,
                "force_retrain": False,
                "training_config": {
                    "epochs": 50,
                    "batch_size": 32
                }
            }
        }


class TrainingResponse(BaseModel):
    """Response when training is started"""
    job_id: str = Field(..., description="Training job identifier")
    crypto_symbol: str = Field(..., description="Cryptocurrency symbol")
    model_type: str = Field(..., description="Model type being trained")
    status: TrainingStatus = Field(..., description="Current training status")
    message: str = Field(..., description="Human-readable status message")
    started_at: datetime = Field(..., description="Training start time")
    estimated_duration_minutes: Optional[int] = Field(None, description="Estimated training duration")
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "train_btc_lstm_20240128_143022",
                "crypto_symbol": "BTC",
                "model_type": "lstm",
                "status": "pending",
                "message": "Training job queued successfully",
                "started_at": "2024-01-28T14:30:22Z",
                "estimated_duration_minutes": 15
            }
        }


class TrainingStatusResponse(BaseModel):
    """Response for training status check"""
    job_id: str = Field(..., description="Training job identifier")
    crypto_symbol: str = Field(..., description="Cryptocurrency symbol")
    model_type: str = Field(..., description="Model type")
    status: TrainingStatus = Field(..., description="Current status")
    progress_percentage: Optional[float] = Field(None, ge=0, le=100, description="Training progress")
    current_epoch: Optional[int] = Field(None, description="Current epoch (if running)")
    total_epochs: Optional[int] = Field(None, description="Total epochs")
    started_at: datetime = Field(..., description="Start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")
    duration_seconds: Optional[int] = Field(None, description="Duration in seconds")
    message: str = Field(..., description="Status message")
    error_details: Optional[str] = Field(None, description="Error details if failed")
    
    # Training metrics (if completed)
    training_metrics: Optional[Dict[str, float]] = Field(None, description="Final training metrics")
    validation_metrics: Optional[Dict[str, float]] = Field(None, description="Final validation metrics")
    model_performance: Optional[Dict[str, float]] = Field(None, description="Model performance metrics")
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "train_btc_lstm_20240128_143022",
                "crypto_symbol": "BTC",
                "model_type": "lstm",
                "status": "running",
                "progress_percentage": 65.0,
                "current_epoch": 65,
                "total_epochs": 100,
                "started_at": "2024-01-28T14:30:22Z",
                "duration_seconds": 540,
                "message": "Training in progress - epoch 65/100"
            }
        }


class ModelInfo(BaseModel):
    """Information about a trained model"""
    model_id: str = Field(..., description="Model identifier")
    crypto_symbol: str = Field(..., description="Cryptocurrency symbol")
    model_type: str = Field(..., description="Model type")
    version: str = Field(..., description="Model version")
    is_active: bool = Field(..., description="Is this the active model")
    created_at: datetime = Field(..., description="Model creation time")
    training_duration_seconds: Optional[int] = Field(None, description="Training duration")
    data_points_used: Optional[int] = Field(None, description="Training data points")
    performance_metrics: Optional[Dict[str, float]] = Field(None, description="Performance metrics")
    model_path: Optional[str] = Field(None, description="Model file path")
    
    class Config:
        schema_extra = {
            "example": {
                "model_id": "btc_lstm_20240128_145530",
                "crypto_symbol": "BTC",
                "model_type": "lstm",
                "version": "1.0",
                "is_active": True,
                "created_at": "2024-01-28T14:55:30Z",
                "training_duration_seconds": 1200,
                "data_points_used": 4320,
                "performance_metrics": {
                    "rmse": 1250.5,
                    "mae": 980.2,
                    "r2_score": 0.87
                }
            }
        }


class ModelListResponse(BaseModel):
    """Response for model list endpoint"""
    models: List[ModelInfo] = Field(..., description="List of models")
    total: int = Field(..., description="Total number of models")
    active_models: int = Field(..., description="Number of active models")
    
    class Config:
        schema_extra = {
            "example": {
                "models": [
                    {
                        "model_id": "btc_lstm_20240128_145530",
                        "crypto_symbol": "BTC",
                        "model_type": "lstm",
                        "version": "1.0",
                        "is_active": True,
                        "created_at": "2024-01-28T14:55:30Z"
                    }
                ],
                "total": 3,
                "active_models": 1
            }
        }


class ModelActivationRequest(BaseModel):
    """Request to activate a model"""
    model_id: str = Field(..., description="Model identifier to activate")
    force_activation: Optional[bool] = Field(False, description="Force activation even if performance is low")
    
    class Config:
        schema_extra = {
            "example": {
                "model_id": "btc_lstm_20240128_145530",
                "force_activation": False
            }
        }


class ModelActivationResponse(BaseModel):
    """Response for model activation"""
    model_id: str = Field(..., description="Activated model identifier")
    crypto_symbol: str = Field(..., description="Cryptocurrency symbol")
    previous_active_model: Optional[str] = Field(None, description="Previously active model ID")
    activated_at: datetime = Field(..., description="Activation time")
    message: str = Field(..., description="Activation message")
    
    class Config:
        schema_extra = {
            "example": {
                "model_id": "btc_lstm_20240128_145530",
                "crypto_symbol": "BTC",
                "previous_active_model": "btc_lstm_20240127_091234",
                "activated_at": "2024-01-28T15:00:00Z",
                "message": "Model activated successfully"
            }
        }


class ModelPerformanceResponse(BaseModel):
    """Response for model performance metrics"""
    model_id: str = Field(..., description="Model identifier")
    crypto_symbol: str = Field(..., description="Cryptocurrency symbol")
    model_type: str = Field(..., description="Model type")
    
    # Training metrics
    training_metrics: Dict[str, float] = Field(..., description="Training metrics")
    validation_metrics: Dict[str, float] = Field(..., description="Validation metrics")
    
    # Performance metrics
    rmse: float = Field(..., description="Root Mean Square Error")
    mae: float = Field(..., description="Mean Absolute Error")
    r2_score: float = Field(..., description="R-squared score")
    mape: Optional[float] = Field(None, description="Mean Absolute Percentage Error")
    
    # Model info
    created_at: datetime = Field(..., description="Model creation time")
    data_points_used: int = Field(..., description="Training data points")
    training_duration_seconds: int = Field(..., description="Training duration")
    
    class Config:
        schema_extra = {
            "example": {
                "model_id": "btc_lstm_20240128_145530",
                "crypto_symbol": "BTC",
                "model_type": "lstm",
                "training_metrics": {
                    "loss": 0.0023,
                    "val_loss": 0.0025
                },
                "validation_metrics": {
                    "rmse": 1250.5,
                    "mae": 980.2
                },
                "rmse": 1250.5,
                "mae": 980.2,
                "r2_score": 0.87,
                "mape": 3.2,
                "created_at": "2024-01-28T14:55:30Z",
                "data_points_used": 4320,
                "training_duration_seconds": 1200
            }
        }