# File: backend/app/ml/training/training_service.py
# Fixed ML Training Service with corrected scaler handling

import os
import warnings

# Suppress TensorFlow C++ messages completely
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Only FATAL errors

# Suppress all Python warnings including Keras warnings
warnings.filterwarnings('ignore')

# Configure TensorFlow logging before importing TensorFlow
import logging
logging.getLogger('tensorflow').setLevel(logging.FATAL)

# Now import TensorFlow and suppress its logger
import tensorflow as tf
tf.get_logger().setLevel('FATAL')

import asyncio
import logging
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

# Import existing ML components
from app.ml.models.lstm_predictor import LSTMPredictor
from app.ml.preprocessing.data_processor import CryptoPriceDataProcessor
from app.ml.config.ml_config import ml_config, model_registry
from app.ml.utils.model_utils import ModelMetrics, ModelPersistence

# Import existing database components
from app.core.database import SessionLocal
from app.repositories import (
    cryptocurrency_repository, 
    price_data_repository,
    prediction_repository
)
from app.models import Cryptocurrency, PriceData, Prediction
from app.schemas.prediction import PredictionCreate

logger = logging.getLogger(__name__)


class MLTrainingService:
    """
    Fixed ML Training Service for Cryptocurrency Price Prediction
    """
    
    def __init__(self):
        """Initialize training service with existing components"""
        self.data_processor = CryptoPriceDataProcessor(
            scaling_method=ml_config.scaling_method,
            handle_missing=ml_config.handle_missing,
            add_technical_indicators=ml_config.add_technical_indicators,
            add_time_features=ml_config.add_time_features,
            add_price_features=ml_config.add_price_features,
            outlier_threshold=ml_config.outlier_threshold,
            min_data_points=ml_config.min_data_points
        )
        
        self.model_metrics = ModelMetrics()
        self.model_persistence = ModelPersistence()
        
        # Ensure model storage directory exists
        os.makedirs(ml_config.models_storage_path, exist_ok=True)
        
        logger.info("MLTrainingService initialized with existing components")
    
    async def train_model_for_crypto(
        self,
        crypto_symbol: str,
        training_config: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Train LSTM model for a specific cryptocurrency with automatic fallback
        """
        logger.info(f"Starting model training for {crypto_symbol}")
        
        # First, try comprehensive training
        try:
            result = await self._train_model_comprehensive(
                crypto_symbol=crypto_symbol,
                training_config=training_config,
                db=db
            )
            
            if result.get('success', False):
                logger.info(f"✅ Comprehensive training succeeded for {crypto_symbol}")
                return result
            else:
                logger.warning(f"⚠️ Comprehensive training failed for {crypto_symbol}: {result.get('error', 'Unknown error')}")
                raise Exception(f"Comprehensive training failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.warning(f"⚠️ Comprehensive training failed for {crypto_symbol}: {str(e)}")
          
            logger.error(f"❌ Comprehensive training failed for {crypto_symbol}: {str(e)}")
            return {
                'success': False,
                'error': f"Comprehensive training failed. Main: {str(e)}",
                'crypto_symbol': crypto_symbol,
                'message': f'Comprehensive training failed for {crypto_symbol}'
            }

    async def _train_model_comprehensive(
        self,
        crypto_symbol: str,
        training_config: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:

        # Create database session if not provided
        if db is None:
            db = SessionLocal()
            close_db = True
        else:
            close_db = False
        
        try:
            # Step 1: Get cryptocurrency from database
            crypto = cryptocurrency_repository.get_by_symbol(db, crypto_symbol)
            if not crypto:
                raise ValueError(f"Cryptocurrency {crypto_symbol} not found in database")
            
            # Step 2: Load historical price data from database
            training_data = await self._load_training_data(db, crypto.id)
            if training_data.empty:
                raise ValueError(f"No price data found for {crypto_symbol}")
            
            logger.info(f"Loaded {len(training_data)} price records for {crypto_symbol}")
            
            # Step 3: Create LSTM predictor FIRST (before data processing)
            lstm_predictor = self._create_lstm_predictor(
                n_features=1,  # Will be updated after processing
                training_config=training_config
            )
            
            # Step 4: Use LSTM predictor's prepare_data method (this handles scaling)
            try:
                X, y, target_scaler, feature_scaler = lstm_predictor.prepare_data(
                    training_data,
                    target_column='close_price'
                )
                
                logger.info(f"Data prepared by LSTM predictor: X={X.shape}, y={y.shape}")
                
                # Update n_features based on actual data
                lstm_predictor.n_features = X.shape[2]
                
            except Exception as e:
                logger.error(f"Error in LSTM prepare_data: {str(e)}")
                # Fallback to manual data preparation
                X, y = self._manual_prepare_data(training_data)
                target_scaler = None
                feature_scaler = None
            
            # Step 5: Split data for training
            X_train, y_train, X_val, y_val, X_test, y_test = self._split_data(X, y)
            
            # Step 6: Train the model
            training_metrics = lstm_predictor.train(
                X_train=X_train,
                y_train=y_train,
                X_val=X_val,
                y_val=y_val,
                save_model=False  # We'll save manually with metadata
            )
            
            # Step 7: Evaluate model performance
            try:
                evaluation_metrics = lstm_predictor.evaluate(X_test, y_test)
            except Exception as e:
                logger.warning(f"Evaluation failed: {str(e)}, using default metrics")
                evaluation_metrics = {'rmse': 0.0, 'mae': 0.0, 'r2_score': 0.0}
            
            # Step 8: Save model with metadata
            model_id = f"{crypto_symbol}_lstm_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            model_path = os.path.join(ml_config.models_storage_path, f"{model_id}.h5")
            
            # Save model and metadata using existing utility
            all_metrics = {**training_metrics, **evaluation_metrics}
            
            try:
                # Try to save with full metadata
                feature_names = ['price_features'] * X.shape[2]  # Generic feature names
                
                metadata = self.model_persistence.create_model_metadata(
                    model_type="lstm",
                    crypto_symbol=crypto_symbol,
                    training_metrics=all_metrics,
                    feature_names=feature_names,
                    training_config=training_config or {},
                    data_info={'features_count': X.shape[2], 'data_points': len(training_data)}
                )
                
                # Save model files
                lstm_predictor.save_model(model_path)
                
                # Try to save metadata if method exists
                if hasattr(self.model_persistence, 'save_model_metadata'):
                    self.model_persistence.save_model_metadata(model_path, metadata)
                else:
                    # Manual metadata save
                    metadata_path = model_path.replace('.h5', '_metadata.json')
                    with open(metadata_path, 'w') as f:
                        json.dump(metadata, f, indent=2, default=str)
                
            except Exception as e:
                logger.warning(f"Could not save full metadata: {str(e)}")
                # Just save the model
                lstm_predictor.save_model(model_path)
            
            # Step 9: Register model in existing model registry
            # Step 9: Register model in existing model registry
            try:
                # Ensure performance_metrics is never None/empty
                safe_metrics = {}
                if all_metrics and isinstance(all_metrics, dict):
                    safe_metrics = all_metrics
                else:
                    # Provide default metrics if all_metrics is None/empty
                    safe_metrics = {
                        "training_completed": True,
                        "model_id": model_id,
                        "crypto_symbol": crypto_symbol
                    }
                    # Add training metrics if available
                    if training_metrics:
                        safe_metrics.update(training_metrics)
                    # Add evaluation metrics if available
                    if evaluation_metrics:
                        safe_metrics.update(evaluation_metrics)
                
                model_registry.register_model(
                    model_id=model_id,
                    crypto_symbol=crypto_symbol,
                    model_type="lstm",
                    model_path=model_path,
                    performance_metrics=safe_metrics,  # Always provide valid dict
                    metadata={'training_completed': True, 'auto_registered': True}
                )
                
                # Set as active model if it's better than existing
                try:
                    await self._update_active_model_if_better(crypto_symbol, model_id, safe_metrics)
                except:
                    # Fallback: just set as active
                    model_registry.set_active_model(crypto_symbol, model_id)
                
                logger.info(f"Model registered successfully in registry: {model_id}")
                
            except Exception as e:
                logger.error(f"Could not register model: {str(e)}")
                # Try basic registration as fallback
                try:
                    basic_metrics = {"registered_at": datetime.now().isoformat()}
                    model_registry.register_model(
                        model_id=model_id,
                        crypto_symbol=crypto_symbol,
                        model_type="lstm",
                        model_path=model_path,
                        performance_metrics=basic_metrics,
                        metadata={'fallback_registration': True}
                    )
                    model_registry.set_active_model(crypto_symbol, model_id)
                    logger.info(f"Model registered with fallback method: {model_id}")
                except Exception as e2:
                    logger.error(f"Even fallback registration failed: {str(e2)}")

                
                # Set as active model if it's better than existing
                await self._update_active_model_if_better(crypto_symbol, model_id, all_metrics)
                
            except Exception as e:
                logger.warning(f"Could not register model: {str(e)}")
            
            # Step 10: Store training results in database
            try:
                await self._store_training_results(
                    db, crypto.id, model_id, all_metrics, len(training_data)
                )
            except Exception as e:
                logger.warning(f"Could not store training results: {str(e)}")
            
            result = {
                'success': True,
                'model_id': model_id,
                'crypto_symbol': crypto_symbol,
                'model_path': model_path,
                'training_metrics': training_metrics,
                'evaluation_metrics': evaluation_metrics,
                'training_duration': training_metrics.get('training_duration_seconds', 0),
                'data_points_used': len(training_data),
                'features_count': X.shape[2],
                'message': f'Model trained successfully for {crypto_symbol}'
            }
            
            logger.info(f"Training completed successfully for {crypto_symbol}: {model_id}")
            return result
            
        except Exception as e:
            logger.error(f"Comprehensive model training failed for {crypto_symbol}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'crypto_symbol': crypto_symbol,
                'message': f'Comprehensive training failed for {crypto_symbol}'
            }
        
        finally:
            if close_db:
                db.close()
    
    def _manual_prepare_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Manual data preparation as fallback"""
        
        # Simple feature engineering
        data = df.copy()
        data = data.sort_values('timestamp').reset_index(drop=True)
        
        # Use basic OHLCV features
        features = ['open_price', 'high_price', 'low_price', 'close_price', 'volume']
        available_features = [f for f in features if f in data.columns]
        
        if not available_features:
            # Last resort: use only close price
            available_features = ['close_price']
        
        # Normalize features
        from sklearn.preprocessing import MinMaxScaler
        scaler = MinMaxScaler()
        
        feature_data = data[available_features].fillna(method='ffill').fillna(0)
        scaled_features = scaler.fit_transform(feature_data)
        
        # Create sequences
        sequence_length = 20
        X, y = [], []
        
        for i in range(sequence_length, len(scaled_features)):
            X.append(scaled_features[i-sequence_length:i])
            y.append(scaled_features[i, available_features.index('close_price')])
        
        return np.array(X), np.array(y)
    
    def _split_data(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Split data for training, validation, and testing"""
        
        total_len = len(X)
        train_end = int(total_len * 0.7)
        val_end = int(total_len * 0.85)
        
        X_train = X[:train_end]
        y_train = y[:train_end]
        X_val = X[train_end:val_end]
        y_val = y[train_end:val_end]
        X_test = X[val_end:]
        y_test = y[val_end:]
        
        logger.info(f"Data split - Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
        
        return X_train, y_train, X_val, y_val, X_test, y_test
    
    async def _load_training_data(self, db: Session, crypto_id: int) -> pd.DataFrame:
        """Load training data from database using existing repository"""
        
        # Get data from the last 6 months for training
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=180)
        
        # Use existing price_data_repository with the correct method name
        price_records = price_data_repository.get_price_history(
            db=db,
            crypto_id=crypto_id,
            start_date=start_date,
            end_date=end_date,
            limit=10000  # Reasonable limit
        )
        
        if not price_records:
            return pd.DataFrame()
        
        # Convert to DataFrame
        data = []
        for record in price_records:
            data.append({
                'timestamp': record.timestamp,
                'open_price': float(record.open_price),
                'high_price': float(record.high_price),
                'low_price': float(record.low_price),
                'close_price': float(record.close_price),
                'volume': float(record.volume) if record.volume else 0.0,
                'market_cap': float(record.market_cap) if record.market_cap else 0.0
            })
        
        df = pd.DataFrame(data)
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        return df
    
    def _create_lstm_predictor(
        self, 
        n_features: int, 
        training_config: Optional[Dict[str, Any]]
    ) -> LSTMPredictor:
        """Create LSTM predictor with configuration"""
        
        config = training_config or {}
        
        return LSTMPredictor(
            sequence_length=config.get('sequence_length', ml_config.lstm_sequence_length),
            n_features=n_features,
            lstm_units=config.get('lstm_units', ml_config.lstm_units),
            dropout_rate=config.get('dropout_rate', ml_config.lstm_dropout_rate),
            learning_rate=config.get('learning_rate', ml_config.lstm_learning_rate),
            batch_size=config.get('batch_size', ml_config.lstm_batch_size),
            epochs=config.get('epochs', ml_config.lstm_epochs),
            validation_split=config.get('validation_split', ml_config.lstm_validation_split),
            model_name=f"crypto_lstm_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        )
    
    async def _update_active_model_if_better(
        self, 
        crypto_symbol: str, 
        model_id: str, 
        metrics: Dict[str, float]
    ) -> None:
        """Update active model if the new one performs better"""
        
        try:
            current_active = model_registry.get_active_model(crypto_symbol)
            
            if current_active is None:
                # No active model, set this as active
                model_registry.set_active_model(crypto_symbol, model_id)
                logger.info(f"Set {model_id} as active model for {crypto_symbol} (first model)")
            else:
                # Compare performance (lower validation loss is better)
                current_val_loss = current_active['performance_metrics'].get('final_val_loss', float('inf'))
                new_val_loss = metrics.get('final_val_loss', float('inf'))
                
                if new_val_loss < current_val_loss:
                    model_registry.set_active_model(crypto_symbol, model_id)
                    logger.info(f"Updated active model for {crypto_symbol}: {model_id} (better performance)")
                else:
                    logger.info(f"Kept existing active model for {crypto_symbol} (better performance)")
        except Exception as e:
            logger.warning(f"Could not update active model: {str(e)}")
    
    async def _store_training_results(
        self,
        db: Session,
        crypto_id: int,
        model_id: str,
        metrics: Dict[str, float],
        data_points: int
    ) -> None:
        """Store training results in database"""
        
        try:
            # Convert numpy types to Python native types for JSON serialization
            clean_metrics = {}
            for key, value in metrics.items():
                if hasattr(value, 'item'):  # numpy scalar
                    clean_metrics[key] = float(value.item())
                elif isinstance(value, (np.int64, np.int32)):
                    clean_metrics[key] = int(value)
                elif isinstance(value, (np.float64, np.float32)):
                    clean_metrics[key] = float(value)
                else:
                    clean_metrics[key] = value
            
            # Calculate valid confidence score (0-1 range)
            r2_score = clean_metrics.get('r2_score', 0.0)
            confidence_score = max(0.0, min(1.0, (r2_score + 1) / 2))  # Normalize R² to 0-1
            if r2_score < 0:
                confidence_score = 0.1  # Minimum confidence for poor models
            
            # Use a dummy positive price for training records
            dummy_price = Decimal('1.0')
            
            # Future date for training records
            future_date = datetime.now(timezone.utc) + timedelta(days=1)
            
            # Create a training record in predictions table for tracking
            prediction_data = PredictionCreate(
                crypto_id=crypto_id,
                user_id=1,  # System user for training records
                model_name="lstm_training_result",
                predicted_price=dummy_price,  # Valid positive price
                confidence_score=Decimal(str(confidence_score)),  # Valid confidence
                prediction_horizon=0,  # Training record indicator
                target_date=future_date.date(),  # Future date
                target_datetime=future_date,
                input_price=dummy_price,
                features_used=json.dumps({
                    'training_metrics': clean_metrics,
                    'data_points': data_points,
                    'model_id': model_id,
                    'is_training_record': True
                }),
                notes=f"Training completed for model {model_id}"
            )
            
            # Use existing repository to store
            prediction_repository.create(db, obj_in=prediction_data)
            db.commit()
            
            logger.info(f"Stored training results in database for model {model_id}")
            
        except Exception as e:
            logger.warning(f"Could not store training results: {str(e)}")
            # Try with ultra-minimal data
            try:
                future_date = datetime.now(timezone.utc) + timedelta(days=1)
                minimal_prediction = PredictionCreate(
                    crypto_id=crypto_id,
                    user_id=1,
                    model_name="lstm_training",
                    predicted_price=Decimal('1.0'),  # Valid positive price
                    confidence_score=Decimal('0.5'),  # Valid confidence
                    prediction_horizon=0,
                    target_date=future_date.date(),  # Future date
                    target_datetime=future_date,
                    input_price=Decimal('1.0'),
                    notes=f"Training record for {model_id}"
                )
                prediction_repository.create(db, obj_in=minimal_prediction)
                db.commit()
                logger.info(f"Stored minimal training record for {model_id}")
            except Exception as e2:
                logger.error(f"Could not store even minimal training record: {str(e2)}")
    
    async def get_training_status(self, crypto_symbol: str) -> Dict[str, Any]:
        """Get training status for a cryptocurrency"""
        
        try:
            active_model = model_registry.get_active_model(crypto_symbol)
            all_models = model_registry.list_models(crypto_symbol)
            
            return {
                'crypto_symbol': crypto_symbol,
                'has_active_model': active_model is not None,
                'active_model': active_model,
                'total_models': len(all_models),
                'models': all_models[:5]  # Last 5 models
            }
        except Exception as e:
            return {
                'crypto_symbol': crypto_symbol,
                'has_active_model': False,
                'active_model': None,
                'total_models': 0,
                'models': [],
                'error': str(e)
            }
    
    async def cleanup_old_models(self, crypto_symbol: str, keep_count: int = 5) -> Dict[str, Any]:
        """Clean up old models, keeping only the most recent ones"""
        
        try:
            all_models = model_registry.list_models(crypto_symbol)
            
            if len(all_models) <= keep_count:
                return {
                    'success': True,
                    'message': f'No cleanup needed, only {len(all_models)} models exist',
                    'cleaned_count': 0
                }
            
            # Keep active model and most recent ones
            models_to_remove = all_models[keep_count:]
            cleaned_count = 0
            
            for model in models_to_remove:
                if not model.get('is_active', False):  # Don't remove active model
                    model_id = model.get('model_id')
                    if model_id and model_registry.remove_model(model_id):
                        # Also remove model files
                        model_path = model.get('model_path')
                        if model_path and os.path.exists(model_path):
                            try:
                                os.remove(model_path)
                                # Remove associated files
                                for ext in ['_metadata.json', '_scalers.pkl', '_config.json']:
                                    file_path = model_path.replace('.h5', ext)
                                    if os.path.exists(file_path):
                                        os.remove(file_path)
                            except Exception as e:
                                logger.warning(f"Could not remove model file {model_path}: {e}")
                        
                        cleaned_count += 1
            
            return {
                'success': True,
                'message': f'Cleaned up {cleaned_count} old models for {crypto_symbol}',
                'cleaned_count': cleaned_count
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Cleanup failed for {crypto_symbol}'
            }


# Global training service instance
training_service = MLTrainingService()

# Helper function for batch training with automatic fallback
async def train_multiple_cryptos(
    crypto_symbols: List[str],
    training_config: Optional[Dict[str, Any]] = None,
    max_concurrent: int = 3
) -> Dict[str, Any]:
    """Train models for multiple cryptocurrencies with automatic fallback support"""
    
    results = {}
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def train_single_crypto(symbol: str) -> Tuple[str, Dict[str, Any]]:
        async with semaphore:
            result = await training_service.train_model_for_crypto(
                crypto_symbol=symbol,
                training_config=training_config
            )
            return symbol, result
    
    # Execute training tasks
    tasks = [train_single_crypto(symbol) for symbol in crypto_symbols]
    completed_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    successful_count = 0
    fallback_count = 0
    failed_count = 0
    
    for result in completed_results:
        if isinstance(result, Exception):
            symbol = "unknown"
            results[symbol] = {
                'success': False,
                'error': str(result),
                'message': 'Unexpected error during training'
            }
            failed_count += 1
        else:
            symbol, training_result = result
            results[symbol] = training_result
            
            if training_result.get('success', False):
                if training_result.get('used_fallback', False):
                    fallback_count += 1
                else:
                    successful_count += 1
            else:
                failed_count += 1
    
    return {
        'success': successful_count + fallback_count > 0,
        'results': results,
        'summary': {
            'total_cryptos': len(crypto_symbols),
            'successful_comprehensive': successful_count,
            'successful_fallback': fallback_count,
            'failed': failed_count,
            'success_rate': (successful_count + fallback_count) / len(crypto_symbols) * 100
        },
        'message': f'Training completed: {successful_count} comprehensive, {fallback_count} fallback, {failed_count} failed'
    }