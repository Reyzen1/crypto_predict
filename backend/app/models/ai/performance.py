# backend/app/models/ai/performance.py
# Model performance evaluation results and metrics with job traceability

from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, Numeric, DateTime, ForeignKey, CheckConstraint, Index, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from ..base import BaseModel, CreatedAtMixin


class ModelPerformance(BaseModel, CreatedAtMixin):
    """
    Model performance evaluation results and metrics with job traceability
    
    Comprehensive performance tracking with ML metrics, trading performance,
    statistical validation, and business assessment. Links to originating jobs.
    
    Uses CreatedAtMixin (only created_at) because evaluations are immutable
    historical records of model performance at a specific point in time.
    """
    __tablename__ = 'model_performance'
    
    # 🔗 Model Reference & Job Traceability
    model_id = Column(Integer, ForeignKey('ai_models.id'), nullable=False, index=True)
    source_job_id = Column(Integer, ForeignKey('model_jobs.id'), nullable=True, index=True)
    
    # 📊 Evaluation Context (simplified - job details via JOIN)
    evaluation_date = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    evaluation_trigger = Column(String(30), nullable=False, index=True,
                              comment="Trigger: 'job_completion', 'manual', 'scheduled', 'api_request'")
    
    # 📈 Core ML Performance Metrics
    accuracy = Column(Numeric(6,4), nullable=True, comment="Classification accuracy (0-1)")
    precision_score = Column(Numeric(6,4), nullable=True, comment="Precision score (0-1)")
    recall = Column(Numeric(6,4), nullable=True, comment="Recall score (0-1)")
    f1_score = Column(Numeric(6,4), nullable=True, comment="F1 score (0-1)")
    auc_score = Column(Numeric(8,4), nullable=True, comment="AUC score (0-1)")
    
    # 💰 Trading Performance Metrics
    win_rate = Column(Numeric(6,4), nullable=True, comment="Win rate percentage (0-1)")
    profit_factor = Column(Numeric(8,2), nullable=True, comment="Profit factor")
    sharpe_ratio = Column(Numeric(8,4), nullable=True, comment="Sharpe ratio")
    max_drawdown = Column(Numeric(6,4), nullable=True, comment="Maximum drawdown (0-1)")
    total_return_pct = Column(Numeric(8,2), nullable=True, comment="Total return percentage")
    calmar_ratio = Column(Numeric(8,4), nullable=True, comment="Calmar ratio")
    
    # 📊 Statistical Quality Metrics
    mse = Column(Numeric(10,6), nullable=True, comment="Mean squared error")
    mae = Column(Numeric(8,4), nullable=True, comment="Mean absolute error")
    r2_score = Column(Numeric(6,4), nullable=True, comment="R-squared score")
    
    # 🔢 Sample Quality & Distribution
    total_samples = Column(Integer, nullable=True, comment="Total number of samples")
    valid_predictions = Column(Integer, nullable=True, comment="Number of valid predictions")
    confidence_mean = Column(Numeric(6,4), nullable=True, comment="Mean confidence score")
    confidence_std = Column(Numeric(6,4), nullable=True, comment="Standard deviation of confidence")
    
    # 🎯 Business Performance Assessment
    meets_min_threshold = Column(Boolean, nullable=True, comment="Meets minimum performance threshold")
    performance_grade = Column(String(2), nullable=True, comment="Performance grade: A, B, C, D, F")
    composite_score = Column(Numeric(6,4), nullable=True, comment="Composite performance score (0-1)")
    evaluation_status = Column(String(20), nullable=False, default='completed', index=True,
                             comment="Status: 'completed', 'failed', 'partial', 'invalidated'")
    
    # 🌍 Market Context
    market_regime = Column(String(20), nullable=True, comment="Market regime during evaluation")
    market_volatility = Column(Numeric(6,4), nullable=True, comment="Market volatility (0-1)")
    
    # 📋 Evaluation Results & Analysis
    confusion_matrix = Column(JSONB, nullable=True, default={}, comment="Confusion matrix for classification")
    performance_breakdown = Column(JSONB, nullable=True, default={}, comment="Detailed performance breakdown")
    benchmark_comparison = Column(JSONB, nullable=True, default={}, comment="Comparison with benchmarks")
    evaluation_summary = Column(Text, nullable=True, comment="Summary of evaluation results")
    
    # 🔗 Relationships
    model = relationship("AIModel", back_populates="performance_evaluations")
    source_job = relationship("ModelJob", back_populates="performance_evaluations")
    
    # 📋 Comprehensive Validation Constraints
    __table_args__ = (
        # ML Metrics Constraints
        CheckConstraint(
            'accuracy IS NULL OR (accuracy >= 0 AND accuracy <= 1) AND '
            'precision_score IS NULL OR (precision_score >= 0 AND precision_score <= 1) AND '
            'recall IS NULL OR (recall >= 0 AND recall <= 1) AND '
            'f1_score IS NULL OR (f1_score >= 0 AND f1_score <= 1) AND '
            'auc_score IS NULL OR (auc_score >= 0 AND auc_score <= 1)',
            name='chk_perf_ml_metrics'
        ),
        
        # Trading Metrics Constraints
        CheckConstraint(
            'win_rate IS NULL OR (win_rate >= 0 AND win_rate <= 1) AND '
            'max_drawdown IS NULL OR (max_drawdown >= 0 AND max_drawdown <= 1) AND '
            'profit_factor IS NULL OR profit_factor >= 0',
            name='chk_perf_trading_metrics'
        ),
        
        # Statistical Metrics Constraints
        CheckConstraint(
            'r2_score IS NULL OR (r2_score >= -1 AND r2_score <= 1) AND '
            'mse IS NULL OR mse >= 0 AND '
            'mae IS NULL OR mae >= 0',
            name='chk_perf_statistical_metrics'
        ),
        
        # Sample Counts Constraints
        CheckConstraint(
            'total_samples IS NULL OR total_samples > 0 AND '
            'valid_predictions IS NULL OR (valid_predictions >= 0 AND valid_predictions <= total_samples)',
            name='chk_perf_sample_counts'
        ),
        
        # Confidence Metrics Constraints
        CheckConstraint(
            'confidence_mean IS NULL OR (confidence_mean >= 0 AND confidence_mean <= 1) AND '
            'confidence_std IS NULL OR confidence_std >= 0',
            name='chk_perf_confidence_metrics'
        ),
        
        CheckConstraint(
            'composite_score IS NULL OR (composite_score >= 0 AND composite_score <= 1)',
            name='chk_perf_composite_score'
        ),
        
        CheckConstraint(
            'market_volatility IS NULL OR (market_volatility >= 0 AND market_volatility <= 1)',
            name='chk_perf_market_volatility'
        ),
        
        CheckConstraint(
            "evaluation_status IN ('completed', 'failed', 'partial', 'invalidated')",
            name='chk_perf_status_valid'
        ),
        
        CheckConstraint(
            "performance_grade IS NULL OR performance_grade IN ('A', 'B', 'C', 'D', 'F')",
            name='chk_perf_grade_valid'
        ),
        
        CheckConstraint(
            "market_regime IS NULL OR market_regime IN ('bull', 'bear', 'sideways', 'volatile')",
            name='chk_perf_market_regime_valid'
        ),
        
        CheckConstraint(
            "evaluation_trigger IN ('job_completion', 'manual', 'scheduled', 'api_request')",
            name='chk_perf_trigger_valid'
        ),
        
        # High-Performance Indexes
        Index('idx_perf_model_recent', 'model_id', 'evaluation_date'),
        Index('idx_perf_grade_threshold', 'performance_grade', 'meets_min_threshold', 'composite_score'),
        Index('idx_perf_job_source', 'source_job_id', 'evaluation_date'),
        Index('idx_perf_trigger_status', 'evaluation_trigger', 'evaluation_status', 'evaluation_date'),
        Index('idx_perf_composite_score', 'composite_score'),
        Index('idx_perf_market_regime', 'market_regime', 'evaluation_date'),
    )
    
    def __repr__(self):
        return f"<ModelPerformance(id={self.id}, model_id={self.model_id}, grade='{self.performance_grade}', score={self.composite_score})>"
    
    @property
    def is_high_performance(self):
        """Check if this is a high performance evaluation (grade A or B)"""
        return self.performance_grade in ['A', 'B'] if self.performance_grade else False
    
    @property
    def overall_ml_score(self):
        """Calculate overall ML score from available metrics"""
        metrics = [self.accuracy, self.precision_score, self.recall, self.f1_score]
        valid_metrics = [float(m) for m in metrics if m is not None]
        return sum(valid_metrics) / len(valid_metrics) if valid_metrics else None
    
    @property
    def overall_trading_score(self):
        """Calculate overall trading score"""
        if self.win_rate and self.profit_factor and self.sharpe_ratio:
            # Weighted average considering different aspects
            return (float(self.win_rate) * 0.4 + 
                   min(float(self.profit_factor) / 2.0, 1.0) * 0.3 + 
                   min(max(float(self.sharpe_ratio), 0) / 3.0, 1.0) * 0.3)
        return None
    
    @property
    def sample_quality_score(self):
        """Calculate sample quality score"""
        if self.total_samples and self.valid_predictions:
            validity_ratio = self.valid_predictions / self.total_samples
            confidence_factor = float(self.confidence_mean) if self.confidence_mean else 0.5
            return validity_ratio * confidence_factor
        return None
    
    def calculate_composite_score(self):
        """Calculate and update composite performance score"""
        ml_score = self.overall_ml_score
        trading_score = self.overall_trading_score
        quality_score = self.sample_quality_score
        
        scores = []
        if ml_score is not None:
            scores.append(ml_score * 0.4)  # 40% weight
        if trading_score is not None:
            scores.append(trading_score * 0.4)  # 40% weight  
        if quality_score is not None:
            scores.append(quality_score * 0.2)  # 20% weight
            
        if scores:
            self.composite_score = sum(scores) / len(scores) * (len(scores) / 3)  # Normalize
            return self.composite_score
        return None
    
    def assign_performance_grade(self):
        """Assign performance grade based on composite score"""
        if not self.composite_score:
            self.calculate_composite_score()
            
        if self.composite_score is None:
            self.performance_grade = None
            return
            
        score = float(self.composite_score)
        if score >= 0.9:
            self.performance_grade = 'A'
        elif score >= 0.8:
            self.performance_grade = 'B'
        elif score >= 0.7:
            self.performance_grade = 'C'
        elif score >= 0.6:
            self.performance_grade = 'D'
        else:
            self.performance_grade = 'F'
    
    def check_threshold_compliance(self, min_accuracy=0.7, min_win_rate=0.55):
        """Check if performance meets minimum thresholds"""
        accuracy_ok = self.accuracy is None or float(self.accuracy) >= min_accuracy
        win_rate_ok = self.win_rate is None or float(self.win_rate) >= min_win_rate
        
        self.meets_min_threshold = accuracy_ok and win_rate_ok
        return self.meets_min_threshold
    
    @classmethod
    def get_recent_by_model(cls, session, model_id: int, limit: int = 10):
        """Get recent evaluations for a specific model"""
        return session.query(cls).filter(
            cls.model_id == model_id
        ).order_by(cls.evaluation_date.desc()).limit(limit).all()
    
    @classmethod
    def get_high_performance_evaluations(cls, session, min_grade: str = 'B'):
        """Get high performance evaluations"""
        grade_order = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'F': 1}
        min_grade_value = grade_order.get(min_grade, 4)
        
        return session.query(cls).filter(
            cls.performance_grade.in_([g for g, v in grade_order.items() if v >= min_grade_value])
        ).order_by(cls.composite_score.desc()).all()
    
    @classmethod
    def get_by_job(cls, session, job_id: int):
        """Get evaluations triggered by a specific job"""
        return session.query(cls).filter(
            cls.source_job_id == job_id
        ).order_by(cls.evaluation_date.desc()).all()
    
    def to_dict(self, include_detailed: bool = False) -> dict:
        """Convert evaluation to dictionary"""
        data = {
            'id': self.id,
            'model_id': self.model_id,
            'source_job_id': self.source_job_id,
            'evaluation_date': self.evaluation_date.isoformat() if self.evaluation_date else None,
            'evaluation_trigger': self.evaluation_trigger,
            'evaluation_status': self.evaluation_status,
            'performance_grade': self.performance_grade,
            'composite_score': float(self.composite_score) if self.composite_score else None,
            'meets_min_threshold': self.meets_min_threshold,
            'is_high_performance': self.is_high_performance,
            'market_regime': self.market_regime,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_detailed:
            data.update({
                # ML Metrics
                'accuracy': float(self.accuracy) if self.accuracy else None,
                'precision_score': float(self.precision_score) if self.precision_score else None,
                'recall': float(self.recall) if self.recall else None,
                'f1_score': float(self.f1_score) if self.f1_score else None,
                'auc_score': float(self.auc_score) if self.auc_score else None,
                
                # Trading Metrics
                'win_rate': float(self.win_rate) if self.win_rate else None,
                'profit_factor': float(self.profit_factor) if self.profit_factor else None,
                'sharpe_ratio': float(self.sharpe_ratio) if self.sharpe_ratio else None,
                'max_drawdown': float(self.max_drawdown) if self.max_drawdown else None,
                'total_return_pct': float(self.total_return_pct) if self.total_return_pct else None,
                'calmar_ratio': float(self.calmar_ratio) if self.calmar_ratio else None,
                
                # Statistical Metrics
                'mse': float(self.mse) if self.mse else None,
                'mae': float(self.mae) if self.mae else None,
                'r2_score': float(self.r2_score) if self.r2_score else None,
                
                # Sample Quality
                'total_samples': self.total_samples,
                'valid_predictions': self.valid_predictions,
                'confidence_mean': float(self.confidence_mean) if self.confidence_mean else None,
                'confidence_std': float(self.confidence_std) if self.confidence_std else None,
                
                # Market Context
                'market_volatility': float(self.market_volatility) if self.market_volatility else None,
                
                # Detailed Analysis
                'confusion_matrix': self.confusion_matrix,
                'performance_breakdown': self.performance_breakdown,
                'benchmark_comparison': self.benchmark_comparison,
                'evaluation_summary': self.evaluation_summary,
                
                # Calculated Scores
                'overall_ml_score': self.overall_ml_score,
                'overall_trading_score': self.overall_trading_score,
                'sample_quality_score': self.sample_quality_score
            })
        
        return data