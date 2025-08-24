# File: backend\app\models\market\sentiment.py
# SQLAlchemy model for sentiment data

from sqlalchemy import Column, Integer, DateTime, DECIMAL, JSON, Index
from sqlalchemy.sql import func

from app.core.database import Base

class MarketSentimentData(Base):
    """
    Market sentiment analysis from multiple sources
    """
    __tablename__ = "market_sentiment_data"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Sentiment scores
    fear_greed_index = Column(DECIMAL(5, 2))  # 0-100
    social_sentiment = Column(DECIMAL(5, 4))  # -1 to 1
    news_sentiment = Column(DECIMAL(5, 4))    # -1 to 1
    composite_sentiment = Column(DECIMAL(5, 4))  # -1 to 1
    
    # Data sources and analysis
    sentiment_sources = Column(JSON, default={})
    funding_rates = Column(JSON, default={})
    options_data = Column(JSON, default={})
    analysis_metrics = Column(JSON, default={})
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<MarketSentimentData(composite_sentiment={self.composite_sentiment})>"

# Performance indexes
Index('idx_sentiment_fear_greed', MarketSentimentData.fear_greed_index.desc(), MarketSentimentData.timestamp.desc())
Index('idx_sentiment_composite', MarketSentimentData.composite_sentiment.desc(), MarketSentimentData.timestamp.desc())
