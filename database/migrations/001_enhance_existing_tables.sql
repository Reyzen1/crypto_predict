-- backend/database/migrations/001_enhance_existing_tables.sql
-- =============================================
-- CryptoPredict Phase 2: Enhance Existing Tables
-- Migration from Phase 1 to Phase 2 Schema
-- =============================================

-- Start transaction for atomic migration
BEGIN;

-- 1. Enhance existing users table
-- Add role field for admin management
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'casual' 
    CHECK (role IN ('admin', 'professional', 'casual'));

-- Add index for role-based queries
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role, is_active);

-- Update superusers to admin role
UPDATE users SET role = 'admin' WHERE is_superuser = true;

-- Add comment for documentation
COMMENT ON COLUMN users.role IS 'User role: admin (system management), professional (advanced features), casual (basic features)';

-- 2. Enhance existing cryptocurrencies table
-- Add sector_id for Layer 2 integration (will reference crypto_sectors table)
ALTER TABLE cryptocurrencies 
ADD COLUMN IF NOT EXISTS sector_id INTEGER,
ADD COLUMN IF NOT EXISTS watchlist_tier VARCHAR(10) DEFAULT 'none' 
    CHECK (watchlist_tier IN ('tier1', 'tier2', 'none'));

-- Add indexes for new columns
CREATE INDEX IF NOT EXISTS idx_cryptocurrencies_sector ON cryptocurrencies(sector_id, is_active);
CREATE INDEX IF NOT EXISTS idx_cryptocurrencies_tier ON cryptocurrencies(watchlist_tier, is_active);

-- Add comments
COMMENT ON COLUMN cryptocurrencies.sector_id IS 'Reference to crypto_sectors table for Layer 2 classification';
COMMENT ON COLUMN cryptocurrencies.watchlist_tier IS 'Admin watchlist tier: tier1 (high priority), tier2 (medium priority), none (not in watchlist)';

-- 3. Enhance existing price_data table  
-- Add technical indicators for Layer 4 analysis
ALTER TABLE price_data 
ADD COLUMN IF NOT EXISTS technical_indicators JSONB DEFAULT '{}';

-- Add index for technical indicators queries
CREATE INDEX IF NOT EXISTS idx_price_data_indicators ON price_data USING GIN (technical_indicators);
CREATE INDEX IF NOT EXISTS idx_price_data_timestamp_desc ON price_data(timestamp DESC);

-- Add comment
COMMENT ON COLUMN price_data.technical_indicators IS 'JSONB field storing calculated technical indicators (RSI, MACD, etc.)';

-- 4. ENHANCE EXISTING PREDICTIONS TABLE (UNIFIED APPROACH)
-- Add new Phase 4 fields to existing predictions table
-- This preserves existing data while adding new capabilities

-- Add new Phase 4 columns
ALTER TABLE predictions 
ADD COLUMN IF NOT EXISTS layer_source VARCHAR(10) CHECK (layer_source IN ('layer1', 'layer2', 'layer3', 'layer4')),
ADD COLUMN IF NOT EXISTS macro_context JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS prediction_type VARCHAR(20) DEFAULT 'price'
ADD COLUMN IF NOT EXISTS predicted_value JSONB DEFAULT '{}';

-- Helper function for safe JSON conversion
CREATE OR REPLACE FUNCTION safe_to_jsonb(input_text TEXT)
RETURNS JSONB AS $$
BEGIN
    -- Return empty object for NULL or empty values
    IF input_text IS NULL OR input_text = '' OR input_text = 'NULL' OR input_text = '""' THEN
        RETURN '{}'::jsonb;
    END IF;
    
    -- Try to parse as JSON first
    BEGIN
        IF input_text ~ '^[\[\{].*[\]\}]$' THEN
            RETURN input_text::jsonb;
        END IF;
    EXCEPTION
        WHEN invalid_text_representation THEN
            -- If not valid JSON, wrap safely using json_build_object
            NULL;
    END;
    
    -- For non-JSON strings, wrap safely
    RETURN json_build_object('raw_data', input_text)::jsonb;
EXCEPTION
    WHEN OTHERS THEN
        -- Fallback to empty object if all else fails
        RETURN '{}'::jsonb;
END;
$$ LANGUAGE plpgsql;

-- Convert string fields to JSONB using safe function
ALTER TABLE predictions 
ALTER COLUMN features_used TYPE JSONB USING safe_to_jsonb(features_used::text);

ALTER TABLE predictions 
ALTER COLUMN model_parameters TYPE JSONB USING safe_to_jsonb(model_parameters::text);

ALTER TABLE predictions 
ALTER COLUMN input_features TYPE JSONB USING safe_to_jsonb(input_features::text);

ALTER TABLE predictions 
ALTER COLUMN debug_info TYPE JSONB USING safe_to_jsonb(debug_info::text);

-- Clean up NULL string values to proper NULL
UPDATE predictions SET user_id = NULL WHERE user_id::text = 'NULL';
UPDATE predictions SET actual_price = NULL WHERE actual_price::text = 'NULL';
UPDATE predictions SET accuracy_percentage = NULL WHERE accuracy_percentage::text = 'NULL';
UPDATE predictions SET absolute_error = NULL WHERE absolute_error::text = 'NULL';
UPDATE predictions SET squared_error = NULL WHERE squared_error::text = 'NULL';
UPDATE predictions SET is_accurate = NULL WHERE is_accurate::text = 'NULL';
UPDATE predictions SET training_data_end = NULL WHERE training_data_end::text = 'NULL';
UPDATE predictions SET market_conditions = NULL WHERE market_conditions::text = 'NULL';
UPDATE predictions SET volatility_level = NULL WHERE volatility_level::text = 'NULL';
UPDATE predictions SET model_training_time = NULL WHERE model_training_time::text = 'NULL';
UPDATE predictions SET prediction_time = NULL WHERE prediction_time::text = 'NULL';
UPDATE predictions SET evaluated_at = NULL WHERE evaluated_at::text = 'NULL';

-- Ensure proper constraints for enhanced table
ALTER TABLE predictions 
ALTER COLUMN confidence_score SET NOT NULL;

-- Add constraint if it doesn't exist
DO $$ 
BEGIN
    ALTER TABLE predictions ADD CONSTRAINT predictions_confidence_check 
        CHECK (confidence_score >= 0 AND confidence_score <= 1);
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Add new indexes for Phase 2 functionality
CREATE INDEX IF NOT EXISTS idx_predictions_crypto_layer ON predictions(crypto_id, layer_source, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_layer_source ON predictions(layer_source, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_macro_context ON predictions USING GIN (macro_context);

CREATE INDEX IF NOT EXISTS idx_predictions_prediction_type ON predictions(prediction_type);
CREATE INDEX IF NOT EXISTS idx_predictions_layer_type ON predictions(layer_source, prediction_type);
CREATE INDEX IF NOT EXISTS idx_predictions_crypto_type ON predictions(crypto_id, prediction_type);
CREATE INDEX IF NOT EXISTS idx_predictions_type_time ON predictions(prediction_type, created_at DESC);

-- Add comments for documentation
COMMENT ON TABLE predictions IS 'Unified predictions table for Phase 1 & Phase 2 - Enhanced 4-Layer AI System';
COMMENT ON COLUMN predictions.layer_source IS 'Source layer for prediction: layer1=macro, layer2=sector, layer3=asset, layer4=timing';
COMMENT ON COLUMN predictions.macro_context IS 'Macro market context from Layer 1 analysis stored as JSONB';
COMMENT ON COLUMN predictions.prediction_type IS 'price, regime, sector_rotation, signal_classification, probability';

-- Drop helper function after use
DROP FUNCTION IF EXISTS safe_to_jsonb(TEXT);

-- 5. Create function for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add trigger for predictions table if it doesn't exist
DO $$
BEGIN
    CREATE TRIGGER update_predictions_updated_at 
        BEFORE UPDATE ON predictions 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- 6. Validate enhanced schema
-- Check that all enhancements were applied correctly
DO $$ 
DECLARE 
    users_role_count INTEGER;
    crypto_sector_count INTEGER;
    predictions_layer_count INTEGER;
BEGIN
    -- Verify users.role column exists
    SELECT COUNT(*) INTO users_role_count 
    FROM information_schema.columns 
    WHERE table_name='users' AND column_name='role';
    
    -- Verify cryptocurrencies.sector_id column exists  
    SELECT COUNT(*) INTO crypto_sector_count
    FROM information_schema.columns 
    WHERE table_name='cryptocurrencies' AND column_name='sector_id';
    
    -- Verify predictions.layer_source column exists
    SELECT COUNT(*) INTO predictions_layer_count
    FROM information_schema.columns 
    WHERE table_name='predictions' AND column_name='layer_source';
    
    -- Raise notice with validation results
    RAISE NOTICE 'Schema Enhancement Validation:';
    RAISE NOTICE 'Users role column: %', CASE WHEN users_role_count > 0 THEN 'EXISTS ✓' ELSE 'MISSING ✗' END;
    RAISE NOTICE 'Crypto sector_id column: %', CASE WHEN crypto_sector_count > 0 THEN 'EXISTS ✓' ELSE 'MISSING ✗' END;
    RAISE NOTICE 'Predictions layer_source column: %', CASE WHEN predictions_layer_count > 0 THEN 'EXISTS ✓' ELSE 'MISSING ✗' END;
    
    -- Verify data integrity
    RAISE NOTICE 'Predictions table records: %', (SELECT COUNT(*) FROM predictions);
    RAISE NOTICE 'Users with role assigned: %', (SELECT COUNT(*) FROM users WHERE role IS NOT NULL);
END $$;

-- Create backup info
INSERT INTO system_info (key, value, created_at) 
VALUES ('migration_001_completed', 'Enhanced existing tables for Phase 2', NOW())
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();

-- Commit transaction
COMMIT;
