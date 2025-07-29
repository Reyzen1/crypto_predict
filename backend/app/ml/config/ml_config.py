# File: backend/app/ml/config/ml_config.py
# TRULY DYNAMIC ML Configuration - ZERO Hard-coding

import os
import re
import pandas as pd
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Tuple
from pydantic import BaseModel, Field

# NEW: Import persistent registry
from .persistent_registry import create_persistent_model_registry


class MLConfig(BaseModel):
    """
    Minimal ML Configuration - Only essential settings
    NO feature definitions - everything is discovered dynamically
    """
    
    # Core Training Configuration (MODEL-AGNOSTIC)
    default_epochs: int = Field(default=50)
    default_batch_size: int = Field(default=32)
    default_sequence_length: int = Field(default=60)
    default_learning_rate: float = Field(default=0.001)
    default_dropout_rate: float = Field(default=0.2)
    
    # Data Processing Configuration (BEHAVIOR ONLY)
    scaling_method: str = Field(default="standard")  # How to scale, not what to scale
    handle_missing: bool = Field(default=True)       # Whether to handle, not which columns
    add_technical_indicators: bool = Field(default=True)  # Whether to add, not which ones
    add_time_features: bool = Field(default=True)         # Whether to add, not which ones  
    add_price_features: bool = Field(default=True)        # Whether to add, not which ones
    outlier_threshold: float = Field(default=4.0)         # Threshold, not columns
    min_data_points: int = Field(default=50)              # Minimum requirement
    
    # LSTM Specific Configuration (STRUCTURE ONLY)
    lstm_sequence_length: int = Field(default=60)
    lstm_units: List[int] = Field(default=[50, 50, 50])
    lstm_dropout_rate: float = Field(default=0.2)
    lstm_learning_rate: float = Field(default=0.001)
    lstm_batch_size: int = Field(default=32)
    lstm_epochs: int = Field(default=100)
    lstm_validation_split: float = Field(default=0.2)
    
    # Storage Configuration
    models_storage_path: str = Field(default="models")
    
    class Config:
        extra = "allow"


# Global ML configuration instance
ml_config = MLConfig()


class SmartFeatureDetector:
    """
    Intelligent feature detector that analyzes data to determine:
    - What columns exist
    - What type each column is (price, volume, time, etc.)
    - What features can be engineered
    - What target should be used
    
    ZERO hard-coding - everything discovered from data patterns
    """
    
    @staticmethod
    def analyze_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Completely analyze dataframe and determine all feature information
        
        Args:
            df: Input dataframe
            
        Returns:
            Complete analysis with discovered features
        """
        analysis = {
            "columns": df.columns.tolist(),
            "dtypes": df.dtypes.to_dict(),
            "shape": df.shape,
            "feature_types": {},
            "target_candidates": [],
            "time_columns": [],
            "numeric_columns": [],
            "categorical_columns": [],
            "engineerable_features": {},
            "data_quality": {}
        }
        
        # Analyze each column
        for col in df.columns:
            analysis["feature_types"][col] = SmartFeatureDetector._classify_column(col, df[col])
        
        # Find target candidates (price-related columns)
        analysis["target_candidates"] = SmartFeatureDetector._find_target_candidates(analysis["feature_types"])
        
        # Categorize columns by type
        analysis["time_columns"] = SmartFeatureDetector._find_time_columns(analysis["feature_types"])
        analysis["numeric_columns"] = SmartFeatureDetector._find_numeric_columns(df, analysis["feature_types"])
        analysis["categorical_columns"] = SmartFeatureDetector._find_categorical_columns(analysis["feature_types"])
        
        # Determine engineerable features
        analysis["engineerable_features"] = SmartFeatureDetector._find_engineerable_features(analysis)
        
        # Data quality assessment
        analysis["data_quality"] = SmartFeatureDetector._assess_data_quality(df)
        
        return analysis
    
    @staticmethod
    def _classify_column(col_name: str, col_data: pd.Series) -> Dict[str, Any]:
        """
        Classify a single column based on name patterns and data content
        
        Returns:
            Classification information
        """
        col_lower = col_name.lower()
        
        classification = {
            "name": col_name,
            "dtype": str(col_data.dtype),
            "is_numeric": pd.api.types.is_numeric_dtype(col_data),
            "is_datetime": pd.api.types.is_datetime64_any_dtype(col_data),
            "null_count": col_data.isnull().sum(),
            "unique_count": col_data.nunique(),
            "patterns": []
        }
        
        # Pattern detection (completely dynamic)
        patterns = {
            "price": ["price", "cost", "value", "rate", "usd", "btc", "eth"],
            "volume": ["volume", "vol", "amount", "quantity", "size"],
            "time": ["time", "date", "timestamp", "created", "updated", "at"],
            "change": ["change", "diff", "delta", "pct", "percent"],
            "high_low": ["high", "low", "max", "min", "top", "bottom"],
            "open_close": ["open", "close", "start", "end"],
            "market": ["market", "cap", "capitalization", "mcap"],
            "technical": ["rsi", "macd", "sma", "ema", "bb", "bollinger"],
            "id": ["id", "uuid", "key", "index", "_id"]
        }
        
        # Check which patterns match
        for pattern_type, keywords in patterns.items():
            if any(keyword in col_lower for keyword in keywords):
                classification["patterns"].append(pattern_type)
        
        # Determine primary type
        if classification["is_datetime"] or "time" in classification["patterns"]:
            classification["primary_type"] = "datetime"
        elif "id" in classification["patterns"]:
            classification["primary_type"] = "identifier"
        elif classification["is_numeric"]:
            if "price" in classification["patterns"]:
                classification["primary_type"] = "price"
            elif "volume" in classification["patterns"]:
                classification["primary_type"] = "volume"
            elif "change" in classification["patterns"]:
                classification["primary_type"] = "change_indicator"
            else:
                classification["primary_type"] = "numeric_feature"
        else:
            classification["primary_type"] = "categorical"
        
        return classification
    
    @staticmethod
    def _find_target_candidates(feature_types: Dict[str, Any]) -> List[str]:
        """Find potential target columns for prediction"""
        candidates = []
        
        # Priority scoring for target selection
        for col, info in feature_types.items():
            score = 0
            
            # Price-related patterns get highest priority
            if "price" in info["patterns"]:
                score += 100
                
                # Specific price types
                if any(keyword in col.lower() for keyword in ["close", "current", "last"]):
                    score += 50
                elif any(keyword in col.lower() for keyword in ["open", "high", "low"]):
                    score += 30
            
            # Must be numeric
            if not info["is_numeric"]:
                score = 0
            
            # Penalize high null counts
            if info["null_count"] > 0:
                score -= info["null_count"] * 5
            
            if score > 0:
                candidates.append({"column": col, "score": score})
        
        # Sort by score and return column names
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return [c["column"] for c in candidates]
    
    @staticmethod
    def _find_time_columns(feature_types: Dict[str, Any]) -> List[str]:
        """Find time-related columns"""
        return [col for col, info in feature_types.items() 
                if info["primary_type"] == "datetime"]
    
    @staticmethod
    def _find_numeric_columns(df: pd.DataFrame, feature_types: Dict[str, Any]) -> List[str]:
        """Find numeric columns suitable for ML features"""
        numeric_cols = []
        
        for col, info in feature_types.items():
            if (info["is_numeric"] and 
                info["primary_type"] != "identifier" and
                info["null_count"] < len(df) * 0.5):  # Less than 50% null
                numeric_cols.append(col)
        
        return numeric_cols
    
    @staticmethod
    def _find_categorical_columns(feature_types: Dict[str, Any]) -> List[str]:
        """Find categorical columns"""
        return [col for col, info in feature_types.items() 
                if info["primary_type"] == "categorical" and info["unique_count"] < 50]
    
    @staticmethod
    def _find_engineerable_features(analysis: Dict[str, Any]) -> Dict[str, List[str]]:
        """Find what features can be engineered from existing data"""
        engineerable = {
            "price_features": [],
            "volume_features": [],
            "time_features": [],
            "technical_indicators": [],
            "ratio_features": []
        }
        
        feature_types = analysis["feature_types"]
        
        # Price-based features
        price_cols = [col for col, info in feature_types.items() if "price" in info["patterns"]]
        if price_cols:
            engineerable["price_features"] = [
                "price_returns", "price_volatility", "price_momentum"
            ]
        
        # Volume-based features  
        volume_cols = [col for col, info in feature_types.items() if "volume" in info["patterns"]]
        if volume_cols:
            engineerable["volume_features"] = [
                "volume_sma", "volume_change", "volume_ratio"
            ]
        
        # Time-based features
        if analysis["time_columns"]:
            engineerable["time_features"] = [
                "hour", "day_of_week", "month", "quarter", "is_weekend"
            ]
        
        # Technical indicators (if we have price data)
        if price_cols:
            engineerable["technical_indicators"] = [
                "rsi", "macd", "bollinger_bands", "moving_averages"
            ]
        
        # Ratio features (if we have multiple numeric columns)
        numeric_cols = analysis["numeric_columns"]
        if len(numeric_cols) >= 2:
            engineerable["ratio_features"] = [f"{col1}_{col2}_ratio" 
                                           for col1 in numeric_cols[:3] 
                                           for col2 in numeric_cols[:3] 
                                           if col1 != col2]
        
        return engineerable
    
    @staticmethod
    def _assess_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
        """Assess overall data quality"""
        total_cells = df.shape[0] * df.shape[1]
        null_cells = df.isnull().sum().sum()
        
        return {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "null_percentage": (null_cells / total_cells) * 100 if total_cells > 0 else 0,
            "duplicate_rows": df.duplicated().sum(),
            "data_types": df.dtypes.value_counts().to_dict(),
            "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
            "date_range": SmartFeatureDetector._get_date_range(df)
        }
    
    @staticmethod
    def _get_date_range(df: pd.DataFrame) -> Dict[str, Any]:
        """Get date range if datetime columns exist"""
        date_info = {"has_datetime": False}
        
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                date_info["has_datetime"] = True
                date_info["start_date"] = df[col].min()
                date_info["end_date"] = df[col].max()
                date_info["time_column"] = col
                break
        
        return date_info


class DynamicConfigFactory:
    """
    Factory that creates configurations based on actual data analysis
    NO predetermined feature lists
    """
    
    @staticmethod
    def create_training_config(
        data_analysis: Dict[str, Any],
        model_type: str = "lstm",
        custom_overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create training configuration based on data analysis
        
        Args:
            data_analysis: Result from SmartFeatureDetector.analyze_dataframe()
            model_type: Type of model
            custom_overrides: Any custom settings
            
        Returns:
            Complete training configuration
        """
        # Base configuration from data analysis
        config = {
            "model_type": model_type,
            "data_info": {
                "available_features": data_analysis["numeric_columns"],
                "target_column": data_analysis["target_candidates"][0] if data_analysis["target_candidates"] else None,
                "time_column": data_analysis["time_columns"][0] if data_analysis["time_columns"] else None,
                "total_samples": data_analysis["shape"][0]
            },
            "feature_engineering": {
                "enabled_features": data_analysis["engineerable_features"],
                "scaling_method": ml_config.scaling_method,
                "handle_missing": ml_config.handle_missing
            }
        }
        
        # Add model-specific configuration
        if model_type.lower() == "lstm":
            # Adjust sequence length based on data size
            recommended_sequence = min(
                ml_config.lstm_sequence_length,
                data_analysis["shape"][0] // 10  # 10% of data max
            )
            
            config["model_params"] = {
                "sequence_length": recommended_sequence,
                "lstm_units": ml_config.lstm_units,
                "dropout_rate": ml_config.lstm_dropout_rate,
                "learning_rate": ml_config.lstm_learning_rate,
                "batch_size": ml_config.lstm_batch_size,
                "epochs": ml_config.lstm_epochs,
                "validation_split": ml_config.lstm_validation_split
            }
        
        # Apply custom overrides
        if custom_overrides:
            config = DynamicConfigFactory._deep_update(config, custom_overrides)
        
        return config
    
    @staticmethod
    def _deep_update(base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Deep update dictionary"""
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                base_dict[key] = DynamicConfigFactory._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
        return base_dict


# Factory functions - completely data-driven
def analyze_and_configure(df: pd.DataFrame, model_type: str = "lstm") -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    One-stop function to analyze data and create configuration
    
    Args:
        df: Input dataframe
        model_type: Model type to configure for
        
    Returns:
        Tuple of (data_analysis, training_config)
    """
    # Analyze data completely
    data_analysis = SmartFeatureDetector.analyze_dataframe(df)
    
    # Create configuration based on analysis
    training_config = DynamicConfigFactory.create_training_config(data_analysis, model_type)
    
    return data_analysis, training_config


def ensure_models_directory() -> str:
    """Ensure models directory exists and return path"""
    models_dir = ml_config.models_storage_path
    os.makedirs(models_dir, exist_ok=True)
    return models_dir


# Create persistent model registry instance
model_registry = create_persistent_model_registry(
    models_dir=ml_config.models_storage_path
)


# Export important components
__all__ = [
    "ml_config",
    "model_registry", 
    "MLConfig",
    "SmartFeatureDetector",
    "DynamicConfigFactory",
    "analyze_and_configure",
    "ensure_models_directory"
]