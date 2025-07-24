# File: backend/app/ml/preprocessing/data_processor.py
# Fixed version - no deprecated pandas methods

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging

# Technical analysis library - with safe imports
import ta
from ta.utils import dropna

# Safe imports for specific indicators
try:
    from ta.volatility import BollingerBands
    from ta.trend import MACD, EMAIndicator, SMAIndicator
    from ta.momentum import RSIIndicator, StochasticOscillator
except ImportError as e:
    logging.warning(f"Some TA indicators not available: {e}")

# Scikit-learn preprocessing
from sklearn.preprocessing import MinMaxScaler, StandardScaler, RobustScaler
from sklearn.impute import SimpleImputer

logger = logging.getLogger(__name__)


class CryptoPriceDataProcessor:
    """
    Comprehensive data preprocessing pipeline for cryptocurrency price data
    
    This class handles:
    - Data cleaning and validation
    - Feature engineering with technical indicators
    - Data scaling and normalization  
    - Missing value handling
    - Data quality checks
    - Train/validation/test splitting
    """
    
    def __init__(
        self,
        scaling_method: str = "minmax",        # minmax, standard, robust
        handle_missing: str = "interpolate",   # drop, interpolate, forward_fill
        add_technical_indicators: bool = True,
        add_time_features: bool = True,
        add_price_features: bool = True,
        outlier_threshold: float = 4.0,        # Standard deviations for outlier detection
        min_data_points: int = 50             # Minimum data points required
    ):
        """Initialize data processor"""
        self.scaling_method = scaling_method
        self.handle_missing = handle_missing
        self.add_technical_indicators = add_technical_indicators
        self.add_time_features = add_time_features
        self.add_price_features = add_price_features
        self.outlier_threshold = outlier_threshold
        self.min_data_points = min_data_points
        
        # Initialize scalers
        self.scaler = self._get_scaler()
        self.feature_scalers = {}
        
        # Track feature names
        self.feature_names = []
        self.original_columns = []
        
        logger.info(f"Initialized CryptoPriceDataProcessor with {scaling_method} scaling")
    
    def _get_scaler(self):
        """Get appropriate scaler based on scaling method"""
        if self.scaling_method == "minmax":
            return MinMaxScaler(feature_range=(0, 1))
        elif self.scaling_method == "standard":
            return StandardScaler()
        elif self.scaling_method == "robust":
            return RobustScaler()
        else:
            raise ValueError(f"Unknown scaling method: {self.scaling_method}")
    
    def process_data(
        self,
        data: pd.DataFrame,
        target_column: str = "close_price",
        timestamp_column: str = "timestamp"
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Complete data processing pipeline"""
        logger.info(f"Starting data processing for {len(data)} records")
        
        # Store original info
        original_shape = data.shape
        self.original_columns = data.columns.tolist()
        
        # Processing steps
        processing_info = {
            'original_shape': original_shape,
            'processing_steps': [],
            'feature_engineering': {},
            'data_quality': {}
        }
        
        # 1. Data validation and cleaning
        data_clean = self._validate_and_clean_data(data, timestamp_column, target_column)
        processing_info['processing_steps'].append('data_validation_cleaning')
        processing_info['data_quality']['after_cleaning'] = data_clean.shape
        
        # 2. Handle missing values
        data_clean = self._handle_missing_values(data_clean)
        processing_info['processing_steps'].append('missing_value_handling')
        processing_info['data_quality']['after_missing_handling'] = data_clean.shape
        
        # 3. Add time-based features
        if self.add_time_features:
            data_clean = self._add_time_features(data_clean, timestamp_column)
            processing_info['processing_steps'].append('time_features')
            processing_info['feature_engineering']['time_features'] = True
        
        # 4. Add price-based features
        if self.add_price_features:
            data_clean = self._add_price_features(data_clean)
            processing_info['processing_steps'].append('price_features')
            processing_info['feature_engineering']['price_features'] = True
        
        # 5. Add technical indicators
        if self.add_technical_indicators:
            data_clean = self._add_technical_indicators(data_clean)
            processing_info['processing_steps'].append('technical_indicators')
            processing_info['feature_engineering']['technical_indicators'] = True
        
        # 6. Remove outliers
        data_clean = self._remove_outliers(data_clean, target_column)
        processing_info['processing_steps'].append('outlier_removal')
        processing_info['data_quality']['after_outlier_removal'] = data_clean.shape
        
        # 7. Final data quality check
        self._final_quality_check(data_clean)
        processing_info['processing_steps'].append('final_quality_check')
        processing_info['data_quality']['final_shape'] = data_clean.shape
        
        # Store feature names
        self.feature_names = [col for col in data_clean.columns if col != target_column and col != timestamp_column]
        processing_info['feature_names'] = self.feature_names
        processing_info['total_features'] = len(self.feature_names)
        
        logger.info(f"Data processing completed: {original_shape} → {data_clean.shape}")
        return data_clean, processing_info
    
    def _validate_and_clean_data(
        self,
        data: pd.DataFrame,
        timestamp_column: str,
        target_column: str
    ) -> pd.DataFrame:
        """Validate and clean input data"""
        data = data.copy()
        
        # Check required columns
        required_columns = [timestamp_column, target_column]
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Convert timestamp column
        if data[timestamp_column].dtype == 'object':
            data[timestamp_column] = pd.to_datetime(data[timestamp_column])
        
        # Sort by timestamp
        data = data.sort_values(timestamp_column).reset_index(drop=True)
        
        # Remove duplicates based on timestamp
        before_dedup = len(data)
        data = data.drop_duplicates(subset=[timestamp_column], keep='last')
        after_dedup = len(data)
        
        if before_dedup != after_dedup:
            logger.warning(f"Removed {before_dedup - after_dedup} duplicate timestamps")
        
        # Ensure numeric columns are properly typed
        numeric_columns = ['open_price', 'high_price', 'low_price', 'close_price', 'volume']
        for col in numeric_columns:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
        
        # Check minimum data points
        if len(data) < max(self.min_data_points, 30):
            raise ValueError(f"Insufficient data points: {len(data)} < {self.min_data_points}")
        
        return data
    
    def _handle_missing_values(self, data: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values - FIXED: No deprecated methods"""
        data = data.copy()
        
        if self.handle_missing == "drop":
            # Drop rows with any missing values
            before_drop = len(data)
            data = data.dropna()
            after_drop = len(data)
            logger.info(f"Dropped {before_drop - after_drop} rows with missing values")
            
        elif self.handle_missing == "interpolate":
            # Interpolate missing values
            numeric_columns = data.select_dtypes(include=[np.number]).columns
            data[numeric_columns] = data[numeric_columns].interpolate(method='linear')
            
            # Forward fill any remaining missing values - FIXED
            data[numeric_columns] = data[numeric_columns].ffill()
            
            # Backward fill any remaining missing values at the beginning - FIXED
            data[numeric_columns] = data[numeric_columns].bfill()
            
        elif self.handle_missing == "forward_fill":
            # Forward fill missing values - FIXED
            numeric_columns = data.select_dtypes(include=[np.number]).columns
            data[numeric_columns] = data[numeric_columns].ffill()
            data[numeric_columns] = data[numeric_columns].bfill()
        
        return data
    
    def _add_time_features(self, data: pd.DataFrame, timestamp_column: str) -> pd.DataFrame:
        """Add time-based features"""
        data = data.copy()
        
        # Extract time components
        data['hour'] = data[timestamp_column].dt.hour
        data['day_of_week'] = data[timestamp_column].dt.dayofweek
        data['day_of_month'] = data[timestamp_column].dt.day
        data['month'] = data[timestamp_column].dt.month
        data['quarter'] = data[timestamp_column].dt.quarter
        
        # Cyclical features (important for neural networks)
        data['hour_sin'] = np.sin(2 * np.pi * data['hour'] / 24)
        data['hour_cos'] = np.cos(2 * np.pi * data['hour'] / 24)
        data['day_sin'] = np.sin(2 * np.pi * data['day_of_week'] / 7)
        data['day_cos'] = np.cos(2 * np.pi * data['day_of_week'] / 7)
        data['month_sin'] = np.sin(2 * np.pi * data['month'] / 12)
        data['month_cos'] = np.cos(2 * np.pi * data['month'] / 12)
        
        return data
    
    def _add_price_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add price-based features"""
        data = data.copy()
        
        # Price returns
        data['returns_1h'] = data['close_price'].pct_change(1)
        data['returns_4h'] = data['close_price'].pct_change(4)  
        data['returns_24h'] = data['close_price'].pct_change(24)
        data['returns_7d'] = data['close_price'].pct_change(168)  # 7 days * 24 hours
        
        # Rolling statistics
        data['volatility_24h'] = data['returns_1h'].rolling(24).std()
        data['volatility_7d'] = data['returns_1h'].rolling(168).std()
        
        # Price range indicators
        data['hl_ratio'] = data['high_price'] / data['low_price']
        data['oc_ratio'] = data['open_price'] / data['close_price']
        data['true_range'] = np.maximum(
            data['high_price'] - data['low_price'],
            np.maximum(
                abs(data['high_price'] - data['close_price'].shift(1)),
                abs(data['low_price'] - data['close_price'].shift(1))
            )
        )
        
        # Volume-weighted average price (VWAP)
        data['vwap'] = (data['close_price'] * data['volume']).rolling(24).sum() / data['volume'].rolling(24).sum()
        
        # Volume features
        data['volume_sma'] = data['volume'].rolling(20).mean()
        data['volume_ratio'] = data['volume'] / data['volume_sma']
        
        return data
    
    def _add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators using TA library"""
        data = data.copy()
        
        try:
            # Moving averages
            data['sma_20'] = data['close_price'].rolling(20).mean()
            data['sma_50'] = data['close_price'].rolling(50).mean()
            data['ema_12'] = data['close_price'].ewm(span=12).mean()
            data['ema_26'] = data['close_price'].ewm(span=26).mean()
            
            # RSI
            try:
                rsi = RSIIndicator(close=data['close_price'], window=14)
                data['rsi'] = rsi.rsi()
            except Exception:
                data['rsi'] = ta.momentum.rsi(data['close_price'], window=14)
            
            # MACD
            try:
                macd = MACD(close=data['close_price'], window_slow=26, window_fast=12, window_sign=9)
                data['macd'] = macd.macd()
                data['macd_signal'] = macd.macd_signal()
                data['macd_histogram'] = macd.macd_diff()
            except Exception:
                data['macd'] = ta.trend.macd(data['close_price'])
                data['macd_signal'] = ta.trend.macd_signal(data['close_price'])
            
            # Bollinger Bands
            try:
                bb = BollingerBands(close=data['close_price'], window=20, window_dev=2)
                data['bollinger_upper'] = bb.bollinger_hband()
                data['bollinger_lower'] = bb.bollinger_lband()
                data['bollinger_middle'] = bb.bollinger_mavg()
                data['bollinger_position'] = (data['close_price'] - data['bollinger_lower']) / (data['bollinger_upper'] - data['bollinger_lower'])
            except Exception:
                pass
            
            # Additional TA indicators
            data['volume_sma_ta'] = ta.volume.volume_sma(data['close_price'], data['volume'], window=20)
            
            # Support and resistance levels (simplified)
            data['support_20'] = data['low_price'].rolling(20).min()
            data['resistance_20'] = data['high_price'].rolling(20).max()
            data['support_distance'] = data['close_price'] - data['support_20']
            data['resistance_distance'] = data['resistance_20'] - data['close_price']
            
            # Momentum indicators
            data['momentum_10'] = data['close_price'] / data['close_price'].shift(10)
            data['momentum_20'] = data['close_price'] / data['close_price'].shift(20)
            
        except Exception as e:
            logger.warning(f"Some technical indicators failed: {e}")
        
        return data
    
    def _remove_outliers(self, data: pd.DataFrame, target_column: str) -> pd.DataFrame:
        """Remove outliers using IQR method"""
        data = data.copy()
        
        # Calculate IQR for target column
        Q1 = data[target_column].quantile(0.25)
        Q3 = data[target_column].quantile(0.75)
        IQR = Q3 - Q1
        
        # Define outlier bounds
        lower_bound = Q1 - self.outlier_threshold * IQR
        upper_bound = Q3 + self.outlier_threshold * IQR
        
        # Filter outliers
        before_filter = len(data)
        data = data[(data[target_column] >= lower_bound) & (data[target_column] <= upper_bound)]
        after_filter = len(data)
        
        if before_filter != after_filter:
            logger.info(f"Removed {before_filter - after_filter} outliers from {target_column}")
        
        return data
    
    def _final_quality_check(self, data: pd.DataFrame) -> None:
        """Final data quality check - FIXED: No deprecated methods"""
        # Handle infinite values
        inf_counts = {}
        for col in data.select_dtypes(include=[np.number]).columns:
            inf_count = np.isinf(data[col]).sum()
            if inf_count > 0:
                inf_counts[col] = inf_count
                # Replace infinite values with NaN then interpolate
                data[col] = data[col].replace([np.inf, -np.inf], np.nan)
                data[col] = data[col].interpolate()
        
        if inf_counts:
            logger.warning(f"Found and handled infinite values: {inf_counts}")
        
        # Check for remaining NaN values
        nan_counts = data.isnull().sum()
        nan_columns = nan_counts[nan_counts > 0]
        
        if not nan_columns.empty:
            logger.warning(f"Remaining NaN values: {nan_columns.to_dict()}")
            # Forward fill remaining NaN values - FIXED
            data.ffill(inplace=True)
            data.bfill(inplace=True)
        
        # Final check for data sufficiency
        if len(data) < max(self.min_data_points, 30):
            raise ValueError(f"After processing, insufficient data points: {len(data)} < {self.min_data_points}")
        
        logger.info("Data quality check completed")