# File: backend/app/ml/config/ml_config.py
# Complete fixed version of ML configuration

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ScalingMethod(str, Enum):
    """Scaling methods for feature normalization"""
    STANDARD = "standard"
    MINMAX = "minmax"
    ROBUST = "robust"
    QUANTILE = "quantile"


class MLConfig(BaseModel):
    """ML Configuration settings"""
    
    # Model hyperparameters
    sequence_length: int = Field(default=60)
    lstm_sequence_length: int = Field(default=60)  # Add missing attribute
    lstm_units: List[int] = Field(default=[50, 50, 50])
    dropout_rate: float = Field(default=0.2)
    lstm_dropout_rate: float = Field(default=0.2)  # Add missing attribute
    learning_rate: float = Field(default=0.001)
    lstm_learning_rate: float = Field(default=0.001)  # Add missing attribute
    batch_size: int = Field(default=32)
    lstm_batch_size: int = Field(default=32)  # Add missing attribute
    epochs: int = Field(default=100)
    lstm_epochs: int = Field(default=100)  # Add missing attribute
    validation_split: float = Field(default=0.2)
    lstm_validation_split: float = Field(default=0.2)  # Add missing attribute
    early_stopping_patience: int = Field(default=10)
    
    # Data preprocessing
    scaling_method: ScalingMethod = Field(default=ScalingMethod.STANDARD)
    handle_missing: bool = Field(default=True)
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
    """Simple model registry - FIXED VERSION"""
    
    def __init__(self):
        self.models: Dict[str, Dict[str, Any]] = {}
        self.active_models: Dict[str, str] = {}
    
    def register_model(self, model_id: str, crypto_symbol: str, model_type: str, 
                      model_path: str, performance_metrics: Dict[str, float], 
                      metadata: Optional[Dict[str, Any]] = None) -> None:
        """Register a new model"""
        self.models[model_id] = {
            'model_id': model_id,  # Add model_id to the data
            'crypto_symbol': crypto_symbol,
            'model_type': model_type,
            'model_path': model_path,
            'performance_metrics': performance_metrics,
            'metadata': metadata or {},
            'registered_at': datetime.utcnow().isoformat(),
            'is_active': False
        }
    
    def set_active_model(self, crypto_symbol: str, model_id: str) -> None:
        """Set a model as active for a cryptocurrency"""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
        if crypto_symbol in self.active_models:
            old_model_id = self.active_models[crypto_symbol]
            if old_model_id in self.models:
                self.models[old_model_id]['is_active'] = False
        self.active_models[crypto_symbol] = model_id
        self.models[model_id]['is_active'] = True
    
    def get_active_model(self, crypto_symbol: str) -> Optional[Dict[str, Any]]:
        """Get the active model for a cryptocurrency"""
        if crypto_symbol not in self.active_models:
            return None
        model_id = self.active_models[crypto_symbol]
        return self.models.get(model_id)
    
    def list_models(self, crypto_symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all models, optionally filtered by crypto symbol - FIXED VERSION"""
        models = list(self.models.values())
        if crypto_symbol:
            models = [m for m in models if m.get('crypto_symbol') == crypto_symbol]
        
        # FIXED: Safe sorting - handle missing 'registered_at' key
        def get_sort_key(model):
            # Try 'registered_at' first, fallback to other timestamps
            if 'registered_at' in model:
                return model['registered_at']
            elif 'metadata' in model and 'created_at' in model['metadata']:
                return model['metadata']['created_at']
            else:
                # Fallback to current time as ISO string
                return datetime.now().isoformat()
        
        try:
            return sorted(models, key=get_sort_key, reverse=True)
        except Exception as e:
            # If sorting fails, return unsorted list
            return models
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model"""
        return self.models.get(model_id)
    
    def get_model_performance(self, model_id: str) -> Optional[Dict[str, float]]:
        """Get performance metrics for a model"""
        if model_id not in self.models:
            return None
        return self.models[model_id]['performance_metrics']
    
    def remove_model(self, model_id: str) -> bool:
        """Remove a model from registry"""
        if model_id not in self.models:
            return False
        crypto_symbol = self.models[model_id]['crypto_symbol']
        if crypto_symbol in self.active_models and self.active_models[crypto_symbol] == model_id:
            del self.active_models[crypto_symbol]
        del self.models[model_id]
        return True


# Global model registry instance
model_registry = ModelRegistry()