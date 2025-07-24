# File: backend/app/ml/training/training_service.py
# Complete ML Training Service integrating with existing codebase

import asyncio
import logging
import os
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
    Complete ML Training Service for Cryptocurrency Price Prediction
    
    This service orchestrates the entire ML training pipeline:
    - Data collection from database using existing repositories
    - Data preprocessing using existing CryptoPriceDataProcessor
    - Model training using existing LSTMPredictor
    - Model evaluation and persistence
    - Integration with existing model registry
    - Storing results in existing database models
    """
    
    def __init__(self):
        """Initialize training service with existing components"""
        self.data_processor = CryptoPriceDataProcessor(
            scaling_method=ml_config.scaling_method.value,
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
        Train LSTM model for a specific cryptocurrency
        
        Args:
            crypto_symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
            training_config: Optional training configuration override
            db: Optional database session
            
        Returns:
            Dictionary with training results and metrics
        """
        logger.info(f"Starting model training for {crypto_symbol}")
        
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
            
            # Step 3: Preprocess data using existing data processor
            processed_data, processing_info = self.data_processor.process_data(
                training_data,
                target_column='close_price',
                timestamp_column='timestamp'
            )
            
            logger.info(f"Data preprocessing completed: {processing_info['total_features']} features created")
            
            # Step 4: Prepare data for LSTM training
            X_train, y_train, X_val, y_val, X_test, y_test = await self._prepare_lstm_data(
                processed_data, training_config
            )
            
            # Step 5: Create and configure LSTM predictor
            lstm_predictor = self._create_lstm_predictor(
                n_features=X_train.shape[2],
                training_config=training_config
            )
            
            # IMPORTANT: Set the scalers before training
            lstm_predictor.scaler = self.data_processor.scaler
            lstm_predictor.feature_scaler = getattr(self.data_processor, 'feature_scaler', None)
            
            # Step 6: Train the model
            training_metrics = lstm_predictor.train(
                X_train=X_train,
                y_train=y_train,
                X_val=X_val,
                y_val=y_val,
                save_model=False  # We'll save manually with metadata
            )
            
            # Step 7: Evaluate model performance
            evaluation_metrics = lstm_predictor.evaluate(X_test, y_test)
            
            # Step 8: Save model with metadata
            model_id = f"{crypto_symbol}_lstm_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            model_path = os.path.join(ml_config.models_storage_path, f"{model_id}.h5")
            
            # Save model and metadata using existing utility
            all_metrics = {**training_metrics, **evaluation_metrics}
            feature_names = list(processed_data.columns)
            
            metadata = self.model_persistence.create_model_metadata(
                model_type="lstm",
                crypto_symbol=crypto_symbol,
                training_metrics=all_metrics,
                feature_names=feature_names,
                training_config=training_config or {},
                data_info=processing_info
            )
            
            # Save model files
            lstm_predictor.save_model(model_path)
            self.model_persistence.save_model_metadata(model_path, metadata)
            
            # Step 9: Register model in existing model registry
            model_registry.register_model(
                model_id=model_id,
                crypto_symbol=crypto_symbol,
                model_type="lstm",
                model_path=model_path,
                performance_metrics=all_metrics,
                metadata=metadata
            )
            
            # Set as active model if it's better than existing
            await self._update_active_model_if_better(crypto_symbol, model_id, all_metrics)
            
            # Step 10: Store training results in database
            await self._store_training_results(
                db, crypto.id, model_id, all_metrics, len(training_data)
            )
            
            # Step 11: Generate sample predictions and store them
            await self._generate_sample_predictions(
                db, crypto.id, lstm_predictor, X_test, y_test, model_id
            )
            
            result = {
                'success': True,
                'model_id': model_id,
                'crypto_symbol': crypto_symbol,
                'model_path': model_path,
                'training_metrics': training_metrics,
                'evaluation_metrics': evaluation_metrics,
                'data_info': processing_info,
                'training_duration': training_metrics.get('training_duration_seconds', 0),
                'data_points_used': len(training_data),
                'features_count': len(feature_names),
                'message': f'Model trained successfully for {crypto_symbol}'
            }
            
            logger.info(f"Training completed successfully for {crypto_symbol}: {model_id}")
            return result
            
        except Exception as e:
            logger.error(f"Model training failed for {crypto_symbol}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'crypto_symbol': crypto_symbol,
                'message': f'Training failed for {crypto_symbol}'
            }
        
        finally:
            if close_db:
                db.close()
    
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
    
    async def _prepare_lstm_data(
        self, 
        processed_data: pd.DataFrame, 
        training_config: Optional[Dict[str, Any]]
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Prepare data for LSTM training with proper splits"""
        
        # Get feature columns (exclude timestamp and target)
        feature_columns = [col for col in processed_data.columns 
                          if col not in ['timestamp', 'close_price']]
        
        features = processed_data[feature_columns].values
        target = processed_data['close_price'].values
        
        # Use existing LSTMPredictor prepare_data method
        lstm_predictor = LSTMPredictor(sequence_length=ml_config.lstm_sequence_length)
        
        X, y, _, _ = lstm_predictor.prepare_data(
            processed_data,
            target_column='close_price',
            feature_columns=feature_columns
        )
        
        # Split data according to ml_config ratios
        total_len = len(X)
        train_end = int(total_len * ml_config.train_ratio)
        val_end = int(total_len * (ml_config.train_ratio + ml_config.validation_ratio))
        
        X_train = X[:train_end]
        y_train = y[:train_end]
        X_val = X[train_end:val_end]
        y_val = y[train_end:val_end]
        X_test = X[val_end:]
        y_test = y[val_end:]
        
        logger.info(f"Data split - Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
        
        return X_train, y_train, X_val, y_val, X_test, y_test
    
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
    
    async def _store_training_results(
        self,
        db: Session,
        crypto_id: int,
        model_id: str,
        metrics: Dict[str, float],
        data_points: int
    ) -> None:
        """Store training results in database"""
        
        # Create a training record in predictions table for tracking
        prediction_data = PredictionCreate(
            crypto_id=crypto_id,
            model_name="lstm_training_result",
            model_version=model_id,
            predicted_price=Decimal('0.0'),  # Not a real prediction
            confidence_score=Decimal(str(metrics.get('r2_score', 0.0))),
            prediction_horizon=0,  # Training record
            target_datetime=datetime.utcnow(),
            input_price=Decimal('0.0'),
            features_used=json.dumps({
                'training_metrics': metrics,
                'data_points': data_points,
                'model_id': model_id
            }),
            notes=f"Training completed for model {model_id}"
        )
        
        # Use existing repository to store
        prediction_repository.create(db, obj_in=prediction_data)
        db.commit()
        
        logger.info(f"Stored training results in database for model {model_id}")
    
    async def _generate_sample_predictions(
        self,
        db: Session,
        crypto_id: int,
        lstm_predictor: LSTMPredictor,
        X_test: np.ndarray,
        y_test: np.ndarray,
        model_id: str
    ) -> None:
        """Generate and store sample predictions for evaluation"""
        
        if len(X_test) == 0:
            return
        
        # Generate predictions on test set
        predictions, confidence_intervals = lstm_predictor.predict(
            X_test[:10],  # First 10 test samples
            return_confidence=True
        )
        
        # Store predictions in database
        for i, (pred, actual) in enumerate(zip(predictions[:5], y_test[:5])):  # Store first 5
            
            prediction_data = PredictionCreate(
                crypto_id=crypto_id,
                model_name="lstm",
                model_version=model_id,
                predicted_price=Decimal(str(float(pred))),
                confidence_score=Decimal('0.85'),  # Default confidence
                prediction_horizon=24,  # 24 hours ahead
                target_datetime=datetime.now(timezone.utc) + timedelta(hours=24),
                input_price=Decimal(str(float(actual))),
                features_used=json.dumps({'test_prediction': True, 'test_index': i}),
                notes=f"Test prediction from model {model_id}"
            )
            
            prediction_repository.create(db, obj_in=prediction_data)
        
        db.commit()
        logger.info(f"Stored {min(5, len(predictions))} sample predictions for model {model_id}")
    
    async def get_training_status(self, crypto_symbol: str) -> Dict[str, Any]:
        """Get training status for a cryptocurrency"""
        
        active_model = model_registry.get_active_model(crypto_symbol)
        all_models = model_registry.list_models(crypto_symbol)
        
        return {
            'crypto_symbol': crypto_symbol,
            'has_active_model': active_model is not None,
            'active_model': active_model,
            'total_models': len(all_models),
            'models': all_models[:5]  # Last 5 models
        }
    
    async def cleanup_old_models(self, crypto_symbol: str, keep_count: int = 5) -> Dict[str, Any]:
        """Clean up old models, keeping only the most recent ones"""
        
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
            if not model['is_active']:  # Don't remove active model
                model_id = model['model_id'] if 'model_id' in model else None
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


# Global training service instance
training_service = MLTrainingService()