# docs\Design\17_0_Database_ERD_Structure.md
# 🗄️ Database ERD Design - Days 15-18
## **📈 Complete ERD Structure**

```mermaid
erDiagram
    %% Core User Management
    users {
        int id PK "NOT NULL; rimary key for user identification"
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
        varchar symbol UK "NOT NULL; Unique trading symbol (BTC, ETH, etc.)"
        varchar name "NOT NULL; Full cryptocurrency name"
        varchar asset_type "NOT NULL; Asset type (e.g., crypto, stablecoin, macro (for DXY, VIX, SP500, Gold, Oil, CPI, ...), index (for total, total2, total3, btc.d, usdt.d, altcoin index, ...))"
        varchar quote_currency "For pairs, the quote currency (e.g., USDT)"
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
        int access_count "Total number of times this asset has been accessed"
        boolean is_active "NOT NULL; default: true; Whether this asset is active in our system"
        boolean is_supported "NOT NULL; default: true; Whether we provide analysis for this asset"
        timestamp created_at "NOT NULL; default: Now(); Record creation timestamp"
        timestamp updated_at "NOT NULL; default: Now(); Last data update timestamp"
    }

    price_data {
        int id PK "NOT NULL; Primary key for price data records"
        int asset_id FK "NOT NULL; Foreign key linking to assets.id"
        varchar timeframe "Timeframe of the record (e.g., '1m', '5m', '1h', '1d')"
        numeric(20,8) open_price "Opening price for the time period in USD"
        numeric(20,8) high_price "Highest price during the time period in USD"
        numeric(20,8) low_price "Lowest price during the time period in USD"
        numeric(20,8) close_price "Closing price for the time period in USD"
        numeric(30,2) volume "Trading volume during the time period in USD"
        numeric(30,2) market_cap "Market capitalization at this timestamp in USD"
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
        timestamp created_at "NOT NULL; default: Now(); Record creation timestamp"
    }

    price_data_archive {
        int id PK "NOT NULL; Primary key for archived price data records"
        int asset_id FK "NOT NULL; Foreign key linking to assets.id"
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
        timestamp created_at "NOT NULL; default: Now(); Record creation timestamp"
    }

    %% Layer 1: Macro Analysis
    metrics_snapshot {
        int                id                       "Primary key"  
        timestamp          snapshot_time            "When snapshot is taken"  
        varchar(10)        timeframe                "Interval ('1h','4h','1d')"  
        numeric(18,2)      price                    "BTC price at snapshot time"

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
        timestamp          created_at                 "Record creation timestamp"
        timestamp          updated_at                 "Last update timestamp"
    }
        
    market_regime_analysis {
        int                id                         "Primary key"
        int                metrics_snapshot_id        "FK → metrics_snapshot.id"
        int                ai_model_id              "FK → ai_models.id"

        timestamp          analysis_time              "When this analysis ran"
        varchar(10)        regime                     "Detected regime: 'Bull','Bear','Sideways'"

        -- 📈 Trend & Breakout Signals
        numeric(5,2)       trend_strength_score       "AI trend-strength (0–1)"
        boolean            breakout_signal            "TRUE if price broke key technical level"
        boolean            volume_confirmation        "TRUE if breakout volume ≥ X% above N-bar avg volume"
        numeric(5,2)       volatility_expansion_score "Pct. increase in ATR or Bollinger width on breakout"
        boolean            retest_confirmation        "TRUE if price retested and held breakout level within M bars"
        numeric(5,2)       momentum_divergence_score  "Score of divergence between momentum indicator & price"
        boolean            multi_timeframe_breakout   "TRUE if breakout confirmed on multiple timeframes"
        boolean            price_above_ma200          "Price > 200-period SMA?"

        -- 🔑 AI-Detected Key Levels (JSON array with strength)
        jsonb              key_levels                 "Array of pivotal levels detected by AI:
            [
                {type:'support',    value:64200, strength:0.85},
                {type:'support',    value:63000, strength:0.72},
                {type:'resistance', value:67000, strength:0.67},
                {type:'trendline',  points:[{x:'2025-09-20T12:00',y:65500},…], strength:0.60}
            ]"

        -- 🤖 AI Meta-Signals
        varchar(10)        ai_regime_prediction       "AI-predicted regime"
        numeric(4,2)       ai_confidence_score        "AI model confidence (0–1)"
        numeric(4,2)       signal_agreement_score     "Ensemble agreement across signals (0–1)"
        int                regime_duration_estimate   "Estimated duration of current regime in hours"

        -- 📝 Analyst Notes & Rationale
        jsonb              analysis_data              "Free-text or structured rationale"
                            Example:
                            {
                                'rationale': [
                                    'BTC above MA200 and RSI>50',
                                    'TOTAL and TOTAL2 rising, BTC.D falling',
                                    'Fear & Greed in Greed zone',
                                    'DXY not in strong uptrend'
                                ],
                                'notes': 'Slightly higher allocation to alts; medium risk.'
                            }
        timestamp          created_at                 "Record creation timestamp"
        timestamp          updated_at                 "Last update timestamp"
    }


    %% Layer 2: Sector Analysis
    sectors {
        int id PK "Primary key for crypto sectors"
        varchar coingecko_id
        varchar name UK "Unique sector name (DeFi, Gaming, Infrastructure, etc.)"
        text description "Detailed description of the sector"
        numeric(30,2) market_cap
        numeric(30,2) market_cap_change_24h
        numeric(30,2) volume_24h
        jsonb metrics_details "7 records for ohlv in 7d timeframe and so on.. "
        int[] top_3_coins_id "[bitcoin's PK, ethereum's PK, binancecoin's PK]",
        boolean is_active "Whether this sector is actively tracked"
        timestamp created_at "Record creation timestamp"
        timestamp updated_at "Last update timestamp"
    }

    sector_history {
        int id PK "Primary key for sector history data"
        int sector_id FK "Foreign key linking to sectors table"
        varchar timeframe "Timeframe of the record (e.g., '1m', '5m', '1h', '1d')"
        numeric(30,2) market_cap
        numeric(30,2) volume_24h
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
        timestamp created_at "Record creation timestamp"
    }

    sector_mapping {
        int id PK "Primary key for crypto-sector mapping"
        int asset_id FK "Foreign key linking to assets table"
        int sector_id FK "Foreign key linking to sectors table"
        boolean is_primary_sector "Whether this is the primary sector for the crypto"
        timestamp created_at "Record creation timestamp"
        timestamp updated_at "Last update timestamp"
    }

    sector_analysis {
        int id PK "Primary key for sector analysis record"
        int metrics_snapshot_id FK "Foreign key linking to metrics_snapshot.id"
        int ai_model_id FK "Foreign key linking to ai_models.id"
        int sector_id FK "Foreign key linking to sectors.id (DeFi, L1, L2, NFT, AI, RWA, ...)"

        varchar timeframe "Timeframe of the record (e.g., '1d', '7d', '30d')"
        timestamp candle_time "Timestamp of the candle in UTC."
        timestamp analysis_time "Timestamp when this analysis was executed"

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

        timestamp created_at "Record creation timestamp"
        timestamp updated_at "Last update timestamp"
    }

    cross_sector_analysis {
        int id PK "Primary key for cross-sector analysis record"
        int metrics_snapshot_id FK "Foreign key linking to metrics_snapshot.id"
        int ai_model_id FK "Foreign key linking to ai_models.id"

        timestamp analysis_time "Timestamp when this cross-sector analysis was executed"

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

        timestamp created_at "Record creation timestamp"
        timestamp updated_at "Last update timestamp"
    }

    sector_rotation_flows {
        int id PK
        int cross_sector_analysis_id FK "Link to cross_sector_analysis.id"
        int from_sector_id FK "Source sector"
        int to_sector_id FK "Destination sector"
        numeric(6,2) score "Rotation score (0–1)"
        timestamp created_at
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
        int asset_id FK "Foreign key linking to assets table"
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
        int asset_id FK "REFERENCES assets(id); only for crypto assets available in the system."
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
        int asset_id FK "Cryptocurrency this signal applies to"
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
        int asset_id FK "Cryptocurrency being predicted"
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
        int asset_id FK "Cryptocurrency this alert monitors"
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


```
