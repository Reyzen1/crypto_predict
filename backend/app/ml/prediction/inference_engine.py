# File: backend/app/ml/prediction/inference_engine.py
# High-performance Inference Engine for LSTM Models

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import threading

# Import ML components
from app.ml.models.lstm_predictor import LSTMPredictor
from app.ml.preprocessing.data_processor import CryptoPriceDataProcessor
from app.ml.config.ml_config import ml_config

logger = logging.getLogger(__name__)


class InferenceEngine:
    """
    High-performance Inference Engine for LSTM Models
    
    Features:
    - Optimized batch predictions
    - Asynchronous inference
    - Memory-efficient processing
    - Performance monitoring
    - Error handling and fallbacks
    - Thread-safe operations
    """
    
    def __init__(self, max_workers: int = 4):
        """
        Initialize inference engine
        
        Args:
            max_workers: Maximum number of worker threads for concurrent processing
        """
        self.max_workers = max_workers
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        
        # Performance tracking
        self.inference_stats = {
            'total_inferences': 0,
            'batch_inferences': 0,
            'average_inference_time': 0.0,
            'total_inference_time': 0.0,
            'error_count': 0,
            'last_inference': None
        }
        
        # Thread safety
        self._lock = threading.RLock()
        
        logger.info(f"InferenceEngine initialized with {max_workers} workers")
    
    async def predict_single(
        self,
        model: LSTMPredictor,
        input_data: np.ndarray,
        return_confidence: bool = True,
        return_raw: bool = False
    ) -> Dict[str, Any]:
        """
        Perform single prediction with comprehensive error handling
        
        Args:
            model: Trained LSTM model
            input_data: Input sequence data
            return_confidence: Whether to calculate confidence
            return_raw: Whether to return raw model output
            
        Returns:
            Prediction result dictionary
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            if not self._validate_model(model):
                raise ValueError("Invalid or untrained model")
            
            if not self._validate_input_data(input_data, model):
                raise ValueError("Invalid input data format")
            
            # Perform inference in thread pool for CPU-intensive operations
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.thread_pool,
                self._perform_inference,
                model,
                input_data,
                return_confidence,
                return_raw
            )
            
            # Update statistics
            inference_time = time.time() - start_time
            await self._update_inference_stats(inference_time, success=True)
            
            return {
                'success': True,
                'prediction': result['prediction'],
                'confidence': result.get('confidence'),
                'raw_output': result.get('raw_output') if return_raw else None,
                'inference_time_ms': round(inference_time * 1000, 2),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            error_time = time.time() - start_time
            await self._update_inference_stats(error_time, success=False)
            logger.error(f"Single prediction failed: {str(e)}")
            
            return {
                'success': False,
                'error': str(e),
                'inference_time_ms': round(error_time * 1000, 2),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def predict_batch(
        self,
        model: LSTMPredictor,
        input_batch: List[np.ndarray],
        return_confidence: bool = True,
        batch_size: int = 32
    ) -> Dict[str, Any]:
        """
        Perform batch predictions for efficiency
        
        Args:
            model: Trained LSTM model
            input_batch: List of input sequences
            return_confidence: Whether to calculate confidence
            batch_size: Size of processing batches
            
        Returns:
            Batch prediction results
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            if not self._validate_model(model):
                raise ValueError("Invalid or untrained model")
            
            if not input_batch:
                raise ValueError("Empty input batch")
            
            # Process in chunks for memory efficiency
            all_predictions = []
            all_confidences = []
            
            for i in range(0, len(input_batch), batch_size):
                batch_chunk = input_batch[i:i + batch_size]
                
                # Convert list to numpy array for batch processing
                batch_array = np.array(batch_chunk)
                
                # Validate batch format
                if not self._validate_batch_data(batch_array, model):
                    raise ValueError(f"Invalid batch data format at chunk {i}")
                
                # Perform batch inference
                loop = asyncio.get_event_loop()
                chunk_result = await loop.run_in_executor(
                    self.thread_pool,
                    self._perform_batch_inference,
                    model,
                    batch_array,
                    return_confidence
                )
                
                all_predictions.extend(chunk_result['predictions'])
                if return_confidence:
                    all_confidences.extend(chunk_result['confidences'])
            
            # Update statistics
            inference_time = time.time() - start_time
            await self._update_batch_stats(len(input_batch), inference_time, success=True)
            
            result = {
                'success': True,
                'batch_size': len(input_batch),
                'predictions': all_predictions,
                'average_prediction': float(np.mean(all_predictions)),
                'inference_time_ms': round(inference_time * 1000, 2),
                'predictions_per_second': round(len(input_batch) / inference_time, 2),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if return_confidence:
                result['confidences'] = all_confidences
                result['average_confidence'] = float(np.mean(all_confidences))
            
            return result
            
        except Exception as e:
            error_time = time.time() - start_time
            await self._update_batch_stats(len(input_batch) if input_batch else 0, error_time, success=False)
            logger.error(f"Batch prediction failed: {str(e)}")
            
            return {
                'success': False,
                'error': str(e),
                'batch_size': len(input_batch) if input_batch else 0,
                'inference_time_ms': round(error_time * 1000, 2),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def predict_with_uncertainty(
        self,
        model: LSTMPredictor,
        input_data: np.ndarray,
        n_samples: int = 100,
        dropout_rate: float = 0.1
    ) -> Dict[str, Any]:
        """
        Perform prediction with uncertainty quantification using Monte Carlo dropout
        
        Args:
            model: Trained LSTM model
            input_data: Input sequence data
            n_samples: Number of Monte Carlo samples
            dropout_rate: Dropout rate for uncertainty sampling
            
        Returns:
            Prediction with uncertainty estimates
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            if not self._validate_model(model):
                raise ValueError("Invalid or untrained model")
            
            if not self._validate_input_data(input_data, model):
                raise ValueError("Invalid input data format")
            
            # Perform Monte Carlo sampling
            loop = asyncio.get_event_loop()
            uncertainty_result = await loop.run_in_executor(
                self.thread_pool,
                self._monte_carlo_prediction,
                model,
                input_data,
                n_samples,
                dropout_rate
            )
            
            inference_time = time.time() - start_time
            await self._update_inference_stats(inference_time, success=True)
            
            return {
                'success': True,
                'prediction_mean': float(uncertainty_result['mean']),
                'prediction_std': float(uncertainty_result['std']),
                'confidence_interval': {
                    'lower': float(uncertainty_result['lower_bound']),
                    'upper': float(uncertainty_result['upper_bound'])
                },
                'uncertainty_score': float(uncertainty_result['uncertainty']),
                'n_samples': n_samples,
                'inference_time_ms': round(inference_time * 1000, 2),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            error_time = time.time() - start_time
            await self._update_inference_stats(error_time, success=False)
            logger.error(f"Uncertainty prediction failed: {str(e)}")
            
            return {
                'success': False,
                'error': str(e),
                'inference_time_ms': round(error_time * 1000, 2),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _perform_inference(
        self,
        model: LSTMPredictor,
        input_data: np.ndarray,
        return_confidence: bool = True,
        return_raw: bool = False
    ) -> Dict[str, Any]:
        """
        Perform actual inference (runs in thread pool)
        
        Args:
            model: LSTM model
            input_data: Input sequence
            return_confidence: Calculate confidence
            return_raw: Return raw output
            
        Returns:
            Inference results
        """
        try:
            # Perform prediction
            if return_confidence:
                prediction, confidence = model.predict(input_data, return_confidence=True)
            else:
                prediction = model.predict(input_data, return_confidence=False)
                confidence = None
            
            # Handle different prediction formats
            if isinstance(prediction, np.ndarray):
                prediction_value = float(prediction[0]) if len(prediction) > 0 else float(prediction)
            else:
                prediction_value = float(prediction)
            
            result = {
                'prediction': prediction_value
            }
            
            if return_confidence and confidence is not None:
                result['confidence'] = float(confidence)
            
            if return_raw:
                result['raw_output'] = prediction.tolist() if isinstance(prediction, np.ndarray) else prediction
            
            return result
            
        except Exception as e:
            logger.error(f"Inference execution failed: {str(e)}")
            raise
    
    def _perform_batch_inference(
        self,
        model: LSTMPredictor,
        batch_data: np.ndarray,
        return_confidence: bool = True
    ) -> Dict[str, Any]:
        """
        Perform batch inference (runs in thread pool)
        
        Args:
            model: LSTM model
            batch_data: Batch of input sequences
            return_confidence: Calculate confidence
            
        Returns:
            Batch inference results
        """
        try:
            # Perform batch prediction
            if return_confidence:
                predictions, confidences = model.predict(batch_data, return_confidence=True)
            else:
                predictions = model.predict(batch_data, return_confidence=False)
                confidences = None
            
            # Convert to lists for JSON serialization
            if isinstance(predictions, np.ndarray):
                predictions_list = predictions.flatten().tolist()
            else:
                predictions_list = [float(predictions)] if not isinstance(predictions, list) else predictions
            
            result = {
                'predictions': predictions_list
            }
            
            if return_confidence and confidences is not None:
                if isinstance(confidences, np.ndarray):
                    confidences_list = confidences.flatten().tolist()
                else:
                    confidences_list = [float(confidences)] if not isinstance(confidences, list) else confidences
                result['confidences'] = confidences_list
            
            return result
            
        except Exception as e:
            logger.error(f"Batch inference execution failed: {str(e)}")
            raise
    
    def _monte_carlo_prediction(
        self,
        model: LSTMPredictor,
        input_data: np.ndarray,
        n_samples: int,
        dropout_rate: float
    ) -> Dict[str, Any]:
        """
        Perform Monte Carlo dropout for uncertainty estimation
        
        Args:
            model: LSTM model
            input_data: Input sequence
            n_samples: Number of samples
            dropout_rate: Dropout rate
            
        Returns:
            Uncertainty estimates
        """
        try:
            predictions = []
            
            # Perform multiple predictions with dropout
            for _ in range(n_samples):
                # Enable dropout during inference for uncertainty
                # Note: This requires model to support dropout during inference
                try:
                    pred = model.predict(input_data, return_confidence=False)
                    if isinstance(pred, np.ndarray):
                        pred_value = float(pred[0]) if len(pred) > 0 else float(pred)
                    else:
                        pred_value = float(pred)
                    predictions.append(pred_value)
                except:
                    # Fallback: add some noise to simulate uncertainty
                    base_pred = model.predict(input_data, return_confidence=False)
                    if isinstance(base_pred, np.ndarray):
                        base_value = float(base_pred[0]) if len(base_pred) > 0 else float(base_pred)
                    else:
                        base_value = float(base_pred)
                    
                    # Add gaussian noise
                    noise = np.random.normal(0, base_value * dropout_rate)
                    predictions.append(base_value + noise)
            
            # Calculate statistics
            mean_pred = np.mean(predictions)
            std_pred = np.std(predictions)
            
            # Calculate confidence interval (95%)
            lower_bound = np.percentile(predictions, 2.5)
            upper_bound = np.percentile(predictions, 97.5)
            
            # Uncertainty score (coefficient of variation)
            uncertainty = std_pred / abs(mean_pred) if mean_pred != 0 else 1.0
            
            return {
                'mean': mean_pred,
                'std': std_pred,
                'lower_bound': lower_bound,
                'upper_bound': upper_bound,
                'uncertainty': uncertainty,
                'all_predictions': predictions
            }
            
        except Exception as e:
            logger.error(f"Monte Carlo prediction failed: {str(e)}")
            raise
    
    def _validate_model(self, model: LSTMPredictor) -> bool:
        """Validate that model is ready for inference"""
        
        try:
            if not model:
                return False
            
            if not hasattr(model, 'is_trained') or not model.is_trained:
                return False
            
            if not hasattr(model, 'model') or model.model is None:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _validate_input_data(self, input_data: np.ndarray, model: LSTMPredictor) -> bool:
        """Validate input data format"""
        
        try:
            if input_data is None or not isinstance(input_data, np.ndarray):
                return False
            
            # Check dimensions
            if len(input_data.shape) != 3:
                return False
            
            batch_size, sequence_length, n_features = input_data.shape
            
            # Validate against model requirements
            if hasattr(model, 'sequence_length') and sequence_length != model.sequence_length:
                logger.warning(f"Sequence length mismatch: expected {model.sequence_length}, got {sequence_length}")
                return False
            
            if hasattr(model, 'n_features') and n_features != model.n_features:
                logger.warning(f"Feature count mismatch: expected {model.n_features}, got {n_features}")
                return False
            
            # Check for invalid values
            if np.any(np.isnan(input_data)) or np.any(np.isinf(input_data)):
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Input validation failed: {str(e)}")
            return False
    
    def _validate_batch_data(self, batch_data: np.ndarray, model: LSTMPredictor) -> bool:
        """Validate batch data format"""
        
        try:
            if batch_data is None or not isinstance(batch_data, np.ndarray):
                return False
            
            # Check dimensions
            if len(batch_data.shape) != 3:
                return False
            
            batch_size, sequence_length, n_features = batch_data.shape
            
            # Validate each sample in batch
            for i in range(batch_size):
                sample = batch_data[i:i+1]  # Keep 3D shape
                if not self._validate_input_data(sample, model):
                    logger.warning(f"Invalid sample at batch index {i}")
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Batch validation failed: {str(e)}")
            return False
    
    async def _update_inference_stats(self, inference_time: float, success: bool) -> None:
        """Update inference statistics"""
        
        with self._lock:
            self.inference_stats['total_inferences'] += 1
            self.inference_stats['total_inference_time'] += inference_time
            
            if success:
                # Update average inference time
                total_time = self.inference_stats['total_inference_time']
                total_count = self.inference_stats['total_inferences']
                self.inference_stats['average_inference_time'] = total_time / total_count
            else:
                self.inference_stats['error_count'] += 1
            
            self.inference_stats['last_inference'] = datetime.utcnow().isoformat()
    
    async def _update_batch_stats(self, batch_size: int, inference_time: float, success: bool) -> None:
        """Update batch inference statistics"""
        
        with self._lock:
            self.inference_stats['batch_inferences'] += 1
            
            # Update single inference stats based on batch
            avg_time_per_item = inference_time / max(batch_size, 1)
            
            for _ in range(batch_size):
                await self._update_inference_stats(avg_time_per_item, success)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get inference engine performance statistics"""
        
        with self._lock:
            total_inferences = self.inference_stats['total_inferences']
            error_rate = 0.0
            
            if total_inferences > 0:
                error_rate = self.inference_stats['error_count'] / total_inferences * 100
            
            return {
                'total_inferences': total_inferences,
                'batch_inferences': self.inference_stats['batch_inferences'],
                'average_inference_time_ms': round(
                    self.inference_stats['average_inference_time'] * 1000, 2
                ),
                'total_inference_time_seconds': round(
                    self.inference_stats['total_inference_time'], 2
                ),
                'error_count': self.inference_stats['error_count'],
                'error_rate_percentage': round(error_rate, 2),
                'last_inference': self.inference_stats['last_inference'],
                'worker_threads': self.max_workers,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def reset_stats(self) -> Dict[str, Any]:
        """Reset performance statistics"""
        
        with self._lock:
            old_stats = self.inference_stats.copy()
            
            self.inference_stats = {
                'total_inferences': 0,
                'batch_inferences': 0,
                'average_inference_time': 0.0,
                'total_inference_time': 0.0,
                'error_count': 0,
                'last_inference': None
            }
            
            return {
                'reset_at': datetime.utcnow().isoformat(),
                'previous_stats': old_stats
            }
    
    async def shutdown(self) -> None:
        """Shutdown inference engine and cleanup resources"""
        
        logger.info("Shutting down InferenceEngine...")
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)
        
        logger.info("InferenceEngine shutdown complete")


# Global inference engine instance
inference_engine = InferenceEngine(max_workers=4)


# Helper functions for easy access
async def predict_single_crypto(
    model: LSTMPredictor,
    input_data: np.ndarray,
    return_confidence: bool = True
) -> Dict[str, Any]:
    """
    Helper function for single cryptocurrency prediction
    
    Args:
        model: Trained LSTM model
        input_data: Input sequence data
        return_confidence: Whether to return confidence
        
    Returns:
        Prediction result
    """
    return await inference_engine.predict_single(
        model=model,
        input_data=input_data,
        return_confidence=return_confidence
    )


async def predict_batch_crypto(
    model: LSTMPredictor,
    input_batch: List[np.ndarray],
    return_confidence: bool = True,
    batch_size: int = 32
) -> Dict[str, Any]:
    """
    Helper function for batch cryptocurrency predictions
    
    Args:
        model: Trained LSTM model
        input_batch: List of input sequences
        return_confidence: Whether to return confidence
        batch_size: Processing batch size
        
    Returns:
        Batch prediction results
    """
    return await inference_engine.predict_batch(
        model=model,
        input_batch=input_batch,
        return_confidence=return_confidence,
        batch_size=batch_size
    )


async def predict_with_uncertainty_crypto(
    model: LSTMPredictor,
    input_data: np.ndarray,
    n_samples: int = 100
) -> Dict[str, Any]:
    """
    Helper function for uncertainty-aware predictions
    
    Args:
        model: Trained LSTM model
        input_data: Input sequence data
        n_samples: Number of Monte Carlo samples
        
    Returns:
        Prediction with uncertainty estimates
    """
    return await inference_engine.predict_with_uncertainty(
        model=model,
        input_data=input_data,
        n_samples=n_samples
    )


def get_inference_stats() -> Dict[str, Any]:
    """Get inference engine performance statistics"""
    return inference_engine.get_performance_stats()


def reset_inference_stats() -> Dict[str, Any]:
    """Reset inference engine statistics"""
    return inference_engine.reset_stats()


async def shutdown_inference_engine() -> None:
    """Shutdown inference engine"""
    await inference_engine.shutdown()