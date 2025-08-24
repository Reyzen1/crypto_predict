-- backend/database/migrations/005_create_layer4_tables.sql
-- =============================================
-- CryptoPredict Phase 2: Layer 4 Tables (Micro Timing)
-- Tables for trading signals, executions, and risk management
-- =============================================

BEGIN;

-- =============================================
-- LAYER 4: MICRO TIMING TABLES
-- =============================================

-- 1. Trading Signals Table
-- Stores AI-generated trading signals with precise timing
CREATE TABLE IF NOT EXISTS trading_signals (
    id SERIAL PRIMARY KEY,
    crypto_id INTEGER NOT NULL REFERENCES cryptocurrencies(id) ON DELETE CASCADE,
    signal_type VARCHAR(10) NOT NULL CHECK (signal_type IN ('long', 'short', 'neutral')),
    entry_price NUMERIC(20,8) NOT NULL,
    target_price NUMERIC(20,8) NOT NULL,
    stop_loss NUMERIC(20,8) NOT NULL,
    confidence_score NUMERIC(5,4) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    risk_level VARCHAR(10) NOT NULL CHECK (risk_level IN ('low', 'medium', 'high', 'extreme')),
    risk_reward_ratio NUMERIC(6,2) CHECK (risk_reward_ratio > 0),
    time_horizon_hours INTEGER DEFAULT 24 CHECK (time_horizon_hours > 0),
    max_drawdown_percent NUMERIC(5,2) DEFAULT 5.0,
    position_size_percent NUMERIC(5,2) DEFAULT 2.0 CHECK (position_size_percent > 0 AND position_size_percent <= 100),
    
    -- AI Analysis and Context
    ai_analysis JSONB DEFAULT '{}',
    market_context JSONB DEFAULT '{}',
    technical_indicators JSONB DEFAULT '{}',
    layer1_context JSONB DEFAULT '{}', -- Macro context from Layer 1
    layer2_context JSONB DEFAULT '{}', -- Sector context from Layer 2
    layer3_context JSONB DEFAULT '{}', -- Asset context from Layer 3
    
    -- Model and Generation Info
    model_name VARCHAR(50) NOT NULL DEFAULT 'timing_model_v1',
    model_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    generation_method VARCHAR(50) DEFAULT 'ai_analysis',
    data_sources JSONB DEFAULT '{}',
    
    -- Status and Lifecycle
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'executed', 'expired', 'cancelled', 'paused')),
    priority_level VARCHAR(10) DEFAULT 'medium' CHECK (priority_level IN ('low', 'medium', 'high', 'urgent')),
    
    -- Timing
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '7 days'),
    activated_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Validation constraints
    CHECK (target_price != entry_price),
    CHECK (stop_loss != entry_price),
    CHECK ((signal_type = 'long' AND target_price > entry_price AND stop_loss < entry_price) OR
           (signal_type = 'short' AND target_price < entry_price AND stop_loss > entry_price) OR
           signal_type = 'neutral')
);

-- Add indexes for Layer 4 signals
CREATE INDEX IF NOT EXISTS idx_signals_crypto_status ON trading_signals(crypto_id, status, generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_generated ON trading_signals(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_expires ON trading_signals(expires_at) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_signals_confidence ON trading_signals(confidence_score DESC, risk_level, generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_type ON trading_signals(signal_type, status, generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_ai_analysis ON trading_signals USING GIN (ai_analysis);
CREATE INDEX IF NOT EXISTS idx_signals_market_context ON trading_signals USING GIN (market_context);
CREATE INDEX IF NOT EXISTS idx_signals_layer_contexts ON trading_signals USING GIN (layer1_context, layer2_context, layer3_context);

-- Add comments
COMMENT ON TABLE trading_signals IS 'Layer 4: AI-generated trading signals with precise entry/exit timing';
COMMENT ON COLUMN trading_signals.risk_reward_ratio IS 'Expected return divided by risk (e.g., 2.0 means 2:1 reward:risk)';
COMMENT ON COLUMN trading_signals.time_horizon_hours IS 'Expected signal duration in hours';
COMMENT ON COLUMN trading_signals.ai_analysis IS 'JSONB containing AI reasoning and technical analysis';
COMMENT ON COLUMN trading_signals.layer1_context IS 'Macro market context from Layer 1 analysis';

-- 2. Signal Executions Table
-- Tracks actual executions of trading signals by users
CREATE TABLE IF NOT EXISTS signal_executions (
    id SERIAL PRIMARY KEY,
    signal_id INTEGER NOT NULL REFERENCES trading_signals(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Execution Details
    execution_price NUMERIC(20,8),
    position_size NUMERIC(30,8),
    position_size_usd NUMERIC(15,2),
    portfolio_percentage NUMERIC(5,2),
    execution_type VARCHAR(20) DEFAULT 'manual' CHECK (execution_type IN ('manual', 'automatic', 'paper_trade')),
    
    -- Order Management
    order_type VARCHAR(20) DEFAULT 'market' CHECK (order_type IN ('market', 'limit', 'stop_limit', 'trailing_stop')),
    order_id VARCHAR(100), -- External exchange order ID
    fill_type VARCHAR(20) DEFAULT 'full' CHECK (fill_type IN ('full', 'partial', 'unfilled')),
    
    -- Status Tracking
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'filled', 'partially_filled', 'cancelled', 'failed')),
    execution_details JSONB DEFAULT '{}',
    exchange VARCHAR(50),
    fees_paid NUMERIC(15,8) DEFAULT 0,
    slippage_percent NUMERIC(5,4),
    
    -- Performance Tracking
    current_pnl NUMERIC(15,2),
    realized_pnl NUMERIC(15,2),
    max_profit NUMERIC(15,2),
    max_drawdown NUMERIC(15,2),
    
    -- Risk Management
    risk_metrics JSONB DEFAULT '{}',
    stop_loss_triggered BOOLEAN DEFAULT false,
    take_profit_triggered BOOLEAN DEFAULT false,
    
    -- Timing
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    closed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for signal executions
CREATE INDEX IF NOT EXISTS idx_signal_executions_user ON signal_executions(user_id, executed_at DESC);
CREATE INDEX IF NOT EXISTS idx_signal_executions_signal ON signal_executions(signal_id, status);
CREATE INDEX IF NOT EXISTS idx_signal_executions_status ON signal_executions(status, executed_at DESC);
CREATE INDEX IF NOT EXISTS idx_signal_executions_performance ON signal_executions(realized_pnl DESC, executed_at DESC) WHERE realized_pnl IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_signal_executions_details ON signal_executions USING GIN (execution_details);

-- Add comments
COMMENT ON TABLE signal_executions IS 'Layer 4: User executions of trading signals with performance tracking';
COMMENT ON COLUMN signal_executions.slippage_percent IS 'Percentage difference between expected and actual execution price';
COMMENT ON COLUMN signal_executions.current_pnl IS 'Current unrealized P&L for open positions';

-- 3. Risk Management Table
-- User-specific risk management settings and current exposure
CREATE TABLE IF NOT EXISTS risk_management (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    
    -- Risk Limits
    max_position_size_usd NUMERIC(15,2) DEFAULT 1000,
    max_portfolio_risk_percent NUMERIC(5,2) DEFAULT 2.0 CHECK (max_portfolio_risk_percent >= 0 AND max_portfolio_risk_percent <= 100),
    max_daily_loss_percent NUMERIC(5,2) DEFAULT 5.0 CHECK (max_daily_loss_percent >= 0 AND max_daily_loss_percent <= 100),
    max_concurrent_signals INTEGER DEFAULT 5 CHECK (max_concurrent_signals > 0),
    
    -- Risk Rules Configuration
    risk_rules JSONB DEFAULT '{}',
    position_sizing_method VARCHAR(20) DEFAULT 'fixed_percent' CHECK (position_sizing_method IN ('fixed_amount', 'fixed_percent', 'kelly_criterion', 'volatility_based')),
    
    -- Current Exposure Tracking
    current_exposure_usd NUMERIC(15,2) DEFAULT 0,
    current_portfolio_risk NUMERIC(5,2) DEFAULT 0,
    active_positions_count INTEGER DEFAULT 0,
    daily_loss_current NUMERIC(15,2) DEFAULT 0,
    
    -- Risk Metrics and Analysis
    risk_metrics JSONB DEFAULT '{}',
    portfolio_correlation JSONB DEFAULT '{}',
    exposure_by_sector JSONB DEFAULT '{}',
    
    -- Performance and Statistics
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    total_pnl NUMERIC(15,2) DEFAULT 0,
    max_drawdown_history NUMERIC(15,2) DEFAULT 0,
    
    -- Risk Management Status
    risk_limit_breached BOOLEAN DEFAULT false,
    auto_stop_trading BOOLEAN DEFAULT false,
    last_risk_check TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    risk_warnings JSONB DEFAULT '[]',
    
    -- Timing
    last_calculated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for risk management
CREATE INDEX IF NOT EXISTS idx_risk_management_user ON risk_management(user_id);
CREATE INDEX IF NOT EXISTS idx_risk_management_exposure ON risk_management(current_exposure_usd DESC, current_portfolio_risk DESC);
CREATE INDEX IF NOT EXISTS idx_risk_management_limits ON risk_management(risk_limit_breached, auto_stop_trading);
CREATE INDEX IF NOT EXISTS idx_risk_management_metrics ON risk_management USING GIN (risk_metrics);

-- Add comments
COMMENT ON TABLE risk_management IS 'Layer 4: User risk management settings, limits, and current exposure tracking';
COMMENT ON COLUMN risk_management.max_portfolio_risk_percent IS 'Maximum percentage of portfolio at risk at any time';
COMMENT ON COLUMN risk_management.position_sizing_method IS 'Method used to calculate position sizes';

-- =============================================
-- LAYER 4: TRIGGERS
-- =============================================

-- Add update triggers for Layer 4 tables
CREATE TRIGGER update_trading_signals_updated_at 
    BEFORE UPDATE ON trading_signals 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_signal_executions_updated_at 
    BEFORE UPDATE ON signal_executions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_risk_management_updated_at 
    BEFORE UPDATE ON risk_management 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update risk management when signal executions change
CREATE OR REPLACE FUNCTION update_risk_exposure()
RETURNS TRIGGER AS $$
BEGIN
    -- Update risk management metrics when executions change
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        UPDATE risk_management 
        SET 
            current_exposure_usd = (
                SELECT COALESCE(SUM(position_size_usd), 0)
                FROM signal_executions 
                WHERE user_id = NEW.user_id 
                AND status IN ('filled', 'partially_filled')
                AND closed_at IS NULL
            ),
            active_positions_count = (
                SELECT COUNT(*)
                FROM signal_executions
                WHERE user_id = NEW.user_id
                AND status IN ('filled', 'partially_filled') 
                AND closed_at IS NULL
            ),
            last_calculated = NOW()
        WHERE user_id = NEW.user_id;
        
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE risk_management 
        SET 
            current_exposure_usd = (
                SELECT COALESCE(SUM(position_size_usd), 0)
                FROM signal_executions 
                WHERE user_id = OLD.user_id 
                AND status IN ('filled', 'partially_filled')
                AND closed_at IS NULL
            ),
            active_positions_count = (
                SELECT COUNT(*)
                FROM signal_executions
                WHERE user_id = OLD.user_id
                AND status IN ('filled', 'partially_filled')
                AND closed_at IS NULL
            ),
            last_calculated = NOW()
        WHERE user_id = OLD.user_id;
        
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER signal_executions_update_risk
    AFTER INSERT OR UPDATE OR DELETE ON signal_executions
    FOR EACH ROW EXECUTE FUNCTION update_risk_exposure();

-- =============================================
-- LAYER 4: VIEWS FOR COMMON QUERIES
-- =============================================

-- View for active trading signals with crypto details
CREATE OR REPLACE VIEW v_active_signals AS
SELECT 
    ts.id,
    ts.crypto_id,
    c.symbol,
    c.name as crypto_name,
    c.current_price,
    ts.signal_type,
    ts.entry_price,
    ts.target_price,
    ts.stop_loss,
    ts.confidence_score,
    ts.risk_level,
    ts.risk_reward_ratio,
    ts.time_horizon_hours,
    ts.position_size_percent,
    -- Calculate potential return percentage
    CASE 
        WHEN ts.signal_type = 'long' THEN 
            ((ts.target_price - ts.entry_price) / ts.entry_price * 100)
        WHEN ts.signal_type = 'short' THEN 
            ((ts.entry_price - ts.target_price) / ts.entry_price * 100)
        ELSE 0
    END as potential_return_percent,
    -- Calculate potential loss percentage
    CASE 
        WHEN ts.signal_type = 'long' THEN 
            ((ts.entry_price - ts.stop_loss) / ts.entry_price * 100)
        WHEN ts.signal_type = 'short' THEN 
            ((ts.stop_loss - ts.entry_price) / ts.entry_price * 100)
        ELSE 0
    END as max_loss_percent,
    ts.generated_at,
    ts.expires_at,
    -- Time until expiry
    EXTRACT(epoch FROM (ts.expires_at - NOW())) / 3600 as hours_until_expiry
FROM trading_signals ts
JOIN cryptocurrencies c ON ts.crypto_id = c.id
WHERE ts.status = 'active' 
    AND ts.expires_at > NOW()
ORDER BY ts.confidence_score DESC, ts.risk_reward_ratio DESC, ts.generated_at DESC;

-- View for signal execution performance
CREATE OR REPLACE VIEW v_signal_performance AS
SELECT 
    se.id,
    se.signal_id,
    se.user_id,
    u.email as user_email,
    c.symbol,
    ts.signal_type,
    ts.entry_price,
    se.execution_price,
    se.position_size_usd,
    se.realized_pnl,
    se.max_profit,
    se.max_drawdown,
    CASE 
        WHEN se.realized_pnl > 0 THEN 'profit'
        WHEN se.realized_pnl < 0 THEN 'loss'
        ELSE 'break_even'
    END as trade_outcome,
    -- Calculate return percentage
    CASE 
        WHEN se.position_size_usd > 0 THEN (se.realized_pnl / se.position_size_usd * 100)
        ELSE 0
    END as return_percent,
    se.executed_at,
    se.closed_at,
    -- Calculate holding duration
    CASE 
        WHEN se.closed_at IS NOT NULL THEN 
            EXTRACT(epoch FROM (se.closed_at - se.executed_at)) / 3600
        ELSE 
            EXTRACT(epoch FROM (NOW() - se.executed_at)) / 3600
    END as holding_hours
FROM signal_executions se
JOIN trading_signals ts ON se.signal_id = ts.id
JOIN cryptocurrencies c ON ts.crypto_id = c.id
JOIN users u ON se.user_id = u.id
WHERE se.status IN ('filled', 'partially_filled')
ORDER BY se.executed_at DESC;

-- View for user risk overview
CREATE OR REPLACE VIEW v_user_risk_overview AS
SELECT 
    rm.user_id,
    u.email as user_email,
    u.role as user_role,
    rm.current_exposure_usd,
    rm.current_portfolio_risk,
    rm.max_portfolio_risk_percent,
    rm.active_positions_count,
    rm.max_concurrent_signals,
    -- Risk utilization percentages
    CASE 
        WHEN rm.max_portfolio_risk_percent > 0 THEN 
            (rm.current_portfolio_risk / rm.max_portfolio_risk_percent * 100)
        ELSE 0
    END as risk_utilization_percent,
    CASE 
        WHEN rm.max_concurrent_signals > 0 THEN 
            (rm.active_positions_count::FLOAT / rm.max_concurrent_signals * 100)
        ELSE 0
    END as position_utilization_percent,
    rm.total_trades,
    rm.winning_trades,
    CASE 
        WHEN rm.total_trades > 0 THEN (rm.winning_trades::FLOAT / rm.total_trades * 100)
        ELSE 0
    END as win_rate_percent,
    rm.total_pnl,
    rm.max_drawdown_history,
    rm.risk_limit_breached,
    rm.auto_stop_trading,
    rm.last_calculated
FROM risk_management rm
JOIN users u ON rm.user_id = u.id
ORDER BY rm.current_exposure_usd DESC, rm.current_portfolio_risk DESC;

-- =============================================
-- LAYER 4: SEED DATA
-- =============================================

-- Create default risk management settings for existing users
INSERT INTO risk_management (user_id, max_position_size_usd, max_portfolio_risk_percent, risk_rules)
SELECT 
    id,
    CASE 
        WHEN role = 'admin' THEN 10000
        WHEN role = 'professional' THEN 5000
        ELSE 1000
    END,
    CASE 
        WHEN role = 'admin' THEN 5.0
        WHEN role = 'professional' THEN 3.0
        ELSE 2.0
    END,
    jsonb_build_object(
        'auto_stop_loss', true,
        'max_correlation', 0.7,
        'diversification_required', true,
        'risk_adjusted_sizing', true
    )
FROM users 
WHERE is_active = true
ON CONFLICT (user_id) DO NOTHING;

-- =============================================
-- VALIDATION AND COMPLETION
-- =============================================

-- Validate Layer 4 tables creation
DO $$ 
DECLARE 
    table_count INTEGER;
    risk_profiles INTEGER;
BEGIN
    -- Count Layer 4 tables
    SELECT COUNT(*) INTO table_count 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('trading_signals', 'signal_executions', 'risk_management');
    
    -- Count risk profiles created
    SELECT COUNT(*) INTO risk_profiles FROM risk_management;
    
    RAISE NOTICE '⚡ Layer 4 Tables Created: %/3', table_count;
    RAISE NOTICE 'Risk profiles created: %', risk_profiles;
END $$;

-- Record migration completion
INSERT INTO system_info (key, value, created_at) 
VALUES ('migration_005_completed', 'Layer 4 (Micro Timing) tables created successfully', NOW())
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();

COMMIT;

