# backend/app/repositories/macro/regime_analysis.py
# Repository for AI market regime analysis

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
import logging

from ..base_repository import BaseRepository
from app.models.macro.regime_analysis import AIRegimeAnalysis

# Setup logger
logger = logging.getLogger(__name__)


class AIRegimeAnalysisRepository(BaseRepository):
    """
    Repository for AI-driven market regime analysis
    """
    
    def __init__(self, db: Session):
        super().__init__(AIRegimeAnalysis, db)
    
    def get_latest_analysis(self) -> Optional[AIRegimeAnalysis]:
        """Get the most recent regime analysis"""
        try:
            return self.db.query(AIRegimeAnalysis).order_by(
                AIRegimeAnalysis.analysis_timestamp.desc()
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting latest analysis: {str(e)}")
            return None
    
    def get_by_regime(self, regime: str) -> List[AIRegimeAnalysis]:
        """Get analyses for specific market regime"""
        try:
            if not regime or not regime.strip():
                return []
            return self.db.query(AIRegimeAnalysis).filter(
                AIRegimeAnalysis.detected_regime == regime.strip()
            ).order_by(AIRegimeAnalysis.analysis_timestamp.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting analyses by regime '{regime}': {str(e)}")
            return []
    
    def get_high_confidence_analyses(self, min_confidence: float = 0.8) -> List[AIRegimeAnalysis]:
        """Get high confidence regime analyses"""
        try:
            if min_confidence < 0 or min_confidence > 1:
                min_confidence = 0.8
            return self.db.query(AIRegimeAnalysis).filter(
                AIRegimeAnalysis.confidence_score >= min_confidence
            ).order_by(AIRegimeAnalysis.analysis_timestamp.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting high confidence analyses: {str(e)}")
            return []
    
    def get_regime_changes(self, days: int = 90) -> List[Dict[str, Any]]:
        """Get regime changes over time period"""
        try:
            if days <= 0 or days > 1095:  # Max 3 years
                days = 90
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            analyses = self.db.query(AIRegimeAnalysis).filter(
                AIRegimeAnalysis.analysis_timestamp >= cutoff_date
            ).order_by(AIRegimeAnalysis.analysis_timestamp.asc()).all()
            
            if len(analyses) < 2:
                return []
            
            regime_changes = []
            current_regime = analyses[0].detected_regime
            
            for analysis in analyses[1:]:
                try:
                    if analysis.detected_regime != current_regime:
                        regime_changes.append({
                            'timestamp': analysis.analysis_timestamp.isoformat(),
                            'from_regime': current_regime,
                            'to_regime': analysis.detected_regime,
                            'confidence': float(analysis.confidence_score) if analysis.confidence_score is not None else 0.0,
                            'model_used': analysis.model_name
                        })
                        current_regime = analysis.detected_regime
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error processing regime change data: {str(e)}")
                    continue
            
            return regime_changes
        except SQLAlchemyError as e:
            logger.error(f"Error getting regime changes: {str(e)}")
            return []
    
    def get_by_model(self, model_name: str, limit: int = 100) -> List[AIRegimeAnalysis]:
        """Get analyses by specific AI model"""
        try:
            if not model_name or not model_name.strip():
                return []
            if limit <= 0 or limit > 1000:
                limit = 100
            return self.db.query(AIRegimeAnalysis).filter(
                AIRegimeAnalysis.model_name == model_name.strip()
            ).order_by(AIRegimeAnalysis.analysis_timestamp.desc()).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting analyses by model '{model_name}': {str(e)}")
            return []
    
    def get_consensus_analysis(self, hours: int = 24) -> Dict[str, Any]:
        """Get consensus regime from recent analyses"""
        try:
            if hours <= 0 or hours > 168:  # Max 1 week
                hours = 24
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
            # Get recent analyses grouped by regime
            regime_counts = self.db.query(
                AIRegimeAnalysis.detected_regime,
                func.count(AIRegimeAnalysis.id).label('count'),
                func.avg(AIRegimeAnalysis.confidence_score).label('avg_confidence'),
                func.max(AIRegimeAnalysis.analysis_timestamp).label('latest_time')
            ).filter(
                AIRegimeAnalysis.analysis_timestamp >= cutoff_time
            ).group_by(
                AIRegimeAnalysis.detected_regime
            ).order_by(
                func.count(AIRegimeAnalysis.id).desc()
            ).all()
        
            if not regime_counts:
                return {}
        
            # Calculate consensus
            total_analyses = sum(r.count for r in regime_counts)
            consensus_regime = regime_counts[0]
        
            return {
                'consensus_regime': consensus_regime.detected_regime,
                'consensus_confidence': float(consensus_regime.avg_confidence) if consensus_regime.avg_confidence is not None else 0.0,
                'agreement_percentage': round((consensus_regime.count / total_analyses * 100), 2) if total_analyses > 0 else 0,
                'total_analyses': total_analyses,
                'latest_update': consensus_regime.latest.isoformat(),
                'alternative_regimes': [{
                    'regime': r.detected_regime,
                    'confidence': float(r.avg_confidence) if r.avg_confidence is not None else 0.0,
                    'percentage': round((r.count / total_analyses * 100), 2) if total_analyses > 0 else 0
                } for r in regime_counts[1:]]
            }
        except (ValueError, TypeError) as e:
            logger.error(f"Error processing consensus analysis data: {str(e)}")
            return {}
        except SQLAlchemyError as e:
            logger.error(f"Error getting consensus analysis: {str(e)}")
            return {}
    
    def get_model_performance(self, model_name: str, days: int = 30) -> Dict[str, Any]:
        """Get performance statistics for a specific model"""
        try:
            if not model_name or not model_name.strip():
                return {}
            if days <= 0 or days > 365:
                days = 30
            cutoff_date = datetime.utcnow() - timedelta(days=days)
        
            stats = self.db.query(
                func.count(AIRegimeAnalysis.id).label('total_analyses'),
                func.avg(AIRegimeAnalysis.confidence_score).label('avg_confidence'),
                func.max(AIRegimeAnalysis.confidence_score).label('max_confidence'),
                func.min(AIRegimeAnalysis.confidence_score).label('min_confidence'),
                func.avg(AIRegimeAnalysis.processing_time_sec).label('avg_processing_time')
            ).filter(
                AIRegimeAnalysis.model_name == model_name,
                AIRegimeAnalysis.analysis_timestamp >= cutoff_date
            ).first()
        
            if not stats:
                return {}
        
            return {
                'model_name': model_name,
                'total_analyses': stats.total_analyses or 0,
                'average_confidence': float(stats.avg_confidence) if stats.avg_confidence is not None else 0,
                'max_confidence': float(stats.max_confidence) if stats.max_confidence is not None else 0,
                'min_confidence': float(stats.min_confidence) if stats.min_confidence is not None else 0,
                'average_processing_time': float(stats.avg_processing_time) if stats.avg_processing_time is not None else 0
            }
        except (ValueError, TypeError) as e:
            logger.error(f"Error converting model performance statistics: {str(e)}")
            return {}
        except SQLAlchemyError as e:
            logger.error(f"Error getting model performance: {str(e)}")
            return {}
        except (ValueError, TypeError) as e:
            logger.error(f"Error converting model performance statistics: {str(e)}")
            return {}
        except SQLAlchemyError as e:
            logger.error(f"Error getting model performance: {str(e)}")
            return {}
    
    def get_regime_distribution(self, days: int = 30) -> Dict[str, Any]:
        """Get distribution of detected regimes"""
        try:
            if days <= 0 or days > 365:
                days = 30
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            distribution = self.db.query(
                AIRegimeAnalysis.detected_regime,
                func.count(AIRegimeAnalysis.id).label('count'),
                func.avg(AIRegimeAnalysis.confidence_score).label('avg_confidence')
            ).filter(
                AIRegimeAnalysis.analysis_timestamp >= cutoff_date
            ).group_by(
                AIRegimeAnalysis.detected_regime
            ).order_by(
                func.count(AIRegimeAnalysis.id).desc()
            ).all()
            
            total = sum(d.count for d in distribution)
            
            result = []
            for d in distribution:
                try:
                    result.append({
                        'regime': d.detected_regime,
                        'count': d.count,
                        'percentage': round((d.count / total * 100), 2) if total > 0 else 0,
                        'avg_confidence': float(d.avg_confidence) if d.avg_confidence is not None else 0.0
                    })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error processing regime distribution data: {str(e)}")
                    continue
            
            return {
                'total_analyses': total,
                'regime_distribution': result
            }
        except SQLAlchemyError as e:
            logger.error(f"Error getting regime distribution: {str(e)}")
            return {'total_analyses': 0, 'regime_distribution': []}
    
    def cleanup_old_analyses(self, days_to_keep: int = 90) -> int:
        """Remove old analyses beyond retention period"""
        try:
            if days_to_keep <= 0 or days_to_keep > 1095:  # Max 3 years
                return 0
                
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            deleted_count = self.db.query(AIRegimeAnalysis).filter(
                AIRegimeAnalysis.analysis_timestamp < cutoff_date
            ).delete()
            
            self.db.commit()
            logger.info(f"Cleaned up {deleted_count} old regime analyses")
            return deleted_count
        except SQLAlchemyError as e:
            logger.error(f"Error cleaning up old analyses: {str(e)}")
            self.db.rollback()
            return 0
