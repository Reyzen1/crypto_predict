# File: backend/app/ml/training/training_service.py
# Real ML Training Service with LSTM Integration - FIXED VERSION

import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.ml.models.lstm_predictor import LSTMPredictor
from app.ml.preprocessing.data_processor import CryptoPriceDataProcessor
from app.ml.config.ml_config import ml_config, model_registry

logger = logging.getLogger(__name__)


class MLTrainingService:
    """Real ML Training Service for Cryptocurrency Price Prediction"""
    
    def __init__(self):
        self.models = {}
        self.training_history = {}
        self.data_processor = None
        logger.info("MLTrainingService initialized with real LSTM integration")
    
    def _get_data_processor(self):
        """Get or create data processor"""
        if self.data_processor is None:
            self.data_processor = CryptoPriceDataProcessor(
                scaling_method=ml_config.scaling_method.value,
                min_data_points=ml_config.min_data_points,
                add_technical_indicators=ml_config.add_technical_indicators,
                add_time_features=ml_config.add_time_features,
                add_price_features=ml_config.add_price_features
            )
        return self.data_processor
    
    async def train_model_for_crypto(
        self,
        crypto_symbol: str,
        training_data: pd.DataFrame,
        training_config: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Train LSTM model for a specific cryptocurrency - REAL IMPLEMENTATION"""
        
        try:
            logger.info(f"Starting real LSTM training for {crypto_symbol}")
            training_start = datetime.utcnow()
            
            # Default training config
            if training_config is None:
                training_config = {
                    'sequence_length': ml_config.lstm_sequence_length,
                    'lstm_units': ml_config.lstm_units,
                    'epochs': ml_config.lstm_epochs,
                    'batch_size': ml_config.lstm_batch_size,
                    'learning_rate': ml_config.lstm_learning_rate,
                    'dropout_rate': ml_config.lstm_dropout_rate
                }
            
            # Step 1: Data preprocessing
            logger.info("Step 1: Preprocessing training data...")
            processor = self._get_data_processor()
            
            try:
                processed_data, processing_info = processor.process_data(training_data)
                logger.info(f"Data processing completed: {len(processed_data)} records")
            except Exception as e:
                logger.warning(f"Data processing failed: {e}, using basic processing")
                # Fallback to basic processing
                processed_data = training_data.copy()
                processing_info = {'total_features': len(training_data.columns)}
            
            # Step 2: Initialize LSTM model
            logger.info("Step 2: Initializing LSTM model...")
            
            # Determine number of features from processed data
            available_features = [col for col in processed_data.columns 
                                if col not in ['timestamp', 'id', 'crypto_id', 'created_at']]
            n_features = min(len(available_features), 10)  # Limit features for stability
            
            lstm_model = LSTMPredictor(
                sequence_length=training_config['sequence_length'],
                n_features=n_features,
                lstm_units=training_config['lstm_units'],
                dropout_rate=training_config['dropout_rate'],
                learning_rate=training_config['learning_rate'],
                batch_size=training_config['batch_size'],
                epochs=training_config['epochs'],
                model_name=f"lstm_{crypto_symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            # Step 3: Prepare data for LSTM
            logger.info("Step 3: Preparing LSTM training data...")
            X, y, target_scaler, feature_scaler = lstm_model.prepare_data(processed_data)
            
            logger.info(f"LSTM data prepared: X shape {X.shape}, y shape {y.shape}")
            
            # Step 4: Split data for training/validation
            logger.info("Step 4: Splitting data for training...")
            train_size = int(0.8 * len(X))
            X_train, X_val = X[:train_size], X[train_size:]
            y_train, y_val = y[:train_size], y[train_size:]
            
            logger.info(f"Training data: {X_train.shape[0]} samples, Validation: {X_val.shape[0]} samples")
            
            # Step 5: Train the model
            logger.info("Step 5: Training LSTM model...")
            training_metrics = lstm_model.train(
                X_train, y_train, 
                X_val, y_val, 
                save_model=False  # Don't auto-save during training
            )
            
            # Step 6: Evaluate model
            logger.info("Step 6: Evaluating model performance...")
            evaluation_metrics = lstm_model.evaluate(X_val, y_val)
            
            # Step 7: Test prediction to ensure model works
            logger.info("Step 7: Testing model prediction...")
            test_predictions, confidence_intervals = lstm_model.predict(X_val[:3])
            
            # Calculate training duration
            training_end = datetime.utcnow()
            total_duration = (training_end - training_start).total_seconds()
            
            # Generate model ID
            model_id = f"{crypto_symbol}_lstm_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Store trained model
            self.models[model_id] = {
                'model': lstm_model,
                'crypto_symbol': crypto_symbol,
                'training_config': training_config,
                'training_metrics': training_metrics,
                'evaluation_metrics': evaluation_metrics,
                'created_at': training_end
            }
            
            # Register model in registry
            try:
                model_registry.register_model(
                    model_id=model_id,
                    crypto_symbol=crypto_symbol,
                    model_type="LSTM",
                    model_path=None,  # In-memory model for now
                    performance_metrics=evaluation_metrics
                )
                model_registry.set_active_model(crypto_symbol, model_id)
                logger.info(f"Model {model_id} registered and set as active")
            except Exception as e:
                logger.warning(f"Failed to register model: {e}")
            
            # Prepare success result
            result = {
                'success': True,
                'crypto_symbol': crypto_symbol,
                'model_id': model_id,
                'message': 'LSTM training completed successfully',
                'training_metrics': {
                    'final_loss': training_metrics['final_loss'],
                    'final_val_loss': training_metrics['final_val_loss'],
                    'final_mae': training_metrics['final_mae'],
                    'epochs_trained': training_metrics['epochs_trained'],
                    'training_duration_seconds': training_metrics['training_duration_seconds']
                },
                'evaluation_metrics': evaluation_metrics,
                'model_info': {
                    'sequence_length': lstm_model.sequence_length,
                    'n_features': lstm_model.n_features,
                    'lstm_units': lstm_model.lstm_units,
                    'total_parameters': lstm_model.model.count_params() if lstm_model.model else 0
                },
                'data_info': {
                    'total_records': len(training_data),
                    'processed_records': len(processed_data),
                    'training_samples': len(X_train),
                    'validation_samples': len(X_val),
                    'features_used': n_features
                },
                'sample_predictions': test_predictions.tolist() if test_predictions is not None else [],
                'training_duration_total': total_duration,
                'created_at': training_end.isoformat()
            }
            
            logger.info(f"✅ LSTM training completed successfully for {crypto_symbol}")
            logger.info(f"   - Model ID: {model_id}")
            logger.info(f"   - Final Loss: {training_metrics['final_loss']:.6f}")
            logger.info(f"   - RMSE: {evaluation_metrics.get('rmse', 'N/A'):.4f}")
            logger.info(f"   - Duration: {total_duration:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Model training failed for {crypto_symbol}: {str(e)}")
            
            return {
                'success': False, 
                'error': str(e), 
                'crypto_symbol': crypto_symbol,
                'message': f'Training failed: {str(e)}',
                'training_duration_total': (datetime.utcnow() - training_start).total_seconds() if 'training_start' in locals() else 0
            }
    
    def get_model(self, model_id: str) -> Optional[LSTMPredictor]:
        """Get trained model by ID"""
        model_info = self.models.get(model_id)
        return model_info['model'] if model_info else None
    
    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """List all trained models"""
        return {
            model_id: {
                'crypto_symbol': info['crypto_symbol'],
                'created_at': info['created_at'].isoformat(),
                'training_metrics': info['training_metrics'],
                'evaluation_metrics': info['evaluation_metrics']
            }
            for model_id, info in self.models.items()
        }
    
    def predict_with_model(self, model_id: str, input_data: np.ndarray) -> Optional[np.ndarray]:
        """Make prediction with specific model"""
        try:
            model_info = self.models.get(model_id)
            if not model_info:
                return None
            
            lstm_model = model_info['model']
            predictions, _ = lstm_model.predict(input_data, return_confidence=False)
            return predictions
            
        except Exception as e:
            logger.error(f"Prediction failed for model {model_id}: {e}")
            return None


# Global training service instance
training_service = MLTrainingService()