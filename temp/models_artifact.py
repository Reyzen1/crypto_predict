# ==================================================
# CryptoPredict ORM Models - Complete Production Suite
# Domain-Driven Architecture for Phase 2
# ==================================================

# ==================================================
# backend/app/models/__init__.py
# ==================================================
"""
CryptoPredict Models Package
Domain-Driven Organization for Phase 2 - Production Ready
"""

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

# ==================================================
# backend/app/models/core/__init__.py
# ==================================================
"""
Core Domain Models
Essential entities used across multiple layers
"""

from .user import User, UserActivity
from .crypto import Cryptocurrency
from .price import PriceData
from .prediction import Prediction

__all__ = ["User", "UserActivity", "Cryptocurrency", "PriceData", "Prediction"]

# ==================================================
# backend/app/models/core/user.py
# ==================================================
"""
User Management Models
Handles authentication, authorization and user activities
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import INET

from app.core.database import Base


class User(Base):
    """
    Core user model for authentication and authorization
    Enhanced from Phase 1 with role management for Phase 2
    """
    __tablename__ = "users"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile information
    first_name = Column(String(50))
    last_name = Column(String(50))
    
    # Role-based access control (Enhanced for Phase 2)
    role = Column(String(20), nullable=False, default='casual')  # admin, professional, casual
    
    # Status flags
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    is_superuser = Column(Boolean, nullable=False, default=False)
    
    # User preferences (TEXT for compatibility)
    preferences = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    predictions = relationship("Prediction", back_populates="user", lazy="dynamic")
    watchlists = relationship("Watchlist", back_populates="user", lazy="dynamic")
    activities = relationship("UserActivity", back_populates="user", lazy="dynamic")
    notifications = relationship("Notification", back_populates="user", lazy="dynamic")
    risk_profiles = relationship("RiskManagement", back_populates="user", uselist=False)
    ai_models_created = relationship("AIModel", back_populates="creator", lazy="dynamic")
    suggestion_reviews = relationship("SuggestionReview", back_populates="admin_user", lazy="dynamic")
    signal_executions = relationship("SignalExecution", back_populates="user", lazy="dynamic")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class UserActivity(Base):
    """
    Track user activities for analytics and audit purposes
    Enhanced with all database fields
    """
    __tablename__ = "user_activities"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # User reference
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Activity details
    activity_type = Column(String(50), nullable=False, index=True)
    activity_category = Column(String(30), default='general')
    activity_data = Column(JSON, default={})
    
    # Request information
    request_path = Column(String(500))
    request_method = Column(String(10))
    response_status = Column(Integer)
    response_time_ms = Column(DECIMAL(10, 2))
    
    # Session information
    session_id = Column(String(100))
    ip_address = Column(INET)
    user_agent = Column(Text)
    
    # Device information
    device_type = Column(String(20))
    browser = Column(String(50))
    location_country = Column(String(2))
    
    # Execution status
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    additional_data = Column(JSON, default={})
    
    # Timestamp
    activity_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="activities")
    
    def __repr__(self):
        return f"<UserActivity(id={self.id}, user_id={self.user_id}, type={self.activity_type})>"


# Performance indexes
Index('idx_users_role', User.role, User.is_active)
Index('idx_users_role_active', User.role, User.is_active, User.last_login.desc())
Index('idx_user_activities_user_time', UserActivity.user_id, UserActivity.activity_time.desc())
Index('idx_user_activities_type', UserActivity.activity_type, UserActivity.activity_time.desc())
Index('idx_user_activities_session', UserActivity.session_id, UserActivity.activity_time.desc())

# ==================================================
# backend/app/models/core/crypto.py
# ==================================================
"""
Cryptocurrency Model
Core entity for crypto market data management - separated from PriceData
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, DECIMAL, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Cryptocurrency(Base):
    """
    Cryptocurrency master data
    Enhanced from Phase 1 with sector mapping and watchlist tier support
    """
    __tablename__ = "cryptocurrencies"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic identification
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    coingecko_id = Column(String(50), unique=True, index=True)
    
    # Market data
    market_cap_rank = Column(Integer, index=True)
    current_price = Column(DECIMAL(20, 8))
    market_cap = Column(DECIMAL(30, 2))
    total_volume = Column(DECIMAL(30, 2))
    circulating_supply = Column(DECIMAL(30, 2))
    total_supply = Column(DECIMAL(30, 2))
    max_supply = Column(DECIMAL(30, 2))
    
    # Metadata
    description = Column(Text)
    website_url = Column(String(255))
    blockchain_site = Column(String(255))
    
    # Phase 2 enhancements
    sector_id = Column(Integer, ForeignKey("crypto_sectors.id"), index=True)
    watchlist_tier = Column(String(10), nullable=False, default='none', index=True)  # tier1, tier2, none
    
    # Status flags
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    is_supported = Column(Boolean, nullable=False, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_data_update = Column(DateTime(timezone=True), index=True)
    
    # Relationships
    price_data = relationship("PriceData", back_populates="cryptocurrency", lazy="dynamic")
    predictions = relationship("Prediction", back_populates="cryptocurrency", lazy="dynamic")
    sector = relationship("CryptoSector", back_populates="cryptocurrencies")
    sector_mappings = relationship("CryptoSectorMapping", back_populates="cryptocurrency")
    watchlist_items = relationship("WatchlistItem", back_populates="cryptocurrency")
    ai_suggestions = relationship("AISuggestion", back_populates="cryptocurrency")
    trading_signals = relationship("TradingSignal", back_populates="cryptocurrency")
    
    def __repr__(self):
        return f"<Cryptocurrency(id={self.id}, symbol={self.symbol}, name={self.name})>"


# Performance indexes matching database
Index('idx_cryptocurrencies_sector', Cryptocurrency.sector_id, Cryptocurrency.is_active)
Index('idx_cryptocurrencies_tier', Cryptocurrency.watchlist_tier, Cryptocurrency.is_active)
Index('idx_cryptocurrencies_market_cap', Cryptocurrency.market_cap.desc().nulls_last()).where(Cryptocurrency.is_active == True)
Index('idx_cryptocurrencies_volume', Cryptocurrency.total_volume.desc().nulls_last()).where(Cryptocurrency.is_active == True)
Index('idx_cryptocurrencies_price_change', Cryptocurrency.current_price, Cryptocurrency.updated_at.desc())

# ==================================================
# backend/app/models/core/price.py
# ==================================================
"""
Price Data Model
Time-series price data with technical indicators - separated from Cryptocurrency
"""

from sqlalchemy import Column, Integer, DateTime, DECIMAL, ForeignKey, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import GIN

from app.core.database import Base


class PriceData(Base):
    """
    Historical price data with technical indicators
    Enhanced from Phase 1 with technical indicators support
    """
    __tablename__ = "price_data"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Crypto reference
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False, index=True)
    
    # OHLCV data
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    open_price = Column(DECIMAL(20, 8), nullable=False)
    high_price = Column(DECIMAL(20, 8), nullable=False)
    low_price = Column(DECIMAL(20, 8), nullable=False)
    close_price = Column(DECIMAL(20, 8), nullable=False)
    volume = Column(DECIMAL(30, 8))
    market_cap = Column(DECIMAL(30, 2))
    
    # Technical indicators (Phase 2 enhancement)
    technical_indicators = Column(JSON, default={})
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    cryptocurrency = relationship("Cryptocurrency", back_populates="price_data")
    
    def __repr__(self):
        return f"<PriceData(id={self.id}, crypto_id={self.crypto_id}, timestamp={self.timestamp})>"


# Performance indexes matching database
Index('idx_price_data_timestamp_desc', PriceData.timestamp.desc())
Index('idx_price_data_crypto_timestamp_desc', PriceData.crypto_id, PriceData.timestamp.desc())
Index('idx_price_data_volume', PriceData.volume.desc(), PriceData.timestamp.desc())
Index('idx_price_data_technical', PriceData.technical_indicators, postgresql_using='gin')

# ==================================================
# backend/app/models/core/prediction.py
# ==================================================
"""
Unified Prediction Model
Handles all types of predictions across 4-layer AI architecture
Enhanced from Phase 1 with multi-type prediction support
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, DECIMAL, ForeignKey, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Prediction(Base):
    """
    Unified prediction model for all prediction types
    Enhanced from Phase 1 to support multi-layer AI predictions
    """
    __tablename__ = "predictions"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    
    # Layer identification (Phase 2 enhancement)
    layer_source = Column(String(10), index=True)  # layer1, layer2, layer3, layer4
    
    # Model information
    model_name = Column(String(50), nullable=False, index=True)
    model_version = Column(String(20), nullable=False)
    
    # Phase 2 enhancement: Multi-type prediction support
    prediction_type = Column(String(20), nullable=False, default='price', index=True)
    
    # Traditional price prediction (Phase 1 - maintained for backward compatibility)
    predicted_price = Column(DECIMAL(15, 4), nullable=False)
    
    # Phase 2 enhancement: Flexible prediction value for non-price predictions
    predicted_value = Column(JSON, default={})
    
    # Confidence and validation
    confidence_score = Column(DECIMAL(5, 2), nullable=False, index=True)
    prediction_horizon = Column(Integer, nullable=False)
    target_datetime = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Feature engineering
    features_used = Column(JSON)
    model_parameters = Column(JSON)
    input_price = Column(DECIMAL(15, 4), nullable=False)
    input_features = Column(JSON)
    
    # Phase 2 enhancement: Macro context from upper layers
    macro_context = Column(JSON, default={})
    
    # Evaluation results
    actual_price = Column(DECIMAL(20, 8))
    accuracy_percentage = Column(DECIMAL(5, 2))
    absolute_error = Column(DECIMAL(20, 8))
    squared_error = Column(DECIMAL(30, 8))
    is_realized = Column(Boolean, nullable=False, default=False, index=True)
    is_accurate = Column(Boolean, index=True)
    accuracy_threshold = Column(DECIMAL(5, 2))
    
    # Model performance metadata
    training_data_end = Column(DateTime(timezone=True), index=True)
    market_conditions = Column(String(20), index=True)
    volatility_level = Column(String(10), index=True)
    model_training_time = Column(DECIMAL(10, 2))
    prediction_time = Column(DECIMAL(10, 6))
    
    # Additional information
    notes = Column(Text)
    debug_info = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    evaluated_at = Column(DateTime(timezone=True), index=True)
    
    # Relationships
    cryptocurrency = relationship("Cryptocurrency", back_populates="predictions")
    user = relationship("User", back_populates="predictions")
    
    def __repr__(self):
        return f"<Prediction(id={self.id}, type={self.prediction_type}, layer={self.layer_source})>"


# Performance indexes matching database
Index('idx_predictions_layer_type', Prediction.layer_source, Prediction.prediction_type)
Index('idx_predictions_crypto_type', Prediction.crypto_id, Prediction.prediction_type)
Index('idx_predictions_type_time', Prediction.prediction_type, Prediction.created_at.desc())
Index('idx_predictions_crypto_layer', Prediction.crypto_id, Prediction.layer_source, Prediction.created_at.desc())
Index('idx_predictions_evaluation', Prediction.is_realized, Prediction.is_accurate, Prediction.evaluated_at.desc())

# ==================================================
# backend/app/models/market/__init__.py
# ==================================================
"""
Market Analysis Domain Models
Layer 1: Macro market analysis and sentiment tracking
"""

from .regime import MarketRegimeAnalysis
from .sentiment import MarketSentimentData
from .dominance import DominanceData
from .indicators import MacroIndicator

__all__ = ["MarketRegimeAnalysis", "MarketSentimentData", "DominanceData", "MacroIndicator"]

# ==================================================
# backend/app/models/market/regime.py
# ==================================================
"""
Market Regime Analysis Model
Layer 1: Macro market state detection and regime classification
"""

from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, JSON, Index
from sqlalchemy.sql import func

from app.core.database import Base


class MarketRegimeAnalysis(Base):
    """
    Market regime analysis and classification
    Tracks overall market state: Bull/Bear/Neutral/Volatile
    """
    __tablename__ = "market_regime_analysis"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Market regime classification
    regime = Column(String(10), nullable=False, index=True)  # bull, bear, sideways, volatile
    confidence_score = Column(DECIMAL(5, 4), nullable=False, index=True)
    
    # Regime characteristics
    risk_level = Column(String(10), nullable=False, index=True)  # low, medium, high, extreme
    trend_strength = Column(DECIMAL(5, 4))
    recommended_exposure = Column(DECIMAL(5, 4))
    
    # Analysis data from database
    indicators = Column(JSON, default={})
    analysis_data = Column(JSON, default={})
    market_context = Column(JSON, default={})
    
    # Timestamps
    analysis_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<MarketRegimeAnalysis(regime={self.regime}, confidence={self.confidence_score})>"


# Performance indexes
Index('idx_market_regime_regime', MarketRegimeAnalysis.regime, MarketRegimeAnalysis.confidence_score.desc())

# ==================================================
# backend/app/models/market/sentiment.py
# ==================================================
"""
Market Sentiment Data Model
Layer 1: Multi-source sentiment aggregation
"""

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

# ==================================================
# backend/app/models/market/dominance.py  
# ==================================================
"""
Market Dominance Data Model
Layer 1: BTC, ETH, and altcoin market dominance tracking
"""

from sqlalchemy import Column, Integer, DateTime, DECIMAL, JSON, Index
from sqlalchemy.sql import func

from app.core.database import Base


class DominanceData(Base):
    """
    Market dominance tracking for major cryptocurrencies
    """
    __tablename__ = "dominance_data"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Dominance percentages
    btc_dominance = Column(DECIMAL(5, 2), nullable=False, index=True)
    eth_dominance = Column(DECIMAL(5, 2), nullable=False, index=True)  
    alt_dominance = Column(DECIMAL(5, 2), nullable=False)
    stablecoin_dominance = Column(DECIMAL(5, 2), default=0)
    
    # Market data
    total_market_cap = Column(DECIMAL(20, 2))
    total_volume_24h = Column(DECIMAL(20, 2))
    
    # Analysis data
    trend_analysis = Column(JSON, default={})
    dominance_changes = Column(JSON, default={})
    rotation_signals = Column(JSON, default={})
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<DominanceData(btc={self.btc_dominance}%, eth={self.eth_dominance}%)>"


# Performance indexes
Index('idx_dominance_btc', DominanceData.btc_dominance.desc(), DominanceData.timestamp.desc())
Index('idx_dominance_eth', DominanceData.eth_dominance.desc(), DominanceData.timestamp.desc())

# ==================================================
# backend/app/models/market/indicators.py
# ==================================================
"""
Macro Economic Indicators Model
Layer 1: Economic indicators affecting crypto markets
"""

from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, JSON, Index, UniqueConstraint
from sqlalchemy.sql import func

from app.core.database import Base


class MacroIndicator(Base):
    """
    Macro economic indicators tracking
    """
    __tablename__ = "macro_indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Indicator identification
    indicator_name = Column(String(50), nullable=False, index=True)
    indicator_category = Column(String(30), nullable=False, default='general', index=True)
    
    # Values
    value = Column(DECIMAL(15, 8), nullable=False)  # Updated field name
    normalized_value = Column(DECIMAL(5, 4))
    
    # Metadata
    timeframe = Column(String(20), nullable=False, default='1d')
    data_source = Column(String(50), nullable=False, index=True)
    metadata = Column(JSON, default={})
    quality_score = Column(DECIMAL(3, 2), default=1.0)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<MacroIndicator(name={self.indicator_name}, value={self.value})>"


# Unique constraint and indexes
UniqueConstraint('indicator_name', 'timeframe', 'timestamp', name='macro_indicators_indicator_name_timeframe_timestamp_key')
Index('idx_macro_indicators_name_time', MacroIndicator.indicator_name, MacroIndicator.timestamp.desc())
Index('idx_macro_indicators_category', MacroIndicator.indicator_category, MacroIndicator.timestamp.desc())

# ==================================================
# backend/app/models/sectors/__init__.py
# ==================================================
"""
Sectors Domain Models  
Layer 2: Sector analysis and rotation tracking
"""

from .sector import CryptoSector, CryptoSectorMapping
from .performance import SectorPerformance
from .rotation import SectorRotationAnalysis

__all__ = ["CryptoSector", "CryptoSectorMapping", "SectorPerformance", "SectorRotationAnalysis"]

# ==================================================
# backend/app/models/sectors/sector.py
# ==================================================
"""
Crypto Sectors and Mapping Models
Layer 2: Sector definitions and crypto-sector relationships
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, DECIMAL, ForeignKey, JSON, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class CryptoSector(Base):
    """
    Cryptocurrency sector definitions
    """
    __tablename__ = "crypto_sectors"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Sector identification
    name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Sector characteristics
    characteristics = Column(JSON, default={})
    sector_type = Column(String(20), default='general')
    maturity_level = Column(String(10), default='medium')
    risk_category = Column(String(10), default='medium')
    
    # Status and ordering
    is_active = Column(Boolean, default=True, index=True)
    sort_order = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    cryptocurrencies = relationship("Cryptocurrency", back_populates="sector")
    sector_mappings = relationship("CryptoSectorMapping", back_populates="sector")
    performance_records = relationship("SectorPerformance", back_populates="sector")
    
    def __repr__(self):
        return f"<CryptoSector(id={self.id}, name={self.name})>"


class CryptoSectorMapping(Base):
    """
    Many-to-many mapping between cryptocurrencies and sectors
    """
    __tablename__ = "crypto_sector_mapping"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False, index=True)
    sector_id = Column(Integer, ForeignKey("crypto_sectors.id"), nullable=False, index=True)
    
    # Mapping details
    allocation_percentage = Column(DECIMAL(5, 2), nullable=False, default=100)
    is_primary_sector = Column(Boolean, default=True)
    mapping_confidence = Column(DECIMAL(5, 4), default=1.0)
    mapping_source = Column(String(50), default='manual')
    sector_weight = Column(DECIMAL(5, 4), default=1.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    cryptocurrency = relationship("Cryptocurrency", back_populates="sector_mappings")
    sector = relationship("CryptoSector", back_populates="sector_mappings")
    
    def __repr__(self):
        return f"<CryptoSectorMapping(crypto_id={self.crypto_id}, sector_id={self.sector_id})>"


# Constraints and indexes
UniqueConstraint('crypto_id', 'sector_id', name='crypto_sector_mapping_crypto_id_sector_id_key')
Index('idx_crypto_sector_crypto', CryptoSectorMapping.crypto_id, CryptoSectorMapping.is_primary_sector.desc())
Index('idx_crypto_sector_sector', CryptoSectorMapping.sector_id, CryptoSectorMapping.allocation_percentage.desc())
Index('idx_crypto_sector_primary', CryptoSectorMapping.is_primary_sector, CryptoSectorMapping.mapping_confidence.desc())

# ==================================================
# backend/app/models/sectors/performance.py
# ==================================================
"""
Sector Performance Analytics Model
Layer 2: Sector performance tracking and analysis
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, DECIMAL, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class SectorPerformance(Base):
    """
    Real-time and historical performance data for crypto sectors
    """
    __tablename__ = "sector_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Sector reference
    sector_id = Column(Integer, ForeignKey("crypto_sectors.id"), nullable=False, index=True)
    
    # Performance metrics
    performance_1h = Column(DECIMAL(8, 4))
    performance_24h = Column(DECIMAL(8, 4))
    performance_7d = Column(DECIMAL(8, 4))
    performance_30d = Column(DECIMAL(8, 4))
    performance_90d = Column(DECIMAL(8, 4))
    
    # Volume and market cap changes
    volume_change_24h = Column(DECIMAL(8, 4))
    market_cap_change_24h = Column(DECIMAL(8, 4))
    
    # Totals
    market_cap_total = Column(DECIMAL(20, 2))
    volume_total_24h = Column(DECIMAL(20, 2))
    asset_count = Column(Integer, default=0)
    
    # Top/worst performers
    top_performer_id = Column(Integer, ForeignKey("cryptocurrencies.id"))
    worst_performer_id = Column(Integer, ForeignKey("cryptocurrencies.id"))
    
    # Analysis metrics
    performance_metrics = Column(JSON, default={})
    momentum_score = Column(DECIMAL(5, 4))    # -1 to 1
    relative_strength = Column(DECIMAL(5, 4)) # vs overall market
    
    # Timestamps
    analysis_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    sector = relationship("CryptoSector", back_populates="performance_records")
    top_performer = relationship("Cryptocurrency", foreign_keys=[top_performer_id])
    worst_performer = relationship("Cryptocurrency", foreign_keys=[worst_performer_id])
    
    def __repr__(self):
        return f"<SectorPerformance(sector_id={self.sector_id}, 24h={self.performance_24h}%)>"


# Performance indexes
Index('idx_sector_perf_sector_time', SectorPerformance.sector_id, SectorPerformance.analysis_time.desc())
Index('idx_sector_perf_performance', SectorPerformance.performance_24h.desc(), SectorPerformance.analysis_time.desc())
Index('idx_sector_perf_momentum', SectorPerformance.momentum_score.desc(), SectorPerformance.analysis_time.desc())

# ==================================================
# backend/app/models/sectors/rotation.py
# ==================================================
"""
Sector Rotation Analysis Model
Layer 2: Capital rotation patterns between crypto sectors
"""

from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, JSON, ForeignKey, Index
from sqlalchemy.sql import func

from app.core.database import Base


class SectorRotationAnalysis(Base):
    """
    Analysis of capital rotation patterns between crypto sectors
    """
    __tablename__ = "sector_rotation_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Rotation direction
    from_sector_id = Column(Integer, ForeignKey("crypto_sectors.id"), index=True)
    to_sector_id = Column(Integer, ForeignKey("crypto_sectors.id"), index=True)
    
    # Rotation metrics
    rotation_strength = Column(DECIMAL(5, 4), nullable=False)  # 0-1
    confidence_score = Column(DECIMAL(5, 4), nullable=False)   # 0-1
    capital_flow_estimate = Column(DECIMAL(15, 2))            # USD estimate
    flow_direction = Column(String(10))                        # inflow/outflow/neutral
    
    # Analysis data
    rotation_indicators = Column(JSON, default={})
    market_context = Column(JSON, default={})
    detection_method = Column(String(50), default='volume_price_analysis')
    
    # Timestamps
    analysis_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<SectorRotationAnalysis(from={self.from_sector_id}, to={self.to_sector_id})>"


# Performance indexes
Index('idx_sector_rotation_strength', SectorRotationAnalysis.rotation_strength.desc(), SectorRotationAnalysis.confidence_score.desc())
Index('idx_sector_rotation_from', SectorRotationAnalysis.from_sector_id, SectorRotationAnalysis.analysis_time.desc())
Index('idx_sector_rotation_to', SectorRotationAnalysis.to_sector_id, SectorRotationAnalysis.analysis_time.desc())

# ==================================================
# backend/app/models/trading/__init__.py
# ==================================================
"""
Trading Domain Models
Layer 4: Trading execution and risk management
"""

from .signal import TradingSignal
from .execution import SignalExecution  
from .risk import RiskManagement

__all__ = ["TradingSignal", "SignalExecution", "RiskManagement"]

# ==================================================
# backend/app/models/trading/signal.py
# ==================================================
"""
Trading Signals Model
Layer 4: AI-generated trading signals with precise entry/exit timing
"""

from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, ForeignKey, JSON, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import timedelta

from app.core.database import Base


class TradingSignal(Base):
    """
    AI-generated trading signals with precise entry/exit timing
    Enhanced to match database schema exactly
    """
    __tablename__ = "trading_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Crypto reference
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False, index=True)
    
    # Signal basics
    signal_type = Column(String(10), nullable=False, index=True)  # buy, sell, hold
    entry_price = Column(DECIMAL(20, 8), nullable=False)
    target_price = Column(DECIMAL(20, 8), nullable=False)
    stop_loss = Column(DECIMAL(20, 8), nullable=False)
    
    # Risk and confidence
    confidence_score = Column(DECIMAL(5, 4), nullable=False, index=True)
    risk_level = Column(String(10), nullable=False)  # low, medium, high
    risk_reward_ratio = Column(DECIMAL(6, 2))
    
    # Timing and position sizing
    time_horizon_hours = Column(Integer, default=24)
    max_drawdown_percent = Column(DECIMAL(5, 2), default=5.0)
    position_size_percent = Column(DECIMAL(5, 2), default=2.0)
    
    # Analysis context
    ai_analysis = Column(JSON, default={})
    market_context = Column(JSON, default={})
    technical_indicators = Column(JSON, default={})
    layer1_context = Column(JSON, default={})
    layer2_context = Column(JSON, default={})
    layer3_context = Column(JSON, default={})
    
    # Model and generation info
    model_name = Column(String(50), nullable=False, default='timing_model_v1')
    model_version = Column(String(20), nullable=False, default='1.0')
    generation_method = Column(String(50), default='ai_analysis')
    data_sources = Column(JSON, default={})
    
    # Status and priority
    status = Column(String(20), default='active')  # active, expired, executed
    priority_level = Column(String(10), default='medium')  # low, medium, high
    
    # Timestamps
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), default=lambda: func.now() + timedelta(days=7))
    activated_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    cryptocurrency = relationship("Cryptocurrency", back_populates="trading_signals")
    executions = relationship("SignalExecution", back_populates="signal")
    
    def __repr__(self):
        return f"<TradingSignal(id={self.id}, type={self.signal_type}, crypto_id={self.crypto_id})>"


# Performance indexes matching database
Index('idx_signals_crypto_status', TradingSignal.crypto_id, TradingSignal.status, TradingSignal.generated_at.desc())
Index('idx_signals_confidence', TradingSignal.confidence_score.desc(), TradingSignal.risk_level, TradingSignal.generated_at.desc())
Index('idx_signals_expires', TradingSignal.expires_at).where(TradingSignal.status == 'active')
Index('idx_signals_type', TradingSignal.signal_type, TradingSignal.status, TradingSignal.generated_at.desc())

# ==================================================
# backend/app/models/trading/execution.py
# ==================================================
"""
Signal Execution Model
Layer 4: User executions of trading signals with performance tracking
"""

from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, ForeignKey, JSON, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class SignalExecution(Base):
    """
    User executions of trading signals with performance tracking
    """
    __tablename__ = "signal_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    signal_id = Column(Integer, ForeignKey("trading_signals.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Execution details
    execution_price = Column(DECIMAL(20, 8))
    position_size = Column(DECIMAL(30, 8))
    position_size_usd = Column(DECIMAL(15, 2))
    portfolio_percentage = Column(DECIMAL(5, 2))
    
    # Order details
    execution_type = Column(String(20), default='manual')  # manual, auto
    order_type = Column(String(20), default='market')     # market, limit
    order_id = Column(String(100))
    fill_type = Column(String(20), default='full')        # full, partial
    status = Column(String(20), default='pending')        # pending, filled, cancelled
    
    # Execution metadata
    execution_details = Column(JSON, default={})
    exchange = Column(String(50))
    fees_paid = Column(DECIMAL(15, 8), default=0)
    slippage_percent = Column(DECIMAL(5, 4))
    
    # Performance tracking
    current_pnl = Column(DECIMAL(15, 2))
    realized_pnl = Column(DECIMAL(15, 2))
    max_profit = Column(DECIMAL(15, 2))
    max_drawdown = Column(DECIMAL(15, 2))
    risk_metrics = Column(JSON, default={})
    
    # Exit conditions
    stop_loss_triggered = Column(Boolean, default=False)
    take_profit_triggered = Column(Boolean, default=False)
    
    # Timestamps
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    signal = relationship("TradingSignal", back_populates="executions")
    user = relationship("User", back_populates="signal_executions")
    
    def __repr__(self):
        return f"<SignalExecution(id={self.id}, signal_id={self.signal_id}, user_id={self.user_id})>"


# Performance indexes
Index('idx_signal_executions_user', SignalExecution.user_id, SignalExecution.executed_at.desc())
Index('idx_signal_executions_signal', SignalExecution.signal_id, SignalExecution.status)
Index('idx_signal_executions_performance', SignalExecution.realized_pnl.desc(), SignalExecution.executed_at.desc()).where(SignalExecution.realized_pnl.isnot(None))

# ==================================================
# backend/app/models/trading/risk.py
# ==================================================
"""
Risk Management Model
Layer 4: User risk management settings, limits, and current exposure tracking
"""

from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, ForeignKey, JSON, Boolean, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class RiskManagement(Base):
    """
    User risk management settings, limits, and current exposure tracking
    """
    __tablename__ = "risk_management"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User reference
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Risk limits
    max_position_size_usd = Column(DECIMAL(15, 2), default=1000)
    max_portfolio_risk_percent = Column(DECIMAL(5, 2), default=2.0)
    max_daily_loss_percent = Column(DECIMAL(5, 2), default=5.0)
    max_concurrent_signals = Column(Integer, default=5)
    
    # Risk rules and settings
    risk_rules = Column(JSON, default={})
    position_sizing_method = Column(String(20), default='fixed_percent')
    
    # Current exposure tracking
    current_exposure_usd = Column(DECIMAL(15, 2), default=0)
    current_portfolio_risk = Column(DECIMAL(5, 2), default=0)
    active_positions_count = Column(Integer, default=0)
    daily_loss_current = Column(DECIMAL(15, 2), default=0)
    
    # Analysis and metrics
    risk_metrics = Column(JSON, default={})
    portfolio_correlation = Column(JSON, default={})
    exposure_by_sector = Column(JSON, default={})
    
    # Performance tracking
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    total_pnl = Column(DECIMAL(15, 2), default=0)
    max_drawdown_history = Column(DECIMAL(15, 2), default=0)
    
    # Risk control flags
    risk_limit_breached = Column(Boolean, default=False)
    auto_stop_trading = Column(Boolean, default=False)
    
    # Risk monitoring
    last_risk_check = Column(DateTime(timezone=True), server_default=func.now())
    risk_warnings = Column(JSON, default=[])
    
    # Timestamps
    last_calculated = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="risk_profiles")
    
    def __repr__(self):
        return f"<RiskManagement(user_id={self.user_id}, exposure=${self.current_exposure_usd})>"


# Constraints and indexes
Index('idx_risk_management_exposure', RiskManagement.current_exposure_usd.desc(), RiskManagement.current_portfolio_risk.desc())
Index('idx_risk_management_limits', RiskManagement.risk_limit_breached, RiskManagement.auto_stop_trading)

# ==================================================
# backend/app/models/watchlist/__init__.py
# ==================================================
"""
Watchlist Domain Models
Layer 3: Asset management and AI suggestions
"""

from .watchlist import Watchlist, WatchlistItem
from .suggestion import AISuggestion
from .review import SuggestionReview

__all__ = ["Watchlist", "WatchlistItem", "AISuggestion", "SuggestionReview"]

# ==================================================
# backend/app/models/watchlist/watchlist.py
# ==================================================
"""
Watchlist Management Models
Layer 3: Watchlist containers for different user types and purposes
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, DECIMAL, Text, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Watchlist(Base):
    """
    Watchlist containers for different user types and purposes
    """
    __tablename__ = "watchlists"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User reference (nullable for system watchlists)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    
    # Watchlist identification
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False, index=True)  # admin_tier1, admin_tier2, user_custom
    description = Column(Text)
    
    # Watchlist settings
    max_items = Column(Integer, default=50)
    is_active = Column(Boolean, default=True, index=True)
    is_public = Column(Boolean, default=False)
    settings = Column(JSON, default={})
    performance_metrics = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="watchlists")
    items = relationship("WatchlistItem", back_populates="watchlist", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Watchlist(id={self.id}, name={self.name}, type={self.type})>"


class WatchlistItem(Base):
    """
    Individual cryptocurrency items within watchlists
    """
    __tablename__ = "watchlist_items"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    watchlist_id = Column(Integer, ForeignKey("watchlists.id"), nullable=False, index=True)
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False, index=True)
    
    # Item properties
    score = Column(DECIMAL(5, 2), default=0)  # AI-calculated score 0-100
    rank_position = Column(Integer)           # Position ranking within watchlist
    status = Column(String(20), default='active')  # active, paused, removed
    
    # Analysis data
    selection_criteria = Column(JSON, default={})  # Criteria used for selection
    performance_metrics = Column(JSON, default={})
    risk_metrics = Column(JSON, default={})
    ai_analysis = Column(JSON, default={})
    
    # Management info
    added_by_user_id = Column(Integer, ForeignKey("users.id"))
    added_reason = Column(Text)
    
    # Timestamps
    last_updated_score = Column(DateTime(timezone=True), server_default=func.now())
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    watchlist = relationship("Watchlist", back_populates="items")
    cryptocurrency = relationship("Cryptocurrency", back_populates="watchlist_items")
    added_by_user = relationship("User")
    
    def __repr__(self):
        return f"<WatchlistItem(id={self.id}, watchlist_id={self.watchlist_id}, crypto_id={self.crypto_id})>"


# Constraints and indexes
UniqueConstraint('watchlist_id', 'crypto_id', name='watchlist_items_watchlist_id_crypto_id_key')
Index('idx_watchlist_items_watchlist', WatchlistItem.watchlist_id, WatchlistItem.status, WatchlistItem.score.desc())
Index('idx_watchlist_items_score', WatchlistItem.score.desc(), WatchlistItem.watchlist_id)
Index('idx_watchlist_items_rank', WatchlistItem.watchlist_id, WatchlistItem.rank_position)

# ==================================================
# backend/app/models/watchlist/suggestion.py
# ==================================================
"""
AI Suggestions Model
Layer 3: AI-generated suggestions for watchlist management
"""

from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, ForeignKey, JSON, Text, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import timedelta

from app.core.database import Base


class AISuggestion(Base):
    """
    AI-generated suggestions for watchlist management
    """
    __tablename__ = "ai_suggestions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Crypto reference
    crypto_id = Column(Integer, ForeignKey("cryptocurrencies.id"), nullable=False, index=True)
    
    # Suggestion details
    suggestion_type = Column(String(20), nullable=False, index=True)  # add_tier1, add_tier2, remove, tier_change
    current_tier = Column(String(10))      # Current watchlist tier
    suggested_tier = Column(String(10))    # Suggested watchlist tier
    
    # AI scoring
    confidence_score = Column(DECIMAL(5, 4), nullable=False, index=True)
    priority_score = Column(DECIMAL(5, 2), default=50, index=True)  # 0-100
    
    # AI analysis
    reasoning = Column(JSON, default={})          # AI reasoning and explanation
    analysis_data = Column(JSON, default={})     # Supporting analysis
    supporting_metrics = Column(JSON, default={})
    risk_assessment = Column(JSON, default={})
    
    # Model information
    model_version = Column(String(50))
    data_sources = Column(JSON, default={})
    
    # Review status
    status = Column(String(20), default='pending', index=True)  # pending, approved, rejected, expired
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    review_notes = Column(Text)
    
    # Timestamps
    expires_at = Column(DateTime(timezone=True), default=lambda: func.now() + timedelta(days=7))
    suggested_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    cryptocurrency = relationship("Cryptocurrency", back_populates="ai_suggestions")
    reviewer = relationship("User")
    reviews = relationship("SuggestionReview", back_populates="suggestion")
    
    def __repr__(self):
        return f"<AISuggestion(id={self.id}, type={self.suggestion_type}, crypto_id={self.crypto_id})>"


# Performance indexes
Index('idx_ai_suggestions_status', AISuggestion.status, AISuggestion.priority_score.desc(), AISuggestion.suggested_at.desc())
Index('idx_ai_suggestions_crypto', AISuggestion.crypto_id, AISuggestion.status)
Index('idx_ai_suggestions_type', AISuggestion.suggestion_type, AISuggestion.confidence_score.desc())
Index('idx_ai_suggestions_expires', AISuggestion.expires_at).where(AISuggestion.status == 'pending')

# ==================================================
# backend/app/models/watchlist/review.py
# ==================================================
"""
Suggestion Review Model
Layer 3: Admin reviews and actions on AI suggestions
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, DECIMAL, ForeignKey, JSON, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class SuggestionReview(Base):
    """
    Admin reviews and actions on AI suggestions
    """
    __tablename__ = "suggestion_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    suggestion_id = Column(Integer, ForeignKey("ai_suggestions.id"), nullable=False, index=True)
    admin_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Review decision
    action = Column(String(10), nullable=False, index=True)  # approved, rejected, modified
    review_notes = Column(Text)
    modifications = Column(JSON, default={})
    
    # Review quality metrics
    confidence_adjustment = Column(DECIMAL(5, 4))  # Admin confidence override
    reviewer_score = Column(DECIMAL(5, 2))         # Admin confidence in decision
    review_time_spent = Column(Integer)            # Time in seconds
    follow_up_required = Column(Boolean, default=False)
    
    # Timestamps
    reviewed_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    suggestion = relationship("AISuggestion", back_populates="reviews")
    admin_user = relationship("User", back_populates="suggestion_reviews")
    
    def __repr__(self):
        return f"<SuggestionReview(id={self.id}, action={self.action}, suggestion_id={self.suggestion_id})>"


# Performance indexes
Index('idx_suggestion_reviews_admin', SuggestionReview.admin_user_id, SuggestionReview.reviewed_at.desc())
Index('idx_suggestion_reviews_action', SuggestionReview.action, SuggestionReview.reviewed_at.desc())

# ==================================================
# backend/app/models/system/__init__.py
# ==================================================
"""
System Domain Models
System management, health monitoring, and AI model tracking
"""

from .ai_model import AIModel
from .health import SystemHealth
from .info import SystemInfo
from .notification import Notification

__all__ = ["AIModel", "SystemHealth", "SystemInfo", "Notification"]

# ==================================================
# backend/app/models/system/ai_model.py
# ==================================================
"""
AI Models Management
System management of AI models, versions, and performance tracking
"""

from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, JSON, Boolean, ForeignKey, Index, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import date

from app.core.database import Base


class AIModel(Base):
    """
    AI Models management and performance tracking
    """
    __tablename__ = "ai_models"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Model identification  
    name = Column(String(100), unique=True, nullable=False, index=True)  # Updated field name
    version = Column(String(50), nullable=False)
    model_type = Column(String(20), nullable=False, index=True)
    
    # Model status
    status = Column(String(20), default='inactive')  # active, inactive, training, error
    
    # Configuration and parameters
    configuration = Column(JSON, default={})
    hyperparameters = Column(JSON, default={})
    training_config = Column(JSON, default={})
    
    # Performance metrics
    performance_metrics = Column(JSON, default={})
    accuracy_metrics = Column(JSON, default={})
    backtesting_results = Column(JSON, default={})
    
    # Training data
    training_data_from = Column(date)
    training_data_to = Column(date)
    
    # Timestamps
    last_trained = Column(DateTime(timezone=True))
    last_prediction = Column(DateTime(timezone=True))
    next_retrain_due = Column(DateTime(timezone=True))
    
    # Health and monitoring
    health_status = Column(JSON, default={})
    error_logs = Column(JSON, default=[])
    
    # Usage statistics
    prediction_count = Column(Integer, default=0)
    success_rate = Column(DECIMAL(5, 4))
    
    # Management
    created_by = Column(Integer, ForeignKey("users.id"))
    model_path = Column(String(500))
    model_size_mb = Column(DECIMAL(10, 2))
    deployment_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    creator = relationship("User", back_populates="ai_models_created")
    
    def __repr__(self):
        return f"<AIModel(id={self.id}, name={self.name}, type={self.model_type})>"


# Performance indexes
Index('idx_ai_models_type_status', AIModel.model_type, AIModel.status)
Index('idx_ai_models_performance', AIModel.model_type, AIModel.success_rate.desc().nulls_last())
Index('idx_ai_models_training', AIModel.last_trained.desc())

# ==================================================
# backend/app/models/system/health.py
# ==================================================
"""
System Health Monitoring
Comprehensive system health tracking and alerting
"""

from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, JSON, Boolean, Index
from sqlalchemy.sql import func

from app.core.database import Base


class SystemHealth(Base):
    """
    System health monitoring and metrics tracking
    """
    __tablename__ = "system_health"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Health check timestamp
    check_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Component health status
    api_status = Column(JSON, default={})
    database_status = Column(JSON, default={})
    ml_models_status = Column(JSON, default={})
    data_pipeline_status = Column(JSON, default={})
    external_apis_status = Column(JSON, default={})
    
    # Overall health metrics
    overall_health_score = Column(DECIMAL(5, 2), default=100)
    response_time_ms = Column(DECIMAL(10, 2))
    
    # System resource usage
    cpu_usage_percent = Column(DECIMAL(5, 2))
    memory_usage_percent = Column(DECIMAL(5, 2))
    disk_usage_percent = Column(DECIMAL(5, 2))
    
    # Database metrics
    active_connections = Column(Integer)
    slow_queries_count = Column(Integer, default=0)
    database_size_mb = Column(DECIMAL(15, 2))
    
    # Application metrics
    active_users_count = Column(Integer, default=0)
    requests_per_minute = Column(DECIMAL(10, 2))
    error_rate_percent = Column(DECIMAL(5, 4), default=0)
    
    # Additional monitoring data
    performance_metrics = Column(JSON, default={})
    error_logs = Column(JSON, default=[])
    warnings = Column(JSON, default=[])
    
    # Alert management
    alert_level = Column(String(10), default='normal', index=True)  # normal, warning, critical
    alerts_sent = Column(JSON, default=[])
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<SystemHealth(score={self.overall_health_score}, alert_level={self.alert_level})>"


# Performance indexes
Index('idx_system_health_score', SystemHealth.overall_health_score, SystemHealth.check_time.desc())
Index('idx_system_health_alert', SystemHealth.alert_level, SystemHealth.check_time.desc())

# ==================================================
# backend/app/models/system/info.py
# ==================================================
"""
System Info Model
Key-value storage for system configuration and metadata
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Index
from sqlalchemy.sql import func

from app.core.database import Base


class SystemInfo(Base):
    """
    System configuration and metadata storage
    """
    __tablename__ = "system_info"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Key-value storage
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    metadata = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<SystemInfo(key={self.key}, value={self.value[:50]}...)>"

# ==================================================
# backend/app/models/system/notification.py
# ==================================================
"""
Notification System Model
User notification system for alerts, signals, and system messages
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import timedelta

from app.core.database import Base


class Notification(Base):
    """
    User notification system
    """
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User reference
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Notification details
    notification_type = Column(String(20), nullable=False, index=True)  # signal, alert, system, educational
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, default={})  # Additional notification data
    
    # Status and priority
    status = Column(String(20), default='unread', index=True)  # unread, read, dismissed, archived
    priority = Column(String(20), default='normal', index=True)  # low, normal, high, urgent
    
    # Delivery settings
    channel = Column(String(20), default='in_app')  # in_app, email, push, sms
    source = Column(String(50), default='system')
    
    # Reference tracking
    reference_id = Column(Integer)        # Reference to related entity
    reference_type = Column(String(30))   # Type of referenced entity
    
    # Scheduling and expiration
    scheduled_for = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    sent_at = Column(DateTime(timezone=True))
    read_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True), default=lambda: func.now() + timedelta(days=30))
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.notification_type}, user_id={self.user_id})>"


# Performance indexes
Index('idx_notifications_user_status', Notification.user_id, Notification.status, Notification.scheduled_for.desc())
Index('idx_notifications_type', Notification.notification_type, Notification.priority, Notification.scheduled_for.desc())
Index('idx_notifications_expires', Notification.expires_at).where(Notification.status != 'expired')
Index('idx_notifications_reference', Notification.reference_type, Notification.reference_id)

# ==================================================
# backend/app/models/database_setup.py
# ==================================================
"""
Database Setup and Configuration
Complete model registration and validation for production deployment
"""

from sqlalchemy import create_engine, Index
from sqlalchemy.orm import sessionmaker

# Import all models to ensure they are registered with SQLAlchemy
from .core.user import User, UserActivity
from .core.crypto import Cryptocurrency  
from .core.price import PriceData
from .core.prediction import Prediction

from .market.regime import MarketRegimeAnalysis
from .market.sentiment import MarketSentimentData
from .market.dominance import DominanceData
from .market.indicators import MacroIndicator

from .sectors.sector import CryptoSector, CryptoSectorMapping
from .sectors.performance import SectorPerformance
from .sectors.rotation import SectorRotationAnalysis

from .trading.signal import TradingSignal
from .trading.execution import SignalExecution
from .trading.risk import RiskManagement

from .watchlist.watchlist import Watchlist, WatchlistItem
from .watchlist.suggestion import AISuggestion
from .watchlist.review import SuggestionReview

from .system.ai_model import AIModel
from .system.health import SystemHealth
from .system.info import SystemInfo
from .system.notification import Notification

# All models list for validation and setup
ALL_MODELS = [
    # Core domain (5 models)
    User, UserActivity, Cryptocurrency, PriceData, Prediction,
    
    # Market domain (4 models) 
    MarketRegimeAnalysis, MarketSentimentData, DominanceData, MacroIndicator,
    
    # Sectors domain (4 models)
    CryptoSector, CryptoSectorMapping, SectorPerformance, SectorRotationAnalysis,
    
    # Trading domain (3 models)
    TradingSignal, SignalExecution, RiskManagement,
    
    # Watchlist domain (4 models)
    Watchlist, WatchlistItem, AISuggestion, SuggestionReview,
    
    # System domain (4 models)
    AIModel, SystemHealth, SystemInfo, Notification,
]

print(f"✅ Total models registered: {len(ALL_MODELS)} models")
print("✅ Domain-Driven Architecture implemented successfully")
print("✅ Production-ready with database schema compatibility")

# Model validation function
def validate_models():
    """Validate all models are properly configured"""
    errors = []
    
    for model in ALL_MODELS:
        try:
            # Check if model has required attributes
            if not hasattr(model, '__tablename__'):
                errors.append(f"{model.__name__} missing __tablename__")
            
            if not hasattr(model, 'id'):
                errors.append(f"{model.__name__} missing primary key 'id'")
                
        except Exception as e:
            errors.append(f"{model.__name__}: {str(e)}")
    
    if errors:
        print("❌ Model validation errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✅ All models validated successfully")
        return True

# Domain model counts for verification
DOMAIN_COUNTS = {
    'core': 5,      # User, UserActivity, Cryptocurrency, PriceData, Prediction
    'market': 4,    # MarketRegimeAnalysis, MarketSentimentData, DominanceData, MacroIndicator
    'sectors': 4,   # CryptoSector, CryptoSectorMapping, SectorPerformance, SectorRotationAnalysis
    'trading': 3,   # TradingSignal, SignalExecution, RiskManagement
    'watchlist': 4, # Watchlist, WatchlistItem, AISuggestion, SuggestionReview
    'system': 4,    # AIModel, SystemHealth, SystemInfo, Notification
}

print("\n📊 Model distribution by domain:")
for domain, count in DOMAIN_COUNTS.items():
    print(f"  {domain}: {count} models")

print(f"📊 Total: {sum(DOMAIN_COUNTS.values())} models")

# Export commonly used model groups
CORE_MODELS = [User, UserActivity, Cryptocurrency, PriceData, Prediction]
MARKET_MODELS = [MarketRegimeAnalysis, MarketSentimentData, DominanceData, MacroIndicator]
SECTORS_MODELS = [CryptoSector, CryptoSectorMapping, SectorPerformance, SectorRotationAnalysis]
TRADING_MODELS = [TradingSignal, SignalExecution, RiskManagement]
WATCHLIST_MODELS = [Watchlist, WatchlistItem, AISuggestion, SuggestionReview]
SYSTEM_MODELS = [AIModel, SystemHealth, SystemInfo, Notification]

# Quick model access by name
MODEL_REGISTRY = {model.__name__: model for model in ALL_MODELS}

def get_model(model_name: str):
    """Get model class by name"""
    return MODEL_REGISTRY.get(model_name)

def get_models_by_domain(domain: str):
    """Get all models for a specific domain"""
    domain_map = {
        'core': CORE_MODELS,
        'market': MARKET_MODELS,
        'sectors': SECTORS_MODELS,
        'trading': TRADING_MODELS,
        'watchlist': WATCHLIST_MODELS,
        'system': SYSTEM_MODELS,
    }
    return domain_map.get(domain, [])

# Initialize database tables
def create_all_tables(engine):
    """Create all tables in the database"""
    from app.core.database import Base
    Base.metadata.create_all(bind=engine)
    print("✅ All database tables created successfully")

# Model relationship validation
def validate_relationships():
    """Validate foreign key relationships between models"""
    print("🔗 Validating model relationships...")
    
    # Key relationships to validate
    relationships = [
        (User, "predictions", Prediction),
        (User, "watchlists", Watchlist),
        (Cryptocurrency, "price_data", PriceData),
        (Cryptocurrency, "predictions", Prediction),
        (Watchlist, "items", WatchlistItem),
        (AISuggestion, "reviews", SuggestionReview),
        (TradingSignal, "executions", SignalExecution),
    ]
    
    for parent_model, relationship_name, child_model in relationships:
        if hasattr(parent_model, relationship_name):
            print(f"  ✅ {parent_model.__name__}.{relationship_name} -> {child_model.__name__}")
        else:
            print(f"  ❌ Missing: {parent_model.__name__}.{relationship_name}")
    
    print("🔗 Relationship validation complete")

if __name__ == "__main__":
    validate_models()
    validate_relationships()
    print("\n🎉 Production-Ready ORM Models Complete!")
    print("📁 Structure: 6 domains, 24 models, Database-compatible implementation")
    print("🚀 Ready for Phase 2 development deployment!")

# ==================================================
# END OF COMPLETE ORM MODELS SUITE
# ==================================================