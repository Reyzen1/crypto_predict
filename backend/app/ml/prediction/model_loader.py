# File: backend/app/ml/prediction/model_loader.py
# Model Loading and Management System for CryptoPredict

import os
import logging
import time
import threading
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import json
import pickle

# Import ML components
from app.ml.models.lstm_predictor import LSTMPredictor
from app.ml.config.ml_config import ml_config, model_registry
from app.ml.utils.model_utils import ModelPersistence

logger = logging.getLogger(__name__)


class ModelLoader:
    """
    Advanced Model Loading and Management System
    
    Features:
    - Efficient model loading with caching
    - Hot-swapping of models
    - Memory management and optimization
    - Model health checking
    - Automatic cleanup of old models
    - Thread-safe operations
    """
    
    def __init__(self):
        """Initialize model loader"""
        self.models_cache = {}
        self.cache_timestamps = {}
        self.model_metadata = {}
        
        # Configuration
        self.max_cached_models = ml_config.max_cached_models if hasattr(ml_config, 'max_cached_models') else 5
        self.cache_ttl = 3600  # 1 hour
        self.memory_limit_mb = 1024  # 1GB limit for cached models
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Model persistence utility
        self.model_persistence = ModelPersistence()
        
        # Performance tracking
        self.load_stats = {
            'total_loads': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'load_times': [],
            'memory_usage_mb': 0
        }
        
        logger.info("ModelLoader initialized successfully")
    
    def load_model(
        self, 
        crypto_symbol: str,
        model_id: Optional[str] = None,
        force_reload: bool = False
    ) -> Optional[LSTMPredictor]:
        """
        Load model for cryptocurrency with advanced caching
        
        Args:
            crypto_symbol: Symbol of cryptocurrency
            model_id: Specific model ID to load (optional)
            force_reload: Force reload even if cached
            
        Returns:
            Loaded LSTM model or None if failed
        """
        start_time = time.time()
        
        with self._lock:
            try:
                # Determine which model to load
                if model_id is None:
                    # Get active model from registry
                    active_model = model_registry.get_active_model(crypto_symbol)
                    if not active_model:
                        logger.warning(f"No active model found for {crypto_symbol}")
                        return None
                    model_id = active_model.get('model_id')
                    model_path = active_model.get('model_path')
                else:
                    # Get specific model info
                    model_info = model_registry.get_model_info(model_id)
                    if not model_info:
                        logger.warning(f"Model {model_id} not found in registry")
                        return None
                    model_path = model_info.get('model_path')
                
                if not model_path:
                    logger.error(f"No model path found for {model_id}")
                    return None
                
                # Check cache first (unless force reload)
                cache_key = f"{crypto_symbol}:{model_id}"
                
                if not force_reload and cache_key in self.models_cache:
                    # Check if cache is still valid
                    cache_time = self.cache_timestamps.get(cache_key, 0)
                    if time.time() - cache_time < self.cache_ttl:
                        # Verify model is still healthy
                        model = self.models_cache[cache_key]
                        if self._verify_model_health(model):
                            self.load_stats['cache_hits'] += 1
                            logger.debug(f"Model cache hit for {crypto_symbol}:{model_id}")
                            return model
                        else:
                            # Remove unhealthy model from cache
                            self._remove_from_cache(cache_key)
                
                # Load model from disk
                self.load_stats['cache_misses'] += 1
                model = self._load_model_from_disk(model_path, crypto_symbol)
                
                if model:
                    # Add to cache
                    self._add_to_cache(cache_key, model, model_path)
                    load_time = time.time() - start_time
                    self.load_stats['load_times'].append(load_time)
                    self.load_stats['total_loads'] += 1
                    
                    logger.info(f"Model loaded for {crypto_symbol}:{model_id} "
                               f"in {load_time:.3f}s")
                
                return model
                
            except Exception as e:
                logger.error(f"Failed to load model for {crypto_symbol}: {str(e)}")
                return None
    
    def _load_model_from_disk(
        self, 
        model_path: str, 
        crypto_symbol: str
    ) -> Optional[LSTMPredictor]:
        """Load model from disk with error handling"""
        
        try:
            # Verify file exists
            if not os.path.exists(model_path):
                logger.error(f"Model file not found: {model_path}")
                return None
            
            # Check file size and age
            file_stats = os.stat(model_path)
            file_size_mb = file_stats.st_size / (1024 * 1024)
            file_age_days = (time.time() - file_stats.st_mtime) / (24 * 3600)
            
            logger.debug(f"Loading model: {model_path} "
                        f"(size: {file_size_mb:.2f}MB, age: {file_age_days:.1f} days)")
            
            # Create LSTM predictor instance
            model = LSTMPredictor()
            
            # Load the model
            model.load_model(model_path)
            
            # Verify model is functional
            if not self._verify_model_functionality(model):
                logger.error(f"Model verification failed for {model_path}")
                return None
            
            logger.debug(f"Model loaded successfully from {model_path}")
            return model
            
        except Exception as e:
            logger.error(f"Error loading model from {model_path}: {str(e)}")
            return None
    
    def _add_to_cache(
        self, 
        cache_key: str, 
        model: LSTMPredictor, 
        model_path: str
    ) -> None:
        """Add model to cache with memory management"""
        
        # Check memory limits before adding
        current_memory = self._estimate_memory_usage()
        
        # If we're near the limit, clean up old models
        if (current_memory > self.memory_limit_mb or 
            len(self.models_cache) >= self.max_cached_models):
            self._cleanup_old_models()
        
        # Add to cache
        self.models_cache[cache_key] = model
        self.cache_timestamps[cache_key] = time.time()
        
        # Store metadata
        self.model_metadata[cache_key] = {
            'model_path': model_path,
            'loaded_at': datetime.utcnow(),
            'access_count': 0,
            'last_health_check': time.time()
        }
        
        # Update memory usage
        self._update_memory_usage()
        
        logger.debug(f"Model cached: {cache_key}")
    
    def _remove_from_cache(self, cache_key: str) -> None:
        """Remove model from cache"""
        
        if cache_key in self.models_cache:
            del self.models_cache[cache_key]
        
        if cache_key in self.cache_timestamps:
            del self.cache_timestamps[cache_key]
        
        if cache_key in self.model_metadata:
            del self.model_metadata[cache_key]
        
        self._update_memory_usage()
        logger.debug(f"Model removed from cache: {cache_key}")
    
    def _cleanup_old_models(self) -> None:
        """Clean up old or least used models from cache"""
        
        if not self.models_cache:
            return
        
        # Sort by last access time (oldest first)
        sorted_models = sorted(
            self.cache_timestamps.items(),
            key=lambda x: x[1]
        )
        
        # Remove oldest models if over limit
        models_to_remove = []
        
        # Remove expired models
        current_time = time.time()
        for cache_key, timestamp in sorted_models:
            if current_time - timestamp > self.cache_ttl:
                models_to_remove.append(cache_key)
        
        # Remove excess models if still over limit
        remaining_count = len(self.models_cache) - len(models_to_remove)
        if remaining_count > self.max_cached_models:
            excess_count = remaining_count - self.max_cached_models
            for i in range(excess_count):
                if i < len(sorted_models):
                    cache_key = sorted_models[i][0]
                    if cache_key not in models_to_remove:
                        models_to_remove.append(cache_key)
        
        # Remove selected models
        for cache_key in models_to_remove:
            self._remove_from_cache(cache_key)
        
        if models_to_remove:
            logger.info(f"Cleaned up {len(models_to_remove)} cached models")
    
    def _verify_model_health(self, model: LSTMPredictor) -> bool:
        """Verify that cached model is still healthy"""
        
        try:
            # Basic checks
            if not model or not model.is_trained:
                return False
            
            if not hasattr(model, 'model') or model.model is None:
                return False
            
            # Try a simple prediction with dummy data
            if hasattr(model, 'sequence_length') and hasattr(model, 'n_features'):
                import numpy as np
                dummy_input = np.random.random((1, model.sequence_length, model.n_features))
                _ = model.model.predict(dummy_input, verbose=0)
                return True
            
            return True
            
        except Exception as e:
            logger.warning(f"Model health check failed: {str(e)}")
            return False
    
    def _verify_model_functionality(self, model: LSTMPredictor) -> bool:
        """Verify that loaded model is functional"""
        
        try:
            # Check basic attributes
            if not model.is_trained:
                logger.warning("Model is not marked as trained")
                return False
            
            if not hasattr(model, 'model') or model.model is None:
                logger.warning("Model does not have Keras model")
                return False
            
            # Check scalers
            if not hasattr(model, 'scaler') or model.scaler is None:
                logger.warning("Model missing target scaler")
                return False
            
            # Try prediction with dummy data
            if (hasattr(model, 'sequence_length') and 
                hasattr(model, 'n_features') and
                model.sequence_length > 0 and 
                model.n_features > 0):
                
                import numpy as np
                dummy_input = np.random.random((1, model.sequence_length, model.n_features))
                prediction = model.model.predict(dummy_input, verbose=0)
                
                if prediction is None or len(prediction) == 0:
                    logger.warning("Model prediction test failed")
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Model functionality verification failed: {str(e)}")
            return False
    
    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage of cached models in MB"""
        
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
            return memory_mb
        except ImportError:
            # Fallback: rough estimate based on number of models
            return len(self.models_cache) * 50  # Assume 50MB per model
    
    def _update_memory_usage(self) -> None:
        """Update memory usage statistics"""
        self.load_stats['memory_usage_mb'] = self._estimate_memory_usage()
    
    def get_cached_models(self) -> List[Dict[str, Any]]:
        """Get information about currently cached models"""
        
        with self._lock:
            cached_models = []
            
            for cache_key, model in self.models_cache.items():
                metadata = self.model_metadata.get(cache_key, {})
                
                cached_models.append({
                    'cache_key': cache_key,
                    'crypto_symbol': cache_key.split(':')[0],
                    'model_id': cache_key.split(':')[1] if ':' in cache_key else 'unknown',
                    'loaded_at': metadata.get('loaded_at'),
                    'model_path': metadata.get('model_path'),
                    'access_count': metadata.get('access_count', 0),
                    'is_healthy': self._verify_model_health(model),
                    'cache_age_seconds': time.time() - self.cache_timestamps.get(cache_key, 0)
                })
            
            return cached_models
    
    def reload_model(self, crypto_symbol: str, model_id: Optional[str] = None) -> bool:
        """Force reload a model (clear cache and reload)"""
        
        with self._lock:
            # Remove from cache if exists
            cache_key = f"{crypto_symbol}:{model_id or 'active'}"
            if cache_key in self.models_cache:
                self._remove_from_cache(cache_key)
            
            # Load fresh model
            model = self.load_model(crypto_symbol, model_id, force_reload=True)
            return model is not None
    
    def clear_cache(self) -> Dict[str, Any]:
        """Clear all cached models"""
        
        with self._lock:
            cleared_count = len(self.models_cache)
            
            self.models_cache.clear()
            self.cache_timestamps.clear()
            self.model_metadata.clear()
            
            self._update_memory_usage()
            
            logger.info(f"Cleared {cleared_count} cached models")
            
            return {
                'cleared_models': cleared_count,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get loader performance statistics"""
        
        total_requests = self.load_stats['cache_hits'] + self.load_stats['cache_misses']
        cache_hit_rate = 0.0
        average_load_time = 0.0
        
        if total_requests > 0:
            cache_hit_rate = self.load_stats['cache_hits'] / total_requests * 100
        
        if self.load_stats['load_times']:
            average_load_time = sum(self.load_stats['load_times']) / len(self.load_stats['load_times'])
        
        return {
            'total_loads': self.load_stats['total_loads'],
            'cache_hit_rate': round(cache_hit_rate, 2),
            'cache_hits': self.load_stats['cache_hits'],
            'cache_misses': self.load_stats['cache_misses'],
            'average_load_time_seconds': round(average_load_time, 3),
            'cached_models_count': len(self.models_cache),
            'memory_usage_mb': round(self.load_stats['memory_usage_mb'], 2),
            'cache_ttl_seconds': self.cache_ttl,
            'max_cached_models': self.max_cached_models,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all cached models"""
        
        with self._lock:
            healthy_count = 0
            unhealthy_models = []
            
            for cache_key, model in self.models_cache.items():
                if self._verify_model_health(model):
                    healthy_count += 1
                    # Update last health check time
                    if cache_key in self.model_metadata:
                        self.model_metadata[cache_key]['last_health_check'] = time.time()
                else:
                    unhealthy_models.append(cache_key)
            
            # Remove unhealthy models
            for cache_key in unhealthy_models:
                self._remove_from_cache(cache_key)
                logger.warning(f"Removed unhealthy model from cache: {cache_key}")
            
            return {
                'total_cached': len(self.models_cache) + len(unhealthy_models),
                'healthy_models': healthy_count,
                'unhealthy_removed': len(unhealthy_models),
                'cache_health_percentage': round(
                    healthy_count / max(len(self.models_cache) + len(unhealthy_models), 1) * 100, 2
                ),
                'memory_usage_mb': round(self.load_stats['memory_usage_mb'], 2),
                'timestamp': datetime.utcnow().isoformat()
            }


# Global model loader instance
model_loader = ModelLoader()


# Helper functions for easy access
def load_crypto_model(
    crypto_symbol: str,
    model_id: Optional[str] = None,
    force_reload: bool = False
) -> Optional[LSTMPredictor]:
    """
    Helper function to load a cryptocurrency model
    
    Args:
        crypto_symbol: Symbol of cryptocurrency
        model_id: Specific model ID (optional)
        force_reload: Force reload from disk
        
    Returns:
        Loaded LSTM model or None
    """
    return model_loader.load_model(crypto_symbol, model_id, force_reload)


def get_loader_stats() -> Dict[str, Any]:
    """Get model loader performance statistics"""
    return model_loader.get_performance_stats()


def clear_model_cache() -> Dict[str, Any]:
    """Clear all cached models"""
    return model_loader.clear_cache()


def check_model_health() -> Dict[str, Any]:
    """Perform health check on cached models"""
    return model_loader.health_check()