-- Copilot Space: Comprehensive Database Schema for Crypto AI Analysis Platform
-- Each table and field is commented in English for clarity.

-- 1. Users and Management
CREATE TABLE users (
    id SERIAL PRIMARY KEY, -- Unique user identifier
    username VARCHAR(30) UNIQUE NOT NULL, -- Username for login
    email VARCHAR(100) UNIQUE NOT NULL, -- User's email address
    password_hash VARCHAR(128) NOT NULL, -- Hashed password for security
    is_admin BOOLEAN DEFAULT false, -- Admin flag
    status VARCHAR(20) DEFAULT 'active', -- User status (active, suspended, etc.)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- Registration date
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Last profile update
);

-- 2. Cryptocurrencies
CREATE TABLE cryptocurrencies (
    id SERIAL PRIMARY KEY, -- Unique crypto identifier
    symbol VARCHAR(20) UNIQUE NOT NULL, -- Ticker symbol (e.g., BTC)
    name VARCHAR(50) NOT NULL, -- Full name (e.g., Bitcoin)
    sector_id INTEGER REFERENCES crypto_sectors(id), -- Related sector (Layer 2)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Entry creation date
);

-- 3. Crypto Sectors (Layer 2)
CREATE TABLE crypto_sectors (
    id SERIAL PRIMARY KEY, -- Unique sector identifier
    name VARCHAR(50) UNIQUE NOT NULL, -- Sector name (e.g., DeFi, Layer1)
    description TEXT, -- Optional sector description
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Entry creation date
);

-- Mapping cryptocurrencies to sectors (Layer 2)
CREATE TABLE crypto_sector_mapping (
    id SERIAL PRIMARY KEY, -- Unique mapping identifier
    crypto_id INTEGER REFERENCES cryptocurrencies(id) ON DELETE CASCADE, -- Crypto reference
    sector_id INTEGER REFERENCES crypto_sectors(id) ON DELETE CASCADE, -- Sector reference
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Mapping creation date
);

-- 4. Watchlists (User asset management)
CREATE TABLE watchlists (
    id SERIAL PRIMARY KEY, -- Unique watchlist identifier
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, -- Owner user reference
    name VARCHAR(50) NOT NULL, -- Watchlist name
    is_public BOOLEAN DEFAULT false, -- Public/private flag
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Creation date
);

CREATE TABLE watchlist_items (
    id SERIAL PRIMARY KEY, -- Unique item identifier
    watchlist_id INTEGER REFERENCES watchlists(id) ON DELETE CASCADE, -- Parent watchlist reference
    crypto_id INTEGER REFERENCES cryptocurrencies(id) ON DELETE CASCADE, -- Crypto reference
    allocation NUMERIC(5,2) DEFAULT 0.0, -- Allocated percentage in portfolio
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Entry creation date
);

-- 5. Layer 1: Macro Market Analysis and Indicators
CREATE TABLE market_regime_analysis (
    id SERIAL PRIMARY KEY, -- Unique regime analysis identifier
    regime VARCHAR(10) NOT NULL, -- Market regime (bull, bear, neutral)
    confidence NUMERIC(5,4), -- Model confidence score
    context JSONB, -- Additional regime context (JSON)
    evaluated_at TIMESTAMP WITH TIME ZONE, -- Regime evaluation time
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Entry creation date
);

CREATE TABLE market_sentiment_data (
    id SERIAL PRIMARY KEY, -- Unique sentiment data identifier
    source VARCHAR(50), -- Sentiment source (e.g., Fear & Greed, Twitter)
    value NUMERIC(5,2), -- Sentiment value
    context JSONB, -- Additional sentiment context (JSON)
    evaluated_at TIMESTAMP WITH TIME ZONE, -- Sentiment evaluation time
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Entry creation date
);

CREATE TABLE dominance_data (
    id SERIAL PRIMARY KEY, -- Unique dominance entry identifier
    symbol VARCHAR(20), -- Crypto symbol (BTC, ETH, ...)
    dominance NUMERIC(6,3), -- Dominance percentage
    context JSONB, -- Additional dominance context (JSON)
    evaluated_at TIMESTAMP WITH TIME ZONE, -- Dominance evaluation time
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Entry creation date
);

CREATE TABLE macro_indicators (
    id SERIAL PRIMARY KEY, -- Unique macro indicator identifier
    indicator_name VARCHAR(50), -- Indicator name (e.g., SMA, Volume)
    value NUMERIC(20,8), -- Indicator value
    context JSONB, -- Additional indicator context (JSON)
    evaluated_at TIMESTAMP WITH TIME ZONE, -- Indicator evaluation time
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Entry creation date
);

-- 6. Layer 2: Sector Analysis and Performance
CREATE TABLE sector_performance (
    id SERIAL PRIMARY KEY, -- Unique performance entry identifier
    sector_id INTEGER REFERENCES crypto_sectors(id) ON DELETE CASCADE, -- Sector reference
    period VARCHAR(20), -- Time period (e.g., 1d, 1w, 1m)
    performance NUMERIC(10,4), -- Performance metric (e.g., ROI)
    context JSONB, -- Additional performance context (JSON)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Entry creation date
);

CREATE TABLE sector_rotation_analysis (
    id SERIAL PRIMARY KEY, -- Unique rotation entry identifier
    from_sector_id INTEGER REFERENCES crypto_sectors(id), -- Source sector reference
    to_sector_id INTEGER REFERENCES crypto_sectors(id), -- Destination sector reference
    score NUMERIC(5,3), -- Rotation score
    context JSONB, -- Additional rotation context (JSON)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Entry creation date
);

-- 7. Layer 3 & 4: AI Predictions and Signals
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY, -- Unique prediction identifier
    crypto_id INTEGER REFERENCES cryptocurrencies(id), -- Crypto reference (nullable for macro predictions)
    watchlist_id INTEGER REFERENCES watchlists(id), -- Related watchlist (nullable)
    user_id INTEGER REFERENCES users(id), -- User reference (nullable for system AI)
    model_name VARCHAR(50), -- Model name
    model_version VARCHAR(20), -- Model version
    ai_layer INTEGER, -- AI layer (1: macro, 2: sector, 3: asset, 4: timing)
    predicted_type VARCHAR(30), -- Prediction type (price, regime, signal, indicator, ...)
    predicted_value JSONB, -- Model output value (number, string, JSON)
    confidence_score NUMERIC(5,4), -- Model confidence score
    prediction_horizon INTEGER, -- Prediction horizon (hours/days)
    target_datetime TIMESTAMP WITH TIME ZONE, -- Target date/time for prediction
    features_used JSONB, -- Features used in prediction (JSON)
    model_parameters JSONB, -- Model hyperparameters (JSON)
    input_price NUMERIC(20,8), -- Input price (for price predictions)
    input_features JSONB, -- Input feature set (JSON)
    context_data JSONB, -- Additional context (JSON)
    actual_price NUMERIC(20,8), -- Actual price after prediction period
    accuracy_percentage NUMERIC(5,2), -- Model accuracy (percentage)
    absolute_error NUMERIC(20,8), -- Absolute error of prediction
    squared_error NUMERIC(30,8), -- Squared error for metrics
    is_realized BOOLEAN DEFAULT false, -- Prediction realized flag
    is_accurate BOOLEAN, -- Meets accuracy threshold flag
    accuracy_threshold NUMERIC(5,2) DEFAULT 5.0, -- Accuracy threshold for evaluation
    training_data_end TIMESTAMP WITH TIME ZONE, -- End of training data
    market_conditions VARCHAR(20), -- Market condition during prediction
    volatility_level VARCHAR(10), -- Volatility level (low/medium/high)
    model_training_time NUMERIC(10,2), -- Model training duration (seconds)
    prediction_time NUMERIC(10,6), -- Prediction computation duration (seconds)
    notes TEXT, -- Optional notes
    debug_info JSONB, -- Debug information (JSON)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- Creation date
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- Last update
    evaluated_at TIMESTAMP WITH TIME ZONE -- Evaluation date
);

-- 8. AI Suggestions (Asset and Watchlist Management)
CREATE TABLE ai_suggestions (
    id SERIAL PRIMARY KEY, -- Unique suggestion identifier
    watchlist_id INTEGER REFERENCES watchlists(id) ON DELETE CASCADE, -- Target watchlist reference
    crypto_id INTEGER REFERENCES cryptocurrencies(id), -- Target crypto reference
    suggestion_type VARCHAR(30), -- Suggestion type (add, remove, rebalance, replace, alert)
    ai_layer INTEGER, -- AI layer responsible for suggestion
    confidence_score NUMERIC(5,4), -- Model confidence score
    reasoning JSONB, -- Reasoning and explanation (JSON)
    context_data JSONB, -- Additional context (JSON)
    status VARCHAR(20) DEFAULT 'pending', -- Suggestion status (pending, approved, rejected, implemented)
    reviewed_by INTEGER REFERENCES users(id), -- Reviewer user reference
    reviewed_at TIMESTAMP WITH TIME ZONE, -- Review date/time
    implemented_at TIMESTAMP WITH TIME ZONE, -- Implementation date/time
    actual_return NUMERIC(10,4), -- Actual return after implementation
    success_score NUMERIC(5,3), -- Success score for evaluation
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Creation date
);

-- 9. User Activities (Interaction Tracking)
CREATE TABLE user_activities (
    id SERIAL PRIMARY KEY, -- Unique activity identifier
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, -- User reference
    activity_type VARCHAR(30), -- Activity type (login, prediction_view, suggestion_accept, etc.)
    details JSONB, -- Extended activity details (JSON)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Activity date/time
);

-- 10. System Logs and Events
CREATE TABLE system_logs (
    id SERIAL PRIMARY KEY, -- Unique log identifier
    user_id INTEGER REFERENCES users(id), -- User reference (nullable for system events)
    event_type VARCHAR(30), -- Event type (error, info, warning, etc.)
    event_details JSONB, -- Event details (JSON)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Event date/time
);