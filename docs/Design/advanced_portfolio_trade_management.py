# Database Migration: Advanced Portfolio & Trade Management
# Portfolio-Trade Synchronization with Enhanced Analytics

"""
Advanced Portfolio & Trade Management Database Migration
========================================================

This migration implements:
1. Trade Catalog System with psychological tracking
2. Enhanced Portfolio Management with external assets
3. AI Recommendations System for multi-level users
4. Automatic Portfolio-Trade Synchronization
5. Advanced Analytics Views
6. Portfolio Health Monitoring

Created: September 2025
"""

# ============================================================================
# 1. CREATE TABLES
# ============================================================================

CREATE_TRADE_CATALOG_TABLE = """
-- Trade Catalog System for comprehensive trade tracking
CREATE TABLE IF NOT EXISTS trade_catalog (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Asset Information (Multiple asset types support)
    asset_type VARCHAR(20) NOT NULL CHECK (asset_type IN ('crypto', 'stock', 'forex', 'commodity', 'external')),
    asset_symbol VARCHAR(20) NOT NULL,
    crypto_id INTEGER REFERENCES cryptocurrencies(id),
    external_asset_info JSONB DEFAULT '{}',
    
    -- Trade Execution Details
    trade_type VARCHAR(10) NOT NULL CHECK (trade_type IN ('long', 'short', 'buy', 'sell')),
    entry_price NUMERIC(20,8) NOT NULL,
    exit_price NUMERIC(20,8),
    quantity NUMERIC(20,8) NOT NULL,
    position_size_usd NUMERIC(15,2) NOT NULL,
    leverage_ratio NUMERIC(6,2) DEFAULT 1.0,
    
    -- Precise Timing
    entry_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    exit_datetime TIMESTAMP WITH TIME ZONE,
    timeframe VARCHAR(10) NOT NULL,
    session_type VARCHAR(20),
    
    -- Psychological State (Critical for trading psychology)
    emotion_before_entry VARCHAR(20),
    emotion_during_trade VARCHAR(20), 
    emotion_after_exit VARCHAR(20),
    confidence_level INTEGER CHECK (confidence_level BETWEEN 1 AND 10),
    stress_level INTEGER CHECK (stress_level BETWEEN 1 AND 10),
    
    -- Market Context
    market_sentiment VARCHAR(20),
    volatility_level VARCHAR(10),
    volume_profile VARCHAR(20),
    
    -- Technical Analysis
    primary_setup VARCHAR(50),
    confirmation_signals JSONB DEFAULT '{}',
    chart_pattern VARCHAR(30),
    
    -- Risk Management
    planned_risk_percent NUMERIC(5,2) NOT NULL,
    actual_risk_percent NUMERIC(5,2),
    stop_loss_price NUMERIC(20,8),
    take_profit_price NUMERIC(20,8),
    risk_reward_ratio NUMERIC(6,2),
    
    -- Performance
    realized_pnl NUMERIC(15,2),
    realized_pnl_percent NUMERIC(8,4),
    fees_paid NUMERIC(15,2) DEFAULT 0,
    net_profit NUMERIC(15,2),
    
    -- AI Integration
    trade_source VARCHAR(20) NOT NULL CHECK (trade_source IN ('manual', 'ai_signal', 'copy_trade', 'algorithm')),
    signal_id INTEGER REFERENCES trading_signals(id),
    ai_confidence_score NUMERIC(3,2),
    
    -- Learning
    trade_notes TEXT,
    lessons_learned TEXT,
    mistakes_made TEXT,
    what_went_right TEXT,
    what_went_wrong TEXT,
    
    -- Status
    trade_status VARCHAR(20) DEFAULT 'open' CHECK (trade_status IN ('open', 'closed', 'stop_hit', 'target_hit', 'cancelled')),
    is_paper_trade BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT check_crypto_asset_consistency CHECK (
        (asset_type = 'crypto' AND crypto_id IS NOT NULL) OR 
        (asset_type != 'crypto' AND crypto_id IS NULL)
    )
);
"""

CREATE_ENHANCED_PORTFOLIO_TABLE = """
-- Enhanced Portfolio with External Assets Support
CREATE TABLE IF NOT EXISTS enhanced_user_portfolio (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Asset Information  
    asset_type VARCHAR(20) NOT NULL CHECK (asset_type IN ('crypto', 'stock', 'forex', 'commodity', 'external')),
    asset_symbol VARCHAR(20) NOT NULL,
    crypto_id INTEGER REFERENCES cryptocurrencies(id),
    external_asset_data JSONB DEFAULT '{}',
    
    -- Current Holdings (Calculated from trades)
    total_quantity NUMERIC(20,8) NOT NULL DEFAULT 0,
    avg_entry_price NUMERIC(20,8),
    total_invested_usd NUMERIC(15,2) NOT NULL DEFAULT 0,
    
    -- Strategy
    allocation_target_percent NUMERIC(5,2),
    investment_thesis TEXT,
    investment_timeframe VARCHAR(20) CHECK (investment_timeframe IN ('short_term', 'medium_term', 'long_term')),
    risk_category VARCHAR(15) DEFAULT 'medium' CHECK (risk_category IN ('conservative', 'moderate', 'aggressive')),
    
    -- Risk Management
    portfolio_stop_loss_percent NUMERIC(5,2),
    portfolio_take_profit_percent NUMERIC(5,2),
    max_allocation_percent NUMERIC(5,2) DEFAULT 10,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    position_status VARCHAR(20) DEFAULT 'active' CHECK (position_status IN ('active', 'reducing', 'accumulating', 'exit_plan')),
    last_rebalance_date TIMESTAMP WITH TIME ZONE,
    
    -- AI Integration
    ai_score NUMERIC(3,2),
    ai_recommendation VARCHAR(20),
    last_ai_analysis TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT uq_user_asset UNIQUE(user_id, asset_type, asset_symbol),
    CONSTRAINT check_crypto_portfolio_consistency CHECK (
        (asset_type = 'crypto' AND crypto_id IS NOT NULL) OR 
        (asset_type != 'crypto' AND crypto_id IS NULL)
    )
);
"""

CREATE_AI_RECOMMENDATIONS_TABLE = """
-- Multi-Level AI Recommendations System
CREATE TABLE IF NOT EXISTS ai_recommendations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Classification
    recommendation_type VARCHAR(30) NOT NULL CHECK (recommendation_type IN (
        'trade_entry', 'risk_management', 'portfolio_allocation', 
        'position_sizing', 'exit_strategy', 'diversification', 'learning'
    )),
    recommendation_level VARCHAR(20) NOT NULL CHECK (recommendation_level IN ('beginner', 'intermediate', 'advanced', 'professional')),
    target_entity_type VARCHAR(20),
    target_entity_id INTEGER,
    
    -- AI Analysis
    ai_model_used VARCHAR(50) NOT NULL,
    confidence_score NUMERIC(3,2) NOT NULL CHECK (confidence_score >= 0.00 AND confidence_score <= 1.00),
    analysis_data JSONB NOT NULL,
    
    -- Content
    recommendation_title VARCHAR(200) NOT NULL,
    recommendation_summary TEXT NOT NULL,
    detailed_analysis TEXT,
    action_items JSONB DEFAULT '{}',
    
    -- Specific Recommendations
    suggested_position_size NUMERIC(8,4),
    suggested_stop_loss NUMERIC(20,8),
    suggested_take_profit NUMERIC(20,8),
    risk_warning_level VARCHAR(10),
    
    -- Portfolio Management
    portfolio_adjustment JSONB DEFAULT '{}',
    diversification_advice TEXT,
    correlation_warnings JSONB DEFAULT '{}',
    
    -- Learning
    educational_content JSONB DEFAULT '{}',
    skill_improvement_areas JSONB DEFAULT '{}',
    
    -- User Interaction
    user_rating INTEGER CHECK (user_rating BETWEEN 1 AND 5),
    user_feedback TEXT,
    was_followed BOOLEAN DEFAULT false,
    outcome_result JSONB DEFAULT '{}',
    
    -- Status
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'followed', 'ignored', 'expired')),
    priority_level VARCHAR(10) DEFAULT 'medium' CHECK (priority_level IN ('low', 'medium', 'high', 'urgent')),
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE
);
"""

# ============================================================================
# 2. CREATE INDEXES
# ============================================================================

CREATE_INDEXES = """
-- Trade Catalog Indexes
CREATE INDEX IF NOT EXISTS idx_trade_catalog_user ON trade_catalog(user_id, entry_datetime DESC);
CREATE INDEX IF NOT EXISTS idx_trade_catalog_asset ON trade_catalog(asset_type, asset_symbol);
CREATE INDEX IF NOT EXISTS idx_trade_catalog_crypto ON trade_catalog(crypto_id) WHERE crypto_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trade_catalog_status ON trade_catalog(trade_status, entry_datetime DESC);
CREATE INDEX IF NOT EXISTS idx_trade_catalog_signal ON trade_catalog(signal_id) WHERE signal_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trade_catalog_timeframe ON trade_catalog(timeframe, entry_datetime DESC);
CREATE INDEX IF NOT EXISTS idx_trade_catalog_performance ON trade_catalog(realized_pnl_percent DESC) WHERE trade_status = 'closed';

-- Enhanced Portfolio Indexes
CREATE INDEX IF NOT EXISTS idx_enhanced_portfolio_user ON enhanced_user_portfolio(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_enhanced_portfolio_asset ON enhanced_user_portfolio(asset_type, asset_symbol);
CREATE INDEX IF NOT EXISTS idx_enhanced_portfolio_crypto ON enhanced_user_portfolio(crypto_id) WHERE crypto_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_enhanced_portfolio_status ON enhanced_user_portfolio(position_status, last_rebalance_date);

-- AI Recommendations Indexes
CREATE INDEX IF NOT EXISTS idx_ai_recommendations_user ON ai_recommendations(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_recommendations_type ON ai_recommendations(recommendation_type, recommendation_level);
CREATE INDEX IF NOT EXISTS idx_ai_recommendations_status ON ai_recommendations(status, priority_level);
CREATE INDEX IF NOT EXISTS idx_ai_recommendations_target ON ai_recommendations(target_entity_type, target_entity_id);
"""

# ============================================================================
# 3. CREATE SYNCHRONIZATION TRIGGERS
# ============================================================================

CREATE_SYNC_FUNCTION = """
-- Function to synchronize portfolio from trade catalog
CREATE OR REPLACE FUNCTION sync_portfolio_from_trades()
RETURNS TRIGGER AS $$
DECLARE
    total_qty NUMERIC(20,8) := 0;
    avg_price NUMERIC(20,8) := 0;
    total_invested NUMERIC(15,2) := 0;
    total_buy_qty NUMERIC(20,8) := 0;
    total_buy_cost NUMERIC(15,2) := 0;
BEGIN
    -- Calculate aggregated position from all closed trades
    SELECT 
        COALESCE(SUM(
            CASE 
                WHEN trade_type IN ('buy', 'long') THEN quantity
                WHEN trade_type IN ('sell', 'short') THEN -quantity
                ELSE 0
            END
        ), 0),
        
        COALESCE(SUM(
            CASE 
                WHEN trade_type IN ('buy', 'long') THEN quantity * entry_price
                ELSE 0
            END
        ), 0),
        
        COALESCE(SUM(
            CASE 
                WHEN trade_type IN ('buy', 'long') THEN quantity
                ELSE 0
            END
        ), 0)
        
    INTO total_qty, total_buy_cost, total_buy_qty
    FROM trade_catalog 
    WHERE user_id = COALESCE(NEW.user_id, OLD.user_id)
    AND asset_symbol = COALESCE(NEW.asset_symbol, OLD.asset_symbol)
    AND asset_type = COALESCE(NEW.asset_type, OLD.asset_type)
    AND trade_status = 'closed';
    
    -- Calculate average entry price
    IF total_buy_qty > 0 THEN
        avg_price := total_buy_cost / total_buy_qty;
    END IF;
    
    -- Calculate total invested (only positive positions)
    total_invested := GREATEST(total_buy_cost, 0);
    
    -- Update or insert portfolio record
    INSERT INTO enhanced_user_portfolio (
        user_id, asset_type, asset_symbol, crypto_id,
        total_quantity, avg_entry_price, total_invested_usd,
        updated_at
    ) VALUES (
        COALESCE(NEW.user_id, OLD.user_id),
        COALESCE(NEW.asset_type, OLD.asset_type),
        COALESCE(NEW.asset_symbol, OLD.asset_symbol),
        COALESCE(NEW.crypto_id, OLD.crypto_id),
        total_qty,
        NULLIF(avg_price, 0),
        total_invested,
        NOW()
    )
    ON CONFLICT (user_id, asset_type, asset_symbol)
    DO UPDATE SET
        total_quantity = EXCLUDED.total_quantity,
        avg_entry_price = EXCLUDED.avg_entry_price,
        total_invested_usd = EXCLUDED.total_invested_usd,
        updated_at = NOW();
    
    -- Remove portfolio record if no position remaining
    IF total_qty = 0 THEN
        UPDATE enhanced_user_portfolio 
        SET is_active = false, updated_at = NOW()
        WHERE user_id = COALESCE(NEW.user_id, OLD.user_id)
        AND asset_symbol = COALESCE(NEW.asset_symbol, OLD.asset_symbol)
        AND asset_type = COALESCE(NEW.asset_type, OLD.asset_type);
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;
"""

CREATE_SYNC_TRIGGER = """
-- Trigger for automatic portfolio synchronization
DROP TRIGGER IF EXISTS trigger_sync_portfolio ON trade_catalog;
CREATE TRIGGER trigger_sync_portfolio
    AFTER INSERT OR UPDATE OR DELETE ON trade_catalog
    FOR EACH ROW
    EXECUTE FUNCTION sync_portfolio_from_trades();
"""

# ============================================================================
# 4. CREATE ANALYTICS VIEWS
# ============================================================================

CREATE_TRADE_ANALYTICS_VIEW = """
-- Comprehensive Trade Performance Analytics
CREATE OR REPLACE VIEW v_trade_performance_analytics AS
SELECT 
    tc.*,
    
    -- Performance Metrics
    CASE 
        WHEN tc.trade_status = 'closed' AND tc.exit_price IS NOT NULL THEN
            CASE 
                WHEN tc.trade_type IN ('long', 'buy') THEN
                    ((tc.exit_price - tc.entry_price) / tc.entry_price * 100)
                WHEN tc.trade_type IN ('short', 'sell') THEN
                    ((tc.entry_price - tc.exit_price) / tc.entry_price * 100)
            END
        ELSE NULL
    END as return_percent,
    
    -- Risk Analysis
    CASE 
        WHEN tc.stop_loss_price IS NOT NULL THEN
            ABS(tc.entry_price - tc.stop_loss_price) / tc.entry_price * 100
    END as actual_risk_percent,
    
    -- Psychology Scoring
    CASE 
        WHEN tc.emotion_before_entry IN ('confident', 'calm', 'focused') AND 
             tc.emotion_after_exit IN ('satisfied', 'confident', 'calm') THEN 'excellent_psychology'
        WHEN tc.emotion_before_entry IN ('confident', 'calm') THEN 'good_psychology'
        WHEN tc.emotion_before_entry IN ('fearful', 'fomo', 'greedy') THEN 'poor_psychology'
        ELSE 'neutral_psychology'
    END as psychology_score,
    
    -- Time Analysis
    CASE 
        WHEN tc.exit_datetime IS NOT NULL THEN
            EXTRACT(EPOCH FROM (tc.exit_datetime - tc.entry_datetime)) / 3600
        ELSE
            EXTRACT(EPOCH FROM (NOW() - tc.entry_datetime)) / 3600
    END as holding_hours,
    
    -- Market Timing Analysis
    CASE 
        WHEN EXTRACT(hour FROM tc.entry_datetime) BETWEEN 8 AND 16 THEN 'market_hours'
        WHEN EXTRACT(hour FROM tc.entry_datetime) BETWEEN 17 AND 23 THEN 'after_hours'
        ELSE 'overnight'
    END as entry_timing,
    
    -- AI Performance Comparison
    CASE 
        WHEN tc.signal_id IS NOT NULL AND tc.trade_status = 'closed' THEN
            tc.realized_pnl_percent - COALESCE(
                (SELECT COALESCE(
                    (ai_analysis->>'expected_return_percent')::NUMERIC, 0
                ) FROM trading_signals WHERE id = tc.signal_id), 0
            )
    END as ai_vs_actual_performance,
    
    -- Risk-Reward Analysis
    CASE 
        WHEN tc.realized_pnl IS NOT NULL AND tc.actual_risk_percent IS NOT NULL AND tc.actual_risk_percent > 0 THEN
            ABS(tc.realized_pnl_percent) / tc.actual_risk_percent
    END as actual_risk_reward_ratio

FROM trade_catalog tc;
"""

CREATE_PORTFOLIO_HEALTH_VIEW = """
-- Portfolio Health Dashboard
CREATE OR REPLACE VIEW v_portfolio_health_dashboard AS
SELECT 
    eup.user_id,
    eup.asset_symbol,
    eup.asset_type,
    eup.total_quantity,
    eup.avg_entry_price,
    eup.total_invested_usd,
    eup.position_status,
    
    -- Performance Calculation (requires real-time price)
    CASE 
        WHEN eup.asset_type = 'crypto' AND c.current_price IS NOT NULL AND eup.avg_entry_price IS NOT NULL THEN
            ((c.current_price - eup.avg_entry_price) / eup.avg_entry_price * 100)
    END as unrealized_pnl_percent,
    
    -- Current Value
    CASE 
        WHEN eup.asset_type = 'crypto' AND c.current_price IS NOT NULL THEN
            eup.total_quantity * c.current_price
    END as current_value_usd,
    
    -- Risk Assessment
    eup.portfolio_stop_loss_percent,
    eup.max_allocation_percent,
    
    -- Activity Metrics
    (SELECT COUNT(*) 
     FROM ai_recommendations ar 
     WHERE ar.user_id = eup.user_id 
     AND ar.status = 'active'
     AND ar.target_entity_type = 'portfolio'
    ) as active_ai_recommendations,
    
    (SELECT COUNT(*) 
     FROM trade_catalog tc 
     WHERE tc.user_id = eup.user_id 
     AND tc.asset_symbol = eup.asset_symbol
     AND tc.asset_type = eup.asset_type
     AND tc.entry_datetime > NOW() - INTERVAL '30 days'
    ) as trades_last_30_days,
    
    -- Risk Status
    CASE 
        WHEN eup.total_invested_usd > (eup.max_allocation_percent / 100) * 10000 THEN 'overallocated'
        WHEN eup.position_status = 'exit_plan' THEN 'exit_planned'
        WHEN eup.is_active = false THEN 'inactive'
        ELSE 'normal'
    END as risk_status,
    
    -- Last Activity
    eup.last_rebalance_date,
    eup.updated_at

FROM enhanced_user_portfolio eup
LEFT JOIN cryptocurrencies c ON eup.crypto_id = c.id
WHERE eup.is_active = true;
"""

CREATE_AI_RECOMMENDATIONS_DASHBOARD = """
-- AI Recommendations Dashboard
CREATE OR REPLACE VIEW v_ai_recommendations_dashboard AS
SELECT 
    ar.*,
    u.email as user_email,
    
    -- Urgency Calculation
    CASE 
        WHEN ar.priority_level = 'urgent' THEN 10
        WHEN ar.priority_level = 'high' THEN 7
        WHEN ar.priority_level = 'medium' THEN 3
        ELSE 1
    END +
    CASE 
        WHEN ar.expires_at IS NOT NULL THEN
            CASE 
                WHEN ar.expires_at < NOW() + INTERVAL '1 hour' THEN 5
                WHEN ar.expires_at < NOW() + INTERVAL '24 hours' THEN 2
                ELSE 0
            END
        ELSE 0
    END as urgency_score,
    
    -- Status Analysis
    CASE 
        WHEN ar.expires_at IS NOT NULL AND ar.expires_at <= NOW() THEN 'expired'
        ELSE ar.status
    END as effective_status,
    
    -- Target Information
    CASE 
        WHEN ar.target_entity_type = 'trade' THEN
            (SELECT tc.asset_symbol FROM trade_catalog tc WHERE tc.id = ar.target_entity_id)
        WHEN ar.target_entity_type = 'portfolio' THEN
            (SELECT eup.asset_symbol FROM enhanced_user_portfolio eup WHERE eup.id = ar.target_entity_id)
    END as target_asset,
    
    -- Performance Tracking
    CASE 
        WHEN ar.was_followed = true AND ar.outcome_result IS NOT NULL THEN
            (ar.outcome_result->>'success_score')::NUMERIC
    END as outcome_success_score

FROM ai_recommendations ar
JOIN users u ON ar.user_id = u.id
ORDER BY urgency_score DESC, ar.created_at DESC;
"""

# ============================================================================
# 5. MIGRATION EXECUTION ORDER
# ============================================================================

MIGRATION_STEPS = [
    ("Create Trade Catalog Table", CREATE_TRADE_CATALOG_TABLE),
    ("Create Enhanced Portfolio Table", CREATE_ENHANCED_PORTFOLIO_TABLE), 
    ("Create AI Recommendations Table", CREATE_AI_RECOMMENDATIONS_TABLE),
    ("Create Indexes", CREATE_INDEXES),
    ("Create Sync Function", CREATE_SYNC_FUNCTION),
    ("Create Sync Trigger", CREATE_SYNC_TRIGGER),
    ("Create Trade Analytics View", CREATE_TRADE_ANALYTICS_VIEW),
    ("Create Portfolio Health View", CREATE_PORTFOLIO_HEALTH_VIEW),
    ("Create AI Recommendations Dashboard", CREATE_AI_RECOMMENDATIONS_DASHBOARD),
]

def run_migration():
    """Execute the complete migration"""
    import psycopg2
    from app.core.config import settings
    
    conn = psycopg2.connect(settings.DATABASE_URL)
    cur = conn.cursor()
    
    try:
        for step_name, step_sql in MIGRATION_STEPS:
            print(f"Executing: {step_name}")
            cur.execute(step_sql)
            conn.commit()
            print(f"✅ Completed: {step_name}")
        
        print("\n🎉 Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    run_migration()
