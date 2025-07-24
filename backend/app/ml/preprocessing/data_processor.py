# File: backend/app/ml/preprocessing/data_processor.py
# Fixed version with compatible TA library usage

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
        """
        Initialize data processor
        """
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
        """
        Complete data processing pipeline
        
        Args:
            data: Raw price data DataFrame
            target_column: Name of target column for prediction
            timestamp_column: Name of timestamp column
            
        Returns:
            Tuple of (processed_data, processing_info)
        """
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
        if len(data) < max(self.min_data_points, 30):  # More flexible minimum
            raise ValueError(f"Insufficient data points: {len(data)} < {self.min_data_points}")
        
        return data
    
    def _handle_missing_values(self, data: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values based on strategy"""
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
            
            # Forward fill any remaining missing values
            data[numeric_columns] = data[numeric_columns].fillna(method='ffill')
            
            # Backward fill any remaining missing values at the beginning
            data[numeric_columns] = data[numeric_columns].fillna(method='bfill')
            
        elif self.handle_missing == "forward_fill":
            # Forward fill missing values
            numeric_columns = data.select_dtypes(include=[np.number]).columns
            data[numeric_columns] = data[numeric_columns].fillna(method='ffill')
            data[numeric_columns] = data[numeric_columns].fillna(method='bfill')
        
        return data
    
    def _add_time_features(self, data: pd.DataFrame, timestamp_column: str) -> pd.DataFrame:
        """Add time-based features"""
        data = data.copy()
        
        # Extract time components
        data['hour'] = data[timestamp_column].dt.hour
        data['day_of_week'] = data[timestamp_column].dt.dayofweek  # 0=Monday, 6=Sunday
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
        
        # Market session indicators (assuming UTC timestamps)
        data['asian_session'] = ((data['hour'] >= 0) & (data['hour'] < 9)).astype(int)
        data['european_session'] = ((data['hour'] >= 8) & (data['hour'] < 17)).astype(int)
        data['american_session'] = ((data['hour'] >= 13) & (data['hour'] < 22)).astype(int)
        
        # Weekend indicator
        data['is_weekend'] = (data['day_of_week'] >= 5).astype(int)
        
        logger.info("Added time-based features")
        return data
    
    def _add_price_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add price-based features"""
        data = data.copy()
        
        # Price returns (percentage change)
        if 'close_price' in data.columns:
            data['returns_1h'] = data['close_price'].pct_change(1)
            data['returns_4h'] = data['close_price'].pct_change(4)  
            data['returns_24h'] = data['close_price'].pct_change(24)
            data['returns_7d'] = data['close_price'].pct_change(168)  # 7 days * 24 hours
        
        # Price volatility (rolling standard deviation of returns)
        if 'returns_1h' in data.columns:
            data['volatility_24h'] = data['returns_1h'].rolling(window=24).std()
            data['volatility_7d'] = data['returns_1h'].rolling(window=168).std()
        
        # Price ranges
        if all(col in data.columns for col in ['high_price', 'low_price', 'close_price']):
            data['price_range'] = data['high_price'] - data['low_price']
            data['price_range_pct'] = data['price_range'] / data['close_price']
            
            # True Range (for volatility measurement)
            data['true_range'] = np.maximum(
                data['high_price'] - data['low_price'],
                np.maximum(
                    abs(data['high_price'] - data['close_price'].shift(1)),
                    abs(data['low_price'] - data['close_price'].shift(1))
                )
            )
        
        # Price position within range
        if all(col in data.columns for col in ['high_price', 'low_price', 'close_price']):
            data['price_position'] = (data['close_price'] - data['low_price']) / (data['high_price'] - data['low_price'])
            data['price_position'] = data['price_position'].fillna(0)  # Handle division by zero
        
        # Volume-weighted features
        if all(col in data.columns for col in ['close_price', 'volume']):
            data['vwap'] = (data['close_price'] * data['volume']).rolling(window=24).sum() / data['volume'].rolling(window=24).sum()
            data['volume_sma'] = data['volume'].rolling(window=24).mean()
            data['volume_ratio'] = data['volume'] / data['volume_sma']
        
        logger.info("Added price-based features")
        return data
    
    def _add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add technical analysis indicators with safe imports"""
        data = data.copy()
        
        # Ensure we have required columns
        required_cols = ['high_price', 'low_price', 'close_price', 'volume']
        if not all(col in data.columns for col in required_cols):
            logger.warning("Missing columns for technical indicators")
            return data
        
        try:
            # Use TA library's comprehensive feature addition
            # This is more reliable than individual indicators
            
            # Prepare data for TA library (rename columns)
            ta_data = data.rename(columns={
                'high_price': 'high',
                'low_price': 'low', 
                'close_price': 'close',
                'volume': 'volume',
                'open_price': 'open'
            })
            
            # Add basic open price if not available
            if 'open' not in ta_data.columns:
                ta_data['open'] = ta_data['close'].shift(1).fillna(ta_data['close'])
            
            # Add all technical analysis features at once
            ta_features = ta.add_all_ta_features(
                ta_data, 
                open="open", 
                high="high", 
                low="low", 
                close="close", 
                volume="volume",
                fillna=True  # Fill NaN values
            )
            
            # Select and rename key indicators
            indicator_mapping = {
                # Moving Averages
                'trend_sma_fast': 'sma_5',
                'trend_sma_slow': 'sma_20',
                'trend_ema_fast': 'ema_12', 
                'trend_ema_slow': 'ema_26',
                
                # Momentum indicators
                'momentum_rsi': 'rsi',
                'momentum_stoch': 'stoch_k',
                'momentum_stoch_signal': 'stoch_d',
                
                # Trend indicators  
                'trend_macd': 'macd',
                'trend_macd_signal': 'macd_signal',
                'trend_macd_diff': 'macd_histogram',
                
                # Volatility indicators
                'volatility_bbh': 'bollinger_upper',
                'volatility_bbl': 'bollinger_lower', 
                'volatility_bbm': 'bollinger_middle',
                'volatility_atr': 'atr',
                
                # Volume indicators
                'volume_sma': 'volume_sma_ta'
            }
            
            # Copy indicators that exist
            for ta_name, our_name in indicator_mapping.items():
                if ta_name in ta_features.columns:
                    data[our_name] = ta_features[ta_name]
            
            # Manual calculations for missing indicators
            
            # Simple Moving Averages (manual backup)
            if 'sma_5' not in data.columns:
                data['sma_5'] = data['close_price'].rolling(window=5).mean()
            if 'sma_20' not in data.columns:
                data['sma_20'] = data['close_price'].rolling(window=20).mean()
            if 'sma_50' not in data.columns:
                data['sma_50'] = data['close_price'].rolling(window=50).mean()
                
            # Exponential Moving Averages (manual backup)
            if 'ema_12' not in data.columns:
                data['ema_12'] = data['close_price'].ewm(span=12).mean()
            if 'ema_26' not in data.columns:
                data['ema_26'] = data['close_price'].ewm(span=26).mean()
                
            # RSI (manual calculation if needed)
            if 'rsi' not in data.columns:
                delta = data['close_price'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                data['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD (manual calculation if needed)
            if 'macd' not in data.columns:
                exp1 = data['close_price'].ewm(span=12).mean()
                exp2 = data['close_price'].ewm(span=26).mean()
                data['macd'] = exp1 - exp2
                data['macd_signal'] = data['macd'].ewm(span=9).mean()
                data['macd_histogram'] = data['macd'] - data['macd_signal']
            
            # Bollinger Bands (manual calculation if needed)
            if 'bollinger_upper' not in data.columns:
                sma20 = data['close_price'].rolling(window=20).mean()
                std20 = data['close_price'].rolling(window=20).std()
                data['bollinger_upper'] = sma20 + (std20 * 2)
                data['bollinger_lower'] = sma20 - (std20 * 2)
                data['bollinger_middle'] = sma20
            
            # Volume SMA (manual - this was causing the warning)
            data['volume_sma'] = data['volume'].rolling(window=20).mean()
            data['volume_ratio'] = data['volume'] / data['volume_sma']
            
            # Additional derived features
            if 'bollinger_upper' in data.columns and 'bollinger_lower' in data.columns:
                data['bollinger_width'] = data['bollinger_upper'] - data['bollinger_lower']
                data['bollinger_position'] = (data['close_price'] - data['bollinger_lower']) / data['bollinger_width']
            
            # Support and Resistance levels
            data['support_20'] = data['low_price'].rolling(window=20).min()
            data['resistance_20'] = data['high_price'].rolling(window=20).max()
            data['support_distance'] = (data['close_price'] - data['support_20']) / data['close_price']
            data['resistance_distance'] = (data['resistance_20'] - data['close_price']) / data['close_price']
            
            # Price momentum
            data['momentum_10'] = data['close_price'] / data['close_price'].shift(10) - 1
            data['momentum_20'] = data['close_price'] / data['close_price'].shift(20) - 1
            
            logger.info("Added technical indicators successfully")
            
        except Exception as e:
            logger.error(f"Error adding technical indicators: {str(e)}")
            logger.info("Falling back to basic technical indicators")
            
            # Fallback to basic indicators if TA library fails
            data['sma_20'] = data['close_price'].rolling(window=20).mean()
            data['ema_12'] = data['close_price'].ewm(span=12).mean()
            data['rsi'] = self._calculate_rsi(data['close_price'])
            data['volume_sma'] = data['volume'].rolling(window=20).mean()
            
        return data
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Manual RSI calculation"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _remove_outliers(self, data: pd.DataFrame, target_column: str) -> pd.DataFrame:
        """Remove outliers using statistical methods"""
        data = data.copy()
        original_length = len(data)
        
        # Z-score method for outlier detection
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            if col in data.columns:
                # Calculate Z-scores
                z_scores = np.abs((data[col] - data[col].mean()) / data[col].std())
                
                # Remove outliers beyond threshold
                outlier_mask = z_scores > self.outlier_threshold
                outlier_count = outlier_mask.sum()
                
                if outlier_count > 0:
                    # Don't remove more than 5% of data as outliers
                    max_outliers = int(0.05 * len(data))
                    if outlier_count > max_outliers:
                        # Keep only the most extreme outliers
                        outlier_indices = z_scores.nlargest(max_outliers).index
                        outlier_mask = pd.Series(False, index=data.index)
                        outlier_mask.loc[outlier_indices] = True
                    
                    data = data[~outlier_mask]
        
        removed_count = original_length - len(data)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} outliers ({removed_count/original_length*100:.2f}%)")
        
        return data
    
    def _final_quality_check(self, data: pd.DataFrame) -> None:
        """Perform final data quality checks"""
        # Check for infinite values
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        inf_counts = {}
        
        for col in numeric_columns:
            inf_count = np.isinf(data[col]).sum()
            if inf_count > 0:
                inf_counts[col] = inf_count
                # Replace inf with NaN, then interpolate
                data[col] = data[col].replace([np.inf, -np.inf], np.nan)
                data[col] = data[col].interpolate()
        
        if inf_counts:
            logger.warning(f"Found and handled infinite values: {inf_counts}")
        
        # Check for remaining NaN values
        nan_counts = data.isnull().sum()
        nan_columns = nan_counts[nan_counts > 0]
        
        if not nan_columns.empty:
            logger.warning(f"Remaining NaN values: {nan_columns.to_dict()}")
            # Forward fill remaining NaN values
            data.fillna(method='ffill', inplace=True)
            data.fillna(method='bfill', inplace=True)
        
        # Final check for data sufficiency
        if len(data) < max(self.min_data_points, 30):  # More flexible minimum
            raise ValueError(f"After processing, insufficient data points: {len(data)} < {self.min_data_points}")
        
        logger.info("Data quality check completed")
    
    def scale_features(
        self,
        data: pd.DataFrame,
        target_column: str = "close_price",
        fit_scalers: bool = True
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Scale features for ML model input"""
        data_scaled = data.copy()
        
        # Separate features and target
        feature_columns = [col for col in data.columns if col not in [target_column, 'timestamp']]
        
        scaling_info = {
            'feature_columns': feature_columns,
            'scaling_method': self.scaling_method,
            'scaled_features': len(feature_columns)
        }
        
        if fit_scalers:
            # Fit and transform features
            if feature_columns:
                self.scaler.fit(data[feature_columns])
                data_scaled[feature_columns] = self.scaler.transform(data[feature_columns])
                scaling_info['scaler_fitted'] = True
            else:
                logger.warning("No feature columns found for scaling")
                scaling_info['scaler_fitted'] = False
        else:
            # Transform using fitted scalers
            if hasattr(self.scaler, 'scale_') and feature_columns:
                data_scaled[feature_columns] = self.scaler.transform(data[feature_columns])
                scaling_info['scaler_fitted'] = False
            else:
                raise ValueError("Scalers not fitted. Call with fit_scalers=True first.")
        
        logger.info(f"Scaled {len(feature_columns)} features using {self.scaling_method} scaling")
        return data_scaled, scaling_info
    
    def split_data(
        self,
        data: pd.DataFrame,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        time_based: bool = True
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """Split data into train/validation/test sets"""
        # Validate ratios
        total_ratio = train_ratio + val_ratio + test_ratio
        if abs(total_ratio - 1.0) > 1e-6:
            raise ValueError(f"Ratios must sum to 1.0, got {total_ratio}")
        
        n_total = len(data)
        n_train = int(n_total * train_ratio)
        n_val = int(n_total * val_ratio)
        
        if time_based:
            # Time-based split (important for time series)
            train_data = data.iloc[:n_train].copy()
            val_data = data.iloc[n_train:n_train + n_val].copy()
            test_data = data.iloc[n_train + n_val:].copy()
        else:
            # Random split
            data_shuffled = data.sample(frac=1, random_state=42).reset_index(drop=True)
            train_data = data_shuffled.iloc[:n_train].copy()
            val_data = data_shuffled.iloc[n_train:n_train + n_val].copy()
            test_data = data_shuffled.iloc[n_train + n_val:].copy()
        
        split_info = {
            'total_samples': n_total,
            'train_samples': len(train_data),
            'val_samples': len(val_data),
            'test_samples': len(test_data),
            'train_ratio_actual': len(train_data) / n_total,
            'val_ratio_actual': len(val_data) / n_total,
            'test_ratio_actual': len(test_data) / n_total,
            'split_method': 'time_based' if time_based else 'random'
        }
        
        logger.info(f"Data split: {len(train_data)} train, {len(val_data)} val, {len(test_data)} test")
        return train_data, val_data, test_data, split_info