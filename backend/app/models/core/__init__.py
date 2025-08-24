# File: backend\app\models\core\__init__.py
# SQLAlchemy model for module initialization

from .user import User, UserActivity
from .crypto import Cryptocurrency
from .price import PriceData
from .prediction import Prediction

__all__ = ["User", "UserActivity", "Cryptocurrency", "PriceData", "Prediction"]
