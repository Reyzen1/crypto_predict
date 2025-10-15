# File: backend/app/repositories/prediction.py
# Prediction repository for ML prediction management

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, and_, or_
from decimal import Decimal

from app.models import Prediction
from backend.app.repositories.base_repository import BaseRepository
from app.schemas.prediction import PredictionCreate, PredictionUpdate


class PredictionRepository(BaseRepository[Prediction, PredictionCreate, PredictionUpdate]):
    """
    Prediction repository with specialized operations for ML predictions
    """

    def __init__(self):
        super().__init__(Prediction)

    def get_by_crypto(
        self, 
        db: Session, 
        crypto_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Prediction]:
        """Get predictions for a specific cryptocurrency"""
        return (
            db.query(Prediction)
            .filter(Prediction.crypto_id == crypto_id)
            .order_by(desc(Prediction.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_user(
        self, 
        db: Session, 
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Prediction]:
        """Get predictions for a specific user"""
        return (
            db.query(Prediction)
            .filter(Prediction.user_id == user_id)
            .order_by(desc(Prediction.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_model(
        self, 
        db: Session, 
        model_name: str,
        model_version: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Prediction]:
        """Get predictions for a specific model"""
        query = db.query(Prediction).filter(Prediction.model_name == model_name)
        
        if model_version:
            query = query.filter(Prediction.model_version == model_version)
        
        return (
            query.order_by(desc(Prediction.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_recent_predictions(
        self, 
        db: Session, 
        days: int = 7,
        limit: int = 100
    ) -> List[Prediction]:
        """Get recent predictions from the last N days"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        return (
            db.query(Prediction)
            .filter(Prediction.created_at >= cutoff_date)
            .order_by(desc(Prediction.created_at))
            .limit(limit)
            .all()
        )

    def get_realized_predictions(
        self, 
        db: Session,
        crypto_id: Optional[int] = None,
        model_name: Optional[str] = None,
        days_back: int = 30
    ) -> List[Prediction]:
        """Get realized predictions for evaluation"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        query = db.query(Prediction).filter(
            and_(
                Prediction.is_realized == True,
                Prediction.created_at >= cutoff_date
            )
        )
        
        if crypto_id:
            query = query.filter(Prediction.crypto_id == crypto_id)
        
        if model_name:
            query = query.filter(Prediction.model_name == model_name)
        
        return query.order_by(desc(Prediction.created_at)).all()

    def get_accuracy_stats(
        self, 
        db: Session,
        crypto_id: Optional[int] = None,
        model_name: Optional[str] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Get accuracy statistics for predictions"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        query = db.query(Prediction).filter(
            and_(
                Prediction.is_realized == True,
                Prediction.created_at >= cutoff_date,
                Prediction.accuracy_percentage.isnot(None)
            )
        )
        
        if crypto_id:
            query = query.filter(Prediction.crypto_id == crypto_id)
        
        if model_name:
            query = query.filter(Prediction.model_name == model_name)
        
        predictions = query.all()
        
        if not predictions:
            return {
                'total_predictions': 0,
                'avg_accuracy': 0.0,
                'accuracy_rate': 0.0
            }
        
        # Calculate statistics
        accuracies = [float(p.accuracy_percentage) for p in predictions]
        accurate_count = sum(1 for p in predictions if p.is_accurate)
        
        return {
            'total_predictions': len(predictions),
            'avg_accuracy': sum(accuracies) / len(accuracies),
            'min_accuracy': min(accuracies),
            'max_accuracy': max(accuracies),
            'accurate_count': accurate_count,
            'accuracy_rate': accurate_count / len(predictions),
            'period_days': days_back
        }

    def delete_old_predictions(
        self, 
        db: Session,
        days_to_keep: int = 90
    ) -> int:
        """Delete old prediction records"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        
        deleted_count = (
            db.query(Prediction)
            .filter(Prediction.created_at < cutoff_date)
            .delete()
        )
        
        db.commit()
        return deleted_count

    def count_total(self, db: Session) -> int:
        """Get total count of all predictions"""
        return db.query(Prediction).count()


# Create global instance
prediction_repository = PredictionRepository()