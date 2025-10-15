# docs\Design\17_2_Database_Integration_And_API_Planning.md
# 🗄️ Database Integration & API Planning - Day 18 (Updated)
## Complete API Architecture Based on ERD Structure - Comprehensive Endpoints

---

## 🎯 **API Design Philosophy**

### **🔄 Database-First API Strategy:**
```
Database ERD-Aligned API Design:
├── 👥 User Management: Complete CRUD operations based on users, user_sessions, user_activities
├── 💰 Asset Management: Full asset lifecycle based on assets table structure
├── 📊 Price Data: OHLCV data management aligned with price_data and price_data_archive
├── � Portfolio Management: User portfolio operations based on portfolios table
├── 👀 Watchlist Management: Personal watchlist operations based on watchlists table
├── 🤖 ML/AI Operations: Model management based on ml_models and ai_suggestions
├── 🔔 Notifications: Alert system based on notifications table
├── �️ Security & Sessions: Authentication based on user_sessions and rate_limiting
└── 📈 Analytics: System monitoring based on user_activities and audit_logs
```

### **📊 Database Schema Integration Summary:**
```
�️ Complete Database Schema Mapping:
├── 👥 Users & Auth: users, user_sessions, user_activities, rate_limiting ✅
├── � Assets: assets, price_data, price_data_archive ✅
├── � User Data: portfolios, watchlists, portfolio_assets, watchlist_assets ✅
├── 🤖 AI/ML: ml_models, model_predictions, ai_suggestions ✅
├── 🔔 Notifications: notifications, notification_preferences ✅
├── 🛡️ Security: audit_logs, data_quality_reports ✅
└── 🎯 Total: 17 core tables - Fully Integrated ✅
```

---

## 📡 **Complete API Structure Based on ERD**

### **🌍 Layer 1: Macro Analysis Endpoints (Universal Access)**
```python
# Market Regime & Macro Analysis
GET /api/v1/macro/current-snapshot
# Source: metrics_snapshot table (latest record by snapshot_time)
# Includes: BTC price, dominance levels, fear & greed index, technical indicators
# Rate Limit: 10 requests/minute for guests, unlimited for users
# Auth: Optional (enhanced data for authenticated users)
# Response: MacroSnapshotResponse

GET /api/v1/macro/market-regime
# Source: ai_regime_analysis table (latest analysis)
# Includes: Current regime, confidence score, transition probability, regime duration
# Auth: Optional
# Response: MarketRegimeResponse

GET /api/v1/macro/sentiment
# Source: metrics_snapshot.fear_greed_index, extended_metrics.sentiment_metrics
# Includes: Fear & Greed Index, social sentiment, Google trends
# Auth: Optional
# Response: MarketSentimentResponse

GET /api/v1/macro/dominance
# Source: metrics_snapshot (btc_dominance, eth_dominance, usdt_dominance, altcoin_dominance)
# Includes: Current dominance levels, historical trends, correlations
# Auth: Optional
# Response: DominanceAnalysisResponse

GET /api/v1/macro/intermarket
# Source: metrics_snapshot (sp500, gold, dxy, us_10y_yield, vix_index)
# Includes: Traditional market correlations with crypto
# Auth: Optional
# Response: IntermarketDataResponse

# Historical Macro Data
GET /api/v1/macro/history
# Source: metrics_snapshot table with time series data
# Query params: timeframe, start_date, end_date, metrics[]
# Includes: Historical snapshots with selected metrics
# Auth: Optional (longer history for users)
# Response: MacroHistoryResponse

GET /api/v1/macro/correlations
# Source: metrics_snapshot with correlation calculations
# Includes: BTC-ETH, BTC-SP500, crypto-traditional market correlations
# Query params: period (7d, 30d, 90d)
# Auth: Optional
# Response: CorrelationAnalysisResponse

# On-Chain & Derivatives
GET /api/v1/macro/onchain
# Source: metrics_snapshot.extended_metrics.onchain_metrics
# Includes: Whale flows, exchange flows, active addresses, miner data
# Auth: Optional (full data for users)
# Response: OnChainMetricsResponse

GET /api/v1/macro/derivatives
# Source: metrics_snapshot (funding_rate_btc, open_interest_btc, liquidations)
# Includes: Funding rates, open interest, liquidation data
# Auth: Optional
# Response: DerivativesDataResponse

GET /api/v1/macro/liquidations
# Source: metrics_snapshot.liquidation_zones JSON field
# Includes: Liquidation heatmap, volume by price zones
# Auth: Optional
# Response: LiquidationAnalysisResponse

# Technical Analysis (Macro Level)
GET /api/v1/macro/technical
# Source: metrics_snapshot technical indicators
# Includes: RSI, MACD, moving averages, volatility indicators
# Query params: indicators[], timeframe
# Auth: Optional
# Response: MacroTechnicalResponse

# Market Breadth & Health  
GET /api/v1/macro/market-health
# Source: metrics_snapshot.extended_metrics.composite_metrics
# Includes: Market breadth, volatility index, liquidity scores
# Auth: Optional
# Response: MarketHealthResponse

# Cycle Analysis
GET /api/v1/macro/cycle-analysis
# Source: metrics_snapshot cycle and seasonal data
# Includes: Halving countdown, seasonal patterns, epoch analysis
# Auth: Optional  
# Response: CycleAnalysisResponse

# Admin Macro Data Management
POST /api/v1/admin/macro/refresh-snapshot
# Creates: New metrics_snapshot record from external data sources
# Updates: Latest market data from CoinGecko, Alternative.me, etc.
# Response: SnapshotOperationResponse

GET /api/v1/admin/macro/data-sources
# Source: System configuration and data source status
# Includes: API health, last update times, error logs
# Response: DataSourceStatusResponse

POST /api/v1/admin/macro/backfill
# Creates: Historical metrics_snapshot records
# Query params: start_date, end_date, data_sources[]
# Response: BackfillOperationResponse
```

### **� Layer 2: Sector Analysis Endpoints**
```python
# Sector Performance & Analysis
GET /api/v1/sectors
# Source: sectors table with is_active filter
# Includes: Sector names, categories, asset counts
# Auth: Optional
# Response: SectorListResponse

GET /api/v1/sectors/{sector_id}/analysis
# Source: ai_sector_analysis table (latest analysis for sector)
# Includes: Performance metrics, capital flows, relative strength
# Auth: Optional
# Response: SectorAnalysisResponse

GET /api/v1/sectors/performance
# Source: ai_sector_analysis table aggregated by sector
# Includes: All sectors performance comparison (24h, 7d, 30d)
# Query params: timeframe, sort_by
# Auth: Optional
# Response: SectorPerformanceResponse

GET /api/v1/sectors/rotation
# Source: ai_sector_analysis rotation scores and flows
# Includes: Capital rotation analysis, inflow/outflow scores
# Auth: Optional (detailed data for users)
# Response: SectorRotationResponse

GET /api/v1/sectors/{sector_id}/assets
# Source: assets table filtered by sector_id
# Includes: Top assets in sector with performance metrics
# Query params: limit, sort_by (market_cap, performance, volume)
# Auth: Optional
# Response: SectorAssetListResponse

# Sector Correlations & Relationships
GET /api/v1/sectors/correlations
# Source: ai_sector_analysis correlation data
# Includes: Inter-sector correlations, BTC/ETH correlations
# Query params: period (7d, 30d, 90d)
# Auth: Optional
# Response: SectorCorrelationResponse

GET /api/v1/sectors/narratives
# Source: ai_sector_analysis.narrative_tag arrays
# Includes: Current dominant narratives, sentiment trends
# Auth: Optional
# Response: SectorNarrativeResponse

# Sector Fundamentals & Metrics
GET /api/v1/sectors/{sector_id}/fundamentals
# Source: ai_sector_analysis fundamental metrics
# Includes: TVL, active users, active protocols, institutional flows
# Auth: Optional
# Response: SectorFundamentalResponse

GET /api/v1/sectors/tvl-analysis
# Source: ai_sector_analysis.tvl_total aggregated
# Includes: Total Value Locked trends across sectors
# Auth: Optional
# Response: TVLAnalysisResponse

# Historical Sector Data
GET /api/v1/sectors/{sector_id}/history
# Source: ai_sector_analysis table with time series data
# Query params: timeframe, start_date, end_date
# Includes: Historical performance, flows, correlations
# Auth: Optional (longer history for users)
# Response: SectorHistoryResponse

GET /api/v1/sectors/cross-sector-analysis
# Source: ai_cross_sector_analysis table (if exists)
# Includes: Cross-sector relationships, rotation patterns
# Auth: Optional
# Response: CrossSectorAnalysisResponse

# Admin Sector Management
GET /api/v1/admin/sectors/analytics
# Source: ai_sector_analysis with detailed analytics
# Includes: Sector health scores, prediction accuracy
# Response: SectorAnalyticsResponse

POST /api/v1/admin/sectors/{sector_id}/refresh-analysis
# Creates: New ai_sector_analysis record
# Updates: Latest sector data and AI analysis
# Response: SectorAnalysisOperationResponse

PUT /api/v1/admin/sectors/{sector_id}
# Updates: sectors table (name, description, is_active)
# Creates: audit_logs record
# Response: Updated sector data
```

### **�👥 User Management Endpoints**
```python
# Authentication & User Management
POST /api/v1/auth/register
# Schema: UserRegister -> users table
# Creates: user record, initial preferences, referral code
# Response: AuthResponse with user data and tokens

POST /api/v1/auth/login
# Schema: UserLogin -> user_sessions table
# Creates: session record, updates last_login, increments login_count
# Response: AuthResponse with tokens and session info

POST /api/v1/auth/refresh
# Updates: user_sessions.last_used_at, generates new tokens
# Response: TokenResponse

POST /api/v1/auth/logout
# Updates: user_sessions.is_active = false
# Creates: user_activities record (logout action)

GET /api/v1/users/me
# Source: users table with current session validation
# Response: UserProfile with preferences, subscription status

PUT /api/v1/users/me
# Updates: users table (first_name, last_name, preferences, timezone, language)
# Creates: user_activities record (profile update)
# Response: Updated UserProfile

POST /api/v1/users/change-password
# Updates: users.password_hash, resets failed_login_attempts
# Creates: user_activities record (password change)
# Response: SuccessResponse

# Admin User Management
GET /api/v1/admin/users
# Source: users table with pagination, filtering by role, status
# Includes: referral statistics, subscription info
# Response: UserListResponse

GET /api/v1/admin/users/{user_id}
# Source: users table joined with user_sessions, user_activities
# Response: Detailed user profile with activity history

PUT /api/v1/admin/users/{user_id}
# Updates: users table (role, is_active, subscription_plan, notes)
# Creates: audit_logs record, user_activities record
# Response: Updated user data

POST /api/v1/admin/users/{user_id}/verify
# Updates: users.is_verified = true
# Creates: notifications record (verification confirmation)
```

### **💰 Asset Management Endpoints**
```python
# Asset Discovery & Management
GET /api/v1/assets
# Source: assets table filtered by is_active, is_supported
# Includes: current_price, market_cap, price_change_percentage_24h
# Query params: asset_type, search, limit, offset
# Response: AssetListResponse

GET /api/v1/assets/{asset_id}
# Source: assets table joined with latest price_data
# Includes: full asset details, external_ids, links, metrics_details
# Response: AssetDetailResponse

GET /api/v1/assets/search
# Source: assets table with full-text search on name, symbol
# Updates: assets.access_count, last_accessed_at
# Response: AssetSearchResponse

POST /api/v1/admin/assets
# Inserts: assets table with validation
# Creates: audit_logs record
# Response: Created asset data

PUT /api/v1/admin/assets/{asset_id}
# Updates: assets table, validates data integrity
# Creates: audit_logs record
# Response: Updated asset data

# Asset Statistics & Analytics
GET /api/v1/assets/{asset_id}/statistics
# Source: price_data aggregated by timeframe
# Calculates: volatility, volume trends, price ranges
# Response: AssetStatistics

GET /api/v1/assets/{asset_id}/price-history
# Source: price_data filtered by date range and timeframe
# Query params: timeframe, start_date, end_date, limit
# Response: PriceDataListResponse
```

### **📊 Price Data Management Endpoints**
```python
# Price Data Operations
GET /api/v1/price-data/{asset_id}
# Source: price_data table with asset join
# Query params: timeframe, limit, start_date, end_date
# Response: OHLCV data array with technical_indicators

POST /api/v1/admin/price-data/fetch
# External: CoinGecko API integration
# Inserts: Multiple price_data records via bulk_insert
# Updates: assets.last_price_update, data_quality_score
# Response: FetchOperationResponse

GET /api/v1/price-data/{asset_id}/technical-indicators
# Source: price_data.technical_indicators JSON field
# Calculates: Real-time RSI, MACD, SMA, EMA, Bollinger Bands
# Response: TechnicalIndicatorsResponse

GET /api/v1/price-data/{asset_id}/support-resistance
# Source: price_data analysis using repository method
# Calculates: Support and resistance levels based on price action
# Response: SupportResistanceLevels

POST /api/v1/admin/price-data/cleanup
# Executes: cleanup_old_data repository method
# Moves: Old records to price_data_archive
# Response: CleanupOperationResponse

GET /api/v1/price-data/quality-report
# Source: price_data with gap analysis and validation
# Calculates: Data quality scores, missing intervals
# Response: DataQualityReport
```

### **⚡ Layer 4: Trading Signals & Timing Endpoints**
```python
# Trading Signals Management
GET /api/v1/signals
# Source: ai_trading_signals table filtered by user preferences
# Query params: asset_id, signal_type, quality, status, timeframe
# Includes: Entry/exit levels, confidence scores, risk metrics
# Auth: Required (personalized signals)
# Response: TradingSignalListResponse

GET /api/v1/signals/{signal_id}
# Source: ai_trading_signals joined with assets, metrics_snapshot
# Includes: Full signal context, market conditions, confluence factors
# Auth: Required
# Response: TradingSignalDetailResponse

GET /api/v1/signals/active
# Source: ai_trading_signals where status = 'active' and expires_at > now()
# Query params: risk_level, min_confidence, asset_type
# Auth: Required
# Response: ActiveSignalListResponse

GET /api/v1/signals/{signal_id}/performance
# Source: ai_trading_signals with performance tracking data
# Includes: MFE/MAE, success rate, actual vs predicted outcomes
# Auth: Required
# Response: SignalPerformanceResponse

# Signal Generation & Analysis
POST /api/v1/signals/generate
# Creates: New ai_trading_signals records based on current market conditions
# Source: Latest metrics_snapshot, ai_models, user preferences
# Auth: Required (Premium feature)
# Response: SignalGenerationResponse

GET /api/v1/signals/opportunities
# Source: ai_trading_signals filtered by high-quality, recent signals
# Includes: Market opportunities, sector rotation signals
# Auth: Required
# Response: MarketOpportunityResponse

GET /api/v1/signals/risk-management
# Source: ai_trading_signals.risk_management and invalidation_criteria
# Includes: Position sizing, stop losses, risk metrics
# Auth: Required
# Response: RiskManagementResponse

# Signal Tracking & Updates
PUT /api/v1/signals/{signal_id}/execute
# Updates: ai_trading_signals (status = 'executed', actual_entry_price)
# Creates: user_activities record (signal execution)
# Auth: Required
# Response: SignalExecutionResponse

PUT /api/v1/signals/{signal_id}/close
# Updates: ai_trading_signals (status = 'closed', performance metrics)
# Creates: user_activities record (signal closure)
# Auth: Required
# Response: SignalClosureResponse

DELETE /api/v1/signals/{signal_id}
# Updates: ai_trading_signals (status = 'cancelled')
# Creates: user_activities record (signal cancellation)
# Auth: Required
# Response: SuccessResponse

# Recommendations & Insights
GET /api/v1/recommendations
# Source: recommendations table filtered by user and target entities
# Includes: Entry/exit recommendations, rebalancing suggestions
# Auth: Required
# Response: RecommendationListResponse

GET /api/v1/recommendations/{recommendation_id}
# Source: recommendations joined with related entities
# Includes: Full recommendation context, AI rationale
# Auth: Required
# Response: RecommendationDetailResponse

PUT /api/v1/recommendations/{recommendation_id}/implement
# Updates: recommendations (status = 'implemented', implemented_at)
# Creates: user_activities record (recommendation implementation)
# Auth: Required
# Response: ImplementationResponse

# Signal Analytics & Performance
GET /api/v1/signals/analytics
# Source: ai_trading_signals aggregated by user, timeframe, asset
# Includes: Win rate, profit factor, average returns, drawdown
# Auth: Required
# Response: SignalAnalyticsResponse

GET /api/v1/signals/backtest/{model_id}
# Source: Historical ai_trading_signals with performance data
# Query params: start_date, end_date, asset_ids[]
# Auth: Required (Premium feature)
# Response: BacktestResultsResponse

# Admin Signal Management
GET /api/v1/admin/signals/performance
# Source: ai_trading_signals with comprehensive performance metrics
# Includes: Model accuracy, signal quality distribution
# Response: AdminSignalPerformanceResponse

POST /api/v1/admin/signals/validate
# Executes: Signal validation across all active signals
# Updates: Signal status based on market conditions
# Response: ValidationOperationResponse

GET /api/v1/admin/signals/model-performance
# Source: ai_trading_signals grouped by ai_model_id
# Includes: Model comparison, accuracy trends over time
# Response: ModelSignalPerformanceResponse
```

### **📈 Portfolio Management Endpoints**
```python
# User Portfolio Operations
GET /api/v1/portfolios
# Source: portfolios table filtered by user_id and is_active
# Includes: portfolio_assets count, total value estimation
# Response: PortfolioListResponse

POST /api/v1/portfolios
# Inserts: portfolios table with user_id from auth
# Creates: user_activities record (portfolio creation)
# Response: Created portfolio data

GET /api/v1/portfolios/{portfolio_id}
# Source: portfolios joined with portfolio_assets and assets
# Includes: Current PnL, allocation breakdown, asset performance
# Response: PortfolioDetailResponse

PUT /api/v1/portfolios/{portfolio_id}
# Updates: portfolios table (is_active, is_public)
# Validates: User ownership
# Response: Updated portfolio data

DELETE /api/v1/portfolios/{portfolio_id}
# Updates: portfolios.is_active = false (soft delete)
# Creates: user_activities record (portfolio deletion)
# Response: SuccessResponse

# Portfolio Asset Management
GET /api/v1/portfolios/{portfolio_id}/assets
# Source: portfolio_assets joined with assets and latest price_data
# Includes: Current prices, PnL calculations, performance metrics
# Response: PortfolioAssetListResponse

POST /api/v1/portfolios/{portfolio_id}/assets
# Inserts: portfolio_assets table with validation
# Updates: portfolio.updated_at
# Creates: user_activities record (asset addition)
# Response: Created portfolio asset

PUT /api/v1/portfolios/{portfolio_id}/assets/{asset_id}
# Updates: portfolio_assets (quantity, entry_price, notes, allocation_target)
# Validates: User ownership and portfolio access
# Response: Updated portfolio asset

DELETE /api/v1/portfolios/{portfolio_id}/assets/{asset_id}
# Updates: portfolio_assets.is_active = false
# Creates: user_activities record (asset removal)
# Response: SuccessResponse

# Portfolio Analytics
GET /api/v1/portfolios/{portfolio_id}/analytics
# Source: ai_portfolio_analysis table with latest analysis
# Includes: Risk metrics, diversification scores, allocation analysis
# Response: PortfolioAnalyticsResponse

GET /api/v1/portfolios/{portfolio_id}/performance
# Source: portfolio_assets with historical price_data
# Calculates: Total return, risk metrics, drawdown analysis
# Response: PortfolioPerformanceResponse
```

### **👀 Watchlist Management Endpoints**
```python
# User Watchlist Operations
GET /api/v1/watchlists
# Source: watchlists table filtered by user_id and is_active
# Includes: watchlist_assets count, asset symbols preview
# Response: WatchlistListResponse

POST /api/v1/watchlists
# Inserts: watchlists table with user_id from auth
# Creates: user_activities record (watchlist creation)
# Response: Created watchlist data

GET /api/v1/watchlists/{watchlist_id}
# Source: watchlists joined with watchlist_assets and assets
# Includes: Current prices, price changes, asset performance
# Response: WatchlistDetailResponse

PUT /api/v1/watchlists/{watchlist_id}
# Updates: watchlists table (name, description, is_public)
# Validates: User ownership
# Response: Updated watchlist data

DELETE /api/v1/watchlists/{watchlist_id}
# Updates: watchlists.is_active = false (soft delete)
# Creates: user_activities record (watchlist deletion)
# Response: SuccessResponse

# Watchlist Asset Management
GET /api/v1/watchlists/{watchlist_id}/assets
# Source: watchlist_assets joined with assets and latest price_data
# Includes: Current prices, technical indicators, AI scores
# Response: WatchlistAssetListResponse

POST /api/v1/watchlists/{watchlist_id}/assets
# Inserts: watchlist_assets table with validation
# Updates: watchlist.updated_at
# Creates: user_activities record (asset addition)
# Response: Created watchlist asset

PUT /api/v1/watchlists/{watchlist_id}/assets/{asset_id}
# Updates: watchlist_assets (position_type, notes, sort_order)
# Validates: User ownership and watchlist access
# Response: Updated watchlist asset

DELETE /api/v1/watchlists/{watchlist_id}/assets/{asset_id}
# Updates: watchlist_assets.is_active = false
# Creates: user_activities record (asset removal)
# Response: SuccessResponse

# Watchlist AI Analysis
GET /api/v1/watchlists/{watchlist_id}/ai-analysis
# Source: ai_watchlist_analysis table with latest analysis
# Includes: Asset scores, signal analysis, AI outlook
# Response: WatchlistAIAnalysisResponse

GET /api/v1/watchlists/{watchlist_id}/signals
# Source: ai_watchlist_analysis.generated_signals JSON field
# Filters: Active signals, confidence threshold
# Response: TradingSignalListResponse
```

### **🤖 AI/ML Model Management Endpoints**
```python
# AI Model Operations
GET /api/v1/ai/models
# Source: ai_models table filtered by status and model_type
# Includes: Performance metrics, configuration, training status
# Query params: model_type, status, architecture
# Response: AIModelListResponse

GET /api/v1/ai/models/{model_id}
# Source: ai_models table with detailed performance metrics
# Includes: Full configuration, training data, feature importance
# Response: AIModelDetailResponse

POST /api/v1/admin/ai/models
# Inserts: ai_models table with validation
# Creates: audit_logs record (model creation)
# Response: Created model data

PUT /api/v1/admin/ai/models/{model_id}
# Updates: ai_models table (status, configuration, performance_metrics)
# Creates: audit_logs record (model update)
# Response: Updated model data

# Model Performance & Analytics
GET /api/v1/ai/models/{model_id}/performance
# Source: model_performance table with historical data
# Includes: Accuracy trends, validation scores, trading metrics
# Response: ModelPerformanceResponse

GET /api/v1/ai/models/{model_id}/predictions
# Source: model_predictions table for recent predictions
# Query params: asset_id, timeframe, start_date, end_date
# Response: ModelPredictionListResponse

POST /api/v1/ai/models/{model_id}/train
# Creates: model_jobs table entry for training job
# Updates: ai_models.status = 'training'
# Response: TrainingJobResponse

GET /api/v1/ai/training-jobs
# Source: model_jobs table with job status
# Includes: Progress, error logs, completion estimates
# Response: TrainingJobListResponse

# AI Analysis Endpoints
GET /api/v1/ai/market-regime
# Source: ai_regime_analysis table (latest)
# Includes: Current regime, confidence, transition probability
# Response: RegimeAnalysisResponse

GET /api/v1/ai/sector-analysis
# Source: ai_sector_analysis table with cross-sector data
# Includes: Sector performance, rotation signals, correlations
# Response: SectorAnalysisResponse

GET /api/v1/ai/suggestions/{user_id}
# Source: ai_suggestions table filtered by user and status
# Includes: Asset recommendations, confidence scores, rationale
# Response: AISuggestionsResponse
```

### **🔔 Notifications & Alerts Endpoints**
```python
# User Notifications
GET /api/v1/notifications
# Source: notifications table filtered by user_id
# Query params: status, notification_type, priority
# Includes: Unread count, pagination
# Response: NotificationListResponse

GET /api/v1/notifications/{notification_id}
# Source: notifications table with full content
# Updates: notifications.read_at if first read
# Response: NotificationDetailResponse

PUT /api/v1/notifications/{notification_id}/read
# Updates: notifications.status = 'read', read_at = now()
# Creates: user_activities record (notification read)
# Response: SuccessResponse

PUT /api/v1/notifications/mark-all-read
# Updates: All unread notifications for user
# Creates: user_activities record (bulk read)
# Response: SuccessResponse

DELETE /api/v1/notifications/{notification_id}
# Updates: notifications.status = 'dismissed'
# Response: SuccessResponse

# Signal Alerts Management
GET /api/v1/alerts
# Source: signal_alerts table filtered by user_id and is_active
# Includes: Asset details, trigger conditions, status
# Response: SignalAlertListResponse

POST /api/v1/alerts
# Inserts: signal_alerts table with validation
# Creates: user_activities record (alert creation)
# Response: Created alert data

GET /api/v1/alerts/{alert_id}
# Source: signal_alerts joined with assets table
# Includes: Current asset price vs trigger value
# Response: SignalAlertDetailResponse

PUT /api/v1/alerts/{alert_id}
# Updates: signal_alerts table (trigger_value, condition, message)
# Validates: User ownership
# Response: Updated alert data

DELETE /api/v1/alerts/{alert_id}
# Updates: signal_alerts.is_active = false
# Creates: user_activities record (alert deletion)
# Response: SuccessResponse

# Alert Status & History
GET /api/v1/alerts/triggered
# Source: signal_alerts table where is_triggered = true
# Includes: Trigger timestamp, asset performance after trigger
# Response: TriggeredAlertListResponse

GET /api/v1/alerts/{alert_id}/history
# Source: user_activities filtered by entity_id (alert_id)
# Includes: Creation, modifications, trigger events
# Response: AlertHistoryResponse

# Admin Notification Management
POST /api/v1/admin/notifications/broadcast
# Inserts: Multiple notifications records for all users
# Creates: audit_logs record (broadcast notification)
# Response: BroadcastOperationResponse

GET /api/v1/admin/notifications/stats
# Source: notifications table aggregated by type, status
# Includes: Send rates, read rates, engagement metrics
# Response: NotificationStatsResponse
```

### **🛡️ Security & Session Management Endpoints**
```python
# Session Management
GET /api/v1/sessions
# Source: user_sessions table filtered by user_id and is_active
# Includes: Device info, IP address, last used timestamp
# Response: UserSessionListResponse

DELETE /api/v1/sessions/{session_id}
# Updates: user_sessions.is_active = false
# Creates: user_activities record (session termination)
# Response: SuccessResponse

DELETE /api/v1/sessions/terminate-all
# Updates: All user sessions to is_active = false except current
# Creates: user_activities record (bulk session termination)
# Response: SuccessResponse

# Rate Limiting & Security
GET /api/v1/security/rate-limits
# Source: rate_limiting table for current user/IP
# Includes: Current usage, limits, reset times
# Response: RateLimitStatusResponse

# Admin Security Monitoring
GET /api/v1/admin/security/audit-logs
# Source: audit_logs table with pagination and filtering
# Query params: user_id, action_type, date_range
# Response: AuditLogListResponse

GET /api/v1/admin/security/suspicious-activity
# Source: user_activities with anomaly detection
# Includes: Multiple failed logins, unusual patterns
# Response: SuspiciousActivityResponse

GET /api/v1/admin/security/active-sessions
# Source: user_sessions table with user details
# Includes: Session duration, device info, geographical data
# Response: ActiveSessionListResponse

POST /api/v1/admin/security/terminate-session/{session_id}
# Updates: user_sessions.is_active = false
# Creates: audit_logs record (admin session termination)
# Response: SuccessResponse

# User Feedback System
GET /api/v1/feedback
# Source: user_feedback table filtered by user_id
# Response: UserFeedbackListResponse

POST /api/v1/feedback
# Inserts: user_feedback table with user context
# Creates: notifications record for admin review
# Response: Created feedback data

GET /api/v1/admin/feedback
# Source: user_feedback table with user details
# Query params: status, feedback_type, priority
# Response: AdminFeedbackListResponse

PUT /api/v1/admin/feedback/{feedback_id}
# Updates: user_feedback (status, response_message, reviewed_by)
# Creates: notifications record for user response
# Response: Updated feedback data
```

### **📈 System Analytics & Monitoring Endpoints**
```python
# System Health Monitoring
GET /api/v1/admin/system/health
# Source: system_health table (latest record)
# Includes: API status, database performance, ML model status
# Response: SystemHealthResponse

GET /api/v1/admin/system/health/history
# Source: system_health table with time series data
# Query params: start_date, end_date, metrics
# Response: SystemHealthHistoryResponse

# Analytics & Reporting
GET /api/v1/admin/analytics/users
# Source: users table with aggregated statistics
# Includes: Registration trends, activity patterns, retention
# Response: UserAnalyticsResponse

GET /api/v1/admin/analytics/assets
# Source: assets table with usage statistics
# Includes: Most accessed assets, data quality trends
# Response: AssetAnalyticsResponse

GET /api/v1/admin/analytics/api-usage
# Source: user_activities table aggregated by endpoint
# Includes: Request counts, response times, error rates
# Response: APIUsageAnalyticsResponse

GET /api/v1/admin/analytics/ml-performance
# Source: model_performance table with accuracy trends
# Includes: Model comparison, prediction accuracy over time
# Response: MLPerformanceAnalyticsResponse

# Data Quality Reports
GET /api/v1/admin/data-quality/assets
# Source: data_quality_reports table for all assets
# Includes: Quality scores, missing data, validation errors
# Response: AssetDataQualityResponse

GET /api/v1/admin/data-quality/price-data
# Source: price_data with gap analysis and validation
# Query params: asset_id, date_range
# Response: PriceDataQualityResponse

POST /api/v1/admin/data-quality/validate
# Executes: Data validation across all tables
# Creates: data_quality_reports records
# Response: ValidationOperationResponse
```

---

## 🔗 **Database Relationship Summary**

### **Core Relationships Based on ERD:**
```
📊 User Management Flow:
users → user_sessions → user_activities
users → portfolios → portfolio_assets → assets
users → watchlists → watchlist_assets → assets
users → notifications, signal_alerts, user_feedback

💰 Asset Data Flow:
assets → price_data → technical_indicators (JSON)
assets → ai_suggestions, ai_regime_analysis
price_data → price_data_archive (historical)

🤖 AI/ML Flow:
ai_models → model_predictions, model_performance
ai_models → ai_regime_analysis, ai_sector_analysis
ai_models → ai_watchlist_analysis, ai_portfolio_analysis

🔔 Notification Flow:
users → notifications, signal_alerts
ai_models → ai_suggestions → notifications
portfolio_assets → signal_alerts (price targets)
```

---

## 📝 **Implementation Guidelines**

### **Database Optimization:**
- Use partitioning for `price_data` table by date
- Implement proper indexing on frequently queried fields
- Archive old data to `price_data_archive` table
- Use JSON fields efficiently with GIN indexes

### **API Security:**
- Implement proper authentication middleware
- Rate limiting based on `rate_limiting` table
- Audit all operations in `audit_logs` table
- Session management via `user_sessions` table

### **Performance Considerations:**
- Cache frequently accessed data (asset prices, regime analysis)
- Use database functions for complex aggregations
- Implement pagination for all list endpoints
- Background jobs for AI model training and data processing
```
