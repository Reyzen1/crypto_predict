# backend/app/repositories/__init__.py
# Repository package initialization - exports all repositories

from .base_repository import BaseRepository

# AI Repositories
from .ai.ai_model_repository import AIModelRepository
from .ai.model_performance_repository import ModelPerformanceRepository
from .ai.model_job_repository import ModelJobRepository

# Asset Repositories  
from .asset.asset_repository import AssetRepository
from .asset.price_data_repository import PriceDataRepository
from .asset.price_data_archive_repository import PriceDataArchiveRepository

# Compatibility aliases for existing code
cryptocurrency_repository = AssetRepository
price_data_repository = PriceDataRepository

# Macro Repositories
from .macro.metrics_snapshot_repository import MetricsSnapshotRepository
from .macro.ai_regime_analysis_repository import AIRegimeAnalysisRepository

# User Repositories
from .user.user_repository import UserRepository


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
    "AIRegimeAnalysisRepository",
    
    # User
    "UserRepository",
    
    # Compatibility aliases
    "cryptocurrency_repository",
    "price_data_repository",
]

