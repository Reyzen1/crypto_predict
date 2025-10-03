# backend/app/repositories/ai/models.py
# Repository for AI model management

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, timedelta

from ..base import BaseRepository
from ...models.ai.model import AIModel
from ...models.enums import ModelStatus, ModelType


class AIModelRepository(BaseRepository):
    """
    Repository for AI model management with specialized queries
    """
    
    def __init__(self, db: Session):
        super().__init__(AIModel, db)
    
    def get_active_models(self) -> List[AIModel]:
        """Get all active AI models"""
        return self.db.query(AIModel).filter(
            AIModel.is_active == True,
            AIModel.status != ModelStatus.DEPRECATED.value
        ).order_by(AIModel.created_at.desc()).all()
    
    def get_by_status(self, status: str) -> List[AIModel]:
        """Get models by status"""
        return self.db.query(AIModel).filter(
            AIModel.status == status
        ).order_by(AIModel.created_at.desc()).all()
    
    def get_by_type(self, model_type: str) -> List[AIModel]:
        """Get models by type"""
        return self.db.query(AIModel).filter(
            AIModel.model_type == model_type
        ).order_by(AIModel.created_at.desc()).all()
    
    def get_production_models(self) -> List[AIModel]:
        """Get models in production"""
        return self.db.query(AIModel).filter(
            AIModel.status == ModelStatus.PRODUCTION.value,
            AIModel.is_active == True
        ).order_by(AIModel.version.desc()).all()
    
    def get_latest_by_asset(self, asset_id: int) -> Optional[AIModel]:
        """Get latest model for specific asset"""
        return self.db.query(AIModel).filter(
            AIModel.target_asset_id == asset_id,
            AIModel.is_active == True
        ).order_by(AIModel.created_at.desc()).first()
    
    def get_models_needing_retraining(self, threshold_days: int = 30) -> List[AIModel]:
        """Get models that need retraining based on last training date"""
        cutoff_date = datetime.utcnow() - timedelta(days=threshold_days)
        return self.db.query(AIModel).filter(
            AIModel.last_training_date < cutoff_date,
            AIModel.status == ModelStatus.PRODUCTION.value,
            AIModel.is_active == True
        ).all()
    
    def get_performance_summary(self, model_id: int) -> Dict[str, Any]:
        """Get performance summary for a model"""
        from ...models.ai.performance import ModelPerformance
        
        latest_performance = self.db.query(ModelPerformance).filter(
            ModelPerformance.model_id == model_id
        ).order_by(ModelPerformance.evaluation_date.desc()).first()
        
        if not latest_performance:
            return {}
        
        return {
            'latest_evaluation': latest_performance.evaluation_date,
            'performance_grade': latest_performance.performance_grade,
            'composite_score': float(latest_performance.composite_score) if latest_performance.composite_score else None,
            'meets_threshold': latest_performance.meets_min_threshold
        }
    
    def search_models(self, query: str, limit: int = 20) -> List[AIModel]:
        """Search models by name or description"""
        return self.db.query(AIModel).filter(
            or_(
                AIModel.model_name.ilike(f'%{query}%'),
                AIModel.description.ilike(f'%{query}%')
            )
        ).limit(limit).all()
    
    def get_models_by_creator(self, user_id: int) -> List[AIModel]:
        """Get models created by specific user"""
        return self.db.query(AIModel).filter(
            AIModel.created_by == user_id
        ).order_by(AIModel.created_at.desc()).all()
    
    def update_model_status(self, model_id: int, status: str, notes: str = None) -> bool:
        """Update model status with optional notes"""
        model = self.get(model_id)
        if not model:
            return False
        
        model.status = status
        if notes:
            if not model.metadata:
                model.metadata = {}
            model.metadata['status_change'] = {
                'timestamp': datetime.utcnow().isoformat(),
                'notes': notes
            }
        
        self.db.commit()
        return True
    
    def get_model_versions(self, base_name: str) -> List[AIModel]:
        """Get all versions of a model by base name"""
        return self.db.query(AIModel).filter(
            AIModel.model_name.like(f'{base_name}%')
        ).order_by(AIModel.version.desc()).all()
    
    def deploy_model(self, model_id: int, deployment_config: Dict[str, Any] = None) -> bool:
        """Deploy a model to production"""
        model = self.get(model_id)
        if not model:
            return False
        
        # Check if model is ready for deployment
        if model.status not in [ModelStatus.TRAINED.value, ModelStatus.VALIDATED.value]:
            return False
        
        # Update model status and deployment info
        model.status = ModelStatus.PRODUCTION.value
        model.deployment_date = datetime.utcnow()
        
        if deployment_config:
            if not model.deployment_config:
                model.deployment_config = {}
            model.deployment_config.update(deployment_config)
        
        # Add deployment event to metadata
        if not model.metadata:
            model.metadata = {}
        
        model.metadata['deployment_history'] = model.metadata.get('deployment_history', [])
        model.metadata['deployment_history'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'version': model.version,
            'config': deployment_config or {}
        })
        
        self.db.commit()
        return True
    
    def retire_model(self, model_id: int, reason: str = None) -> bool:
        """Retire a model from production"""
        model = self.get(model_id)
        if not model:
            return False
        
        model.status = ModelStatus.DEPRECATED.value
        model.is_active = False
        
        if reason:
            if not model.metadata:
                model.metadata = {}
            model.metadata['retirement'] = {
                'timestamp': datetime.utcnow().isoformat(),
                'reason': reason
            }
        
        self.db.commit()
        return True
    
    def get_model_lineage(self, model_id: int) -> Dict[str, Any]:
        """Get model lineage (parent/child relationships)"""
        model = self.get(model_id)
        if not model:
            return {}
        
        # Get parent models (if any)
        parent_models = []
        if model.parent_model_id:
            parent = self.get(model.parent_model_id)
            if parent:
                parent_models.append({
                    'id': parent.id,
                    'name': parent.model_name,
                    'version': parent.version,
                    'created_at': parent.created_at.isoformat()
                })
        
        # Get child models
        child_models = self.db.query(AIModel).filter(
            AIModel.parent_model_id == model_id
        ).order_by(AIModel.created_at.desc()).all()
        
        child_models_info = [{
            'id': child.id,
            'name': child.model_name,
            'version': child.version,
            'status': child.status,
            'created_at': child.created_at.isoformat()
        } for child in child_models]
        
        return {
            'model_id': model_id,
            'model_name': model.model_name,
            'version': model.version,
            'parents': parent_models,
            'children': child_models_info,
            'lineage_depth': len(parent_models) + len(child_models_info)
        }
    
    def compare_models(self, model_ids: List[int]) -> Dict[str, Any]:
        """Compare multiple models side by side"""
        if len(model_ids) < 2:
            return {'error': 'At least 2 models required for comparison'}
        
        models = [self.get(mid) for mid in model_ids if self.get(mid)]
        
        if len(models) < 2:
            return {'error': 'Not enough valid models found'}
        
        from ...models.ai.performance import ModelPerformance
        
        comparison = {
            'models': [],
            'comparison_timestamp': datetime.utcnow().isoformat()
        }
        
        for model in models:
            # Get latest performance
            latest_perf = self.db.query(ModelPerformance).filter(
                ModelPerformance.model_id == model.id
            ).order_by(ModelPerformance.evaluation_date.desc()).first()
            
            model_info = {
                'id': model.id,
                'name': model.model_name,
                'version': model.version,
                'type': model.model_type,
                'status': model.status,
                'created_at': model.created_at.isoformat(),
                'training_date': model.last_training_date.isoformat() if model.last_training_date else None,
                'performance': {}
            }
            
            if latest_perf:
                model_info['performance'] = {
                    'grade': latest_perf.performance_grade,
                    'composite_score': float(latest_perf.composite_score) if latest_perf.composite_score else None,
                    'accuracy': float(latest_perf.accuracy) if latest_perf.accuracy else None,
                    'precision': float(latest_perf.precision_score) if latest_perf.precision_score else None,
                    'recall': float(latest_perf.recall) if latest_perf.recall else None,
                    'evaluation_date': latest_perf.evaluation_date.isoformat()
                }
            
            comparison['models'].append(model_info)
        
        # Add comparison insights
        scores = [m['performance'].get('composite_score') for m in comparison['models'] 
                 if m['performance'].get('composite_score')]
        
        if scores:
            best_score_idx = scores.index(max(scores))
            comparison['best_performing'] = comparison['models'][best_score_idx]['id']
            comparison['performance_range'] = {
                'min_score': min(scores),
                'max_score': max(scores),
                'avg_score': sum(scores) / len(scores)
            }
        
        return comparison
    
    def get_model_resource_usage(self, model_id: int) -> Dict[str, Any]:
        """Get model resource usage statistics"""
        model = self.get(model_id)
        if not model:
            return {}
        
        from ...models.ai.job import ModelJob
        
        # Get training jobs for this model
        training_jobs = self.db.query(ModelJob).filter(
            ModelJob.model_id == model_id,
            ModelJob.job_category == 'training'
        ).order_by(ModelJob.created_at.desc()).limit(10).all()
        
        # Calculate resource statistics
        total_training_time = sum(
            job.execution_duration_sec or 0 for job in training_jobs
        )
        
        avg_training_time = total_training_time / len(training_jobs) if training_jobs else 0
        
        # Extract resource allocation from jobs
        resource_usage = {
            'total_training_jobs': len(training_jobs),
            'total_training_time_hours': round(total_training_time / 3600, 2),
            'avg_training_time_hours': round(avg_training_time / 3600, 2),
            'resource_requirements': {},
            'last_training_resources': {}
        }
        
        if training_jobs:
            latest_job = training_jobs[0]
            if latest_job.resource_allocation:
                resource_usage['last_training_resources'] = latest_job.resource_allocation
        
        # Model size estimation (if available in metadata)
        if model.metadata and 'model_size' in model.metadata:
            resource_usage['model_size_mb'] = model.metadata['model_size']
        
        return resource_usage
    
    def get_model_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get analytics for all models over specified period"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Model creation trends
        new_models = self.db.query(func.count(AIModel.id)).filter(
            AIModel.created_at >= cutoff_date
        ).scalar()
        
        # Status distribution
        status_dist = self.db.query(
            AIModel.status,
            func.count(AIModel.id).label('count')
        ).filter(
            AIModel.created_at >= cutoff_date
        ).group_by(AIModel.status).all()
        
        # Type distribution
        type_dist = self.db.query(
            AIModel.model_type,
            func.count(AIModel.id).label('count')
        ).group_by(AIModel.model_type).all()
        
        # Performance summary
        from ...models.ai.performance import ModelPerformance
        
        avg_performance = self.db.query(
            func.avg(ModelPerformance.composite_score).label('avg_score')
        ).join(AIModel).filter(
            AIModel.created_at >= cutoff_date
        ).scalar()
        
        return {
            'period_days': days,
            'new_models_created': new_models or 0,
            'status_distribution': {s.status: s.count for s in status_dist},
            'type_distribution': {t.model_type: t.count for t in type_dist},
            'average_performance_score': round(float(avg_performance), 3) if avg_performance else None,
            'analysis_timestamp': datetime.utcnow().isoformat()
        }
    
    def auto_cleanup_old_models(self, retention_days: int = 365) -> Dict[str, int]:
        """Automatically cleanup old deprecated models"""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Find old deprecated models
        old_models = self.db.query(AIModel).filter(
            AIModel.status == ModelStatus.DEPRECATED.value,
            AIModel.updated_at < cutoff_date,
            AIModel.is_active == False
        ).all()
        
        cleaned_count = 0
        for model in old_models:
            # Archive model info to metadata before deletion
            if not model.metadata:
                model.metadata = {}
            
            model.metadata['archived_at'] = datetime.utcnow().isoformat()
            model.metadata['cleanup_reason'] = f'Auto cleanup after {retention_days} days'
            
            # In a real implementation, you might move to an archive table
            # For now, just mark as archived
            model.is_active = False
            cleaned_count += 1
        
        self.db.commit()
        
        return {
            'models_cleaned': cleaned_count,
            'retention_days': retention_days,
            'cleanup_date': datetime.utcnow().isoformat()
        }
