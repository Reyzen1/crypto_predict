-- backend/database/migrations/003_create_layer2_tables.sql
-- =============================================
-- CryptoPredict Phase 2: Layer 2 Tables (Sector Analysis)
-- Tables for crypto sector classification and rotation analysis
-- =============================================

BEGIN;

-- =============================================
-- LAYER 2: SECTOR ANALYSIS TABLES
-- =============================================

-- 1. Crypto Sectors Table
-- Defines different cryptocurrency sectors (DeFi, Layer1, etc.)
CREATE TABLE IF NOT EXISTS crypto_sectors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    characteristics JSONB DEFAULT '{}',
    sector_type VARCHAR(20) DEFAULT 'general' CHECK (sector_type IN ('base_layer', 'platform', 'application', 'infrastructure', 'utility', 'speculative', 'general')),
    maturity_level VARCHAR(10) DEFAULT 'medium' CHECK (maturity_level IN ('low', 'medium', 'high')),
    risk_category VARCHAR(10) DEFAULT 'medium' CHECK (risk_category IN ('low', 'medium', 'high', 'extreme')),
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_crypto_sectors_active ON crypto_sectors(is_active, sort_order);
CREATE INDEX IF NOT EXISTS idx_crypto_sectors_type ON crypto_sectors(sector_type, is_active);
CREATE INDEX IF NOT EXISTS idx_crypto_sectors_characteristics ON crypto_sectors USING GIN (characteristics);

-- Add comments
COMMENT ON TABLE crypto_sectors IS 'Layer 2: Cryptocurrency sector definitions and characteristics';
COMMENT ON COLUMN crypto_sectors.name IS 'Unique sector identifier (e.g., defi, layer1, gaming)';
COMMENT ON COLUMN crypto_sectors.display_name IS 'Human-readable sector name';
COMMENT ON COLUMN crypto_sectors.characteristics IS 'JSONB storing sector-specific characteristics and metadata';

-- 2. Sector Performance Table
-- Tracks performance metrics for each sector
CREATE TABLE IF NOT EXISTS sector_performance (
    id SERIAL PRIMARY KEY,
    sector_id INTEGER NOT NULL REFERENCES crypto_sectors(id) ON DELETE CASCADE,
    performance_1h NUMERIC(8,4),
    performance_24h NUMERIC(8,4),
    performance_7d NUMERIC(8,4),
    performance_30d NUMERIC(8,4),
    performance_90d NUMERIC(8,4),
    volume_change_24h NUMERIC(8,4),
    market_cap_change_24h NUMERIC(8,4),
    market_cap_total NUMERIC(20,2),
    volume_total_24h NUMERIC(20,2),
    asset_count INTEGER DEFAULT 0,
    top_performer_id INTEGER REFERENCES cryptocurrencies(id),
    worst_performer_id INTEGER REFERENCES cryptocurrencies(id),
    performance_metrics JSONB DEFAULT '{}',
    momentum_score NUMERIC(5,4) CHECK (momentum_score >= -1 AND momentum_score <= 1),
    relative_strength NUMERIC(5,4) CHECK (relative_strength >= 0 AND relative_strength <= 2),
    analysis_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_sector_perf_sector_time ON sector_performance(sector_id, analysis_time DESC);
CREATE INDEX IF NOT EXISTS idx_sector_perf_performance ON sector_performance(performance_24h DESC, analysis_time DESC);
CREATE INDEX IF NOT EXISTS idx_sector_perf_momentum ON sector_performance(momentum_score DESC, analysis_time DESC);
CREATE INDEX IF NOT EXISTS idx_sector_perf_metrics ON sector_performance USING GIN (performance_metrics);

-- Add comments
COMMENT ON TABLE sector_performance IS 'Layer 2: Real-time and historical performance data for crypto sectors';
COMMENT ON COLUMN sector_performance.momentum_score IS 'Sector momentum score (-1 to 1, higher = stronger momentum)';
COMMENT ON COLUMN sector_performance.relative_strength IS 'Relative strength vs overall market (1 = market performance, >1 = outperforming)';

-- 3. Sector Rotation Analysis Table
-- Tracks capital rotation between sectors
CREATE TABLE IF NOT EXISTS sector_rotation_analysis (
    id SERIAL PRIMARY KEY,
    from_sector_id INTEGER REFERENCES crypto_sectors(id) ON DELETE CASCADE,
    to_sector_id INTEGER REFERENCES crypto_sectors(id) ON DELETE CASCADE,
    rotation_strength NUMERIC(5,4) NOT NULL CHECK (rotation_strength >= 0 AND rotation_strength <= 1),
    confidence_score NUMERIC(5,4) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    capital_flow_estimate NUMERIC(15,2),
    flow_direction VARCHAR(10) CHECK (flow_direction IN ('inflow', 'outflow', 'neutral')),
    rotation_indicators JSONB DEFAULT '{}',
    market_context JSONB DEFAULT '{}',
    detection_method VARCHAR(50) DEFAULT 'volume_price_analysis',
    analysis_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure we don't have rotation from sector to itself
    CHECK (from_sector_id != to_sector_id OR (from_sector_id IS NULL AND to_sector_id IS NOT NULL) OR (from_sector_id IS NOT NULL AND to_sector_id IS NULL))
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_sector_rotation_time ON sector_rotation_analysis(analysis_time DESC);
CREATE INDEX IF NOT EXISTS idx_sector_rotation_strength ON sector_rotation_analysis(rotation_strength DESC, confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_sector_rotation_from ON sector_rotation_analysis(from_sector_id, analysis_time DESC);
CREATE INDEX IF NOT EXISTS idx_sector_rotation_to ON sector_rotation_analysis(to_sector_id, analysis_time DESC);
CREATE INDEX IF NOT EXISTS idx_sector_rotation_indicators ON sector_rotation_analysis USING GIN (rotation_indicators);

-- Add comments
COMMENT ON TABLE sector_rotation_analysis IS 'Layer 2: Analysis of capital rotation patterns between crypto sectors';
COMMENT ON COLUMN sector_rotation_analysis.rotation_strength IS 'Strength of detected rotation (0-1, higher = stronger)';
COMMENT ON COLUMN sector_rotation_analysis.capital_flow_estimate IS 'Estimated capital flow amount in USD';

-- 4. Crypto Sector Mapping Table
-- Maps cryptocurrencies to sectors (many-to-many relationship)
CREATE TABLE IF NOT EXISTS crypto_sector_mapping (
    id SERIAL PRIMARY KEY,
    crypto_id INTEGER NOT NULL REFERENCES cryptocurrencies(id) ON DELETE CASCADE,
    sector_id INTEGER NOT NULL REFERENCES crypto_sectors(id) ON DELETE CASCADE,
    allocation_percentage NUMERIC(5,2) NOT NULL DEFAULT 100 
        CHECK (allocation_percentage > 0 AND allocation_percentage <= 100),
    is_primary_sector BOOLEAN DEFAULT true,
    mapping_confidence NUMERIC(5,4) DEFAULT 1.0 CHECK (mapping_confidence >= 0 AND mapping_confidence <= 1),
    mapping_source VARCHAR(50) DEFAULT 'manual',
    sector_weight NUMERIC(5,4) DEFAULT 1.0 CHECK (sector_weight >= 0 AND sector_weight <= 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint for primary mappings
    UNIQUE(crypto_id, sector_id)
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_crypto_sector_crypto ON crypto_sector_mapping(crypto_id, is_primary_sector DESC);
CREATE INDEX IF NOT EXISTS idx_crypto_sector_sector ON crypto_sector_mapping(sector_id, allocation_percentage DESC);
CREATE INDEX IF NOT EXISTS idx_crypto_sector_primary ON crypto_sector_mapping(is_primary_sector, mapping_confidence DESC);

-- Add constraint to ensure each crypto has exactly one primary sector
CREATE UNIQUE INDEX IF NOT EXISTS idx_crypto_sector_primary_unique 
    ON crypto_sector_mapping(crypto_id) 
    WHERE is_primary_sector = true;

-- Add comments
COMMENT ON TABLE crypto_sector_mapping IS 'Layer 2: Mapping of cryptocurrencies to sectors with allocation percentages';
COMMENT ON COLUMN crypto_sector_mapping.allocation_percentage IS 'Percentage of crypto allocated to this sector (for multi-sector assets)';
COMMENT ON COLUMN crypto_sector_mapping.mapping_confidence IS 'Confidence in sector classification (0-1)';
COMMENT ON COLUMN crypto_sector_mapping.sector_weight IS 'Weight of this crypto within the sector for calculations';

-- =============================================
-- LAYER 2: TRIGGERS
-- =============================================

-- Add update triggers for Layer 2 tables
CREATE TRIGGER update_crypto_sectors_updated_at 
    BEFORE UPDATE ON crypto_sectors 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_crypto_sector_mapping_updated_at 
    BEFORE UPDATE ON crypto_sector_mapping 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- LAYER 2: FOREIGN KEY CONSTRAINTS
-- =============================================

-- Add foreign key from cryptocurrencies to crypto_sectors (deferred until sectors are populated)
-- This will be added after seed data is inserted

-- =============================================
-- LAYER 2: VIEWS FOR COMMON QUERIES
-- =============================================

-- View for sector overview with current performance
CREATE OR REPLACE VIEW v_sector_overview AS
SELECT 
    cs.id,
    cs.name,
    cs.display_name,
    cs.sector_type,
    cs.maturity_level,
    cs.risk_category,
    sp.performance_24h,
    sp.performance_7d,
    sp.market_cap_total,
    sp.volume_total_24h,
    sp.momentum_score,
    sp.relative_strength,
    COUNT(csm.crypto_id) as crypto_count,
    sp.analysis_time as last_updated
FROM crypto_sectors cs
LEFT JOIN sector_performance sp ON cs.id = sp.sector_id 
    AND sp.analysis_time = (
        SELECT MAX(analysis_time) 
        FROM sector_performance sp2 
        WHERE sp2.sector_id = cs.id
    )
LEFT JOIN crypto_sector_mapping csm ON cs.id = csm.sector_id 
    AND csm.is_primary_sector = true
WHERE cs.is_active = true
GROUP BY cs.id, cs.name, cs.display_name, cs.sector_type, cs.maturity_level, 
         cs.risk_category, sp.performance_24h, sp.performance_7d, sp.market_cap_total,
         sp.volume_total_24h, sp.momentum_score, sp.relative_strength, sp.analysis_time
ORDER BY cs.sort_order, cs.name;

-- View for active rotation patterns
CREATE OR REPLACE VIEW v_active_rotations AS
SELECT 
    sra.id,
    cs_from.display_name as from_sector,
    cs_to.display_name as to_sector,
    sra.rotation_strength,
    sra.confidence_score,
    sra.capital_flow_estimate,
    sra.flow_direction,
    sra.analysis_time,
    CASE 
        WHEN sra.rotation_strength > 0.7 AND sra.confidence_score > 0.6 THEN 'strong'
        WHEN sra.rotation_strength > 0.4 AND sra.confidence_score > 0.4 THEN 'moderate'
        ELSE 'weak'
    END as rotation_strength_label
FROM sector_rotation_analysis sra
LEFT JOIN crypto_sectors cs_from ON sra.from_sector_id = cs_from.id
LEFT JOIN crypto_sectors cs_to ON sra.to_sector_id = cs_to.id
WHERE sra.analysis_time >= NOW() - INTERVAL '24 hours'
    AND sra.rotation_strength > 0.2
ORDER BY sra.rotation_strength DESC, sra.confidence_score DESC;

-- =============================================
-- LAYER 2: SEED DATA
-- =============================================

-- Insert crypto sectors
INSERT INTO crypto_sectors (name, display_name, description, sector_type, maturity_level, risk_category, characteristics, sort_order) VALUES
('bitcoin', 'Bitcoin', 'Store of value and digital gold', 'base_layer', 'high', 'low', '{"market_leader": true, "hedge_asset": true}', 1),
('ethereum', 'Ethereum & Smart Contracts', 'Smart contract platforms and dApps', 'platform', 'high', 'medium', '{"programmable": true, "defi_foundation": true}', 2),
('defi', 'DeFi', 'Decentralized Finance protocols and applications', 'application', 'medium', 'medium', '{"yield_generation": true, "composable": true}', 3),
('layer1', 'Layer 1 Blockchains', 'Alternative Layer 1 blockchain platforms', 'platform', 'medium', 'medium', '{"consensus_innovation": true, "ecosystem_building": true}', 4),
('layer2', 'Layer 2 Solutions', 'Scaling solutions and sidechains', 'infrastructure', 'medium', 'medium', '{"scalability": true, "low_fees": true}', 5),
('gaming_nft', 'Gaming & NFTs', 'Gaming tokens and NFT platforms', 'application', 'medium', 'high', '{"entertainment": true, "utility_tokens": true}', 6),
('infrastructure', 'Infrastructure', 'Blockchain infrastructure and tooling', 'infrastructure', 'medium', 'medium', '{"developer_tools": true, "enterprise_focus": true}', 7),
('privacy', 'Privacy Coins', 'Privacy-focused cryptocurrencies', 'utility', 'medium', 'high', '{"anonymity": true, "regulatory_risk": true}', 8),
('meme', 'Meme Coins', 'Community-driven and meme tokens', 'speculative', 'low', 'extreme', '{"social_driven": true, "high_volatility": true}', 9),
('stablecoins', 'Stablecoins', 'Price-stable cryptocurrencies', 'utility', 'high', 'low', '{"price_stability": true, "medium_of_exchange": true}', 10),
('ai_big_data', 'AI & Big Data', 'Artificial Intelligence and data-focused projects', 'application', 'low', 'high', '{"emerging_tech": true, "data_economy": true}', 11),
('real_world_assets', 'Real World Assets', 'Tokenization of real-world assets', 'application', 'low', 'medium', '{"tokenization": true, "traditional_bridge": true}', 12)
ON CONFLICT (name) DO UPDATE SET 
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- Now add foreign key constraint from cryptocurrencies to crypto_sectors
ALTER TABLE cryptocurrencies 
ADD CONSTRAINT fk_cryptocurrencies_sector 
FOREIGN KEY (sector_id) REFERENCES crypto_sectors(id);

-- =============================================
-- VALIDATION AND COMPLETION
-- =============================================

-- Validate Layer 2 tables creation
DO $$ 
DECLARE 
    table_count INTEGER;
    sector_count INTEGER;
BEGIN
    -- Count Layer 2 tables
    SELECT COUNT(*) INTO table_count 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('crypto_sectors', 'sector_performance', 'sector_rotation_analysis', 'crypto_sector_mapping');
    
    -- Count sectors created
    SELECT COUNT(*) INTO sector_count FROM crypto_sectors WHERE is_active = true;
    
    RAISE NOTICE '📊 Layer 2 Tables Created: %/4', table_count;
    RAISE NOTICE 'Crypto sectors defined: %', sector_count;
END $$;

-- Record migration completion
INSERT INTO system_info (key, value, created_at) 
VALUES ('migration_003_completed', 'Layer 2 (Sector Analysis) tables created successfully', NOW())
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();

COMMIT;
