# File: backend/app/models/prediction.py
# SQLAlchemy model for ML predictions storage

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Index, Boolean, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta

from app.core.database import Base


class Prediction(Base):
    """
    Prediction model for storing ML model predictions
    
    This model stores predictions made by various ML models,
    including confidence scores, features used, and performance metrics.
    Designed for tracking prediction accuracy and model performance.
    """
    
    __tablename__ = "predictions"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Optional user association
    
    # Prediction details
    model_name = Column(String(50), nullable=False, index=True)           # LSTM, ARIMA, etc.
    model_version = Column(String(20), nullable=False, default="1.0")     # Model version
    predicted_price = Column(Numeric(precision=20, scale=8), nullable=False) # Predicted price
    confidence_score = Column(Numeric(precision=5, scale=4), nullable=False) # Confidence (0-1)
    
    # Prediction metadata
    prediction_horizon = Column(Integer, nullable=False)                  # Hours ahead (1, 24, 168, etc.)
    target_datetime = Column(DateTime(timezone=True), nullable=False, index=True) # When prediction is for
    features_used = Column(JSON, nullable=True)                          # Features used in prediction
    model_parameters = Column(JSON, nullable=True)                       # Model hyperparameters
    
    # Input data at prediction time
    input_price = Column(Numeric(precision=20, scale=8), nullable=False)  # Price when prediction was made
    input_features = Column(JSON, nullable=True)                         # Feature values at prediction time
    
    # Actual vs Predicted (filled when target_datetime is reached)
    actual_price = Column(Numeric(precision=20, scale=8), nullable=True)  # Actual price (when available)
    accuracy_percentage = Column(Numeric(precision=5, scale=2), nullable=True) # Prediction accuracy
    absolute_error = Column(Numeric(precision=20, scale=8), nullable=True) # |actual - predicted|
    squared_error = Column(Numeric(precision=30, scale=8), nullable=True)  # (actual - predicted)²
    
    # Prediction status
    is_realized = Column(Boolean, default=False, nullable=False)          # Has target_datetime passed?
    is_accurate = Column(Boolean, nullable=True)                         # Is prediction considered accurate?
    accuracy_threshold = Column(Numeric(precision=5, scale=2), default=5.0) # Accuracy threshold %
    
    # Additional metadata
    training_data_end = Column(DateTime(timezone=True), nullable=True)    # Last training data point
    market_conditions = Column(String(20), nullable=True)                # bull, bear, sideways
    volatility_level = Column(String(10), nullable=True)                 # low, medium, high
    
    # Performance tracking
    model_training_time = Column(Numeric(precision=10, scale=2), nullable=True) # Training time in seconds
    prediction_time = Column(Numeric(precision=10, scale=6), nullable=True)     # Prediction time in seconds
    
    # Notes and debugging
    notes = Column(Text, nullable=True)                                   # Additional notes
    debug_info = Column(JSON, nullable=True)                             # Debug information
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    evaluated_at = Column(DateTime(timezone=True), nullable=True)         # When accuracy was calculated
    
    # Relationships
    cryptocurrency = relationship("Cryptocurrency", back_populates="predictions")
    user = relationship("User", back_populates="predictions")
    
    # Database indexes for performance
    __table_args__ = (
        # Composite indexes for common queries
        Index('idx_prediction_crypto_target', 'crypto_id', 'target_datetime'),
        Index('idx_prediction_model_created', 'model_name', 'created_at'),
        Index('idx_prediction_user_created', 'user_id', 'created_at'),
        Index('idx_prediction_horizon', 'prediction_horizon', 'created_at'),
        # Index for accuracy analysis
        Index('idx_prediction_realized', 'is_realized', 'accuracy_percentage'),
        # Index for model performance analysis
        Index('idx_prediction_model_performance', 'model_name', 'model_version', 'confidence_score'),
    )
    
    def __repr__(self):
        return f"<Prediction(crypto_id={self.crypto_id}, model='{self.model_name}', target='{self.target_datetime}')>"
    
    @property
    def is_overdue(self) -> bool:
        """Check if prediction target time has passed"""
        return datetime.utcnow() > self.target_datetime
    
    @property
    def time_until_target(self) -> timedelta:
        """Time remaining until target datetime"""
        return self.target_datetime - datetime.utcnow()
    
    @property
    def prediction_error_percentage(self) -> float:
        """Calculate prediction error percentage"""
        if not self.actual_price or not self.predicted_price:
            return None
        
        if self.input_price == 0:
            return None
            
        error = abs(float(self.actual_price - self.predicted_price))
        return (error / float(self.input_price)) * 100
    
    def calculate_accuracy(self, actual_price: float) -> None:
        """Calculate and store prediction accuracy"""
        self.actual_price = actual_price
        self.absolute_error = abs(actual_price - float(self.predicted_price))
        self.squared_error = (actual_price - float(self.predicted_price)) ** 2
        
        if float(self.predicted_price) > 0:
            self.accuracy_percentage = 100 - (self.absolute_error / float(self.predicted_price) * 100)
            self.is_accurate = self.accuracy_percentage >= float(self.accuracy_threshold)
        
        self.is_realized = True
        self.evaluated_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'crypto_id': self.crypto_id,
            'user_id': self.user_id,
            'model_name': self.model_name,
            'model_version': self.model_version,
            'predicted_price': float(self.predicted_price),
            'confidence_score': float(self.confidence_score),
            'prediction_horizon': self.prediction_horizon,
            'target_datetime': self.target_datetime.isoformat() if self.target_datetime else None,
            'input_price': float(self.input_price),
            'actual_price': float(self.actual_price) if self.actual_price else None,
            'accuracy_percentage': float(self.accuracy_percentage) if self.accuracy_percentage else None,
            'is_realized': self.is_realized,
            'is_accurate': self.is_accurate,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }