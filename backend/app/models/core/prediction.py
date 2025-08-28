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
    model_name = Column(String(50), nullable=False, index=True)           # LSTM, ARIMA, etc.
    model_version = Column(String(20), nullable=False, default="1.0")     # Model version
    
    # Phase 2 enhancement: Multi-type prediction support
    prediction_type = Column(String(20), nullable=False, default='price', index=True)
    
    # Traditional price prediction (Phase 1 - maintained for backward compatibility)
    predicted_price = Column(DECIMAL(15, 4), nullable=False)                        # Predicted price
    
    # Phase 2 enhancement: Flexible prediction value for non-price predictions
    predicted_value = Column(JSON, default=dict)
    
    # Confidence and validation
    confidence_score = Column(DECIMAL(5, 2), nullable=False, index=True)            # Confidence (0-1)
    prediction_horizon = Column(Integer, nullable=False)                            # Hours ahead (1, 24, 168, etc.)
    target_datetime = Column(DateTime(timezone=True), nullable=False, index=True)   # When prediction is for
    
    # Feature engineering
    features_used = Column(JSON)                                        # Features used in prediction
    model_parameters = Column(JSON)                                     # Model hyperparameters
    input_price = Column(DECIMAL(15, 4))                 # Price when prediction was made
    input_features = Column(JSON)                                       # Feature values at prediction time
    
    # Phase 2 enhancement: Macro context from upper layers
    macro_context = Column(JSON, default=dict)
    
    # Evaluation results
    actual_price = Column(DECIMAL(20, 8))                # Actual price (when available)
    accuracy_percentage = Column(DECIMAL(5, 2))          # Prediction accuracy
    absolute_error = Column(DECIMAL(20, 8))              # |actual - predicted|
    squared_error = Column(DECIMAL(30, 8))               # (actual - predicted)²
    is_realized = Column(Boolean, nullable=False, default=False, index=True)    # Has target_datetime passed?
    is_accurate = Column(Boolean, index=True)                           # Is prediction considered accurate?
    accuracy_threshold = Column(DECIMAL(5, 2))                          # Accuracy threshold %

    # Model performance metadata
    training_data_end = Column(DateTime(timezone=True), index=True)   # Last training data point
    market_conditions = Column(String(20), index=True)           # bull, bear, sideways
    volatility_level = Column(String(10), index=True)            # low, medium, high
    model_training_time = Column(DECIMAL(10, 2))                 # Training time in seconds
    prediction_time = Column(DECIMAL(10, 6))                     # Prediction time in seconds

    # Additional information
    notes = Column(Text)                                  # Additional notes
    debug_info = Column(JSON)                             # Debug information
    
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
