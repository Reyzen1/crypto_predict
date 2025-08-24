# File: backend\app\models\__init__.py
# SQLAlchemy model for   init   data

# Core domain imports
from .core.user import User, UserActivity
from .core.crypto import Cryptocurrency
from .core.price import PriceData
from .core.prediction import Prediction

# Market analysis domain
from .market.regime import MarketRegimeAnalysis
from .market.sentiment import MarketSentimentData
from .market.dominance import DominanceData
from .market.indicators import MacroIndicator

# Sectors domain
from .sectors.sector import CryptoSector, CryptoSectorMapping
from .sectors.performance import SectorPerformance
from .sectors.rotation import SectorRotationAnalysis

# Trading domain
from .trading.signal import TradingSignal
from .trading.execution import SignalExecution
from .trading.risk import RiskManagement

# Watchlist domain
from .watchlist.watchlist import Watchlist, WatchlistItem
from .watchlist.suggestion import AISuggestion
from .watchlist.review import SuggestionReview

# System domain
from .system.ai_model import AIModel
from .system.health import SystemHealth
from .system.info import SystemInfo
from .system.notification import Notification

# All models for easy import
__all__ = [
    # Core (4 models)
    "User", "UserActivity", "Cryptocurrency", "PriceData", "Prediction",
    
    # Market (4 models)
    "MarketRegimeAnalysis", "MarketSentimentData", "DominanceData", "MacroIndicator",
    
    # Sectors (4 models)
    "CryptoSector", "CryptoSectorMapping", "SectorPerformance", "SectorRotationAnalysis",
    
    # Trading (3 models)
    "TradingSignal", "SignalExecution", "RiskManagement",
    
    # Watchlist (4 models)
    "Watchlist", "WatchlistItem", "AISuggestion", "SuggestionReview",
    
    # System (4 models)
    "AIModel", "SystemHealth", "SystemInfo", "Notification",
]
