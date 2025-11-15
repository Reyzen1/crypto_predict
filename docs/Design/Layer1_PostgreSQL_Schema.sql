-- ===============================================
-- CryptoPredict Layer 1 Database Schema
-- PostgreSQL Implementation - 9 Core Tables
-- Date: October 2, 2025
-- Purpose: Complete Layer 1 (Macro Analysis) implementation
-- ===============================================

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- ===============================================
-- 1. USERS TABLE - Core user management and authentication
-- ===============================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    role VARCHAR(20) NOT NULL DEFAULT 'public',
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    login_count INTEGER DEFAULT 0,
    preferences JSONB DEFAULT '{}',
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    last_login TIMESTAMP WITH TIME ZONE,
    bio TEXT,
    profile_picture_url VARCHAR(500),
    reset_password_token VARCHAR(255),
    reset_password_expires TIMESTAMP WITH TIME ZONE,
    email_verification_token VARCHAR(255),
    email_verification_expires TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    lockout_expires TIMESTAMP WITH TIME ZONE,
    referral_code VARCHAR(50) UNIQUE,
    referred_by INTEGER REFERENCES users(id),
    referral_count INTEGER DEFAULT 0,
    account_balance NUMERIC(15,2) DEFAULT 0.00,
    subscription_plan VARCHAR(20) DEFAULT 'free',
    subscription_expires_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_login_count_positive CHECK (login_count >= 0),
    CONSTRAINT chk_referral_count_positive CHECK (referral_count >= 0),
    CONSTRAINT chk_failed_login_attempts_positive CHECK (failed_login_attempts >= 0),
    CONSTRAINT chk_account_balance_positive CHECK (account_balance >= 0)
);

-- Indexes for users table
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_users_subscription_plan ON users(subscription_plan);
CREATE INDEX idx_users_referral_code ON users(referral_code) WHERE referral_code IS NOT NULL;
CREATE INDEX idx_users_created_at ON users(created_at);

-- ===============================================
-- 2. ASSETS TABLE - Cryptocurrency and asset management
-- ===============================================
CREATE TABLE IF NOT EXISTS assets (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    asset_type VARCHAR(20) NOT NULL,
    quote_currency VARCHAR(10),
    external_ids JSONB DEFAULT '{}',
    logo_url TEXT,
    links JSONB DEFAULT '{}',
    description TEXT,
    
    -- Market data
    market_cap NUMERIC(30,2),
    market_cap_rank INTEGER,
    current_price NUMERIC(20,8),
    total_volume NUMERIC(30,2),
    circulating_supply NUMERIC(30,8),
    total_supply NUMERIC(30,8),
    max_supply NUMERIC(30,8),
    price_change_percentage_24h NUMERIC(10,4),
    price_change_percentage_7d NUMERIC(10,4),
    price_change_percentage_30d NUMERIC(10,4),
    ath NUMERIC(20,8),
    ath_date TIMESTAMP WITH TIME ZONE,
    atl NUMERIC(20,8),
    atl_date TIMESTAMP WITH TIME ZONE,
    metrics_details JSONB DEFAULT '{}',
    
    -- Usage tracking
    timeframe_usage JSONB DEFAULT '{}',
    
    -- Performance optimization cache
    timeframe_data JSONB DEFAULT '{}',
    
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    access_count INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_supported BOOLEAN NOT NULL DEFAULT true,
    data_quality_score INTEGER NOT NULL DEFAULT 100,
    data_source VARCHAR(20) NOT NULL DEFAULT 'coingecko',
    last_price_update TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_market_cap_positive CHECK (market_cap IS NULL OR market_cap >= 0),
    CONSTRAINT chk_current_price_positive CHECK (current_price IS NULL OR current_price > 0),
    CONSTRAINT chk_supply_positive CHECK (circulating_supply IS NULL OR circulating_supply >= 0),
    CONSTRAINT chk_data_quality CHECK (data_quality_score BETWEEN 0 AND 100),
    CONSTRAINT chk_market_cap_rank CHECK (market_cap_rank IS NULL OR market_cap_rank > 0),
    CONSTRAINT chk_access_count_positive CHECK (access_count >= 0)
);

-- Indexes for assets table
CREATE INDEX idx_assets_symbol ON assets(symbol);
CREATE INDEX idx_assets_type_active ON assets(asset_type, is_active);
CREATE INDEX idx_assets_market_cap_rank ON assets(market_cap_rank) WHERE market_cap_rank IS NOT NULL;
CREATE INDEX idx_assets_last_accessed ON assets(last_accessed_at) WHERE last_accessed_at IS NOT NULL;
CREATE INDEX idx_assets_data_source ON assets(data_source);
-- GIN index for fast JSON queries on timeframe_data cache
CREATE INDEX idx_assets_timeframe_data ON assets USING GIN (timeframe_data) WHERE timeframe_data IS NOT NULL;

-- ===============================================
-- 3. PRICE_DATA TABLE - Historical and real-time price data
-- ===============================================
CREATE TABLE IF NOT EXISTS price_data (
    id BIGSERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    timeframe VARCHAR(10) NOT NULL,
    candle_time TIMESTAMP WITH TIME ZONE NOT NULL,
    open_price NUMERIC(20,8) NOT NULL,
    high_price NUMERIC(20,8) NOT NULL,
    low_price NUMERIC(20,8) NOT NULL,
    close_price NUMERIC(20,8) NOT NULL,
    volume NUMERIC(30,2) NOT NULL DEFAULT 0,
    market_cap NUMERIC(30,2),
    trade_count INTEGER,
    vwap NUMERIC(20,8),
    
    technical_indicators JSONB DEFAULT '{}',
    
    is_validated BOOLEAN NOT NULL DEFAULT false,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_ohlc_logic CHECK (low_price <= open_price AND low_price <= close_price AND high_price >= open_price AND high_price >= close_price),
    CONSTRAINT chk_prices_positive CHECK (open_price > 0 AND high_price > 0 AND low_price > 0 AND close_price > 0),
    CONSTRAINT chk_volume_non_negative CHECK (volume >= 0),
    CONSTRAINT unique_asset_timeframe_candle UNIQUE (asset_id, timeframe, candle_time)
);

-- Indexes for price_data table
CREATE INDEX idx_price_data_asset_timeframe_time ON price_data(asset_id, timeframe, candle_time DESC);
CREATE INDEX idx_price_data_candle_time ON price_data(candle_time DESC);
CREATE INDEX idx_price_data_timeframe ON price_data(timeframe);
CREATE INDEX idx_price_data_volume ON price_data(volume DESC) WHERE volume > 0;

-- ===============================================
-- 4. METRICS_SNAPSHOT TABLE - Macro market analysis snapshots
-- ===============================================
CREATE TABLE IF NOT EXISTS metrics_snapshot (
    id BIGSERIAL PRIMARY KEY,
    snapshot_time TIMESTAMP WITH TIME ZONE NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    btc_price_usd NUMERIC(18,8) NOT NULL,
    
    -- Technical Indicators
    rsi_14 NUMERIC(5,2),
    sma_200 NUMERIC(30,8),
    ema_200 NUMERIC(30,8),
    
    -- Market Sentiment
    fear_greed_index NUMERIC(5,2),
    google_trends_score NUMERIC(5,2),
    
    -- Derivatives & Futures
    funding_rate_btc NUMERIC(10,6),
    open_interest_btc NUMERIC(30,2),
    
    -- On-chain & Whale Flows
    whale_netflow_24h NUMERIC(30,2),
    active_addresses_btc INTEGER,
    
    -- Composite & Health
    altcoin_dominance NUMERIC(5,2),
    liquidity_score NUMERIC(10,6),
    
    -- Cycle & Returns
    halving_countdown_days INTEGER,
    weekly_return NUMERIC(5,4),
    monthly_return NUMERIC(5,4),
    
    -- Dominance & Total Market-Cap Levels
    btc_dominance NUMERIC(5,2),
    eth_dominance NUMERIC(5,2),
    usdt_dominance NUMERIC(5,2),
    total_market_cap NUMERIC(18,2),
    
    -- Intermarket Levels
    sp500 NUMERIC(10,2),
    gold NUMERIC(10,2),
    dxy NUMERIC(10,2),
    
    -- Liquidations
    liquidations_long NUMERIC(30,2),
    liquidations_short NUMERIC(30,2),
    liquidation_zones JSONB DEFAULT '[]',
    
    -- Extended Metrics
    extended_metrics JSONB DEFAULT '{}',
    
    -- Enhanced Core Metrics
    btc_eth_correlation_30d NUMERIC(6,4),
    btc_sp500_correlation_30d NUMERIC(6,4),
    us_10y_yield NUMERIC(8,4),
    vix_index NUMERIC(8,4),
    
    -- Market Breadth & Quality
    crypto_market_breadth NUMERIC(6,2),
    new_highs_24h INTEGER,
    new_lows_24h INTEGER,
    momentum_index NUMERIC(8,4),
    
    -- Data Quality & Metadata
    data_quality_flags JSONB DEFAULT '{}',
    snapshot_version VARCHAR(50),
    is_validated BOOLEAN NOT NULL DEFAULT false,
    has_anomalies BOOLEAN NOT NULL DEFAULT false,
    data_source VARCHAR(20) NOT NULL DEFAULT 'aggregated',
    
    -- Performance Timing
    data_collection_started TIMESTAMP WITH TIME ZONE,
    data_collection_completed TIMESTAMP WITH TIME ZONE,
    collection_duration_ms INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_snapshot_time_timeframe UNIQUE (snapshot_time, timeframe),
    CONSTRAINT chk_fear_greed_range CHECK (fear_greed_index IS NULL OR fear_greed_index BETWEEN 0 AND 100),
    CONSTRAINT chk_dominance_range CHECK (btc_dominance IS NULL OR btc_dominance BETWEEN 0 AND 100),
    CONSTRAINT chk_btc_price_positive CHECK (btc_price_usd > 0),
    CONSTRAINT chk_collection_duration CHECK (collection_duration_ms IS NULL OR collection_duration_ms >= 0)
);

-- Indexes for metrics_snapshot table
CREATE INDEX idx_metrics_snapshot_time ON metrics_snapshot(snapshot_time DESC);
CREATE INDEX idx_metrics_snapshot_timeframe ON metrics_snapshot(timeframe);
CREATE INDEX idx_metrics_snapshot_time_timeframe ON metrics_snapshot(snapshot_time DESC, timeframe);
CREATE INDEX idx_metrics_snapshot_btc_price ON metrics_snapshot(btc_price_usd);

-- ===============================================
-- 5. AI_REGIME_ANALYSIS TABLE - AI-powered market regime analysis
-- ===============================================
CREATE TABLE IF NOT EXISTS ai_regime_analysis (
    id BIGSERIAL PRIMARY KEY,
    metrics_snapshot_id BIGINT NOT NULL REFERENCES metrics_snapshot(id) ON DELETE CASCADE,
    ai_model_id INTEGER NOT NULL, -- Will reference ai_models(id)
    
    -- Analysis Metadata
    analysis_time TIMESTAMP WITH TIME ZONE NOT NULL,
    analysis_timeframe VARCHAR(10) NOT NULL,
    data_source VARCHAR(20) NOT NULL DEFAULT 'live',
    
    -- Regime Classification
    current_regime VARCHAR(15) NOT NULL,
    predicted_regime VARCHAR(15),
    regime_confidence NUMERIC(4,2) NOT NULL,
    regime_transition_prob NUMERIC(4,2),
    regime_duration_days INTEGER,
    regime_duration_estimate INTEGER,
    
    -- Regime Strength & Quality Metrics
    trend_strength_score NUMERIC(6,2),
    regime_quality_score NUMERIC(6,2),
    volatility_regime_score NUMERIC(6,2),
    momentum_alignment_score NUMERIC(6,2),
    
    -- Market Structure Analysis
    trend_intact BOOLEAN,
    structure_break BOOLEAN,
    structure_change_type VARCHAR(20),
    structure_strength NUMERIC(8,4),
    
    -- Technical Breakout & Pattern Analysis
    breakout_signal BOOLEAN,
    breakout_type VARCHAR(30),
    breakout_level NUMERIC(18,8),
    volume_confirmation BOOLEAN,
    volume_surge_ratio NUMERIC(6,2),
    retest_confirmation BOOLEAN,
    volatility_expansion_score NUMERIC(6,2),
    
    -- Multi-Timeframe Analysis
    timeframe_alignment JSONB DEFAULT '{}',
    multi_timeframe_agreement BOOLEAN,
    timeframe_consensus_score NUMERIC(4,2),
    
    -- AI-Detected Key Levels & Zones
    key_levels JSONB DEFAULT '[]',
    
    -- Market Psychology & Sentiment Integration
    sentiment_regime VARCHAR(20),
    fear_greed_impact NUMERIC(6,2),
    sentiment_regime_conflict BOOLEAN,
    psychological_level_score NUMERIC(4,2),
    
    -- Flow & Liquidity Analysis
    liquidity_regime VARCHAR(20),
    institutional_flow_score NUMERIC(6,2),
    retail_participation_score NUMERIC(6,2),
    whale_activity_influence BOOLEAN,
    
    -- Intermarket & Macro Context
    macro_regime_alignment VARCHAR(20),
    correlation_stability NUMERIC(4,2),
    risk_on_off_regime BOOLEAN,
    global_risk_appetite VARCHAR(15),
    
    -- Regime Transition Signals
    transition_indicators JSONB DEFAULT '{}',
    
    -- Trading & Investment Implications
    recommended_strategy VARCHAR(20),
    risk_adjustment_factor NUMERIC(4,2),
    position_sizing_guidance VARCHAR(20),
    sector_regime_impact JSONB DEFAULT '{}',
    
    -- Enhanced AI Meta-Signals
    ai_confidence_score NUMERIC(4,2),
    signal_agreement_score NUMERIC(4,2),
    prediction_stability NUMERIC(4,2),
    model_performance_rating VARCHAR(20),
    
    -- Historical Context & Comparison
    historical_analogue VARCHAR(30),
    historical_similarity NUMERIC(4,2),
    regime_statistics JSONB DEFAULT '{}',
    
    -- Quality Assurance & Validation
    analysis_validated BOOLEAN NOT NULL DEFAULT false,
    validation_flags JSONB DEFAULT '{}',
    analysis_version VARCHAR(50),
    analyst_notes TEXT,
    
    -- Comprehensive Analysis Rationale
    analysis_data JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT chk_regime_confidence CHECK (regime_confidence BETWEEN 0 AND 1),
    CONSTRAINT chk_transition_prob CHECK (regime_transition_prob IS NULL OR regime_transition_prob BETWEEN 0 AND 1),
    CONSTRAINT chk_trend_strength CHECK (trend_strength_score IS NULL OR trend_strength_score BETWEEN 0 AND 1),
    CONSTRAINT chk_risk_adjustment CHECK (risk_adjustment_factor IS NULL OR risk_adjustment_factor BETWEEN 0.1 AND 5.0),
    CONSTRAINT chk_regime_duration_positive CHECK (regime_duration_days IS NULL OR regime_duration_days >= 0)
);

-- Indexes for ai_regime_analysis table
CREATE INDEX idx_regime_analysis_snapshot ON ai_regime_analysis(metrics_snapshot_id);
CREATE INDEX idx_regime_analysis_model ON ai_regime_analysis(ai_model_id);
CREATE INDEX idx_regime_analysis_time ON ai_regime_analysis(analysis_time DESC);
CREATE INDEX idx_regime_analysis_current_regime ON ai_regime_analysis(current_regime);
CREATE INDEX idx_regime_analysis_timeframe ON ai_regime_analysis(analysis_timeframe);

-- ===============================================
-- 6. AI_MODELS TABLE - AI model management and versioning  
-- ===============================================
CREATE TABLE IF NOT EXISTS ai_models (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    architecture VARCHAR(50) NOT NULL,
    model_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'inactive',

    -- 🎯 Model Configuration & Hyperparameters (Enhanced Schema)
    configuration JSONB DEFAULT '{}',
    
    -- 📊 Performance Metrics (Comprehensive Structured Schema)
    performance_metrics JSONB DEFAULT '{}',
    
    -- 🔧 Training Configuration (Enhanced Schema)
    training_features JSONB DEFAULT '{}',
    training_data_range JSONB DEFAULT '{}',
    training_data_timeframe VARCHAR(10) NOT NULL,
    target_variable VARCHAR(50) NOT NULL,
    
    -- 📋 Input/Output Schema (Structured Schema)
    input_schema JSONB DEFAULT '{}',
    output_schema JSONB DEFAULT '{}',
    
    -- 🏥 Health Monitoring (Comprehensive Structured Schema)
    health_status JSONB DEFAULT '{}',
    
    -- 📝 Model Metadata
    training_notes TEXT,
    model_file_path VARCHAR(100),
    framework VARCHAR(50),
    deployment_environment VARCHAR(20),
    
    -- ⏰ Timestamps & Activity
    last_trained TIMESTAMP WITH TIME ZONE,
    last_prediction TIMESTAMP WITH TIME ZONE,
    deployed_at TIMESTAMP WITH TIME ZONE,
    deprecated_at TIMESTAMP WITH TIME ZONE,
    
    -- 🔄 Model Lifecycle
    is_active BOOLEAN NOT NULL DEFAULT false,
    prediction_count INTEGER NOT NULL DEFAULT 0,
    model_size_mb NUMERIC(10,2),
    training_duration_minutes INTEGER,
    
    -- 🎚️ Business Constraints
    min_confidence_threshold NUMERIC(4,2) NOT NULL DEFAULT 0.5,
    max_predictions_per_hour INTEGER,
    requires_manual_approval BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 📋 Enhanced Constraints
    CONSTRAINT chk_confidence_threshold CHECK (min_confidence_threshold BETWEEN 0 AND 1),
    CONSTRAINT chk_prediction_count_positive CHECK (prediction_count >= 0),
    CONSTRAINT chk_model_size_positive CHECK (model_size_mb IS NULL OR model_size_mb > 0),
    CONSTRAINT chk_training_duration_positive CHECK (training_duration_minutes IS NULL OR training_duration_minutes > 0),
    CONSTRAINT chk_max_predictions_positive CHECK (max_predictions_per_hour IS NULL OR max_predictions_per_hour > 0)
);

-- Enhanced Indexes for ai_models Performance
CREATE UNIQUE INDEX idx_unique_active_model ON ai_models (name, model_type) WHERE is_active = true;

-- Other indexes for ai_models table
CREATE INDEX idx_ai_models_name ON ai_models(name);
CREATE INDEX idx_ai_models_type ON ai_models(model_type);
CREATE INDEX idx_ai_models_status ON ai_models(status);
CREATE INDEX idx_ai_models_active ON ai_models(is_active);
CREATE INDEX idx_ai_models_created_at ON ai_models(created_at DESC);

-- ===============================================
-- 7. MODEL_JOBS TABLE - Unified model job management (training, prediction, evaluation, etc.)
-- ===============================================
CREATE TABLE IF NOT EXISTS model_jobs (
    id BIGSERIAL PRIMARY KEY,
    model_id INTEGER NOT NULL REFERENCES ai_models(id) ON DELETE CASCADE,
    
    -- Job Classification & Control
    job_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    job_category VARCHAR(15) NOT NULL DEFAULT 'training',
    job_type VARCHAR(25) NOT NULL DEFAULT 'batch',
    job_name VARCHAR(30) NOT NULL DEFAULT 'Unnamed Job',
    
    -- Execution Tracking
    progress_pct NUMERIC(5,2) NOT NULL DEFAULT 0,
    current_phase VARCHAR(20),
    total_steps INTEGER,
    completed_steps INTEGER,
    
    -- Comprehensive Job Configuration
    job_config JSONB NOT NULL DEFAULT '{}',
    
    -- Real-Time Job Metrics & Statistics
    job_metrics JSONB DEFAULT '{}',
    
    -- Comprehensive Timing Information
    queued_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    execution_duration_sec INTEGER,
    estimated_duration_sec INTEGER,
    
    -- Job Outputs & Results
    job_outputs JSONB DEFAULT '{}',
    
    -- Scheduling & Automation
    is_scheduled BOOLEAN DEFAULT false,
    schedule_expression VARCHAR(50),
    next_scheduled_run TIMESTAMP WITH TIME ZONE,
    auto_retry_enabled BOOLEAN DEFAULT true,
    
    -- Job Management & Ownership
    created_by INTEGER REFERENCES users(id),
    assigned_to INTEGER REFERENCES users(id),
    priority VARCHAR(10) DEFAULT 'normal',
    queue_name VARCHAR(20),
    
    -- Error Handling & Retry Logic
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,
    failure_details JSONB DEFAULT '{}',
    
    -- Resource Management & Limits
    resource_allocation JSONB DEFAULT '{}',
    
    -- Job Logging & Monitoring
    execution_log TEXT,
    job_events JSONB DEFAULT '{}',
    monitoring_webhook VARCHAR(50),
    
    -- Dependencies & Relationships
    job_dependencies JSONB DEFAULT '{}',
    parent_job_id BIGINT REFERENCES model_jobs(id),
    blocks_other_jobs BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Enhanced Business Logic Constraints
    CONSTRAINT chk_jobs_progress_range CHECK (progress_pct >= 0 AND progress_pct <= 100),
    CONSTRAINT chk_jobs_retry_logic CHECK (retry_count >= 0 AND retry_count <= max_retries),
    CONSTRAINT chk_jobs_max_retries CHECK (max_retries >= 0 AND max_retries <= 20),
    CONSTRAINT chk_jobs_steps_logic CHECK (completed_steps IS NULL OR total_steps IS NULL OR completed_steps <= total_steps),
    CONSTRAINT chk_jobs_timing_logic CHECK (started_at IS NULL OR completed_at IS NULL OR started_at <= completed_at),
    CONSTRAINT chk_jobs_duration_positive CHECK (execution_duration_sec IS NULL OR execution_duration_sec >= 0),
    CONSTRAINT chk_jobs_schedule_logic CHECK (schedule_expression IS NULL OR is_scheduled = true)
);

-- Optimized Indexes for model_jobs Performance
CREATE INDEX idx_model_jobs_active ON model_jobs(job_status, priority DESC, created_at ASC) WHERE job_status IN ('pending', 'running');
CREATE INDEX idx_model_jobs_model_category ON model_jobs(model_id, job_category, job_status, created_at DESC);
CREATE INDEX idx_model_jobs_scheduled ON model_jobs(is_scheduled, next_scheduled_run ASC) WHERE is_scheduled = true;
CREATE INDEX idx_model_jobs_monitoring ON model_jobs(job_status, progress_pct, last_heartbeat DESC) WHERE job_status = 'running';
CREATE INDEX idx_model_jobs_user_jobs ON model_jobs(created_by, job_status, created_at DESC);
CREATE INDEX idx_model_jobs_queue_management ON model_jobs(queue_name, priority DESC, queued_at ASC) WHERE job_status = 'pending';
CREATE INDEX idx_model_jobs_parent_child ON model_jobs(parent_job_id, job_status) WHERE parent_job_id IS NOT NULL;

-- ===============================================
-- 8. MODEL_PERFORMANCE TABLE - Model performance evaluations
-- ===============================================
CREATE TABLE IF NOT EXISTS model_performance (
    id BIGSERIAL PRIMARY KEY,
    model_id INTEGER NOT NULL REFERENCES ai_models(id) ON DELETE CASCADE,
    source_job_id BIGINT REFERENCES model_jobs(id) ON DELETE SET NULL,
    
    -- Evaluation Context (simplified - job details via JOIN)
    evaluation_date TIMESTAMP WITH TIME ZONE NOT NULL,
    evaluation_trigger VARCHAR(30) NOT NULL,
    
    -- Core ML Performance Metrics
    accuracy NUMERIC(6,4),
    precision_score NUMERIC(6,4),
    recall NUMERIC(6,4),
    f1_score NUMERIC(6,4),
    auc_score NUMERIC(8,4),
    
    -- Trading Performance Metrics
    win_rate NUMERIC(6,4),
    profit_factor NUMERIC(8,2),
    sharpe_ratio NUMERIC(8,4),
    max_drawdown NUMERIC(6,4),
    total_return_pct NUMERIC(8,2),
    calmar_ratio NUMERIC(8,4),
    
    -- Statistical Quality Metrics
    mse NUMERIC(10,6),
    mae NUMERIC(8,4),
    r2_score NUMERIC(6,4),
    
    -- Sample Quality & Distribution
    total_samples INTEGER,
    valid_predictions INTEGER,
    confidence_mean NUMERIC(6,4),
    confidence_std NUMERIC(6,4),
    
    -- Business Performance Assessment
    meets_min_threshold BOOLEAN,
    performance_grade VARCHAR(2) CHECK (performance_grade IN ('A', 'B', 'C', 'D', 'F')),
    composite_score NUMERIC(6,4),
    evaluation_status VARCHAR(20) NOT NULL DEFAULT 'completed',
    
    -- Market Context
    market_regime VARCHAR(20),
    market_volatility NUMERIC(6,4),
    
    -- Evaluation Results & Analysis
    confusion_matrix JSONB DEFAULT '{}',
    performance_breakdown JSONB DEFAULT '{}',
    benchmark_comparison JSONB DEFAULT '{}',
    evaluation_summary TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Comprehensive Validation Constraints
    CONSTRAINT chk_perf_ml_metrics CHECK (
        accuracy IS NULL OR (accuracy >= 0 AND accuracy <= 1) AND
        precision_score IS NULL OR (precision_score >= 0 AND precision_score <= 1) AND
        recall IS NULL OR (recall >= 0 AND recall <= 1) AND
        f1_score IS NULL OR (f1_score >= 0 AND f1_score <= 1) AND
        auc_score IS NULL OR (auc_score >= 0 AND auc_score <= 1)
    ),
    CONSTRAINT chk_perf_trading_metrics CHECK (
        win_rate IS NULL OR (win_rate >= 0 AND win_rate <= 1) AND
        max_drawdown IS NULL OR (max_drawdown >= 0 AND max_drawdown <= 1) AND
        profit_factor IS NULL OR profit_factor >= 0
    ),
    CONSTRAINT chk_perf_statistical_metrics CHECK (
        r2_score IS NULL OR (r2_score >= -1 AND r2_score <= 1) AND
        mse IS NULL OR mse >= 0 AND
        mae IS NULL OR mae >= 0
    ),
    CONSTRAINT chk_perf_sample_counts CHECK (
        total_samples IS NULL OR total_samples > 0 AND
        valid_predictions IS NULL OR (valid_predictions >= 0 AND valid_predictions <= total_samples)
    ),
    CONSTRAINT chk_perf_confidence_metrics CHECK (
        confidence_mean IS NULL OR (confidence_mean >= 0 AND confidence_mean <= 1) AND
        confidence_std IS NULL OR confidence_std >= 0
    ),
    CONSTRAINT chk_perf_composite_score CHECK (composite_score IS NULL OR (composite_score >= 0 AND composite_score <= 1)),
    CONSTRAINT chk_perf_market_volatility CHECK (market_volatility IS NULL OR (market_volatility >= 0 AND market_volatility <= 1))
);

-- High-Performance Indexes for model_performance
CREATE INDEX idx_perf_model_recent ON model_performance(model_id, evaluation_date DESC);
CREATE INDEX idx_perf_grade_threshold ON model_performance(performance_grade, meets_min_threshold, composite_score DESC);
CREATE INDEX idx_perf_job_source ON model_performance(source_job_id, evaluation_date DESC) WHERE source_job_id IS NOT NULL;
CREATE INDEX idx_perf_trigger_status ON model_performance(evaluation_trigger, evaluation_status, evaluation_date DESC);

-- ===============================================
-- ADD FOREIGN KEY CONSTRAINTS FOR FORWARD REFERENCES
-- ===============================================
-- Add foreign key constraints after all tables are created
ALTER TABLE ai_regime_analysis 
ADD CONSTRAINT fk_ai_regime_analysis_model 
FOREIGN KEY (ai_model_id) REFERENCES ai_models(id) ON DELETE RESTRICT;

-- ===============================================
-- TRIGGER FUNCTIONS FOR AUTOMATIC TIMESTAMP UPDATES
-- ===============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic updated_at updates
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_assets_updated_at BEFORE UPDATE ON assets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_price_data_updated_at BEFORE UPDATE ON price_data FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_metrics_snapshot_updated_at BEFORE UPDATE ON metrics_snapshot FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ai_regime_analysis_updated_at BEFORE UPDATE ON ai_regime_analysis FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ai_models_updated_at BEFORE UPDATE ON ai_models FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_model_performance_updated_at BEFORE UPDATE ON model_performance FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_model_jobs_updated_at BEFORE UPDATE ON model_jobs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ===============================================
-- INITIAL DATA INSERTION
-- ===============================================

-- Insert initial users (Admin and Guest)
INSERT INTO users (
    email, 
    password_hash, 
    first_name, 
    last_name, 
    role, 
    is_active, 
    is_verified, 
    subscription_plan,
    language,
    timezone
) VALUES 
-- Admin User
('admin@cryptopredict.com', 
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXig/JS5TQMy', -- password: admin123
 'System', 
 'Administrator', 
 'admin', 
 true, 
 true, 
 'enterprise',
 'en',
 'UTC'),

-- Guest User  
('guest@cryptopredict.com',
 '$2b$12$8Hqw9PgF3kL5mR2nQ7vY1eX9sT4bC6dA8fG2hJ5kL7mP9qR3sT6v', -- password: guest123
 'Guest',
 'User',
 'guest',
 true,
 false,
 'free',
 'en',
 'UTC')
ON CONFLICT (email) DO NOTHING;

-- Insert initial crypto assets (essential fields only)
INSERT INTO assets (
    symbol,
    name,
    asset_type,
    quote_currency,
    external_ids
) VALUES 
-- Bitcoin (BTC)
('BTC', 'Bitcoin', 'crypto', 'USDT', '{"binance_id": "BTCUSDT", "coingecko_id": "bitcoin", "tradingview_id": "BTCUSDT"}'),

-- Ethereum (ETH)  
('ETH', 'Ethereum', 'crypto', 'USDT', '{"binance_id": "ETHUSDT", "coingecko_id": "ethereum", "tradingview_id": "ETHUSDT"}'),

-- Tether USD (USDT)
('USDT', 'Tether USD', 'stablecoin',  'USD', '{"binance_id": "USDT", "coingecko_id": "tether", "tradingview_id": "USDTUSDC"}'),

-- Bitcoin Dominance (BTC.D)
('BTC.D', 'Bitcoin Dominance', 'index', 'USD', '{"tradingview_id": "BTC.D"}'),

-- Ethereum Dominance (ETH.D)
('ETH.D', 'Ethereum Dominance', 'index', 'USD', '{"tradingview_id": "ETH.D"}')

-- Total Market Cap (TOTAL)
('TOTAL', 'Total Market Cap', 'index', 'USD (B)', '{"tradingview_id": "TOTAL"}')

ON CONFLICT (symbol) DO NOTHING;

-- ===============================================
-- COMMENTS AND DOCUMENTATION
-- ===============================================
COMMENT ON TABLE users IS 'Core user management table for authentication and user data';
COMMENT ON TABLE assets IS 'Master table for all supported cryptocurrencies and assets';
COMMENT ON COLUMN assets.timeframe_data IS 'Performance cache storing timeframe availability info. Format: {"1h": {"count": 720, "earliest": "2025-01-01T00:00:00Z", "latest": "2025-10-23T12:00:00Z"}, "1d": {...}}. Reduces aggregation_status queries from 8 to 1.';
COMMENT ON TABLE price_data IS 'Historical and real-time OHLCV price data with technical indicators';
COMMENT ON TABLE metrics_snapshot IS 'Market-wide macro analysis snapshots at different timeframes';
COMMENT ON TABLE ai_regime_analysis IS 'AI-powered market regime analysis and predictions';
COMMENT ON TABLE ai_models IS 'AI/ML model management with versioning and performance tracking';
COMMENT ON TABLE model_performance IS 'Model performance evaluation results and metrics with job traceability';
COMment ON TABLE model_jobs IS 'Unified model job management for training, prediction, evaluation, and optimization';

-- ===============================================
-- END OF SCHEMA
-- ===============================================
-- Total Tables: 8 (optimized from 9)
-- Total Indexes: 45+
-- Total Constraints: 35+
-- Purpose: Complete Layer 1 (Macro Analysis) implementation for CryptoPredict
-- Features: Unified job management, comprehensive performance tracking
-- Compatible with: PostgreSQL 12+
-- ===============================================