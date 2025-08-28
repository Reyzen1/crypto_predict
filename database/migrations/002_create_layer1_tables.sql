-- backend/database/migrations/002_create_layer1_tables.sql
-- =============================================
-- CryptoPredict Phase 2: Layer 1 Tables (Macro Market Analysis)
-- Tables for macro market regime, sentiment, and dominance analysis
-- =============================================

BEGIN;

-- =============================================
-- LAYER 1: MACRO MARKET ANALYSIS TABLES
-- =============================================

-- 1. Market Regime Analysis Table
-- Stores overall market regime detection results
CREATE TABLE IF NOT EXISTS market_regime_analysis (
    id SERIAL PRIMARY KEY,
    regime VARCHAR(10) NOT NULL CHECK (regime IN ('bull', 'bear', 'sideways', 'volatile')),
    confidence_score NUMERIC(5,4) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    risk_level VARCHAR(10) NOT NULL CHECK (risk_level IN ('low', 'medium', 'high', 'extreme')),
    trend_strength NUMERIC(5,4) CHECK (trend_strength >= 0 AND trend_strength <= 1),
    recommended_exposure NUMERIC(5,4) CHECK (recommended_exposure >= 0 AND recommended_exposure <= 1),
    indicators JSONB DEFAULT '{}',
    analysis_data JSONB DEFAULT '{}',
    market_context JSONB DEFAULT '{}',
    analysis_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_market_regime_time ON market_regime_analysis(analysis_time DESC);
CREATE INDEX IF NOT EXISTS idx_market_regime_regime ON market_regime_analysis(regime, confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_market_regime_indicators ON market_regime_analysis USING GIN (indicators);

-- Add comments
COMMENT ON TABLE market_regime_analysis IS 'Layer 1: Market regime detection and analysis results';
COMMENT ON COLUMN market_regime_analysis.regime IS 'Detected market regime: bull, bear, sideways, volatile';
COMMENT ON COLUMN market_regime_analysis.confidence_score IS 'Confidence in regime detection (0-1)';
COMMENT ON COLUMN market_regime_analysis.indicators IS 'JSONB storing various market indicators used for detection';

-- 2. Market Sentiment Data Table
-- Stores aggregated sentiment indicators
CREATE TABLE IF NOT EXISTS market_sentiment_data (
    id SERIAL PRIMARY KEY,
    fear_greed_index NUMERIC(5,2) CHECK (fear_greed_index >= 0 AND fear_greed_index <= 100),
    social_sentiment NUMERIC(5,4) CHECK (social_sentiment >= -1 AND social_sentiment <= 1),
    news_sentiment NUMERIC(5,4) CHECK (news_sentiment >= -1 AND news_sentiment <= 1),
    composite_sentiment NUMERIC(5,4) CHECK (composite_sentiment >= -1 AND composite_sentiment <= 1),
    sentiment_sources JSONB DEFAULT '{}',
    funding_rates JSONB DEFAULT '{}',
    options_data JSONB DEFAULT '{}',
    analysis_metrics JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_sentiment_timestamp ON market_sentiment_data(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sentiment_fear_greed ON market_sentiment_data(fear_greed_index DESC, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sentiment_composite ON market_sentiment_data(composite_sentiment DESC, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sentiment_sources ON market_sentiment_data USING GIN (sentiment_sources);

-- Add comments
COMMENT ON TABLE market_sentiment_data IS 'Layer 1: Aggregated market sentiment indicators';
COMMENT ON COLUMN market_sentiment_data.fear_greed_index IS 'Fear & Greed Index (0-100, higher = more greedy)';
COMMENT ON COLUMN market_sentiment_data.composite_sentiment IS 'Composite sentiment score (-1 to 1, higher = more positive)';

-- 3. Dominance Data Table
-- Stores BTC, ETH, and altcoin dominance data
CREATE TABLE IF NOT EXISTS dominance_data (
    id SERIAL PRIMARY KEY,
    btc_dominance NUMERIC(5,2) NOT NULL CHECK (btc_dominance >= 0 AND btc_dominance <= 100),
    eth_dominance NUMERIC(5,2) NOT NULL CHECK (eth_dominance >= 0 AND eth_dominance <= 100),
    alt_dominance NUMERIC(5,2) NOT NULL CHECK (alt_dominance >= 0 AND alt_dominance <= 100),
    stablecoin_dominance NUMERIC(5,2) DEFAULT 0 CHECK (stablecoin_dominance >= 0 AND stablecoin_dominance <= 100),
    total_market_cap NUMERIC(20,2),
    total_volume_24h NUMERIC(20,2),
    trend_analysis JSONB DEFAULT '{}',
    dominance_changes JSONB DEFAULT '{}',
    rotation_signals JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_dominance_timestamp ON dominance_data(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_dominance_btc ON dominance_data(btc_dominance DESC, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_dominance_eth ON dominance_data(eth_dominance DESC, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_dominance_analysis ON dominance_data USING GIN (trend_analysis);

-- Add constraint to ensure dominances add up reasonably (allowing for rounding)
ALTER TABLE dominance_data ADD CONSTRAINT dominance_total_check 
    CHECK ((btc_dominance + eth_dominance + alt_dominance + stablecoin_dominance) BETWEEN 95 AND 105);

-- Add comments
COMMENT ON TABLE dominance_data IS 'Layer 1: BTC, ETH, and altcoin market dominance data';
COMMENT ON COLUMN dominance_data.btc_dominance IS 'Bitcoin market cap dominance percentage';
COMMENT ON COLUMN dominance_data.eth_dominance IS 'Ethereum market cap dominance percentage';
COMMENT ON COLUMN dominance_data.rotation_signals IS 'JSONB storing rotation signals between asset classes';

-- 4. Macro Indicators Table
-- Stores various macro economic indicators
CREATE TABLE IF NOT EXISTS macro_indicators (
    id SERIAL PRIMARY KEY,
    indicator_name VARCHAR(50) NOT NULL,
    indicator_category VARCHAR(30) NOT NULL DEFAULT 'general',
    value NUMERIC(15,8) NOT NULL,
    normalized_value NUMERIC(5,4), -- Normalized to 0-1 or -1 to 1 range
    timeframe VARCHAR(20) NOT NULL DEFAULT '1d',
    data_source VARCHAR(50) NOT NULL,
    meta_data JSONB DEFAULT '{}',
    quality_score NUMERIC(3,2) DEFAULT 1.0 CHECK (quality_score >= 0 AND quality_score <= 1),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint to prevent duplicate indicators for same time
    UNIQUE(indicator_name, timeframe, timestamp)
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_macro_indicators_name_time ON macro_indicators(indicator_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_macro_indicators_category ON macro_indicators(indicator_category, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_macro_indicators_source ON macro_indicators(data_source, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_macro_indicators_meta_data ON macro_indicators USING GIN (meta_data);

-- Add comments
COMMENT ON TABLE macro_indicators IS 'Layer 1: Various macro economic indicators affecting crypto markets';
COMMENT ON COLUMN macro_indicators.indicator_name IS 'Name of the indicator (e.g., DXY, VIX, SPY, etc.)';
COMMENT ON COLUMN macro_indicators.normalized_value IS 'Value normalized to standard range for comparison';
COMMENT ON COLUMN macro_indicators.quality_score IS 'Data quality score (0-1, higher = better quality)';

-- =============================================
-- LAYER 1: TRIGGERS AND FUNCTIONS
-- =============================================

-- Add update triggers for Layer 1 tables
CREATE TRIGGER update_market_regime_updated_at 
    BEFORE UPDATE ON market_regime_analysis 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- LAYER 1: VIEWS FOR COMMON QUERIES
-- =============================================

-- View for latest market regime with sentiment
CREATE OR REPLACE VIEW v_latest_market_state AS
SELECT 
    mra.regime,
    mra.confidence_score as regime_confidence,
    mra.risk_level,
    mra.trend_strength,
    mra.recommended_exposure,
    msd.fear_greed_index,
    msd.composite_sentiment,
    dd.btc_dominance,
    dd.eth_dominance,
    dd.alt_dominance,
    dd.total_market_cap,
    mra.analysis_time,
    msd.timestamp as sentiment_timestamp,
    dd.timestamp as dominance_timestamp
FROM market_regime_analysis mra
CROSS JOIN LATERAL (
    SELECT * FROM market_sentiment_data 
    ORDER BY timestamp DESC LIMIT 1
) msd
CROSS JOIN LATERAL (
    SELECT * FROM dominance_data 
    ORDER BY timestamp DESC LIMIT 1
) dd
WHERE mra.analysis_time = (
    SELECT MAX(analysis_time) FROM market_regime_analysis
);

-- View for macro indicators summary
CREATE OR REPLACE VIEW v_macro_indicators_latest AS
SELECT 
    indicator_name,
    indicator_category,
    value,
    normalized_value,
    data_source,
    quality_score,
    timestamp,
    ROW_NUMBER() OVER (PARTITION BY indicator_name ORDER BY timestamp DESC) as rn
FROM macro_indicators
WHERE timestamp >= NOW() - INTERVAL '7 days';

-- =============================================
-- LAYER 1: SEED DATA
-- =============================================

-- Insert default macro indicators categories
INSERT INTO macro_indicators (indicator_name, indicator_category, value, data_source, meta_data, timestamp) VALUES
('DXY', 'traditional_markets', 103.5, 'federal_reserve', '{"description": "US Dollar Index"}', NOW()),
('VIX', 'traditional_markets', 18.2, 'cboe', '{"description": "Volatility Index"}', NOW()),
('SPY', 'traditional_markets', 4200.0, 'yahoo_finance', '{"description": "S&P 500 ETF"}', NOW()),
('GOLD', 'commodities', 1950.0, 'yahoo_finance', '{"description": "Gold Price USD/oz"}', NOW()),
('BTC_FUNDING', 'crypto_metrics', 0.01, 'binance', '{"description": "BTC Perpetual Funding Rate"}', NOW())
ON CONFLICT (indicator_name, timeframe, timestamp) DO NOTHING;

-- Insert initial market regime (will be updated by AI models)
INSERT INTO market_regime_analysis (
    regime, 
    confidence_score, 
    risk_level, 
    trend_strength, 
    recommended_exposure,
    indicators,
    analysis_data
) VALUES (
    'sideways', 
    0.5, 
    'medium', 
    0.3, 
    0.5,
    '{"initialization": true, "manual_entry": true}',
    '{"status": "initial_state", "note": "Default regime before AI analysis"}'
) ON CONFLICT DO NOTHING;

-- Insert initial sentiment data
INSERT INTO market_sentiment_data (
    fear_greed_index,
    composite_sentiment,
    sentiment_sources
) VALUES (
    50,
    0.0,
    '{"initialization": true, "note": "Neutral starting sentiment"}'
) ON CONFLICT DO NOTHING;

-- Insert initial dominance data  
INSERT INTO dominance_data (
    btc_dominance,
    eth_dominance,
    alt_dominance,
    stablecoin_dominance,
    total_market_cap,
    trend_analysis
) VALUES (
    52.0,
    18.0,
    25.0,
    5.0,
    2500000000000,
    '{"initialization": true, "note": "Estimated initial dominances"}'
) ON CONFLICT DO NOTHING;

-- =============================================
-- VALIDATION AND COMPLETION
-- =============================================

-- Validate Layer 1 tables creation
DO $$ 
DECLARE 
    table_count INTEGER;
BEGIN
    -- Count Layer 1 tables
    SELECT COUNT(*) INTO table_count 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('market_regime_analysis', 'market_sentiment_data', 'dominance_data', 'macro_indicators');
    
    RAISE NOTICE '🌍 Layer 1 Tables Created: %/4', table_count;
    
    -- Validate indexes
    RAISE NOTICE 'Market regime records: %', (SELECT COUNT(*) FROM market_regime_analysis);
    RAISE NOTICE 'Sentiment data records: %', (SELECT COUNT(*) FROM market_sentiment_data);
    RAISE NOTICE 'Dominance data records: %', (SELECT COUNT(*) FROM dominance_data);
    RAISE NOTICE 'Macro indicators records: %', (SELECT COUNT(*) FROM macro_indicators);
END $$;

-- Record migration completion
INSERT INTO system_info (key, value, created_at) 
VALUES ('migration_002_completed', 'Layer 1 tables created successfully', NOW())
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();

COMMIT;
