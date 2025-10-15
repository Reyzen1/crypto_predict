# SQLAlchemy Models Package
# CryptoPredict - Domain-based Model Structure

# Base classes and mixins
from .base import Base, BaseModel, CreatedAtMixin, UpdatedAtMixin, TimestampMixin, IDMixin
from .mixins import (
    ActiveMixin, SoftDeleteMixin, UserTrackingMixin, 
    ValidationMixin, AIAnalysisMixin, DataQualityMixin,
    AccessTrackingMixin, UserPreferencesMixin, ExternalIdsMixin
)
from .enums import (
    UserRole, AssetType, TimeframeEnum, Regime,
    JobStatus, ModelType, ModelStatus
)

# User Management
from .user import User, UserSession, UserActivity

# Asset Management  
from .asset import Asset, PriceData, PriceDataArchive

# AI Framework
from .ai import AIModel, ModelPerformance, ModelJob

# Layer 1: Macro Analysis
from .macro import MetricsSnapshot, AIRegimeAnalysis

# Layer 2: Sector Analysis
from .sector import *

# Layer 3: Asset Selection & Management
from .selection import *

# Layer 4: Trading Operations
from .trading import *

__all__ = [
    # Base
    "BaseModel",
    "Base",
    
    # User models will be exported here
    # Asset models will be exported here
    # AI models will be exported here
    # Macro models will be exported here
    # Sector models will be exported here
    # Selection models will be exported here
    # Trading models will be exported here
]