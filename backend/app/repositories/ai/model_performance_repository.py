# backend/app/repositories/ai/performance.py
# Repository for model performance evaluations

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, timedelta

from ..base_repository import BaseRepository
from ...models.ai.performance import ModelPerformance


class ModelPerformanceRepository(BaseRepository):
    """
    Repository for model performance evaluation management
    """
    
    def __init__(self, db: Session):
        super().__init__(ModelPerformance, db)
    
    def get_by_model(self, model_id: int, limit: int = 10) -> List[ModelPerformance]:
        """Get recent evaluations for a model"""
        return self.db.query(ModelPerformance).filter(
            ModelPerformance.model_id == model_id
        ).order_by(ModelPerformance.evaluation_date.desc()).limit(limit).all()
    
    def get_latest_by_model(self, model_id: int) -> Optional[ModelPerformance]:
        """Get latest evaluation for a model"""
        return self.db.query(ModelPerformance).filter(
            ModelPerformance.model_id == model_id
        ).order_by(ModelPerformance.evaluation_date.desc()).first()
    
    def get_high_performance_models(self, min_grade: str = 'B') -> List[ModelPerformance]:
        """Get high performance model evaluations"""
        grade_order = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'F': 1}
        min_grade_value = grade_order.get(min_grade, 4)
        
        return self.db.query(ModelPerformance).filter(
            ModelPerformance.performance_grade.in_(
                [g for g, v in grade_order.items() if v >= min_grade_value]
            )
        ).order_by(ModelPerformance.composite_score.desc()).all()
    
    def get_by_job(self, job_id: int) -> List[ModelPerformance]:
        """Get evaluations from specific job"""
        return self.db.query(ModelPerformance).filter(
            ModelPerformance.source_job_id == job_id
        ).order_by(ModelPerformance.evaluation_date.desc()).all()
    
    def get_performance_trends(self, model_id: int, days: int = 30) -> List[ModelPerformance]:
        """Get performance trend for a model over time"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.db.query(ModelPerformance).filter(
            ModelPerformance.model_id == model_id,
            ModelPerformance.evaluation_date >= cutoff_date
        ).order_by(ModelPerformance.evaluation_date.asc()).all()
    
    def get_by_market_regime(self, regime: str) -> List[ModelPerformance]:
        """Get evaluations by market regime"""
        return self.db.query(ModelPerformance).filter(
            ModelPerformance.market_regime == regime
        ).order_by(ModelPerformance.evaluation_date.desc()).all()
    
    def get_threshold_compliant_models(self) -> List[ModelPerformance]:
        """Get models meeting minimum thresholds"""
        return self.db.query(ModelPerformance).filter(
            ModelPerformance.meets_min_threshold == True
        ).order_by(ModelPerformance.composite_score.desc()).all()
    
    def get_performance_statistics(self, model_id: int = None) -> Dict[str, Any]:
        """Get performance statistics"""
        query = self.db.query(ModelPerformance)
        if model_id:
            query = query.filter(ModelPerformance.model_id == model_id)
        
        stats = query.with_entities(
            func.avg(ModelPerformance.composite_score).label('avg_score'),
            func.max(ModelPerformance.composite_score).label('max_score'),
            func.min(ModelPerformance.composite_score).label('min_score'),
            func.count(ModelPerformance.id).label('total_evaluations'),
            func.sum(func.case((ModelPerformance.meets_min_threshold == True, 1), else_=0)).label('threshold_compliant')
        ).first()
        
        if not stats:
            return {}
        
        return {
            'average_score': float(stats.avg_score) if stats.avg_score else 0,
            'max_score': float(stats.max_score) if stats.max_score else 0,
            'min_score': float(stats.min_score) if stats.min_score else 0,
            'total_evaluations': stats.total_evaluations or 0,
            'threshold_compliant': stats.threshold_compliant or 0,
            'compliance_rate': (stats.threshold_compliant / stats.total_evaluations * 100) if stats.total_evaluations > 0 else 0
        }
    
    def detect_performance_degradation(self, model_id: int, lookback_days: int = 14) -> Dict[str, Any]:
        """Detect performance degradation trends"""
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
        
        recent_evals = self.db.query(ModelPerformance).filter(
            ModelPerformance.model_id == model_id,
            ModelPerformance.evaluation_date >= cutoff_date
        ).order_by(ModelPerformance.evaluation_date.asc()).all()
        
        if len(recent_evals) < 3:
            return {'status': 'insufficient_data', 'evaluations_count': len(recent_evals)}
        
        # Calculate trend
        scores = [float(e.composite_score) for e in recent_evals if e.composite_score]
        if len(scores) < 3:
            return {'status': 'insufficient_scores'}
        
        # Simple linear regression for trend detection
        n = len(scores)
        x_values = list(range(n))
        
        sum_x = sum(x_values)
        sum_y = sum(scores)
        sum_xy = sum(x * y for x, y in zip(x_values, scores))
        sum_x_squared = sum(x * x for x in x_values)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x_squared - sum_x * sum_x)
        
        # Calculate degradation metrics
        latest_score = scores[-1]
        avg_score = sum(scores) / len(scores)
        score_volatility = (max(scores) - min(scores)) / avg_score * 100
        
        degradation_detected = slope < -0.01 and latest_score < avg_score * 0.95
        
        return {
            'status': 'analysis_complete',
            'degradation_detected': degradation_detected,
            'trend_slope': round(slope, 4),
            'latest_score': round(latest_score, 3),
            'average_score': round(avg_score, 3),
            'score_volatility_pct': round(score_volatility, 2),
            'evaluation_period_days': lookback_days,
            'evaluations_analyzed': len(scores),
            'recommendation': 'retrain_model' if degradation_detected else 'monitor_continue'
        }
    
    def get_benchmark_comparison(self, model_id: int, benchmark_type: str = 'peer_average') -> Dict[str, Any]:
        """Compare model performance against benchmarks"""
        model_performance = self.get_latest_by_model(model_id)
        if not model_performance:
            return {'error': 'No performance data found for model'}
        
        # Get model info for comparison context
        from ...models.ai.model import AIModel
        model = self.db.query(AIModel).filter(AIModel.id == model_id).first()
        
        if not model:
            return {'error': 'Model not found'}
        
        if benchmark_type == 'peer_average':
            # Compare against other models of same type
            peer_performances = self.db.query(
                func.avg(ModelPerformance.composite_score).label('avg_score'),
                func.avg(ModelPerformance.accuracy).label('avg_accuracy'),
                func.avg(ModelPerformance.precision_score).label('avg_precision'),
                func.avg(ModelPerformance.win_rate).label('avg_win_rate')
            ).join(AIModel).filter(
                AIModel.model_type == model.model_type,
                AIModel.id != model_id,
                ModelPerformance.evaluation_date >= datetime.utcnow() - timedelta(days=30)
            ).first()
            
            if not peer_performances or not peer_performances.avg_score:
                return {'error': 'No peer data available for comparison'}
            
            comparison = {
                'benchmark_type': 'peer_average',
                'model_performance': {
                    'composite_score': float(model_performance.composite_score) if model_performance.composite_score else 0,
                    'accuracy': float(model_performance.accuracy) if model_performance.accuracy else 0,
                    'precision': float(model_performance.precision_score) if model_performance.precision_score else 0,
                    'win_rate': float(model_performance.win_rate) if model_performance.win_rate else 0
                },
                'benchmark_performance': {
                    'composite_score': float(peer_performances.avg_score),
                    'accuracy': float(peer_performances.avg_accuracy) if peer_performances.avg_accuracy else 0,
                    'precision': float(peer_performances.avg_precision) if peer_performances.avg_precision else 0,
                    'win_rate': float(peer_performances.avg_win_rate) if peer_performances.avg_win_rate else 0
                }
            }
            
            # Calculate relative performance
            model_score = comparison['model_performance']['composite_score']
            benchmark_score = comparison['benchmark_performance']['composite_score']
            
            if benchmark_score > 0:
                relative_performance = (model_score - benchmark_score) / benchmark_score * 100
                comparison['relative_performance_pct'] = round(relative_performance, 2)
                comparison['performance_category'] = (
                    'excellent' if relative_performance > 10 else
                    'above_average' if relative_performance > 0 else
                    'below_average' if relative_performance > -10 else
                    'poor'
                )
            
            return comparison
        
        elif benchmark_type == 'historical_best':
            # Compare against historical best performance for this model
            best_performance = self.db.query(ModelPerformance).filter(
                ModelPerformance.model_id == model_id
            ).order_by(ModelPerformance.composite_score.desc()).first()
            
            if not best_performance:
                return {'error': 'No historical performance data'}
            
            current_score = float(model_performance.composite_score) if model_performance.composite_score else 0
            best_score = float(best_performance.composite_score) if best_performance.composite_score else 0
            
            return {
                'benchmark_type': 'historical_best',
                'current_score': current_score,
                'best_score': best_score,
                'performance_decline_pct': round((best_score - current_score) / best_score * 100, 2) if best_score > 0 else 0,
                'best_performance_date': best_performance.evaluation_date.isoformat()
            }
        
        return {'error': f'Unknown benchmark type: {benchmark_type}'}
    
    def get_performance_insights(self, model_id: int) -> Dict[str, Any]:
        """Generate comprehensive performance insights"""
        insights = {
            'model_id': model_id,
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'insights': []
        }
        
        # Get recent performance data
        recent_performances = self.get_by_model(model_id, limit=10)
        if not recent_performances:
            insights['insights'].append({
                'type': 'warning',
                'message': 'No performance data available for analysis'
            })
            return insights
        
        latest_performance = recent_performances[0]
        
        # Performance grade insights
        if latest_performance.performance_grade:
            grade_insights = {
                'A': 'Excellent performance - model is performing optimally',
                'B': 'Good performance - model is performing well within acceptable range',
                'C': 'Average performance - consider monitoring for improvements',
                'D': 'Below average performance - review model configuration',
                'F': 'Poor performance - immediate attention required'
            }
            
            insights['insights'].append({
                'type': 'performance_grade',
                'grade': latest_performance.performance_grade,
                'message': grade_insights.get(latest_performance.performance_grade, 'Unknown grade')
            })
        
        # Threshold compliance
        if not latest_performance.meets_min_threshold:
            insights['insights'].append({
                'type': 'warning',
                'message': 'Model performance is below minimum thresholds'
            })
        
        # Market regime analysis
        if latest_performance.market_regime:
            regime_performances = self.get_by_market_regime(latest_performance.market_regime)
            if len(regime_performances) > 1:
                avg_score = sum(float(p.composite_score) for p in regime_performances if p.composite_score) / len(regime_performances)
                current_score = float(latest_performance.composite_score) if latest_performance.composite_score else 0
                
                if current_score > avg_score * 1.1:
                    insights['insights'].append({
                        'type': 'strength',
                        'message': f'Model performs exceptionally well in {latest_performance.market_regime} market conditions'
                    })
                elif current_score < avg_score * 0.9:
                    insights['insights'].append({
                        'type': 'weakness',
                        'message': f'Model underperforms in {latest_performance.market_regime} market conditions'
                    })
        
        # Performance trend analysis
        if len(recent_performances) >= 3:
            scores = [float(p.composite_score) for p in recent_performances[::-1] if p.composite_score]
            if len(scores) >= 3:
                recent_trend = scores[-1] - scores[-3]
                if recent_trend > 0.05:
                    insights['insights'].append({
                        'type': 'positive_trend',
                        'message': 'Model performance is showing improvement trend'
                    })
                elif recent_trend < -0.05:
                    insights['insights'].append({
                        'type': 'negative_trend', 
                        'message': 'Model performance is showing decline trend - consider retraining'
                    })
        
        return insights
    
    def get_performance_alerts(self, threshold_config: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """Generate performance-based alerts"""
        if threshold_config is None:
            threshold_config = {
                'min_composite_score': 0.7,
                'min_accuracy': 0.75,
                'min_win_rate': 0.55,
                'max_days_without_evaluation': 7
            }
        
        alerts = []
        
        # Check for models with poor recent performance
        poor_performers = self.db.query(ModelPerformance).filter(
            ModelPerformance.composite_score < threshold_config['min_composite_score'],
            ModelPerformance.evaluation_date >= datetime.utcnow() - timedelta(days=7)
        ).all()
        
        for perf in poor_performers:
            alerts.append({
                'type': 'poor_performance',
                'severity': 'high',
                'model_id': perf.model_id,
                'message': f'Model {perf.model_id} composite score ({perf.composite_score:.3f}) below threshold ({threshold_config["min_composite_score"]})',
                'evaluation_date': perf.evaluation_date.isoformat()
            })
        
        # Check for models without recent evaluations
        from ...models.ai.model import AIModel
        
        stale_models = self.db.query(AIModel).filter(
            AIModel.is_active == True,
            AIModel.status.in_(['production', 'training'])
        ).all()
        
        cutoff_date = datetime.utcnow() - timedelta(days=threshold_config['max_days_without_evaluation'])
        
        for model in stale_models:
            latest_eval = self.get_latest_by_model(model.id)
            if not latest_eval or latest_eval.evaluation_date < cutoff_date:
                alerts.append({
                    'type': 'stale_evaluation',
                    'severity': 'medium',
                    'model_id': model.id,
                    'message': f'Model {model.id} has not been evaluated in {threshold_config["max_days_without_evaluation"]} days',
                    'last_evaluation': latest_eval.evaluation_date.isoformat() if latest_eval else None
                })
        
        return sorted(alerts, key=lambda x: x['severity'], reverse=True)
    
    def export_performance_report(self, model_ids: List[int] = None, days: int = 30) -> Dict[str, Any]:
        """Export comprehensive performance report"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(ModelPerformance).filter(
            ModelPerformance.evaluation_date >= cutoff_date
        )
        
        if model_ids:
            query = query.filter(ModelPerformance.model_id.in_(model_ids))
        
        performances = query.order_by(ModelPerformance.evaluation_date.desc()).all()
        
        # Group by model
        model_data = {}
        for perf in performances:
            if perf.model_id not in model_data:
                model_data[perf.model_id] = []
            model_data[perf.model_id].append({
                'evaluation_date': perf.evaluation_date.isoformat(),
                'composite_score': float(perf.composite_score) if perf.composite_score else None,
                'accuracy': float(perf.accuracy) if perf.accuracy else None,
                'precision': float(perf.precision_score) if perf.precision_score else None,
                'recall': float(perf.recall) if perf.recall else None,
                'win_rate': float(perf.win_rate) if perf.win_rate else None,
                'performance_grade': perf.performance_grade,
                'meets_threshold': perf.meets_min_threshold,
                'market_regime': perf.market_regime
            })
        
        # Calculate summary statistics
        summary = {
            'report_period_days': days,
            'total_evaluations': len(performances),
            'models_evaluated': len(model_data),
            'generated_at': datetime.utcnow().isoformat()
        }
        
        if performances:
            scores = [float(p.composite_score) for p in performances if p.composite_score]
            if scores:
                summary.update({
                    'avg_composite_score': round(sum(scores) / len(scores), 3),
                    'best_composite_score': round(max(scores), 3),
                    'worst_composite_score': round(min(scores), 3)
                })
        
        return {
            'summary': summary,
            'model_performances': model_data,
            'export_timestamp': datetime.utcnow().isoformat()
        }
