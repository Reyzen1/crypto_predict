# 🗄️ SQLAlchemy Models Planning - CryptoPredict
## Based on ERD Database Design (17_0_Datre.md)

### 📋 Overvند برنامه‌ریزی کامل برای پیاده‌سازی مدل‌های SQLAlchemy بر اساس طراحی ERD می‌باشد.

---

## 🏗️ Structure Organization

### 📁 Directory Structure (پیشنهادی بهبود یافته)

### 📁 ساختار نهایی مدل‌های SQLAlchemy
```
backend/app/models/
├── __init__.py
├── shared/
│   ├── __init__.py
│   ├── base.py                    # Base model classes
│   ├── mixins.py                  # Reusable mixins
│   └── enums.py                   # Enum definitions
├── user/
│   ├── __init__.py
│   ├── user.py                   # User model
│   ├── session.py                # UserSession model  
│   └── activity.py               # UserActivity model
├── asset/
│   ├── __init__.py
│   ├── asset.py                  # Asset model
│   ├── price_data.py             # PriceData model
│   └── price_data_archive.py     # PriceDataArchive model
├── ai/
│   ├── __init__.py
│   ├── models.py                 # AIModel model
│   ├── evaluations.py            # ModelEvaluation model
│   ├── training_jobs.py          # ModelTrainingJob model
│   └── prediction_jobs.py        # ModelPredictionJob model
├── macro/                         # Layer 1: Market-wide Analysis
│   ├── __init__.py
│   ├── metrics_snapshot.py       # MetricsSnapshot model
│   └── regime_analysis.py        # AIRegimeAnalysis model
├── sector/                        # Layer 2: Sector Analysis  
│   ├── __init__.py
│   ├── sector.py                 # Sector, SectorHistory, SectorMapping
│   ├── analysis.py               # AISectorAnalysis model
│   └── cross_analysis.py         # AICrossSectorAnalysis, SectorRotationFlow
├── selection/                     # Layer 3: Asset Selection & Management
│   ├── __init__.py
│   ├── watchlist.py              # Watchlist, WatchlistAsset  
│   ├── portfolio.py              # Portfolio, PortfolioAsset
│   └── analysis.py               # AIWatchlistAnalysis, AIPortfolioAnalysis
└── trading/                       # Layer 4: Trading Operations
    ├── __init__.py
    ├── signals.py                # AITradingSignal
    └── actions.py                # TradeAction, PortfolioAssetAnalysis
```





## 🤔 مقایسه روش‌های دسته‌بندی

### ✅ مزایا و معایب هر روش:

| روش | مزایا | معایب | مناسب برای |
|-----|-------|--------|------------|
| **Layer-based** | مطابق معماری تجاری، درک flow آسان | وابستگی پیچیده، تکرار کد | تیم‌های تخصصی هر لایه |
| **Domain-based** | کم coupling، maintain آسان، DDD | ممکن است layer ها مخفی شوند | تیم‌های backend-focused |
| **Hybrid** | ترکیب مزایای هر دو، انعطاف بالا | پیچیدگی بیشتر ساختار | پروژه‌های بزرگ |

### 🎯 توصیه نهایی:

**برای پروژه CryptoPredict، گزینه 1 (Domain-based) را پیشنهاد می‌دهم** چون:

1. **سادگی توسعه**: هر developer می‌تواند روی یک domain مستقل کار کند
2. **کم‌تر coupling**: تغییرات در یک domain کم‌تر روی بقیه تأثیر می‌گذارد  
3. **Test کردن آسان‌تر**: هر domain جداگانه قابل test است
4. **Reusability بهتر**: مدل‌های مشترک در shared قرار می‌گیرند
5. **مطابق با FastAPI best practices**: Route ها هم به همین شکل دسته‌بندی می‌شوند

### 📋 Mapping با Layer های تجاری:

| Layer | شاخه | مسئولیت | مدل‌های کلیدی |
|-------|------|----------|----------------|
| **Layer 1** | `macro/` | تحلیل کلان بازار | MetricsSnapshot, AIRegimeAnalysis |
| **Layer 2** | `sector/` | تحلیل سکتوری | Sector, AISectorAnalysis, AICrossSectorAnalysis |
| **Layer 3** | `selection/` | انتخاب و مدیریت دارایی | Watchlist, Portfolio, Analysis |
| **Layer 4** | `trading/` | عملیات معاملاتی | AITradingSignal, TradeAction |

### 🤔 گزینه‌های نام‌گذاری Layer 3:

| نام | مزایا | معایب | امتیاز |
|-----|-------|-------|--------|
| `portfolio/` | شناخته شده، استاندارد مالی | فقط Portfolio را تداعی می‌کند | 7/10 |
| `selection/` | دقیق همان نام Layer 3، جامع | ممکن است غیرمألوف باشد | 9/10 ⭐ |
| `investment/` | جامع اما عمومی | خیلی کلی، گنگ | 6/10 |
| `management/` | شامل مدیریت کلی | خیلی عمومی | 5/10 |

**انتخاب نهایی: `selection/`** چون دقیقاً همان نام Layer 3 است و هر دو watchlist و portfolio را شامل می‌شود.

### 🎯 ویژگی‌های ساختار:

- **`shared/`**: کلاس‌های پایه، mixins، و enums مشترک
- **`user/`**: مدیریت کاربران، sessions، و activities  
- **`asset/`**: دارایی‌ها و داده‌های قیمت
- **`ai/`**: مدل‌های هوش مصنوعی و jobs
- **`macro/`**: تحلیل کلان بازار (Layer 1)
- **`sector/`**: تحلیل سکتوری (Layer 2)  
- **`selection/`**: انتخاب و مدیریت دارایی (Layer 3)
- **`trading/`**: عملیات معاملاتی (Layer 4)

---

## 🔧 Core Components

### 1. Base Classes & Mixins

#### base.py
```python
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()

class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class IDMixin:
    """Mixin for primary key ID"""
    id = Column(Integer, primary_key=True, nullable=False)

class BaseModel(Base, IDMixin, TimestampMixin):
    """Abstract base model with common functionality"""
    __abstract__ = True
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"
```

#### mixins.py
```python
from sqlalchemy import Column, Boolean, Integer, Text, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship

class ActiveMixin:
    """Mixin for is_active field"""
    is_active = Column(Boolean, nullable=False, default=True)

class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    @hybrid_property
    def is_deleted(self):
        return self.deleted_at is not None

class UserTrackingMixin:
    """Mixin for tracking user who created/modified records"""
    added_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    last_modified_by = Column(Integer, ForeignKey('users.id'), nullable=False)

class ValidationMixin:
    """Mixin for data validation fields"""
    is_validated = Column(Boolean, nullable=False, default=False)
    
class AIAnalysisMixin:
    """Mixin for AI analysis common fields"""
    ai_confidence_score = Column(Numeric(4,2), nullable=True)
    signal_agreement_score = Column(Numeric(4,2), nullable=True) 
    analysis_data = Column(JSON, nullable=True, default={})
```

#### enums.py
```python
import enum

class UserRole(enum.Enum):
    ADMIN = "admin"
    PUBLIC = "public" 
    GUEST = "guest"

class SubscriptionPlan(enum.Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class AssetType(enum.Enum):
    CRYPTO = "crypto"
    STABLECOIN = "stablecoin"
    MACRO = "macro"
    INDEX = "index"

class TimeframeEnum(enum.Enum):
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    ONE_HOUR = "1h"
    FOUR_HOURS = "4h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1M"

class MarketRegime(enum.Enum):
    BULL = "Bull"
    BEAR = "Bear"
    SIDEWAYS = "Sideways"
    TRANSITION = "Transition"
    ACCUMULATION = "Accumulation"
    DISTRIBUTION = "Distribution"

class JobStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ModelType(enum.Enum):
    MACRO = "macro"
    SECTOR = "sector"
    ASSET = "asset"
    TIMING = "timing"

class ModelStatus(enum.Enum):
    ACTIVE = "active"
    TRAINING = "training"
    INACTIVE = "inactive"
    ERROR = "error"
    DEPRECATED = "deprecated"
```

---

## 📊 Model Implementations

### 2. User Management Models

#### user/user.py
```python
from sqlalchemy import Column, String, Boolean, Integer, Numeric, Text, DateTime, Enum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.mixins import SoftDeleteMixin
from app.models.enums import UserRole, SubscriptionPlan
from werkzeug.security import generate_password_hash, check_password_hash

class User(BaseModel, SoftDeleteMixin):
    __tablename__ = 'users'
    
    # Authentication & Basic Info
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.PUBLIC, index=True)
    
    # Account Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    login_count = Column(Integer, nullable=True, default=0)
    
    # Preferences & Localization
    preferences = Column(JSON, nullable=True, default={})
    timezone = Column(String(50), nullable=True, default='UTC')
    language = Column(String(10), nullable=False, default='en')
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Profile Info
    bio = Column(Text, nullable=True)
    profile_picture_url = Column(String(500), nullable=True)
    
    # Security
    reset_password_token = Column(String(255), nullable=True)
    reset_password_expires = Column(DateTime(timezone=True), nullable=True)
    email_verification_token = Column(String(255), nullable=True)
    email_verification_expires = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, nullable=True, default=0)
    lockout_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Referral System
    referral_code = Column(String(50), nullable=True, unique=True, index=True)
    referred_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    referral_count = Column(Integer, nullable=True, default=0)
    
    # Monetization
    account_balance = Column(Numeric(15,2), nullable=True, default=0.00)
    subscription_plan = Column(Enum(SubscriptionPlan), nullable=True, default=SubscriptionPlan.FREE, index=True)
    subscription_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Admin Notes
    notes = Column(Text, nullable=True)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", lazy='dynamic')
    activities = relationship("UserActivity", back_populates="user", lazy='dynamic')
    watchlists = relationship("Watchlist", back_populates="user", lazy='dynamic')
    portfolios = relationship("Portfolio", back_populates="user", lazy='dynamic')
    
    # Self-referential relationship for referrals
    referrer = relationship("User", remote_side=[id], backref="referrals")
    
    # Check Constraints (handled by PostgreSQL)
    __table_args__ = (
        CheckConstraint('login_count >= 0', name='chk_login_count_positive'),
        CheckConstraint('referral_count >= 0', name='chk_referral_count_positive'),
        CheckConstraint('failed_login_attempts >= 0', name='chk_failed_login_attempts_positive'),
        CheckConstraint('account_balance >= 0', name='chk_account_balance_positive'),
        Index('idx_users_email', 'email'),
        Index('idx_users_role', 'role'),
        Index('idx_users_is_active', 'is_active'),
        Index('idx_users_subscription_plan', 'subscription_plan'),
        Index('idx_users_referral_code', 'referral_code'),
        Index('idx_users_created_at', 'created_at'),
    )
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
        
    @property
    def full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email.split('@')[0]
```

#### user/user_session.py
```python
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import INET, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class UserSession(BaseModel):
    __tablename__ = 'user_sessions'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    session_token = Column(String(255), nullable=False, unique=True, index=True)
    refresh_token = Column(String(255), nullable=True)
    device_info = Column(JSON, nullable=True, default={})
    ip_address = Column(INET, nullable=True)
    is_active = Column(Boolean, nullable=True, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    activities = relationship("UserActivity", back_populates="session", lazy='dynamic')
```

#### user/user_activity.py  
```python
from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime
from sqlalchemy.dialects.postgresql import INET, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class UserActivity(BaseModel):
    __tablename__ = 'user_activities'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey('user_sessions.id'), nullable=False, index=True)
    activity_type = Column(String(50), nullable=False, index=True)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    action = Column(String(50), nullable=False, index=True)
    details = Column(JSON, nullable=True, default={})
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Only created_at needed (no updates)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="activities")
    session = relationship("UserSession", back_populates="activities")
```

### 3. Asset Management Models

#### asset/asset.py
```python
from sqlalchemy import Column, String, Text, Numeric, Integer, Boolean, DateTime, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.mixins import ActiveMixin
from app.models.enums import AssetType

class Asset(BaseModel, ActiveMixin):
    __tablename__ = 'assets'
    
    # Basic Info
    symbol = Column(String(20), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    asset_type = Column(Enum(AssetType), nullable=False, index=True)
    quote_currency = Column(String(10), nullable=True)
    external_ids = Column(JSON, nullable=True, default={})
    logo_url = Column(Text, nullable=True)
    links = Column(JSON, nullable=True, default={})
    description = Column(Text, nullable=True)
    
    # Market Data
    market_cap = Column(Numeric(30,2), nullable=True)
    market_cap_rank = Column(Integer, nullable=True, index=True)
    current_price = Column(Numeric(20,8), nullable=True)
    total_volume = Column(Numeric(30,2), nullable=True)
    circulating_supply = Column(Numeric(30,8), nullable=True)
    total_supply = Column(Numeric(30,8), nullable=True)
    max_supply = Column(Numeric(30,8), nullable=True)
    price_change_percentage_24h = Column(Numeric(10,4), nullable=True)
    price_change_percentage_7d = Column(Numeric(10,4), nullable=True)
    price_change_percentage_30d = Column(Numeric(10,4), nullable=True)
    ath = Column(Numeric(20,8), nullable=True)
    ath_date = Column(DateTime(timezone=True), nullable=True)
    atl = Column(Numeric(20,8), nullable=True)
    atl_date = Column(DateTime(timezone=True), nullable=True)
    metrics_details = Column(JSON, nullable=True, default={})
    
    # Usage Tracking
    timeframe_usage = Column(JSON, nullable=True, default={})
    last_accessed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    access_count = Column(Integer, nullable=False, default=0)
    is_supported = Column(Boolean, nullable=False, default=True)
    data_quality_score = Column(Integer, nullable=False, default=100)
    data_source = Column(String(20), nullable=False, default='coingecko', index=True)
    last_price_update = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    price_data = relationship("PriceData", back_populates="asset", lazy='dynamic')
    price_data_archive = relationship("PriceDataArchive", back_populates="asset", lazy='dynamic')
    sector_mappings = relationship("SectorMapping", back_populates="asset", lazy='dynamic')
    watchlist_assets = relationship("WatchlistAsset", back_populates="asset", lazy='dynamic')
    portfolio_assets = relationship("PortfolioAsset", back_populates="asset", lazy='dynamic')
    
    # Constraints & Indexes
    __table_args__ = (
        CheckConstraint('market_cap IS NULL OR market_cap >= 0', name='chk_market_cap_positive'),
        CheckConstraint('current_price IS NULL OR current_price > 0', name='chk_current_price_positive'),
        CheckConstraint('circulating_supply IS NULL OR circulating_supply >= 0', name='chk_supply_positive'),
        CheckConstraint('data_quality_score BETWEEN 0 AND 100', name='chk_data_quality'),
        CheckConstraint('market_cap_rank IS NULL OR market_cap_rank > 0', name='chk_market_cap_rank'),
        CheckConstraint('access_count >= 0', name='chk_access_count_positive'),
        Index('idx_assets_symbol', 'symbol'),
        Index('idx_assets_type_active', 'asset_type', 'is_active'),
        Index('idx_assets_market_cap_rank', 'market_cap_rank'),
        Index('idx_assets_last_accessed', 'last_accessed_at'),
        Index('idx_assets_data_source', 'data_source'),
    )
```

#### asset/price_data.py
```python
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, CheckConstraint, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.mixins import ValidationMixin
from app.models.enums import TimeframeEnum

class PriceData(BaseModel, ValidationMixin):
    __tablename__ = 'price_data'
    
    asset_id = Column(Integer, ForeignKey('assets.id', ondelete='CASCADE'), nullable=False, index=True)
    timeframe = Column(Enum(TimeframeEnum), nullable=False, index=True)
    
    # OHLCV Data
    open_price = Column(Numeric(20,8), nullable=False)
    high_price = Column(Numeric(20,8), nullable=False)
    low_price = Column(Numeric(20,8), nullable=False)
    close_price = Column(Numeric(20,8), nullable=False)
    volume = Column(Numeric(30,2), nullable=False, default=0)
    market_cap = Column(Numeric(30,2), nullable=True)
    trade_count = Column(Integer, nullable=True)
    vwap = Column(Numeric(20,8), nullable=True)
    
    # Technical Indicators (cached)
    technical_indicators = Column(JSON, nullable=True, default={})
    
    # Timing
    candle_time = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Relationships
    asset = relationship("Asset", back_populates="price_data")
    
    # Constraints & Indexes
    __table_args__ = (
        CheckConstraint(
            'low_price <= open_price AND low_price <= close_price AND high_price >= open_price AND high_price >= close_price',
            name='chk_ohlc_logic'
        ),
        CheckConstraint(
            'open_price > 0 AND high_price > 0 AND low_price > 0 AND close_price > 0',
            name='chk_prices_positive'
        ),
        CheckConstraint('volume >= 0', name='chk_volume_non_negative'),
        UniqueConstraint('asset_id', 'timeframe', 'candle_time', name='unique_asset_timeframe_candle'),
        Index('idx_price_data_asset_timeframe_time', 'asset_id', 'timeframe', 'candle_time'),
        Index('idx_price_data_candle_time', 'candle_time'),
        Index('idx_price_data_timeframe', 'timeframe'),
        Index('idx_price_data_volume', 'volume'),
    )
```

### 4. AI Models & Analysis

#### ai/ai_models.py
```python
from sqlalchemy import Column, String, Integer, Boolean, Numeric, DateTime, Text, CheckConstraint, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.enums import ModelType, ModelStatus

class AIModel(BaseModel):
    __tablename__ = 'ai_models'
    
    name = Column(String(100), nullable=False)
    version = Column(String(20), nullable=False)
    architecture = Column(String(50), nullable=False)
    model_type = Column(Enum(ModelType), nullable=False, index=True)
    status = Column(Enum(ModelStatus), nullable=False, default=ModelStatus.INACTIVE, index=True)
    
    # Configuration
    configuration = Column(JSON, nullable=True, default={})
    performance_metrics = Column(JSON, nullable=True, default={})
    training_features = Column(JSON, nullable=True, default={})
    training_data_range = Column(JSON, nullable=True, default={})
    training_data_timeframe = Column(String(10), nullable=False)
    target_variable = Column(String(50), nullable=False)
    
    # Schema
    input_schema = Column(JSON, nullable=True, default={})
    output_schema = Column(JSON, nullable=True, default={})
    
    # Health & Monitoring
    health_status = Column(JSON, nullable=True, default={})
    
    # Metadata
    training_notes = Column(Text, nullable=True)
    model_file_path = Column(String(100), nullable=True)
    framework = Column(String(50), nullable=True)
    deployment_environment = Column(String(20), nullable=True)
    
    # Activity Tracking
    last_trained = Column(DateTime(timezone=True), nullable=True)
    last_prediction = Column(DateTime(timezone=True), nullable=True)
    deployed_at = Column(DateTime(timezone=True), nullable=True)
    deprecated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Stats
    is_active = Column(Boolean, nullable=False, default=False, index=True)
    prediction_count = Column(Integer, nullable=False, default=0)
    model_size_mb = Column(Numeric(10,2), nullable=True)
    training_duration_minutes = Column(Integer, nullable=True)
    
    # Business Rules
    min_confidence_threshold = Column(Numeric(4,2), nullable=False, default=0.5)
    max_predictions_per_hour = Column(Integer, nullable=True)
    requires_manual_approval = Column(Boolean, nullable=True, default=False)
    
    # Relationships
    evaluations = relationship("ModelEvaluation", back_populates="model", lazy='dynamic')
    training_jobs = relationship("ModelTrainingJob", back_populates="model", lazy='dynamic')
    prediction_jobs = relationship("ModelPredictionJob", back_populates="model", lazy='dynamic')
    regime_analyses = relationship("AIRegimeAnalysis", back_populates="ai_model", lazy='dynamic')
    
    # Constraints & Indexes
    __table_args__ = (
        CheckConstraint('min_confidence_threshold BETWEEN 0 AND 1', name='chk_confidence_threshold'),
        CheckConstraint('prediction_count >= 0', name='chk_prediction_count_positive'),
        # Unique constraint for active models only (handled by partial index)
        Index('idx_unique_active_model', 'name', 'model_type', unique=True, postgresql_where=Column('is_active') == True),
        Index('idx_ai_models_name', 'name'),
        Index('idx_ai_models_type', 'model_type'),
        Index('idx_ai_models_status', 'status'),
        Index('idx_ai_models_active', 'is_active'),
        Index('idx_ai_models_created_at', 'created_at'),
    )
```

### 5. Layer 1: Macro Analysis Models

#### analysis/layer1/metrics_snapshot.py
```python
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, Text, CheckConstraint, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.mixins import ValidationMixin
from app.models.enums import TimeframeEnum

class MetricsSnapshot(BaseModel, ValidationMixin):
    __tablename__ = 'metrics_snapshot'
    
    # Core Info
    snapshot_time = Column(DateTime(timezone=True), nullable=False, index=True)
    timeframe = Column(Enum(TimeframeEnum), nullable=False, index=True)
    btc_price_usd = Column(Numeric(18,8), nullable=False)
    
    # Technical Indicators
    rsi_14 = Column(Numeric(5,2), nullable=True)
    sma_200 = Column(Numeric(30,8), nullable=True)
    ema_200 = Column(Numeric(30,8), nullable=True)
    
    # Market Sentiment
    fear_greed_index = Column(Numeric(5,2), nullable=True)
    google_trends_score = Column(Numeric(5,2), nullable=True)
    
    # Derivatives & Futures
    funding_rate_btc = Column(Numeric(10,6), nullable=True)
    open_interest_btc = Column(Numeric(30,2), nullable=True)
    
    # On-chain & Whale Flows
    whale_netflow_24h = Column(Numeric(30,2), nullable=True)
    active_addresses_btc = Column(Integer, nullable=True)
    
    # Composite & Health
    altcoin_dominance = Column(Numeric(5,2), nullable=True)
    liquidity_score = Column(Numeric(10,6), nullable=True)
    
    # Cycle & Returns
    halving_countdown_days = Column(Integer, nullable=True)
    weekly_return = Column(Numeric(5,4), nullable=True)
    monthly_return = Column(Numeric(5,4), nullable=True)
    
    # Dominance & Total Market-Cap Levels
    btc_dominance = Column(Numeric(5,2), nullable=True)
    eth_dominance = Column(Numeric(5,2), nullable=True)
    usdt_dominance = Column(Numeric(5,2), nullable=True)
    total_market_cap = Column(Numeric(18,2), nullable=True)
    
    # Intermarket Levels
    sp500 = Column(Numeric(10,2), nullable=True)
    gold = Column(Numeric(10,2), nullable=True)
    dxy = Column(Numeric(10,2), nullable=True)
    
    # Liquidations
    liquidations_long = Column(Numeric(30,2), nullable=True)
    liquidations_short = Column(Numeric(30,2), nullable=True)
    liquidation_zones = Column(JSON, nullable=True, default=[])
    
    # Extended Metrics
    extended_metrics = Column(JSON, nullable=True, default={})
    
    # Enhanced Core Metrics
    btc_eth_correlation_30d = Column(Numeric(6,4), nullable=True)
    btc_sp500_correlation_30d = Column(Numeric(6,4), nullable=True)
    us_10y_yield = Column(Numeric(8,4), nullable=True)
    vix_index = Column(Numeric(8,4), nullable=True)
    
    # Market Breadth & Quality
    crypto_market_breadth = Column(Numeric(6,2), nullable=True)
    new_highs_24h = Column(Integer, nullable=True)
    new_lows_24h = Column(Integer, nullable=True)
    momentum_index = Column(Numeric(8,4), nullable=True)
    
    # Data Quality & Metadata
    data_quality_flags = Column(JSON, nullable=True, default={})
    snapshot_version = Column(String(50), nullable=True)
    has_anomalies = Column(Boolean, nullable=False, default=False)
    data_source = Column(String(20), nullable=False, default='aggregated')
    
    # Performance Timing
    data_collection_started = Column(DateTime(timezone=True), nullable=True)
    data_collection_completed = Column(DateTime(timezone=True), nullable=True)
    collection_duration_ms = Column(Integer, nullable=True)
    
    # Relationships
    regime_analyses = relationship("AIRegimeAnalysis", back_populates="metrics_snapshot", lazy='dynamic')
    sector_analyses = relationship("AISectorAnalysis", back_populates="metrics_snapshot", lazy='dynamic')
    
    # Constraints & Indexes
    __table_args__ = (
        UniqueConstraint('snapshot_time', 'timeframe', name='unique_snapshot_time_timeframe'),
        CheckConstraint('fear_greed_index IS NULL OR fear_greed_index BETWEEN 0 AND 100', name='chk_fear_greed_range'),
        CheckConstraint('btc_dominance IS NULL OR btc_dominance BETWEEN 0 AND 100', name='chk_dominance_range'),
        CheckConstraint('btc_price_usd > 0', name='chk_btc_price_positive'),
        CheckConstraint('collection_duration_ms IS NULL OR collection_duration_ms >= 0', name='chk_collection_duration'),
        Index('idx_metrics_snapshot_time', 'snapshot_time'),
        Index('idx_metrics_snapshot_timeframe', 'timeframe'),
        Index('idx_metrics_snapshot_time_timeframe', 'snapshot_time', 'timeframe'),
        Index('idx_metrics_snapshot_btc_price', 'btc_price_usd'),
    )
```

### 6. Model Relationships Summary

```python
# Key Relationships Overview:

# User → UserSession (1:N)
# User → UserActivity (1:N)  
# User → Watchlist (1:N)
# User → Portfolio (1:N)

# Asset → PriceData (1:N)
# Asset → PriceDataArchive (1:N)
# Asset → SectorMapping (1:N)
# Asset → WatchlistAsset (1:N)
# Asset → PortfolioAsset (1:N)

# AIModel → ModelEvaluation (1:N)
# AIModel → ModelTrainingJob (1:N)
# AIModel → ModelPredictionJob (1:N)
# AIModel → AIRegimeAnalysis (1:N)

# MetricsSnapshot → AIRegimeAnalysis (1:N)
# MetricsSnapshot → AISectorAnalysis (1:N)
# MetricsSnapshot → AICrossSectorAnalysis (1:N)

# Sector → SectorHistory (1:N)
# Sector → SectorMapping (1:N)
# Sector → AISectorAnalysis (1:N)

# Watchlist → WatchlistAsset (1:N)
# Portfolio → PortfolioAsset (1:N)
```

---

## 🎯 Implementation Priority

### Phase 1: Core Foundation (Layer 1 Focus)
1. ✅ **shared/**: Base classes, mixins, enums
2. ✅ **user/**: User management models  
3. ✅ **asset/**: Asset models & price data
4. ✅ **ai/**: AI models framework
5. ✅ **macro/**: MetricsSnapshot, AIRegimeAnalysis

### Phase 2: Extended Analysis (Layer 2 & 3)
1. 🔄 **sector/**: Sector models & analysis
2. 🔄 **selection/**: Watchlist & Portfolio models
3. 🔄 AI analysis models for Layer 2 & 3

### Phase 3: Advanced Features (Layer 4)
1. ⏳ **trading/**: Trading signals & actions
2. ⏳ Advanced AI features & optimization
3. ⏳ Real-time processing & notifications

---

## 🔧 Technical Considerations

### Database Configuration
```python
# alembic/env.py configuration needed:
# - Enable JSON support for PostgreSQL
# - Configure timezone handling
# - Set up partitioning for large tables (price_data, metrics_snapshot)
# - Index optimization for time-series queries

# Key Indexes for Performance:
# 1. Time-based queries (candle_time, snapshot_time)
# 2. Asset-based filtering
# 3. User activity tracking
# 4. AI model lookups
```

### Validation & Business Logic
```python
# Implement in each model:
# 1. Data validation methods
# 2. Business rule enforcement
# 3. Calculated properties
# 4. Custom queries via class methods
# 5. Serialization methods for API responses
```

### Performance Optimization
```python
# 1. Lazy loading strategies
# 2. Query optimization with joins
# 3. Caching strategies for frequently accessed data
# 4. Partitioning for time-series data
# 5. Materialized views for complex aggregations
```

---

## 📋 Next Steps

1. **Create base infrastructure** (base.py, mixins.py, enums.py)
2. **Implement Layer 1 models** (User, Asset, AIModel, MetricsSnapshot, AIRegimeAnalysis)
3. **Set up Alembic migrations**
4. **Create model tests**
5. **Add serialization methods**
6. **Implement Layer 2 models**
7. **Add advanced relationships**
8. **Performance optimization**

---

> 📝 **Note**: این طرح ریزی بر اساس ERD کامل طراحی شده و آماده پیاده‌سازی تدریجی است. اولویت با Layer 1 (Macro Analysis) شروع شده و به سمت لایه‌های بالاتر ادامه می‌یابد.