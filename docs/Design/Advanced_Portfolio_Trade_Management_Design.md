# Advanced Portfolio & Trade Management Design
## سیستم جامع مدیریت پورتفلیو و ترید کاتالوگ

---

## 🎯 **مسائل شناسایی شده و راه‌حل‌ها**

### **❌ مشکلات طراحی فعلی:**
1. **نبود Trade Cataloging System** - عدم ثبت احساسات و تحلیل در لحظه ترید
2. **فیلدهای اضافی** - محاسبه مواردی که قابل compute هستند
3. **عدم پشتیبانی External Assets** - فقط crypto در دیتابیس
4. **ارتباط ناقص Portfolio-Trades** - مشکل synchronization
5. **AI Integration ناقص** - نبود توصیه‌های هوشمند برای سطوح مختلف

---

## 🗂️ **طراحی جامع جدول‌ها**

### **1️⃣ Trade Catalog System - ثبت کامل هر ترید**

```sql
-- جدول اصلی Trade Catalog
CREATE TABLE trade_catalog (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Asset Information
    asset_type VARCHAR(20) NOT NULL,                       -- 'crypto', 'stock', 'forex', 'commodity', 'external'
    asset_symbol VARCHAR(20) NOT NULL,                     -- BTC, AAPL, EUR/USD, GOLD, etc
    crypto_id INTEGER REFERENCES cryptocurrencies(id),     -- فقط برای crypto assets
    external_asset_info JSONB,                             -- برای external assets
    
    -- Trade Execution Details (دقیق)
    trade_type VARCHAR(10) NOT NULL,                       -- 'long', 'short', 'buy', 'sell'
    entry_price NUMERIC(20,8) NOT NULL,
    exit_price NUMERIC(20,8),                             -- null اگر هنوز باز است
    quantity NUMERIC(20,8) NOT NULL,
    position_size_usd NUMERIC(15,2) NOT NULL,
    leverage_ratio NUMERIC(6,2) DEFAULT 1.0,              -- 1.0 = no leverage
    
    -- Timing Details (دقیق تا دقیقه و ساعت)
    entry_datetime TIMESTAMP WITH TIME ZONE NOT NULL,      -- دقیق تا دقیقه
    exit_datetime TIMESTAMP WITH TIME ZONE,                -- زمان بستن position
    timeframe VARCHAR(10) NOT NULL,                        -- '1m', '5m', '15m', '1h', '4h', '1d'
    session_type VARCHAR(20),                              -- 'london', 'new_york', 'tokyo', 'overlap'
    
    -- Emotional & Psychological State (مهم برای trade psychology)
    emotion_before_entry VARCHAR(20),                      -- 'confident', 'fearful', 'greedy', 'neutral', 'fomo'
    emotion_during_trade VARCHAR(20),                      -- احساس در حین ترید
    emotion_after_exit VARCHAR(20),                        -- احساس بعد از بستن
    confidence_level INTEGER CHECK (confidence_level BETWEEN 1 AND 10),
    stress_level INTEGER CHECK (stress_level BETWEEN 1 AND 10),
    
    -- Market Context (قابل محاسبه ولی مفید برای catalog)
    market_sentiment VARCHAR(20),                          -- 'bullish', 'bearish', 'sideways'
    volatility_level VARCHAR(10),                          -- 'low', 'medium', 'high', 'extreme'
    volume_profile VARCHAR(20),                            -- 'above_average', 'below_average', 'normal'
    
    -- Technical Analysis Context
    primary_setup VARCHAR(50),                             -- 'breakout', 'pullback', 'reversal', 'trend_follow'
    confirmation_signals JSONB,                            -- RSI, MACD, etc که استفاده شده
    chart_pattern VARCHAR(30),                             -- 'triangle', 'flag', 'head_shoulders'
    
    -- Risk Management
    planned_risk_percent NUMERIC(5,2) NOT NULL,            -- درصد ریسک برنامه‌ریزی شده
    actual_risk_percent NUMERIC(5,2),                      -- ریسک واقعی
    stop_loss_price NUMERIC(20,8),
    take_profit_price NUMERIC(20,8),
    risk_reward_ratio NUMERIC(6,2),                        -- محاسبه شده
    
    -- Performance (محاسبه شده)
    realized_pnl NUMERIC(15,2),                           -- سود/زیان محقق شده
    realized_pnl_percent NUMERIC(8,4),                    -- درصد سود/زیان
    fees_paid NUMERIC(15,2) DEFAULT 0,
    net_profit NUMERIC(15,2),                             -- بعد از کسر فی
    
    -- Trade Source & AI Integration
    trade_source VARCHAR(20) NOT NULL,                     -- 'manual', 'ai_signal', 'copy_trade', 'algorithm'
    signal_id INTEGER REFERENCES trading_signals(id),      -- اگر از AI آمده
    ai_confidence_score NUMERIC(3,2),                      -- اعتماد AI در هنگام پیشنهاد
    
    -- Learning & Notes
    trade_notes TEXT,                                       -- یادداشت‌های شخصی
    lessons_learned TEXT,                                   -- درس‌هایی که یاد گرفته
    mistakes_made TEXT,                                     -- اشتباهات صورت گرفته
    what_went_right TEXT,                                   -- چه چیزی درست بود
    what_went_wrong TEXT,                                   -- چه چیزی اشتباه بود
    
    -- Status & Tracking
    trade_status VARCHAR(20) DEFAULT 'open',               -- 'open', 'closed', 'stop_hit', 'target_hit'
    is_paper_trade BOOLEAN DEFAULT false,                  -- آیا demo trade بوده؟
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT check_trade_type CHECK (trade_type IN ('long', 'short', 'buy', 'sell')),
    CONSTRAINT check_asset_type CHECK (asset_type IN ('crypto', 'stock', 'forex', 'commodity', 'external')),
    CONSTRAINT check_trade_source CHECK (trade_source IN ('manual', 'ai_signal', 'copy_trade', 'algorithm')),
    CONSTRAINT check_trade_status CHECK (trade_status IN ('open', 'closed', 'stop_hit', 'target_hit', 'cancelled')),
    CONSTRAINT check_crypto_asset CHECK (
        (asset_type = 'crypto' AND crypto_id IS NOT NULL) OR
        (asset_type != 'crypto' AND crypto_id IS NULL)
    )
);

-- Indexes for trade_catalog
CREATE INDEX idx_trade_catalog_user ON trade_catalog(user_id, entry_datetime DESC);
CREATE INDEX idx_trade_catalog_asset ON trade_catalog(asset_type, asset_symbol);
CREATE INDEX idx_trade_catalog_crypto ON trade_catalog(crypto_id) WHERE crypto_id IS NOT NULL;
CREATE INDEX idx_trade_catalog_status ON trade_catalog(trade_status, entry_datetime DESC);
CREATE INDEX idx_trade_catalog_signal ON trade_catalog(signal_id) WHERE signal_id IS NOT NULL;
CREATE INDEX idx_trade_catalog_timeframe ON trade_catalog(timeframe, entry_datetime DESC);
CREATE INDEX idx_trade_catalog_performance ON trade_catalog(realized_pnl_percent DESC) WHERE trade_status = 'closed';
```

### **2️⃣ Enhanced Portfolio Management**

```sql
-- جدول پورتفلیو با پشتیبانی External Assets
CREATE TABLE enhanced_user_portfolio (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Asset Information (گسترده‌تر از قبل)
    asset_type VARCHAR(20) NOT NULL,                       -- 'crypto', 'stock', 'forex', 'commodity', 'external'
    asset_symbol VARCHAR(20) NOT NULL,                     -- symbol اصلی
    crypto_id INTEGER REFERENCES cryptocurrencies(id),     -- فقط برای crypto
    external_asset_data JSONB,                             -- اطلاعات external assets
    
    -- Current Holdings (محاسبه شده از trades)
    total_quantity NUMERIC(20,8) NOT NULL DEFAULT 0,       -- مجموع کل
    avg_entry_price NUMERIC(20,8),                         -- میانگین قیمت ورود
    total_invested_usd NUMERIC(15,2) NOT NULL DEFAULT 0,   -- کل سرمایه گذاری شده
    
    -- Portfolio Strategy
    allocation_target_percent NUMERIC(5,2),                -- درصد هدف در portfolio
    investment_thesis TEXT,                                 -- دلیل سرمایه‌گذاری
    investment_timeframe VARCHAR(20),                       -- 'short_term', 'medium_term', 'long_term'
    risk_category VARCHAR(15) DEFAULT 'medium',             -- 'conservative', 'moderate', 'aggressive'
    
    -- Risk Management (portfolio level)
    portfolio_stop_loss_percent NUMERIC(5,2),              -- SL کل پوزیشن
    portfolio_take_profit_percent NUMERIC(5,2),            -- TP کل پوزیشن
    max_allocation_percent NUMERIC(5,2) DEFAULT 10,        -- حداکثر تخصیص
    
    -- Status & Tracking
    is_active BOOLEAN DEFAULT true,
    position_status VARCHAR(20) DEFAULT 'active',           -- 'active', 'reducing', 'accumulating', 'exit_plan'
    last_rebalance_date TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT check_asset_type_portfolio CHECK (asset_type IN ('crypto', 'stock', 'forex', 'commodity', 'external')),
    CONSTRAINT check_crypto_portfolio CHECK (
        (asset_type = 'crypto' AND crypto_id IS NOT NULL) OR
        (asset_type != 'crypto' AND crypto_id IS NULL)
    ),
    CONSTRAINT uq_user_asset UNIQUE(user_id, asset_type, asset_symbol)
);
```

### **3️⃣ AI Recommendations System - توصیه‌های چندسطحه**

```sql
-- سیستم توصیه‌های هوشمند برای سطوح مختلف
CREATE TABLE ai_recommendations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Recommendation Context
    recommendation_type VARCHAR(30) NOT NULL,              -- 'trade_entry', 'risk_management', 'portfolio_allocation', 'position_sizing', 'exit_strategy'
    recommendation_level VARCHAR(20) NOT NULL,             -- 'beginner', 'intermediate', 'advanced', 'professional'
    target_entity_type VARCHAR(20),                        -- 'trade', 'portfolio', 'risk_profile', 'strategy'
    target_entity_id INTEGER,                              -- ID مربوط به trade یا portfolio
    
    -- AI Analysis
    ai_model_used VARCHAR(50) NOT NULL,
    confidence_score NUMERIC(3,2) NOT NULL,
    analysis_data JSONB NOT NULL,                          -- تحلیل کامل AI
    
    -- Recommendation Content
    recommendation_title VARCHAR(200) NOT NULL,
    recommendation_summary TEXT NOT NULL,
    detailed_analysis TEXT,
    action_items JSONB,                                     -- اقدامات پیشنهادی
    
    -- Risk Management Recommendations
    suggested_position_size NUMERIC(8,4),                  -- درصد پیشنهادی
    suggested_stop_loss NUMERIC(20,8),
    suggested_take_profit NUMERIC(20,8),
    risk_warning_level VARCHAR(10),                        -- 'low', 'medium', 'high', 'critical'
    
    -- Capital Management Recommendations
    portfolio_adjustment JSONB,                            -- تنظیمات portfolio
    diversification_advice TEXT,
    correlation_warnings JSONB,                            -- هشدار همبستگی
    
    -- Learning Recommendations
    educational_content JSONB,                             -- محتوای آموزشی پیشنهادی
    skill_improvement_areas JSONB,                         -- مهارت‌هایی که باید بهبود یابد
    
    -- User Interaction
    user_rating INTEGER CHECK (user_rating BETWEEN 1 AND 5),
    user_feedback TEXT,
    was_followed BOOLEAN,
    outcome_result JSONB,                                   -- نتیجه اجرای توصیه
    
    -- Status & Timing
    status VARCHAR(20) DEFAULT 'active',                   -- 'active', 'followed', 'ignored', 'expired'
    priority_level VARCHAR(10) DEFAULT 'medium',           -- 'low', 'medium', 'high', 'urgent'
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT check_recommendation_type CHECK (recommendation_type IN (
        'trade_entry', 'risk_management', 'portfolio_allocation', 
        'position_sizing', 'exit_strategy', 'diversification', 'learning'
    )),
    CONSTRAINT check_recommendation_level CHECK (recommendation_level IN (
        'beginner', 'intermediate', 'advanced', 'professional'
    ))
);

-- Indexes for ai_recommendations
CREATE INDEX idx_ai_recommendations_user ON ai_recommendations(user_id, created_at DESC);
CREATE INDEX idx_ai_recommendations_type ON ai_recommendations(recommendation_type, recommendation_level);
CREATE INDEX idx_ai_recommendations_status ON ai_recommendations(status, priority_level);
CREATE INDEX idx_ai_recommendations_target ON ai_recommendations(target_entity_type, target_entity_id);
```

---

## 🔄 **Portfolio-Trade Synchronization Logic**

### **روش هیبرید پیشنهادی:**

```sql
-- Trigger برای آپدیت خودکار portfolio از trades
CREATE OR REPLACE FUNCTION sync_portfolio_from_trades()
RETURNS TRIGGER AS $$
DECLARE
    portfolio_record RECORD;
    total_qty NUMERIC(20,8);
    avg_price NUMERIC(20,8);
    total_invested NUMERIC(15,2);
BEGIN
    -- پیدا کردن یا ایجاد portfolio record
    SELECT * INTO portfolio_record 
    FROM enhanced_user_portfolio 
    WHERE user_id = NEW.user_id 
    AND asset_symbol = NEW.asset_symbol 
    AND asset_type = NEW.asset_type;
    
    -- محاسبه مجدد از تمام trades
    SELECT 
        COALESCE(SUM(
            CASE 
                WHEN trade_type IN ('buy', 'long') THEN quantity
                WHEN trade_type IN ('sell', 'short') THEN -quantity
            END
        ), 0),
        
        COALESCE(AVG(
            CASE 
                WHEN trade_type IN ('buy', 'long') THEN entry_price
            END
        ), 0),
        
        COALESCE(SUM(
            CASE 
                WHEN trade_type IN ('buy', 'long') THEN position_size_usd
                WHEN trade_type IN ('sell', 'short') THEN -position_size_usd
            END
        ), 0)
    INTO total_qty, avg_price, total_invested
    FROM trade_catalog 
    WHERE user_id = NEW.user_id 
    AND asset_symbol = NEW.asset_symbol 
    AND asset_type = NEW.asset_type
    AND trade_status = 'closed';
    
    -- آپدیت یا insert portfolio
    INSERT INTO enhanced_user_portfolio (
        user_id, asset_type, asset_symbol, crypto_id,
        total_quantity, avg_entry_price, total_invested_usd
    ) VALUES (
        NEW.user_id, NEW.asset_type, NEW.asset_symbol, NEW.crypto_id,
        total_qty, avg_price, total_invested
    )
    ON CONFLICT (user_id, asset_type, asset_symbol)
    DO UPDATE SET
        total_quantity = EXCLUDED.total_quantity,
        avg_entry_price = EXCLUDED.avg_entry_price,
        total_invested_usd = EXCLUDED.total_invested_usd,
        updated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger برای sync خودکار
CREATE TRIGGER trigger_sync_portfolio
    AFTER INSERT OR UPDATE OR DELETE ON trade_catalog
    FOR EACH ROW
    EXECUTE FUNCTION sync_portfolio_from_trades();
```

---

## 📊 **Views تحلیلی پیشرفته**

### **1️⃣ Trade Performance Analytics:**

```sql
CREATE VIEW v_trade_performance_analytics AS
SELECT 
    tc.*,
    
    -- Performance Metrics
    CASE 
        WHEN tc.trade_status = 'closed' THEN
            (tc.exit_price - tc.entry_price) / tc.entry_price * 100
        ELSE NULL
    END as return_percent,
    
    -- Risk Metrics
    CASE 
        WHEN tc.stop_loss_price IS NOT NULL THEN
            ABS(tc.entry_price - tc.stop_loss_price) / tc.entry_price * 100
    END as actual_risk_percent,
    
    -- Psychology Scoring
    CASE 
        WHEN tc.emotion_before_entry = 'confident' AND tc.emotion_after_exit IN ('satisfied', 'confident') THEN 'good_psychology'
        WHEN tc.emotion_before_entry IN ('fearful', 'fomo') THEN 'poor_psychology'
        ELSE 'neutral_psychology'
    END as psychology_score,
    
    -- Time Analysis
    EXTRACT(EPOCH FROM (tc.exit_datetime - tc.entry_datetime)) / 3600 as holding_hours,
    
    -- Market Timing
    CASE 
        WHEN EXTRACT(hour FROM tc.entry_datetime) BETWEEN 8 AND 16 THEN 'market_hours'
        WHEN EXTRACT(hour FROM tc.entry_datetime) BETWEEN 17 AND 23 THEN 'after_hours'
        ELSE 'overnight'
    END as entry_timing,
    
    -- AI Comparison
    CASE 
        WHEN tc.signal_id IS NOT NULL AND tc.trade_status = 'closed' THEN
            tc.realized_pnl_percent - (
                SELECT predicted_return 
                FROM trading_signals 
                WHERE id = tc.signal_id
            )
    END as ai_vs_actual_performance

FROM trade_catalog tc;
```

### **2️⃣ Portfolio Health Dashboard:**

```sql
CREATE VIEW v_portfolio_health_dashboard AS
SELECT 
    eup.user_id,
    eup.asset_symbol,
    eup.asset_type,
    
    -- Current Status
    eup.total_quantity,
    eup.avg_entry_price,
    eup.total_invested_usd,
    
    -- Performance (real-time calculation needed)
    CASE 
        WHEN eup.asset_type = 'crypto' THEN
            (c.current_price - eup.avg_entry_price) / eup.avg_entry_price * 100
    END as unrealized_pnl_percent,
    
    -- Risk Analysis
    eup.portfolio_stop_loss_percent,
    eup.max_allocation_percent,
    
    -- AI Recommendations Count
    (SELECT COUNT(*) 
     FROM ai_recommendations ar 
     WHERE ar.user_id = eup.user_id 
     AND ar.status = 'active'
     AND ar.target_entity_type = 'portfolio'
    ) as active_ai_recommendations,
    
    -- Recent Trade Activity
    (SELECT COUNT(*) 
     FROM trade_catalog tc 
     WHERE tc.user_id = eup.user_id 
     AND tc.asset_symbol = eup.asset_symbol
     AND tc.entry_datetime > NOW() - INTERVAL '30 days'
    ) as trades_last_30_days,
    
    -- Risk Warnings
    CASE 
        WHEN eup.total_invested_usd > (eup.max_allocation_percent / 100) * 10000 THEN 'overallocated'
        WHEN eup.position_status = 'exit_plan' THEN 'exit_planned'
        ELSE 'normal'
    END as risk_status

FROM enhanced_user_portfolio eup
LEFT JOIN cryptocurrencies c ON eup.crypto_id = c.id
WHERE eup.is_active = true;
```

---

## 🤖 **AI Recommendation Examples برای سطوح مختلف**

### **سطح مبتدی:**
```json
{
  "recommendation_type": "risk_management",
  "recommendation_level": "beginner",
  "title": "کاهش ریسک معامله شما",
  "summary": "ریسک این معامله بیش از حد مجاز است",
  "action_items": [
    {
      "action": "reduce_position_size",
      "current_size": "5%",
      "suggested_size": "2%",
      "reason": "برای تازه‌کارها حداکثر 2% ریسک در هر معامله"
    }
  ],
  "educational_content": {
    "article": "مدیریت ریسک برای مبتدیان",
    "video": "چگونه سایز پوزیشن محاسبه کنیم"
  }
}
```

### **سطح حرفه‌ای:**
```json
{
  "recommendation_type": "portfolio_allocation",
  "recommendation_level": "professional", 
  "title": "بهینه‌سازی همبستگی پورتفلیو",
  "analysis_data": {
    "correlation_matrix": {...},
    "sector_exposure": {...},
    "risk_metrics": {...}
  },
  "action_items": [
    {
      "action": "rebalance_sectors",
      "details": "کاهش exposure در DeFi tokens از 40% به 25%"
    },
    {
      "action": "add_hedge_position", 
      "asset": "USDT",
      "percentage": "15%"
    }
  ]
}
```

---

## ✅ **مزایای طراحی جدید:**

1. **✅ Complete Trade Cataloging** - ثبت کامل احساسات، تحلیل، و جزئیات
2. **✅ Smart Portfolio Sync** - ترکیب manual entry + auto calculation
3. **✅ External Asset Support** - پشتیبانی کامل از external assets
4. **✅ Multi-Level AI Recommendations** - توصیه‌های متناسب با سطح کاربر
5. **✅ Advanced Analytics** - تحلیل‌های عمیق performance و psychology
6. **✅ Flexible Risk Management** - مدیریت ریسک در سطح trade و portfolio
7. **✅ Learning Integration** - ثبت lessons learned و continuous improvement

این طراحی مشکلات شناسایی شده را حل می‌کند و یک سیستم کامل trade management فراهم می‌کند.
