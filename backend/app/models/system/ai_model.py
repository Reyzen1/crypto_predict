# File: backend\app\models\system\ai_model.py
# SQLAlchemy model for ai model data

from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, JSON, Boolean, ForeignKey, Index, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import date

from app.core.database import Base

class AIModel(Base):
    """
    AI Models management and performance tracking
    """
    __tablename__ = "ai_models"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Model identification  
    name = Column(String(100), unique=True, nullable=False, index=True)  # Updated field name
    version = Column(String(50), nullable=False)
    model_type = Column(String(20), nullable=False, index=True)
    
    # Model status
    status = Column(String(20), default='inactive')  # active, inactive, training, error
    
    # Configuration and parameters
    configuration = Column(JSON, default={})
    hyperparameters = Column(JSON, default={})
    training_config = Column(JSON, default={})
    
    # Performance metrics
    performance_metrics = Column(JSON, default={})
    accuracy_metrics = Column(JSON, default={})
    backtesting_results = Column(JSON, default={})
    
    # Training data
    training_data_from = Column(date)
    training_data_to = Column(date)
    
    # Timestamps
    last_trained = Column(DateTime(timezone=True))
    last_prediction = Column(DateTime(timezone=True))
    next_retrain_due = Column(DateTime(timezone=True))
    
    # Health and monitoring
    health_status = Column(JSON, default={})
    error_logs = Column(JSON, default=[])
    
    # Usage statistics
    prediction_count = Column(Integer, default=0)
    success_rate = Column(DECIMAL(5, 4))
    
    # Management
    created_by = Column(Integer, ForeignKey("users.id"))
    model_path = Column(String(500))
    model_size_mb = Column(DECIMAL(10, 2))
    deployment_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    creator = relationship("User", back_populates="ai_models_created")
    
    def __repr__(self):
        return f"<AIModel(id={self.id}, name={self.name}, type={self.model_type})>"

# Performance indexes
Index('idx_ai_models_type_status', AIModel.model_type, AIModel.status)
Index('idx_ai_models_performance', AIModel.model_type, AIModel.success_rate.desc().nulls_last())
Index('idx_ai_models_training', AIModel.last_trained.desc())
