# File: backend\app\models\system\__init__.py
# SQLAlchemy model for module initialization

from .ai_model import AIModel
from .health import SystemHealth
from .info import SystemInfo
from .notification import Notification

__all__ = ["AIModel", "SystemHealth", "SystemInfo", "Notification"]
