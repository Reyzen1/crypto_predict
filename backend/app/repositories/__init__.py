# backend/app/repositories/__init__.py
# Repository package initialization - exports all repositories

from .base import BaseRepository

# AI Repositories
from .ai import (
    AIModelRepository,
    ModelPerformanceRepository,
    ModelJobRepository
)

# Asset Repositories  
from .asset import (
    AssetRepository,
    PriceDataRepository,
    PriceDataArchiveRepository
)

# Macro Repositories
from .macro import (
    MetricsSnapshotRepository,
    AIMarketRegimeAnalysisRepository
)

# User Repositories
from .user import (
    UserRepository
)


__all__ = [
    # Base
    "BaseRepository",
    
    # AI
    "AIModelRepository",
    "ModelPerformanceRepository", 
    "ModelJobRepository",
    
    # Asset
    "AssetRepository",
    "PriceDataRepository",
    "PriceDataArchiveRepository",
    
    # Macro
    "MetricsSnapshotRepository",
    "AIMarketRegimeAnalysisRepository",
    
    # User
    "UserRepository",
]

