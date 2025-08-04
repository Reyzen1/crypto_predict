# File: backend/app/ml/prediction/prediction_service.py
# Real-time Prediction Service for CryptoPredict

import asyncio
import logging
import json
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

# Redis for caching
try:
    import redis
    from redis import Redis
except ImportError:
    redis = None

# Import existing ML components
from app.ml.models.lstm_predictor import LSTMPredictor
from app.ml.preprocessing.data_processor import CryptoPriceDataProcessor
from app.ml.config.ml_config import ml_config, model_registry
from app.ml.utils.model_utils import ModelMetrics

# Import existing database components
from app.core.database import SessionLocal
from app.core.config import settings
from app.repositories import (
    cryptocurrency_repository, 
    price_data_repository,
    prediction_repository
)
from app.repositories.ml_repository import ml_repository
from app.models import Cryptocurrency, PriceData, Prediction
from app.schemas.prediction import PredictionCreate

logger = logging.getLogger(__name__)


class PredictionService:
    """
    Real-time Prediction Service for Cryptocurrency Price Prediction
    
    Features:
    - Real-time predictions for multiple cryptocurrencies
    - Model loading and caching
    - Confidence interval calculation
    - Performance monitoring
    - Redis caching for fast responses
    - Automatic fallback mechanisms
    """
    
    def __init__(self):
        """Initialize prediction service"""
        self.data_processor = CryptoPriceDataProcessor(
            scaling_method=ml_config.scaling_method,
            handle_missing=ml_config.handle_missing,
            add_technical_indicators=ml_config.add_technical_indicators,
            add_time_features=ml_config.add_time_features,
            add_price_features=ml_config.add_price_features,
            outlier_threshold=ml_config.outlier_threshold,
            min_data_points=ml_config.min_data_points
        )
        
        # Model cache for loaded models
        self.model_cache = {}
        self.model_cache_timestamps = {}
        self.cache_ttl = 3600  # 1 hour
        
        # Redis cache for predictions
        self.redis_client = None
        if redis and hasattr(settings, 'REDIS_URL'):
            try:
                self.redis_client = redis.from_url(settings.REDIS_URL)
                # Test connection
                self.redis_client.ping()
                logger.info("Redis connection established for prediction caching")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
                self.redis_client = None
        
        # Performance tracking
        self.performance_metrics = {
            'total_predictions': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'average_response_time': 0.0,
            'error_count': 0
        }
        
        logger.info("PredictionService initialized successfully")
    
    async def predict_price(
        self,
        crypto_symbol: str,
        prediction_horizon: int = 24,  # hours
        use_cache: bool = True,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Generate price prediction for a cryptocurrency
        
        Args:
            crypto_symbol: Symbol of cryptocurrency (e.g., 'BTC')
            prediction_horizon: Hours ahead to predict (default: 24)
            use_cache: Whether to use cached predictions
            db: Database session
            
        Returns:
            Dictionary with prediction results
        """
        start_time = time.time()
        close_db = False
        
        try:
            # Database session management
            if db is None:
                db = SessionLocal()
                close_db = True
            
            # Step 1: Check cache first
            if use_cache and self.redis_client:
                cached_result = await self._get_cached_prediction(
                    crypto_symbol, prediction_horizon
                )
                if cached_result:
                    self.performance_metrics['cache_hits'] += 1
                    self._update_response_time(time.time() - start_time)
                    return cached_result
                
                self.performance_metrics['cache_misses'] += 1
            
            # Step 2: Validate cryptocurrency
            crypto = cryptocurrency_repository.get_by_symbol(db, crypto_symbol)
            if not crypto:
                raise ValueError(f"Cryptocurrency {crypto_symbol} not found")
            
            if not crypto.is_active:
                raise ValueError(f"Cryptocurrency {crypto_symbol} is not active")
            
            # Step 3: Load or get cached model
            model = await self._load_model(crypto_symbol)
            if not model:
                raise ValueError(f"No trained model available for {crypto_symbol}")
            
            # Step 4: Prepare input data
            input_data = await self._prepare_prediction_input(
                db, crypto.id, model.sequence_length
            )
            
            # Step 5: Generate prediction
            prediction_result = await self._generate_prediction(
                model, input_data, prediction_horizon
            )
            
            # Step 6: Calculate confidence intervals
            confidence_data = await self._calculate_confidence(
                model, input_data, prediction_result
            )
            
            # Step 7: Get current price for comparison
            current_price = await self._get_current_price(db, crypto.id)
            
            # Step 8: Prepare result
            result = {
                'success': True,
                'crypto_symbol': crypto_symbol,
                'current_price': float(current_price),
                'predicted_price': float(prediction_result['price']),
                'prediction_horizon_hours': prediction_horizon,
                'confidence_score': float(confidence_data['confidence']),
                'confidence_interval': {
                    'lower': float(confidence_data['lower_bound']),
                    'upper': float(confidence_data['upper_bound'])
                },
                'model_info': {
                    'model_id': model.model_name,
                    'features_used': input_data.shape[1] if len(input_data.shape) > 1 else 1,
                    'sequence_length': model.sequence_length,
                    'last_training': self._get_model_training_date(crypto_symbol)
                },
                'prediction_metadata': {
                    'timestamp': datetime.utcnow().isoformat(),
                    'response_time_ms': round((time.time() - start_time) * 1000, 2),
                    'cache_used': False,
                    'data_points_used': len(input_data)
                }
            }
            
            # Step 9: Cache result
            if self.redis_client:
                await self._cache_prediction(crypto_symbol, prediction_horizon, result)
            
            # Step 10: Store prediction in database
            await self._store_prediction_result(db, crypto.id, result)
            
            # Update performance metrics
            self.performance_metrics['total_predictions'] += 1
            self._update_response_time(time.time() - start_time)
            
            logger.info(f"Prediction generated for {crypto_symbol}: "
                       f"${result['predicted_price']:.2f} "
                       f"(confidence: {result['confidence_score']:.2f})")
            
            return result
            
        except Exception as e:
            self.performance_metrics['error_count'] += 1
            logger.error(f"Prediction failed for {crypto_symbol}: {str(e)}")
            
            # Try fallback prediction
            fallback_result = await self._fallback_prediction(
                crypto_symbol, prediction_horizon, db
            )
            
            if fallback_result:
                fallback_result['prediction_metadata']['fallback_used'] = True
                return fallback_result
            
            return {
                'success': False,
                'crypto_symbol': crypto_symbol,
                'error': str(e),
                'prediction_horizon_hours': prediction_horizon,
                'timestamp': datetime.utcnow().isoformat(),
                'response_time_ms': round((time.time() - start_time) * 1000, 2)
            }
            
        finally:
            if close_db:
                db.close()
    
    async def predict_batch(
        self,
        crypto_symbols: List[str],
        prediction_horizon: int = 24,
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """
        Generate predictions for multiple cryptocurrencies
        
        Args:
            crypto_symbols: List of cryptocurrency symbols
            prediction_horizon: Hours ahead to predict
            max_concurrent: Maximum concurrent predictions
            
        Returns:
            Dictionary with results for each symbol
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def predict_single(symbol: str) -> Tuple[str, Dict[str, Any]]:
            async with semaphore:
                result = await self.predict_price(symbol, prediction_horizon)
                return symbol, result
        
        # Execute batch predictions
        tasks = [predict_single(symbol) for symbol in crypto_symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        batch_result = {
            'success': True,
            'predictions': {},
            'summary': {
                'total_requested': len(crypto_symbols),
                'successful': 0,
                'failed': 0,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        for result in results:
            if isinstance(result, Exception):
                batch_result['summary']['failed'] += 1
                continue
                
            symbol, prediction = result
            batch_result['predictions'][symbol] = prediction
            
            if prediction.get('success', False):
                batch_result['summary']['successful'] += 1
            else:
                batch_result['summary']['failed'] += 1
        
        return batch_result
    
    async def _load_model(self, crypto_symbol: str) -> Optional[LSTMPredictor]:
        """Load model for cryptocurrency (with caching)"""
        
        # Check cache first
        cache_key = f"model_{crypto_symbol}"
        
        if cache_key in self.model_cache:
            # Check if cache is still valid
            cache_time = self.model_cache_timestamps.get(cache_key, 0)
            if time.time() - cache_time < self.cache_ttl:
                return self.model_cache[cache_key]
            else:
                # Remove expired cache
                del self.model_cache[cache_key]
                del self.model_cache_timestamps[cache_key]
        
        # Load model from registry
        try:
            active_model = model_registry.get_active_model(crypto_symbol)
            if not active_model:
                logger.warning(f"No active model found for {crypto_symbol}")
                return None
            
            model_path = active_model.get('model_path')
            if not model_path:
                logger.warning(f"No model path for {crypto_symbol}")
                return None
            
            # Create and load LSTM predictor
            model = LSTMPredictor()
            model.load_model(model_path)
            
            # Cache the loaded model
            self.model_cache[cache_key] = model
            self.model_cache_timestamps[cache_key] = time.time()
            
            logger.info(f"Model loaded for {crypto_symbol}: {model_path}")
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model for {crypto_symbol}: {str(e)}")
            return None
    
    async def _prepare_prediction_input(
        self, 
        db: Session, 
        crypto_id: int, 
        sequence_length: int
    ) -> np.ndarray:
        """Prepare input data for prediction"""
        
        # Get recent price data
        recent_data = ml_repository.get_recent_data_for_prediction(
            db=db,
            crypto_id=crypto_id,
            sequence_length=sequence_length
        )
        
        # FIX: Check numpy array instead of pandas DataFrame
        if recent_data is None:
            raise ValueError("Insufficient recent data for prediction")
        
        # Process data using the same processor as training
        processed_data, _ = self.data_processor.process_data(recent_data)
        
        if len(processed_data) < sequence_length:
            raise ValueError(f"Need at least {sequence_length} data points for prediction")
        
        # Get the last sequence for prediction
        features = processed_data.select_dtypes(include=[np.number]).values
        
        # Take last sequence_length records
        input_sequence = features[-sequence_length:]
        
        # Reshape for LSTM input (1, sequence_length, n_features)
        return input_sequence.reshape(1, sequence_length, -1)    

    async def _generate_prediction(
        self,
        model: LSTMPredictor,
        input_data: np.ndarray,
        prediction_horizon: int
    ) -> Dict[str, Any]:
        """Generate prediction using the model"""
        
        try:
            # Generate prediction
            predicted_price, confidence = model.predict(
                input_data, 
                return_confidence=True
            )
            
            # Handle prediction horizon (for now, single step prediction)
            # TODO: Implement multi-step prediction for longer horizons
            
            return {
                'price': predicted_price[0] if isinstance(predicted_price, np.ndarray) else predicted_price,
                'raw_confidence': confidence,
                'horizon_hours': prediction_horizon
            }
            
        except Exception as e:
            logger.error(f"Model prediction failed: {str(e)}")
            raise ValueError(f"Prediction generation failed: {str(e)}")
    
    async def _calculate_confidence(
        self,
        model: LSTMPredictor,
        input_data: np.ndarray,
        prediction_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate confidence intervals for prediction"""
        
        try:
            predicted_price = prediction_result['price']
            
            # Simple confidence calculation based on historical model performance
            # TODO: Implement proper uncertainty quantification
            
            # For now, use a simple approach based on model's historical accuracy
            base_confidence = prediction_result.get('raw_confidence', 0.7)
            
            # Calculate confidence interval (±5% for now)
            confidence_range = predicted_price * 0.05
            
            return {
                'confidence': min(base_confidence * 100, 95.0),  # Cap at 95%
                'lower_bound': predicted_price - confidence_range,
                'upper_bound': predicted_price + confidence_range,
                'interval_width': confidence_range * 2
            }
            
        except Exception as e:
            logger.warning(f"Confidence calculation failed: {str(e)}")
            return {
                'confidence': 50.0,  # Default confidence
                'lower_bound': prediction_result['price'] * 0.95,
                'upper_bound': prediction_result['price'] * 1.05,
                'interval_width': prediction_result['price'] * 0.1
            }
    
    async def _get_current_price(self, db: Session, crypto_id: int) -> Decimal:
        """Get current price for the cryptocurrency"""
        
        latest_price = price_data_repository.get_latest_price(db, crypto_id)
        if latest_price:
            return latest_price.close_price
        
        # Fallback: get most recent price
        recent_prices = price_data_repository.get_price_history(
            db=db,
            crypto_id=crypto_id,
            start_date=datetime.now(timezone.utc) - timedelta(hours=24),
            end_date=datetime.now(timezone.utc),
            limit=1
        )
        
        if recent_prices:
            return recent_prices[0].close_price
        
        raise ValueError("No current price data available")
    
    async def _get_cached_prediction(
        self, 
        crypto_symbol: str, 
        prediction_horizon: int
    ) -> Optional[Dict[str, Any]]:
        """Get cached prediction from Redis"""
        
        if not self.redis_client:
            return None
        
        try:
            cache_key = f"prediction:{crypto_symbol}:{prediction_horizon}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                result = json.loads(cached_data)
                result['prediction_metadata']['cache_used'] = True
                logger.debug(f"Cache hit for {crypto_symbol}")
                return result
                
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {str(e)}")
        
        return None
    
    async def _cache_prediction(
        self,
        crypto_symbol: str,
        prediction_horizon: int,
        result: Dict[str, Any]
    ) -> None:
        """Cache prediction result in Redis"""
        
        if not self.redis_client:
            return
        
        try:
            cache_key = f"prediction:{crypto_symbol}:{prediction_horizon}"
            # Cache for 10 minutes (predictions should be fresh)
            cache_ttl = 600
            
            self.redis_client.setex(
                cache_key,
                cache_ttl,
                json.dumps(result, default=str)
            )
            
        except Exception as e:
            logger.warning(f"Cache storage failed: {str(e)}")
    
    async def _store_prediction_result(
        self,
        db: Session,
        crypto_id: int,
        result: Dict[str, Any]
    ) -> None:
        """Store prediction result in database"""
        
        try:
            if not result.get('success', False):
                return
            
            prediction_data = {
                'model_name': result['model_info']['model_id'],
                'predicted_price': result['predicted_price'],
                'confidence_score': result['confidence_score'] / 100,  # Convert to 0-1 scale
                'prediction_horizon': result['prediction_horizon_hours'],
                'target_datetime': datetime.utcnow() + timedelta(
                    hours=result['prediction_horizon_hours']
                ),
                'input_price': result['current_price'],
                'features_used': result['model_info']['features_used'],
                'model_parameters': result['model_info'],
                'notes': f"Auto-generated prediction via PredictionService"
            }
            
            # Store using ml_repository
            ml_repository.store_prediction(
                db=db,
                crypto_id=crypto_id,
                model_id=result['model_info']['model_id'],
                prediction_data=prediction_data
            )
            
        except Exception as e:
            logger.warning(f"Failed to store prediction result: {str(e)}")
    
    async def _fallback_prediction(
        self,
        crypto_symbol: str,
        prediction_horizon: int,
        db: Session
    ) -> Optional[Dict[str, Any]]:
        """Generate fallback prediction using simple methods"""
        
        try:
            logger.info(f"Attempting fallback prediction for {crypto_symbol}")
            
            # Get cryptocurrency
            crypto = cryptocurrency_repository.get_by_symbol(db, crypto_symbol)
            if not crypto:
                return None
            
            # Get recent price data
            recent_prices = price_data_repository.get_price_history(
                db=db,
                crypto_id=crypto.id,
                start_date=datetime.now(timezone.utc) - timedelta(days=7),
                end_date=datetime.now(timezone.utc),
                limit=50
            )
            
            if len(recent_prices) < 5:
                return None
            
            # Simple moving average prediction
            prices = [float(p.close_price) for p in recent_prices[-10:]]
            current_price = prices[-1]
            ma_7 = sum(prices[-7:]) / 7
            ma_3 = sum(prices[-3:]) / 3
            
            # Simple trend-based prediction
            trend = (ma_3 - ma_7) / ma_7
            predicted_price = current_price * (1 + trend * 0.1)  # Damped trend
            
            return {
                'success': True,
                'crypto_symbol': crypto_symbol,
                'current_price': current_price,
                'predicted_price': predicted_price,
                'prediction_horizon_hours': prediction_horizon,
                'confidence_score': 30.0,  # Lower confidence for fallback
                'confidence_interval': {
                    'lower': predicted_price * 0.9,
                    'upper': predicted_price * 1.1
                },
                'model_info': {
                    'model_id': 'fallback_ma',
                    'features_used': 1,
                    'sequence_length': 7,
                    'last_training': 'N/A'
                },
                'prediction_metadata': {
                    'timestamp': datetime.utcnow().isoformat(),
                    'cache_used': False,
                    'fallback_used': True,
                    'method': 'moving_average_trend'
                }
            }
            
        except Exception as e:
            logger.error(f"Fallback prediction failed for {crypto_symbol}: {str(e)}")
            return None
    
    def _get_model_training_date(self, crypto_symbol: str) -> str:
        """Get the last training date for the model"""
        
        try:
            active_model = model_registry.get_active_model(crypto_symbol)
            if active_model and 'created_at' in active_model:
                return active_model['created_at']
        except Exception:
            pass
        
        return 'Unknown'
    
    def _update_response_time(self, response_time: float) -> None:
        """Update average response time metric"""
        
        total_predictions = self.performance_metrics['total_predictions']
        current_avg = self.performance_metrics['average_response_time']
        
        # Calculate new average
        new_avg = (current_avg * total_predictions + response_time) / (total_predictions + 1)
        self.performance_metrics['average_response_time'] = new_avg
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring"""
        
        total_requests = (self.performance_metrics['cache_hits'] + 
                         self.performance_metrics['cache_misses'])
        
        cache_hit_rate = 0.0
        if total_requests > 0:
            cache_hit_rate = self.performance_metrics['cache_hits'] / total_requests * 100
        
        return {
            'total_predictions': self.performance_metrics['total_predictions'],
            'cache_hit_rate': round(cache_hit_rate, 2),
            'average_response_time': round(self.performance_metrics['average_response_time'] * 1000, 2),  # ms
            'error_rate': round(
                self.performance_metrics['error_count'] / 
                max(self.performance_metrics['total_predictions'], 1) * 100, 2
            ),
            'models_cached': len(self.model_cache),
            'redis_available': self.redis_client is not None,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def clear_cache(self) -> Dict[str, Any]:
        """Clear all caches"""
        
        # Clear model cache
        model_count = len(self.model_cache)
        self.model_cache.clear()
        self.model_cache_timestamps.clear()
        
        # Clear Redis cache
        redis_cleared = 0
        if self.redis_client:
            try:
                keys = self.redis_client.keys("prediction:*")
                if keys:
                    redis_cleared = self.redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis cache clear failed: {str(e)}")
        
        return {
            'models_cleared': model_count,
            'redis_keys_cleared': redis_cleared,
            'timestamp': datetime.utcnow().isoformat()
        }


# Global prediction service instance
prediction_service = PredictionService()


# Helper functions for easy access
async def predict_crypto_price(
    crypto_symbol: str,
    prediction_horizon: int = 24,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Simple helper function for single cryptocurrency prediction
    
    Args:
        crypto_symbol: Symbol of cryptocurrency (e.g., 'BTC')
        prediction_horizon: Hours ahead to predict (default: 24)
        use_cache: Whether to use cached predictions
        
    Returns:
        Prediction result dictionary
    """
    return await prediction_service.predict_price(
        crypto_symbol=crypto_symbol,
        prediction_horizon=prediction_horizon,
        use_cache=use_cache
    )


async def predict_multiple_cryptos(
    crypto_symbols: List[str],
    prediction_horizon: int = 24
) -> Dict[str, Any]:
    """
    Simple helper function for multiple cryptocurrency predictions
    
    Args:
        crypto_symbols: List of cryptocurrency symbols
        prediction_horizon: Hours ahead to predict
        
    Returns:
        Batch prediction results
    """
    return await prediction_service.predict_batch(
        crypto_symbols=crypto_symbols,
        prediction_horizon=prediction_horizon
    )


async def get_prediction_performance() -> Dict[str, Any]:
    """Get prediction service performance metrics"""
    return prediction_service.get_performance_metrics()


async def clear_prediction_cache() -> Dict[str, Any]:
    """Clear all prediction caches"""
    return prediction_service.clear_cache()