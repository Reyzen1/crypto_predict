# backend/app/models/ai/models.py
# AI Model management and versioning

from sqlalchemy import Column, String, Integer, Text, Numeric, Boolean, DateTime, CheckConstraint, Index, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from ..base import BaseModel, TimestampMixin
from ..mixins import ActiveMixin


class AIModel(BaseModel, TimestampMixin, ActiveMixin):
    """
    AI Model management and versioning
    
    Tracks model versions, performance, and deployment status
    Matches ERD structure with comprehensive configuration and health monitoring
    """
    __tablename__ = 'ai_models'
    
    # Model Identity & Classification
    name = Column(String(100), nullable=False, index=True)
    version = Column(String(20), nullable=False)
    architecture = Column(String(50), nullable=False, index=True)
    model_type = Column(String(20), nullable=False, index=True)
    status = Column(String(20), nullable=False, default='inactive', index=True)
    
    # 🎯 Model Configuration & Hyperparameters (ERD Schema)
    configuration = Column(JSONB, nullable=True, default={})
    
    # 📊 Performance Metrics (Comprehensive Structured Schema)
    performance_metrics = Column(JSONB, nullable=True, default={})
    
    # 🔧 Training Configuration (ERD Schema)
    training_features = Column(JSONB, nullable=True, default={})
    training_data_range = Column(JSONB, nullable=True, default={})
    training_data_timeframe = Column(String(10), nullable=False)
    target_variable = Column(String(50), nullable=False)
    
    # 📋 Input/Output Schema (Structured Schema)
    input_schema = Column(JSONB, nullable=True, default={})
    output_schema = Column(JSONB, nullable=True, default={})
    
    # 🏥 Health Monitoring (Comprehensive Structured Schema)
    health_status = Column(JSONB, nullable=True, default={})
    
    # 📝 Model Metadata
    training_notes = Column(Text, nullable=True)
    model_file_path = Column(String(100), nullable=True)
    framework = Column(String(50), nullable=True)
    deployment_environment = Column(String(20), nullable=True)
    
    # ⏰ Timestamps & Activity
    last_trained = Column(DateTime(timezone=True), nullable=True)
    last_prediction = Column(DateTime(timezone=True), nullable=True)
    deployed_at = Column(DateTime(timezone=True), nullable=True)
    deprecated_at = Column(DateTime(timezone=True), nullable=True)
    
    # 🔄 Model Lifecycle
    prediction_count = Column(Integer, nullable=False, default=0)
    model_size_mb = Column(Numeric(10,2), nullable=True)
    training_duration_minutes = Column(Integer, nullable=True)
    
    # 🎚️ Business Constraints
    min_confidence_threshold = Column(Numeric(4,2), nullable=False, default=0.5)
    max_predictions_per_hour = Column(Integer, nullable=True)
    requires_manual_approval = Column(Boolean, nullable=True, default=False)
    
    # Relationships (Updated for new schema)
    performance_evaluations = relationship("ModelPerformance", back_populates="model", cascade="all, delete-orphan")
    jobs = relationship("ModelJob", back_populates="model", cascade="all, delete-orphan")
    regime_analyses = relationship("AIMarketRegimeAnalysis", back_populates="ai_model", cascade="all, delete-orphan")
    
    # 📋 Enhanced Constraints & Indexes (ERD Compliant)
    __table_args__ = (
        # Check constraints (ERD)
        
        # Check constraints (ERD)
        CheckConstraint('prediction_count >= 0', name='chk_prediction_count_positive'),
        CheckConstraint('min_confidence_threshold BETWEEN 0 AND 1', name='chk_confidence_threshold'),
        CheckConstraint("architecture IN ('lstm', 'transformer', 'ensemble', 'regression', 'rule_based')", name='chk_architecture_valid'),
        CheckConstraint("model_type IN ('macro', 'sector', 'asset', 'timing')", name='chk_model_type_valid'),
        CheckConstraint("status IN ('active', 'training', 'inactive', 'error', 'deprecated')", name='chk_status_valid'),
        CheckConstraint("training_data_timeframe IN ('1m','5m','15m','1h','4h','1d','1w','1M')", name='chk_timeframe_valid'),
        CheckConstraint("target_variable IN ('price_direction', 'trend_strength', 'volatility_regime', 'regime_change_probability')", name='chk_target_variable_valid'),
        CheckConstraint("framework IS NULL OR framework IN ('scikit-learn', 'tensorflow', 'pytorch', 'xgboost')", name='chk_framework_valid'),
        CheckConstraint("deployment_environment IS NULL OR deployment_environment IN ('development', 'staging', 'production')", name='chk_deployment_env_valid'),
        CheckConstraint('model_size_mb IS NULL OR model_size_mb > 0', name='chk_model_size_positive'),
        CheckConstraint('training_duration_minutes IS NULL OR training_duration_minutes > 0', name='chk_training_duration_positive'),
        CheckConstraint('max_predictions_per_hour IS NULL OR max_predictions_per_hour > 0', name='chk_max_predictions_positive'),
        
        # Enhanced Performance Indexes (ERD)
        Index('idx_ai_models_name', 'name'),
        Index('idx_ai_models_type', 'model_type'),
        Index('idx_ai_models_status', 'status'),
        Index('idx_ai_models_architecture', 'architecture'),
        Index('idx_ai_models_active', 'is_active'),
        Index('idx_ai_models_created_at', 'created_at'),
        Index('idx_ai_models_last_prediction', 'last_prediction'),
        Index('idx_ai_models_deployment_env', 'deployment_environment'),
        Index('idx_ai_models_name_version', 'name', 'version'),
        Index('idx_ai_models_type_status', 'model_type', 'status'),
        Index('idx_unique_active_model', 'name', 'model_type', unique=True, postgresql_where=text('is_active = true')),
    )
    
    def __repr__(self):
        return f"<AIModel(id={self.id}, name='{self.name}', version='{self.version}', status='{self.status}')>"
    
    @property
    def full_name(self):
        """Get full model name with version"""
        return f"{self.name}_v{self.version}"
    
    @property
    def is_trained(self):
        """Check if model is trained and ready"""
        return self.status in ['active', 'inactive'] and self.last_trained is not None
    
    @property
    def is_ready_for_deployment(self):
        """Check if model is ready for deployment"""
        return (self.status == 'inactive' and 
                self.model_file_path and 
                self.performance_metrics)
    
    @property
    def training_duration_hours(self):
        """Get training duration in hours"""
        if self.training_duration_minutes:
            return round(self.training_duration_minutes / 60, 2)
        return None
    
    @property
    def performance_score(self):
        """Calculate overall performance score from performance_metrics JSON"""
        if not self.performance_metrics:
            return None
            
        classification_metrics = self.performance_metrics.get('classification_metrics', {})
        metrics = []
        
        for key in ['accuracy', 'precision', 'recall', 'f1_score']:
            if key in classification_metrics:
                metrics.append(float(classification_metrics[key]))
        
        return sum(metrics) / len(metrics) if metrics else None
    
    @property
    def is_high_performance(self):
        """Check if model has high performance (>0.8)"""
        score = self.performance_score
        return score and score > 0.8
    
    @property
    def deployment_status(self):
        """Get deployment status description"""
        if self.status == 'active' and self.deployment_environment:
            return f"Active in {self.deployment_environment}"
        elif self.status == 'active':
            return "Active (environment unknown)"
        elif self.is_ready_for_deployment:
            return "Ready for deployment"
        else:
            return "Not ready for deployment"
    
    def update_prediction_stats(self):
        """Update prediction usage statistics"""
        from datetime import datetime, timezone
        self.prediction_count += 1
        self.last_prediction = datetime.now(timezone.utc)
    
    def set_training_started(self, duration_minutes: int = None):
        """Mark training as started"""
        self.status = 'training'
        if duration_minutes:
            self.training_duration_minutes = duration_minutes
    
    def set_training_completed(self, performance_metrics: dict = None):
        """Mark training as completed with metrics"""
        from datetime import datetime, timezone
        
        self.last_trained = datetime.now(timezone.utc)
        self.status = 'inactive'  # Trained but not deployed
        
        if performance_metrics:
            self.performance_metrics = performance_metrics
    
    def set_deployment_status(self, environment: str, active: bool = True):
        """Update deployment status"""
        from datetime import datetime, timezone
        
        self.deployment_environment = environment
        
        if active and self.status == 'inactive':
            self.status = 'active'
            self.deployed_at = datetime.now(timezone.utc)
        elif not active:
            self.status = 'inactive'
    
    def add_performance_metric(self, metric_name: str, value: float, metadata: dict = None):
        """Add custom performance metric"""
        if not self.performance_metrics:
            self.performance_metrics = {}
        
        from datetime import datetime, timezone
        
        self.performance_metrics[metric_name] = {
            'value': value,
            'metadata': metadata or {},
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
    
    def get_performance_metric(self, metric_name: str):
        """Get specific performance metric"""
        if self.performance_metrics and metric_name in self.performance_metrics:
            return self.performance_metrics[metric_name]
        return None
    
    @classmethod
    def get_by_name_version(cls, session, name: str, version: str):
        """Get model by name and version"""
        return session.query(cls).filter(
            cls.name == name,
            cls.version == version
        ).first()
    
    @classmethod
    def get_latest_version(cls, session, name: str):
        """Get latest version of a model"""
        return session.query(cls).filter(
            cls.name == name
        ).order_by(cls.created_at.desc()).first()
    
    @classmethod
    def get_deployed_models(cls, session, environment: str = None):
        """Get deployed models"""
        query = session.query(cls).filter(
            cls.status == 'active',
            cls.is_active == True
        )
        
        if environment:
            query = query.filter(cls.deployment_environment == environment)
            
        return query.order_by(cls.last_prediction.desc()).all()
    
    @classmethod
    def get_by_type(cls, session, model_type: str):
        """Get models by type"""
        return session.query(cls).filter(
            cls.model_type == model_type,
            cls.is_active == True
        ).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_high_performance_models(cls, session, min_score: float = 0.8):
        """Get high performance models based on performance_metrics"""
        # This would need custom SQL or application-level filtering
        # since we're using JSONB for performance metrics
        return session.query(cls).filter(
            cls.is_active == True,
            cls.performance_metrics.isnot(None)
        ).all()
    
    @classmethod
    def get_training_models(cls, session):
        """Get models currently in training"""
        return session.query(cls).filter(
            cls.status == 'training'
        ).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_ready_for_deployment(cls, session):
        """Get models ready for deployment"""
        return session.query(cls).filter(
            cls.status == 'inactive',
            cls.model_file_path.isnot(None),
            cls.performance_metrics.isnot(None)
        ).order_by(cls.created_at.desc()).all()
    
    def to_dict(self, include_detailed: bool = False) -> dict:
        """Convert model to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'full_name': self.full_name,
            'architecture': self.architecture,
            'model_type': self.model_type,
            'status': self.status,
            'deployment_status': self.deployment_status,
            'is_active': self.is_active,
            'performance_score': self.performance_score,
            'is_high_performance': self.is_high_performance,
            'prediction_count': self.prediction_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_detailed:
            data.update({
                'configuration': self.configuration,
                'performance_metrics': self.performance_metrics,
                'training_features': self.training_features,
                'training_data_range': self.training_data_range,
                'training_data_timeframe': self.training_data_timeframe,
                'target_variable': self.target_variable,
                'input_schema': self.input_schema,
                'output_schema': self.output_schema,
                'health_status': self.health_status,
                'training_notes': self.training_notes,
                'model_file_path': self.model_file_path,
                'framework': self.framework,
                'deployment_environment': self.deployment_environment,
                'last_trained': self.last_trained.isoformat() if self.last_trained else None,
                'last_prediction': self.last_prediction.isoformat() if self.last_prediction else None,
                'deployed_at': self.deployed_at.isoformat() if self.deployed_at else None,
                'deprecated_at': self.deprecated_at.isoformat() if self.deprecated_at else None,
                'model_size_mb': float(self.model_size_mb) if self.model_size_mb else None,
                'training_duration_minutes': self.training_duration_minutes,
                'training_duration_hours': self.training_duration_hours,
                'min_confidence_threshold': float(self.min_confidence_threshold),
                'max_predictions_per_hour': self.max_predictions_per_hour,
                'requires_manual_approval': self.requires_manual_approval
            })
        
        return data