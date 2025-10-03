# backend/app/repositories/macro/metrics.py
# Repository for macro economic metrics management

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
import logging

from ..base import BaseRepository
from ...models.macro.metrics_snapshot import MetricsSnapshot

# Setup logger
logger = logging.getLogger(__name__)


class MetricsSnapshotRepository(BaseRepository):
    """
    Repository for macro economic metrics snapshots
    """
    
    def __init__(self, db: Session):
        super().__init__(MetricsSnapshot, db)
    
    def get_latest_snapshot(self) -> Optional[MetricsSnapshot]:
        """Get the most recent metrics snapshot"""
        try:
            return self.db.query(MetricsSnapshot).order_by(
                MetricsSnapshot.snapshot_date.desc()
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting latest snapshot: {str(e)}")
            return None
    
    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[MetricsSnapshot]:
        """Get snapshots within date range"""
        try:
            if not start_date or not end_date or start_date > end_date:
                return []
            return self.db.query(MetricsSnapshot).filter(
                MetricsSnapshot.snapshot_date >= start_date,
                MetricsSnapshot.snapshot_date <= end_date
            ).order_by(MetricsSnapshot.snapshot_date.asc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting snapshots by date range: {str(e)}")
            return []
    
    def get_recent_snapshots(self, days: int = 30) -> List[MetricsSnapshot]:
        """Get recent snapshots"""
        try:
            if days <= 0 or days > 1095:  # Max 3 years
                days = 30
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            return self.db.query(MetricsSnapshot).filter(
                MetricsSnapshot.snapshot_date >= cutoff_date
            ).order_by(MetricsSnapshot.snapshot_date.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting recent snapshots: {str(e)}")
            return []
    
    def get_quality_snapshots(self, min_quality_score: float = 0.8) -> List[MetricsSnapshot]:
        """Get high quality snapshots"""
        return self.db.query(MetricsSnapshot).filter(
            MetricsSnapshot.data_quality_score >= min_quality_score,
            MetricsSnapshot.has_data_issues == False
        ).order_by(MetricsSnapshot.snapshot_date.desc()).all()
    
    def get_snapshots_with_issues(self) -> List[MetricsSnapshot]:
        """Get snapshots with data quality issues"""
        return self.db.query(MetricsSnapshot).filter(
            MetricsSnapshot.has_data_issues == True
        ).order_by(MetricsSnapshot.snapshot_date.desc()).all()
    
    def get_fear_greed_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get fear & greed index trend"""
        try:
            if days <= 0 or days > 365:
                days = 30
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            snapshots = self.db.query(MetricsSnapshot).filter(
                MetricsSnapshot.snapshot_date >= cutoff_date,
                MetricsSnapshot.fear_greed_index.isnot(None)
            ).order_by(MetricsSnapshot.snapshot_date.asc()).all()
            
            result = []
            for s in snapshots:
                try:
                    result.append({
                        'date': s.snapshot_date.isoformat(),
                        'fear_greed_index': float(s.fear_greed_index) if s.fear_greed_index is not None else None,
                        'market_sentiment': s.market_sentiment
                    })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error converting fear_greed_index to float: {str(e)}")
                    continue
            return result
        except SQLAlchemyError as e:
            logger.error(f"Error getting fear greed trend: {str(e)}")
            return []
    
    def get_bitcoin_dominance_trend(self, days: int = 90) -> List[Dict[str, Any]]:
        """Get Bitcoin dominance trend"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        snapshots = self.db.query(MetricsSnapshot).filter(
            MetricsSnapshot.snapshot_date >= cutoff_date,
            MetricsSnapshot.btc_dominance.isnot(None)
        ).order_by(MetricsSnapshot.snapshot_date.asc()).all()
        
        return [{
            'date': s.snapshot_date.isoformat(),
            'btc_dominance': float(s.btc_dominance),
            'total_market_cap': float(s.total_crypto_market_cap) if s.total_crypto_market_cap else None
        } for s in snapshots]
    
    def get_market_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get market statistics for period"""
        try:
            if days <= 0 or days > 1095:
                days = 30
            cutoff_date = datetime.utcnow() - timedelta(days=days)
        
            stats = self.db.query(
                func.avg(MetricsSnapshot.fear_greed_index).label('avg_fear_greed'),
                func.max(MetricsSnapshot.fear_greed_index).label('max_fear_greed'),
                func.min(MetricsSnapshot.fear_greed_index).label('min_fear_greed'),
                func.avg(MetricsSnapshot.btc_dominance).label('avg_btc_dominance'),
                func.avg(MetricsSnapshot.total_crypto_market_cap).label('avg_market_cap'),
                func.count(MetricsSnapshot.id).label('total_snapshots'),
                func.avg(MetricsSnapshot.data_quality_score).label('avg_quality')
            ).filter(
                MetricsSnapshot.snapshot_date >= cutoff_date
            ).first()
        
            if not stats:
                return {}
        
        except SQLAlchemyError as e:
            logger.error(f"Error getting market statistics: {str(e)}")
            return {}
        
        try:
            return {
                'average_fear_greed': float(stats.avg_fear_greed) if stats.avg_fear_greed is not None else 0,
                'max_fear_greed': float(stats.max_fear_greed) if stats.max_fear_greed is not None else 0,
                'min_fear_greed': float(stats.min_fear_greed) if stats.min_fear_greed is not None else 0,
                'average_btc_dominance': float(stats.avg_btc_dominance) if stats.avg_btc_dominance is not None else 0,
                'average_market_cap': float(stats.avg_market_cap) if stats.avg_market_cap is not None else 0,
                'total_snapshots': stats.total_snapshots or 0,
                'average_quality_score': float(stats.avg_quality) if stats.avg_quality is not None else 0
            }
        except (ValueError, TypeError) as e:
            logger.error(f"Error converting statistics values: {str(e)}")
            return {
                'average_fear_greed': 0,
                'max_fear_greed': 0,
                'min_fear_greed': 0,
                'average_btc_dominance': 0,
                'average_market_cap': 0,
                'total_snapshots': 0,
                'average_quality_score': 0
            }
    
    def find_market_regime_changes(self, days: int = 90) -> List[Dict[str, Any]]:
        """Identify potential market regime changes"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        snapshots = self.db.query(MetricsSnapshot).filter(
            MetricsSnapshot.snapshot_date >= cutoff_date
        ).order_by(MetricsSnapshot.snapshot_date.asc()).all()
        
        if len(snapshots) < 2:
            return []
        
        regime_changes = []
        current_sentiment = snapshots[0].market_sentiment
        
        for i, snapshot in enumerate(snapshots[1:], 1):
            if (snapshot.market_sentiment and 
                snapshot.market_sentiment != current_sentiment):
                
                regime_changes.append({
                    'date': snapshot.snapshot_date.isoformat(),
                    'from_sentiment': current_sentiment,
                    'to_sentiment': snapshot.market_sentiment,
                    'fear_greed_index': float(snapshot.fear_greed_index) if snapshot.fear_greed_index else None
                })
                current_sentiment = snapshot.market_sentiment
        
        return regime_changes
    
    def cleanup_old_snapshots(self, days_to_keep: int = 365) -> int:
        """Remove old snapshots beyond retention period"""
        try:
            if days_to_keep <= 0 or days_to_keep > 3650:  # Max 10 years
                return 0
                
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            deleted_count = self.db.query(MetricsSnapshot).filter(
                MetricsSnapshot.snapshot_date < cutoff_date
            ).delete()
            
            self.db.commit()
            logger.info(f"Cleaned up {deleted_count} old snapshots")
            return deleted_count
        except SQLAlchemyError as e:
            logger.error(f"Error cleaning up old snapshots: {str(e)}")
            self.db.rollback()
            return 0
