-- backend/database/migrations/004_create_layer3_tables.sql
-- =============================================
-- CryptoPredict Phase 2: Layer 3 Tables (Asset Selection)
-- Tables for watchlist management and AI suggestions
-- =============================================

BEGIN;

-- =============================================
-- LAYER 3: ASSET SELECTION TABLES
-- =============================================

-- 1. Watchlists Table
-- Manages different types of watchlists
CREATE TABLE IF NOT EXISTS watchlists (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('admin_tier1', 'admin_tier2', 'user_custom')),
    description TEXT,
    max_items INTEGER DEFAULT 50,
    is_active BOOLEAN DEFAULT true,
    is_public BOOLEAN DEFAULT false,
    settings JSONB DEFAULT '{}',
    performance_metrics JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Admin watchlists don't need user_id, user watchlists require it
    CHECK (
        (type IN ('admin_tier1', 'admin_tier2') AND user_id IS NULL) OR
        (type = 'user_custom' AND user_id IS NOT NULL)
    )
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_watchlist_type ON watchlists(type, is_active);
CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlists(user_id, type, is_active);
CREATE INDEX IF NOT EXISTS idx_watchlist_settings ON watchlists USING GIN (settings);

-- Add comments
COMMENT ON TABLE watchlists IS 'Layer 3: Watchlist containers for different user types and purposes';
COMMENT ON COLUMN watchlists.type IS 'Type: admin_tier1 (high priority), admin_tier2 (medium priority), user_custom (personal)';
COMMENT ON COLUMN watchlists.settings IS 'JSONB storing watchlist-specific settings and preferences';

-- 2. Watchlist Items Table
-- Individual items in watchlists
CREATE TABLE IF NOT EXISTS watchlist_items (
    id SERIAL PRIMARY KEY,
    watchlist_id INTEGER NOT NULL REFERENCES watchlists(id) ON DELETE CASCADE,
    crypto_id INTEGER NOT NULL REFERENCES cryptocurrencies(id) ON DELETE CASCADE,
    score NUMERIC(5,2) DEFAULT 0,
    rank_position INTEGER,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'pending_review', 'removed', 'paused')),
    selection_criteria JSONB DEFAULT '{}',
    performance_metrics JSONB DEFAULT '{}',
    risk_metrics JSONB DEFAULT '{}',
    ai_analysis JSONB DEFAULT '{}',
    added_by_user_id INTEGER REFERENCES users(id),
    added_reason TEXT,
    last_updated_score TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint to prevent duplicate cryptos in same watchlist
    UNIQUE(watchlist_id, crypto_id)
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_watchlist_items_watchlist ON watchlist_items(watchlist_id, status, score DESC);
CREATE INDEX IF NOT EXISTS idx_watchlist_items_crypto ON watchlist_items(crypto_id, status);
CREATE INDEX IF NOT EXISTS idx_watchlist_items_score ON watchlist_items(score DESC, watchlist_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_items_rank ON watchlist_items(watchlist_id, rank_position);
CREATE INDEX IF NOT EXISTS idx_watchlist_items_criteria ON watchlist_items USING GIN (selection_criteria);
CREATE INDEX IF NOT EXISTS idx_watchlist_items_ai_analysis ON watchlist_items USING GIN (ai_analysis);

-- Add comments
COMMENT ON TABLE watchlist_items IS 'Layer 3: Individual cryptocurrency items within watchlists';
COMMENT ON COLUMN watchlist_items.score IS 'AI-calculated score for this asset (0-100)';
COMMENT ON COLUMN watchlist_items.rank_position IS 'Position ranking within the watchlist';
COMMENT ON COLUMN watchlist_items.selection_criteria IS 'JSONB storing criteria used for selection';

-- 3. AI Suggestions Table
-- AI-generated suggestions for watchlist modifications
CREATE TABLE IF NOT EXISTS ai_suggestions (
    id SERIAL PRIMARY KEY,
    crypto_id INTEGER NOT NULL REFERENCES cryptocurrencies(id) ON DELETE CASCADE,
    suggestion_type VARCHAR(20) NOT NULL CHECK (suggestion_type IN ('add_tier1', 'add_tier2', 'remove', 'tier_change', 'rank_change')),
    current_tier VARCHAR(10),
    suggested_tier VARCHAR(10),
    confidence_score NUMERIC(5,4) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    priority_score NUMERIC(5,2) DEFAULT 50 CHECK (priority_score >= 0 AND priority_score <= 100),
    reasoning JSONB DEFAULT '{}',
    analysis_data JSONB DEFAULT '{}',
    supporting_metrics JSONB DEFAULT '{}',
    risk_assessment JSONB DEFAULT '{}',
    model_version VARCHAR(50),
    data_sources JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'expired')),
    reviewed_by INTEGER REFERENCES users(id),
    review_notes TEXT,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '7 days'),
    suggested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_status ON ai_suggestions(status, priority_score DESC, suggested_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_crypto ON ai_suggestions(crypto_id, status);
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_type ON ai_suggestions(suggestion_type, confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_priority ON ai_suggestions(priority_score DESC, confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_expires ON ai_suggestions(expires_at) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_reasoning ON ai_suggestions USING GIN (reasoning);

-- Add comments
COMMENT ON TABLE ai_suggestions IS 'Layer 3: AI-generated suggestions for watchlist management';
COMMENT ON COLUMN ai_suggestions.suggestion_type IS 'Type of suggestion: add_tier1, add_tier2, remove, tier_change, rank_change';
COMMENT ON COLUMN ai_suggestions.priority_score IS 'Priority score for processing suggestions (0-100, higher = more urgent)';
COMMENT ON COLUMN ai_suggestions.reasoning IS 'JSONB containing AI reasoning and explanation';

-- 4. Suggestion Reviews Table
-- Admin reviews of AI suggestions
CREATE TABLE IF NOT EXISTS suggestion_reviews (
    id SERIAL PRIMARY KEY,
    suggestion_id INTEGER NOT NULL REFERENCES ai_suggestions(id) ON DELETE CASCADE,
    admin_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(10) NOT NULL CHECK (action IN ('approve', 'reject', 'modify', 'defer')),
    review_notes TEXT,
    modifications JSONB DEFAULT '{}',
    confidence_adjustment NUMERIC(5,4),
    reviewer_score NUMERIC(5,2) CHECK (reviewer_score >= 0 AND reviewer_score <= 100),
    review_time_spent INTEGER, -- seconds spent reviewing
    follow_up_required BOOLEAN DEFAULT false,
    reviewed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_suggestion_reviews_suggestion ON suggestion_reviews(suggestion_id);
CREATE INDEX IF NOT EXISTS idx_suggestion_reviews_admin ON suggestion_reviews(admin_user_id, reviewed_at DESC);
CREATE INDEX IF NOT EXISTS idx_suggestion_reviews_action ON suggestion_reviews(action, reviewed_at DESC);
CREATE INDEX IF NOT EXISTS idx_suggestion_reviews_modifications ON suggestion_reviews USING GIN (modifications);

-- Add comments
COMMENT ON TABLE suggestion_reviews IS 'Layer 3: Admin reviews and actions on AI suggestions';
COMMENT ON COLUMN suggestion_reviews.reviewer_score IS 'Admin confidence score in their review decision';
COMMENT ON COLUMN suggestion_reviews.review_time_spent IS 'Time spent reviewing in seconds (for efficiency metrics)';

-- =============================================
-- LAYER 3: TRIGGERS
-- =============================================

-- Add update triggers for Layer 3 tables
CREATE TRIGGER update_watchlists_updated_at 
    BEFORE UPDATE ON watchlists 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_watchlist_items_updated_at 
    BEFORE UPDATE ON watchlist_items 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update cryptocurrencies.watchlist_tier when watchlist items change
CREATE OR REPLACE FUNCTION update_crypto_watchlist_tier()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the cryptocurrency's watchlist_tier based on highest tier watchlist it's in
    UPDATE cryptocurrencies 
    SET watchlist_tier = COALESCE(
        (SELECT 
            CASE 
                WHEN EXISTS(SELECT 1 FROM watchlist_items wi 
                          JOIN watchlists w ON wi.watchlist_id = w.id 
                          WHERE wi.crypto_id = COALESCE(NEW.crypto_id, OLD.crypto_id)
                          AND w.type = 'admin_tier1' AND wi.status = 'active') THEN 'tier1'
                WHEN EXISTS(SELECT 1 FROM watchlist_items wi 
                          JOIN watchlists w ON wi.watchlist_id = w.id 
                          WHERE wi.crypto_id = COALESCE(NEW.crypto_id, OLD.crypto_id)
                          AND w.type = 'admin_tier2' AND wi.status = 'active') THEN 'tier2'
                ELSE 'none'
            END
        ), 'none')
    WHERE id = COALESCE(NEW.crypto_id, OLD.crypto_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER watchlist_items_update_tier
    AFTER INSERT OR UPDATE OR DELETE ON watchlist_items
    FOR EACH ROW EXECUTE FUNCTION update_crypto_watchlist_tier();

-- =============================================
-- LAYER 3: VIEWS FOR COMMON QUERIES
-- =============================================

-- View for watchlist summary with counts and performance
CREATE OR REPLACE VIEW v_watchlist_summary AS
SELECT 
    w.id,
    w.name,
    w.type,
    w.description,
    w.max_items,
    COUNT(wi.id) as current_items,
    COUNT(wi.id) FILTER (WHERE wi.status = 'active') as active_items,
    COUNT(wi.id) FILTER (WHERE wi.status = 'pending_review') as pending_items,
    AVG(wi.score) FILTER (WHERE wi.status = 'active') as avg_score,
    MAX(wi.score) FILTER (WHERE wi.status = 'active') as max_score,
    MIN(wi.score) FILTER (WHERE wi.status = 'active') as min_score,
    w.created_at,
    w.updated_at
FROM watchlists w
LEFT JOIN watchlist_items wi ON w.id = wi.watchlist_id
WHERE w.is_active = true
GROUP BY w.id, w.name, w.type, w.description, w.max_items, w.created_at, w.updated_at
ORDER BY 
    CASE w.type 
        WHEN 'admin_tier1' THEN 1 
        WHEN 'admin_tier2' THEN 2 
        ELSE 3 
    END,
    w.name;

-- View for pending AI suggestions with crypto details
CREATE OR REPLACE VIEW v_pending_suggestions AS
SELECT 
    ais.id,
    ais.suggestion_type,
    ais.confidence_score,
    ais.priority_score,
    c.symbol,
    c.name as crypto_name,
    c.current_price,
    c.market_cap_rank,
    c.watchlist_tier as current_tier,
    ais.suggested_tier,
    ais.reasoning,
    ais.suggested_at,
    ais.expires_at,
    EXTRACT(epoch FROM (ais.expires_at - NOW())) / 3600 as hours_until_expiry
FROM ai_suggestions ais
JOIN cryptocurrencies c ON ais.crypto_id = c.id
WHERE ais.status = 'pending' 
    AND ais.expires_at > NOW()
ORDER BY ais.priority_score DESC, ais.confidence_score DESC, ais.suggested_at ASC;

-- View for watchlist items with crypto details
CREATE OR REPLACE VIEW v_watchlist_items_detailed AS
SELECT 
    wi.id,
    wi.watchlist_id,
    w.name as watchlist_name,
    w.type as watchlist_type,
    wi.crypto_id,
    c.symbol,
    c.name as crypto_name,
    c.current_price,
    c.market_cap_rank,
    wi.score,
    wi.rank_position,
    wi.status,
    wi.selection_criteria,
    wi.performance_metrics,
    wi.added_at,
    wi.updated_at
FROM watchlist_items wi
JOIN watchlists w ON wi.watchlist_id = w.id
JOIN cryptocurrencies c ON wi.crypto_id = c.id
WHERE w.is_active = true
ORDER BY w.type, wi.rank_position NULLS LAST, wi.score DESC;

-- =============================================
-- LAYER 3: SEED DATA
-- =============================================

-- Create default admin watchlists
INSERT INTO watchlists (name, type, description, max_items, settings) VALUES
('Admin Tier 1 Assets', 'admin_tier1', 'High-confidence cryptocurrency selections with strong fundamentals and growth potential', 25, 
 '{"auto_rebalance": true, "min_score": 70, "max_volatility": 0.08, "min_market_cap": 1000000000}'::jsonb),
('Admin Tier 2 Assets', 'admin_tier2', 'Medium-confidence cryptocurrency selections with good potential but higher risk', 50,
 '{"auto_rebalance": true, "min_score": 50, "max_volatility": 0.15, "min_market_cap": 100000000}'::jsonb)
ON CONFLICT DO NOTHING;

-- Insert sample AI suggestion (will be replaced by real AI)
INSERT INTO ai_suggestions (
    crypto_id, 
    suggestion_type, 
    confidence_score, 
    priority_score,
    reasoning,
    analysis_data,
    model_version
) 
SELECT 
    c.id,
    'add_tier2',
    0.75,
    80,
    '{"factors": ["strong_volume_growth", "technical_breakout", "sector_rotation"], "summary": "Strong technical and fundamental indicators suggest addition to watchlist"}'::jsonb,
    '{"price_momentum": 0.85, "volume_trend": "increasing", "relative_strength": 1.25}'::jsonb,
    'initial_ai_v1.0'
FROM cryptocurrencies c 
WHERE c.symbol = 'ETH' 
  AND NOT EXISTS (SELECT 1 FROM ai_suggestions WHERE crypto_id = c.id)
LIMIT 1;

-- =============================================
-- VALIDATION AND COMPLETION
-- =============================================

-- Validate Layer 3 tables creation
DO $$ 
DECLARE 
    table_count INTEGER;
    watchlist_count INTEGER;
    suggestion_count INTEGER;
BEGIN
    -- Count Layer 3 tables
    SELECT COUNT(*) INTO table_count 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('watchlists', 'watchlist_items', 'ai_suggestions', 'suggestion_reviews');
    
    -- Count watchlists and suggestions
    SELECT COUNT(*) INTO watchlist_count FROM watchlists WHERE is_active = true;
    SELECT COUNT(*) INTO suggestion_count FROM ai_suggestions WHERE status = 'pending';
    
    RAISE NOTICE '💰 Layer 3 Tables Created: %/4', table_count;
    RAISE NOTICE 'Active watchlists: %', watchlist_count;
    RAISE NOTICE 'Pending suggestions: %', suggestion_count;
END $$;

-- Record migration completion
INSERT INTO system_info (key, value, created_at) 
VALUES ('migration_004_completed', 'Layer 3 (Asset Selection) tables created successfully', NOW())
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();

COMMIT;