# docs\Design\17_0_Database_ERD_Structure.md
# 🗄️ Database ERD Design - Days 15-18
## **📈 Complete ERD Structure**

```mermaid
erDiagram
    %% Core User Management
    users {
        int id PK "NOT NULL; Primary key for user identification"
        varchar email UK "NOT NULL; Unique email address for authentication"
        varchar password_hash "NOT NULL; Hashed password for security"
        varchar first_name "User's first name for personalization"
        varchar last_name "User's last name for personalization"
        varchar role "NOT NULL; default: public; User role: admin/public/guest for access control"
        boolean is_active "NOT NULL; default: true; Account status for system access"
        boolean is_verified "NOT NULL; default: false; Email verification status"
        int login_count "Total login count for engagement metrics"
        jsonb preferences "User preferences and settings in JSON format"
        varchar timezone "User's timezone for localized timestamps"
        varchar language "NOT NULL; default: en; User's preferred language (en, fa, etc.)"
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
        timestamp created_at "NOT NULL; default: Now(); Account creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last profile update timestamp"
    }

    user_sessions {
        int id PK "NOT NULL; Primary key for session identification"
        int user_id FK "NOT NULL; Foreign key linking to users table"
        varchar session_token UK "Unique session token for authentication"
        varchar refresh_token "Token for session renewal"
        jsonb device_info "Device and browser information for security"
        inet ip_address "IP address for security and location tracking"
        boolean is_active "Session active status"
        timestamp expires_at "Session expiration time"
        timestamp last_used_at "Last activity timestamp for session management"
        timestamp created_at "NOT NULL; default: Now(); Session creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last activity timestamp for session management"
    }

    user_activities {
        int id PK "NOT NULL; Primary key for activity tracking"
        int user_id FK "NOT NULL; Foreign key linking to users table"
        int session_id FK "NOT NULL; Session identifier for activity correlation"
        varchar activity_type "NOT NULL; Type of user activity (login, watchlist_update, ai_interaction)"
        varchar entity_type "Type of entity being interacted with (watchlist, asset, suggestion)"
        int entity_id "ID of the specific entity being acted upon"
        varchar action "NOT NULL; Specific action performed (create, update, delete, view)"
        jsonb details "Additional activity details in JSON format"
        inet ip_address "IP address for security and audit trail"
        text user_agent "Browser/device user agent string"
        timestamp created_at "NOT NULL; default: Now(); Activity timestamp for audit and analytics"
    }

    %% Cryptocurrency Data
    assets {
        int id PK "NOT NULL; Primary key for cryptocurrency identification"
        varchar(20) symbol UK "NOT NULL; Unique trading symbol (BTC, ETH, etc.)"
        varchar(100) name "NOT NULL; Full cryptocurrency name"
        varchar(20) asset_type "NOT NULL; CHECK (asset_type IN ('crypto','stablecoin','macro','index')); Asset type (crypto, stablecoin, macro for DXY/VIX/SP500/Gold/Oil/CPI, index for total/total2/total3/btc.d/usdt.d/altcoin)"
        varchar(10) quote_currency "For pairs, the quote currency (e.g., USDT)"
        jsonb external_ids "External API identifiers in JSON format.
                        Example:{'coingecko': 'bitcoin','coinmarketcap': '1'}"
        text logo_url "URL to the cryptocurrency logo image"
        jsonb links "All related URLs and addresses (website, explorer, whitepaper, twitter, telegram, reddit, github, contract, etc.)"
        text description "Detailed cryptocurrency description"

        numeric(30,2) market_cap "Latest known total market capitalization in USD"
        int market_cap_rank "Latest market capitalization ranking"
        numeric(20,8) current_price "Latest known price in USD"
        numeric(30,2) total_volume "24h trading volume in USD"
        numeric(30,8) circulating_supply "Current circulating token supply"
        numeric(30,8) total_supply "Total token supply (may be NULL if unknown)"
        numeric(30,8) max_supply "Maximum possible token supply (may be NULL if unlimited)"
        numeric(10,4) price_change_percentage_24h "24-hour price change percentage"
        numeric(10,4) price_change_percentage_7d "7-day price change percentage"
        numeric(10,4) price_change_percentage_30d "30-day price change percentage"
        numeric(20,8) ath "all the time high price"
        timestamp ath_date "all the time high price date"
        numeric(20,8) atl "all the time low price"
        timestamp atl_date "all the time low price date"
        jsonb metrics_details "7 records for ohlv in 7d timeframe and so on.. "

        jsonb timeframe_usage "Usage statistics per timeframe in JSON format.
                            Keys = timeframe codes (e.g., '1m', '5m', '1h', '1d')
                            Values = integer usage counts.
                            Example:{'1m': 5, '5m': 12, '1h': 120, '4h': 45, '1d': 100}"
        timestamp last_accessed_at "Last time this asset was accessed by any user"
        int access_count "NOT NULL; default: 0; Total number of times this asset has been accessed"
        boolean is_active "NOT NULL; default: true; Whether this asset is active in our system"
        boolean is_supported "NOT NULL; default: true; Whether we have data for this asset; assets with false will be hidden from UI. This asset may be added by user in the portfolio but we don't have data for it"
        int data_quality_score "NOT NULL; default: 100; Data quality score (0-100)"
        varchar(20) data_source "NOT NULL; default: 'coingecko'; Primary data source: coingecko, binance, coinmarketcap"
        timestamp last_price_update "Last time price data was updated for this asset"
        
        -- 📝 PHASE 1 SCOPE: crypto and stablecoin assets only
        --    macro and index assets will be added in Phase 2
        timestamp created_at "NOT NULL; default: Now(); Record creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last data update timestamp"
        
        -- 📋 Enhanced Constraints
        CONSTRAINT chk_market_cap_positive CHECK (market_cap IS NULL OR market_cap >= 0)
        CONSTRAINT chk_current_price_positive CHECK (current_price IS NULL OR current_price > 0)
        CONSTRAINT chk_supply_positive CHECK (circulating_supply IS NULL OR circulating_supply >= 0)
        CONSTRAINT chk_data_quality CHECK (data_quality_score BETWEEN 0 AND 100)
        CONSTRAINT chk_market_cap_rank CHECK (market_cap_rank IS NULL OR market_cap_rank > 0)
        
        -- 📊 Indexes for Performance
        INDEX idx_assets_symbol (symbol)
        INDEX idx_assets_type_active (asset_type, is_active)
        INDEX idx_assets_market_cap_rank (market_cap_rank) WHERE market_cap_rank IS NOT NULL
        INDEX idx_assets_last_accessed (last_accessed_at) WHERE last_accessed_at IS NOT NULL
    }

    price_data {
        int id PK "NOT NULL; Primary key for price data records"
        int asset_id FK "NOT NULL; Foreign key linking to assets.id"
        varchar(10) timeframe "NOT NULL; CHECK (timeframe IN ('1m','5m','15m','1h','4h','1d','1w','1M')); Timeframe of the record"
        numeric(20,8) open_price "NOT NULL; Opening price for the time period in USD"
        numeric(20,8) high_price "NOT NULL; Highest price during the time period in USD"
        numeric(20,8) low_price "NOT NULL; Lowest price during the time period in USD"
        numeric(20,8) close_price "NOT NULL; Closing price for the time period in USD"
        numeric(30,2) volume "NOT NULL; default: 0; Trading volume during the time period in USD"
        numeric(30,2) market_cap "Market capitalization at this timestamp in USD"
        int trade_count "Number of trades during the time period"
        numeric(20,8) vwap "Volume Weighted Average Price during the period"
        
        jsonb technical_indicators "Calculated technical indicators (RSI, MACD, etc.).
                                    Computed asynchronously and cached here for performance.
                                    Example:
                                    {
                                        'RSI': {'14': 56.23, '21': 58.45},
                                        'MACD': {'value': -12.45, 'signal': -10.32, 'histogram': -2.13},
                                        'SMA': {'20': 45500.12, '50': 45000.12, '200': 42000.55},
                                        'EMA': {'12': 46000.78, '26': 45200.44, '200': 43000.44},
                                        'BB': {'upper': 47000, 'middle': 45000, 'lower': 43000},
                                        'volume_sma': {'20': 1500000},
                                        'computed_at': '2025-09-29T10:00:00Z'
                                    }"
        
        timestamp candle_time "NOT NULL; Start time of the OHLC candle in UTC"
        boolean is_validated "NOT NULL; default: false; Whether data has been validated"
        
        -- 📝 PHASE 1 SCOPE: crypto assets only, macro data via external APIs
        -- 📝 NOTE: data_source and data_quality_score moved to assets table for optimization
        timestamp created_at "NOT NULL; default: Now(); Record creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last data update timestamp"
        
        -- 📋 Enhanced Constraints & Validations
        CONSTRAINT chk_ohlc_logic CHECK (low_price <= open_price AND low_price <= close_price AND high_price >= open_price AND high_price >= close_price)
        CONSTRAINT chk_prices_positive CHECK (open_price > 0 AND high_price > 0 AND low_price > 0 AND close_price > 0)
        CONSTRAINT chk_volume_non_negative CHECK (volume >= 0)
        CONSTRAINT unique_asset_timeframe_candle UNIQUE (asset_id, timeframe, candle_time)
        
        -- 📊 Performance Indexes
        INDEX idx_price_data_asset_timeframe_time (asset_id, timeframe, candle_time DESC)
        INDEX idx_price_data_candle_time (candle_time DESC)
        INDEX idx_price_data_timeframe (timeframe)
        INDEX idx_price_data_volume (volume DESC) WHERE volume > 0
        
        -- 🚀 Partitioning Strategy (PostgreSQL)
        -- PARTITION BY RANGE (candle_time) - monthly partitions
        -- This will be implemented in migration scripts
    }

    price_data_archive {
        int id PK "NOT NULL; Primary key for archived price data records"
        int asset_id FK "NOT NULL; Foreign key linking to assets.id"
        varchar(10) timeframe "NOT NULL; CHECK (timeframe IN ('1m','5m','15m','1h','4h','1d','1w','1M')); Timeframe of the record"
        numeric(20,8) open_price "NOT NULL; Opening price for the time period in USD"
        numeric(20,8) high_price "NOT NULL; Highest price during the time period in USD"
        numeric(20,8) low_price "NOT NULL; Lowest price during the time period in USD"
        numeric(20,8) close_price "NOT NULL; Closing price for the time period in USD"
        numeric(30,2) volume "NOT NULL; default: 0; Trading volume during the time period in USD"
        numeric(30,2) market_cap "Market capitalization at this timestamp in USD"
        int trade_count "Number of trades during the time period"
        numeric(20,8) vwap "Volume Weighted Average Price during the period"
        
        jsonb technical_indicators "Calculated technical indicators"
        
        timestamp candle_time "NOT NULL; Start time of the OHLC candle in UTC"
        boolean is_validated "NOT NULL; default: false; Whether data has been validated"
        
        timestamp created_at "NOT NULL; default: Now(); Record creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last data update timestamp"
        
        -- 📋 Enhanced Constraints & Validations
        CONSTRAINT chk_ohlc_logic_archive CHECK (low_price <= open_price AND low_price <= close_price AND high_price >= open_price AND high_price >= close_price)
        CONSTRAINT chk_prices_positive_archive CHECK (open_price > 0 AND high_price > 0 AND low_price > 0 AND close_price > 0)
        CONSTRAINT chk_volume_non_negative_archive CHECK (volume >= 0)
        CONSTRAINT unique_asset_timeframe_candle_archive UNIQUE (asset_id, timeframe, candle_time)
        
        -- 📊 Performance Indexes
        INDEX idx_price_data_archive_asset_timeframe_time (asset_id, timeframe, candle_time DESC)
        INDEX idx_price_data_archive_candle_time (candle_time DESC)
        INDEX idx_price_data_archive_timeframe (timeframe)
        INDEX idx_price_data_archive_volume (volume DESC) WHERE volume > 0
        
        -- 🚀 Partitioning Strategy (PostgreSQL)
        -- PARTITION BY RANGE (candle_time) - monthly partitions for archive
        -- This will be implemented in migration scripts
    }

    %% Layer 1: Macro Analysis
    metrics_snapshot {
        int                id                       "NOT NULL; Primary key"  
        timestamp          snapshot_time            "NOT NULL; When snapshot is taken"  
        varchar(10)        timeframe                "NOT NULL; CHECK (timeframe IN ('1m','5m','15m','1h','4h','1d','1w')); Time interval"  
        numeric(18,8)      btc_price_usd            "NOT NULL; BTC price in USD at snapshot time"

        -- 📊 Technical Indicators  
        numeric(5,2)       rsi_14                   "14-period RSI"  
        numeric(30,8)      sma_200                  "200-period simple MA"  
        numeric(30,8)      ema_200                  "200-period exponential MA"  

        -- 🧠 Market Sentiment  
        numeric(5,2)       fear_greed_index         "Fear & Greed Index (alternative.me)"  
        numeric(5,2)       google_trends_score      "Google Trends score for 'Bitcoin'"  

        -- 🧪 Derivatives & Futures  
        numeric(10,6)      funding_rate_btc         "BTC perpetual funding rate"  
        numeric(30,2)      open_interest_btc        "BTC futures open interest"  

        -- 🧬 On-chain & Whale Flows  
        numeric(30,2)      whale_netflow_24h        "24h net flow whale→exchange"  
        int                active_addresses_btc     "Daily active BTC addresses"  

        -- 🧮 Composite & Health  
        numeric(5,2)       altcoin_dominance        "Altcoins’ market-cap dominance (%)"  
        numeric(10,6)      liquidity_score          "24h volume / market-cap ratio"  

        -- 🧭 Cycle & Returns  
        int                halving_countdown_days   "Days until next BTC halving"  
        numeric(5,4)       weekly_return            "1-week return (%)"  
        numeric(5,4)       monthly_return           "1-month return (%)"  

        -- ⭐ Dominance & Total Market-Cap Levels  
        numeric(5,2)       btc_dominance            "BTC dominance (%)"  
        numeric(5,2)       eth_dominance            "ETH dominance (%)"  
        numeric(5,2)       usdt_dominance           "USDT dominance (%)"  
        numeric(18,2)      total                    "Total market-cap (USD)"  

        -- 🔗 Intermarket Levels  
        numeric(10,2)      sp500                    "S&P500 closing price (USD)"  
        numeric(10,2)      gold                     "Gold closing price (USD)"  
        numeric(10,2)      dxy                      "DXY index closing value"  

        -- 📦 Liquidations
        numeric(30,2)      liquidations_long        "24h total long-position liquidation volume (BTC)"
        numeric(30,2)      liquidations_short       "24h total short-position liquidation volume (BTC)"
        jsonb              liquidation_zones        "Liquidation Zones (JSON array of price-bins)
                                                    [  
                                                        {bin_low, bin_high, long_vol, short_vol}, …  
                                                    ]"  

        -- 📦 Extended Metrics (categorized JSON of medium/low-priority signals)  
        jsonb              extended_metrics         "{  
            technical_indicators: {  
                rsi_7, stochastic_k, stochastic_d,  
                macd_value, macd_signal, macd_histogram,  
                sma_100, sma_50, sma_20,  
                ema_100, ema_50, ema_20,  
                bollinger_upper, bollinger_lower, bollinger_bandwidth,  
                atr_14, adx, di_plus, di_minus  
            },  
            trend_metrics: {  
                momentum_score, consolidation_score  
            },  
            sentiment_metrics: {  
                social_sentiment_score, sentiment_direction,  
                twitter_volume, reddit_volume  
            },  
            derivatives_metrics: {  
                funding_rate_eth, open_interest_eth,  
                liquidations_long_24h, liquidations_short_24h,  
                oi_change_24h, funding_rate_trend  
            },  
            onchain_metrics: {  
                exchange_netflow_btc, exchange_netflow_eth,  
                active_addresses_eth,  
                whale_to_exchange_volume_btc, whale_from_exchange_volume_btc,  
                supply_on_exchanges_btc, supply_on_exchanges_eth,  
                tx_volume_btc, tx_volume_eth,  
                miner_outflow, miner_balance_change  
            },  
            composite_metrics: {  
                volatility_index, breadth_advancers_ratio,  
                breadth_new_highs_lows_ratio  
            },  
            correlation_metrics: {  
                corr_eth_btc_30d, corr_total2_btc_30d  
            },  
            cycle_metrics: {  
                btc_epoch_phase, seasonality_score  
            },  
                ai_metrics: {  
                regime_volatility_score  
            }  
        }"  
        -- 📊 Enhanced Core Metrics
        numeric(6,4)       btc_eth_correlation_30d  "30-day BTC-ETH price correlation"
        numeric(6,4)       btc_sp500_correlation_30d "30-day BTC-SP500 correlation"
        numeric(8,4)       us_10y_yield             "US 10-year treasury yield (%)"
        numeric(8,4)       vix_index                "VIX volatility index"
        
        -- 📈 Market Breadth & Quality
        numeric(6,2)       crypto_market_breadth    "Percentage of top 100 cryptos in uptrend"
        int                new_highs_24h            "Number of assets hitting 24h highs"
        int                new_lows_24h             "Number of assets hitting 24h lows"
        numeric(8,4)       momentum_index           "Composite momentum indicator"
        
        -- 🔍 Data Quality & Metadata
        jsonb              data_quality_flags       "Data quality and completeness:
                                                    {
                                                        'completeness_score': 0.95,
                                                        'data_freshness_minutes': 5,
                                                        'missing_sources': [],
                                                        'outlier_flags': {'btc_price': false, 'volume': false},
                                                        'validation_errors': []
                                                    }"
        varchar(50)        snapshot_version         "Version of data collection pipeline"
        boolean            is_validated             "NOT NULL; default: false; Whether data has been validated"
        boolean            has_anomalies            "NOT NULL; default: false; Whether anomalies were detected"
        varchar(20)        data_source              "NOT NULL; default: 'aggregated'; Source: coingecko, binance, aggregated"
        
        -- ⏰ Performance Timing
        timestamp          data_collection_started "When data collection began"
        timestamp          data_collection_completed "When data collection completed"
        int                collection_duration_ms  "Data collection time (milliseconds)"
        
        timestamp          created_at               "NOT NULL; default: Now(); Record creation timestamp"
        timestamp          updated_at               "NOT NULL; default: Now(); Last update timestamp"
        
        -- 📋 Enhanced Constraints
        CONSTRAINT unique_snapshot_time_timeframe UNIQUE (snapshot_time, timeframe)
        CONSTRAINT chk_fear_greed_range CHECK (fear_greed_index IS NULL OR fear_greed_index BETWEEN 0 AND 100)
        CONSTRAINT chk_dominance_range CHECK (btc_dominance BETWEEN 0 AND 100)
        CONSTRAINT chk_btc_price_positive CHECK (price > 0)
        CONSTRAINT chk_collection_duration CHECK (collection_duration_ms IS NULL OR collection_duration_ms >= 0)
    }
        
    ai_regime_analysis {
        int                id                         "NOT NULL; Primary key"
        int                metrics_snapshot_id        "NOT NULL; FK → metrics_snapshot.id"
        int                ai_model_id                "NOT NULL; FK → ai_models.id"

        -- ⏰ Analysis Metadata
        timestamp          analysis_time              "NOT NULL; When this analysis was executed"
        varchar(10)        analysis_timeframe         "NOT NULL; Analysis timeframe: '1h','4h','1d','1w', '1M'"
        varchar(20)        data_source                "NOT NULL; default: 'live'; Data source: live, backtest, simulation"
        
        -- 🎯 Regime Classification
        varchar(15)        current_regime             "NOT NULL; CHECK (current_regime IN ('Bull','Bear','Sideways','Transition','Accumulation','Distribution')); Detected current regime"
        varchar(15)        predicted_regime           "AI-predicted next regime"
        numeric(4,2)       regime_confidence          "NOT NULL; AI confidence in regime classification (0–1)"
        numeric(4,2)       regime_transition_prob     "Probability of regime change in next period (0–1)"
        int                regime_duration_days       "Current regime duration in days"
        int                regime_duration_estimate   "Estimated remaining duration of current regime (hours)"

        -- 📊 Regime Strength & Quality Metrics
        numeric(6,2)       trend_strength_score       "AI trend strength assessment (0–1)"
        numeric(6,2)       regime_quality_score       "Quality/clarity of current regime (0–1)"
        numeric(6,2)       volatility_regime_score    "Volatility assessment: low(0-0.3), medium(0.3-0.7), high(0.7-1)"
        numeric(6,2)       momentum_alignment_score   "Alignment between price and momentum indicators (0–1)"
        
        -- 🔄 Market Structure Analysis
        boolean            trend_intact               "Whether primary trend remains intact"
        boolean            structure_break            "TRUE if market structure was broken"
        varchar(20)        structure_change_type      "Type of structure change: 'higher_high', 'lower_low', 'consolidation', 'reversal'"
        numeric(8,4)       structure_strength         "Strength of current market structure (0–1)"

        -- 📈 Technical Breakout & Pattern Analysis
        boolean            breakout_signal            "TRUE if price broke key technical level"
        varchar(30)        breakout_type              "Type of breakout: 'resistance', 'support', 'trendline', 'pattern', 'range'"
        numeric(18,8)      breakout_level             "Price level of the breakout"
        boolean            volume_confirmation        "TRUE if breakout volume ≥ threshold above average"
        numeric(6,2)       volume_surge_ratio         "Volume surge ratio vs average (1.0 = average)"
        boolean            retest_confirmation        "TRUE if breakout level was retested successfully"
        numeric(6,2)       volatility_expansion_score "Volatility expansion during breakout (0–1)"

        -- 📊 Multi-Timeframe Analysis
        jsonb              timeframe_alignment        "Cross-timeframe regime alignment:
                                                    {
                                                        '1h': {'regime': 'Bull', 'strength': 0.8, 'confidence': 0.9},
                                                        '4h': {'regime': 'Bull', 'strength': 0.9, 'confidence': 0.85},
                                                        '1d': {'regime': 'Sideways', 'strength': 0.4, 'confidence': 0.7},
                                                        'alignment_score': 0.75
                                                    }"
        
        boolean            multi_timeframe_agreement  "TRUE if multiple timeframes agree on regime"
        numeric(4,2)       timeframe_consensus_score  "Consensus strength across timeframes (0–1)"

        -- 🔑 AI-Detected Key Levels & Zones
        jsonb              key_levels                 "Enhanced key levels with context:
                                                    [
                                                        {
                                                            'type': 'support',
                                                            'value': 64200,
                                                            'strength': 0.85,
                                                            'tests_count': 3,
                                                            'last_test': '2025-09-28T14:30:00Z',
                                                            'distance_pct': 2.1,
                                                            'volume_at_level': 'high'
                                                        },
                                                        {
                                                            'type': 'dynamic_trendline',
                                                            'equation': 'y = 1.2x + 60000',
                                                            'points': [
                                                                {'time': '2025-09-20T12:00:00Z', 'price': 65500},
                                                                {'time': '2025-09-25T16:00:00Z', 'price': 66700}
                                                            ],
                                                            'strength': 0.78,
                                                            'slope': 'ascending'
                                                        }
                                                    ]"

        -- 💡 Market Psychology & Sentiment Integration
        varchar(20)        sentiment_regime           "Sentiment-based regime: 'extreme_fear', 'fear', 'neutral', 'greed', 'extreme_greed'"
        numeric(6,2)       fear_greed_impact          "Impact of fear/greed on regime (0–1)"
        boolean            sentiment_regime_conflict  "TRUE if price and sentiment regimes conflict"
        numeric(4,2)       psychological_level_score  "Proximity to psychological levels impact (0–1)"

        -- 🌊 Flow & Liquidity Analysis
        varchar(20)        liquidity_regime           "Liquidity environment: 'abundant', 'normal', 'tight', 'stressed'"
        numeric(6,2)       institutional_flow_score   "Institutional flow impact on regime (0–1)"
        numeric(6,2)       retail_participation_score "Retail participation level (0–1)"
        boolean            whale_activity_influence   "TRUE if whale activity significantly influenced regime"

        -- � Intermarket & Macro Context
        varchar(20)        macro_regime_alignment     "Alignment with macro environment: 'supportive', 'neutral', 'headwind'"
        numeric(4,2)       correlation_stability      "Stability of crypto-traditional market correlations (0–1)"
        boolean            risk_on_off_regime         "TRUE if in clear risk-on/risk-off regime"
        varchar(15)        global_risk_appetite       "Global risk appetite: 'risk_on', 'risk_off', 'mixed', 'transitioning'"

        -- 🎚️ Regime Transition Signals
        jsonb              transition_indicators      "Early regime transition signals:
                                                    {
                                                        'divergence_signals': [
                                                            {'indicator': 'RSI', 'type': 'bearish_divergence', 'strength': 0.7},
                                                            {'indicator': 'volume', 'type': 'declining_on_rally', 'strength': 0.6}
                                                        ],
                                                        'structural_signals': [
                                                            {'type': 'failing_to_make_higher_high', 'strength': 0.8}
                                                        ],
                                                        'sentiment_signals': [
                                                            {'type': 'extreme_optimism', 'reading': 85, 'strength': 0.9}
                                                        ],
                                                        'transition_probability': 0.35
                                                    }"

        -- 🎯 Trading & Investment Implications
        varchar(20)        recommended_strategy       "Recommended strategy: 'trend_following', 'mean_reversion', 'breakout', 'range_trading', 'defensive'"
        numeric(4,2)       risk_adjustment_factor     "Suggested risk adjustment (0.5=half risk, 2.0=double risk)"
        varchar(20)        position_sizing_guidance   "Position sizing: 'conservative', 'normal', 'aggressive', 'maximum'"
        jsonb              sector_regime_impact       "Impact on different sectors:
                                                    {
                                                        'defi': {'impact': 'positive', 'strength': 0.8},
                                                        'l1': {'impact': 'neutral', 'strength': 0.3},
                                                        'nft': {'impact': 'negative', 'strength': 0.6}
                                                    }"

        -- 🤖 Enhanced AI Meta-Signals
        numeric(4,2)       ai_confidence_score        "Overall AI model confidence (0–1)"
        numeric(4,2)       signal_agreement_score     "Ensemble agreement across different AI signals (0–1)"
        numeric(4,2)       prediction_stability       "Stability of predictions over recent periods (0–1)"
        varchar(20)        model_performance_rating   "Recent model performance: 'excellent', 'good', 'average', 'poor'"
        
        -- 📊 Historical Context & Comparison
        varchar(30)        historical_analogue        "Similar historical market period"
        numeric(4,2)       historical_similarity      "Similarity to historical pattern (0–1)"
        jsonb              regime_statistics          "Statistical analysis of current regime:
                                                    {
                                                        'typical_duration_days': 45,
                                                        'current_duration_days': 23,
                                                        'typical_volatility': 0.65,
                                                        'current_volatility': 0.72,
                                                        'success_rate_historical': 0.68
                                                    }"

        -- � Quality Assurance & Validation
        boolean            analysis_validated         "NOT NULL; default: false; Whether analysis passed validation checks"
        jsonb              validation_flags           "Quality flags and warnings:
                                                    {
                                                        'data_quality_score': 0.95,
                                                        'completeness_check': true,
                                                        'outlier_flags': [],
                                                        'confidence_warnings': [],
                                                        'model_health_score': 0.92
                                                    }"
        
        varchar(50)        analysis_version           "Version of analysis pipeline used"
        text               analyst_notes              "Manual analyst notes and observations"
        
        -- 📝 Comprehensive Analysis Rationale
        jsonb              analysis_data              "Comprehensive structured analysis:
                                                    {
                                                        'primary_signals': [
                                                            'BTC above MA200 with strong volume',
                                                            'RSI showing bullish momentum',
                                                            'Fear & Greed index in greed territory'
                                                        ],
                                                        'supporting_evidence': [
                                                            'TOTAL and TOTAL2 rising consistently',
                                                            'BTC dominance declining (altcoin favorable)',
                                                            'DXY not in aggressive uptrend'
                                                        ],
                                                        'risk_factors': [
                                                            'High leverage in system',
                                                            'Approaching key resistance zone'
                                                        ],
                                                        'key_levels_to_watch': [64200, 67000, 70000],
                                                        'invalidation_scenario': 'Break below 62000 with volume',
                                                        'strategic_implications': 'Favor crypto exposure, moderate altcoin allocation',
                                                        'next_review_trigger': 'price_action_at_67000_resistance'
                                                    }"

        timestamp          created_at                 "NOT NULL; default: Now(); Record creation timestamp"
        timestamp          updated_at                 "NOT NULL; default: Now(); Last update timestamp"
        
        -- 📋 Enhanced Constraints & Validations
        CONSTRAINT chk_regime_confidence CHECK (regime_confidence BETWEEN 0 AND 1)
        CONSTRAINT chk_transition_prob CHECK (regime_transition_prob IS NULL OR regime_transition_prob BETWEEN 0 AND 1)
        CONSTRAINT chk_trend_strength CHECK (trend_strength_score IS NULL OR trend_strength_score BETWEEN 0 AND 1)
        CONSTRAINT chk_risk_adjustment CHECK (risk_adjustment_factor IS NULL OR risk_adjustment_factor BETWEEN 0.1 AND 5.0)
        CONSTRAINT chk_regime_duration_positive CHECK (regime_duration_days IS NULL OR regime_duration_days >= 0)
    }


    %% Layer 2: Sector Analysis
    sectors {
        int id PK "NOT NULL; Primary key for crypto sectors"
        varchar coingecko_id UK "NOT NULL; Unique Coingecko sector ID"
        varchar name UK "NOT NULL; Unique sector name (DeFi, Gaming, Infrastructure, etc.)"
        text description "NOT NULL; Detailed description of the sector"
        numeric(30,2) market_cap "Total market capitalization of all coins in this sector (USD)"
        numeric(30,2) market_cap_change_24h "24h change in sector market cap (USD)"
        numeric(30,2) volume_24h "24h trading volume of the sector (USD)"
        jsonb metrics_details "7 records for ohlv in 7d timeframe and so on.. "
        int[] top_3_coins_id "[bitcoin's PK, ethereum's PK, binancecoin's PK]",
        boolean is_active "Whether this sector is actively tracked"
        timestamp created_at "NOT NULL; default: Now(); Record creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last update timestamp"
    }

    sector_history {
        int id PK "NOT NULL; Primary key for sector history data"
        int sector_id FK "NOT NULL; Foreign key linking to sectors table"
        varchar timeframe "Timeframe of the record (e.g., '1m', '5m', '1h', '1d')"
        numeric(30,2) market_cap "Total market capitalization of the sector (USD)"
        numeric(30,2) volume_24h "24h trading volume of the sector (USD)"
        jsonb technical_indicators "Calculated technical indicators (RSI, MACD, etc.).
                                    NULL if not stored for this asset/timeframe.
                                    Example:
                                    {
                                    'RSI': 56.23,
                                    'MACD': { 'value': -12.45, 'signal': -10.32, 'histogram': -2.13 },
                                    'SMA': { '50': 45000.12, '200': 42000.55 },
                                    'EMA': { '20': 45500.78, '100': 43000.44 }
                                    }"
        timestamp candle_time "Timestamp of the candle in UTC."
        timestamp created_at "NOT NULL; default: Now(); Record creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last data update timestamp"
    }

    sector_mapping {
        int id PK "NOT NULL; Primary key for crypto-sector mapping"
        int asset_id FK "NOT NULL; Foreign key linking to assets table"
        int sector_id FK "NOT NULL; Foreign key linking to sectors table"
        boolean is_primary_sector "NOT NULL; default: false; Whether this is the primary sector for the crypto"
        timestamp created_at "NOT NULL; default: Now(); Record creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last update timestamp"
    }

    ai_sector_analysis {
        int id PK "NOT NULL; Primary key for sector analysis record"
        int metrics_snapshot_id FK "NOT NULL; Foreign key linking to metrics_snapshot.id"
        int ai_model_id FK "NOT NULL; Foreign key linking to ai_models.id"
        int sector_id FK "NOT NULL; Foreign key linking to sectors.id (DeFi, L1, L2, NFT, AI, RWA, ...)"

        varchar timeframe "Timeframe of the record (e.g., '1d', '7d', '30d')"
        timestamp candle_time "Timestamp of the candle in UTC."
        timestamp analysis_time "NOT NULL; Timestamp when this analysis was executed"

        -- 📈 Sector performance & returns
        numeric(12,2) sector_market_cap "Total market capitalization of the sector (USD)"
        numeric(12,2) sector_volume_24h "24h trading volume of the sector (USD)"
        numeric(6,2) sector_dominance_pct "Sector share of the total crypto market (%)"
        numeric(6,2) performance_24h_pct "Sector return in the last 24 hours (%)"
        numeric(6,2) performance_7d_pct "Sector return in the last 7 days (%)"
        numeric(6,2) performance_30d_pct "Sector return in the last 30 days (%)"

        -- 🔄 Capital rotation & flows
        numeric(6,2) rotation_inflow_score "AI score for capital inflow into the sector (0–1)"
        numeric(6,2) rotation_outflow_score "AI score for capital outflow from the sector (0–1)"
        numeric(6,2) relative_strength_score "Relative strength of the sector vs. BTC or total market (0–1)"

        -- 💧 Liquidity & volatility
        numeric(6,2) liquidity_score "Liquidity depth score (0–1)"
        numeric(6,2) volatility_score "Volatility score (0–1)"

        -- 📊 Correlation & narratives
        numeric(6,2) correlation_with_btc "Correlation coefficient with BTC returns"
        numeric(6,2) correlation_with_eth "Correlation coefficient with ETH returns"
        varchar(50) narrative_tag[] "Array of dominant narrative: 'AI', 'RWA', 'DeFi Summer', 'NFT Boom', etc."

        -- 🏦 Institutional & fundamental metrics
        numeric(12,2) institutional_inflow "Estimated institutional inflows into the sector (USD)"
        numeric(12,2) tvl_total "Total Value Locked (TVL) in the sector (USD)"
        int active_users "Number of active users in the sector"
        int active_protocols "Number of active protocols in the sector"

        -- 🔑 AI key signals
        jsonb key_signals "AI-detected key signals:
            [
                {type:'momentum_leader', value:true},
                {type:'liquidity_surge', value:0.78},
                {type:'rotation_inflow', value:0.85}
            ]"

        -- 🤖 AI meta-signals
        varchar(20) ai_sector_outlook "AI outlook: 'Bullish','Bearish','Neutral'"
        numeric(4,2) ai_confidence_score "AI model confidence score (0–1)"
        numeric(4,2) signal_agreement_score "Agreement level across signals (0–1)"
        int outlook_duration_estimate "Estimated duration of current outlook (hours)"

        -- 📝 Analyst notes & rationale
        jsonb analysis_data "Notes and rationale:
            {
                'rationale': [
                    'DeFi TVL +15% in the past week',
                    'Uniswap trading volume increased by 20%',
                    'DeFi market cap share rose from 12% to 14%'
                ],
                'notes': 'Slightly higher allocation to DeFi short-term, medium risk.'
            }"

        timestamp created_at "NOT NULL; default: Now(); Record creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last update timestamp"
    }

    ai_cross_sector_analysis {
        int id PK "NOT NULL; Primary key for cross-sector analysis record"
        int metrics_snapshot_id FK "NOT NULL; Foreign key linking to metrics_snapshot.id"
        int ai_model_id FK "NOT NULL; Foreign key linking to ai_models.id"

        varchar timeframe "Timeframe of the record (e.g., '1d', '7d', '30d')"
        timestamp candle_time "Timestamp of the candle in UTC."
        timestamp analysis_time "NOT NULL; Timestamp when this cross-sector analysis was executed"

        -- 🔄 Sector rotation & comparative flows
        jsonb sector_rotation_flows "Matrix of capital flows between sectors:
            {
            'DeFi→AI': 0.72,
            'AI→NFT': 0.15,
            'L1→RWA': 0.60
            }"

        jsonb sector_performance_ranking "Ranking of sectors by performance:
            [
            {sector:'AI', return_7d:12.5, rank:1},
            {sector:'DeFi', return_7d:8.2, rank:2},
            {sector:'NFT', return_7d:-3.1, rank:5}
            ]"

        -- 📈 Liquidity & volatility comparison
        jsonb liquidity_comparison "Liquidity comparison across sectors:
            { 'AI':0.85, 'DeFi':0.78, 'NFT':0.40 }"
        jsonb volatility_comparison "Volatility comparison across sectors:
            { 'AI':0.65, 'DeFi':0.55, 'NFT':0.90 }"

        -- 🏦 Market share & dominance
        jsonb dominance_distribution "Market share of each sector:
            { 'BTC':48.2, 'DeFi':14.1, 'AI':6.5, 'NFT':2.3 }"

        -- 🔍 Correlation between sectors
        jsonb correlation_matrix "Correlation matrix of returns between sectors:
            {
            'DeFi': {'AI':0.72,'NFT':0.55},
            'AI':   {'DeFi':0.72,'NFT':0.40}
            }"

        -- ⏳ Narrative trends
        jsonb narrative_trends "Dominant narratives across sectors:
            [
            {sector:'AI', narrative:'AI Agents', strength:0.88},
            {sector:'RWA', narrative:'Tokenized Treasuries', strength:0.75}
            ]"

        -- ⚖️ Risk/Reward comparison
        jsonb risk_reward_map "Risk vs. reward comparison across sectors:
            [
            {sector:'AI', risk:0.8, reward:0.9},
            {sector:'DeFi', risk:0.6, reward:0.7}
            ]"

        -- 🤖 AI meta-signals
        varchar(20) ai_market_outlook "AI outlook for the overall crypto market: 'Bullish','Bearish','Neutral'"
        numeric(4,2) ai_confidence_score "AI model confidence score (0–1)"
        numeric(4,2) signal_agreement_score "Agreement level across AI signals (0–1)"
        int outlook_duration_estimate "Estimated duration of current outlook (hours)"

        -- 📝 Analyst notes & rationale
        jsonb analysis_data "Notes and rationale:
            {
            'rationale': [
                'Capital rotating from L1 into DeFi and AI',
                'NFTs show low correlation with other sectors',
                'RWA attracting institutional inflows'
            ],
            'notes': 'Portfolio allocation: overweight AI and DeFi, underweight NFT'
            }"

        timestamp created_at "NOT NULL; default: Now(); Record creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last update timestamp"
    }

    sector_rotation_flows {
        int id PK   "NOT NULL; Primary key for sector rotation flow record"
        int ai_cross_sector_analysis_id FK "NOT NULL; Link to ai_cross_sector_analysis.id"
        int from_sector_id FK "NOT NULL; Source sector"
        int to_sector_id FK "NOT NULL; Destination sector"
        numeric(6,2) score "NOT NULL; Rotation score (0–1)"
        timestamp created_at "NOT NULL; default: Now(); Record creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last update timestamp"
    }

    %% Layer 3: Asset Selection
    watchlists {
        int id PK "NOT NULL; Primary key for watchlist identification"
        varchar name "NOT NULL; Watchlist name for user identification"
        text description "Detailed description of watchlist purpose"
        int user_id FK "NOT NULL; Foreign key linking to users table (null for default)"
        varchar watchlist_type "NOT NULL; default/personal; Type of watchlist: system default or user personal"
        boolean is_active "NOT NULL; default: true; Whether this watchlist is currently active"
        boolean is_public "Whether this watchlist can be shared (future feature)"
        int max_assets "Maximum number of assets allowed in this watchlist"
        int sort_order "Order for displaying multiple watchlists"
        timestamp created_at "NOT NULL; default: Now(); Watchlist creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last modification timestamp"
    }

    watchlist_assets {
        int id PK "NOT NULL; Primary key for watchlist asset entries"
        int watchlist_id FK "NOT NULL; Foreign key linking to watchlists table"
        int asset_id FK "NOT NULL; Foreign key linking to assets table"
        varchar position_type "NOT NULL; Type of position type to watch: long, short"
        int sort_order "NOT NULL; Position/rank within the watchlist for ordering"
        text notes "User or admin notes about this asset inclusion"
        boolean is_active "NOT NULL; Whether this asset is currently active in the watchlist"
        int added_by FK "NOT NULL; User who added this asset (admin or user)"
        int last_modified_by FK "NOT NULL; User who last modified this asset entry"
        timestamp created_at "NOT NULL; default: Now(); When this asset was added to the watchlist"
        timestamp updated_at "NOT NULL; default: Now(); Last update timestamp"
    }

    ai_watchlist_analysis{
        int id PK "NOT NULL; Primary key for AI watchlist analysis record"
        int watchlist_id FK "NOT NULL; Foreign key linking to watchlists.id"
        int metrics_snapshot_id FK "NOT NULL; Foreign key linking to metrics_snapshot.id"
        int ai_model_id FK "NOT NULL; Foreign key linking to ai_models.id"

        varchar timeframe "Timeframe of the record (e.g., '1d', '7d', '30d')"
        timestamp candle_time "Timestamp of the candle in UTC."
        timestamp analysis_time "NOT NULL; Timestamp when this analysis was executed"

        -- 📊 Asset scoring & ranking
        jsonb asset_scores "Array of assets with AI scores and rankings:
            [
                {asset_id:1, score:0.92, rank:1, signal_count:3, avg_signal_quality:0.85},
                {asset_id:2, score:0.85, rank:2, signal_count:1, avg_signal_quality:0.70}
            ]"

        -- 🔑 Key signals per asset
        jsonb key_signals "Matrix of key signals detected by AI for each asset:
            {
                '1': {momentum:0.9, volume_spike:true, breakout:true, active_signals:[123,124]},
                '2': {momentum:0.7, volume_spike:false, breakout:false, active_signals:[125]}
            }"

        -- 🎯 Generated trading signals
        jsonb generated_signals "Trading signals generated for watchlist assets:
            [
                {signal_id:123, asset_id:1, signal_type:'long', confidence:0.92, entry_price:45000},
                {signal_id:124, asset_id:1, signal_type:'short', confidence:0.78, entry_price:46500},
                {signal_id:125, asset_id:2, signal_type:'long', confidence:0.70, entry_price:3200}
            ]"

        -- 🤖 AI meta-signals
        varchar(20) ai_watchlist_outlook "AI outlook for the watchlist: 'Bullish','Bearish','Neutral'"
        numeric(4,2) ai_confidence_score "AI model confidence score (0–1)"
        numeric(4,2) signal_agreement_score "Agreement level across signals (0–1)"
        int outlook_duration_estimate "Estimated duration of current outlook (hours)"

        -- 📝 Analyst notes & rationale
        jsonb analysis_data "Notes and rationale:
            {
                'rationale': [
                    'Top-ranked assets show strong momentum and volume',
                    'Several assets breaking out of key resistance levels'
                ],
                'notes': 'Consider adding top 3 ranked assets to portfolio.'
            }"

        timestamp created_at "NOT NULL; default: Now(); Record creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last update timestamp"
    }

    portfolios {
        int id PK
        int user_id FK "NOT NULL; REFERENCES users(id) ON DELETE CASCADE"
        boolean is_active "NOT NULL; default: true; Whether this watchlist is currently active"
        boolean is_public "Whether this watchlist can be shared (future feature)"
        timestamp created_at "NOT NULL; default: Now(); Record creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last update timestamp"
    }

    portfolio_assets {
        int id PK "NOT NULL; Primary key for portfolio asset entries"
        int portfolio_id FK "NOT NULL; Foreign key linking to portfolios table"
        int asset_id FK "NOT NULL; Foreign key linking to assets table"
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
        text notes "additional notes"
        int sort_order "NOT NULL; Position/rank within the portfolio for ordering"
        boolean is_active "NOT NULL; Whether this asset is currently active in the portfolio"
        int added_by FK "NOT NULL; User who added this asset (admin or user)"
        int last_modified_by FK "NOT NULL; User who last modified this asset entry"
        timestamp created_at "NOT NULL; default: Now(); When this asset was added to the portfolio"
        timestamp updated_at "NOT NULL; default: Now(); Last update timestamp"
    }

    ai_portfolio_analysis {
        int id PK "NOT NULL; Primary key for AI portfolio analysis record"
        int portfolio_id FK "NOT NULL; Foreign key linking to portfolios.id"
        int metrics_snapshot_id FK "NOT NULL; Foreign key linking to metrics_snapshot.id"
        int ai_model_id FK "NOT NULL; Foreign key linking to ai_models.id"

        varchar timeframe "Timeframe of the record (e.g., '1d', '7d', '30d')"
        timestamp candle_time "Timestamp of the candle in UTC."
        timestamp analysis_time "NOT NULL; Timestamp when this analysis was executed"

        -- 📊 Portfolio-level metrics
        numeric total_portfolio_value_usd "Current total portfolio value in USD"
        numeric total_pnl_pct "Total portfolio unrealized P&L percentage"
        numeric total_pnl_usd "Total portfolio unrealized P&L in USD"
        numeric portfolio_risk_score "Overall portfolio risk assessment (0–1, 1 = highest risk)"
        numeric diversification_score "Portfolio diversification score (0–1, 1 = well diversified)"
        numeric concentration_risk "Portfolio concentration risk (0–1, 1 = highly concentrated)"

        -- 🎯 Asset allocation analysis
        jsonb current_allocation "Current allocation breakdown:
            {
                'by_sector': {'DeFi': 35.5, 'L1': 40.2, 'AI': 15.3, 'Stables': 9.0},
                'by_risk': {'high': 25.5, 'medium': 60.2, 'low': 14.3},
                'by_asset_type': {'crypto': 91.0, 'stablecoin': 9.0}
            }"
        
        jsonb optimal_allocation "AI-suggested optimal allocation:
            {
                'by_sector': {'DeFi': 30.0, 'L1': 35.0, 'AI': 20.0, 'Stables': 15.0},
                'by_risk': {'high': 20.0, 'medium': 65.0, 'low': 15.0}
            }"

        jsonb allocation_deviation "Deviation from optimal allocation:
            {
                'DeFi': +5.5,
                'L1': +5.2,
                'AI': -4.7,
                'Stables': -6.0
            }"

        -- � Risk & correlation analysis
        numeric portfolio_beta "Portfolio beta relative to BTC (market correlation)"
        numeric portfolio_volatility "Portfolio volatility score (0–1)"
        numeric sharpe_ratio "Portfolio Sharpe ratio (risk-adjusted return)"
        numeric max_drawdown_pct "Maximum drawdown percentage in analysis period"

        jsonb correlation_matrix "Asset correlation analysis within portfolio:
            {
                'high_correlation_pairs': [
                    {'asset1': 'BTC', 'asset2': 'ETH', 'correlation': 0.85},
                    {'asset1': 'UNI', 'asset2': 'AAVE', 'correlation': 0.78}
                ],
                'diversification_benefits': 0.65
            }"

        -- 🚨 Portfolio-level recommendations
        boolean rebalance_needed "Whether portfolio rebalancing is recommended"
        varchar overall_action "Overall portfolio action: 'hold', 'reduce_risk', 'increase_exposure', 'rebalance', 'defensive'"
        
        jsonb rebalancing_suggestions "Specific rebalancing recommendations:
            [
                {action: 'reduce', asset: 'BTC', current_pct: 45.2, target_pct: 40.0, reason: 'overweight', related_signals:[126,127]},
                {action: 'increase', asset: 'stablecoins', current_pct: 9.0, target_pct: 15.0, reason: 'risk_management'},
                {action: 'add', asset: 'AI_tokens', current_pct: 15.3, target_pct: 20.0, reason: 'sector_rotation', suggested_signals:[128,129]}
            ]"

        -- 🎯 Portfolio-related trading signals
        jsonb portfolio_signals "Trading signals relevant to current portfolio:
            {
                'exit_signals': [
                    {signal_id:126, asset_id:1, type:'partial_exit', reason:'rebalance', urgency:'medium'}
                ],
                'entry_signals': [
                    {signal_id:128, asset_id:15, type:'new_position', reason:'sector_rotation', allocation_pct:5.0},
                    {signal_id:129, asset_id:16, type:'add_position', reason:'dca_opportunity', allocation_pct:3.0}
                ],
                'adjustment_signals': [
                    {signal_id:127, asset_id:1, type:'reduce_position', current_weight:45.2, target_weight:40.0}
                ]
            }"

        -- 💰 Performance & efficiency analysis
        numeric portfolio_efficiency_score "Portfolio efficiency vs optimal frontier (0–1)"
        numeric total_fees_impact_pct "Impact of trading fees on portfolio performance (%)"
        numeric opportunity_cost_score "Opportunity cost of current allocation (0–1)"

        -- 🔄 Rotation & timing analysis
        jsonb sector_rotation_impact "Impact of sector rotation on portfolio:
            {
                'benefiting_sectors': ['AI', 'RWA'],
                'underperforming_sectors': ['NFT', 'Gaming'],
                'rotation_score': 0.72
            }"

        varchar portfolio_cycle_phase "Portfolio position in market cycle: 'accumulation', 'markup', 'distribution', 'decline'"
        numeric cycle_adjustment_score "How well portfolio is positioned for current cycle (0–1)"

        -- 🤖 AI meta-signals
        varchar(20) ai_portfolio_outlook "AI outlook for the portfolio: 'Bullish','Bearish','Neutral'"
        numeric(4,2) ai_confidence_score "AI model confidence score (0–1)"
        numeric(4,2) signal_agreement_score "Agreement level across signals (0–1)"
        int outlook_duration_estimate "Estimated duration of current outlook (hours)"

        -- 📝 Detailed analysis & rationale
        jsonb analysis_data "Comprehensive portfolio analysis:
            {
                'strengths': [
                    'Well diversified across sectors',
                    'Good risk-adjusted returns',
                    'Low correlation between major holdings'
                ],
                'weaknesses': [
                    'Overweight in L1 tokens',
                    'Insufficient stable allocation for current market conditions'
                ],
                'opportunities': [
                    'AI sector showing strong momentum',
                    'DeFi yield opportunities emerging'
                ],
                'threats': [
                    'High correlation during market stress',
                    'Regulatory risks in certain sectors'
                ],
                'action_priorities': [
                    {priority: 1, action: 'Increase stablecoin allocation', timeline: 'immediate'},
                    {priority: 2, action: 'Rebalance sector weights', timeline: '1-2 days'},
                    {priority: 3, action: 'Consider AI sector exposure', timeline: '1 week'}
                ]
            }"

        timestamp created_at "NOT NULL; default: Now(); Record creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last update timestamp"
    }

    ai_portfolio_asset_analysis {
        int id PK "NOT NULL; Primary key for AI trade action analysis record"
        int portfolio_asset_id FK "NOT NULL; Foreign key linking to portfolio_assets.id for open positions"
        int metrics_snapshot_id FK "NOT NULL; Foreign key linking to metrics_snapshot.id"
        int ai_model_id FK "NOT NULL; Foreign key linking to ai_models.id"

        varchar timeframe "Timeframe of the record (e.g., '1m', '5m', '15m', '1h', '4h', '1d')"
        timestamp candle_time "Timestamp of the candle in UTC."
        timestamp analysis_time "NOT NULL; Timestamp when this analysis was executed"

        -- 📊 Current position evaluation
        varchar position_status "Current position status: 'healthy', 'at_risk', 'critical', 'take_profit_zone'"
        numeric current_pnl_pct "Current unrealized P&L percentage"
        numeric risk_level_score "Current risk level assessment (0–1, 1 = highest risk)"
        numeric exit_probability "AI probability that position should be closed (0–1)"
        
        -- 🚨 Action recommendations
        varchar recommended_action "AI recommendation: 'hold', 'partial_exit_25', 'partial_exit_50', 'partial_exit_75', 'full_exit', 'add_position', 'move_sl_to_be', 'tighten_sl', 'extend_tp'"
        varchar urgency_level "Urgency of recommendation: 'low', 'medium', 'high', 'immediate'"
        text recommendation_reason "Detailed reason for the recommendation"
        
        -- 💡 Position management suggestions
        numeric suggested_sl_price "AI-suggested new stop loss price"
        numeric suggested_tp_price "AI-suggested new take profit price"
        numeric suggested_exit_percentage "Suggested percentage of position to exit (0-100)"
        numeric optimal_position_size "AI-calculated optimal position size based on current conditions"

        -- 🔑 Current market signals affecting position
        jsonb current_signals "Real-time signals affecting the position:
            {
                momentum_shift: 'bearish',
                volume_declining: true,
                support_broken: false,
                sentiment_change: 'neutral_to_bearish',
                sector_rotation: 'outflow',
                correlation_breakdown: true
            }"

        -- ⚠️ Risk factors identified
        jsonb risk_factors "Current risk factors identified by AI:
            [
                {factor: 'support_level_approaching', severity: 'medium', price_level: 45000},
                {factor: 'volume_decline', severity: 'low', trend: 'decreasing'},
                {factor: 'sector_weakness', severity: 'high', affected_correlation: 0.8}
            ]"

        -- 📈 Market condition changes
        varchar market_regime_change "Market regime change since entry: 'bull_to_bear', 'bull_to_sideways', 'bear_to_bull', 'no_change'"
        numeric condition_deterioration_score "Score of how much conditions have deteriorated since entry (0–1)"

        -- 🤖 AI meta-signals
        varchar(20) ai_position_outlook "AI outlook for this specific position: 'Bullish','Bearish','Neutral'"
        numeric(4,2) ai_confidence_score "AI model confidence score (0–1)"
        numeric(4,2) signal_agreement_score "Agreement level across signals (0–1)"
        int analysis_horizon_hours "Time horizon for this analysis validity (hours)"

        -- 📝 Detailed analysis & rationale
        jsonb analysis_data "Detailed analysis and rationale:
            {
                'entry_analysis': {
                    'entry_price': 50000,
                    'entry_conditions': ['momentum_strong', 'volume_high', 'breakout_confirmed'],
                    'entry_quality_score': 0.85
                },
                'current_analysis': {
                    'current_price': 48000,
                    'current_conditions': ['momentum_weakening', 'volume_declining', 'support_holding'],
                    'condition_change_score': -0.3
                },
                'rationale': [
                    'Position showing signs of weakness with declining momentum',
                    'Volume profile suggests institutional selling',
                    'Key support at 47500 - consider partial exit if broken'
                ],
                'next_review': '2025-09-30T08:00:00Z'
            }"

        timestamp created_at "NOT NULL; default: Now(); Record creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last update timestamp"
    }


    trade_actions {
        int id PK "NOT NULL; Primary key for trade action records"
        int portfolio_asset_id FK "NOT NULL; REFERENCES portfolio_assets(id)"
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
        int ai_signal_id FK "REFERENCES ai_trading_signals(id); if AI-generated"
        text lesson_learned "lessons learned; mistakes made; what was right; what was wrong"
        text notes "notes for this action"
        timestamp created_at "NOT NULL; default: Now(); Record creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last update timestamp"
    }

    %% Layer 4: Micro Timing
    ai_trading_signals {
        int id PK "NOT NULL; Primary key for trading signal identification"
        int asset_id FK "NOT NULL; Cryptocurrency this signal applies to"
        int ai_model_id FK "NOT NULL; Foreign key linking to ai_models table"
        int metrics_snapshot_id FK "NOT NULL; Link to market conditions at signal generation"
        int watchlist_analysis_id FK "Link to ai_watchlist_analysis if signal generated from watchlist screening"
        int portfolio_analysis_id FK "Link to ai_portfolio_analysis if signal generated for portfolio rebalancing"
        
        varchar signal_type "NOT NULL; long/short; Type of trading signal: long or short position"
        varchar signal_origin "NOT NULL; Origin of signal: 'watchlist_screening', 'portfolio_rebalancing', 'market_opportunity', 'risk_management'"
        varchar signal_quality "NOT NULL; Signal quality: 'high', 'medium', 'low' based on confluence factors"
        numeric confidence_score "NOT NULL; AI confidence in this signal (0–1)"
        
        -- 📈 Entry & Exit Levels
        numeric entry_price "Recommended entry price for the trade"
        numeric target_price "Target price for profit taking"
        numeric stop_loss "Stop loss price for risk management"
        varchar risk_level "Risk level assessment: low, medium, high, extreme"
        numeric risk_reward_ratio "Risk to reward ratio for this trade"
        
        -- 🎯 Signal Context
        jsonb market_context "Market regime context at signal generation:
            {
                'regime': 'Bull',
                'trend_strength': 0.85,
                'volatility_level': 'medium',
                'volume_profile': 'above_average'
            }"
        
        jsonb sector_context "Sector analysis context:
            {
                'sector_performance': 0.78,
                'sector_rotation': 'inflow',
                'relative_strength': 0.82
            }"
        
        jsonb confluence_factors "Technical confluence supporting this signal:
            [
                {factor: 'breakout_confirmed', weight: 0.9},
                {factor: 'volume_spike', weight: 0.8},
                {factor: 'rsi_oversold_recovery', weight: 0.7},
                {factor: 'sector_strength', weight: 0.75}
            ]"
        
        -- 🚨 Risk Management
        jsonb invalidation_criteria "Conditions that would invalidate this signal:
            [
                {condition: 'price_below_45000', severity: 'high'},
                {condition: 'volume_dries_up', severity: 'medium'},
                {condition: 'sector_weakness', severity: 'medium'}
            ]"
        
        jsonb risk_management "Risk management guidelines:
            {
                'max_position_size_pct': 5.0,
                'suggested_leverage': 1.0,
                'stop_loss_type': 'technical',
                'position_sizing_method': 'kelly_criterion'
            }"
        
        -- ⏱️ Timing & Duration
        int time_horizon_hours "Expected time horizon for this signal in hours"
        varchar optimal_entry_timeframe "Best timeframe for entry: '1m', '5m', '15m', '1h'"
        varchar monitoring_timeframe "Recommended timeframe for monitoring: '5m', '15m', '1h', '4h'"
        
        -- 📊 Performance Tracking
        varchar status "Signal status: active, executed, expired, cancelled, invalidated"
        numeric actual_entry_price "Actual entry price if signal was executed"
        numeric max_favorable_excursion "Best price reached after signal generation"
        numeric max_adverse_excursion "Worst price reached after signal generation"
        boolean signal_successful "Whether signal reached target before stop loss"
        
        -- 🎚️ Signal Metadata
        varchar signal_strength "Overall signal strength: 'weak', 'moderate', 'strong', 'very_strong'"
        int confluence_count "Number of confirming technical factors"
        numeric market_correlation "Correlation with overall market sentiment (0–1)"
        
        timestamp expires_at "When this signal expires"
        timestamp invalidated_at "When signal was invalidated (if applicable)"
        timestamp created_at "NOT NULL; default: Now(); When this signal was generated"
        timestamp updated_at "NOT NULL; default: Now(); Last update timestamp"
    }


    %% Actionable Insights & Recommendations   
    recommendations {
        int id PK "NOT NULL; Unique identifier for each recommendation"

        varchar target_entity_type "Type of entity: 'portfolio', 'watchlist', 'asset', 'user', 'strategy'"
        int target_entity_id "ID of the target entity (e.g. portfolios.id, watchlists.id)"

        varchar recommendation_type "Type of recommendation: 'entry', 'exit', 'risk_management', 'rebalance', 'allocation', 'position_sizing', 'learning'"
        varchar recommendation_title "Short title summarizing the recommendation"
        text recommendation_summary "Brief explanation of the recommendation purpose"

        jsonb recommendation_payload "Structured content: suggested_position_size, stop_loss, take_profit, rebalance instructions, etc."

        int ai_regime_analysis_id FK "Reference to ai_regime_analysis that generated this recommendation"
        int ai_sector_analysis_id FK "Reference to ai_sector_analysis that generated this recommendation"
        int ai_cross_sector_analysis_id FK "Reference to ai_cross_sector_analysis that generated this recommendation"
        int ai_trading_signal_id FK "Reference to ai_trading_signals that generated this recommendation"

        varchar status "Lifecycle status: 'pending', 'approved', 'followed', 'implemented', 'ignored', 'expired', 'rejected'"
        varchar priority_level "Importance level: 'low', 'medium', 'high', 'urgent'"

        text user_feedback "Optional user comments or feedback"
        int user_rating "User rating: 1 (poor) to 5 (excellent)"
        jsonb outcome_result "Structured result of recommendation execution (e.g. actual_return, success_score)"

        int reviewed_by FK "ID of admin/user who reviewed the recommendation"
        timestamp reviewed_at "Timestamp when recommendation was reviewed"
        timestamp implemented_at "Timestamp when recommendation was executed"
        timestamp expires_at "Expiration time after which recommendation is no longer valid"
        timestamp created_at "NOT NULL; default: Now(); Timestamp when recommendation was created"
        timestamp updated_at "NOT NULL; default: Now(); Timestamp when recommendation was last updated"
    }

    %% AI Model Management
    ai_models {
        int id PK "NOT NULL; Unique identifier for each model version"
        varchar(100) name "NOT NULL; Model name (shared across versions)"
        varchar(20) version "NOT NULL; Model version (e.g., v1.0.0) — a new record is created in this table for every new version"
        varchar(50) architecture "NOT NULL; Model architecture: lstm, transformer, ensemble, regression, rule_based"
        varchar(20) model_type "NOT NULL; CHECK (model_type IN ('macro','sector','asset','timing')); Model type classification"
        varchar(20) status "NOT NULL; default: 'inactive'; CHECK (status IN ('active','training','inactive','error','deprecated')); Model status"
        
        -- 🎯 Model Configuration & Hyperparameters
        jsonb configuration "Model configuration and hyperparameters:
            {
                'algorithm': 'random_forest',
                'hyperparameters': {
                    'n_estimators': 100,
                    'max_depth': 10,
                    'learning_rate': 0.01
                },
                'preprocessing': {
                    'normalization': 'standard_scaler',
                    'feature_selection': 'mutual_info'
                }
            }"
        
        -- 📊 Performance Metrics (Structured Schema)
        jsonb performance_metrics "Comprehensive performance metrics:
            {
                'classification_metrics': {
                    'accuracy': 0.85,
                    'precision': 0.82,
                    'recall': 0.88,
                    'f1_score': 0.85
                },
                'trading_metrics': {
                    'sharpe_ratio': 1.2,
                    'max_drawdown': 0.15,
                    'win_rate': 0.65,
                    'profit_factor': 1.8,
                    'calmar_ratio': 2.1
                },
                'regression_metrics': {
                    'mse': 0.025,
                    'mae': 0.15,
                    'r2_score': 0.78
                },
                'validation_scores': {
                    'cross_val_score': 0.83,
                    'out_of_sample_score': 0.79
                }
            }"
        
        -- 🔧 Training Configuration
        jsonb training_features "Set of features used for training:
            {
                'technical_indicators': ['rsi_14', 'macd', 'bollinger_bands', 'sma_200'],
                'market_data': ['price', 'volume', 'market_cap'],
                'macro_indicators': ['btc_dominance', 'fear_greed_index', 'dxy'],
                'onchain_metrics': ['whale_flows', 'exchange_flows'],
                'feature_count': 45,
                'feature_importance': {
                    'rsi_14': 0.12,
                    'volume': 0.08,
                    'btc_dominance': 0.15
                }
            }"
        
        jsonb training_data_range "Date range and details of training data:
            {
                'start_date': '2023-01-01T00:00:00Z',
                'end_date': '2024-12-31T23:59:59Z',
                'total_samples': 45000,
                'train_samples': 36000,
                'validation_samples': 4500,
                'test_samples': 4500,
                'data_quality_score': 0.92
            }"
        
        varchar(10) training_data_timeframe "NOT NULL; Time interval between training data points (1m, 5m, 15m, 1h, 4h, 1d)"
        varchar(50) target_variable "NOT NULL; Target variable: price_direction, trend_strength, volatility_regime, regime_change_probability"
        
        -- 📋 Input/Output Schema
        jsonb input_schema "Structure of model input data:
            {
                'required_fields': [
                    {'name': 'price', 'type': 'float', 'range': [0, 1000000]},
                    {'name': 'volume', 'type': 'float', 'range': [0, 10000000000]},
                    {'name': 'rsi_14', 'type': 'float', 'range': [0, 100]}
                ],
                'optional_fields': [
                    {'name': 'sentiment_score', 'type': 'float', 'range': [-1, 1]}
                ],
                'preprocessing_required': true,
                'normalization_method': 'standard_scaler'
            }"
        
        jsonb output_schema "Structure of model output:
            {
                'prediction_type': 'classification',
                'possible_values': ['Bull', 'Bear', 'Sideways'],
                'confidence_score': {'type': 'float', 'range': [0, 1]},
                'additional_outputs': {
                    'regime_strength': {'type': 'float', 'range': [0, 1]},
                    'duration_estimate': {'type': 'int', 'unit': 'hours'}
                }
            }"
        
        -- 🏥 Health Monitoring (Structured Schema)
        jsonb health_status "Comprehensive health monitoring:
            {
                'status': 'healthy',
                'last_health_check': '2025-09-29T10:00:00Z',
                'performance_metrics': {
                    'response_time_ms': 150,
                    'memory_usage_mb': 512,
                    'cpu_usage_pct': 25,
                    'gpu_usage_pct': 45
                },
                'error_metrics': {
                    'error_rate_24h': 0.02,
                    'failed_predictions_24h': 5,
                    'last_error': '2025-09-28T15:30:00Z'
                },
                'data_quality': {
                    'missing_data_pct': 0.01,
                    'outlier_detection_score': 0.95
                },
                'alerts': [
                    {
                        'type': 'warning',
                        'message': 'Slightly elevated response time',
                        'timestamp': '2025-09-29T09:45:00Z'
                    }
                ]
            }"
        
        -- 📝 Model Metadata
        text training_notes "Free-form notes about training process, data sources, and implementation specifics"
        varchar(100) model_file_path "Path to saved model file (for deployment)"
        varchar(50) framework "ML framework used: scikit-learn, tensorflow, pytorch, xgboost"
        varchar(20) deployment_environment "Deployment environment: development, staging, production"
        
        -- ⏰ Timestamps & Activity
        timestamp last_trained "Timestamp when this version was trained"
        timestamp last_prediction "Timestamp of last prediction made by this version"
        timestamp deployed_at "When this model version was deployed to production"
        timestamp deprecated_at "When this model version was deprecated"
        
        -- 🔄 Model Lifecycle
        boolean is_active "NOT NULL; default: false; Indicates if this version is currently deployed"
        int prediction_count "NOT NULL; default: 0; Total number of predictions made by this version"
        numeric model_size_mb "Model file size in megabytes"
        int training_duration_minutes "Total training time in minutes"
        
        -- 🎚️ Business Constraints
        numeric min_confidence_threshold "NOT NULL; default: 0.5; Minimum confidence score for valid predictions"
        int max_predictions_per_hour "Rate limiting for predictions per hour"
        boolean requires_manual_approval "Whether predictions need manual review before use"
        
        timestamp created_at "NOT NULL; default: Now(); Record creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last record update timestamp"
        
        -- 📋 Constraints & Indexes
        CONSTRAINT unique_active_model UNIQUE (name, model_type) WHERE is_active = true
        CONSTRAINT chk_confidence_threshold CHECK (min_confidence_threshold BETWEEN 0 AND 1)
        CONSTRAINT chk_prediction_count_positive CHECK (prediction_count >= 0)
    }

    model_performance {
        int id PK "NOT NULL; Unique identifier for evaluation record"
        int model_id FK "NOT NULL; Foreign key to ai_models (specific model version)"
        int source_job_id FK "Foreign key to model_jobs - links evaluation to the job that triggered it"
        
        -- � NOTE: Configuration, timing, and job details are accessed via source_job_id relationship
        -- Use JOIN with model_jobs to get: job_params, started_at, completed_at, execution_time, etc.
        
        -- �📊 Evaluation Metadata (Non-redundant with model_jobs)
        timestamp evaluation_date "NOT NULL; When this evaluation was performed"
        varchar(50) evaluation_type "NOT NULL; Type: 'backtesting', 'forward_testing', 'cross_validation', 'live_performance', 'job_triggered'"
        
        -- 📈 Core Performance Metrics (کلیدی‌ترین metrics)
        numeric(8,6) accuracy "Classification accuracy (0-1)"
        numeric(8,6) precision_score "Precision score (0-1)"
        numeric(8,6) recall "Recall score (0-1)"
        numeric(8,6) f1_score "F1 score (0-1)"
        
        -- 💰 Trading Performance (مهم‌ترین برای crypto)
        numeric(8,6) win_rate "Win rate percentage (0-1)"
        numeric(10,4) profit_factor "Profit factor (gross profit / gross loss)"
        numeric(10,6) sharpe_ratio "Risk-adjusted returns"
        numeric(8,6) max_drawdown "Maximum drawdown percentage (0-1)"
        numeric(10,4) total_return "Total return percentage"
        
        -- � Statistical Metrics
        numeric mse "Mean Squared Error"
        numeric mae "Mean Absolute Error"
        numeric r2_score "R-squared score"
        
        -- 🔍 Evaluation Quality & Details
        int sample_count "Number of samples/predictions evaluated"
        numeric(6,4) confidence_avg "Average confidence score of predictions"
        numeric(6,4) confidence_std "Standard deviation of confidence scores"
        int true_positives "Count of true positive predictions"
        int false_positives "Count of false positive predictions"
        int true_negatives "Count of true negative predictions"
        int false_negatives "Count of false negative predictions"
        
        -- 📊 Market Condition Context
        varchar(20) market_regime "Market regime during evaluation: 'bull', 'bear', 'sideways', 'volatile'"
        numeric(8,6) market_volatility "Average market volatility during period (0-1)"
        numeric(10,4) btc_correlation "Correlation with BTC during evaluation period"
        
        -- 📝 Evaluation-Specific Details (Not available in model_jobs)
        jsonb detailed_metrics "Detailed breakdown of all computed metrics and intermediate results"
        jsonb evaluation_metadata "Evaluation-specific metadata (test dataset info, evaluation conditions, etc.)"
        
        -- 🎯 Pass/Fail Status & Grading
        boolean meets_threshold "Whether performance meets minimum business thresholds"
        varchar(2) performance_grade "Performance grade: 'A', 'B', 'C', 'D', 'F'"
        numeric(6,4) overall_score "Computed overall performance score (0-1)"
        varchar(20) evaluation_status "Status: 'completed', 'failed', 'partial', 'invalidated'"
        
        -- 📋 Analysis & Notes
        text evaluation_notes "Detailed notes about this evaluation run"
        text recommendations "Recommendations based on evaluation results"
        
        timestamp created_at "NOT NULL; default: Now(); Evaluation record creation time"
        
        -- � High-Performance Indexes
        INDEX idx_perf_model_recent (model_id, evaluation_date DESC)
        INDEX idx_perf_grade_threshold (performance_grade, meets_min_threshold, composite_score DESC)
        INDEX idx_perf_trading_metrics (win_rate DESC, sharpe_ratio DESC, profit_factor DESC) WHERE meets_min_threshold = true
        INDEX idx_perf_job_source (source_job_id, evaluation_date DESC) WHERE source_job_id IS NOT NULL
        INDEX idx_perf_trigger_status (evaluation_trigger, evaluation_status, evaluation_date DESC)
        INDEX idx_perf_quality_samples (total_samples DESC, valid_predictions DESC) WHERE evaluation_status = 'completed'
        
        -- ✅ Comprehensive Validation Constraints
        CONSTRAINT chk_perf_ml_metrics CHECK (
            accuracy IS NULL OR (accuracy >= 0 AND accuracy <= 1) AND
            precision_score IS NULL OR (precision_score >= 0 AND precision_score <= 1) AND
            recall IS NULL OR (recall >= 0 AND recall <= 1) AND
            f1_score IS NULL OR (f1_score >= 0 AND f1_score <= 1) AND
            auc_score IS NULL OR (auc_score >= 0 AND auc_score <= 1)
        )
        CONSTRAINT chk_perf_trading_metrics CHECK (
            win_rate IS NULL OR (win_rate >= 0 AND win_rate <= 1) AND
            max_drawdown IS NULL OR (max_drawdown >= 0 AND max_drawdown <= 1) AND
            profit_factor IS NULL OR profit_factor >= 0
        )
        CONSTRAINT chk_perf_statistical_metrics CHECK (
            r2_score IS NULL OR (r2_score >= -1 AND r2_score <= 1) AND
            mse IS NULL OR mse >= 0 AND
            mae IS NULL OR mae >= 0
        )
        CONSTRAINT chk_perf_sample_counts CHECK (
            total_samples IS NULL OR total_samples > 0 AND
            valid_predictions IS NULL OR (valid_predictions >= 0 AND valid_predictions <= total_samples)
        )
        CONSTRAINT chk_perf_confidence_metrics CHECK (
            confidence_mean IS NULL OR (confidence_mean >= 0 AND confidence_mean <= 1) AND
            confidence_std IS NULL OR confidence_std >= 0
        )
        CONSTRAINT chk_perf_composite_score CHECK (composite_score IS NULL OR (composite_score >= 0 AND composite_score <= 1))
        CONSTRAINT chk_perf_market_volatility CHECK (market_volatility IS NULL OR (market_volatility >= 0 AND market_volatility <= 1))
        
        -- 🏷️ Enum Value Constraints
        CONSTRAINT chk_perf_evaluation_trigger CHECK (evaluation_trigger IN ('job_completion', 'manual', 'scheduled', 'api_request'))
        CONSTRAINT chk_perf_grade_valid CHECK (performance_grade IS NULL OR performance_grade IN ('A', 'B', 'C', 'D', 'F'))
        CONSTRAINT chk_perf_market_regime CHECK (market_regime IS NULL OR market_regime IN ('bull', 'bear', 'sideways', 'volatile'))
        CONSTRAINT chk_perf_status_valid CHECK (evaluation_status IN ('completed', 'failed', 'partial', 'invalidated'))
    }

    %% 🔗 OPTIMIZED DESIGN: model_jobs ↔ model_performance
    %% ✅ model_jobs: Complete job lifecycle, configuration, execution, resources
    %% ✅ model_performance: Pure evaluation results, metrics, grading
    %% ✅ Zero redundancy: All job context via JOIN, performance data separate
    %% ✅ Usage: JOIN tables to get complete picture of model training → evaluation
    
    model_jobs {
        int id PK "NOT NULL; Unique identifier for model job"
        int model_id FK "NOT NULL; Foreign key to ai_models"
        
        -- 🎯 Job Classification & Control
        varchar(20) job_status "NOT NULL; pending, running, completed, failed, cancelled, paused"
        varchar(15) job_category "NOT NULL; training, prediction, evaluation, optimization, deployment"
        varchar(25) job_type "NOT NULL; Specific job type within category"
        varchar(30) job_name "Human-readable job name/description"
        
        -- 📊 Execution Tracking
        numeric(5,2) progress_pct "NOT NULL; default: 0; Job progress (0-100)"
        varchar(20) current_phase "Current execution phase/stage"
        int total_steps "Total number of steps in job (if applicable)"
        int completed_steps "Number of completed steps"
        
        -- ⚙️ Comprehensive Job Configuration  
        jsonb job_config "NOT NULL; Complete job configuration and parameters:
            {
                -- Training Jobs
                'training_config': {
                    'dataset_config': {
                        'start_date': '2023-01-01',
                        'end_date': '2024-12-31',
                        'timeframe': '1h',
                        'validation_split': 0.2
                    },
                    'hyperparameters': {
                        'learning_rate': 0.001,
                        'batch_size': 64,
                        'epochs': 100,
                        'early_stopping_patience': 10
                    },
                    'feature_config': {
                        'technical_indicators': true,
                        'market_regime_features': true,
                        'sector_features': false
                    }
                },
                -- Prediction Jobs
                'prediction_config': {
                    'start_date': '2024-01-01',
                    'end_date': '2024-12-31',
                    'timeframe': '1h',
                    'assets': ['BTC', 'ETH', 'ADA'],
                    'prediction_horizon': 24
                },
                'output_config': {
                    'include_confidence': true,
                    'include_probabilities': true,
                    'export_format': 'json',
                    'store_in_db': true
                },
                'filters': {
                    'min_confidence_threshold': 0.7,
                    'sector_filter': ['DeFi', 'L1'],
                    'market_cap_min': 1000000000
                }
            }"
        
        -- � Real-time Metrics (Dynamic based on job category)
        jsonb job_metrics "Real-time job metrics (structure varies by job category):
            {
                -- Training Jobs
                'training_metrics': {
                    'current_epoch': 45,
                    'train_loss': 0.0234,
                    'val_loss': 0.0267,
                    'train_accuracy': 0.87,
                    'val_accuracy': 0.83,
                    'learning_rate': 0.0008,
                    'time_per_epoch': 12.5
                },
                -- Prediction Jobs
                'prediction_stats': {
                    'total_samples': 10000,
                    'processed_samples': 7500,
                    'successful_predictions': 7200,
                    'failed_predictions': 300,
                    'avg_confidence': 0.82,
                    'processing_rate_per_second': 15.6
                },
                -- Performance Metrics (All Jobs)
                'resource_usage': {
                    'peak_memory_mb': 2048,
                    'avg_cpu_percent': 75,
                    'avg_gpu_percent': 90,
                    'disk_io_mb': 156
                }
            }"
        
        -- 📝 Logging & Monitoring
        text log_output "Job logs and output (truncated for storage)"
        text error_message "Detailed error message if the job failed"
        
        -- ⏱️ Timing Information
        timestamp started_at "When the job actually started"
        timestamp completed_at "When the job completed (success or failure)"
        numeric execution_time_seconds "Total execution time of the job"
        timestamp estimated_completion "Estimated completion time (updated during processing)"
        
        -- � Results & Output (Dynamic based on job category)
        jsonb job_results "Job results and outputs:
            {
                -- Training Jobs
                'model_output_path': '/models/BTC_LSTM_v2.1.0.pkl',
                'final_metrics': {
                    'final_accuracy': 0.87,
                    'final_loss': 0.0234,
                    'validation_score': 0.83
                },
                -- Prediction Jobs
                'predictions_output_path': '/predictions/btc_predictions_20241003.json',
                'sample_predictions': [
                    {'asset': 'BTC', 'prediction': 'bull', 'confidence': 0.85, 'timestamp': '2024-10-03T10:00:00Z'}
                ],
                -- Performance Metrics
                'performance_summary': {
                    'throughput_per_minute': 850,
                    'data_quality_score': 0.94,
                    'success_rate': 0.96
                }
            }"
        
        -- 🔄 Scheduling & Recurrence (For prediction jobs mainly)
        boolean is_recurring "Whether this is a recurring scheduled job"
        varchar cron_schedule "Cron expression for recurring jobs (if applicable)"
        timestamp next_run_time "Next scheduled execution time (for recurring jobs)"
        
        -- 👥 User & Administrative
        int initiated_by FK "User/admin who started this job"
        varchar priority "Job priority: low, normal, high, urgent"
        int retry_count "Number of times this job has been retried"
        int max_retries "Maximum number of retries allowed (default: 3)"
        
        -- 📊 Performance & Resource Management
        jsonb resource_limits "Resource limits for this job:
            {
                'max_memory_mb': 4096,
                'max_execution_seconds': 3600,
                'max_cpu_percent': 80,
                'max_gpu_percent': 95
            }"
        
        timestamp created_at "NOT NULL; default: Now(); Job creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last update timestamp"
        
        -- 📋 Enhanced Constraints & Indexes
        CONSTRAINT chk_progress_range CHECK (progress_percentage >= 0 AND progress_percentage <= 100)
        CONSTRAINT chk_retry_count CHECK (retry_count >= 0 AND retry_count <= max_retries)
        CONSTRAINT chk_max_retries CHECK (max_retries >= 0 AND max_retries <= 10)
        CONSTRAINT chk_job_category_valid CHECK (job_category IN ('training', 'prediction', 'evaluation', 'optimization'))
        CONSTRAINT chk_cron_schedule_valid CHECK (cron_schedule IS NULL OR is_recurring = true)
        
        -- Indexes for Performance
        INDEX idx_model_jobs_status_category (job_status, job_category, created_at DESC)
        INDEX idx_model_jobs_model_type (model_id, job_category, job_status)
        INDEX idx_model_jobs_priority_queue (priority DESC, created_at ASC) WHERE job_status = 'pending'
        INDEX idx_model_jobs_recurring (is_recurring, next_run_time ASC) WHERE is_recurring = true
        INDEX idx_model_jobs_monitoring (job_status, progress_percentage, updated_at DESC) WHERE job_status IN ('pending', 'running')
    }
    

    %% ❌ model_audit_logs - حذف شد برای MVP
    %% 📝 فاز 2: اضافه می‌شود برای compliance و enterprise features
    %% model_audit_logs {
    %%     int id PK
    %%     int model_id FK
    %%     varchar action_type
    %%     text action_details
        int performed_by FK "NOT NULL; User/admin who performed the action"
        jsonb previous_state "Snapshot of model state before the action"
        jsonb new_state "Snapshot of model state after the action"
        timestamp action_time "When the action was performed"
        timestamp created_at "NOT NULL; default: Now(); Audit log creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last update timestamp"
    }

    %% User Notifications & Feedback
    notifications {
        int id PK "NOT NULL; Primary key for notification tracking"
        int user_id FK "NOT NULL; User receiving this notification"
        varchar notification_type "NOT NULL; Type of notification: signal, alert, system, educational"
        varchar title "NOT NULL; Notification title/subject"
        text message "NOT NULL; Notification message content"
        jsonb data "Additional notification data and metadata"
        varchar status "Notification status: unread, read, dismissed"
        varchar priority "Notification priority: low, normal, high, urgent"
        timestamp scheduled_for "When notification should be sent"
        timestamp sent_at "When notification was actually sent"
        timestamp read_at "When user read the notification"
        timestamp expires_at "When notification expires"
        timestamp created_at "NOT NULL; default: Now(); Notification creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last update timestamp"
    }

    user_feedback {
        int id PK "NOT NULL; Primary key for user feedback"
        int user_id FK "NOT NULL; User providing the feedback"
        varchar feedback_type "NOT NULL; Type of feedback: bug_report, feature_request, general_comment"
        text message "NOT NULL; Feedback message content"
        jsonb context_data "Additional context about the feedback"
        varchar status "Feedback status: new, in_review, addressed, closed"
        varchar priority "Feedback priority: low, normal, high"
        int reviewed_by FK "Admin/user who reviewed the feedback"
        text response_message "Response message to the user"
        timestamp reviewed_at "When feedback was reviewed"
        timestamp responded_at "When response was sent to user"
        timestamp created_at "NOT NULL; default: Now(); Feedback submission timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last update timestamp"
    }   

    %% Signal Alerts (User-specific alerts)
    signal_alerts {
        int id PK "NOT NULL; Primary key for signal alerts"
        int user_id FK "NOT NULL; User who created this alert"
        int asset_id FK "NOT NULL; Cryptocurrency this alert monitors"
        varchar alert_type "NOT NULL; Alert type: price_target, signal_generated, volume_spike"
        numeric trigger_value "NOT NULL; Value that triggers the alert"
        varchar condition "NOT NULL; Condition: above, below, equals, percentage_change"
        boolean is_active "NOT NULL; default: true; Whether alert is currently active"
        boolean is_triggered "NOT NULL; default: false; Whether alert has been triggered"
        text message "Custom alert message"
        varchar notification_method "How to notify: email, push, sms"
        timestamp triggered_at "When alert was triggered"
        timestamp last_checked "Last time alert condition was checked"
        timestamp expires_at "When alert expires"
        timestamp created_at "NOT NULL; default: Now(); Alert creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last update timestamp"
    }

    %% System Management
    system_health {
        int id PK "NOT NULL; Primary key for system health monitoring"
        timestamp check_time "NOT NULL; When this health check was performed"
        jsonb api_status "Status of various API endpoints and services"
        jsonb database_status "Database performance and connection status"
        jsonb ml_models_status "Status and performance of ML models"
        jsonb data_pipeline_status "Status of data ingestion and processing pipelines"
        numeric overall_health_score "Overall system health score (0-100)"
        jsonb performance_metrics "System performance metrics and KPIs"
        jsonb error_logs "Recent error logs and issues"
        timestamp created_at "NOT NULL; default: Now(); Record creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last update timestamp"
    }

    analytics_data {
        int id PK "NOT NULL; Primary key for analytics data storage"
        varchar category "NOT NULL; Analytics category: user_behavior, api_usage, performance"
        varchar metric_name "NOT NULL; Name of the metric being tracked"
        numeric metric_value "NOT NULL; Value of the metric"
        jsonb dimensions "Metric dimensions and breakdown"
        varchar aggregation_level "Aggregation: hourly, daily, weekly, monthly"
        timestamp created_at "NOT NULL; default: Now(); Record creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last update timestamp"
    }

    api_request_logs {
        int id PK "NOT NULL; Primary key for API request logging"
        int user_id FK "NOT NULL; User making the API request (if authenticated)"
        varchar endpoint "NOT NULL; API endpoint called"
        varchar http_method "NOT NULL; HTTP method used"
        int response_status "NOT NULL; HTTP response status code"
        numeric response_time_ms "NOT NULL; Response time in milliseconds"
        timestamp created_at "NOT NULL; default: Now(); API request log creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last update timestamp"
    }

    external_api_logs {
        int id PK "NOT NULL; Primary key for external API logging"
        varchar api_provider "NOT NULL; External API provider: coingecko, binance, etc."
        varchar endpoint "NOT NULL; API endpoint called"
        varchar http_method "NOT NULL; HTTP method used"
        int response_status "NOT NULL; HTTP response status code"
        numeric response_time_ms "NOT NULL; Response time in milliseconds"
        timestamp created_at "NOT NULL; default: Now(); External API log creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last update timestamp"
    }

    background_tasks {
        int id PK "NOT NULL; Primary key for background task tracking"
        varchar task_name "NOT NULL; Name of the background task"
        varchar task_type "NOT NULL; Type: data_sync, model_training, cleanup"
        varchar status "NOT NULL; Status: pending, running, completed, failed"
        jsonb task_params "NOT NULL; Task parameters and configuration"
        jsonb result_data "Task execution results"
        text error_message "Error message if task failed"
        timestamp started_at "When task execution started"
        timestamp completed_at "When task execution completed"
        numeric execution_time_seconds "Total execution time"
        timestamp created_at "NOT NULL; default: Now(); Task creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last update timestamp"
    }

    %% === RELATIONSHIPS ===
    %% Core User Management
    users ||--o{ user_sessions : "has sessions"
    users ||--o{ user_activities : "performs activities"
    users ||--o{ portfolios : "owns portfolios"
    users ||--o{ watchlists : "creates watchlists"
    users ||--o{ notifications : "receives notifications"
    users ||--o{ user_feedback : "provides feedback"
    users ||--o{ signal_alerts : "sets alerts"
    users ||--o{ trade_actions : "executes trades"
    users ||--o{ recommendations : "receives recommendations"
    users ||--o{ model_jobs : "initiates model jobs"
    
    %% Asset & Market Data
    assets ||--o{ price_data : "has price data"
    assets ||--o{ price_data_archive : "has archived data"
    assets ||--o{ portfolio_assets : "included in portfolios"
    assets ||--o{ watchlist_assets : "watched in lists"
    assets ||--o{ ai_trading_signals : "generates signals"
    assets ||--o{ signal_alerts : "triggers alerts"
    assets ||--o{ sector_mapping : "belongs to sectors"
    
    %% Sectors
    sectors ||--o{ sector_history : "has historical data"
    sectors ||--o{ sector_mapping : "contains assets"
    sectors ||--o{ ai_sector_analysis : "analyzed by AI"
    sectors ||--o{ sector_rotation_flows : "source sector"
    sectors ||--o{ sector_rotation_flows : "destination sector"
    
    %% AI Analysis Chain
    metrics_snapshot ||--o{ ai_regime_analysis : "regime analysis"
    metrics_snapshot ||--o{ ai_sector_analysis : "sector analysis"
    metrics_snapshot ||--o{ ai_cross_sector_analysis : "cross-sector analysis"
    metrics_snapshot ||--o{ ai_watchlist_analysis : "watchlist analysis"
    metrics_snapshot ||--o{ ai_portfolio_analysis : "portfolio analysis"
    metrics_snapshot ||--o{ ai_portfolio_asset_analysis : "asset analysis"
    metrics_snapshot ||--o{ ai_trading_signals : "trading signals"
    
    %% AI Models
    ai_models ||--o{ ai_regime_analysis : "analyzes regime"
    ai_models ||--o{ ai_sector_analysis : "analyzes sectors"
    ai_models ||--o{ ai_cross_sector_analysis : "cross-sector analysis"
    ai_models ||--o{ ai_watchlist_analysis : "analyzes watchlists"
    ai_models ||--o{ ai_portfolio_analysis : "analyzes portfolios"
    ai_models ||--o{ ai_portfolio_asset_analysis : "analyzes assets"
    ai_models ||--o{ ai_trading_signals : "generates signals"
    ai_models ||--o{ model_performance : "performance evaluations"
    ai_models ||--o{ model_jobs : "model jobs"
    
    %% Job to Performance Relationship
    model_jobs ||--o{ model_performance : "triggers evaluations"
    
    %% Portfolio Management
    portfolios ||--o{ portfolio_assets : "contains assets"
    portfolios ||--o{ ai_portfolio_analysis : "analyzed by AI"
    portfolio_assets ||--o{ ai_portfolio_asset_analysis : "asset analysis"
    portfolio_assets ||--o{ trade_actions : "trade history"
    
    %% Watchlists
    watchlists ||--o{ watchlist_assets : "contains assets"
    watchlists ||--o{ ai_watchlist_analysis : "analyzed by AI"
    
    %% Trading Signals & Recommendations
    ai_trading_signals ||--o{ trade_actions : "triggers trades"
    ai_trading_signals ||--o{ recommendations : "generates recommendations"
    ai_watchlist_analysis ||--o{ ai_trading_signals : "generates signals"
    ai_portfolio_analysis ||--o{ ai_trading_signals : "generates signals"
    
    %% Cross-Sector Analysis
    ai_cross_sector_analysis ||--o{ sector_rotation_flows : "tracks flows"
```

## 🛡️ **Security & Performance Considerations**

### **Required Indexes:**
```sql
-- Performance Critical Indexes
CREATE INDEX idx_price_data_asset_time ON price_data(asset_id, candle_time DESC);
CREATE INDEX idx_assets_symbol ON assets(symbol);
CREATE INDEX idx_portfolio_assets_portfolio ON portfolio_assets(portfolio_id, is_active);
CREATE INDEX idx_ai_signals_asset_status ON ai_trading_signals(asset_id, status, created_at DESC);
CREATE INDEX idx_metrics_snapshot_time ON metrics_snapshot(snapshot_time DESC);

-- JSONB Indexes for AI Analysis
CREATE INDEX idx_extended_metrics_gin ON metrics_snapshot USING GIN(extended_metrics);
CREATE INDEX idx_analysis_data_gin ON ai_regime_analysis USING GIN(analysis_data);
CREATE INDEX idx_key_levels_gin ON ai_regime_analysis USING GIN(key_levels);
```

### **Data Constraints:**
```sql
-- Business Logic Constraints
ALTER TABLE users ADD CONSTRAINT chk_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');
```

### **Partitioning Strategy:**
```sql
-- Partition price_data by month for better performance
CREATE TABLE price_data (
    -- existing columns
) PARTITION BY RANGE (candle_time);

CREATE TABLE price_data_y2025m09 PARTITION OF price_data
    FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');
```

### **Security Enhancements:**
```sql
-- Row Level Security for multi-tenant data
ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;
CREATE POLICY portfolio_access ON portfolios FOR ALL TO authenticated_users
    USING (user_id = current_user_id());

-- Audit Trail
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(50),
    operation VARCHAR(10),
    old_values JSONB,
    new_values JSONB,
    changed_by INTEGER REFERENCES users(id),
    changed_at TIMESTAMP DEFAULT NOW()
);
```

## 📋 **Critical Issues Found & Fixed:**

### ✅ **Completed Improvements:**
1. **Added Relationships**: تمام روابط بین جداول تعریف شد
2. **Performance Indexes**: ایندکس‌های ضروری برای کارایی بالا
3. **Data Constraints**: محدودیت‌های منطقی کسب‌وکار
4. **Security Features**: امنیت سطر و audit trail

### ⚠️ **Remaining Issues to Address:**
1. **Type Specifications**: برخی varchar ها نیاز به تعریف طول دارند
2. **Enum Types**: استفاده از ENUM بجای VARCHAR برای مقادیر ثابت
3. **Backup Strategy**: نیاز به استراتژی backup برای جداول critical
4. **Monitoring**: جداول monitoring برای performance tracking

### 🎯 **Priority Recommendations:**
1. **اولویت بالا**: اعمال indexes و constraints
2. **اولویت متوسط**: پیاده‌سازی partitioning برای price_data
3. **اولویت پایین**: بهبود type definitions و enum ها
