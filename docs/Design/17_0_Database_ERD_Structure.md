# docs\Design\17_0_Database_ERD_Structure.md
# 🗄️ Database ERD Design - Days 15-18
## **📈 Complete ERD Structure**

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
        int login_count "Total login count for engagement metrics"
        jsonb preferences "User preferences and settings in JSON format"
        varchar timezone "User's timezone for localized timestamps"
        varchar language "User's preferred language (en, fa, etc.)"
        timestamp last_login "Last login time for activity tracking"  
        text bio "Short user biography or description"
        varchar profile_picture_url "URL to user's profile picture"
        varchar reset_password_token "Token for password reset functionality"
        timestamp reset_password_expires "Expiration time for reset token"
        varchar email_verification_token "Token for email verification"
        timestamp email_verification_expires "Expiration time for email verification token"
        int failed_login_attempts "Count of consecutive failed login attempts"
        timestamp lockout_expires "Account lockout expiration time after too many failed attempts"
        varchar referral_code "Unique referral code for user invitations"
        int referred_by FK "User ID of the referrer, if applicable"
        int referral_count "Number of successful referrals made by this user"
        numeric account_balance "User's account balance for future monetization"
        varchar subscription_plan "Current subscription plan: free, basic, pro, enterprise"
        timestamp subscription_expires_at "Subscription plan expiration date"
        text notes "Admin notes about the user"
        timestamp deleted_at "Soft delete timestamp for account deactivation"
        int deleted_by FK "User ID of admin who deleted/deactivated the account"
        timestamp created_at "Account creation timestamp"
        timestamp updated_at "Last profile update timestamp"
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
        timestamp last_used_at "Last activity timestamp for session management"
        timestamp created_at "Session creation timestamp"
        timestamp updated_at "Last activity timestamp for session management"
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
        int session_id FK "Session identifier for activity correlation"
        timestamp created_at "Activity timestamp for audit and analytics"
        timestamp updated_at "Last update timestamp"
    }

    %% Cryptocurrency Data
    cryptocurrencies {
        int id PK "Primary key for cryptocurrency identification"
        varchar symbol UK "Unique trading symbol (BTC, ETH, etc.)"
        varchar name "Full cryptocurrency name"
        jsonb external_ids "Mapping of external API identifiers in JSON format.
                        Keys = service names, Values = asset IDs in those services.
                        Example:
                        {
                          'coingecko': 'bitcoin',
                          'coinmarketcap': '1',
                          'binance': 'BTCUSDT',
                          'kraken': 'XBTUSD'
                        }"
        numeric(30,2) market_cap "Latest known total market capitalization in USD"
        int market_cap_rank "Latest market capitalization ranking"
        numeric(20,8) current_price "Latest known price in USD"
        numeric(30,2) total_volume "Latest known 24h trading volume in USD"
        numeric(30,8) circulating_supply "Current circulating token supply"
        numeric(30,8) total_supply "Total token supply (may be NULL if unknown)"
        numeric(30,8) max_supply "Maximum possible token supply (may be NULL if unlimited)"
        numeric(10,4) price_change_percentage_24h "24-hour price change percentage"
        numeric(10,4) price_change_percentage_7d "7-day price change percentage"
        numeric(10,4) price_change_percentage_30d "30-day price change percentage"
        text description "Detailed cryptocurrency description"
        text logo_url "URL to the cryptocurrency logo image"
        jsonb links "All related URLs and addresses (website, explorer, whitepaper, twitter, telegram, reddit, github, contract, etc.)                  
                Example:
                 {
                   'website': 'https://bitcoin.org',
                   'explorer': 'https://www.blockchain.com/btc',
                   'whitepaper': 'https://bitcoin.org/bitcoin.pdf',
                   'twitter': 'https://twitter.com/bitcoin',
                   'telegram': 'https://t.me/bitcoin',
                   'reddit': 'https://reddit.com/r/bitcoin',
                   'github': ['https://github.com/bitcoin/bitcoin'],
                   'contract': '0x1234567890abcdef...'
                 }"
        jsonb timeframe_usage "Usage statistics per timeframe in JSON format.
                            Keys = timeframe codes (e.g., '1m', '5m', '1h', '1d')
                            Values = integer usage counts.
                            Example:{'1m': 5, '5m': 12, '1h': 120, '4h': 45, '1d': 100}"
        timestamp last_accessed_at "Last time this asset was accessed by any user"
        int access_count "Total number of times this asset has been accessed"
        boolean is_active "Whether this asset is active in our system"
        boolean is_supported "Whether we provide analysis for this asset"
        timestamp created_at "Record creation timestamp"
        timestamp updated_at "Last data update timestamp"
    }

    price_data {
        int id PK "Primary key for price data records"
        int crypto_id FK "Foreign key linking to cryptocurrencies.id"
        varchar timeframe "Timeframe of the record (e.g., '1m', '5m', '1h', '1d')"
        numeric(20,8) open_price "Opening price for the time period in USD"
        numeric(20,8) high_price "Highest price during the time period in USD"
        numeric(20,8) low_price "Lowest price during the time period in USD"
        numeric(20,8) close_price "Closing price for the time period in USD"
        numeric(30,2) volume "Trading volume during the time period in USD"
        numeric(30,2) market_cap "Market capitalization at this timestamp in USD"
        numeric(30,8) circulating_supply "Circulating supply at this timestamp"
        jsonb technical_indicators "Calculated technical indicators (RSI, MACD, etc.).
                                    NULL if not stored for this asset/timeframe.
                                    Example:
                                    {
                                    'RSI': 56.23,
                                    'MACD': { 'value': -12.45, 'signal': -10.32, 'histogram': -2.13 },
                                    'SMA': { '50': 45000.12, '200': 42000.55 },
                                    'EMA': { '20': 45500.78, '100': 43000.44 }
                                    }"
        timestamp candle_time "Start time of the OHLC candle in UTC."
        timestamp created_at "Record creation timestamp"
    }

    price_data_archive {
        int id PK "Primary key for archived price data records"
        int crypto_id FK "Foreign key linking to cryptocurrencies.id"
        varchar timeframe "Timeframe of the record (e.g., '1m', '5m', '1h', '1d')"
        numeric(20,8) open_price "Opening price for the time period in USD"
        numeric(20,8) high_price "Highest price during the time period in USD"
        numeric(20,8) low_price "Lowest price during the time period in USD"
        numeric(20,8) close_price "Closing price for the time period in USD"
        numeric(30,2) volume "Trading volume during the time period in USD"
        numeric(30,2) market_cap "Market capitalization at this timestamp in USD"
        jsonb technical_indicators "Calculated technical indicators (RSI, MACD, etc.).
                                    Usually NULL for archived data unless specifically preserved."
        timestamp candle_time "Start time of the OHLC candle in UTC."
        timestamp created_at "Record creation timestamp"
    }

    %% Layer 1: Macro Analysis
    market_regime_analysis {
        int id PK "Primary key for market regime analysis"
        varchar regime "bull/bear/sideways" 
        numeric confidence_score "AI confidence score for regime classification (0-1)"
        jsonb indicators "Market indicators used for regime detection"
        jsonb analysis_data "Detailed analysis data and supporting metrics"
        timestamp created_at "Record creation timestamp"
        timestamp updated_at "Last update timestamp"
    }

    market_sentiment_data {
        int id PK "Primary key for sentiment data"
        numeric fear_greed_index "Fear & Greed Index value (0-100)"
        numeric social_sentiment "Aggregated social media sentiment score"
        jsonb sentiment_sources "Data from various sentiment sources (Twitter, Reddit, etc.)"
        jsonb analysis_metrics "Detailed sentiment analysis metrics"
        timestamp created_at "Record creation timestamp"
        timestamp updated_at "Last update timestamp"        
    }

    dominance_data {
        int id PK "Primary key for dominance data"
        numeric btc_dominance "Bitcoin market dominance percentage"
        numeric eth_dominance "Ethereum market dominance percentage"
        numeric alt_dominance "Altcoin market dominance percentage"
        jsonb trend_analysis "Dominance trend analysis and patterns"
        timestamp created_at "Record creation timestamp"
        timestamp updated_at "Last update timestamp"        
    }

    macro_indicators {
        int id PK "Primary key for macro indicators"
        varchar indicator_name "Name of the macro indicator (VIX, DXY, etc.)"
        numeric value "Current value of the indicator"
        varchar timeframe "Timeframe for this indicator (1h, 4h, 1d, etc.)"
        jsonb metadata "Additional metadata about the indicator"
        timestamp created_at "Record creation timestamp"
        timestamp updated_at "Last update timestamp"        
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
        timestamp created_at "Record creation timestamp"
        timestamp updated_at "Last update timestamp"
    }

    sector_rotation_analysis {
        int id PK "Primary key for sector rotation analysis"
        int from_sector_id FK "Sector where capital is rotating from"
        int to_sector_id FK "Sector where capital is rotating to"
        numeric rotation_strength "Strength of the rotation signal (0-1)"
        numeric confidence_score "AI confidence in rotation analysis (0-1)"
        jsonb rotation_indicators "Indicators supporting this rotation analysis"
        timestamp created_at "Record creation timestamp"
        timestamp updated_at "Last update timestamp"
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
        varchar watchlist_type "default/personal; Type of watchlist: system default or user personal"
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
        varchar position_type "Type of position type to watch: long, short"
        int position "Position/rank within the watchlist for ordering"
        text notes "User or admin notes about this asset inclusion"
        boolean is_active "Whether this asset is currently active in the watchlist"
        int added_by FK "User who added this asset (admin or user)"
        int last_modified_by FK "User who last modified this asset entry"
        timestamp created_at "When this asset was added to the watchlist"
        timestamp updated_at "Last update timestamp"
    }

    portfolio {
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

    trade_actions {
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
        varchar risk_level "Risk level assessment: low, medium, high, extreme"
        numeric risk_reward_ratio "Risk to reward ratio for this trade"
        int time_horizon_hours "Expected time horizon for this signal in hours"
        varchar status "Signal status: active, executed, expired, cancelled"
        timestamp expires_at "When this signal expires"
        timestamp created_at "When this signal was generated"
        timestamp updated_at "Last update timestamp"
    }


    %% Predictions (Unified for all layers)
    predictions {
        int id PK "Primary key for prediction tracking"
        int crypto_id FK "Cryptocurrency being predicted"
        (new) int ai_models_id FK "AI model that generated this prediction"
        varchar prediction_type "Type of prediction: price, event, trend, etc."
        numeric predicted_price "Predicted price value"
        jsonb predicted_value "Non-price predictions in structured format"
        numeric confidence_score "Model confidence in this prediction (0-1)"
        int prediction_horizon "Prediction time horizon in hours"
        timestamp target_datetime "Target date/time for this prediction"
        jsonb features_used "Input features used by the model"
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
        jsonb market_conditions "Market conditions during prediction"
        varchar volatility_level "Volatility level: low, medium, high"
        numeric prediction_time "Time taken to generate prediction (seconds)"
        text notes "Additional notes about this prediction"
        jsonb debug_info "Debug information for model analysis"
        timestamp evaluated_at "When prediction was evaluated for accuracy"
        timestamp created_at "Prediction creation timestamp"
        timestamp updated_at "Last update timestamp"
    }

    ai_recommendations {
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
    ai_models {
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

    model_performance {
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
        timestamp updated_at "Last record update timestamp"
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
        timestamp updated_at "Last update timestamp"
    }

    analytics_data {
        int id PK "Primary key for analytics data storage"
        varchar category "Analytics category: user_behavior, api_usage, performance"
        varchar metric_name "Name of the metric being tracked"
        numeric metric_value "Value of the metric"
        jsonb dimensions "Metric dimensions and breakdown"
        varchar aggregation_level "Aggregation: hourly, daily, weekly, monthly"
        timestamp created_at "Record creation timestamp"
        timestamp updated_at "Last update timestamp"
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
        timestamp created_at "Record creation timestamp"
        timestamp updated_at "Last update timestamp"
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
        timestamp updated_at "Last update timestamp"
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
        timestamp updated_at "Last update timestamp"
    }


    %% Core User Management Relationships
    users ||--o{ user_sessions : "has"
    users ||--o{ user_activities : "performs"  
    users ||--o{ watchlists : "owns"
    users ||--o{ portfolio : "manages"
    users ||--o{ signal_alerts : "creates"
    users ||--o{ notifications : "receives"
    users }o--o{ users : "refers" %% self-referencing for referral system
    users ||--o{ users : "deleted_by"
    user_sessions ||--o{ user_activities : "includes"
    
    %% Cryptocurrency Core Relationships
    cryptocurrencies ||--o{ price_data : "has"
    cryptocurrencies ||--o{ watchlist_assets : "included_in"
    cryptocurrencies ||--o{ predictions : "predicted_for"
    cryptocurrencies ||--o{ trading_signals : "generates_signals_for"
    cryptocurrencies ||--o{ crypto_sector_mapping : "belongs_to_sectors"
    cryptocurrencies ||--o{ signal_alerts : "monitored_by_alerts"
    cryptocurrencies ||--o{ portfolio : "held_in"

    %% Portfolio & Trading Relationships
    portfolio ||--o{ trade_actions : "has"
    trade_actions }o--|| trading_signals : "based_on" %% optional relationship
    
    %% Sector Analysis Relationships  
    crypto_sectors ||--o{ sector_performance : "has"
    crypto_sectors ||--o{ crypto_sector_mapping : "contains"
    crypto_sectors ||--o{ sector_rotation_analysis : "from_sector"
    crypto_sectors ||--o{ sector_rotation_analysis : "to_sector"

    %% Watchlist Relationships
    watchlists ||--o{ watchlist_assets : "contains"
    watchlists ||--o{ ai_recommendations : "targets" %% corrected from ai_suggestions

    %% AI & ML Relationships
    ai_models ||--o{ predictions : "generates"
    ai_models ||--o{ model_performance : "evaluated_by"
    
    %% Predictions as Central Hub
    predictions ||--o{ trading_signals : "generates"
    predictions ||--o{ ai_recommendations : "basis_for"

    %% Recommendation System
    ai_recommendations }o--|| watchlists : "targets"
    ai_recommendations }o--|| cryptocurrencies : "suggests"
    ai_recommendations }o--|| predictions : "based_on"
    ai_recommendations }o--|| users : "reviewed_by" %% for reviewed_by field

    %% Junction Tables (Many-to-Many)
    watchlist_assets }o--|| watchlists : "belongs_to"
    watchlist_assets }o--|| cryptocurrencies : "references"
    watchlist_assets }o--|| users : "added_by"
    watchlist_assets }o--|| users : "modified_by"

    crypto_sector_mapping }o--|| cryptocurrencies : "maps_crypto"
    crypto_sector_mapping }o--|| crypto_sectors : "maps_sector"

    %% Alert Relationships
    signal_alerts }o--|| users : "belongs_to"
    signal_alerts }o--|| cryptocurrencies : "monitors"

    %% Notification Relationships  
    notifications }o--|| users : "sent_to"

    %% User Activity Tracking
    user_activities }o--|| users : "performed_by"

    %% Background System Relationships
    external_api_logs : "standalone_logging"
    system_health : "standalone_monitoring"
    background_tasks : "standalone_task_management"
    analytics_data : "standalone_analytics"
```
