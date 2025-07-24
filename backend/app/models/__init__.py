# File: backend/app/models/__init__.py
# Import all SQLAlchemy models for proper registration

from app.core.database import Base

# Import all models to ensure they're registered with SQLAlchemy
from .user import User
from .cryptocurrency import Cryptocurrency
from .price_data import PriceData
from .prediction import Prediction

# Export all models for easy importing
__all__ = [
    "Base",
    "User", 
    "Cryptocurrency",
    "PriceData", 
    "Prediction"
]