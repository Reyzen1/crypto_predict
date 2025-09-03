# docs\Design\17_Database_ERD_Design.md
# 🗄️ Database ERD Design - Days 15-18
## Complete Database Architecture for 4-Layer AI System

# 🗓️ **روز 17: Table Creation Scripts**

## 💾 **SQL Implementation (صبح - 4 ساعت)**

### **🔧 Complete Enhanced Tables Creation**

```sql
-- =============================================
-- CryptoPredict Phase 2 Database Schema
-- Enhanced 4-Layer AI Architecture
-- Complete database schema for cryptocurrency prediction system
-- Supporting macro analysis, sector rotation, asset selection, and micro timing
-- =============================================

-- 1. Users TABLE - Core user management and authentication
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY, -- Unique identifier for each user
    email VARCHAR(255) NOT NULL UNIQUE, -- Email address for authentication and communication
    password_hash VARCHAR(255) NOT NULL, -- Hashed password for secure authentication
    first_name VARCHAR(50), -- User's first name for personalization
    last_name VARCHAR(50), -- User's last name for personalization
    role VARCHAR(20) NOT NULL DEFAULT 'public', -- User role: 'admin' or 'public' for access control
    is_active BOOLEAN NOT NULL DEFAULT true, -- Account status for system access control
    is_verified BOOLEAN NOT NULL DEFAULT false, -- Email verification status
    is_premium BOOLEAN NOT NULL DEFAULT false, -- Premium subscription status for future features
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- Account creation timestamp
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- Last profile update timestamp
    last_login TIMESTAMP WITH TIME ZONE, -- Last login time for activity tracking
    login_count INTEGER DEFAULT 0, -- Total login count for engagement metrics
    preferences JSONB DEFAULT '{}', -- User preferences and settings stored as JSON
    timezone VARCHAR(50) DEFAULT 'UTC', -- User's timezone for localized timestamps
    language VARCHAR(10) DEFAULT 'en' -- User's preferred language (en, fa, etc.)
);

-- Indexes for users table
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_admin_overview ON users(id, email, role, is_active, created_at, last_login);

-- 2. Cryptocurrency Data TABLE - Master table for all supported cryptocurrencies
CREATE TABLE IF NOT EXISTS cryptocurrencies (
    id SERIAL PRIMARY KEY, -- Unique identifier for each cryptocurrency
    symbol VARCHAR(10) NOT NULL UNIQUE, -- Trading symbol (BTC, ETH, etc.)
    name VARCHAR(100) NOT NULL, -- Full cryptocurrency name
    coingecko_id VARCHAR(50) UNIQUE, -- CoinGecko API identifier for data fetching
    market_cap_rank INTEGER, -- Current market capitalization ranking
    current_price NUMERIC(20, 8), -- Current price in USD with high precision
    market_cap NUMERIC(30, 2), -- Total market capitalization
    total_volume NUMERIC(30, 2), -- 24-hour trading volume
    circulating_supply NUMERIC(30, 2), -- Current circulating token supply
    total_supply NUMERIC(30, 2), -- Total token supply (minted)
    max_supply NUMERIC(30, 2), -- Maximum possible token supply
    price_change_percentage_24h NUMERIC(10, 4), -- 24-hour price change percentage
    price_change_percentage_7d NUMERIC(10, 4), -- 7-day price change percentage
    price_change_percentage_30d NUMERIC(10, 4), -- 30-day price change percentage
    description TEXT, -- Detailed cryptocurrency description
    website_url VARCHAR(255), -- Official project website
    blockchain_site VARCHAR(255), -- Blockchain explorer URL
    whitepaper_url VARCHAR(255), -- Technical whitepaper URL
    twitter_username VARCHAR(100), -- Official Twitter handle
    telegram_channel VARCHAR(100), -- Official Telegram channel
    subreddit_url VARCHAR(255), -- Official Reddit community
    github_repos JSONB, -- Array of GitHub repository URLs
    sectors JSONB, -- Array of sectors this crypto belongs to (DeFi, Gaming, etc.)
    contract_address VARCHAR(100), -- Smart contract address for tokens
    decimals INTEGER, -- Token decimal places for precision calculations
    is_active BOOLEAN NOT NULL DEFAULT true, -- Whether crypto is active in our system
    is_supported BOOLEAN NOT NULL DEFAULT true, -- Whether we provide analysis for this asset
    tier INTEGER DEFAULT 2, -- Priority tier: 1=priority analysis, 2=standard, 3=basic
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- Record creation timestamp
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- Last data update timestamp
    last_data_update TIMESTAMP WITH TIME ZONE -- Last price/market data refresh
);

-- Indexes for cryptocurrencies table
CREATE INDEX idx_cryptocurrencies_symbol ON cryptocurrencies(symbol);
CREATE INDEX idx_cryptocurrencies_coingecko_id ON cryptocurrencies(coingecko_id);
CREATE INDEX idx_cryptocurrencies_market_cap_rank ON cryptocurrencies(market_cap_rank);
CREATE INDEX idx_cryptocurrencies_active ON cryptocurrencies(is_active, is_supported);
CREATE INDEX idx_cryptocurrencies_tier ON cryptocurrencies(tier, market_cap_rank);

-- 3. PRICE DATA TABLE - Historical and real-time price data for all cryptocurrencies
CREATE TABLE IF NOT EXISTS price_data (
    id SERIAL PRIMARY KEY, -- Unique identifier for each price data point
    crypto_id INTEGER NOT NULL REFERENCES cryptocurrencies(id) ON DELETE CASCADE, -- Link to cryptocurrency
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL, -- Timestamp for this price data point
    open_price NUMERIC(20, 8) NOT NULL, -- Opening price for the time period
    high_price NUMERIC(20, 8) NOT NULL, -- Highest price during the time period
    low_price NUMERIC(20, 8) NOT NULL, -- Lowest price during the time period
    close_price NUMERIC(20, 8) NOT NULL, -- Closing price for the time period
    volume NUMERIC(30, 8), -- Trading volume during the time period
    market_cap NUMERIC(30, 2), -- Market capitalization at this timestamp
    technical_indicators JSONB DEFAULT '{}', -- Pre-calculated technical indicators (RSI, MACD, etc.)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- Record creation timestamp
    
    -- Constraints for data integrity
    CONSTRAINT unique_crypto_timestamp UNIQUE(crypto_id, timestamp) -- Prevent duplicate price data
);

-- Indexes for price_data table
CREATE INDEX idx_price_data_crypto_id ON price_data(crypto_id);
CREATE INDEX idx_price_data_timestamp ON price_data(timestamp DESC);
CREATE INDEX idx_price_data_crypto_timestamp ON price_data(crypto_id, timestamp DESC);

-- 4. Create Layer 1 Tables (Macro Market Analysis) - Overall market regime and sentiment analysis

-- Market Regime Analysis - Tracks bull/bear/sideways market conditions
CREATE TABLE IF NOT EXISTS market_regime_analysis (
    id SERIAL PRIMARY KEY, -- Unique identifier for each regime analysis
    regime VARCHAR(10) NOT NULL CHECK (regime IN ('bull', 'bear', 'sideways')), -- Current market regime
    confidence_score NUMERIC(5,4) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1), -- AI confidence (0-1)
    indicators JSONB DEFAULT '{}', -- Market indicators used for regime detection
    analysis_data JSONB DEFAULT '{}', -- Detailed analysis data and supporting metrics
    analysis_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- When this analysis was performed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- Record creation timestamp
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Last update timestamp
);

-- Indexes for market_regime_analysis table - Performance optimization for time-based queries
CREATE INDEX idx_market_regime_time ON market_regime_analysis(analysis_time DESC);

-- Market Sentiment Data - Aggregated sentiment from multiple sources (Fear & Greed, social media)
CREATE TABLE IF NOT EXISTS market_sentiment_data (
    id SERIAL PRIMARY KEY, -- Unique identifier for each sentiment snapshot
    fear_greed_index NUMERIC(5,2), -- Fear & Greed Index value (0-100)
    social_sentiment NUMERIC(5,4), -- Aggregated social media sentiment score
    sentiment_sources JSONB DEFAULT '{}', -- Data from various sentiment sources (Twitter, Reddit, etc.)
    analysis_metrics JSONB DEFAULT '{}', -- Detailed sentiment analysis metrics and breakdowns
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- Timestamp for this sentiment snapshot
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Record creation timestamp
);

-- Indexes for market_sentiment_data table - Performance optimization for time-based queries
CREATE INDEX idx_sentiment_timestamp ON market_sentiment_data(timestamp DESC);

-- Dominance Data - Bitcoin, Ethereum, and Altcoin market dominance tracking
CREATE TABLE IF NOT EXISTS dominance_data (
    id SERIAL PRIMARY KEY, -- Unique identifier for each dominance snapshot
    btc_dominance NUMERIC(5,2) NOT NULL, -- Bitcoin market dominance percentage
    eth_dominance NUMERIC(5,2) NOT NULL, -- Ethereum market dominance percentage
    alt_dominance NUMERIC(5,2) NOT NULL, -- Altcoin market dominance percentage
    trend_analysis JSONB DEFAULT '{}', -- Dominance trend analysis and pattern recognition
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- Timestamp for this dominance snapshot
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Record creation timestamp
);

-- Indexes for dominance_data table - Performance optimization for time-based queries
CREATE INDEX idx_dominance_timestamp ON dominance_data(timestamp DESC);

-- Macro Indicators - External market indicators that affect crypto markets
CREATE TABLE IF NOT EXISTS macro_indicators (
    id SERIAL PRIMARY KEY, -- Unique identifier for each macro indicator record
    indicator_name VARCHAR(50) NOT NULL, -- Name of the macro indicator (VIX, DXY, SPY, etc.)
    value NUMERIC(15,8) NOT NULL, -- Current value of the indicator
    timeframe VARCHAR(20) NOT NULL, -- Timeframe for this indicator (1h, 4h, 1d, 1w, etc.)
    metadata JSONB DEFAULT '{}', -- Additional metadata about the indicator source and calculation
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- Timestamp for this indicator value
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Record creation timestamp
);

-- Indexes for macro_indicators table - Performance optimization for indicator queries
CREATE INDEX idx_macro_indicators_name ON macro_indicators(indicator_name);
CREATE INDEX idx_macro_indicators_timestamp ON macro_indicators(timestamp DESC);

-- 5. Create Layer 2 Tables (Sector Analysis) - Cryptocurrency sector classification and performance tracking

-- Crypto Sectors - Master table for cryptocurrency sector definitions
CREATE TABLE IF NOT EXISTS crypto_sectors (
    id SERIAL PRIMARY KEY, -- Unique identifier for each crypto sector
    name VARCHAR(50) NOT NULL UNIQUE, -- Unique sector name (DeFi, Gaming, Infrastructure, etc.)
    description TEXT, -- Detailed description of the sector and its characteristics
    characteristics JSONB DEFAULT '{}', -- Sector characteristics and defining features
    is_active BOOLEAN DEFAULT true, -- Whether this sector is actively tracked and analyzed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- Record creation timestamp
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Last update timestamp
);

-- Indexes for crypto_sectors table - Performance optimization for sector queries
CREATE INDEX idx_crypto_sectors_name ON crypto_sectors(name);
CREATE INDEX idx_crypto_sectors_active ON crypto_sectors(is_active);

-- Sector Performance - Performance metrics and analysis for each cryptocurrency sector
CREATE TABLE IF NOT EXISTS sector_performance (
    id SERIAL PRIMARY KEY, -- Unique identifier for each sector performance record
    sector_id INTEGER NOT NULL REFERENCES crypto_sectors(id) ON DELETE CASCADE, -- Link to crypto sector
    performance_24h NUMERIC(8,4), -- 24-hour sector performance percentage
    performance_7d NUMERIC(8,4), -- 7-day sector performance percentage
    performance_30d NUMERIC(8,4), -- 30-day sector performance percentage
    volume_change NUMERIC(8,4), -- Volume change percentage for the sector
    market_cap_change NUMERIC(8,4), -- Market cap change percentage for the sector
    performance_metrics JSONB DEFAULT '{}', -- Detailed performance metrics and sector-specific calculations
    analysis_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- When this performance analysis was calculated
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Record creation timestamp
);
-- Indexes for sector_performance table - Performance optimization for sector and time-based queries
CREATE INDEX idx_sector_perf_sector_time ON sector_performance(sector_id, analysis_time DESC);

-- Sector Rotation Analysis - Identifies capital rotation between cryptocurrency sectors
CREATE TABLE IF NOT EXISTS sector_rotation_analysis (
    id SERIAL PRIMARY KEY, -- Unique identifier for each sector rotation analysis
    from_sector_id INTEGER REFERENCES crypto_sectors(id) ON DELETE CASCADE, -- Sector where capital is rotating from
    to_sector_id INTEGER REFERENCES crypto_sectors(id) ON DELETE CASCADE, -- Sector where capital is rotating to
    rotation_strength NUMERIC(5,4) CHECK (rotation_strength >= 0 AND rotation_strength <= 1), -- Strength of rotation signal (0-1)
    confidence_score NUMERIC(5,4) CHECK (confidence_score >= 0 AND confidence_score <= 1), -- AI confidence in rotation analysis (0-1)
    rotation_indicators JSONB DEFAULT '{}', -- Indicators and metrics supporting this rotation analysis
    analysis_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- When this rotation analysis was performed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Record creation timestamp
);

-- Indexes for sector_rotation_analysis table - Performance optimization for time-based queries
CREATE INDEX idx_sector_rotation_time ON sector_rotation_analysis(analysis_time DESC);

-- Crypto Sector Mapping - Maps cryptocurrencies to their respective sectors
CREATE TABLE IF NOT EXISTS crypto_sector_mapping (
    id SERIAL PRIMARY KEY, -- Unique identifier for each crypto-sector mapping
    crypto_id INTEGER NOT NULL REFERENCES cryptocurrencies(id) ON DELETE CASCADE, -- Link to cryptocurrency
    sector_id INTEGER NOT NULL REFERENCES crypto_sectors(id) ON DELETE CASCADE, -- Link to crypto sector
    allocation_percentage NUMERIC(5,2) DEFAULT 100 CHECK (allocation_percentage > 0 AND allocation_percentage <= 100), -- Percentage allocation of crypto to this sector
    is_primary_sector BOOLEAN DEFAULT true, -- Whether this is the primary sector classification for the crypto
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- Record creation timestamp
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- Last update timestamp
    UNIQUE(crypto_id, sector_id) -- Prevent duplicate mappings of same crypto to same sector
);

-- Indexes for crypto_sector_mapping table - Performance optimization for sector and crypto queries
CREATE INDEX idx_crypto_sector_crypto ON crypto_sector_mapping(crypto_id);
CREATE INDEX idx_crypto_sector_sector ON crypto_sector_mapping(sector_id);

-- 6. Create Layer 3 Tables (Asset Selection) - User watchlists and AI-driven asset selection

-- ===== WATCHLISTS TABLE (Enhanced) - User and system watchlists for cryptocurrency tracking =====
CREATE TABLE watchlists (
    id SERIAL PRIMARY KEY, -- Unique identifier for each watchlist
    name VARCHAR(100) NOT NULL, -- Watchlist name for user identification
    description TEXT, -- Detailed description of watchlist purpose and strategy
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, -- Link to user (null for system default watchlists)
    type VARCHAR(20) NOT NULL DEFAULT 'personal', -- Type: 'default' (system) or 'personal' (user-created)
    is_active BOOLEAN NOT NULL DEFAULT true, -- Whether this watchlist is currently active
    is_public BOOLEAN NOT NULL DEFAULT false, -- Whether this watchlist can be shared (future feature)
    max_assets INTEGER DEFAULT 25, -- Maximum number of assets allowed in this watchlist
    sort_order INTEGER DEFAULT 0, -- Order for displaying multiple watchlists to users
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- Watchlist creation timestamp
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- Last modification timestamp
    
    -- Constraints for data integrity
    CONSTRAINT check_watchlist_type CHECK (type IN ('default', 'personal')), -- Validate watchlist type
    CONSTRAINT check_default_watchlist_user CHECK ( -- Ensure default watchlists have no user, personal watchlists have user
        (type = 'default' AND user_id IS NULL) OR 
        (type = 'personal' AND user_id IS NOT NULL)
    )
);

-- Indexes for watchlists table - Performance optimization for user and type-based queries
CREATE INDEX idx_watchlists_user_id ON watchlists(user_id);
CREATE INDEX idx_watchlists_type ON watchlists(type);
CREATE INDEX idx_watchlists_active ON watchlists(is_active);
CREATE INDEX idx_watchlist_user ON watchlists(user_id, type);
CREATE INDEX idx_watchlists_active_updated ON watchlists(id, updated_at) WHERE is_active = true;
CREATE UNIQUE INDEX idx_watchlists_default ON watchlists(type) WHERE type = 'default'; -- Ensure only one default watchlist

-- ===== WATCHLIST ASSETS TABLE (Enhanced) - Individual assets within watchlists =====
CREATE TABLE watchlist_assets (
    id SERIAL PRIMARY KEY, -- Unique identifier for each watchlist asset entry
    watchlist_id INTEGER NOT NULL REFERENCES watchlists(id) ON DELETE CASCADE, -- Link to parent watchlist
    crypto_id INTEGER NOT NULL REFERENCES cryptocurrencies(id) ON DELETE CASCADE, -- Link to cryptocurrency
    position INTEGER NOT NULL DEFAULT 1, -- Position/rank within the watchlist for ordering display
    weight DECIMAL(5,4) DEFAULT 0.0, -- Portfolio weight allocation for this asset (0-1)
    target_allocation DECIMAL(5,4), -- Target allocation percentage for portfolio management
    notes TEXT, -- User or admin notes about this asset inclusion rationale
    is_active BOOLEAN NOT NULL DEFAULT true, -- Whether this asset is currently active in the watchlist
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- When this asset was added to the watchlist
    added_by INTEGER REFERENCES users(id), -- User who added this asset (admin or regular user)
    last_modified_by INTEGER REFERENCES users(id), -- User who last modified this asset entry
    
    -- Constraints for data integrity
    UNIQUE(watchlist_id, crypto_id), -- Prevent duplicate assets in same watchlist
    UNIQUE(watchlist_id, position) -- Prevent duplicate positions within same watchlist
);
-- Indexes for watchlist_assets table - Performance optimization for watchlist and asset queries
CREATE INDEX idx_watchlist_assets_watchlist ON watchlist_assets(watchlist_id);
CREATE INDEX idx_watchlist_assets_crypto ON watchlist_assets(crypto_id);
CREATE INDEX idx_watchlist_assets_position ON watchlist_assets(watchlist_id, position);
CREATE INDEX idx_watchlist_assets_active ON watchlist_assets(is_active);
CREATE INDEX idx_watchlist_assets_composite ON watchlist_assets(watchlist_id, is_active, position);

-- ===== AI SUGGESTIONS TABLE (Enhanced) - AI-generated suggestions for watchlist optimization =====
CREATE TABLE ai_suggestions (
    id SERIAL PRIMARY KEY, -- Unique identifier for each AI suggestion
    watchlist_id INTEGER NOT NULL REFERENCES watchlists(id) ON DELETE CASCADE, -- Watchlist this suggestion applies to
    crypto_id INTEGER NOT NULL REFERENCES cryptocurrencies(id), -- Cryptocurrency being suggested
    suggestion_type VARCHAR(50) NOT NULL, -- Type of suggestion: 'add', 'remove', 'rebalance', 'tier_change'
    ai_layer INTEGER NOT NULL, -- Which AI layer generated this suggestion (1-4)
    confidence_score DECIMAL(5,4) NOT NULL, -- AI confidence in this suggestion (0.0000 to 1.0000)
    reasoning JSONB NOT NULL, -- Structured AI reasoning and explanation for the suggestion
    context_data JSONB, -- Market context data and conditions used for the suggestion
    target_position INTEGER, -- Suggested position/rank in the watchlist
    target_weight DECIMAL(5,4), -- Suggested portfolio weight allocation
    expected_return DECIMAL(8,4), -- Expected return percentage from implementing this suggestion
    risk_score DECIMAL(5,4), -- Risk assessment score for this suggestion (0-1)
    
    -- Status tracking for suggestion lifecycle
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- Current status: 'pending', 'approved', 'rejected', 'implemented'
    reviewed_by INTEGER REFERENCES users(id), -- Admin user who reviewed this suggestion
    reviewed_at TIMESTAMP WITH TIME ZONE, -- When the suggestion was reviewed by admin
    implemented_at TIMESTAMP WITH TIME ZONE, -- When the suggestion was implemented
    
    -- Performance tracking for AI improvement
    actual_return DECIMAL(8,4), -- Actual return achieved after implementation
    success_score DECIMAL(5,4), -- Success rating of the suggestion (0-1)
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- Suggestion creation timestamp
    expires_at TIMESTAMP WITH TIME ZONE, -- When this suggestion expires if not acted upon
    
    -- Constraints for data integrity
    CONSTRAINT check_suggestion_type CHECK (suggestion_type IN ('add', 'remove', 'rebalance', 'tier_change')),
    CONSTRAINT check_status CHECK (status IN ('pending', 'approved', 'rejected', 'implemented', 'expired')),
    CONSTRAINT check_ai_layer CHECK (ai_layer BETWEEN 1 AND 4) -- Validate AI layer is within expected range
);

-- Indexes for ai_suggestions table - Performance optimization for suggestion queries and analytics
CREATE INDEX idx_ai_suggestions_watchlist_id ON ai_suggestions(watchlist_id);
CREATE INDEX idx_ai_suggestions_crypto_id ON ai_suggestions(crypto_id);
CREATE INDEX idx_ai_suggestions_status ON ai_suggestions(status);
CREATE INDEX idx_ai_suggestions_layer ON ai_suggestions(ai_layer);
CREATE INDEX idx_ai_suggestions_confidence ON ai_suggestions(confidence_score DESC);
CREATE INDEX idx_ai_suggestions_created_at ON ai_suggestions(created_at DESC);
CREATE INDEX idx_ai_suggestions_status_created ON ai_suggestions(status, created_at DESC);
CREATE INDEX idx_ai_suggestions_crypto ON ai_suggestions(crypto_id);
CREATE INDEX idx_ai_suggestions_composite ON ai_suggestions(status, ai_layer, confidence_score DESC);

-- 7. Create Layer 4 Tables (Micro Timing) - Precise timing signals for trade execution

-- Function to set default expiry time for trading signals (7 days from creation)
CREATE OR REPLACE FUNCTION default_signal_expiry() 
RETURNS TIMESTAMP WITH TIME ZONE AS $$
BEGIN
    RETURN NOW() + INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- Trading Signals - AI-generated trading signals with entry, target, and stop-loss levels
CREATE TABLE IF NOT EXISTS trading_signals (
    id SERIAL PRIMARY KEY, -- Unique identifier for each trading signal
    crypto_id INTEGER NOT NULL REFERENCES cryptocurrencies(id) ON DELETE CASCADE, -- Cryptocurrency this signal applies to
    signal_type VARCHAR(10) NOT NULL CHECK (signal_type IN ('long', 'short')), -- Type of position: long or short
    entry_price NUMERIC(20,8) NOT NULL, -- Recommended entry price for the trade
    target_price NUMERIC(20,8) NOT NULL, -- Target price for profit taking
    stop_loss NUMERIC(20,8) NOT NULL, -- Stop loss price for risk management
    confidence_score NUMERIC(5,4) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1), -- AI confidence (0-1)
    risk_level VARCHAR(10) NOT NULL CHECK (risk_level IN ('low', 'medium', 'high', 'extreme')), -- Risk level assessment
    risk_reward_ratio NUMERIC(6,2) CHECK (risk_reward_ratio > 0), -- Risk to reward ratio for this trade
    time_horizon_hours INTEGER DEFAULT 24, -- Expected time horizon for this signal in hours
    ai_analysis JSONB DEFAULT '{}', -- Detailed AI analysis and reasoning supporting this signal
    market_context JSONB DEFAULT '{}', -- Market context and conditions when signal was generated
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'executed', 'expired', 'cancelled')), -- Current signal status
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- When this signal was generated
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT default_signal_expiry(), -- When this signal expires
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Last update timestamp
);

-- Indexes for trading_signals table - Performance optimization for signal queries and status tracking
CREATE INDEX idx_trading_signals_status ON trading_signals(crypto_id, status, generated_at DESC);
CREATE INDEX idx_trading_signals_generated ON trading_signals(generated_at DESC);

-- Signal Executions - Tracks user execution of trading signals for performance analysis
CREATE TABLE IF NOT EXISTS signal_executions (
    id SERIAL PRIMARY KEY, -- Unique identifier for each signal execution
    signal_id INTEGER NOT NULL REFERENCES trading_signals(id) ON DELETE CASCADE, -- Link to the original trading signal
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- User who executed this signal
    execution_price NUMERIC(20,8), -- Actual price at which the signal was executed
    position_size NUMERIC(30,8), -- Size of the position taken by the user
    portfolio_percentage NUMERIC(5,2), -- Percentage of user's portfolio allocated to this trade
    execution_type VARCHAR(20) DEFAULT 'manual' CHECK (execution_type IN ('manual', 'automatic')), -- How signal was executed
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'filled', 'partially_filled', 'cancelled')), -- Execution status
    execution_details JSONB DEFAULT '{}', -- Detailed execution information and metadata
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- When the signal was executed
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Last update timestamp
);
-- Indexes for signal_executions table - Performance optimization for user and signal tracking
CREATE INDEX idx_signal_executions_user ON signal_executions(user_id, executed_at DESC);
CREATE INDEX idx_signal_executions_signal ON signal_executions(signal_id);

-- Risk Management - User-specific risk management settings and current exposure tracking
CREATE TABLE IF NOT EXISTS risk_management (
    id SERIAL PRIMARY KEY, -- Unique identifier for each risk management profile
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE, -- User these risk settings belong to (one per user)
    max_position_size NUMERIC(30,8) DEFAULT 1000, -- Maximum position size allowed per trade
    max_portfolio_risk NUMERIC(5,4) DEFAULT 0.02 CHECK (max_portfolio_risk >= 0 AND max_portfolio_risk <= 1), -- Maximum portfolio risk percentage (0-1)
    risk_rules JSONB DEFAULT '{}', -- Custom risk rules and parameters defined by user or system
    current_exposure JSONB DEFAULT '{}', -- Current portfolio exposure and open positions
    risk_metrics JSONB DEFAULT '{}', -- Calculated risk metrics and real-time assessments
    last_calculated TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- When risk metrics were last calculated
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Last update timestamp
);

-- Indexes for risk_management table - Performance optimization for user risk queries
CREATE INDEX idx_risk_management_user ON risk_management(user_id);

-- 8. Predictions - Unified prediction tracking for all AI layers with comprehensive performance metrics
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY, -- Unique identifier for each prediction
    crypto_id INTEGER NOT NULL REFERENCES cryptocurrencies(id) ON DELETE CASCADE, -- Cryptocurrency being predicted
    watchlist_id INTEGER REFERENCES watchlists(id) ON DELETE SET NULL, -- Watchlist context for this prediction
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL, -- User receiving this prediction (null for system-wide)
    model_name VARCHAR(50) NOT NULL, -- Name of the AI model that generated this prediction
    model_version VARCHAR(20) NOT NULL, -- Version of the AI model used
    layer_source INTEGER DEFAULT 3, -- Which AI layer generated this prediction (1-4)
    prediction_type VARCHAR(20) DEFAULT 'price', -- Type of prediction: 'price', 'event', 'trend', etc.
    predicted_price NUMERIC(20, 8) NOT NULL, -- Predicted price value
    predicted_value JSONB DEFAULT '{}', -- Non-price predictions in structured format
    confidence_score NUMERIC(5, 4) NOT NULL, -- Model confidence in this prediction (0-1)
    prediction_horizon INTEGER NOT NULL, -- Prediction time horizon in hours
    target_datetime TIMESTAMP WITH TIME ZONE NOT NULL, -- Target date/time for this prediction
    features_used JSONB, -- Input features used by the model for transparency
    model_parameters JSONB, -- Model parameters and configuration used
    input_price NUMERIC(20, 8) NOT NULL, -- Input price when prediction was made
    input_features JSONB, -- Input feature values at prediction time
    context_data JSONB, -- Market context and conditions at prediction time
    
    -- Results tracking for model evaluation and improvement
    actual_price NUMERIC(20, 8), -- Actual price at target datetime (for evaluation)
    accuracy_percentage NUMERIC(5, 2), -- Prediction accuracy percentage
    absolute_error NUMERIC(20, 8), -- Absolute error between predicted and actual
    squared_error NUMERIC(30, 8), -- Squared error for statistical analysis
    is_realized BOOLEAN NOT NULL DEFAULT false, -- Whether the prediction timeframe has passed
    is_accurate BOOLEAN, -- Whether prediction met accuracy threshold
    accuracy_threshold NUMERIC(5, 2) DEFAULT 5.0, -- Threshold percentage for considering prediction accurate
    
    -- Metadata for model analysis and debugging
    training_data_end TIMESTAMP WITH TIME ZONE, -- End date of training data used
    market_conditions VARCHAR(20), -- Market conditions during prediction (bull/bear/sideways)
    volatility_level VARCHAR(10), -- Volatility level: low, medium, high
    model_training_time NUMERIC(10, 2), -- Time taken to train the model (seconds)
    prediction_time NUMERIC(10, 6), -- Time taken to generate prediction (seconds)
    notes TEXT, -- Additional notes about this prediction
    debug_info JSONB, -- Debug information for model analysis and troubleshooting
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- Prediction creation timestamp
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- Last update timestamp
    evaluated_at TIMESTAMP WITH TIME ZONE -- When prediction was evaluated for accuracy
);

-- Indexes for predictions table - Performance optimization for prediction queries and analytics
CREATE INDEX idx_predictions_crypto_layer ON predictions(crypto_id, layer_source, created_at DESC);
CREATE INDEX idx_predictions_layer_source ON predictions(layer_source, created_at DESC);
CREATE INDEX idx_predictions_context_data ON predictions USING GIN (context_data);
CREATE INDEX idx_predictions_prediction_type ON predictions(prediction_type);
CREATE INDEX idx_predictions_layer_type ON predictions(layer_source, prediction_type);
CREATE INDEX idx_predictions_crypto_type ON predictions(crypto_id, prediction_type);
CREATE INDEX idx_predictions_type_time ON predictions(prediction_type, created_at DESC);
CREATE INDEX idx_predictions_composite ON predictions(crypto_id, is_realized, created_at DESC);

-- =============================================
-- SYSTEM MANAGEMENT TABLES - Core system monitoring and AI model management
-- =============================================

-- AI Models - Registry and management of all AI models in the system
CREATE TABLE IF NOT EXISTS ai_models (
    id SERIAL PRIMARY KEY, -- Unique identifier for each AI model
    name VARCHAR(100) NOT NULL UNIQUE, -- Unique name of the AI model
    version VARCHAR(50) NOT NULL, -- Version string of the model (semantic versioning)
    model_type VARCHAR(20) NOT NULL CHECK (model_type IN ('macro', 'sector', 'asset', 'timing')), -- Which layer this model serves
    status VARCHAR(20) DEFAULT 'inactive' CHECK (status IN ('active', 'training', 'inactive', 'error')), -- Current model status
    configuration JSONB DEFAULT '{}', -- Model configuration, hyperparameters, and settings
    performance_metrics JSONB DEFAULT '{}', -- Model performance metrics, accuracy scores, and statistics
    last_trained TIMESTAMP WITH TIME ZONE, -- When the model was last trained or retrained
    last_prediction TIMESTAMP WITH TIME ZONE, -- When the model last generated a prediction
    health_status JSONB DEFAULT '{}', -- Model health indicators and operational status
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- Model creation timestamp
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Last update timestamp
);

-- Indexes for ai_models table - Performance optimization for model type and status queries
CREATE INDEX idx_ai_models_type_status ON ai_models(model_type, status);

-- System Health - Comprehensive system monitoring and health tracking
CREATE TABLE IF NOT EXISTS system_health (
    id SERIAL PRIMARY KEY, -- Unique identifier for each health check record
    check_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- When this health check was performed
    api_status JSONB DEFAULT '{}', -- Status of various API endpoints and external services
    database_status JSONB DEFAULT '{}', -- Database performance, connection status, and query metrics
    ml_models_status JSONB DEFAULT '{}', -- Status and performance of all ML models
    data_pipeline_status JSONB DEFAULT '{}', -- Status of data ingestion and processing pipelines
    overall_health_score NUMERIC(5,2) CHECK (overall_health_score >= 0 AND overall_health_score <= 100), -- Overall system health score (0-100)
    performance_metrics JSONB DEFAULT '{}', -- System performance metrics, response times, and KPIs
    error_logs JSONB DEFAULT '[]', -- Recent error logs and critical issues
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Record creation timestamp
);
-- Indexes for system_health table - Performance optimization for time-based health monitoring
CREATE INDEX idx_system_health_time ON system_health(check_time DESC);

-- User Sessions - Secure session management for authenticated users
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY, -- Unique identifier for each user session
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- User this session belongs to
    session_token VARCHAR(255) NOT NULL UNIQUE, -- Unique session token for authentication
    refresh_token VARCHAR(255), -- Token for session renewal and extended authentication
    device_info JSONB, -- Device and browser information for security tracking
    ip_address INET, -- IP address for security and location tracking
    is_active BOOLEAN NOT NULL DEFAULT true, -- Whether this session is currently active
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, -- When this session expires
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- Session creation timestamp
    last_used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Last activity timestamp for session management
);

-- Indexes for user_sessions table - Performance optimization for session management
CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_sessions_active ON user_sessions(is_active, expires_at);

-- User Activities - Comprehensive activity logging for audit trail and analytics
CREATE TABLE user_activities (
    id SERIAL PRIMARY KEY, -- Unique identifier for each activity record
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL, -- User who performed the activity (null for system activities)
    activity_type VARCHAR(50) NOT NULL, -- Type of activity: 'login', 'watchlist_update', 'ai_interaction', etc.
    entity_type VARCHAR(50), -- Type of entity being acted upon: 'watchlist', 'asset', 'suggestion', etc.
    entity_id INTEGER, -- ID of the specific entity being acted upon
    action VARCHAR(50) NOT NULL, -- Specific action performed: 'create', 'update', 'delete', 'view', etc.
    details JSONB, -- Additional activity details and context in structured format
    ip_address INET, -- IP address for security and audit trail
    user_agent TEXT, -- Browser/device user agent string for security analysis
    session_id VARCHAR(255), -- Session identifier for activity correlation
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Activity timestamp for audit and analytics
);
    details JSONB, -- Additional activity details
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for user_activities table - Performance optimization for activity tracking and audit queries
CREATE INDEX idx_activity_log_user_id ON user_activities(user_id);
CREATE INDEX idx_activity_log_type ON user_activities(activity_type);
CREATE INDEX idx_activity_log_created_at ON user_activities(created_at DESC);
CREATE INDEX idx_activity_log_entity ON user_activities(entity_type, entity_id);

-- Notifications - User notification system for alerts, signals, and system messages
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY, -- Unique identifier for each notification
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- User receiving this notification
    notification_type VARCHAR(20) NOT NULL CHECK (notification_type IN ('signal', 'alert', 'system', 'educational')), -- Type of notification
    title VARCHAR(200) NOT NULL, -- Notification title/subject line
    message TEXT NOT NULL, -- Main notification message content
    data JSONB DEFAULT '{}', -- Additional notification data and metadata
    status VARCHAR(20) DEFAULT 'unread' CHECK (status IN ('unread', 'read', 'dismissed')), -- Notification read status
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')), -- Notification priority level
    scheduled_for TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- When notification should be sent/displayed
    sent_at TIMESTAMP WITH TIME ZONE, -- When notification was actually sent
    read_at TIMESTAMP WITH TIME ZONE, -- When user read the notification
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '30 days'), -- When notification expires
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Notification creation timestamp
);

-- Indexes for notifications table - Performance optimization for user notification queries
CREATE INDEX idx_notifications_user_status ON notifications(user_id, status, scheduled_for DESC);

-- =============================================
-- TRIGGERS FOR AUTO-UPDATE TIMESTAMPS
-- =============================================

-- Function to update timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_cryptocurrencies_updated_at BEFORE UPDATE ON cryptocurrencies 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_crypto_sectors_updated_at BEFORE UPDATE ON crypto_sectors 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_market_regime_updated_at BEFORE UPDATE ON market_regime_analysis 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_watchlists_updated_at BEFORE UPDATE ON watchlists 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_watchlist_assets_updated_at BEFORE UPDATE ON watchlist_assets 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_crypto_sector_mapping_updated_at BEFORE UPDATE ON crypto_sector_mapping 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_trading_signals_updated_at BEFORE UPDATE ON trading_signals 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_signal_executions_updated_at BEFORE UPDATE ON signal_executions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_risk_management_updated_at BEFORE UPDATE ON risk_management 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_predictions_updated_at BEFORE UPDATE ON predictions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- DATA SEEDING
-- =============================================

-- Insert default crypto sectors
INSERT INTO crypto_sectors (name, description, characteristics) VALUES
('Bitcoin', 'Store of value and digital gold', '{"type": "base_layer", "maturity": "high"}'),
('Ethereum & Smart Contracts', 'Smart contract platforms', '{"type": "platform", "maturity": "high"}'),
('DeFi', 'Decentralized Finance protocols', '{"type": "application", "maturity": "medium"}'),
('Layer 1 Blockchains', 'Alternative Layer 1 blockchains', '{"type": "platform", "maturity": "medium"}'),
('Layer 2 Solutions', 'Scaling solutions', '{"type": "infrastructure", "maturity": "medium"}'),
('NFTs & Gaming', 'Non-fungible tokens and gaming', '{"type": "application", "maturity": "medium"}'),
('Infrastructure', 'Blockchain infrastructure', '{"type": "infrastructure", "maturity": "medium"}'),
('Meme Coins', 'Community-driven tokens', '{"type": "speculative", "maturity": "low"}'),
('Privacy Coins', 'Privacy-focused cryptocurrencies', '{"type": "utility", "maturity": "medium"}'),
('Stablecoins', 'Price-stable cryptocurrencies', '{"type": "utility", "maturity": "high"}')
ON CONFLICT (name) DO NOTHING;

-- Create default admin watchlist (only one allowed)
INSERT INTO watchlists (name, type, description) VALUES
('Admin Default Watchlist', 'default', 'System-wide default cryptocurrency watchlist managed by administrators')
ON CONFLICT DO NOTHING;

-- =============================================
-- VIEWS FOR COMMON QUERIES - Optimized views for frequent data access patterns
-- =============================================

-- View for active predictions with comprehensive crypto and user details
-- Provides a consolidated view of unrealized predictions with related information
CREATE OR REPLACE VIEW v_active_predictions AS
SELECT 
    p.*, -- All prediction fields
    c.symbol, -- Cryptocurrency trading symbol
    c.name as crypto_name, -- Full cryptocurrency name
    c.current_price, -- Current market price for comparison
    u.email as user_email -- User email for admin tracking
FROM predictions p
JOIN cryptocurrencies c ON p.crypto_id = c.id -- Join with crypto details
LEFT JOIN users u ON p.user_id = u.id -- Optional user details (system predictions have no user)
WHERE p.is_realized = false -- Only show active/unrealized predictions
ORDER BY p.created_at DESC; -- Most recent predictions first

-- Comprehensive watchlist summary view with asset statistics and user information
-- Aggregates watchlist data with asset counts, weights, and symbol lists for dashboard display
CREATE OR REPLACE VIEW v_watchlist_summary AS
SELECT 
    w.id, -- Watchlist unique identifier
    w.name, -- Watchlist name for display
    w.type, -- Watchlist type (default/personal)
    w.user_id, -- Owner user ID (null for default)
    u.email as user_email, -- Owner email for admin interface
    COUNT(wa.id) as asset_count, -- Total number of assets in watchlist
    w.created_at, -- Watchlist creation date
    w.updated_at, -- Last modification date
    AVG(wa.weight) as avg_asset_weight, -- Average portfolio weight of assets
    STRING_AGG(c.symbol, ', ' ORDER BY wa.position) as asset_symbols -- Comma-separated asset symbols ordered by position
FROM watchlists w
LEFT JOIN users u ON w.user_id = u.id -- Join with user details
LEFT JOIN watchlist_assets wa ON w.id = wa.watchlist_id AND wa.is_active = true -- Only active assets
LEFT JOIN cryptocurrencies c ON wa.crypto_id = c.id -- Asset details
GROUP BY w.id, w.name, w.type, w.user_id, u.email, w.created_at, w.updated_at; -- Group by watchlist

-- Active trading signals view with enhanced crypto details and calculated metrics
-- Provides actionable trading signals with risk/reward calculations for user interface
CREATE OR REPLACE VIEW v_active_signals AS
SELECT 
    ts.*, -- All trading signal fields
    c.symbol, -- Cryptocurrency trading symbol
    c.name as crypto_name, -- Full cryptocurrency name
    c.current_price, -- Current market price for comparison with signal prices
    (ts.target_price - ts.entry_price) / ts.entry_price * 100 as potential_return_pct, -- Calculated potential return percentage
    (ts.entry_price - ts.stop_loss) / ts.entry_price * 100 as max_loss_pct -- Calculated maximum loss percentage
FROM trading_signals ts
JOIN cryptocurrencies c ON ts.crypto_id = c.id -- Join with cryptocurrency details
WHERE ts.status = 'active' AND ts.expires_at > NOW() -- Only active, non-expired signals
ORDER BY ts.confidence_score DESC, ts.generated_at DESC; -- Highest confidence and most recent first

-- AI Performance Analytics View - Comprehensive AI suggestion performance tracking
-- Aggregates AI suggestion performance metrics by layer for system optimization and monitoring
CREATE VIEW v_ai_performance AS
SELECT 
    ai_layer, -- AI layer (1-4) that generated suggestions
    COUNT(*) as total_suggestions, -- Total number of suggestions generated
    COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_count, -- Number of approved suggestions
    COUNT(CASE WHEN status = 'implemented' THEN 1 END) as implemented_count, -- Number of actually implemented suggestions
    AVG(confidence_score) as avg_confidence, -- Average AI confidence score across suggestions
    AVG(CASE WHEN actual_return IS NOT NULL THEN actual_return END) as avg_actual_return, -- Average actual return from implemented suggestions
    AVG(success_score) as avg_success_score, -- Average success rating of suggestions
    COUNT(CASE WHEN success_score > 0.7 THEN 1 END) as high_success_count -- Number of highly successful suggestions (>70% success rate)
FROM ai_suggestions
WHERE created_at >= NOW() - INTERVAL '30 days' -- Last 30 days performance
GROUP BY ai_layer -- Group by AI layer for comparative analysis
ORDER BY ai_layer; -- Order by layer number
-- Admin User Overview View - Comprehensive user statistics for administrative dashboard
-- Provides detailed user metrics including activity, watchlists, and prediction accuracy for management
CREATE VIEW v_users_overview AS
SELECT 
    u.id, -- User unique identifier
    u.email, -- User email address
    u.first_name, -- User first name
    u.last_name, -- User last name
    u.role, -- User role (admin/public)
    u.is_active, -- Account active status
    u.is_premium, -- Premium subscription status
    u.created_at, -- Account creation date
    u.last_login, -- Last login timestamp
    u.login_count, -- Total login count for engagement tracking
    COUNT(w.id) as personal_watchlists_count, -- Number of personal watchlists created
    COUNT(wa.id) as total_assets_count, -- Total assets across all user watchlists
    AVG(CASE WHEN p.is_realized THEN p.accuracy_percentage END) as avg_prediction_accuracy -- Average accuracy of realized predictions
FROM users u
LEFT JOIN watchlists w ON u.id = w.user_id AND w.type = 'personal' -- Only personal watchlists
LEFT JOIN watchlist_assets wa ON w.id = wa.watchlist_id AND wa.is_active = true -- Only active assets
LEFT JOIN predictions p ON u.id = p.user_id -- User's predictions
WHERE u.role = 'public' -- Only public users (not admin users)
GROUP BY u.id, u.email, u.first_name, u.last_name, u.role, u.is_active, u.is_premium, u.created_at, u.last_login, u.login_count;

-- =============================================
-- HELPER FUNCTIONS - Utility functions for system operations and AI integration
-- =============================================

-- Function: Create Default Watchlist - Administrative function to create system-wide default watchlists
-- Creates a default watchlist accessible to all users and logs the activity
CREATE OR REPLACE FUNCTION create_default_watchlist(
    p_name VARCHAR(100), -- Name for the default watchlist
    p_description TEXT DEFAULT NULL -- Optional description
) RETURNS INTEGER AS $$
DECLARE
    watchlist_id INTEGER; -- Variable to store the created watchlist ID
BEGIN
    -- Create the default watchlist with system-wide access
    INSERT INTO watchlists (name, description, type, user_id)
    VALUES (p_name, p_description, 'default', NULL) -- NULL user_id for system default
    RETURNING id INTO watchlist_id;
    
    -- Log the administrative activity for audit trail
    INSERT INTO user_activities (activity_type, entity_type, entity_id, action, details)
    VALUES ('admin_action', 'watchlist', watchlist_id, 'create', 
            jsonb_build_object('type', 'default', 'name', p_name));
    
    RETURN watchlist_id; -- Return the ID of the created watchlist
END;
$$ LANGUAGE plpgsql;

-- Function: Bulk Update Watchlist Assets - Efficient bulk operations for watchlist management
-- Allows administrators to update multiple watchlist assets in a single transaction
CREATE OR REPLACE FUNCTION bulk_update_watchlist_assets(
    p_watchlist_id INTEGER, -- Target watchlist ID
    p_asset_updates JSONB, -- Array of asset updates: {crypto_id, position, weight}
    p_admin_user_id INTEGER -- Admin user performing the operation
) RETURNS VOID AS $$
DECLARE
    asset_record RECORD; -- Variable to iterate through asset updates
BEGIN
    -- Process each asset update in the provided JSON array
    FOR asset_record IN 
        SELECT 
            (value->>'crypto_id')::INTEGER as crypto_id, -- Extract crypto ID
            (value->>'position')::INTEGER as position, -- Extract position
            (value->>'weight')::DECIMAL as weight -- Extract weight
        FROM jsonb_array_elements(p_asset_updates)
    LOOP
        -- Update existing asset or insert new one (upsert operation)
        INSERT INTO watchlist_assets (watchlist_id, crypto_id, position, weight, last_modified_by)
        VALUES (p_watchlist_id, asset_record.crypto_id, asset_record.position, asset_record.weight, p_admin_user_id)
        ON CONFLICT (watchlist_id, crypto_id) -- Handle existing asset
        DO UPDATE SET 
            position = EXCLUDED.position, -- Update position
            weight = EXCLUDED.weight, -- Update weight
            last_modified_by = EXCLUDED.last_modified_by; -- Track who modified
    END LOOP;
    
    -- Update parent watchlist timestamp to reflect changes
    UPDATE watchlists SET updated_at = NOW() WHERE id = p_watchlist_id;
    
    -- Log the bulk update operation for audit trail
    INSERT INTO user_activities (user_id, activity_type, entity_type, entity_id, action, details)
    VALUES (p_admin_user_id, 'admin_action', 'watchlist', p_watchlist_id, 'bulk_update',
            jsonb_build_object('asset_count', jsonb_array_length(p_asset_updates)));
END;
$$ LANGUAGE plpgsql;

-- Function: Get User AI Context - Retrieves user watchlist context for AI analysis
-- Provides comprehensive user context for AI layers to make personalized suggestions
CREATE OR REPLACE FUNCTION get_user_ai_context(p_user_id INTEGER)
RETURNS TABLE(
    watchlist_id INTEGER, -- Watchlist ID for context
    watchlist_type VARCHAR(20), -- Type of watchlist (personal/default)
    asset_count INTEGER, -- Number of assets in watchlist
    assets JSONB -- Structured asset data for AI processing
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        w.id as watchlist_id, -- Watchlist identifier
        w.type as watchlist_type, -- Watchlist type
        COUNT(wa.id)::INTEGER as asset_count, -- Count of active assets
        jsonb_agg(
            jsonb_build_object(
                'crypto_id', wa.crypto_id, -- Cryptocurrency ID
                'symbol', c.symbol, -- Trading symbol
                'position', wa.position, -- Position in watchlist
                'weight', wa.weight -- Portfolio weight
            ) ORDER BY wa.position -- Ordered by position
        ) as assets
    FROM watchlists w
    LEFT JOIN watchlist_assets wa ON w.id = wa.watchlist_id AND wa.is_active = true -- Only active assets
    LEFT JOIN cryptocurrencies c ON wa.crypto_id = c.id -- Asset details
    WHERE 
        -- Get user's personal watchlist or default if no personal watchlist exists
        (w.user_id = p_user_id AND w.type = 'personal') OR
        (w.type = 'default' AND NOT EXISTS (
            SELECT 1 FROM watchlists WHERE user_id = p_user_id AND type = 'personal'
        ))
    GROUP BY w.id, w.type; -- Group by watchlist
END;
$$ LANGUAGE plpgsql;
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        w.id as watchlist_id,
        w.type as watchlist_type,
        COUNT(wa.id)::INTEGER as asset_count,
        jsonb_agg(
            jsonb_build_object(
                'crypto_id', wa.crypto_id,
                'symbol', c.symbol,
                'position', wa.position,
                'weight', wa.weight
            ) ORDER BY wa.position
        ) as assets
    FROM watchlists w
    LEFT JOIN watchlist_assets wa ON w.id = wa.watchlist_id AND wa.is_active = true
    LEFT JOIN cryptocurrencies c ON wa.crypto_id = c.id
    WHERE 
        (w.user_id = p_user_id AND w.type = 'personal') OR
        (w.type = 'default' AND NOT EXISTS (
            SELECT 1 FROM watchlists WHERE user_id = p_user_id AND type = 'personal'
        ))
    GROUP BY w.id, w.type;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- PERFORMANCE OPTIMIZATION & ARCHIVAL SYSTEM
-- Data lifecycle management for maintaining optimal database performance
-- =============================================

-- Archive table for historical user activity logs (maintains audit trail while keeping main table lean)
CREATE TABLE user_activities_archive (
    LIKE user_activities INCLUDING ALL -- Clone structure including indexes and constraints
);

-- Archive table for historical AI suggestions (preserves learning data while optimizing queries)
CREATE TABLE ai_suggestions_archive (
    LIKE ai_suggestions INCLUDING ALL -- Clone structure including indexes and constraints
);

-- Function: Archive Old Data - Automated data lifecycle management
-- Moves old data to archive tables to maintain optimal performance in production tables
CREATE OR REPLACE FUNCTION archive_old_data() RETURNS VOID AS $$
BEGIN
    -- Archive activity logs older than 6 months to maintain audit trail with performance
    INSERT INTO user_activities_archive 
    SELECT * FROM user_activities 
    WHERE created_at < NOW() - INTERVAL '6 months';
    
    -- Remove archived activity logs from main table
    DELETE FROM user_activities 
    WHERE created_at < NOW() - INTERVAL '6 months';
    
    -- Archive implemented AI suggestions older than 3 months (keep recent for learning)
    INSERT INTO ai_suggestions_archive
    SELECT * FROM ai_suggestions
    WHERE status = 'implemented' AND implemented_at < NOW() - INTERVAL '3 months';
    
    -- Remove archived AI suggestions from main table
    DELETE FROM ai_suggestions
    WHERE status = 'implemented' AND implemented_at < NOW() - INTERVAL '3 months';
END;
$$ LANGUAGE plpgsql;
```

---
