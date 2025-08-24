-- backend/database/migrations/006_create_indexes_triggers.sql
-- =============================================
-- CryptoPredict Phase 2: Final Indexes, Triggers & System Tables
-- Performance optimization and system management tables
-- =============================================

BEGIN;

-- =============================================
-- SYSTEM MANAGEMENT TABLES
-- =============================================

-- 1. System Info Table (if not exists)
-- For storing migration status and system metadata
CREATE TABLE IF NOT EXISTS system_info (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) NOT NULL UNIQUE,
    value TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. AI Models Management Table
-- Tracks AI model versions, performance, and status
CREATE TABLE IF NOT EXISTS ai_models (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    version VARCHAR(50) NOT NULL,
    model_type VARCHAR(20) NOT NULL CHECK (model_type IN ('macro', 'sector', 'asset', 'timing', 'ensemble')),
    status VARCHAR(20) DEFAULT 'inactive' CHECK (status IN ('active', 'training', 'inactive', 'error', 'deprecated')),
    
    -- Model Configuration
    configuration JSONB DEFAULT '{}',
    hyperparameters JSONB DEFAULT '{}',
    training_config JSONB DEFAULT '{}',
    
    -- Performance Metrics
    performance_metrics JSONB DEFAULT '{}',
    accuracy_metrics JSONB DEFAULT '{}',
    backtesting_results JSONB DEFAULT '{}',
    
    -- Model Lifecycle
    training_data_from DATE,
    training_data_to DATE,
    last_trained TIMESTAMP WITH TIME ZONE,
    last_prediction TIMESTAMP WITH TIME ZONE,
    next_retrain_due TIMESTAMP WITH TIME ZONE,
    
    -- Health and Monitoring
    health_status JSONB DEFAULT '{}',
    error_logs JSONB DEFAULT '[]',
    prediction_count INTEGER DEFAULT 0,
    success_rate NUMERIC(5,4),
    
    -- Metadata
    created_by INTEGER REFERENCES users(id),
    model_path VARCHAR(500),
    model_size_mb NUMERIC(10,2),
    deployment_notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for ai_models
CREATE INDEX IF NOT EXISTS idx_ai_models_type_status ON ai_models(model_type, status);
CREATE INDEX IF NOT EXISTS idx_ai_models_performance ON ai_models(model_type, success_rate DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_ai_models_training ON ai_models(last_trained DESC);
CREATE INDEX IF NOT EXISTS idx_ai_models_config ON ai_models USING GIN (configuration);

-- 3. System Health Monitoring Table
-- Tracks system health, performance, and issues
CREATE TABLE IF NOT EXISTS system_health (
    id SERIAL PRIMARY KEY,
    check_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Service Status
    api_status JSONB DEFAULT '{}',
    database_status JSONB DEFAULT '{}',
    ml_models_status JSONB DEFAULT '{}',
    data_pipeline_status JSONB DEFAULT '{}',
    external_apis_status JSONB DEFAULT '{}',
    
    -- Performance Metrics
    overall_health_score NUMERIC(5,2) DEFAULT 100 CHECK (overall_health_score >= 0 AND overall_health_score <= 100),
    response_time_ms NUMERIC(10,2),
    cpu_usage_percent NUMERIC(5,2),
    memory_usage_percent NUMERIC(5,2),
    disk_usage_percent NUMERIC(5,2),
    
    -- Database Metrics
    active_connections INTEGER,
    slow_queries_count INTEGER DEFAULT 0,
    database_size_mb NUMERIC(15,2),
    
    -- Application Metrics
    active_users_count INTEGER DEFAULT 0,
    requests_per_minute NUMERIC(10,2),
    error_rate_percent NUMERIC(5,4) DEFAULT 0,
    
    -- Detailed Metrics
    performance_metrics JSONB DEFAULT '{}',
    error_logs JSONB DEFAULT '[]',
    warnings JSONB DEFAULT '[]',
    
    -- Alerts and Notifications
    alert_level VARCHAR(10) DEFAULT 'normal' CHECK (alert_level IN ('normal', 'warning', 'error', 'critical')),
    alerts_sent JSONB DEFAULT '[]',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for system_health
CREATE INDEX IF NOT EXISTS idx_system_health_time ON system_health(check_time DESC);
CREATE INDEX IF NOT EXISTS idx_system_health_score ON system_health(overall_health_score ASC, check_time DESC);
CREATE INDEX IF NOT EXISTS idx_system_health_alert ON system_health(alert_level, check_time DESC);

-- 4. User Activities Logging Table  
-- Tracks user actions for analytics and audit
CREATE TABLE IF NOT EXISTS user_activities (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Activity Details
    activity_type VARCHAR(50) NOT NULL,
    activity_category VARCHAR(30) DEFAULT 'general',
    activity_data JSONB DEFAULT '{}',
    
    -- Request Details
    ip_address INET,
    user_agent TEXT,
    request_path VARCHAR(500),
    request_method VARCHAR(10),
    response_status INTEGER,
    response_time_ms NUMERIC(10,2),
    
    -- Session and Context
    session_id VARCHAR(100),
    device_type VARCHAR(20),
    browser VARCHAR(50),
    location_country VARCHAR(2),
    
    -- Metadata
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    additional_data JSONB DEFAULT '{}',
    
    activity_time TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for user_activities
CREATE INDEX IF NOT EXISTS idx_user_activities_user_time ON user_activities(user_id, activity_time DESC);
CREATE INDEX IF NOT EXISTS idx_user_activities_type ON user_activities(activity_type, activity_time DESC);
CREATE INDEX IF NOT EXISTS idx_user_activities_session ON user_activities(session_id, activity_time DESC);
CREATE INDEX IF NOT EXISTS idx_user_activities_data ON user_activities USING GIN (activity_data);

-- 5. Notifications Table
-- System notifications for users
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Notification Content
    notification_type VARCHAR(20) NOT NULL CHECK (notification_type IN ('signal', 'alert', 'system', 'educational', 'marketing')),
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    
    -- Notification Properties
    status VARCHAR(20) DEFAULT 'unread' CHECK (status IN ('unread', 'read', 'dismissed', 'archived')),
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    channel VARCHAR(20) DEFAULT 'in_app' CHECK (channel IN ('in_app', 'email', 'sms', 'push')),
    
    -- Delivery Control
    scheduled_for TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '30 days'),
    
    -- Metadata
    source VARCHAR(50) DEFAULT 'system',
    reference_id INTEGER, -- Reference to related entity (signal, suggestion, etc.)
    reference_type VARCHAR(30),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for notifications
CREATE INDEX IF NOT EXISTS idx_notifications_user_status ON notifications(user_id, status, scheduled_for DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type, priority, scheduled_for DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_expires ON notifications(expires_at) WHERE status != 'expired';
CREATE INDEX IF NOT EXISTS idx_notifications_reference ON notifications(reference_type, reference_id);

-- =============================================
-- ADDITIONAL PERFORMANCE INDEXES
-- =============================================

-- Enhanced existing table indexes for better performance
CREATE INDEX IF NOT EXISTS idx_price_data_crypto_timestamp ON price_data(crypto_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_price_data_volume ON price_data(volume DESC, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_price_data_technical ON price_data USING GIN (technical_indicators);

-- Predictions table enhanced indexes
CREATE INDEX IF NOT EXISTS idx_predictions_model_performance ON predictions(model_name, accuracy_percentage DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_predictions_horizon ON predictions(prediction_horizon, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_evaluation ON predictions(is_realized, is_accurate, evaluated_at DESC);

CREATE INDEX IF NOT EXISTS idx_predictions_prediction_type ON predictions(prediction_type);
CREATE INDEX IF NOT EXISTS idx_predictions_layer_type ON predictions(layer_source, prediction_type);
CREATE INDEX IF NOT EXISTS idx_predictions_crypto_type ON predictions(crypto_id, prediction_type);
CREATE INDEX IF NOT EXISTS idx_predictions_type_time ON predictions(prediction_type, created_at DESC);

-- Cryptocurrencies enhanced indexes
CREATE INDEX IF NOT EXISTS idx_cryptocurrencies_market_cap ON cryptocurrencies(market_cap DESC NULLS LAST) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_cryptocurrencies_volume ON cryptocurrencies(total_volume DESC NULLS LAST) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_cryptocurrencies_price_change ON cryptocurrencies(current_price, updated_at DESC);

-- Users enhanced indexes
CREATE INDEX IF NOT EXISTS idx_users_role_active ON users(role, is_active, last_login DESC);
CREATE INDEX IF NOT EXISTS idx_users_preferences ON users(preferences);

-- =============================================
-- CROSS-LAYER PERFORMANCE VIEWS
-- =============================================

-- Comprehensive system overview view
CREATE OR REPLACE VIEW v_system_overview AS
SELECT 
    'database' as component,
    (SELECT COUNT(*) FROM predictions WHERE created_at >= NOW() - INTERVAL '24 hours') as daily_predictions,
    (SELECT COUNT(*) FROM trading_signals WHERE status = 'active') as active_signals,
    (SELECT COUNT(*) FROM ai_suggestions WHERE status = 'pending') as pending_suggestions,
    (SELECT COUNT(*) FROM users WHERE is_active = true) as active_users,
    NOW() as snapshot_time
UNION ALL
SELECT 
    'layer1' as component,
    (SELECT COUNT(*) FROM market_regime_analysis WHERE analysis_time >= NOW() - INTERVAL '24 hours'),
    (SELECT COUNT(*) FROM market_sentiment_data WHERE timestamp >= NOW() - INTERVAL '24 hours'),
    (SELECT COUNT(*) FROM dominance_data WHERE timestamp >= NOW() - INTERVAL '24 hours'),
    NULL,
    NOW()
UNION ALL
SELECT 
    'layer2' as component,
    (SELECT COUNT(*) FROM sector_performance WHERE analysis_time >= NOW() - INTERVAL '24 hours'),
    (SELECT COUNT(*) FROM sector_rotation_analysis WHERE analysis_time >= NOW() - INTERVAL '24 hours'),
    (SELECT COUNT(*) FROM crypto_sectors WHERE is_active = true),
    NULL,
    NOW()
UNION ALL
SELECT 
    'layer3' as component,
    (SELECT COUNT(*) FROM watchlist_items WHERE status = 'active'),
    (SELECT COUNT(*) FROM ai_suggestions WHERE status = 'pending'),
    (SELECT COUNT(*) FROM watchlists WHERE is_active = true),
    NULL,
    NOW()
UNION ALL
SELECT 
    'layer4' as component,
    (SELECT COUNT(*) FROM trading_signals WHERE status = 'active'),
    (SELECT COUNT(*) FROM signal_executions WHERE status IN ('filled', 'partially_filled')),
    (SELECT COUNT(*) FROM risk_management WHERE risk_limit_breached = false),
    NULL,
    NOW();

-- Latest data freshness view
CREATE OR REPLACE VIEW v_data_freshness AS
SELECT 
    'price_data' as table_name,
    MAX(timestamp) as latest_timestamp,
    COUNT(*) FILTER (WHERE timestamp >= NOW() - INTERVAL '1 hour') as recent_count,
    NOW() - MAX(timestamp) as staleness_duration
FROM price_data
UNION ALL
SELECT 
    'market_regime_analysis',
    MAX(analysis_time),
    COUNT(*) FILTER (WHERE analysis_time >= NOW() - INTERVAL '1 hour'),
    NOW() - MAX(analysis_time)
FROM market_regime_analysis
UNION ALL
SELECT 
    'sector_performance',
    MAX(analysis_time),
    COUNT(*) FILTER (WHERE analysis_time >= NOW() - INTERVAL '1 hour'),
    NOW() - MAX(analysis_time)
FROM sector_performance;

-- =============================================
-- SYSTEM FUNCTIONS
-- =============================================

-- Function to clean up expired data
CREATE OR REPLACE FUNCTION cleanup_expired_data()
RETURNS TEXT AS $$
DECLARE
    cleanup_results TEXT := '';
    expired_count INTEGER;
BEGIN
    -- Clean up expired notifications
    DELETE FROM notifications WHERE expires_at < NOW() AND status = 'read';
    GET DIAGNOSTICS expired_count = ROW_COUNT;
    cleanup_results := cleanup_results || 'Notifications cleaned: ' || expired_count || E'\n';
    
    -- Clean up expired trading signals
    UPDATE trading_signals SET status = 'expired' WHERE expires_at < NOW() AND status = 'active';
    GET DIAGNOSTICS expired_count = ROW_COUNT;
    cleanup_results := cleanup_results || 'Signals expired: ' || expired_count || E'\n';
    
    -- Clean up old user activities (keep last 90 days)
    DELETE FROM user_activities WHERE activity_time < NOW() - INTERVAL '90 days';
    GET DIAGNOSTICS expired_count = ROW_COUNT;
    cleanup_results := cleanup_results || 'Activities cleaned: ' || expired_count || E'\n';
    
    -- Clean up old system health records (keep last 30 days)
    DELETE FROM system_health WHERE check_time < NOW() - INTERVAL '30 days';
    GET DIAGNOSTICS expired_count = ROW_COUNT;
    cleanup_results := cleanup_results || 'Health records cleaned: ' || expired_count || E'\n';
    
    RETURN cleanup_results;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate system health score
CREATE OR REPLACE FUNCTION calculate_system_health()
RETURNS NUMERIC AS $$
DECLARE
    health_score NUMERIC := 100.0;
    active_errors INTEGER;
    data_freshness INTERVAL;
    api_response_time NUMERIC;
BEGIN
    -- Check for active errors
    SELECT COUNT(*) INTO active_errors 
    FROM system_health 
    WHERE check_time >= NOW() - INTERVAL '1 hour' 
    AND alert_level IN ('error', 'critical');
    
    -- Deduct points for errors
    health_score := health_score - (active_errors * 10);
    
    -- Check data freshness
    SELECT NOW() - MAX(timestamp) INTO data_freshness FROM price_data;
    IF data_freshness > INTERVAL '2 hours' THEN
        health_score := health_score - 20;
    ELSIF data_freshness > INTERVAL '1 hour' THEN
        health_score := health_score - 10;
    END IF;
    
    -- Ensure score doesn't go below 0
    IF health_score < 0 THEN
        health_score := 0;
    END IF;
    
    RETURN health_score;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- ADD MISSING TRIGGERS
-- =============================================

-- Add triggers for system tables
CREATE TRIGGER update_ai_models_updated_at 
    BEFORE UPDATE ON ai_models 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_info_updated_at 
    BEFORE UPDATE ON system_info 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- SEED SYSTEM DATA
-- =============================================

-- Insert system info records
INSERT INTO system_info (key, value, metadata) VALUES
('system_version', '2.0.0', '{"phase": "Phase 2", "layers": 4}'::jsonb),
('database_version', '2.0.0', '{"migration_completed": true}'::jsonb),
('last_cleanup', NOW()::text, '{"auto_cleanup": true}'::jsonb),
('maintenance_mode', 'false', '{"scheduled_maintenance": null}'::jsonb)
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();

-- Insert initial AI models placeholders
INSERT INTO ai_models (name, version, model_type, status, configuration) VALUES
('macro_regime_detector', '1.0', 'macro', 'inactive', '{"type": "classification", "target": "market_regime"}'::jsonb),
('sector_rotation_predictor', '1.0', 'sector', 'inactive', '{"type": "regression", "target": "sector_performance"}'::jsonb),
('asset_selector', '1.0', 'asset', 'inactive', '{"type": "ranking", "target": "asset_score"}'::jsonb),
('timing_optimizer', '1.0', 'timing', 'inactive', '{"type": "signal_generation", "target": "entry_exit_points"}'::jsonb)
ON CONFLICT (name) DO NOTHING;

-- Insert initial system health record
INSERT INTO system_health (
    api_status,
    database_status,
    ml_models_status,
    overall_health_score,
    alert_level
) VALUES (
    '{"status": "operational", "response_time_ms": 50}'::jsonb,
    '{"status": "operational", "connections": 5}'::jsonb,
    '{"status": "initializing", "active_models": 0}'::jsonb,
    95.0,
    'normal'
);

-- =============================================
-- FINAL VALIDATION
-- =============================================

-- Comprehensive validation of entire schema
DO $$ 
DECLARE 
    total_tables INTEGER;
    total_indexes INTEGER;
    total_triggers INTEGER;
    total_views INTEGER;
BEGIN
    -- Count all tables
    SELECT COUNT(*) INTO total_tables 
    FROM information_schema.tables 
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
    
    -- Count all indexes
    SELECT COUNT(*) INTO total_indexes
    FROM pg_indexes 
    WHERE schemaname = 'public';
    
    -- Count all triggers
    SELECT COUNT(*) INTO total_triggers
    FROM information_schema.triggers
    WHERE trigger_schema = 'public';
    
    -- Count all views
    SELECT COUNT(*) INTO total_views
    FROM information_schema.views
    WHERE table_schema = 'public';
    
    RAISE NOTICE '🏆 FINAL SCHEMA VALIDATION:';
    RAISE NOTICE '📊 Total Tables: %', total_tables;
    RAISE NOTICE '🔍 Total Indexes: %', total_indexes;
    RAISE NOTICE '⚡ Total Triggers: %', total_triggers;
    RAISE NOTICE '👁️ Total Views: %', total_views;
    
    -- Validate critical tables exist
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'predictions') AND
       EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'trading_signals') AND
       EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ai_suggestions') THEN
        RAISE NOTICE '✅ All critical tables present';
    ELSE
        RAISE NOTICE '❌ Missing critical tables';
    END IF;
    
    -- Check data integrity
    RAISE NOTICE '📈 Predictions table records: %', (SELECT COUNT(*) FROM predictions);
    RAISE NOTICE '🏛️ Crypto sectors: %', (SELECT COUNT(*) FROM crypto_sectors WHERE is_active = true);
    RAISE NOTICE '👥 Active users: %', (SELECT COUNT(*) FROM users WHERE is_active = true);
END $$;

-- Record final migration completion
INSERT INTO system_info (key, value, metadata) VALUES 
('migrations_completed', 'all', '{"last_migration": "006", "completed_at": "' || NOW() || '", "total_migrations": 6}'::jsonb)
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();

COMMIT;
