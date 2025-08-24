# File: backend\app\models\core\prediction.py
# SQLAlchemy model for prediction data

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, DECIMAL, ForeignKey, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base

class Prediction(Base):
    """
    Unified prediction model for all prediction types
    Enhanced from Phase 1 to support multi-layer AI predictions
    """
    __tablename__ = "predictions"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    
    # Layer identification (Phase 2 enhancement)
    layer_source = Column(String(10), index=True)  # layer1, layer2, layer3, layer4
    
    # Model information
    model_name = Column(String(50), nullable=False, index=True)
    model_version = Column(String(20), nullable=False)
    
    # Phase 2 enhancement: Multi-type prediction support
    prediction_type = Column(String(20), nullable=False, default='price', index=True)
    
    # Traditional price prediction (Phase 1 - maintained for backward compatibility)
    predicted_price = Column(DECIMAL(15, 4), nullable=False)
    
    # Phase 2 enhancement: Flexible prediction value for non-price predictions
    predicted_value = Column(JSON, default={})
    
    # Confidence and validation
    confidence_score = Column(DECIMAL(5, 2), nullable=False, index=True)
    prediction_horizon = Column(Integer, nullable=False)
    target_datetime = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Feature engineering
    features_used = Column(JSON)
    model_parameters = Column(JSON)
    input_price = Column(DECIMAL(15, 4), nullable=False)
    input_features = Column(JSON)
    
    # Phase 2 enhancement: Macro context from upper layers
    macro_context = Column(JSON, default={})
    
    # Evaluation results
    actual_price = Column(DECIMAL(20, 8))
    accuracy_percentage = Column(DECIMAL(5, 2))
    absolute_error = Column(DECIMAL(20, 8))
    squared_error = Column(DECIMAL(30, 8))
    is_realized = Column(Boolean, nullable=False, default=False, index=True)
    is_accurate = Column(Boolean, index=True)
    accuracy_threshold = Column(DECIMAL(5, 2))
    
    # Model performance metadata
    training_data_end = Column(DateTime(timezone=True), index=True)
    market_conditions = Column(String(20), index=True)
    volatility_level = Column(String(10), index=True)
    model_training_time = Column(DECIMAL(10, 2))
    prediction_time = Column(DECIMAL(10, 6))
    
    # Additional information
    notes = Column(Text)
    debug_info = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    evaluated_at = Column(DateTime(timezone=True), index=True)
    
    # Relationships
    cryptocurrency = relationship("Cryptocurrency", back_populates="predictions")
    user = relationship("User", back_populates="predictions")
    
    def __repr__(self):
        return f"<Prediction(id={self.id}, type={self.prediction_type}, layer={self.layer_source})>"

# Performance indexes matching database
Index('idx_predictions_layer_type', Prediction.layer_source, Prediction.prediction_type)
Index('idx_predictions_crypto_type', Prediction.crypto_id, Prediction.prediction_type)
Index('idx_predictions_type_time', Prediction.prediction_type, Prediction.created_at.desc())
Index('idx_predictions_crypto_layer', Prediction.crypto_id, Prediction.layer_source, Prediction.created_at.desc())
Index('idx_predictions_evaluation', Prediction.is_realized, Prediction.is_accurate, Prediction.evaluated_at.desc())

Index('idx_prediction_model_performance', Prediction.model_name, Prediction.model_version, Prediction.confidence_score)
Index('idx_predictions_model_performance', Prediction.model_name, Prediction.accuracy_percentage.desc())
Index('idx_predictions_layer_source', Prediction.layer_source, Prediction.created_at.desc())
Index('idx_predictions_horizon', Prediction.prediction_horizon, Prediction.created_at.desc())
