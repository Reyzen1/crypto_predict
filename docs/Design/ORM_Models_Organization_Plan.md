# 🗃️ ORM Models File Organization Plan
## Recommended Structure for 29 Database Tables

---

## 📁 **Recommended Directory Structure:**

```
backend/app/models/
├── __init__.py                 # Import all models, define __all__
├── base.py                     # Base model with common fields
├── enums.py                    # All enums used across models
│
├── core/                       # Core system models (4 tables)
│   ├── __init__.py
│   ├── user.py                 # users table
│   ├── user_profile.py         # user_profiles table
│   ├── user_session.py         # user_sessions table
│   └── auth.py                 # authentication_logs table
│
├── market/                     # Market data models (2 tables)
│   ├── __init__.py
│   ├── cryptocurrency.py      # cryptocurrencies table
│   └── market_data.py          # market_data table
│
├── layer1/                     # Layer 1: Macro Analysis (4 tables)
│   ├── __init__.py
│   ├── macro_indicator.py      # macro_indicators table
│   ├── market_regime.py        # market_regimes table
│   ├── sentiment.py            # sentiment_data table
│   └── news.py                 # news_events table
│
├── layer2/                     # Layer 2: Sector Analysis (4 tables)
│   ├── __init__.py
│   ├── crypto_sector.py        # crypto_sectors table
│   ├── sector_analysis.py      # sector_analysis table
│   ├── sector_performance.py   # sector_performance table
│   └── sector_rotation.py      # sector_rotation_signals table
│
├── layer3/                     # Layer 3: Asset Selection (3 tables)
│   ├── __init__.py
│   ├── watchlist.py            # watchlists table
│   ├── watchlist_asset.py      # watchlist_assets table
│   └── asset_suggestion.py     # ai_asset_suggestions table
│
├── layer4/                     # Layer 4: Timing Signals (4 tables)
│   ├── __init__.py
│   ├── trading_signal.py       # trading_signals table
│   ├── signal_execution.py     # signal_executions table
│   ├── risk_management.py      # risk_management table
│   └── portfolio.py            # portfolio_tracking table
│
├── ai/                         # AI & ML Management (3 tables)
│   ├── __init__.py
│   ├── model.py                # ai_models table
│   ├── performance.py          # model_performance table
│   └── prediction.py           # predictions table
│
├── system/                     # System Management (5 tables)
│   ├── __init__.py
│   ├── health.py               # system_health table
│   ├── analytics.py            # analytics_data table
│   ├── api_log.py              # external_api_logs table
│   ├── task.py                 # background_tasks table
│   └── feedback.py             # suggestion_feedback table
│
└── relationships/              # Complex relationships and views
    ├── __init__.py
    ├── dashboard_views.py      # Dashboard aggregation models
    ├── analytics_views.py      # Analytics aggregation models
    └── cross_layer_relations.py # Inter-layer relationships
```

---

## 🏗️ **Implementation Priority Order:**

### **Phase 1: Core Foundation (Week 1)**
```python
# Priority 1: Core user and auth models
1. core/user.py              # Users table
2. core/user_profile.py      # User profiles  
3. core/auth.py              # Authentication logs
4. core/user_session.py      # User sessions
```

### **Phase 2: Market Data Foundation (Week 1)**
```python
# Priority 2: Basic market data
5. market/cryptocurrency.py  # Cryptocurrencies table
6. market/market_data.py     # Market data table
```

### **Phase 3: Layer 1 - Macro Analysis (Week 2)**
```python
# Priority 3: Macro analysis foundation
7. layer1/macro_indicator.py # Macro indicators
8. layer1/market_regime.py   # Market regimes
9. layer1/sentiment.py       # Sentiment data
10. layer1/news.py           # News events
```

### **Phase 4: Layer 3 - Watchlists (Week 2)**
```python
# Priority 4: Watchlist management (high user impact)
11. layer3/watchlist.py      # Watchlists table
12. layer3/watchlist_asset.py # Watchlist assets (CRITICAL MISSING)
13. layer3/asset_suggestion.py # AI asset suggestions
```

### **Phase 5: Layer 2 - Sector Analysis (Week 3)**
```python
# Priority 5: Sector analysis
14. layer2/crypto_sector.py  # Crypto sectors
15. layer2/sector_analysis.py # Sector analysis  
16. layer2/sector_performance.py # Sector performance
17. layer2/sector_rotation.py # Sector rotation signals
```

### **Phase 6: Layer 4 - Trading Signals (Week 3)**
```python
# Priority 6: Trading and risk management
18. layer4/trading_signal.py # Trading signals
19. layer4/signal_execution.py # Signal executions
20. layer4/risk_management.py # Risk management
21. layer4/portfolio.py      # Portfolio tracking
```

### **Phase 7: AI Management (Week 4)**
```python
# Priority 7: AI system management
22. ai/model.py              # AI models
23. ai/performance.py        # Model performance
24. ai/prediction.py         # Predictions
```

### **Phase 8: System Management (Week 4)**
```python
# Priority 8: System infrastructure
25. system/health.py         # System health
26. system/analytics.py      # Analytics data
27. system/api_log.py        # External API logs
28. system/task.py           # Background tasks
29. system/feedback.py       # Suggestion feedback
```

---

## 🎯 **File Content Structure:**

### **Example: base.py**
```python
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Base model with common fields for all tables"""
    pass

class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class IDMixin:
    """Mixin for primary key ID"""
    id = Column(Integer, primary_key=True, index=True)
```

### **Example: enums.py**
```python
from enum import Enum

class UserRole(str, Enum):
    GUEST = "guest"
    CASUAL = "casual"
    PROFESSIONAL = "professional"
    ADMIN = "admin"

class MarketRegime(str, Enum):
    BULL = "bull_market"
    BEAR = "bear_market"
    SIDEWAYS = "sideways"
    VOLATILE = "high_volatility"

class SignalType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    WATCH = "watch"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"
```

### **Example: layer3/watchlist_asset.py (CRITICAL MISSING)**
```python
from sqlalchemy import Column, Integer, String, Boolean, Numeric, ForeignKey, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from ..base import Base, TimestampMixin, IDMixin
from ..enums import RiskLevel

class WatchlistAsset(Base, IDMixin, TimestampMixin):
    """Watchlist Assets Table - Layer 3: Asset Selection"""
    __tablename__ = "watchlist_assets"

    # Foreign Keys
    watchlist_id = Column(Integer, ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False)
    cryptocurrency_id = Column(Integer, ForeignKey("cryptocurrencies.id", ondelete="CASCADE"), nullable=False)
    
    # Asset Configuration
    position = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    allocation_percent = Column(Numeric(5,2), default=0.0)
    target_allocation = Column(Numeric(5,2))
    
    # AI Analysis
    ai_score = Column(Numeric(5,2))
    risk_level = Column(String(10), default=RiskLevel.MEDIUM)
    confidence_score = Column(Numeric(5,2))
    
    # Performance Tracking
    performance_metrics = Column(JSONB, default={})
    alert_settings = Column(JSONB, default={})
    
    # Notes and Settings
    notes = Column(Text)
    custom_settings = Column(JSONB, default={})
    
    # Relationships
    watchlist = relationship("Watchlist", back_populates="assets")
    cryptocurrency = relationship("Cryptocurrency", back_populates="watchlist_entries")
    
    # Indexes
    __table_args__ = (
        Index('idx_watchlist_assets_watchlist', 'watchlist_id'),
        Index('idx_watchlist_assets_crypto', 'cryptocurrency_id'),
        Index('idx_watchlist_assets_active', 'is_active'),
        Index('idx_watchlist_assets_performance', 'ai_score', 'confidence_score'),
    )
```

---

## 🔧 **Best Practices:**

### **1. File Naming Convention:**
- Use singular nouns: `user.py`, not `users.py`
- Match table name without prefix: `trading_signal.py` for `trading_signals` table
- Use snake_case for files and PascalCase for classes

### **2. Import Organization:**
```python
# Standard imports first
from datetime import datetime
from typing import Optional, List

# Third-party imports
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

# Local imports
from ..base import Base, TimestampMixin
from ..enums import UserRole, RiskLevel
```

### **3. Model Class Structure:**
```python
class ModelName(Base, IDMixin, TimestampMixin):
    """Brief description and purpose"""
    __tablename__ = "table_name"
    
    # Columns (group by type)
    # Foreign keys first
    # Basic fields
    # JSON fields
    # Computed fields
    
    # Relationships
    
    # Table configuration
    __table_args__ = (
        # Indexes
        # Constraints
        # Comments
    )
    
    # Methods (if needed)
```

### **4. Cross-Module Dependencies:**
- Core models should have minimal dependencies
- Layer models can depend on core and market models
- AI models can depend on all layer models
- System models should be independent

---

## 🚀 **Next Steps:**

1. **Create base.py and enums.py first**
2. **Implement core/ models (users, auth)**
3. **Add market/ models (crypto, market_data)**
4. **Focus on critical missing models (WatchlistAsset, SignalAlert)**
5. **Follow the priority order for remaining models**

---

**📅 Last Updated:** January 30, 2025  
**🎯 Purpose:** Complete ORM model organization plan  
**✅ Status:** Ready for implementation - Start with Phase 1
