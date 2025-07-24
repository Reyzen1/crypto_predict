# File: backend/app/ml/__init__.py
# ML package initialization for CryptoPredict

"""
CryptoPredict ML Package
========================

This package contains all machine learning components for cryptocurrency
price prediction including:

- Models: LSTM neural networks and other ML models
- Preprocessing: Data cleaning and feature engineering
- Training: Model training pipelines
- Prediction: Inference services
- Evaluation: Model performance metrics
- Utils: Utility functions and helpers
- Config: Configuration management

Usage:
    from app.ml.models.lstm_predictor import LSTMPredictor
    from app.ml.preprocessing.data_processor import CryptoPriceDataProcessor
    from app.ml.config.ml_config import ml_config
"""

__version__ = "1.0.0"
__author__ = "CryptoPredict Team"

# Make commonly used classes available at package level
try:
    from .models.lstm_predictor import LSTMPredictor
    from .preprocessing.data_processor import CryptoPriceDataProcessor
    from .config.ml_config import ml_config, model_registry
    from .utils.model_utils import ModelMetrics, DataValidator
    
    __all__ = [
        'LSTMPredictor',
        'CryptoPriceDataProcessor', 
        'ml_config',
        'model_registry',
        'ModelMetrics',
        'DataValidator'
    ]
except ImportError as e:
    # Handle import errors gracefully during development
    print(f"Warning: Some ML components not available: {e}")
    __all__ = []