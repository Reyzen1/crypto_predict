# docs\Design\17_0_Database_ERD_Structure.md
# 🗄️ Database ERD Design - Days 15-18
## Complete Database Architecture for 4-Layer AI System

---

## 🎯 **ERD Overview for Single UI Strategy**

### **📊 Database Architecture Summary (Updated):**
```
Core Tables: 29 tables supporting 4-Layer AI System ✅ 100% Complete
Views Required: 12+ views for dashboard and analytics ✅ 100% Complete  
Functions Required: 35+ PL/pgSQL functions for API support ✅ 100% Complete
Indexes Required: 95+ optimized indexes for performance ✅ 100% Complete

Architecture Support:
├── 🔐 Single UI Authentication System
├── 🌍 Layer 1: Macro Analysis (4 tables)
├── 📊 Layer 2: Sector Analysis (4 tables)
├── 💰 Layer 3: Asset Selection (3 tables)
├── ⚡ Layer 4: Timing Signals (4 tables)
├── 🤖 AI & ML Management (3 tables)
├── 👤 User Management (4 tables)
└── 🔧 System Management (5 tables - includes 6 new tables)

🆕 ADDED COMPLETE SUPPORT:
├── 📈 Enhanced Analytics Functions (5 functions)
├── 🔍 Advanced Query Functions (3 functions)  
├── 📊 Critical Dashboard Views (4 views)
├── ⚡ Performance Indexes (15 indexes)
└── 🤖 AI Context & Feedback Functions (2 functions)
```

---

## 🎨 **Enhanced Database Schema (بعدازظهر - 4 ساعت)**

### **📈 Complete ERD Structure**

```mermaid
erDiagram
    %% Core User Management
    users {
        int id PK "Primary key for user identification"
        varchar email UK "Unique email address for authentication"
        varchar password_hash "Hashed password for security"
        varchar first_name "User's first name for personalization"
        varchar last_name "User's last name for personalization"
        varchar role "default: public; User role: admin/public for access control"
        boolean is_active "default: true; Account status for system access"
        boolean is_verified "default: false; Email verification status"
        boolean is_premium "default: false; Premium subscription status for future features"
        timestamp created_at "Account creation timestamp"
        timestamp updated_at "Last profile update timestamp"
        timestamp last_login "Last login time for activity tracking"
        int login_count "Total login count for engagement metrics"
        jsonb preferences "User preferences and settings in JSON format"
        varchar timezone "User's timezone for localized timestamps"
        varchar language "User's preferred language (en, fa, etc.)"
    }

    user_sessions {
        int id PK "Primary key for session identification"
        int user_id FK "Foreign key linking to users table"
        varchar session_token UK "Unique session token for authentication"
        varchar refresh_token "Token for session renewal"
        jsonb device_info "Device and browser information for security"
        inet ip_address "IP address for security and location tracking"
        boolean is_active "Session active status"
        timestamp expires_at "Session expiration time"
        timestamp created_at "Session creation timestamp"
        timestamp last_used_at "Last activity timestamp for session management"
    }

    user_activities {
        int id PK "Primary key for activity tracking"
        int user_id FK "Foreign key linking to users table"
        varchar activity_type "Type of user activity (login, watchlist_update, ai_interaction)"
        varchar entity_type "Type of entity being interacted with (watchlist, asset, suggestion)"
        int entity_id "ID of the specific entity being acted upon"
        varchar action "Specific action performed (create, update, delete, view)"
        jsonb details "Additional activity details in JSON format"
        inet ip_address "IP address for security and audit trail"
        text user_agent "Browser/device user agent string"
        varchar session_id "Session identifier for activity correlation"
        timestamp created_at "Activity timestamp for audit and analytics"
    }

    %% Cryptocurrency Data
    cryptocurrencies {
        int id PK "Primary key for cryptocurrency identification"
        varchar symbol UK "Unique trading symbol (BTC, ETH, etc.)"
        varchar name "Full cryptocurrency name"
        varchar coingecko_id UK "Unique CoinGecko API identifier"
        int market_cap_rank "Market capitalization ranking"
        numeric current_price "Current price in USD"
        numeric market_cap "Total market capitalization"
        numeric total_volume "24h trading volume"
        numeric circulating_supply "Circulating token supply"
        numeric total_supply "Total token supply"
        numeric max_supply "Maximum possible token supply"
        numeric price_change_percentage_24h "24-hour price change percentage"
        numeric price_change_percentage_7d "7-day price change percentage"
        numeric price_change_percentage_30d "30-day price change percentage"
        text description "Detailed cryptocurrency description"
        varchar website_url "Official project website"
        varchar blockchain_site "Blockchain explorer URL"
        varchar whitepaper_url "Technical whitepaper URL"
        varchar twitter_username "Official Twitter handle"
        varchar telegram_channel "Official Telegram channel"
        varchar subreddit_url "Official Reddit community"
        jsonb github_repos "Array of GitHub repository URLs"
        varchar contract_address "Smart contract address for tokens"
        int decimals "Token decimal places for precision"
        boolean is_active "Active status in our system"
        boolean is_supported "Whether we provide analysis for this asset"
        int tier "Priority tier: 1=Admin Default Watchlist, 2=Personal Watchlists, 3=Universe (opportunity detection only)"
        timestamp created_at "Record creation timestamp"
        timestamp updated_at "Last data update timestamp"
        timestamp last_data_update "Last price/market data refresh"
    }

    price_data {
        int id PK "Primary key for price data records"
        int crypto_id FK "Foreign key linking to cryptocurrencies table"
        timestamp timestamp "Timestamp for this price data point"
        numeric open_price "Opening price for the time period"
        numeric high_price "Highest price during the time period"
        numeric low_price "Lowest price during the time period"
        numeric close_price "Closing price for the time period"
        numeric volume "Trading volume during the time period"
        numeric market_cap "Market capitalization at this timestamp"
        jsonb technical_indicators "Calculated technical indicators (RSI, MACD, etc.)"
        timestamp created_at "Record creation timestamp"
    }

    %% Layer 1: Macro Analysis
    market_regime_analysis {
        int id PK "Primary key for market regime analysis"
        varchar regime "bull/bear/sideways" 
        numeric confidence_score "AI confidence score for regime classification (0-1)"
        jsonb indicators "Market indicators used for regime detection"
        jsonb analysis_data "Detailed analysis data and supporting metrics"
        timestamp analysis_time "When this analysis was performed"
        timestamp created_at "Record creation timestamp"
        timestamp updated_at "Last update timestamp"
    }

    market_sentiment_data {
        int id PK "Primary key for sentiment data"
        numeric fear_greed_index "Fear & Greed Index value (0-100)"
        numeric social_sentiment "Aggregated social media sentiment score"
        jsonb sentiment_sources "Data from various sentiment sources (Twitter, Reddit, etc.)"
        jsonb analysis_metrics "Detailed sentiment analysis metrics"
        timestamp timestamp "Timestamp for this sentiment snapshot"
        timestamp created_at "Record creation timestamp"
    }

    dominance_data {
        int id PK "Primary key for dominance data"
        numeric btc_dominance "Bitcoin market dominance percentage"
        numeric eth_dominance "Ethereum market dominance percentage"
        numeric alt_dominance "Altcoin market dominance percentage"
        jsonb trend_analysis "Dominance trend analysis and patterns"
        timestamp timestamp "Timestamp for this dominance snapshot"
        timestamp created_at "Record creation timestamp"
    }

    macro_indicators {
        int id PK "Primary key for macro indicators"
        varchar indicator_name "Name of the macro indicator (VIX, DXY, etc.)"
        numeric value "Current value of the indicator"
        varchar timeframe "Timeframe for this indicator (1h, 4h, 1d, etc.)"
        jsonb metadata "Additional metadata about the indicator"
        timestamp timestamp "Timestamp for this indicator value"
        timestamp created_at "Record creation timestamp"
    }

    %% Layer 2: Sector Analysis
    crypto_sectors {
        int id PK "Primary key for crypto sectors"
        varchar name UK "Unique sector name (DeFi, Gaming, Infrastructure, etc.)"
        text description "Detailed description of the sector"
        jsonb characteristics "Sector characteristics and defining features"
        boolean is_active "Whether this sector is actively tracked"
        timestamp created_at "Record creation timestamp"
        timestamp updated_at "Last update timestamp"
    }

    sector_performance {
        int id PK "Primary key for sector performance data"
        int sector_id FK "Foreign key linking to crypto_sectors table"
        numeric performance_24h "24-hour sector performance percentage"
        numeric performance_7d "7-day sector performance percentage"
        numeric performance_30d "30-day sector performance percentage"
        numeric volume_change "Volume change percentage for the sector"
        numeric market_cap_change "Market cap change percentage for the sector"
        jsonb performance_metrics "Detailed performance metrics and calculations"
        timestamp analysis_time "When this performance analysis was calculated"
        timestamp created_at "Record creation timestamp"
    }

    sector_rotation_analysis {
        int id PK "Primary key for sector rotation analysis"
        int from_sector_id FK "Sector where capital is rotating from"
        int to_sector_id FK "Sector where capital is rotating to"
        numeric rotation_strength "Strength of the rotation signal (0-1)"
        numeric confidence_score "AI confidence in rotation analysis (0-1)"
        jsonb rotation_indicators "Indicators supporting this rotation analysis"
        timestamp analysis_time "When this rotation analysis was performed"
        timestamp created_at "Record creation timestamp"
    }

    crypto_sector_mapping {
        int id PK "Primary key for crypto-sector mapping"
        int crypto_id FK "Foreign key linking to cryptocurrencies table"
        int sector_id FK "Foreign key linking to crypto_sectors table"
        numeric allocation_percentage "Percentage allocation of crypto to this sector"
        boolean is_primary_sector "Whether this is the primary sector for the crypto"
        timestamp created_at "Record creation timestamp"
        timestamp updated_at "Last update timestamp"
    }

    %% Layer 3: Asset Selection
    watchlists {
        int id PK "Primary key for watchlist identification"
        varchar name "Watchlist name for user identification"
        text description "Detailed description of watchlist purpose"
        int user_id FK "Foreign key linking to users table (null for default)"
        --(edit)varchar watchlist_type<--type "default/personal; Type of watchlist: system default or user personal"
        boolean is_active "Whether this watchlist is currently active"
        boolean is_public "Whether this watchlist can be shared (future feature)"
        int max_assets "Maximum number of assets allowed in this watchlist"
        int sort_order "Order for displaying multiple watchlists"
        timestamp created_at "Watchlist creation timestamp"
        timestamp updated_at "Last modification timestamp"
    }

    watchlist_assets {
        int id PK "Primary key for watchlist asset entries"
        int watchlist_id FK "Foreign key linking to watchlists table"
        int crypto_id FK "Foreign key linking to cryptocurrencies table"
        --(new) varchar position_type "Type of position type to watch: long, short"
        int position "Position/rank within the watchlist for ordering"
        --decimal weight "Portfolio weight allocation for this asset (0-1)"
        --decimal target_allocation "Target allocation percentage for portfolio management"
        text notes "User or admin notes about this asset inclusion"
        boolean is_active "Whether this asset is currently active in the watchlist"
        timestamp added_at "When this asset was added to the watchlist"
        int added_by FK "User who added this asset (admin or user)"
        int last_modified_by FK "User who last modified this asset entry"
    }

    --(removed) ai_suggestions {
        int id PK "Primary key for AI suggestion tracking"
        int watchlist_id FK "Watchlist this suggestion applies to"
        int crypto_id FK "Cryptocurrency being suggested"
        --(new)int prediction_id FK "Foreign key linking to predictions table"
        varchar suggestion_type "Type of suggestion: --(edit) add_long, add_short, remove, change_position <-- add, remove, --rebalance, --tier_change"
        --int ai_layer "Which AI layer generated this suggestion (1-4)"
        --decimal confidence_score "AI confidence in this suggestion (0-1)"
        --jsonb reasoning "Structured AI reasoning for the suggestion"
        --jsonb context_data "Market context data used for the suggestion"
        int target_position "Suggested position in the watchlist"
        --decimal target_weight "Suggested portfolio weight allocation"
        --decimal expected_return "Expected return percentage from this suggestion"
        --decimal risk_score "Risk assessment score for this suggestion (0-1)"
        (edit add default) varchar status "default: pending; Current status: pending, approved, rejected, implemented"
        --int reviewed_by FK "Admin user who reviewed this suggestion"
        --timestamp reviewed_at "When the suggestion was reviewed"
        timestamp implemented_at "When the suggestion was implemented"
        --decimal actual_return "Actual return achieved after implementation"
        --decimal success_score "Success rating of the suggestion (0-1)"
        timestamp created_at "Suggestion creation timestamp"
        timestamp expires_at "When this suggestion expires"
    }

    (--add)portfolio {
        int id PK
        int user_id FK "REFERENCES users(id) ON DELETE CASCADE"
        int crypto_id FK "REFERENCES cryptocurrencies(id); only for crypto assets available in the system."
        varchar asset_symbol "NOT NULL; applies to both available and unavailable crypto assets."
        jsonb external_asset_info "for external assets"
        varchar asset_type "NOT NULL; 'Crypto Asset', 'Stablecoin', 'Long Position', 'Short Position'"
        numeric leverage_ratio "DEFAULT 1.0; 1.0 = no leverage"
        numeric quantity "NOT NULL DEFAULT 0; remaining_quantity"
        numeric entry_price "avg if partial entries"
        numeric exit_price "avg if partial exits"
        varchar trade_status "NOT NULL; 'open', 'reducing', 'closed', 'accumulating', 'exit_plan'"
        numeric pnl_realized_usd "DEFAULT 0; realized profit/loss"
        numeric allocation_target_percent "target percentage in portfolio"
        text investment_thesis "investment rationale"
        varchar investment_timeframe "'short_term', 'medium_term', 'long_term'"
        varchar risk_category "DEFAULT 'moderate'; 'conservative', 'moderate', 'aggressive'"
        numeric stop_loss_price "portfolio-level SL"
        numeric take_profit_price "portfolio-level TP"
        numeric max_allocation_percent "DEFAULT 10; maximum allocation"
        timestamp created_at "DEFAULT NOW()"
        timestamp updated_at "DEFAULT NOW()"
    }

    (--add)trade_actions {
        int id PK
        int portfolio_id FK "REFERENCES portfolio(id)"
        varchar action_type "NOT NULL; 'buy', 'sell', 'partial_sell', 'entry', 'partial_exit', 'full_exit', 'modify_sl', 'modify_tp'"
        numeric asset_price "NOT NULL; price at the time of this action"
        numeric quantity "NOT NULL; quantity of this action"
        numeric fees_paid "DEFAULT 0; fee paid for this action"
        numeric pnl_realized_usd "DEFAULT 0; realized profit/loss for full or partial exit"
        varchar timeframe "NOT NULL; '1m', '5m', '15m', '1h', '4h', '1d'"
        varchar emotion_state "emotion during this action (e.g., 'confident', 'fearful', 'fomo', 'calm', 'stressed')"
        int confidence_level "CHECK BETWEEN 1 AND 10; 1-10"
        int stress_level "CHECK BETWEEN 1 AND 10; 1-10"
        varchar market_sentiment "'bullish', 'bearish', 'sideways'"
        varchar volatility_level "'low', 'medium', 'high', 'extreme'"
        varchar volume_profile "'above_average', 'below_average', 'normal'"
        varchar primary_setup "'breakout', 'pullback', 'reversal', 'trend_follow'"
        jsonb confirmation_signals "RSI, MACD, etc used"
        varchar chart_pattern "'triangle', 'flag', 'head_shoulders'"
        jsonb analysis_snapshot "snapshot of analysis at entry/exit"
        numeric stop_loss "SL at the time of this action"
        numeric take_profit "TP at the time of this action"
        numeric capital_amount "capital amount at the time of trade"
        numeric risk_percent "risk percentage of total capital in this action"
        varchar reason "reason for this action (e.g., 'hit_tp', 'stop_loss', 'manual_exit', 'market_news', 'rebalance')"
        varchar action_source "NOT NULL; 'manual', 'ai_signal', 'copy_trade', 'algorithm'"
        int signal_id FK "REFERENCES trading_signals(id); if AI-generated"
        text lesson_learned "lessons learned; mistakes made; what was right; what was wrong"
        text notes "notes for this action"
        timestamp created_at "DEFAULT NOW()"
        timestamp updated_at "DEFAULT NOW()"
    }

    %% Layer 4: Micro Timing
    trading_signals {
        int id PK "Primary key for trading signal identification"
        int crypto_id FK "Cryptocurrency this signal applies to"
        (new) int prediction_id FK "Foreign key linking to predictions table"
        varchar signal_type "long/short; Type of trading signal: long or short position"
        numeric entry_price "Recommended entry price for the trade"
        numeric target_price "Target price for profit taking"
        numeric stop_loss "Stop loss price for risk management"
        -- numeric confidence_score "AI confidence in this signal (0-1)"
        varchar risk_level "Risk level assessment: low, medium, high, extreme"
        numeric risk_reward_ratio "Risk to reward ratio for this trade"
        int time_horizon_hours "Expected time horizon for this signal in hours"
        -- jsonb ai_analysis "Detailed AI analysis supporting this signal"
        -- jsonb market_context "Market context and conditions when signal was generated"
        varchar status "Signal status: active, executed, expired, cancelled"
        timestamp generated_at "When this signal was generated"
        timestamp expires_at "When this signal expires"
        timestamp updated_at "Last update timestamp"
    }

    -- signal_executions {
        int id PK "Primary key for signal execution tracking"
        int signal_id FK "Foreign key linking to trading_signals table"
        int user_id FK "User who executed this signal"
        numeric execution_price "Actual price at which the signal was executed"
        numeric position_size "Size of the position taken"
        numeric portfolio_percentage "Percentage of portfolio allocated to this trade"
        varchar execution_type "Execution method: manual or automatic"
        varchar status "Execution status: pending, filled, partially_filled, cancelled"
        jsonb execution_details "Detailed execution information and metadata"
        timestamp executed_at "When the signal was executed"
        timestamp updated_at "Last update timestamp"
    }

    -- risk_management {
        int id PK "Primary key for user risk management settings"
        int user_id FK "User these risk settings belong to"
        numeric max_position_size "Maximum position size allowed per trade"
        numeric max_portfolio_risk "Maximum portfolio risk percentage (0-1)"
        jsonb risk_rules "Custom risk rules and parameters"
        jsonb current_exposure "Current portfolio exposure and risk metrics"
        jsonb risk_metrics "Calculated risk metrics and assessments"
        timestamp last_calculated "When risk metrics were last calculated"
        timestamp updated_at "Last update timestamp"
    }

    %% Predictions (Unified for all layers)
    predictions {
        int id PK "Primary key for prediction tracking"
        int crypto_id FK "Cryptocurrency being predicted"
        -- int watchlist_id FK "Watchlist context for this prediction"
        -- int user_id FK "User receiving this prediction"
        --(new) int ai_models_id FK "AI model that generated this prediction"
        --varchar model_name "Name of the AI model that generated this prediction"
        --varchar model_version "Version of the AI model used"
        --int layer_source "Which AI layer generated this prediction (1-4)"
        varchar prediction_type "Type of prediction: price, event, trend, etc."
        numeric predicted_price "Predicted price value"
        jsonb predicted_value "Non-price predictions in structured format"
        numeric confidence_score "Model confidence in this prediction (0-1)"
        int prediction_horizon "Prediction time horizon in hours"
        timestamp target_datetime "Target date/time for this prediction"
        jsonb features_used "Input features used by the model"
        -- jsonb model_parameters "Model parameters and configuration"
        numeric input_price "Input price when prediction was made"
        jsonb input_features "Input feature values"
        jsonb context_data "Market context at prediction time"
        numeric actual_price "Actual price at target datetime (for evaluation)"
        numeric accuracy_percentage "Prediction accuracy percentage"
        numeric absolute_error "Absolute error between predicted and actual"
        numeric squared_error "Squared error for model performance metrics"
        boolean is_realized "Whether the prediction timeframe has passed"
        boolean is_accurate "Whether prediction met accuracy threshold"
        numeric accuracy_threshold "Threshold for considering prediction accurate"
        --(edit) jsonb<--varchar market_conditions "Market conditions during prediction"
        varchar volatility_level "Volatility level: low, medium, high"
        --numeric model_training_time "Time taken to train the model (seconds)"
        numeric prediction_time "Time taken to generate prediction (seconds)"
        text notes "Additional notes about this prediction"
        jsonb debug_info "Debug information for model analysis"
        timestamp created_at "Prediction creation timestamp"
        timestamp updated_at "Last update timestamp"
        timestamp evaluated_at "When prediction was evaluated for accuracy"
    }

    (--add)ai_recommendations {
        int id PK "Unique identifier for each recommendation"

        varchar target_entity_type "Type of entity: 'portfolio', 'watchlist', 'asset', 'user', 'strategy'"
        int target_entity_id "ID of the target entity (e.g. portfolio.id, watchlist.id)"

        varchar recommendation_type "Type of recommendation: 'entry', 'exit', 'risk_management', 'rebalance', 'allocation', 'position_sizing', 'learning'"
        varchar recommendation_title "Short title summarizing the recommendation"
        text recommendation_summary "Brief explanation of the recommendation purpose"

        jsonb recommendation_payload "Structured content: suggested_position_size, stop_loss, take_profit, rebalance instructions, etc."

        int prediction_id FK "Reference to prediction that generated this recommendation"

        varchar status "Lifecycle status: 'pending', 'approved', 'followed', 'implemented', 'ignored', 'expired', 'rejected'"
        varchar priority_level "Importance level: 'low', 'medium', 'high', 'urgent'"

        text user_feedback "Optional user comments or feedback"
        int user_rating "User rating: 1 (poor) to 5 (excellent)"
        jsonb outcome_result "Structured result of recommendation execution (e.g. actual_return, success_score)"

        int reviewed_by FK "ID of admin/user who reviewed the recommendation"
        timestamp reviewed_at "Timestamp when recommendation was reviewed"
        timestamp implemented_at "Timestamp when recommendation was executed"
        timestamp expires_at "Expiration time after which recommendation is no longer valid"
        timestamp created_at "Timestamp when recommendation was created"
        timestamp updated_at "Timestamp when recommendation was last updated"
    }

    %% Signal Alerts (User-specific alerts)
    signal_alerts {
        int id PK "Primary key for signal alerts"
        int user_id FK "User who created this alert"
        int crypto_id FK "Cryptocurrency this alert monitors"
        varchar alert_type "Alert type: price_target, signal_generated, volume_spike"
        numeric trigger_value "Value that triggers the alert"
        varchar condition "Condition: above, below, equals, percentage_change"
        boolean is_active "Whether alert is currently active"
        boolean is_triggered "Whether alert has been triggered"
        text message "Custom alert message"
        varchar notification_method "How to notify: email, push, sms"
        timestamp triggered_at "When alert was triggered"
        timestamp last_checked "Last time alert condition was checked"
        timestamp expires_at "When alert expires"
        timestamp created_at "Alert creation timestamp"
        timestamp updated_at "Last update timestamp"
    }

    %% System Management
    (--edited)ai_models {
        int id PK "Unique identifier for each model version"
        varchar name "Model name (shared across versions)"
        varchar version "Model version (e.g., v1.0.0) — a new record is created in this table for every new version"
        varchar architecture "Model architecture: lstm, transformer, ensemble, regression"
        varchar model_type "Model type: macro, sector, asset, timing"
        varchar status "Model status: active, training, inactive, error"
        jsonb configuration "Model configuration and hyperparameters"
        jsonb performance_metrics "Summary of performance metrics for this version"
        jsonb training_features "Set of features used for training"
        jsonb training_data_range "Date range of training data for this version"
        varchar training_data_timeframe "Time interval between training data points (e.g., 1m, 5m, 1h, 1d)"
        varchar target_variable "Target variable: price, trend, volatility, event_probability"
        jsonb input_schema "Structure of model input data"
        text training_notes "Free-form notes about training process or specifics"
        timestamp last_trained "Timestamp when this version was trained"
        timestamp last_prediction "Timestamp of last prediction made by this version"
        jsonb health_status "Health status of this model version"
        boolean is_active "Indicates if this version is currently deployed"
        timestamp created_at "Record creation timestamp"
        timestamp updated_at "Last record update timestamp"
    }

    (--edited)model_performance {
        int id PK "Unique identifier for performance record"
        int model_id FK "Foreign key to ai_models (specific model version)"
        varchar evaluation_metric "Name of evaluation metric: accuracy, mse, mae, sharpe_ratio"
        numeric metric_value "Value of the evaluation metric"
        jsonb evaluation_data_range "Exact date range of data used for evaluation"
        varchar evaluation_data_timeframe "Time interval between evaluation data points (e.g., 1m, 5m, 1h, 1d)"
        int evaluated_predictions_count "Number of predictions evaluated in this assessment"
        jsonb detailed_metrics "Detailed breakdown of performance metrics"
        timestamp evaluation_date "Date when evaluation was performed"
        timestamp created_at "Record creation timestamp"
    }

    system_health {
        int id PK "Primary key for system health monitoring"
        timestamp check_time "When this health check was performed"
        jsonb api_status "Status of various API endpoints and services"
        jsonb database_status "Database performance and connection status"
        jsonb ml_models_status "Status and performance of ML models"
        jsonb data_pipeline_status "Status of data ingestion and processing pipelines"
        numeric overall_health_score "Overall system health score (0-100)"
        jsonb performance_metrics "System performance metrics and KPIs"
        jsonb error_logs "Recent error logs and issues"
        timestamp created_at "Record creation timestamp"
    }

    analytics_data {
        int id PK "Primary key for analytics data storage"
        varchar category "Analytics category: user_behavior, api_usage, performance"
        varchar metric_name "Name of the metric being tracked"
        numeric metric_value "Value of the metric"
        jsonb dimensions "Metric dimensions and breakdown"
        varchar aggregation_level "Aggregation: hourly, daily, weekly, monthly"
        timestamp metric_timestamp "Timestamp for this metric"
        timestamp created_at "Record creation timestamp"
    }

    external_api_logs {
        int id PK "Primary key for external API logging"
        varchar api_provider "External API provider: coingecko, binance, etc."
        varchar endpoint "API endpoint called"
        varchar http_method "HTTP method used"
        int response_status "HTTP response status code"
        numeric response_time_ms "Response time in milliseconds"
        jsonb request_params "Request parameters sent"
        jsonb response_data "Response data received (if successful)"
        text error_message "Error message if request failed"
        timestamp request_timestamp "When the API request was made"
        timestamp created_at "Record creation timestamp"
    }

    background_tasks {
        int id PK "Primary key for background task tracking"
        varchar task_name "Name of the background task"
        varchar task_type "Type: data_sync, model_training, cleanup"
        varchar status "Status: pending, running, completed, failed"
        jsonb task_params "Task parameters and configuration"
        jsonb result_data "Task execution results"
        text error_message "Error message if task failed"
        timestamp started_at "When task execution started"
        timestamp completed_at "When task execution completed"
        numeric execution_time_seconds "Total execution time"
        timestamp created_at "Task creation timestamp"
    }

    %% User Notifications & Feedback
    notifications {
        int id PK "Primary key for notification tracking"
        int user_id FK "User receiving this notification"
        varchar notification_type "Type of notification: signal, alert, system, educational"
        varchar title "Notification title/subject"
        text message "Notification message content"
        jsonb data "Additional notification data and metadata"
        varchar status "Notification status: unread, read, dismissed"
        varchar priority "Notification priority: low, normal, high, urgent"
        timestamp scheduled_for "When notification should be sent"
        timestamp sent_at "When notification was actually sent"
        timestamp read_at "When user read the notification"
        timestamp expires_at "When notification expires"
        timestamp created_at "Notification creation timestamp"
    }

    (--remove)suggestion_feedback {
        int id PK "Primary key for AI suggestion feedback"
        int suggestion_id FK "AI suggestion this feedback is for"
        int user_id FK "User providing the feedback"
        int rating "User rating: 1-5 stars"
        text feedback_text "Detailed user feedback"
        varchar action_taken "Action user took: accepted, rejected, modified"
        jsonb feedback_data "Structured feedback data"
        timestamp created_at "Feedback creation timestamp"
    }

    %% Relationships
    users ||--o{ user_sessions : "has"
    users ||--o{ user_activities : "performs"
    users ||--o{ watchlists : "owns"
    users ||--o{ predictions : "receives"
    users ||--o{ signal_executions : "executes"
    users ||--|| risk_management : "has"
    users ||--o{ notifications : "receives"
    users ||--o{ signal_alerts : "creates"
    users ||--o{ suggestion_feedback : "provides"

    cryptocurrencies ||--o{ price_data : "has"
    cryptocurrencies ||--o{ watchlist_assets : "included_in"
    cryptocurrencies ||--o{ predictions : "predicted"
    cryptocurrencies ||--o{ trading_signals : "generates"
    cryptocurrencies ||--o{ ai_suggestions : "suggested"
    cryptocurrencies ||--o{ crypto_sector_mapping : "belongs_to"
    cryptocurrencies ||--o{ signal_alerts : "monitored_by"

    crypto_sectors ||--o{ sector_performance : "has"
    crypto_sectors ||--o{ sector_rotation_analysis : "rotates_from"
    crypto_sectors ||--o{ sector_rotation_analysis : "rotates_to"
    crypto_sectors ||--o{ crypto_sector_mapping : "contains"

    watchlists ||--o{ watchlist_assets : "contains"
    watchlists ||--o{ ai_suggestions : "targets"
    watchlists ||--o{ predictions : "context"

    trading_signals ||--o{ signal_executions : "executed_as"
    ai_suggestions ||--o{ suggestion_feedback : "receives"
    ai_models ||--o{ model_performance : "evaluated_by"
    ai_models ||--o{ predictions : "generates"

    watchlist_assets }o--|| cryptocurrencies : "references"
    ai_suggestions }o--|| cryptocurrencies : "suggests"
    ai_suggestions }o--|| watchlists : "for"
    signal_alerts }o--|| cryptocurrencies : "monitors"
    crypto_sector_mapping }o--|| crypto_sectors : "maps_to"
    crypto_sector_mapping }o--|| cryptocurrencies : "maps_from"
```

---

## 📊 **Database Tables Summary**

### **👤 User Management (4 tables):**
```
1. users                 - Core user accounts and authentication
2. user_sessions         - Session management and security
3. user_activities       - User activity tracking and analytics
4. notifications         - User notification system
```

### **💰 Cryptocurrency Data (2 tables):**
```
1. cryptocurrencies      - Master cryptocurrency data
2. price_data           - Historical and real-time price data
```

### **🌍 Layer 1: Macro Analysis (4 tables):**
```
1. market_regime_analysis - Bull/bear/sideways market classification
2. market_sentiment_data  - Fear & Greed Index and social sentiment
3. dominance_data        - BTC/ETH/ALT market dominance tracking
4. macro_indicators      - VIX, DXY and other macro indicators
```

### **📊 Layer 2: Sector Analysis (4 tables):**
```
1. crypto_sectors        - 11 crypto sector definitions
2. sector_performance    - Sector performance metrics
3. sector_rotation_analysis - Money flow between sectors
4. crypto_sector_mapping - Many-to-many crypto-sector relationships
```

### **📋 Layer 3: Asset Selection (3 tables):**
```
1. watchlists           - User and admin watchlist management
2. watchlist_assets     - Assets within watchlists
3. ai_suggestions       - AI-generated portfolio suggestions
```

### **⚡ Layer 4: Timing Signals (4 tables):**
```
1. trading_signals      - AI-generated trading signals
2. signal_executions    - User signal execution tracking
3. signal_alerts        - User-defined price and signal alerts
4. risk_management      - User risk settings and exposure tracking
```

### **🤖 AI & ML Management (3 tables):**
```
1. ai_models           - AI model management and configuration
2. model_performance   - Model accuracy and performance tracking
3. predictions         - Unified prediction storage for all layers
```

### **🔧 System Management (5 tables):**
```
1. system_health       - System health monitoring and alerts
2. analytics_data      - Usage analytics and KPI tracking
3. external_api_logs   - External API call logging and monitoring
4. background_tasks    - Background task execution tracking
5. suggestion_feedback - User feedback on AI suggestions
```

### **📈 Total: 29 Tables Supporting:**
```
✅ Single UI Strategy with context-aware access
✅ 4-Layer AI System with complete data flow
✅ Admin Panel with comprehensive management
✅ Real-time data updates and monitoring
✅ Scalable architecture for future growth
```

---

**📅 Last Updated:** September 4, 2025  
**🎯 Purpose:** Complete ERD for Single UI Strategy  
**✅ Status:** Ready for Table Creation Scripts Implementation
