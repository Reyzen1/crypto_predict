# app/models/__init__.py
# Safe models without relationships to prevent SQLAlchemy conflicts

from app.core.database import Base

# Import existing User model
from app.models.user import User

# Create simple models without relationships
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql.sqltypes import Numeric  
from sqlalchemy.sql import func

class Cryptocurrency(Base):
    __tablename__ = "cryptocurrencies"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    coingecko_id = Column(String(50), nullable=True)
    binance_symbol = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class PriceData(Base):
    __tablename__ = "price_data"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    open_price = Column(Numeric(20, 8), nullable=False)
    high_price = Column(Numeric(20, 8), nullable=False)
    low_price = Column(Numeric(20, 8), nullable=False)
    close_price = Column(Numeric(20, 8), nullable=False)
    volume = Column(Numeric(20, 8), nullable=False)
    market_cap = Column(Numeric(20, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False)
    predicted_price = Column(Numeric(20, 8), nullable=False)
    confidence_score = Column(Numeric(5, 4), nullable=True)
    model_version = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Export all models
__all__ = [
    "Base",
    "User", 
    "Cryptocurrency",
    "PriceData", 
    "Prediction"
]
