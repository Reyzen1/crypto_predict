# File: backend/app/ml/utils/model_utils.py
# Utility functions for ML model operations

from scipy import stats
from datetime import datetime
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, timedelta
import logging
import os
import json

# ML libraries
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib

logger = logging.getLogger(__name__)


class ModelMetrics:
    """
    Utility class for calculating model performance metrics
    
    This class provides comprehensive metrics for evaluating
    cryptocurrency price prediction models.
    """
    
    @staticmethod
    def calculate_regression_metrics(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        price_mean: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Calculate regression metrics for price predictions
        
        Args:
            y_true: True values
            y_pred: Predicted values
            price_mean: Mean price for normalized metrics
            
        Returns:
            Dictionary of regression metrics
        """
        # Basic regression metrics
        mse = mean_squared_error(y_true, y_pred)
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_true, y_pred)
        
        # Percentage metrics
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        smape = np.mean(2 * np.abs(y_true - y_pred) / (np.abs(y_true) + np.abs(y_pred))) * 100
        
        # Normalized metrics
        metrics = {
            'mse': float(mse),
            'mae': float(mae),
            'rmse': float(rmse),
            'r2_score': float(r2),
            'mape': float(mape),
            'smape': float(smape)
        }
        
        # Add normalized RMSE if price mean is provided
        if price_mean and price_mean > 0:
            metrics['nrmse'] = float(rmse / price_mean)
        
        return metrics
    
    @staticmethod
    def calculate_directional_accuracy(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        threshold: float = 0.0
    ) -> Dict[str, float]:
        """
        Calculate directional accuracy metrics
        
        Args:
            y_true: True values
            y_pred: Predicted values
            threshold: Threshold for direction change
            
        Returns:
            Dictionary of directional accuracy metrics
        """
        # Calculate actual and predicted changes
        true_changes = np.diff(y_true)
        pred_changes = np.diff(y_pred)
        
        # Direction indicators
        true_directions = (true_changes > threshold).astype(int)
        pred_directions = (pred_changes > threshold).astype(int)
        
        # Overall directional accuracy
        directional_accuracy = np.mean(true_directions == pred_directions)
        
        # Up movement accuracy
        up_mask = true_directions == 1
        up_accuracy = np.mean(pred_directions[up_mask] == 1) if np.any(up_mask) else 0.0
        
        # Down movement accuracy
        down_mask = true_directions == 0
        down_accuracy = np.mean(pred_directions[down_mask] == 0) if np.any(down_mask) else 0.0
        
        return {
            'directional_accuracy': float(directional_accuracy),
            'up_accuracy': float(up_accuracy),
            'down_accuracy': float(down_accuracy),
            'up_predictions': int(np.sum(pred_directions)),
            'down_predictions': int(len(pred_directions) - np.sum(pred_directions))
        }
    
    @staticmethod
    def calculate_trading_metrics(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        threshold: float = 0.01
    ) -> Dict[str, float]:
        """
        Calculate trading-related performance metrics
        
        Args:
            y_true: True price values
            y_pred: Predicted price values
            threshold: Minimum movement threshold for trading signals
            
        Returns:
            Dictionary of trading metrics
        """
        # Calculate returns
        true_returns = np.diff(y_true) / y_true[:-1]
        pred_returns = np.diff(y_pred) / y_pred[:-1]
        
        # Generate trading signals based on predictions
        buy_signals = pred_returns > threshold
        sell_signals = pred_returns < -threshold
        
        # Calculate strategy returns
        strategy_returns = np.where(buy_signals, true_returns, 
                                  np.where(sell_signals, -true_returns, 0))
        
        # Trading metrics
        total_return = np.sum(strategy_returns)
        win_rate = np.mean(strategy_returns > 0) if len(strategy_returns) > 0 else 0
        avg_win = np.mean(strategy_returns[strategy_returns > 0]) if np.any(strategy_returns > 0) else 0
        avg_loss = np.mean(strategy_returns[strategy_returns < 0]) if np.any(strategy_returns < 0) else 0
        
        # Sharpe ratio (simplified, assuming daily returns)
        sharpe_ratio = np.mean(strategy_returns) / np.std(strategy_returns) if np.std(strategy_returns) > 0 else 0
        
        return {
            'total_return': float(total_return),
            'win_rate': float(win_rate),
            'avg_win': float(avg_win),
            'avg_loss': float(avg_loss),
            'sharpe_ratio': float(sharpe_ratio),
            'num_trades': int(np.sum(buy_signals | sell_signals))
        }
    
    @staticmethod
    def get_comprehensive_metrics(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        timestamps: Optional[pd.DatetimeIndex] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive model evaluation metrics
        
        Args:
            y_true: True values
            y_pred: Predicted values
            timestamps: Timestamps for time-based analysis
            
        Returns:
            Dictionary of all metrics
        """
        price_mean = np.mean(y_true)
        
        metrics = {
            'regression_metrics': ModelMetrics.calculate_regression_metrics(y_true, y_pred, price_mean),
            'directional_metrics': ModelMetrics.calculate_directional_accuracy(y_true, y_pred),
            'trading_metrics': ModelMetrics.calculate_trading_metrics(y_true, y_pred),
            'evaluation_timestamp': datetime.utcnow().isoformat(),
            'sample_size': len(y_true)
        }
        
        # Add time-based analysis if timestamps provided
        if timestamps is not None and len(timestamps) == len(y_true):
            time_metrics = ModelMetrics.calculate_time_based_metrics(y_true, y_pred, timestamps)
            metrics['time_metrics'] = time_metrics
        
        return metrics
    
    @staticmethod
    def calculate_time_based_metrics(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        timestamps: pd.DatetimeIndex
    ) -> Dict[str, Any]:
        """
        Calculate time-based performance metrics
        
        Args:
            y_true: True values
            y_pred: Predicted values
            timestamps: Timestamps for each prediction
            
        Returns:
            Dictionary of time-based metrics
        """
        df = pd.DataFrame({
            'true': y_true,
            'pred': y_pred,
            'timestamp': timestamps
        })
        
        df['error'] = np.abs(df['true'] - df['pred'])
        df['squared_error'] = (df['true'] - df['pred']) ** 2
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        # Hourly performance
        hourly_metrics = df.groupby('hour')['error'].agg(['mean', 'std']).to_dict()
        
        # Daily performance
        daily_metrics = df.groupby('day_of_week')['error'].agg(['mean', 'std']).to_dict()
        
        # Recent vs older performance
        recent_mask = df['timestamp'] > (df['timestamp'].max() - timedelta(days=7))
        recent_performance = df[recent_mask]['error'].mean()
        older_performance = df[~recent_mask]['error'].mean()
        
        return {
            'hourly_performance': hourly_metrics,
            'daily_performance': daily_metrics,
            'recent_mae': float(recent_performance),
            'older_mae': float(older_performance),
            'performance_trend': float(recent_performance - older_performance)
        }


class DataValidator:
    """
    Utility class for validating data quality
    
    This class provides methods to validate data quality
    for ML model training and prediction.
    """
    
    @staticmethod
    def validate_price_data(
        data: pd.DataFrame,
        required_columns: List[str] = None,
        min_samples: int = 100
    ) -> Tuple[bool, List[str]]:
        """
        Validate cryptocurrency price data
        
        Args:
            data: DataFrame to validate
            required_columns: List of required columns
            min_samples: Minimum number of samples required
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Default required columns
        if required_columns is None:
            required_columns = ['timestamp', 'close_price', 'volume']
        
        # Check if DataFrame is empty
        if data is None or (hasattr(data, 'empty') and data.empty) or (isinstance(data, np.ndarray) and data.size == 0):
            issues.append("DataFrame is empty")
            return False, issues
        
        # Check required columns
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            issues.append(f"Missing required columns: {missing_columns}")
        
        # Check minimum samples
        if len(data) < min_samples:
            issues.append(f"Insufficient samples: {len(data)} < {min_samples}")
        
        # Check for numeric columns
        numeric_columns = ['close_price', 'open_price', 'high_price', 'low_price', 'volume']
        for col in numeric_columns:
            if col in data.columns:
                if not pd.api.types.is_numeric_dtype(data[col]):
                    issues.append(f"Column {col} is not numeric")
                
                # Check for negative prices
                if col.endswith('_price') and (data[col] < 0).any():
                    issues.append(f"Negative values found in {col}")
                
                # Check for zero volumes
                if col == 'volume' and (data[col] == 0).sum() > len(data) * 0.1:
                    issues.append(f"Too many zero volumes in {col}")
        
        # Check timestamp column
        if 'timestamp' in data.columns:
            if not pd.api.types.is_datetime64_any_dtype(data['timestamp']):
                try:
                    pd.to_datetime(data['timestamp'])
                except:
                    issues.append("Timestamp column cannot be converted to datetime")
            
            # Check for time gaps
            if 'timestamp' in data.columns and len(data) > 1:
                time_diffs = data['timestamp'].diff().dropna()
                median_diff = time_diffs.median()
                large_gaps = time_diffs[time_diffs > median_diff * 3]
                if len(large_gaps) > 0:
                    issues.append(f"Found {len(large_gaps)} large time gaps")
        
        # Check for missing values
        missing_ratios = data.isnull().sum() / len(data)
        high_missing = missing_ratios[missing_ratios > 0.1]
        if not high_missing.empty:
            issues.append(f"High missing value ratios: {high_missing.to_dict()}")
        
        # Check for duplicates
        if 'timestamp' in data.columns:
            duplicate_count = data['timestamp'].duplicated().sum()
            if duplicate_count > 0:
                issues.append(f"Found {duplicate_count} duplicate timestamps")
        
        # Check for outliers in prices
        price_columns = [col for col in data.columns if col.endswith('_price')]
        for col in price_columns:
            if col in data.columns:
                q1 = data[col].quantile(0.25)
                q3 = data[col].quantile(0.75)
                iqr = q3 - q1
                outliers = data[(data[col] < q1 - 3*iqr) | (data[col] > q3 + 3*iqr)]
                if len(outliers) > len(data) * 0.05:  # More than 5% outliers
                    issues.append(f"High number of outliers in {col}: {len(outliers)}")
        
        is_valid = len(issues) == 0
        return is_valid, issues
    
    @staticmethod
    def validate_model_input(
        X: np.ndarray,
        y: np.ndarray,
        sequence_length: int
    ) -> Tuple[bool, List[str]]:
        """
        Validate model input data
        
        Args:
            X: Input features array
            y: Target values array
            sequence_length: Expected sequence length
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check array shapes
        if X.ndim != 3:
            issues.append(f"X must be 3D array, got {X.ndim}D")
        elif X.shape[1] != sequence_length:
            issues.append(f"X sequence length {X.shape[1]} != expected {sequence_length}")
        
        if y.ndim != 1:
            issues.append(f"y must be 1D array, got {y.ndim}D")
        
        if len(X) != len(y):
            issues.append(f"X and y length mismatch: {len(X)} != {len(y)}")
        
        # Check for NaN or infinite values
        if np.isnan(X).any():
            issues.append("NaN values found in X")
        
        if np.isnan(y).any():
            issues.append("NaN values found in y")
        
        if np.isinf(X).any():
            issues.append("Infinite values found in X")
        
        if np.isinf(y).any():
            issues.append("Infinite values found in y")
        
        # Check data ranges
        if np.any(y <= 0):
            issues.append("Non-positive values found in target prices")
        
        is_valid = len(issues) == 0
        return is_valid, issues


class ModelPersistence:
    """
    Utility class for saving and loading models
    
    This class provides standardized methods for model persistence
    including metadata and versioning.
    """
    
    @staticmethod
    def save_model_with_metadata(
        model,
        model_path: str,
        metadata: Dict[str, Any],
        scalers: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Save model with complete metadata
        
        Args:
            model: Trained model object
            model_path: Path to save model
            metadata: Model metadata dictionary
            scalers: Data scalers dictionary
            config: Model configuration dictionary
            
        Returns:
            Dictionary of saved file paths
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # Save main model
        if hasattr(model, 'save'):
            # Keras model
            model.save(model_path)
        else:
            # Scikit-learn model
            joblib.dump(model, model_path)
        
        saved_paths = {'model': model_path}
        
        # Save metadata
        metadata_path = model_path.replace('.h5', '_metadata.json').replace('.pkl', '_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        saved_paths['metadata'] = metadata_path
        
        # Save scalers
        if scalers:
            scaler_path = model_path.replace('.h5', '_scalers.pkl').replace('.pkl', '_scalers.pkl')
            joblib.dump(scalers, scaler_path)
            saved_paths['scalers'] = scaler_path
        
        # Save config
        if config:
            config_path = model_path.replace('.h5', '_config.json').replace('.pkl', '_config.json')
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2, default=str)
            saved_paths['config'] = config_path
        
        logger.info(f"Model saved with metadata to {model_path}")
        return saved_paths
    
    @staticmethod
    def load_model_with_metadata(
        model_path: str
    ) -> Tuple[Any, Dict[str, Any], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Load model with complete metadata
        
        Args:
            model_path: Path to saved model
            
        Returns:
            Tuple of (model, metadata, scalers, config)
        """
        # Load main model
        if model_path.endswith('.h5'):
            # Keras model
            from tensorflow.keras.models import load_model
            model = load_model(model_path)
        else:
            # Scikit-learn model
            model = joblib.load(model_path)
        
        # Load metadata
        metadata_path = model_path.replace('.h5', '_metadata.json').replace('.pkl', '_metadata.json')
        metadata = {}
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        
        # Load scalers
        scaler_path = model_path.replace('.h5', '_scalers.pkl').replace('.pkl', '_scalers.pkl')
        scalers = None
        if os.path.exists(scaler_path):
            scalers = joblib.load(scaler_path)
        
        # Load config
        config_path = model_path.replace('.h5', '_config.json').replace('.pkl', '_config.json')
        config = None
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        
        logger.info(f"Model loaded with metadata from {model_path}")
        return model, metadata, scalers, config
    
    @staticmethod
    def create_model_metadata(
        model_type: str,
        crypto_symbol: str,
        training_metrics: Dict[str, float],
        feature_names: List[str],
        training_config: Dict[str, Any],
        data_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create standardized model metadata
        
        Args:
            model_type: Type of model (lstm, etc.)
            crypto_symbol: Cryptocurrency symbol
            training_metrics: Training performance metrics
            feature_names: List of feature names used
            training_config: Training configuration used
            data_info: Information about training data
            
        Returns:
            Standardized metadata dictionary
        """
        metadata = {
            'model_info': {
                'model_type': model_type,
                'crypto_symbol': crypto_symbol,
                'model_version': datetime.utcnow().strftime('%Y%m%d_%H%M%S'),
                'created_at': datetime.utcnow().isoformat(),
                'framework': 'tensorflow' if model_type == 'lstm' else 'sklearn'
            },
            'training_metrics': training_metrics,
            'features': {
                'feature_names': feature_names,
                'feature_count': len(feature_names),
                'feature_engineering': training_config.get('feature_engineering', {})
            },
            'training_config': training_config,
            'data_info': data_info or {},
            'model_status': 'trained',
            'last_updated': datetime.utcnow().isoformat()
        }
        
        return metadata


class FeatureImportance:
    """
    Utility class for feature importance analysis
    
    This class provides methods to analyze and visualize
    feature importance for ML models.
    """
    
    @staticmethod
    def calculate_lstm_feature_importance(
        model,
        X_test: np.ndarray,
        y_test: np.ndarray,
        feature_names: List[str],
        n_permutations: int = 10
    ) -> Dict[str, float]:
        """
        Calculate feature importance for LSTM model using permutation importance
        
        Args:
            model: Trained LSTM model
            X_test: Test features
            y_test: Test targets
            feature_names: Names of features
            n_permutations: Number of permutations for importance calculation
            
        Returns:
            Dictionary of feature importance scores
        """
        # Calculate baseline performance
        baseline_pred = model.predict(X_test, verbose=0)
        baseline_mse = mean_squared_error(y_test, baseline_pred)
        
        importance_scores = {}
        
        for i, feature_name in enumerate(feature_names):
            if i >= X_test.shape[2]:  # Skip if feature index is out of bounds
                continue
                
            mse_scores = []
            
            for _ in range(n_permutations):
                # Create permuted version of test data
                X_permuted = X_test.copy()
                
                # Permute the specific feature across all samples and time steps
                perm_indices = np.random.permutation(X_test.shape[0])
                X_permuted[:, :, i] = X_test[perm_indices, :, i]
                
                # Calculate performance with permuted feature
                permuted_pred = model.predict(X_permuted, verbose=0)
                permuted_mse = mean_squared_error(y_test, permuted_pred)
                mse_scores.append(permuted_mse)
            
            # Importance is the increase in error when feature is permuted
            avg_permuted_mse = np.mean(mse_scores)
            importance = avg_permuted_mse - baseline_mse
            importance_scores[feature_name] = max(0, importance)  # Ensure non-negative
        
        # Normalize importance scores
        max_importance = max(importance_scores.values()) if importance_scores else 1
        if max_importance > 0:
            importance_scores = {k: v / max_importance for k, v in importance_scores.items()}
        
        return importance_scores
    
    @staticmethod
    def get_top_features(
        importance_scores: Dict[str, float],
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Get top K most important features
        
        Args:
            importance_scores: Dictionary of feature importance scores
            top_k: Number of top features to return
            
        Returns:
            List of (feature_name, importance_score) tuples sorted by importance
        """
        sorted_features = sorted(importance_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_features[:top_k]


class ModelComparison:
    """
    Utility class for comparing multiple models
    
    This class provides methods to compare performance
    of different models on the same dataset.
    """
    
    @staticmethod
    def compare_models(
        models_dict: Dict[str, Any],
        X_test: np.ndarray,
        y_test: np.ndarray,
        metrics: List[str] = None
    ) -> pd.DataFrame:
        """
        Compare multiple models on test data
        
        Args:
            models_dict: Dictionary of {model_name: model} pairs
            X_test: Test features
            y_test: Test targets
            metrics: List of metrics to calculate
            
        Returns:
            DataFrame with comparison results
        """
        if metrics is None:
            metrics = ['mse', 'mae', 'rmse', 'r2_score', 'mape']
        
        results = []
        
        for model_name, model in models_dict.items():
            try:
                # Make predictions
                if hasattr(model, 'predict'):
                    y_pred = model.predict(X_test)
                    if len(y_pred.shape) > 1:
                        y_pred = y_pred.flatten()
                else:
                    continue
                
                # Calculate metrics
                model_metrics = ModelMetrics.calculate_regression_metrics(y_test, y_pred)
                
                # Add model name and extract requested metrics
                result = {'model': model_name}
                for metric in metrics:
                    result[metric] = model_metrics.get(metric, np.nan)
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error evaluating model {model_name}: {str(e)}")
                # Add row with NaN values for failed model
                result = {'model': model_name}
                for metric in metrics:
                    result[metric] = np.nan
                results.append(result)
        
        comparison_df = pd.DataFrame(results)
        
        # Sort by R² score (descending) or RMSE (ascending)
        if 'r2_score' in comparison_df.columns:
            comparison_df = comparison_df.sort_values('r2_score', ascending=False)
        elif 'rmse' in comparison_df.columns:
            comparison_df = comparison_df.sort_values('rmse', ascending=True)
        
        return comparison_df.reset_index(drop=True)
    
    @staticmethod
    def statistical_significance_test(
        y_true: np.ndarray,
        predictions_dict: Dict[str, np.ndarray],
        alpha: float = 0.05
    ) -> Dict[str, Dict[str, float]]:
        """
        Test statistical significance of model differences
        
        Args:
            y_true: True values
            predictions_dict: Dictionary of {model_name: predictions}
            alpha: Significance level
            
        Returns:
            Dictionary of p-values for model comparisons
        """
        from scipy import stats
        
        # Calculate squared errors for each model
        errors_dict = {}
        for model_name, y_pred in predictions_dict.items():
            errors_dict[model_name] = (y_true - y_pred) ** 2
        
        # Perform pairwise t-tests
        model_names = list(errors_dict.keys())
        p_values = {}
        
        for i, model1 in enumerate(model_names):
            p_values[model1] = {}
            for j, model2 in enumerate(model_names):
                if i != j:
                    # Paired t-test on squared errors
                    statistic, p_value = stats.ttest_rel(
                        errors_dict[model1],
                        errors_dict[model2]
                    )
                    p_values[model1][model2] = p_value
                else:
                    p_values[model1][model2] = 1.0
        
        return p_values


class PredictionValidator:
    """
    Utility class for validating predictions
    
    This class provides methods to validate and filter
    predictions based on quality criteria.
    """
    
    @staticmethod
    def validate_prediction(
        prediction: float,
        confidence: float,
        current_price: float,
        min_confidence: float = 0.6,
        max_change_ratio: float = 0.5
    ) -> Tuple[bool, List[str]]:
        """
        Validate a single prediction
        
        Args:
            prediction: Predicted price
            confidence: Confidence score
            current_price: Current market price
            min_confidence: Minimum required confidence
            max_change_ratio: Maximum allowed price change ratio
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check if prediction is valid number
        if not np.isfinite(prediction) or prediction <= 0:
            issues.append("Invalid prediction value")
        
        # Check confidence score
        if not (0 <= confidence <= 1):
            issues.append("Invalid confidence score")
        elif confidence < min_confidence:
            issues.append(f"Low confidence: {confidence:.3f} < {min_confidence}")
        
        # Check prediction reasonableness
        if current_price > 0 and prediction > 0:
            change_ratio = abs(prediction - current_price) / current_price
            if change_ratio > max_change_ratio:
                issues.append(f"Unrealistic price change: {change_ratio:.3f} > {max_change_ratio}")
        
        is_valid = len(issues) == 0
        return is_valid, issues
    
    @staticmethod
    def filter_predictions(
        predictions: List[Dict[str, Any]],
        min_confidence: float = 0.6,
        max_age_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Filter predictions based on quality criteria
        
        Args:
            predictions: List of prediction dictionaries
            min_confidence: Minimum confidence threshold
            max_age_hours: Maximum age in hours
            
        Returns:
            List of filtered predictions
        """
        current_time = datetime.utcnow()
        filtered_predictions = []
        
        for pred in predictions:
            # Check confidence
            if pred.get('confidence_score', 0) < min_confidence:
                continue
            
            # Check age
            created_at = pred.get('created_at')
            if created_at:
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                
                age_hours = (current_time - created_at).total_seconds() / 3600
                if age_hours > max_age_hours:
                    continue
            
            # Check validity
            is_valid, _ = PredictionValidator.validate_prediction(
                pred.get('predicted_price', 0),
                pred.get('confidence_score', 0),
                pred.get('input_price', 0),
                min_confidence
            )
            
            if is_valid:
                filtered_predictions.append(pred)
        
        return filtered_predictions


class TimeSeriesUtils:
    """
    Utility class for time series specific operations
    
    This class provides methods for time series analysis
    and feature engineering.
    """
    
    @staticmethod
    def detect_seasonality(
        data: pd.Series,
        periods: List[int] = None
    ) -> Dict[str, float]:
        """
        Detect seasonality patterns in time series data
        
        Args:
            data: Time series data
            periods: List of periods to test for seasonality
            
        Returns:
            Dictionary of seasonality strength for each period
        """
        if periods is None:
            periods = [24, 168, 720]  # Hourly, weekly, monthly patterns
        
        seasonality_scores = {}
        
        for period in periods:
            if len(data) > period * 2:
                # Calculate autocorrelation at the period lag
                autocorr = data.autocorr(lag=period)
                seasonality_scores[f'period_{period}'] = abs(autocorr) if not np.isnan(autocorr) else 0
        
        return seasonality_scores
    
    @staticmethod
    def detect_trend(
        data: pd.Series,
        window: int = 24
    ) -> Dict[str, float]:
        """
        Detect trend in time series data
        
        Args:
            data: Time series data
            window: Window for trend calculation
            
        Returns:
            Dictionary with trend information
        """
        if len(data) < window * 2:
            return {'trend_strength': 0, 'trend_direction': 0}
        
        # Calculate rolling mean
        rolling_mean = data.rolling(window=window).mean()
        
        # Calculate trend using linear regression on rolling mean
        valid_data = rolling_mean.dropna()
        if len(valid_data) < 2:
            return {'trend_strength': 0, 'trend_direction': 0}
        
        x = np.arange(len(valid_data))
        y = valid_data.values
        
        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        return {
            'trend_strength': abs(r_value),
            'trend_direction': np.sign(slope),
            'trend_slope': slope,
            'trend_p_value': p_value
        }
    
    @staticmethod
    def calculate_volatility_regime(
        returns: pd.Series,
        window: int = 24,
        threshold_percentiles: Tuple[float, float] = (33, 67)
    ) -> pd.Series:
        """
        Calculate volatility regime (low, medium, high)
        
        Args:
            returns: Return series
            window: Rolling window for volatility calculation
            threshold_percentiles: Percentiles for regime classification
            
        Returns:
            Series with volatility regime labels
        """
        # Calculate rolling volatility
        volatility = returns.rolling(window=window).std()
        
        # Calculate percentile thresholds
        low_threshold = volatility.quantile(threshold_percentiles[0] / 100)
        high_threshold = volatility.quantile(threshold_percentiles[1] / 100)
        
        # Classify regimes
        regime = pd.Series('medium', index=volatility.index)
        regime[volatility <= low_threshold] = 'low'
        regime[volatility >= high_threshold] = 'high'
        
        return regime

