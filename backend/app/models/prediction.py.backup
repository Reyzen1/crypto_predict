# File: ./backend/app/models/prediction.py
# Prediction model for storing AI prediction results

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Prediction(Base):
    """Prediction model for storing AI model predictions"""
    
    __tablename__ = "predictions"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    cryptocurrency_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False)
    
    # Prediction parameters
    prediction_type = Column(String(50), nullable=False)  # price, trend, volatility
    timeframe = Column(String(20), nullable=False)  # 1h, 24h, 7d, 30d
    horizon = Column(Integer, nullable=False)  # Prediction horizon in minutes
    
    # Prediction results
    predicted_price = Column(Float, nullable=True)
    predicted_change = Column(Float, nullable=True)  # Percentage change
    predicted_direction = Column(String(10), nullable=True)  # up, down, sideways
    
    # Confidence and accuracy metrics
    confidence_score = Column(Float, nullable=True)  # 0-1 scale
    accuracy_score = Column(Float, nullable=True)  # Historical accuracy
    
    # Model information
    model_name = Column(String(100), nullable=False)  # LSTM, GRU, etc.
    model_version = Column(String(20), nullable=False)
    features_used = Column(JSON, nullable=True)  # List of features used
    
    # Prediction metadata
    input_data_start = Column(DateTime(timezone=True), nullable=False)
    input_data_end = Column(DateTime(timezone=True), nullable=False)
    prediction_made_at = Column(DateTime(timezone=True), server_default=func.now())
    prediction_target_time = Column(DateTime(timezone=True), nullable=False)
    
    # Actual results (filled when prediction time is reached)
    actual_price = Column(Float, nullable=True)
    actual_change = Column(Float, nullable=True)
    actual_direction = Column(String(10), nullable=True)
    
    # Prediction status
    status = Column(String(20), default="pending")  # pending, completed, failed
    is_public = Column(Boolean, default=False)
    
    # Additional data
    notes = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="predictions")
    cryptocurrency = relationship("Cryptocurrency", back_populates="predictions")
    
    @property
    def is_expired(self) -> bool:
        """Check if prediction target time has passed"""
        from datetime import datetime
        return self.prediction_target_time < datetime.utcnow()
    
    @property
    def accuracy(self) -> float:
        """Calculate prediction accuracy if actual results are available"""
        if self.actual_price is None or self.predicted_price is None:
            return None
        
        # Calculate percentage error
        error = abs(self.actual_price - self.predicted_price) / self.actual_price
        return max(0, 1 - error)
    
    def __repr__(self):
        return f"<Prediction(id={self.id}, crypto_id={self.cryptocurrency_id}, predicted_price={self.predicted_price})>"