# File: backend/app/repositories/ml_repository.py
# ML-specific repository for training data and model management

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, and_, or_
from sqlalchemy.exc import IntegrityError

# Import existing models
from app.models import Cryptocurrency, PriceData, Prediction, User
from app.repositories.base import BaseRepository
from app.repositories import prediction_repository  # Add this import
from app.schemas.prediction import PredictionCreate, PredictionUpdate

import logging

logger = logging.getLogger(__name__)


class MLRepository(BaseRepository[PriceData, dict, dict]):
    """
    Repository for ML-specific database operations
    
    This repository provides specialized methods for:
    - Loading training data with proper formatting
    - Storing ML model results and predictions
    - Managing model performance tracking
    - Querying data for ML workflows
    """
    
    def __init__(self):
        super().__init__(PriceData)
    
    def get_training_data_for_crypto(
        self,
        db: Session,
        crypto_id: int,
        days_back: int = 180,
        min_records: int = 50
    ) -> pd.DataFrame:
        """
        Get formatted training data for a cryptocurrency
        
        Args:
            db: Database session
            crypto_id: Cryptocurrency ID
            days_back: Number of days to look back
            min_records: Minimum required records
            
        Returns:
            DataFrame with properly formatted training data
        """
        logger.info(f"Loading training data for crypto_id={crypto_id}, days_back={days_back}")
        
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)
        
        # Query price data - only using columns that exist in your database
        price_records = (
            db.query(PriceData)
            .filter(
                and_(
                    PriceData.crypto_id == crypto_id,
                    PriceData.timestamp >= start_date,
                    PriceData.timestamp <= end_date
                    # Note: removed data_interval and is_validated filters as they don't exist in your DB
                )
            )
            .order_by(asc(PriceData.timestamp))
            .all()
        )
        
        if len(price_records) < min_records:
            logger.warning(f"Insufficient data: {len(price_records)} < {min_records}")
            return pd.DataFrame()
        
        # Convert to DataFrame with ONLY columns that exist in your database
        data = []
        for record in price_records:
            data.append({
                'timestamp': record.timestamp,
                'open_price': float(record.open_price),
                'high_price': float(record.high_price),
                'low_price': float(record.low_price),
                'close_price': float(record.close_price),
                'volume': float(record.volume) if record.volume else 0.0,
                'market_cap': float(record.market_cap) if record.market_cap else 0.0,
                # Note: No data_source or data_interval in your actual DB
            })
        
        df = pd.DataFrame(data)
        
        # Ensure proper datetime handling
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        logger.info(f"Loaded {len(df)} training records for crypto_id={crypto_id}")
        return df
    
    def get_data_quality_stats(
        self,
        db: Session,
        crypto_id: int,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Get data quality statistics for a cryptocurrency
        
        Returns information about data completeness, gaps, and quality
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)
        
        # Total records
        total_records = (
            db.query(func.count(PriceData.id))
            .filter(
                and_(
                    PriceData.crypto_id == crypto_id,
                    PriceData.timestamp >= start_date,
                    PriceData.timestamp <= end_date
                )
            )
            .scalar()
        )
        
        # Validated records - since is_validated doesn't exist, assume all are validated
        validated_records = total_records
        
        # Records with technical indicators - for simple model, we'll skip this
        records_with_rsi = 0  # Since our simple model doesn't have RSI
        
        # Latest record
        latest_record = (
            db.query(PriceData.timestamp)
            .filter(PriceData.crypto_id == crypto_id)
            .order_by(desc(PriceData.timestamp))
            .first()
        )
        
        # Calculate data freshness
        data_freshness_hours = None
        if latest_record:
            latest_timestamp = latest_record[0]
            current_time = datetime.now(timezone.utc)
            
            # Make sure both datetimes are timezone-aware
            if latest_timestamp.tzinfo is None:
                # If latest_timestamp is naive, assume it's UTC
                latest_timestamp = latest_timestamp.replace(tzinfo=timezone.utc)
            
            time_diff = current_time - latest_timestamp
            data_freshness_hours = time_diff.total_seconds() / 3600
        
        return {
            'total_records': total_records,
            'validated_records': validated_records,
            'validation_rate': validated_records / total_records if total_records > 0 else 0,
            'records_with_indicators': records_with_rsi,
            'indicator_coverage': records_with_rsi / total_records if total_records > 0 else 0,
            'latest_timestamp': latest_record[0] if latest_record else None,
            'data_freshness_hours': data_freshness_hours,
            'data_quality_score': self._calculate_quality_score(
                validated_records, total_records, records_with_rsi, data_freshness_hours
            )
        }
    
    def _calculate_quality_score(
        self,
        validated: int,
        total: int,
        with_indicators: int,
        freshness_hours: Optional[float]
    ) -> float:
        """Calculate a quality score (0-1) based on data metrics"""
        if total == 0:
            return 0.0
        
        # Validation score (0-0.4)
        validation_score = (validated / total) * 0.4
        
        # Indicator coverage score (0-0.3)
        indicator_score = (with_indicators / total) * 0.3
        
        # Freshness score (0-0.3)
        freshness_score = 0.3
        if freshness_hours is not None:
            if freshness_hours <= 2:
                freshness_score = 0.3
            elif freshness_hours <= 24:
                freshness_score = 0.2
            elif freshness_hours <= 72:
                freshness_score = 0.1
            else:
                freshness_score = 0.0
        
        return min(1.0, validation_score + indicator_score + freshness_score)
    
    def store_prediction(
        self,
        db: Session,
        crypto_id: int,
        model_id: str,
        prediction_data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Prediction:
        """
        Store a model prediction in the database
        
        Args:
            db: Database session
            crypto_id: Cryptocurrency ID
            model_id: Model identifier
            prediction_data: Dictionary with prediction details
            user_id: Optional user ID
            
        Returns:
            Created Prediction object
        """

        if user_id is None:
            user_id = 1  # Default system user
        
        target_datetime = prediction_data.get('target_datetime', datetime.utcnow() + timedelta(hours=24))
        target_date = target_datetime.date() if hasattr(target_datetime, 'date') else target_datetime
 

        prediction_create = PredictionCreate(
            crypto_id=crypto_id,
            user_id=user_id,
            model_name=prediction_data.get('model_name', 'lstm'),
            predicted_price=Decimal(str(prediction_data['predicted_price'])),
            confidence_score=Decimal(str(prediction_data.get('confidence_score', 0.5))),
            prediction_horizon=prediction_data.get('prediction_horizon', 24),
            target_date=target_date,
            target_datetime=prediction_data.get('target_datetime', datetime.utcnow() + timedelta(hours=24)),
            input_price=Decimal(str(prediction_data.get('input_price', 0.0))),
            input_features=prediction_data.get('input_features'),
            features_used=prediction_data.get('features_used'),
            model_parameters=prediction_data.get('model_parameters'),
            notes=prediction_data.get('notes')
        )
        
        # Use existing prediction repository to create
        from app.repositories.prediction import prediction_repository
        prediction = prediction_repository.create(db, obj_in=prediction_create)
        
        logger.info(f"Stored prediction for crypto_id={crypto_id}, model={model_id}")
        return prediction
    
    def get_model_predictions(
        self,
        db: Session,
        crypto_id: int,
        model_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Prediction]:
        """Get predictions for a cryptocurrency and optionally a specific model"""
        
        query = db.query(Prediction).filter(Prediction.crypto_id == crypto_id)
        
        if model_id:
            query = query.filter(Prediction.notes.contains(model_id))

        return (
            query.order_by(desc(Prediction.created_at))
            .limit(limit)
            .all()
        )
    
    def evaluate_prediction_accuracy(
        self,
        db: Session,
        prediction_id: int,
        actual_price: Decimal
    ) -> Dict[str, Any]:
        """
        Evaluate prediction accuracy and update the prediction record
        
        Args:
            db: Database session
            prediction_id: Prediction ID to evaluate
            actual_price: Actual price that occurred
            
        Returns:
            Dictionary with accuracy metrics
        """
        # Get prediction
        prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
        if not prediction:
            raise ValueError(f"Prediction {prediction_id} not found")
        
        # Calculate accuracy metrics
        predicted = float(prediction.predicted_price)
        actual = float(actual_price)
        
        absolute_error = abs(actual - predicted)
        percentage_error = (absolute_error / actual) * 100 if actual != 0 else 100
        accuracy_percentage = max(0, 100 - percentage_error)
        
        # Update prediction record
        prediction.actual_price = actual_price
        prediction.absolute_error = Decimal(str(absolute_error))
        prediction.accuracy_percentage = Decimal(str(accuracy_percentage))
        prediction.squared_error = Decimal(str((actual - predicted) ** 2))
        prediction.is_realized = True
        prediction.is_accurate = accuracy_percentage >= 90  # 90% threshold
        prediction.evaluated_at = datetime.now(timezone.utc)
        
        db.commit()
        
        metrics = {
            'prediction_id': prediction_id,
            'predicted_price': predicted,
            'actual_price': actual,
            'absolute_error': absolute_error,
            'percentage_error': percentage_error,
            'accuracy_percentage': accuracy_percentage,
            'is_accurate': prediction.is_accurate
        }
        
        logger.info(f"Evaluated prediction {prediction_id}: {accuracy_percentage:.2f}% accuracy")
        return metrics
    
    def get_model_performance_stats(
        self,
        db: Session,
        crypto_id: int,
        model_id: Optional[str] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Get model performance statistics
        
        Returns aggregated performance metrics for model evaluation
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)
        
        # Base query for realized predictions
        query = (
            db.query(Prediction)
            .filter(
                and_(
                    Prediction.crypto_id == crypto_id,
                    Prediction.is_realized == True,
                    Prediction.created_at >= start_date
                )
            )
        )
        
        if model_id:
            query = query.filter(Prediction.notes.contains(model_id))
        
        predictions = query.all()
        
        if not predictions:
            return {
                'total_predictions': 0,
                'message': 'No realized predictions found'
            }
        
        # Calculate aggregate metrics
        accuracies = [float(p.accuracy_percentage) for p in predictions if p.accuracy_percentage]
        errors = [float(p.absolute_error) for p in predictions if p.absolute_error]
        accurate_count = sum(1 for p in predictions if p.is_accurate)
        
        stats = {
            'total_predictions': len(predictions),
            'accurate_predictions': accurate_count,
            'accuracy_rate': accurate_count / len(predictions),
            'avg_accuracy_percentage': sum(accuracies) / len(accuracies) if accuracies else 0,
            'avg_absolute_error': sum(errors) / len(errors) if errors else 0,
            'min_accuracy': min(accuracies) if accuracies else 0,
            'max_accuracy': max(accuracies) if accuracies else 0,
            'evaluation_period_days': days_back,
            'crypto_id': crypto_id,
            'model_id': model_id
        }
        
        return stats
    
    def get_recent_prices_for_features(
        self,
        db: Session,
        crypto_id: int,
        sequence_length: int = 60
    ) -> pd.DataFrame:
        """
        Get recent price data for creating prediction features
        
        Args:
            db: Database session
            crypto_id: Cryptocurrency ID
            sequence_length: Number of recent records needed
            
        Returns:
            DataFrame with recent price data for feature creation
        """
        # Get most recent records - removed is_validated filter
        recent_records = (
            db.query(PriceData)
            .filter(
                and_(
                    PriceData.crypto_id == crypto_id
                    # Note: removed data_interval filter as it doesn't exist
                )
            )
            .order_by(desc(PriceData.timestamp))
            .limit(sequence_length)
            .all()
        )
        
        if not recent_records:
            return pd.DataFrame()
        
        # Convert to DataFrame and reverse order (oldest first)
        data = []
        for record in reversed(recent_records):
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
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df
    
    def cleanup_old_predictions(
        self,
        db: Session,
        crypto_id: int,
        days_to_keep: int = 90
    ) -> Dict[str, Any]:
        """Clean up old prediction records"""
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        
        # Delete old predictions
        deleted_count = (
            db.query(Prediction)
            .filter(
                and_(
                    Prediction.crypto_id == crypto_id,
                    Prediction.created_at < cutoff_date
                )
            )
            .delete()
        )
        
        db.commit()
        
        return {
            'deleted_predictions': deleted_count,
            'cutoff_date': cutoff_date,
            'crypto_id': crypto_id
        }


# Global ML repository instance
ml_repository = MLRepository()