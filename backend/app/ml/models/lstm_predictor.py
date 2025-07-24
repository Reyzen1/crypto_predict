# File: backend/app/ml/models/lstm_predictor.py
# LSTM Neural Network for cryptocurrency price prediction - CLEAN FIXED VERSION

import numpy as np
import pandas as pd
from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime, timedelta
import pickle
import os
import logging

# TensorFlow and Keras imports
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from tensorflow.keras.regularizers import l1_l2

# Scikit-learn imports for preprocessing
from sklearn.preprocessing import MinMaxScaler, RobustScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

logger = logging.getLogger(__name__)


class LSTMPredictor:
    """
    LSTM Neural Network for Cryptocurrency Price Prediction
    
    This class implements a sophisticated LSTM model for predicting cryptocurrency prices
    using historical price data and technical indicators. It includes features like:
    - Multi-layer LSTM with dropout and batch normalization
    - Feature engineering and preprocessing
    - Model training with early stopping and learning rate scheduling
    - Prediction with confidence intervals
    - Model persistence and versioning
    """
    
    def __init__(
        self,
        sequence_length: int = 60,          # Number of past time steps to use
        n_features: int = 5,                # Number of input features
        lstm_units: List[int] = [50, 50, 50], # LSTM layer units
        dropout_rate: float = 0.2,          # Dropout rate for regularization
        learning_rate: float = 0.001,       # Learning rate for optimizer
        batch_size: int = 32,               # Training batch size
        epochs: int = 100,                  # Maximum training epochs
        validation_split: float = 0.2,      # Validation data split
        model_name: str = "lstm_crypto_predictor"
    ):
        """
        Initialize LSTM Predictor
        
        Args:
            sequence_length: Number of past time steps to use for prediction
            n_features: Number of input features (price, volume, indicators)
            lstm_units: List of LSTM layer units
            dropout_rate: Dropout rate for regularization
            learning_rate: Learning rate for Adam optimizer
            batch_size: Training batch size
            epochs: Maximum number of training epochs
            validation_split: Fraction of data to use for validation
            model_name: Name identifier for the model
        """
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs
        self.validation_split = validation_split
        self.model_name = model_name
        
        # Model components
        self.model = None
        self.scaler = None
        self.feature_scaler = None
        self.is_trained = False
        
        # Training history and metrics
        self.training_history = None
        self.training_metrics = {}
        
        # Model configuration
        self.config = {
            'sequence_length': sequence_length,
            'n_features': n_features,
            'lstm_units': lstm_units,
            'dropout_rate': dropout_rate,
            'learning_rate': learning_rate,
            'batch_size': batch_size,
            'epochs': epochs,
            'validation_split': validation_split,
            'model_name': model_name,
            'created_at': datetime.utcnow().isoformat(),
            'tensorflow_version': tf.__version__
        }
        
        logger.info(f"Initialized LSTM Predictor: {model_name}")
    
    def build_model(self) -> Sequential:
        """
        Build LSTM neural network architecture
        
        Creates a multi-layer LSTM network with the following structure:
        - Multiple LSTM layers with dropout and batch normalization
        - Dense layers for output prediction
        - L1/L2 regularization for overfitting prevention
        
        Returns:
            Compiled Sequential model
        """
        model = Sequential(name=self.model_name)
        
        # First LSTM layer (returns sequences for next LSTM layers)
        model.add(LSTM(
            units=self.lstm_units[0],
            return_sequences=len(self.lstm_units) > 1,
            input_shape=(self.sequence_length, self.n_features),
            kernel_regularizer=l1_l2(l1=0.01, l2=0.01),
            name='lstm_1'
        ))
        model.add(Dropout(self.dropout_rate, name='dropout_1'))
        model.add(BatchNormalization(name='batch_norm_1'))
        
        # Additional LSTM layers
        for i, units in enumerate(self.lstm_units[1:], 2):
            return_sequences = i < len(self.lstm_units)  # Last layer doesn't return sequences
            
            model.add(LSTM(
                units=units,
                return_sequences=return_sequences,
                kernel_regularizer=l1_l2(l1=0.01, l2=0.01),
                name=f'lstm_{i}'
            ))
            model.add(Dropout(self.dropout_rate, name=f'dropout_{i}'))
            model.add(BatchNormalization(name=f'batch_norm_{i}'))
        
        # Dense layers for final prediction
        model.add(Dense(25, activation='relu', name='dense_1'))
        model.add(Dropout(self.dropout_rate / 2, name='dropout_final'))
        model.add(Dense(1, activation='linear', name='output'))  # Linear activation for price prediction
        
        # Compile model
        optimizer = Adam(learning_rate=self.learning_rate)
        model.compile(
            optimizer=optimizer,
            loss='huber',  # Huber loss is more robust to outliers than MSE
            metrics=['mae', 'mse']
        )
        
        logger.info(f"Built LSTM model with {model.count_params()} parameters")
        return model
    
    def prepare_data(
        self, 
        data: pd.DataFrame, 
        target_column: str = 'close_price',
        feature_columns: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, np.ndarray, Any, Any]:
        """
        Prepare data for LSTM training - FIXED VERSION
        
        Args:
            data: DataFrame with price and indicator data
            target_column: Column name for prediction target
            feature_columns: List of feature column names
            
        Returns:
            Tuple of (X, y, target_scaler, feature_scaler)
        """
        if feature_columns is None:
            # Select columns that definitely exist
            available_features = []
            potential_features = [
                'close_price', 'volume', 'open_price', 'high_price', 'low_price',
                'rsi', 'sma_20', 'ema_12', 'macd', 'market_cap'
            ]
            
            for col in potential_features:
                if col in data.columns:
                    available_features.append(col)
            
            feature_columns = available_features[:self.n_features]  # Max n_features columns
            
            if len(feature_columns) < 2:
                # Minimum base columns
                feature_columns = ['close_price', 'volume'] if 'volume' in data.columns else ['close_price', 'open_price']
        
        # Check column existence
        missing_cols = [col for col in feature_columns if col not in data.columns]
        if missing_cols:
            logger.warning(f"Missing columns {missing_cols}, removing from features")
            feature_columns = [col for col in feature_columns if col in data.columns]
        
        if not feature_columns:
            raise ValueError("No valid feature columns found")
        
        if target_column not in data.columns:
            raise ValueError(f"Target column '{target_column}' not found in data")
        
        # Sort by timestamp
        if 'timestamp' in data.columns:
            data = data.sort_values('timestamp').copy()
        
        # Handle missing values - use modern pandas methods
        logger.info(f"Using feature columns: {feature_columns}")
        data_clean = data.copy()
        
        # Replace old fillna with modern pandas methods
        for col in feature_columns + [target_column]:
            if col in data_clean.columns:
                # Forward fill then backward fill
                data_clean[col] = data_clean[col].ffill().bfill()
        
        # Remove remaining NaN values
        data_clean = data_clean.dropna(subset=feature_columns + [target_column])
        
        if len(data_clean) < self.sequence_length + 1:
            raise ValueError(f"Insufficient data after cleaning: {len(data_clean)} < {self.sequence_length + 1}")
        
        # Extract features and target
        features = data_clean[feature_columns].values
        target = data_clean[target_column].values.reshape(-1, 1)
        
        logger.info(f"Data shape before scaling: features {features.shape}, target {target.shape}")
        
        # FIXED: Initialize and fit scalers properly
        if self.feature_scaler is None:
            self.feature_scaler = RobustScaler()  # More robust to outliers
        
        if self.scaler is None:
            self.scaler = MinMaxScaler(feature_range=(0, 1))
        
        # Fit and transform features
        features_scaled = self.feature_scaler.fit_transform(features)
        
        # Fit and transform target
        target_scaled = self.scaler.fit_transform(target)
        
        # Update n_features based on actual features used
        self.n_features = features_scaled.shape[1]
        
        # Create sequences for LSTM
        X, y = self._create_sequences(features_scaled, target_scaled.flatten())
        
        logger.info(f"✅ Data prepared successfully: X shape {X.shape}, y shape {y.shape}")
        logger.info(f"✅ Scalers fitted: feature_scaler={self.feature_scaler is not None}, target_scaler={self.scaler is not None}")
        
        return X, y, self.scaler, self.feature_scaler
    
    def _create_sequences(
        self, 
        features: np.ndarray, 
        target: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for LSTM input
        
        Args:
            features: Scaled feature array
            target: Scaled target array
            
        Returns:
            Tuple of (X_sequences, y_sequences)
        """
        X, y = [], []
        
        for i in range(self.sequence_length, len(features)):
            # Features for past sequence_length time steps
            X.append(features[i - self.sequence_length:i])
            # Target for current time step
            y.append(target[i])
        
        return np.array(X), np.array(y)
    
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        save_model: bool = True,
        model_path: str = None
    ) -> Dict[str, Any]:
        """
        Train LSTM model
        
        Args:
            X_train: Training features
            y_train: Training targets
            X_val: Validation features (optional)
            y_val: Validation targets (optional)
            save_model: Whether to save the trained model
            model_path: Path to save model (optional)
            
        Returns:
            Dictionary with training metrics and history
        """
        logger.info("Starting LSTM model training...")
        
        # Build model if not already built
        if self.model is None:
            self.model = self.build_model()
        
        # Prepare validation data
        if X_val is None or y_val is None:
            validation_data = None
        else:
            validation_data = (X_val, y_val)
        
        # Setup callbacks
        callbacks = self._setup_callbacks(model_path)
        
        # Record training start time
        training_start = datetime.utcnow()
        
        # Train model
        try:
            self.training_history = self.model.fit(
                X_train, y_train,
                batch_size=self.batch_size,
                epochs=self.epochs,
                validation_data=validation_data,
                validation_split=self.validation_split if validation_data is None else 0.0,
                callbacks=callbacks,
                verbose=1,
                shuffle=True
            )
            
            # Record training completion
            training_end = datetime.utcnow()
            training_duration = (training_end - training_start).total_seconds()
            
            # Calculate training metrics
            self.training_metrics = {
                'training_duration_seconds': training_duration,
                'final_loss': float(self.training_history.history['loss'][-1]),
                'final_val_loss': float(self.training_history.history.get('val_loss', [0])[-1]),
                'final_mae': float(self.training_history.history['mae'][-1]),
                'final_val_mae': float(self.training_history.history.get('val_mae', [0])[-1]),
                'epochs_trained': len(self.training_history.history['loss']),
                'best_epoch': np.argmin(self.training_history.history.get('val_loss', self.training_history.history['loss'])) + 1,
                'training_completed_at': training_end.isoformat()
            }
            
            self.is_trained = True
            
            # Save model if requested
            if save_model:
                self.save_model(model_path)
            
            logger.info(f"Training completed in {training_duration:.2f} seconds")
            return self.training_metrics
            
        except Exception as e:
            logger.error(f"Training failed: {str(e)}")
            raise
    
    def _setup_callbacks(self, model_path: str = None) -> List:
        """Setup training callbacks"""
        callbacks = []
        
        # Early stopping
        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=15,
            restore_best_weights=True,
            verbose=1
        )
        callbacks.append(early_stopping)
        
        # Learning rate reduction
        lr_scheduler = ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=10,
            min_lr=1e-7,
            verbose=1
        )
        callbacks.append(lr_scheduler)
        
        # Model checkpointing
        if model_path:
            checkpoint_path = model_path.replace('.h5', '_checkpoint.h5')
            checkpoint = ModelCheckpoint(
                checkpoint_path,
                monitor='val_loss',
                save_best_only=True,
                save_weights_only=False,
                verbose=1
            )
            callbacks.append(checkpoint)
        
        return callbacks
    
    def predict(
        self, 
        X: np.ndarray, 
        return_confidence: bool = True
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Make predictions using trained model
        
        Args:
            X: Input sequences for prediction
            return_confidence: Whether to return confidence intervals
            
        Returns:
            Tuple of (predictions, confidence_intervals)
        """
        if not self.is_trained or self.model is None:
            raise ValueError("Model must be trained before making predictions")
        
        if self.scaler is None:
            raise ValueError("Data scaler not found. Train model first.")
        
        # Make predictions
        predictions_scaled = self.model.predict(X, verbose=0)
        
        # Inverse transform to original scale
        predictions = self.scaler.inverse_transform(predictions_scaled).flatten()
        
        # Calculate confidence intervals if requested
        confidence_intervals = None
        if return_confidence:
            confidence_intervals = self._calculate_confidence_intervals(X, predictions_scaled)
        
        return predictions, confidence_intervals
    
    def _calculate_confidence_intervals(
        self, 
        X: np.ndarray, 
        predictions_scaled: np.ndarray,
        confidence_level: float = 0.95
    ) -> np.ndarray:
        """
        Calculate prediction confidence intervals
        
        Uses Monte Carlo dropout to estimate prediction uncertainty.
        
        Args:
            X: Input data
            predictions_scaled: Scaled predictions
            confidence_level: Confidence level for intervals
            
        Returns:
            Array of confidence intervals
        """
        # Enable dropout during inference for uncertainty estimation
        n_samples = 100
        predictions_samples = []
        
        for _ in range(n_samples):
            # Make prediction with dropout enabled
            pred = self.model(X, training=True)
            predictions_samples.append(pred.numpy())
        
        predictions_samples = np.array(predictions_samples)
        
        # Calculate confidence intervals
        alpha = 1 - confidence_level
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100
        
        lower_bounds = np.percentile(predictions_samples, lower_percentile, axis=0)
        upper_bounds = np.percentile(predictions_samples, upper_percentile, axis=0)
        
        # Inverse transform bounds
        lower_bounds = self.scaler.inverse_transform(lower_bounds).flatten()
        upper_bounds = self.scaler.inverse_transform(upper_bounds).flatten()
        
        return np.column_stack([lower_bounds, upper_bounds])
    
    def evaluate(
        self, 
        X_test: np.ndarray, 
        y_test: np.ndarray
    ) -> Dict[str, float]:
        """
        Evaluate model performance on test data
        
        Args:
            X_test: Test features
            y_test: Test targets
            
        Returns:
            Dictionary with evaluation metrics
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        # Make predictions
        predictions, _ = self.predict(X_test, return_confidence=False)
        
        # Inverse transform true values - FIXED
        y_true = self.scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()
        
        # Calculate metrics
        mse = mean_squared_error(y_true, predictions)
        mae = mean_absolute_error(y_true, predictions)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_true, predictions)
        
        # Calculate percentage errors
        mape = np.mean(np.abs((y_true - predictions) / y_true)) * 100
        
        metrics = {
            'mse': float(mse),
            'mae': float(mae),
            'rmse': float(rmse),
            'r2_score': float(r2),
            'mape': float(mape)
        }
        
        logger.info(f"Model evaluation - RMSE: {rmse:.4f}, MAE: {mae:.4f}, R²: {r2:.4f}")
        return metrics
    
    def save_model(self, filepath: str = None) -> str:
        """
        Save trained model and scalers
        
        Args:
            filepath: Path to save model
            
        Returns:
            Path where model was saved
        """
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        if filepath is None:
            os.makedirs("models/lstm", exist_ok=True)
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filepath = f"models/lstm/{self.model_name}_{timestamp}.h5"
        
        # Save Keras model
        self.model.save(filepath)
        
        # Save scalers and config
        scaler_path = filepath.replace('.h5', '_scalers.pkl')
        config_path = filepath.replace('.h5', '_config.pkl')
        
        with open(scaler_path, 'wb') as f:
            pickle.dump({
                'target_scaler': self.scaler,
                'feature_scaler': self.feature_scaler
            }, f)
        
        with open(config_path, 'wb') as f:
            pickle.dump(self.config, f)
        
        logger.info(f"Model saved to {filepath}")
        return filepath
    
    def load_model(self, filepath: str) -> None:
        """
        Load saved model and scalers
        
        Args:
            filepath: Path to saved model
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        # Load Keras model
        self.model = load_model(filepath)
        
        # Load scalers
        scaler_path = filepath.replace('.h5', '_scalers.pkl')
        if os.path.exists(scaler_path):
            with open(scaler_path, 'rb') as f:
                scalers = pickle.load(f)
                self.scaler = scalers['target_scaler']
                self.feature_scaler = scalers['feature_scaler']
        
        # Load config
        config_path = filepath.replace('.h5', '_config.pkl')
        if os.path.exists(config_path):
            with open(config_path, 'rb') as f:
                self.config = pickle.load(f)
        
        self.is_trained = True
        logger.info(f"Model loaded from {filepath}")
    
    def get_model_summary(self) -> str:
        """Get model architecture summary"""
        if self.model is None:
            return "Model not built yet"
        
        import io
        import sys
        
        # Capture model summary
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()
        
        self.model.summary()
        
        sys.stdout = old_stdout
        return buffer.getvalue()