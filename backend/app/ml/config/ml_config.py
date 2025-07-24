# File: backend/app/ml/config/ml_config.py
# Configuration settings for ML models - FIXED protected namespace warning

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

from pydantic import Field, ConfigDict
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import os


class ModelType(str, Enum):
    LSTM = "lstm"
    LINEAR_REGRESSION = "linear_regression"
    RANDOM_FOREST = "random_forest"


class ScalingMethod(str, Enum):
    MINMAX = "minmax"
    STANDARD = "standard"
    ROBUST = "robust"


class MLConfig(BaseSettings):
    """Machine Learning configuration settings"""
    
    # Fix protected namespace warning
    model_config = ConfigDict(
        env_file=".env",
        env_prefix="ML_",
        case_sensitive=False,
        protected_namespaces=('settings_',)  # This fixes the warning
    )
    
    # LSTM Model Parameters
    lstm_sequence_length: int = Field(default=60)
    lstm_units: List[int] = Field(default=[50, 50, 50])
    lstm_dropout_rate: float = Field(default=0.2)
    lstm_learning_rate: float = Field(default=0.001)
    lstm_batch_size: int = Field(default=32)
    lstm_epochs: int = Field(default=100)
    lstm_validation_split: float = Field(default=0.2)
    
    # Data Processing Parameters - REDUCED requirements
    scaling_method: ScalingMethod = Field(default=ScalingMethod.MINMAX)
    handle_missing: str = Field(default="interpolate")
    add_technical_indicators: bool = Field(default=True)
    add_time_features: bool = Field(default=True)
    add_price_features: bool = Field(default=True)
    outlier_threshold: float = Field(default=4.0)  # Less aggressive
    min_data_points: int = Field(default=50)       # Much lower requirement
    
    # Training Data Split
    train_ratio: float = Field(default=0.7)
    validation_ratio: float = Field(default=0.15)
    test_ratio: float = Field(default=0.15)
    
    # Model Storage - renamed to avoid protected namespace
    models_storage_path: str = Field(default="models")  # Changed from model_storage_path


# Global ML configuration instance
ml_config = MLConfig()


class ModelRegistry:
    """Simple model registry"""
    
    def __init__(self):
        self.models: Dict[str, Dict[str, Any]] = {}
        self.active_models: Dict[str, str] = {}
    
    def register_model(self, model_id: str, crypto_symbol: str, model_type: str, 
                      model_path: str, performance_metrics: Dict[str, float], 
                      metadata: Optional[Dict[str, Any]] = None) -> None:
        self.models[model_id] = {
            'crypto_symbol': crypto_symbol,
            'model_type': model_type,
            'model_path': model_path,
            'performance_metrics': performance_metrics,
            'metadata': metadata or {},
            'registered_at': datetime.utcnow().isoformat(),
            'is_active': False
        }
    
    def set_active_model(self, crypto_symbol: str, model_id: str) -> None:
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
        if crypto_symbol in self.active_models:
            old_model_id = self.active_models[crypto_symbol]
            if old_model_id in self.models:
                self.models[old_model_id]['is_active'] = False
        self.active_models[crypto_symbol] = model_id
        self.models[model_id]['is_active'] = True
    
    def get_active_model(self, crypto_symbol: str) -> Optional[Dict[str, Any]]:
        if crypto_symbol not in self.active_models:
            return None
        model_id = self.active_models[crypto_symbol]
        return self.models.get(model_id)
    
    def list_models(self, crypto_symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        models = list(self.models.values())
        if crypto_symbol:
            models = [m for m in models if m['crypto_symbol'] == crypto_symbol]
        return sorted(models, key=lambda x: x['registered_at'], reverse=True)
    
    def get_model_performance(self, model_id: str) -> Optional[Dict[str, float]]:
        if model_id not in self.models:
            return None
        return self.models[model_id]['performance_metrics']
    
    def remove_model(self, model_id: str) -> bool:
        if model_id not in self.models:
            return False
        crypto_symbol = self.models[model_id]['crypto_symbol']
        if crypto_symbol in self.active_models and self.active_models[crypto_symbol] == model_id:
            del self.active_models[crypto_symbol]
        del self.models[model_id]
        return True


# Global model registry instance
model_registry = ModelRegistry()