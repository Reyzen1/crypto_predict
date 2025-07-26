# File: backend/app/monitoring/performance_tracker.py
# Comprehensive Performance Tracking System for CryptoPredict

import asyncio
import logging
import time
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta, timezone
from collections import deque, defaultdict
from dataclasses import dataclass
import threading
from sqlalchemy.orm import Session

# Redis for metrics storage
try:
    import redis
    from redis import Redis
except ImportError:
    redis = None

# Database components
from app.core.database import SessionLocal
from app.core.config import settings
from app.repositories import prediction_repository, price_data_repository

logger = logging.getLogger(__name__)


@dataclass
class PredictionMetric:
    """Data class for prediction metrics"""
    crypto_symbol: str
    predicted_price: float
    actual_price: Optional[float]
    prediction_time: datetime
    target_time: datetime
    confidence_score: float
    model_id: str
    error: Optional[float] = None
    percentage_error: Optional[float] = None


@dataclass
class PerformanceMetric:
    """Data class for system performance metrics"""
    timestamp: datetime
    response_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    active_predictions: int
    cache_hit_rate: float
    error_count: int


class PerformanceTracker:
    """
    Comprehensive Performance Tracking System
    
    Features:
    - Real-time prediction accuracy tracking
    - System performance monitoring
    - Historical metrics storage
    - Alert generation
    - Performance analytics
    - Redis-based metrics aggregation
    """
    
    def __init__(self, redis_client: Optional[Redis] = None):
        """Initialize performance tracker"""
        
        # Redis connection for metrics storage
        self.redis_client = redis_client
        if not self.redis_client and redis and hasattr(settings, 'REDIS_URL'):
            try:
                self.redis_client = redis.from_url(settings.REDIS_URL)
                self.redis_client.ping()
                logger.info("Redis connection established for performance tracking")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
                self.redis_client = None
        
        # In-memory storage for recent metrics
        self.prediction_metrics = deque(maxlen=1000)  # Last 1000 predictions
        self.performance_metrics = deque(maxlen=500)  # Last 500 performance readings
        
        # Aggregated metrics by crypto symbol
        self.crypto_metrics = defaultdict(lambda: {
            'total_predictions': 0,
            'accurate_predictions': 0,
            'total_error': 0.0,
            'total_percentage_error': 0.0,
            'accuracy_threshold': 0.05,  # 5% threshold for accuracy
            'last_update': None
        })
        
        # System performance tracking
        self.system_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'peak_response_time': 0.0,
            'start_time': datetime.utcnow(),
            'last_reset': datetime.utcnow()
        }
        
        # Alert thresholds
        self.alert_thresholds = {
            'accuracy_threshold': 0.70,  # 70% accuracy minimum
            'response_time_threshold': 2000,  # 2 seconds
            'error_rate_threshold': 0.10,  # 10% error rate
            'memory_threshold': 1024,  # 1GB memory
            'cpu_threshold': 80  # 80% CPU
        }
        
        # Thread safety
        self._lock = threading.RLock()
        
        logger.info("PerformanceTracker initialized successfully")
    
    async def track_prediction(
        self,
        crypto_symbol: str,
        predicted_price: float,
        confidence_score: float,
        model_id: str,
        prediction_time: Optional[datetime] = None,
        target_time: Optional[datetime] = None,
        actual_price: Optional[float] = None
    ) -> str:
        """
        Track a new prediction for performance monitoring
        
        Args:
            crypto_symbol: Symbol of cryptocurrency
            predicted_price: Predicted price value
            confidence_score: Model confidence (0-1)
            model_id: Identifier of the model used
            prediction_time: When prediction was made
            target_time: Target time for the prediction
            actual_price: Actual price (if known)
            
        Returns:
            Tracking ID for this prediction
        """
        
        if prediction_time is None:
            prediction_time = datetime.utcnow()
        
        if target_time is None:
            target_time = prediction_time + timedelta(hours=24)
        
        # Create prediction metric
        metric = PredictionMetric(
            crypto_symbol=crypto_symbol,
            predicted_price=predicted_price,
            actual_price=actual_price,
            prediction_time=prediction_time,
            target_time=target_time,
            confidence_score=confidence_score,
            model_id=model_id
        )
        
        # Calculate error if actual price is known
        if actual_price is not None:
            metric.error = abs(predicted_price - actual_price)
            metric.percentage_error = (metric.error / actual_price) * 100 if actual_price > 0 else 0
        
        # Generate tracking ID
        tracking_id = f"{crypto_symbol}_{prediction_time.strftime('%Y%m%d_%H%M%S')}_{hash(str(metric)) % 10000}"
        
        with self._lock:
            # Add to in-memory storage
            self.prediction_metrics.append(metric)
            
            # Update crypto-specific metrics
            self._update_crypto_metrics(crypto_symbol, metric)
            
            # Store in Redis if available
            if self.redis_client:
                await self._store_metric_in_redis(tracking_id, metric)
        
        logger.debug(f"Prediction tracked: {tracking_id} for {crypto_symbol}")
        return tracking_id
    
    async def update_prediction_actual(
        self,
        tracking_id: str,
        actual_price: float,
        db: Optional[Session] = None
    ) -> bool:
        """
        Update a tracked prediction with actual price
        
        Args:
            tracking_id: Prediction tracking ID
            actual_price: Actual price observed
            db: Database session
            
        Returns:
            Success status
        """
        
        try:
            # Find the metric in memory first
            metric = None
            with self._lock:
                for m in reversed(self.prediction_metrics):
                    if tracking_id in str(m):  # Simple matching
                        metric = m
                        break
            
            # If not found in memory, try Redis
            if not metric and self.redis_client:
                metric = await self._get_metric_from_redis(tracking_id)
            
            if not metric:
                logger.warning(f"Prediction tracking ID not found: {tracking_id}")
                return False
            
            # Update with actual price
            metric.actual_price = actual_price
            metric.error = abs(metric.predicted_price - actual_price)
            metric.percentage_error = (metric.error / actual_price) * 100 if actual_price > 0 else 0
            
            with self._lock:
                # Update crypto metrics
                self._update_crypto_metrics(metric.crypto_symbol, metric)
                
                # Update in Redis
                if self.redis_client:
                    await self._store_metric_in_redis(tracking_id, metric)
            
            logger.info(f"Updated prediction {tracking_id} with actual price ${actual_price:.2f}, "
                       f"error: {metric.percentage_error:.2f}%")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update prediction actual: {str(e)}")
            return False
    
    async def track_system_performance(
        self,
        response_time_ms: float,
        memory_usage_mb: Optional[float] = None,
        cpu_usage_percent: Optional[float] = None,
        active_predictions: Optional[int] = None,
        cache_hit_rate: Optional[float] = None,
        error_count: Optional[int] = None
    ) -> None:
        """
        Track system performance metrics
        
        Args:
            response_time_ms: Response time in milliseconds
            memory_usage_mb: Memory usage in MB
            cpu_usage_percent: CPU usage percentage
            active_predictions: Number of active predictions
            cache_hit_rate: Cache hit rate (0-1)
            error_count: Number of errors
        """
        
        try:
            # Get system metrics if not provided
            if memory_usage_mb is None:
                memory_usage_mb = self._get_memory_usage()
            
            if cpu_usage_percent is None:
                cpu_usage_percent = self._get_cpu_usage()
            
            # Create performance metric
            perf_metric = PerformanceMetric(
                timestamp=datetime.utcnow(),
                response_time_ms=response_time_ms,
                memory_usage_mb=memory_usage_mb,
                cpu_usage_percent=cpu_usage_percent,
                active_predictions=active_predictions or 0,
                cache_hit_rate=cache_hit_rate or 0.0,
                error_count=error_count or 0
            )
            
            with self._lock:
                # Add to in-memory storage
                self.performance_metrics.append(perf_metric)
                
                # Update system metrics
                self._update_system_metrics(perf_metric)
                
                # Store in Redis
                if self.redis_client:
                    await self._store_performance_in_redis(perf_metric)
                
                # Check for alerts
                await self._check_performance_alerts(perf_metric)
            
        except Exception as e:
            logger.error(f"Failed to track system performance: {str(e)}")
    
    def get_prediction_accuracy(
        self,
        crypto_symbol: Optional[str] = None,
        model_id: Optional[str] = None,
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get prediction accuracy statistics
        
        Args:
            crypto_symbol: Filter by crypto symbol
            model_id: Filter by model ID
            time_range_hours: Time range in hours
            
        Returns:
            Accuracy statistics
        """
        
        cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)
        
        with self._lock:
            # Filter metrics
            filtered_metrics = []
            for metric in self.prediction_metrics:
                if metric.prediction_time < cutoff_time:
                    continue
                
                if crypto_symbol and metric.crypto_symbol != crypto_symbol:
                    continue
                
                if model_id and metric.model_id != model_id:
                    continue
                
                if metric.actual_price is not None:  # Only include completed predictions
                    filtered_metrics.append(metric)
            
            if not filtered_metrics:
                return {
                    'total_predictions': 0,
                    'accurate_predictions': 0,
                    'accuracy_rate': 0.0,
                    'average_error': 0.0,
                    'average_percentage_error': 0.0,
                    'time_range_hours': time_range_hours
                }
            
            # Calculate statistics
            total_predictions = len(filtered_metrics)
            accurate_predictions = sum(
                1 for m in filtered_metrics 
                if m.percentage_error is not None and 
                m.percentage_error <= self.alert_thresholds['accuracy_threshold'] * 100
            )
            
            total_error = sum(m.error for m in filtered_metrics if m.error is not None)
            total_percentage_error = sum(
                m.percentage_error for m in filtered_metrics 
                if m.percentage_error is not None
            )
            
            return {
                'total_predictions': total_predictions,
                'accurate_predictions': accurate_predictions,
                'accuracy_rate': (accurate_predictions / total_predictions) * 100,
                'average_error': total_error / total_predictions,
                'average_percentage_error': total_percentage_error / total_predictions,
                'min_error': min(m.percentage_error for m in filtered_metrics if m.percentage_error is not None),
                'max_error': max(m.percentage_error for m in filtered_metrics if m.percentage_error is not None),
                'crypto_symbol': crypto_symbol,
                'model_id': model_id,
                'time_range_hours': time_range_hours,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_system_performance(self, time_range_hours: int = 1) -> Dict[str, Any]:
        """
        Get system performance statistics
        
        Args:
            time_range_hours: Time range in hours
            
        Returns:
            Performance statistics
        """
        
        cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)
        
        with self._lock:
            # Filter recent performance metrics
            recent_metrics = [
                m for m in self.performance_metrics 
                if m.timestamp >= cutoff_time
            ]
            
            if not recent_metrics:
                return {
                    'message': 'No performance data available for the specified time range',
                    'time_range_hours': time_range_hours
                }
            
            # Calculate statistics
            response_times = [m.response_time_ms for m in recent_metrics]
            memory_usage = [m.memory_usage_mb for m in recent_metrics if m.memory_usage_mb]
            cpu_usage = [m.cpu_usage_percent for m in recent_metrics if m.cpu_usage_percent]
            cache_hit_rates = [m.cache_hit_rate for m in recent_metrics if m.cache_hit_rate]
            error_counts = [m.error_count for m in recent_metrics]
            
            return {
                'time_range_hours': time_range_hours,
                'total_requests': len(recent_metrics),
                'response_time': {
                    'average_ms': sum(response_times) / len(response_times),
                    'min_ms': min(response_times),
                    'max_ms': max(response_times),
                    'p95_ms': self._calculate_percentile(response_times, 95),
                    'p99_ms': self._calculate_percentile(response_times, 99)
                },
                'memory_usage': {
                    'average_mb': sum(memory_usage) / len(memory_usage) if memory_usage else 0,
                    'peak_mb': max(memory_usage) if memory_usage else 0
                },
                'cpu_usage': {
                    'average_percent': sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0,
                    'peak_percent': max(cpu_usage) if cpu_usage else 0
                },
                'cache_performance': {
                    'average_hit_rate': sum(cache_hit_rates) / len(cache_hit_rates) if cache_hit_rates else 0,
                    'min_hit_rate': min(cache_hit_rates) if cache_hit_rates else 0
                },
                'errors': {
                    'total_errors': sum(error_counts),
                    'error_rate': sum(error_counts) / len(recent_metrics) if recent_metrics else 0
                },
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_crypto_performance(self, crypto_symbol: str) -> Dict[str, Any]:
        """
        Get performance statistics for a specific cryptocurrency
        
        Args:
            crypto_symbol: Symbol of cryptocurrency
            
        Returns:
            Crypto-specific performance statistics
        """
        
        with self._lock:
            crypto_data = self.crypto_metrics.get(crypto_symbol, {})
            
            if not crypto_data or crypto_data['total_predictions'] == 0:
                return {
                    'crypto_symbol': crypto_symbol,
                    'message': 'No prediction data available for this cryptocurrency',
                    'total_predictions': 0
                }
            
            # Calculate accuracy rate
            accuracy_rate = 0.0
            if crypto_data['total_predictions'] > 0:
                accuracy_rate = (crypto_data['accurate_predictions'] / crypto_data['total_predictions']) * 100
            
            # Calculate average errors
            avg_error = 0.0
            avg_percentage_error = 0.0
            
            if crypto_data['total_predictions'] > 0:
                avg_error = crypto_data['total_error'] / crypto_data['total_predictions']
                avg_percentage_error = crypto_data['total_percentage_error'] / crypto_data['total_predictions']
            
            return {
                'crypto_symbol': crypto_symbol,
                'total_predictions': crypto_data['total_predictions'],
                'accurate_predictions': crypto_data['accurate_predictions'],
                'accuracy_rate': round(accuracy_rate, 2),
                'average_error': round(avg_error, 4),
                'average_percentage_error': round(avg_percentage_error, 2),
                'accuracy_threshold': crypto_data['accuracy_threshold'] * 100,
                'last_update': crypto_data['last_update'],
                'performance_grade': self._calculate_performance_grade(accuracy_rate),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_alert_status(self) -> Dict[str, Any]:
        """
        Get current alert status based on performance thresholds
        
        Returns:
            Alert status and active alerts
        """
        
        alerts = []
        warning_count = 0
        critical_count = 0
        
        with self._lock:
            # Check prediction accuracy alerts
            for crypto_symbol, data in self.crypto_metrics.items():
                if data['total_predictions'] >= 10:  # Minimum predictions for alert
                    accuracy_rate = (data['accurate_predictions'] / data['total_predictions'])
                    
                    if accuracy_rate < self.alert_thresholds['accuracy_threshold']:
                        alerts.append({
                            'type': 'accuracy',
                            'severity': 'critical' if accuracy_rate < 0.5 else 'warning',
                            'crypto_symbol': crypto_symbol,
                            'current_value': round(accuracy_rate * 100, 2),
                            'threshold': self.alert_thresholds['accuracy_threshold'] * 100,
                            'message': f'Low prediction accuracy for {crypto_symbol}: {accuracy_rate*100:.1f}%'
                        })
                        
                        if accuracy_rate < 0.5:
                            critical_count += 1
                        else:
                            warning_count += 1
            
            # Check system performance alerts
            if self.performance_metrics:
                latest_perf = self.performance_metrics[-1]
                
                # Response time alert
                if latest_perf.response_time_ms > self.alert_thresholds['response_time_threshold']:
                    alerts.append({
                        'type': 'response_time',
                        'severity': 'warning',
                        'current_value': latest_perf.response_time_ms,
                        'threshold': self.alert_thresholds['response_time_threshold'],
                        'message': f'High response time: {latest_perf.response_time_ms:.1f}ms'
                    })
                    warning_count += 1
                
                # Memory alert
                if latest_perf.memory_usage_mb > self.alert_thresholds['memory_threshold']:
                    alerts.append({
                        'type': 'memory',
                        'severity': 'warning',
                        'current_value': latest_perf.memory_usage_mb,
                        'threshold': self.alert_thresholds['memory_threshold'],
                        'message': f'High memory usage: {latest_perf.memory_usage_mb:.1f}MB'
                    })
                    warning_count += 1
                
                # CPU alert
                if latest_perf.cpu_usage_percent > self.alert_thresholds['cpu_threshold']:
                    alerts.append({
                        'type': 'cpu',
                        'severity': 'warning',
                        'current_value': latest_perf.cpu_usage_percent,
                        'threshold': self.alert_thresholds['cpu_threshold'],
                        'message': f'High CPU usage: {latest_perf.cpu_usage_percent:.1f}%'
                    })
                    warning_count += 1
        
        return {
            'alert_status': 'critical' if critical_count > 0 else 'warning' if warning_count > 0 else 'healthy',
            'total_alerts': len(alerts),
            'critical_alerts': critical_count,
            'warning_alerts': warning_count,
            'active_alerts': alerts,
            'thresholds': self.alert_thresholds,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def reset_metrics(self, crypto_symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Reset performance metrics
        
        Args:
            crypto_symbol: Reset only for specific crypto (optional)
            
        Returns:
            Reset confirmation
        """
        
        with self._lock:
            if crypto_symbol:
                # Reset specific crypto metrics
                if crypto_symbol in self.crypto_metrics:
                    old_data = self.crypto_metrics[crypto_symbol].copy()
                    self.crypto_metrics[crypto_symbol] = {
                        'total_predictions': 0,
                        'accurate_predictions': 0,
                        'total_error': 0.0,
                        'total_percentage_error': 0.0,
                        'accuracy_threshold': 0.05,
                        'last_update': None
                    }
                    
                    return {
                        'reset_type': 'crypto_specific',
                        'crypto_symbol': crypto_symbol,
                        'previous_data': old_data,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        'error': f'No metrics found for {crypto_symbol}',
                        'timestamp': datetime.utcnow().isoformat()
                    }
            else:
                # Reset all metrics
                prediction_count = len(self.prediction_metrics)
                performance_count = len(self.performance_metrics)
                crypto_count = len(self.crypto_metrics)
                
                self.prediction_metrics.clear()
                self.performance_metrics.clear()
                self.crypto_metrics.clear()
                
                self.system_metrics = {
                    'total_requests': 0,
                    'successful_requests': 0,
                    'failed_requests': 0,
                    'average_response_time': 0.0,
                    'peak_response_time': 0.0,
                    'start_time': datetime.utcnow(),
                    'last_reset': datetime.utcnow()
                }
                
                return {
                    'reset_type': 'full_reset',
                    'cleared_predictions': prediction_count,
                    'cleared_performance_metrics': performance_count,
                    'cleared_crypto_metrics': crypto_count,
                    'timestamp': datetime.utcnow().isoformat()
                }
    
    def _update_crypto_metrics(self, crypto_symbol: str, metric: PredictionMetric) -> None:
        """Update crypto-specific metrics"""
        
        crypto_data = self.crypto_metrics[crypto_symbol]
        crypto_data['total_predictions'] += 1
        crypto_data['last_update'] = datetime.utcnow().isoformat()
        
        if metric.actual_price is not None and metric.error is not None:
            # Check if prediction is accurate (within threshold)
            if metric.percentage_error <= crypto_data['accuracy_threshold'] * 100:
                crypto_data['accurate_predictions'] += 1
            
            crypto_data['total_error'] += metric.error
            crypto_data['total_percentage_error'] += metric.percentage_error
    
    def _update_system_metrics(self, perf_metric: PerformanceMetric) -> None:
        """Update system-wide metrics"""
        
        self.system_metrics['total_requests'] += 1
        
        # Update average response time
        total_requests = self.system_metrics['total_requests']
        current_avg = self.system_metrics['average_response_time']
        new_avg = (current_avg * (total_requests - 1) + perf_metric.response_time_ms) / total_requests
        self.system_metrics['average_response_time'] = new_avg
        
        # Update peak response time
        if perf_metric.response_time_ms > self.system_metrics['peak_response_time']:
            self.system_metrics['peak_response_time'] = perf_metric.response_time_ms
        
        # Count errors
        if perf_metric.error_count > 0:
            self.system_metrics['failed_requests'] += perf_metric.error_count
        else:
            self.system_metrics['successful_requests'] += 1
    
    async def _store_metric_in_redis(self, tracking_id: str, metric: PredictionMetric) -> None:
        """Store prediction metric in Redis"""
        
        if not self.redis_client:
            return
        
        try:
            metric_data = {
                'crypto_symbol': metric.crypto_symbol,
                'predicted_price': metric.predicted_price,
                'actual_price': metric.actual_price,
                'prediction_time': metric.prediction_time.isoformat(),
                'target_time': metric.target_time.isoformat(),
                'confidence_score': metric.confidence_score,
                'model_id': metric.model_id,
                'error': metric.error,
                'percentage_error': metric.percentage_error
            }
            
            # Store with expiration (30 days)
            key = f"prediction_metric:{tracking_id}"
            self.redis_client.setex(key, 30 * 24 * 3600, json.dumps(metric_data, default=str))
            
        except Exception as e:
            logger.warning(f"Failed to store metric in Redis: {str(e)}")
    
    async def _get_metric_from_redis(self, tracking_id: str) -> Optional[PredictionMetric]:
        """Get prediction metric from Redis"""
        
        if not self.redis_client:
            return None
        
        try:
            key = f"prediction_metric:{tracking_id}"
            data = self.redis_client.get(key)
            
            if data:
                metric_data = json.loads(data)
                return PredictionMetric(
                    crypto_symbol=metric_data['crypto_symbol'],
                    predicted_price=metric_data['predicted_price'],
                    actual_price=metric_data.get('actual_price'),
                    prediction_time=datetime.fromisoformat(metric_data['prediction_time']),
                    target_time=datetime.fromisoformat(metric_data['target_time']),
                    confidence_score=metric_data['confidence_score'],
                    model_id=metric_data['model_id'],
                    error=metric_data.get('error'),
                    percentage_error=metric_data.get('percentage_error')
                )
        except Exception as e:
            logger.warning(f"Failed to get metric from Redis: {str(e)}")
        
        return None
    
    async def _store_performance_in_redis(self, perf_metric: PerformanceMetric) -> None:
        """Store performance metric in Redis"""
        
        if not self.redis_client:
            return
        
        try:
            metric_data = {
                'timestamp': perf_metric.timestamp.isoformat(),
                'response_time_ms': perf_metric.response_time_ms,
                'memory_usage_mb': perf_metric.memory_usage_mb,
                'cpu_usage_percent': perf_metric.cpu_usage_percent,
                'active_predictions': perf_metric.active_predictions,
                'cache_hit_rate': perf_metric.cache_hit_rate,
                'error_count': perf_metric.error_count
            }
            
            # Store in time series with expiration (7 days)
            key = f"performance_metric:{int(perf_metric.timestamp.timestamp())}"
            self.redis_client.setex(key, 7 * 24 * 3600, json.dumps(metric_data))
            
        except Exception as e:
            logger.warning(f"Failed to store performance metric in Redis: {str(e)}")
    
    async def _check_performance_alerts(self, perf_metric: PerformanceMetric) -> None:
        """Check for performance alerts and log them"""
        
        alerts = []
        
        # Check response time
        if perf_metric.response_time_ms > self.alert_thresholds['response_time_threshold']:
            alerts.append(f"High response time: {perf_metric.response_time_ms:.1f}ms")
        
        # Check memory usage
        if perf_metric.memory_usage_mb > self.alert_thresholds['memory_threshold']:
            alerts.append(f"High memory usage: {perf_metric.memory_usage_mb:.1f}MB")
        
        # Check CPU usage
        if perf_metric.cpu_usage_percent > self.alert_thresholds['cpu_threshold']:
            alerts.append(f"High CPU usage: {perf_metric.cpu_usage_percent:.1f}%")
        
        # Log alerts
        for alert in alerts:
            logger.warning(f"Performance Alert: {alert}")
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0.0
        except Exception:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            return 0.0
        except Exception:
            return 0.0
    
    def _calculate_percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * percentile / 100
        f = int(k)
        c = k - f
        
        if f == len(sorted_data) - 1:
            return sorted_data[f]
        
        return sorted_data[f] * (1 - c) + sorted_data[f + 1] * c
    
    def _calculate_performance_grade(self, accuracy_rate: float) -> str:
        """Calculate performance grade based on accuracy"""
        
        if accuracy_rate >= 90:
            return 'A+'
        elif accuracy_rate >= 85:
            return 'A'
        elif accuracy_rate >= 80:
            return 'B+'
        elif accuracy_rate >= 75:
            return 'B'
        elif accuracy_rate >= 70:
            return 'C+'
        elif accuracy_rate >= 65:
            return 'C'
        elif accuracy_rate >= 60:
            return 'D'
        else:
            return 'F'


# Global performance tracker instance
performance_tracker = PerformanceTracker()


# Helper functions for easy access
async def track_prediction_performance(
    crypto_symbol: str,
    predicted_price: float,
    confidence_score: float,
    model_id: str,
    actual_price: Optional[float] = None
) -> str:
    """
    Helper function to track prediction performance
    
    Args:
        crypto_symbol: Symbol of cryptocurrency
        predicted_price: Predicted price
        confidence_score: Model confidence (0-1)
        model_id: Model identifier
        actual_price: Actual price (optional)
        
    Returns:
        Tracking ID
    """
    return await performance_tracker.track_prediction(
        crypto_symbol=crypto_symbol,
        predicted_price=predicted_price,
        confidence_score=confidence_score,
        model_id=model_id,
        actual_price=actual_price
    )


async def update_prediction_with_actual(tracking_id: str, actual_price: float) -> bool:
    """
    Helper function to update prediction with actual price
    
    Args:
        tracking_id: Prediction tracking ID
        actual_price: Actual observed price
        
    Returns:
        Success status
    """
    return await performance_tracker.update_prediction_actual(tracking_id, actual_price)


async def track_system_performance_simple(response_time_ms: float) -> None:
    """
    Simple helper function to track system performance
    
    Args:
        response_time_ms: Response time in milliseconds
    """
    await performance_tracker.track_system_performance(response_time_ms=response_time_ms)


def get_crypto_accuracy(crypto_symbol: str) -> Dict[str, Any]:
    """Get accuracy statistics for a cryptocurrency"""
    return performance_tracker.get_prediction_accuracy(crypto_symbol=crypto_symbol)


def get_overall_performance() -> Dict[str, Any]:
    """Get overall system performance statistics"""
    return performance_tracker.get_system_performance()


def get_performance_alerts() -> Dict[str, Any]:
    """Get current performance alerts"""
    return performance_tracker.get_alert_status()