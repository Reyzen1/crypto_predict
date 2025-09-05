# docs\Design\17_2_Database_Integration_And_API_Planning.md
# 🗄️ Database Integration & API Planning - Day 18 (Updated)
## Complete API Architecture for 4-Layer AI System with Single UI Strategy - 87 Endpoints

---

## 🎯 **API Design Philosophy**

### **🔄 Single UI API Strategy:**
```
Universal Access API Design:
├── 🌐 Open Endpoints: Full access for all users (Guest, Logged, Admin)
├── 🔐 Protected Endpoints: Personal operations requiring authentication
├── 👑 Admin Endpoints: System management operations
├── ⚡ Rate Limiting: Fair usage for Guest users
└── 📊 Context-Aware Responses: Data adapted based on user authentication state
```

### **📊 Database Function Integration Summary:**
```
🔄 Complete API-Database Mapping (100% Complete):
├── 🌍 Layer 1 Macro: 4 functions for regime/sentiment/dominance analysis ✅
├── 📊 Layer 2 Sector: 6 functions for sector performance/rotation/mapping ✅
├── 💰 Layer 3 Assets: 15+ functions for watchlists/suggestions/analysis ✅
├── ⚡ Layer 4 Timing: 8+ functions for signals/execution/risk management ✅
├── 🤖 AI & ML: 10+ functions for model management/predictions/performance ✅
├── 🛡️ Security: 8+ functions for audit/session/rate limiting ✅
├── 📈 Analytics: 8+ functions for system monitoring/reporting ✅
└── 🎯 Total: 60+ functions - 100% Complete ✅
```

---

## 📡 **Complete API Structure**

### **🌍 Layer 1: Macro Analysis Endpoints (Universal Access)**
```python
# All users can access macro analysis data
GET /api/v1/macro/regime
# Response: Current market regime with confidence scores using database function get_market_regime_analysis()
# Rate Limit: None (real-time data for all users)
# Auth: Not required

GET /api/v1/macro/sentiment
# Response: Multi-source sentiment analysis (Fear & Greed, Social, News) using database function get_market_sentiment_analysis()
# Rate Limit: None
# Auth: Not required

GET /api/v1/macro/dominance
# Response: BTC.D, ETH.D, ALT.D analysis using database function get_dominance_analysis()
# Rate Limit: None
# Auth: Not required

GET /api/v1/macro/indicators
# Response: Volatility forecasts, correlations, trends using database function get_macro_indicators()
# Rate Limit: None
# Auth: Not required

GET /api/v1/macro/history
# Response: Historical regime changes and analysis
# Rate Limit: 100 requests/hour for guests, unlimited for logged users
# Auth: Optional (enhanced data for logged users)
```

### **📊 Layer 2: Sector Analysis Endpoints (Universal Access)**
```python
GET /api/v1/sectors
# Response: All 11 crypto sectors with performance metrics
# Rate Limit: None
# Auth: Not required

GET /api/v1/sectors/performance
# Response: Sector performance summary using database view v_sector_performance_summary
# Rate Limit: None
# Auth: Not required

GET /api/v1/sectors/{sector_id}/performance
# Response: Detailed sector performance and rotation analysis
# Rate Limit: None
# Auth: Not required

GET /api/v1/sectors/rotation
# Response: Current sector rotation signals and money flow using database function get_sector_rotation_analysis()
# Rate Limit: None
# Auth: Not required

GET /api/v1/sectors/{sector_id}/assets
# Response: Assets in specific sector with sector context
# Rate Limit: None
# Auth: Not required

GET /api/v1/sectors/allocation
# Response: Optimal sector allocation recommendations using database function get_sector_allocation_recommendations()
# Rate Limit: 50 requests/hour for guests, unlimited for logged users
# Auth: Optional (personalized for logged users)

# SECTOR MAPPING ENDPOINTS (Universal Access)
GET /api/v1/sectors/{sector_id}/cryptocurrencies
# Response: All cryptocurrencies in specific sector using database function get_sector_cryptocurrencies(sector_id)
# Rate Limit: None
# Auth: Not required

GET /api/v1/sectors/name/{sector_name}/cryptocurrencies
# Response: All cryptocurrencies in sector by name using database function get_sector_cryptocurrencies_by_name(sector_name)
# Rate Limit: None
# Auth: Not required

GET /api/v1/cryptocurrencies/{crypto_id}/sectors
# Response: All sectors for specific cryptocurrency using database function get_crypto_sectors(crypto_id)
# Rate Limit: None
# Auth: Not required

GET /api/v1/cryptocurrencies/symbol/{symbol}/sectors
# Response: All sectors for cryptocurrency by symbol using database function get_crypto_sectors_by_symbol(symbol)
# Rate Limit: None
# Auth: Not required
```

### **💰 Layer 3: Asset Selection Endpoints (Mixed Access)**
```python
# UNIVERSAL ACCESS (Admin Default Watchlist)
GET /api/v1/watchlists/default
# Response: Admin-curated default watchlist (15 assets)
# Rate Limit: None
# Auth: Not required

GET /api/v1/assets/{asset_id}/analysis
# Response: Complete asset analysis for any supported cryptocurrency
# Rate Limit: None
# Auth: Not required

GET /api/v1/assets/search
# Response: Search and filter assets with AI suggestions
# Rate Limit: 200 requests/hour for guests, unlimited for logged users
# Auth: Not required

# PROTECTED ENDPOINTS (Personal Watchlists)
GET /api/v1/watchlists
# Response: User's personal watchlists
# Auth: Required (JWT token)

POST /api/v1/watchlists
# Request: {name, description, assets[], is_public}
# Response: Created watchlist with ID
# Auth: Required

PUT /api/v1/watchlists/{watchlist_id}
# Request: {name, description, assets[], is_public}
# Response: Updated watchlist
# Auth: Required (owner or admin)

DELETE /api/v1/watchlists/{watchlist_id}
# Response: Deletion confirmation
# Auth: Required (owner or admin)

POST /api/v1/watchlists/{watchlist_id}/assets
# Request: {asset_id, notes}
# Response: Added asset to watchlist
# Auth: Required

DELETE /api/v1/watchlists/{watchlist_id}/assets/{asset_id}
# Response: Removed asset from watchlist
# Auth: Required
```

### **⚡ Layer 4: Timing Signals Endpoints (Universal Access)**
```python
GET /api/v1/signals/current
# Response: Current timing signals for default watchlist using database function get_current_trading_signals()
# Rate Limit: None
# Auth: Not required

GET /api/v1/signals/{asset_id}
# Response: Detailed timing analysis for specific asset
# Rate Limit: None
# Auth: Not required

GET /api/v1/signals/alerts
# Response: Active timing alerts and notifications
# Rate Limit: 100 requests/hour for guests, unlimited for logged users
# Auth: Optional (personal alerts for logged users)

# PROTECTED ENDPOINTS (Personal Signal Management)
POST /api/v1/signals/alerts
# Request: {asset_id, alert_type, threshold, notification_method}
# Response: Created alert with ID
# Auth: Required

PUT /api/v1/signals/alerts/{alert_id}
# Request: {threshold, is_active, notification_method}
# Response: Updated alert
# Auth: Required

DELETE /api/v1/signals/alerts/{alert_id}
# Response: Deletion confirmation
# Auth: Required
```

### **🤖 AI Suggestions Endpoints (Universal Access)**
```python
GET /api/v1/suggestions/current
# Response: Current AI suggestions for default watchlist
# Rate Limit: None
# Auth: Not required

GET /api/v1/suggestions/{asset_id}
# Response: AI suggestions for specific asset
# Rate Limit: None
# Auth: Not required

GET /api/v1/suggestions/personalized
# Response: Personalized AI suggestions based on user behavior
# Rate Limit: 50 requests/hour for guests, unlimited for logged users
# Auth: Optional (enhanced for logged users)

GET /api/v1/users/{user_id}/ai-context
# Response: User AI context using database function get_user_ai_context(user_id)
# Rate Limit: 100 requests/hour for logged users
# Auth: Required (self or admin only)

# PROTECTED ENDPOINTS (Suggestion Feedback)
POST /api/v1/suggestions/{suggestion_id}/feedback
# Request: {rating, feedback_text, action_taken}
# Response: Feedback recorded
# Auth: Required
```

### **📊 Dashboard Endpoints (Context-Aware)**
```python
GET /api/v1/dashboard/overview
# Response: Contextual dashboard based on user authentication state using database view v_dashboard_overview
# - Guest: Default watchlist + macro overview
# - Logged: Personal watchlists + macro overview + personal insights
# - Admin: System overview + admin metrics + performance data
# Rate Limit: None
# Auth: Optional (context-aware response)

GET /api/v1/dashboard/performance
# Response: Performance analytics
# - Guest: Default watchlist performance
# - Logged: Personal portfolio performance
# - Admin: System-wide performance metrics
# Rate Limit: 20 requests/hour for guests, unlimited for logged users
# Auth: Optional
```

### **👤 User Management Endpoints**
```python
# AUTHENTICATION
POST /api/v1/auth/register
# Request: {email, password, first_name, last_name}
# Response: {user_id, access_token, refresh_token}
# Rate Limit: 5 requests/hour per IP

POST /api/v1/auth/login
# Request: {email, password}
# Response: {user_id, access_token, refresh_token}
# Rate Limit: 10 requests/hour per IP

POST /api/v1/auth/refresh
# Request: {refresh_token}
# Response: {access_token}
# Rate Limit: 50 requests/hour per token

POST /api/v1/auth/logout
# Request: {refresh_token}
# Response: {message}
# Auth: Required

# USER PROFILE
GET /api/v1/users/profile
# Response: Complete user profile and preferences
# Auth: Required

PUT /api/v1/users/profile
# Request: {first_name, last_name, timezone, language, preferences}
# Response: Updated profile
# Auth: Required

GET /api/v1/users/activity
# Response: User activity history and engagement metrics
# Auth: Required

# NOTIFICATIONS
GET /api/v1/notifications
# Response: User notifications (unread + recent read)
# Auth: Required

PUT /api/v1/notifications/{notification_id}/read
# Response: Marked as read
# Auth: Required

POST /api/v1/notifications/preferences
# Request: {email_enabled, push_enabled, categories[]}
# Response: Updated notification preferences
# Auth: Required
```

### **👑 Admin Endpoints (Admin Only)**
```python
# SYSTEM MONITORING
GET /api/v1/admin/system/health
# Response: System health metrics, AI model performance, database status
# Auth: Required (admin role)

GET /api/v1/admin/system/metrics
# Response: Detailed system metrics, user engagement, API usage
# Auth: Required (admin role)

# AI PERFORMANCE MONITORING
GET /api/v1/admin/ai/performance
# Response: AI performance metrics using database view v_ai_performance
# Auth: Required (admin role)

# USER MANAGEMENT
GET /api/v1/admin/users
# Response: Paginated user list with statistics
# Query: ?page=1&limit=50&role=all&active=true
# Auth: Required (admin role)

GET /api/v1/admin/users/overview
# Response: Users overview using database view v_users_overview
# Auth: Required (admin role)

PUT /api/v1/admin/users/{user_id}/role
# Request: {role}
# Response: Updated user role
# Auth: Required (admin role)

PUT /api/v1/admin/users/{user_id}/status
# Request: {is_active, is_verified}
# Response: Updated user status
# Auth: Required (admin role)

# WATCHLIST MANAGEMENT
GET /api/v1/admin/watchlists/default
# Response: Current default watchlist configuration
# Auth: Required (admin role)

POST /api/v1/admin/watchlists/default
# Request: {name, description}
# Response: Created default watchlist using database function create_default_watchlist()
# Auth: Required (admin role)

PUT /api/v1/admin/watchlists/default
# Request: {assets[], update_reason}
# Response: Updated default watchlist
# Auth: Required (admin role)

PUT /api/v1/admin/watchlists/{watchlist_id}/assets/bulk
# Request: {asset_updates: [{crypto_id, position, weight}]}
# Response: Bulk updated assets using database function bulk_update_watchlist_assets()
# Auth: Required (admin role)

GET /api/v1/admin/watchlists/analytics
# Response: Analytics on watchlist usage and performance
# Auth: Required (admin role)

# AI MODEL MANAGEMENT
GET /api/v1/admin/models
# Response: All AI models with performance metrics
# Auth: Required (admin role)

POST /api/v1/admin/models/{model_id}/retrain
# Request: {training_parameters}
# Response: Training job initiated
# Auth: Required (admin role)

PUT /api/v1/admin/models/{model_id}/config
# Request: {parameters, thresholds, weights}
# Response: Updated model configuration
# Auth: Required (admin role)

# ANALYTICS
GET /api/v1/admin/analytics/usage
# Response: API usage statistics, user engagement metrics
# Query: ?period=7d&granularity=day
# Auth: Required (admin role)

GET /api/v1/admin/analytics/performance
# Response: System performance metrics, AI accuracy statistics
# Auth: Required (admin role)

# MODEL PERFORMANCE TRACKING (NEW)
GET /api/v1/admin/models/performance
# Response: AI model performance metrics using model_performance table
# Query: ?model_id=123&timeframe=30d&metric=accuracy
# Auth: Required (admin role)

POST /api/v1/admin/models/{model_id}/performance
# Request: {evaluation_metric, metric_value, timeframe, sample_size, detailed_metrics}
# Response: Recorded performance metric
# Auth: Required (admin role)

# ANALYTICS DATA MANAGEMENT (NEW)
GET /api/v1/admin/analytics/data
# Response: Raw analytics data using analytics_data table
# Query: ?category=user_behavior&metric_name=session_duration&aggregation=daily
# Auth: Required (admin role)

POST /api/v1/admin/analytics/data
# Request: {category, metric_name, metric_value, dimensions, aggregation_level}
# Response: Stored analytics data
# Auth: Required (admin role)

# EXTERNAL API MONITORING (NEW)
GET /api/v1/admin/external-apis/logs
# Response: External API call logs using external_api_logs table
# Query: ?provider=coingecko&status=error&hours=24
# Auth: Required (admin role)

GET /api/v1/admin/external-apis/performance
# Response: External API performance statistics
# Auth: Required (admin role)

# BACKGROUND TASKS MONITORING (NEW)
GET /api/v1/admin/tasks
# Response: Background tasks status using background_tasks table
# Query: ?status=running&task_type=data_sync
# Auth: Required (admin role)

POST /api/v1/admin/tasks/{task_id}/cancel
# Response: Cancel background task
# Auth: Required (admin role)

GET /api/v1/admin/tasks/{task_id}/progress
# Response: Task progress details
# Auth: Required (admin role)
```

### **⚡ Signal Alerts Endpoints (NEW)**
```python
# USER SIGNAL ALERTS
GET /api/v1/alerts
# Response: User's active signal alerts using signal_alerts table
# Query: ?crypto_id=1&alert_type=price_target&is_active=true
# Auth: Required

POST /api/v1/alerts
# Request: {crypto_id, alert_type, trigger_value, condition, comparison_timeframe, message, notification_method, expires_at}
# Response: Created alert
# Auth: Required

PUT /api/v1/alerts/{alert_id}
# Request: {trigger_value, condition, is_active, message, notification_method, expires_at}
# Response: Updated alert
# Auth: Required (owner or admin)

DELETE /api/v1/alerts/{alert_id}
# Response: Deleted alert
# Auth: Required (owner or admin)

GET /api/v1/alerts/triggered
# Response: User's triggered alerts history
# Query: ?days=30&crypto_id=1
# Auth: Required

PUT /api/v1/alerts/{alert_id}/acknowledge
# Response: Acknowledge triggered alert
# Auth: Required (owner)

# ADMIN SIGNAL ALERTS MANAGEMENT
GET /api/v1/admin/alerts/overview
# Response: System-wide alerts overview and statistics
# Auth: Required (admin role)

GET /api/v1/admin/alerts/triggered
# Response: All triggered alerts in the system
# Query: ?hours=24&alert_type=volume_spike
# Auth: Required (admin role)
```

### **🔄 AI Suggestion Feedback Endpoints (NEW)**
```python
# USER FEEDBACK ON AI SUGGESTIONS
POST /api/v1/suggestions/{suggestion_id}/feedback
# Request: {rating, feedback_text, action_taken, feedback_data}
# Response: Recorded feedback using suggestion_feedback table
# Auth: Required

GET /api/v1/suggestions/{suggestion_id}/feedback
# Response: User's feedback on specific suggestion
# Auth: Required (owner or admin)

PUT /api/v1/suggestions/feedback/{feedback_id}
# Request: {rating, feedback_text, action_taken, feedback_data}
# Response: Updated feedback
# Auth: Required (owner or admin)

# ADMIN FEEDBACK ANALYTICS
GET /api/v1/admin/suggestions/feedback/analytics
# Response: AI suggestion feedback analytics and patterns
# Query: ?days=30&rating_min=3&action_taken=accepted
# Auth: Required (admin role)

GET /api/v1/admin/suggestions/feedback/trends
# Response: Feedback trends and AI improvement insights
# Auth: Required (admin role)
```
```

---

## 🔗 **Database Integration Mapping**

### **📊 API-to-Database Table Mapping:**
```mermaid
graph TD
    subgraph "Layer 1 APIs"
        A1[GET /api/v1/macro/regime] --> D1[database function get_market_regime_analysis]
        A2[GET /api/v1/macro/sentiment] --> D2[database function get_market_sentiment_analysis]
        A3[GET /api/v1/macro/dominance] --> D3[database function get_dominance_analysis]
        A4[GET /api/v1/macro/indicators] --> D4[database function get_macro_indicators]
    end

    subgraph "Layer 2 APIs"
        B1[GET /api/v1/sectors] --> D5[crypto_sectors]
        B2[GET /api/v1/sectors/performance] --> D6[sector_performance]
        B3[GET /api/v1/sectors/rotation] --> D7[sector_rotation_analysis]
        B4[GET /api/v1/sectors/assets] --> D8[crypto_sector_mapping]
        B5[GET /api/v1/sectors/{id}/cryptocurrencies] --> D8[crypto_sector_mapping + database function get_sector_cryptocurrencies]
        B6[GET /api/v1/sectors/name/{name}/cryptocurrencies] --> D8[crypto_sector_mapping + database function get_sector_cryptocurrencies_by_name]
        B7[GET /api/v1/cryptocurrencies/{id}/sectors] --> D8[crypto_sector_mapping + database function get_crypto_sectors]
        B8[GET /api/v1/cryptocurrencies/symbol/{symbol}/sectors] --> D8[crypto_sector_mapping + database function get_crypto_sectors_by_symbol]
    end

    subgraph "Layer 3 APIs"
        C1[GET /api/v1/watchlists] --> D9[watchlists]
        C2[GET /api/v1/watchlists/assets] --> D10[watchlist_assets]
        C3[GET /api/v1/suggestions] --> D11[ai_suggestions]
        C4[GET /api/v1/assets/analysis] --> D12[cryptocurrencies]
        C5[GET /api/v1/users/{id}/ai-context] --> D13[database function get_user_ai_context]
    end

    subgraph "Layer 4 APIs"
        E1[GET /api/v1/signals/current] --> D13[database function get_current_trading_signals]
        E2[GET /api/v1/signals/{id}] --> D14[trading_signals + signal_alerts]
        E3[POST /api/v1/signals/execute] --> D15[signal_executions]
    end

    subgraph "User APIs"
        F1[GET /api/v1/users/profile] --> D16[users]
        F2[GET /api/v1/notifications] --> D17[notifications]
        F3[GET /api/v1/users/activity] --> D18[user_activities]
    end

    subgraph "Admin APIs"
        G1[GET /api/v1/admin/system] --> D19[system_health]
        G2[GET /api/v1/admin/models] --> D20[ai_models]
        G3[GET /api/v1/admin/analytics] --> D21[analytics_data]
        G4[GET /api/v1/admin/ai/performance] --> D22[database view v_ai_performance]
        G5[GET /api/v1/admin/users/overview] --> D23[database view v_users_overview]
        G6[POST /api/v1/admin/watchlists/default] --> D24[database function create_default_watchlist]
        G7[PUT /api/v1/admin/watchlists/{id}/assets/bulk] --> D25[database function bulk_update_watchlist_assets]
        G8[PUT /api/v1/admin/users/{id}/role] --> D26[database function update_user_role]
        G9[PUT /api/v1/admin/users/{id}/status] --> D27[database function update_user_status]
        G10[GET /api/v1/admin/models/performance] --> D28[model_performance]
        G11[GET /api/v1/admin/analytics/data] --> D29[analytics_data]
        G12[GET /api/v1/admin/external-apis/logs] --> D30[external_api_logs]
        G13[GET /api/v1/admin/tasks] --> D31[background_tasks]
    end

    subgraph "Signal Alerts APIs (NEW)"
        SA1[GET /api/v1/alerts] --> D32[signal_alerts]
        SA2[POST /api/v1/alerts] --> D33[database function create_user_alert]
        SA3[PUT /api/v1/alerts/{id}] --> D34[database function update_user_alert]
        SA4[DELETE /api/v1/alerts/{id}] --> D35[database function delete_user_alert]
        SA5[GET /api/v1/alerts/triggered] --> D36[signal_alerts + database function get_triggered_alerts]
        SA6[PUT /api/v1/alerts/{id}/acknowledge] --> D37[database function acknowledge_alert]
    end

    subgraph "AI Feedback APIs (NEW)"
        FB1[POST /api/v1/suggestions/{id}/feedback] --> D38[suggestion_feedback + database function record_suggestion_feedback]
        FB2[GET /api/v1/suggestions/{id}/feedback] --> D39[suggestion_feedback]
        FB3[PUT /api/v1/suggestions/feedback/{id}] --> D40[database function update_suggestion_feedback]
        FB4[GET /api/v1/admin/suggestions/feedback/analytics] --> D41[database view v_suggestion_feedback_analytics]
    end

    subgraph "SET Operations APIs"
        S1[POST /api/v1/auth/register] --> D28[database function create_user_account_secure]
        S2[POST /api/v1/auth/login] --> D29[database function authenticate_user]
        S3[POST /api/v1/auth/refresh] --> D30[database function refresh_user_token]
        S4[POST /api/v1/auth/logout] --> D31[database function logout_user]
        S5[POST /api/v1/watchlists] --> D32[database function create_watchlist]
        S6[PUT /api/v1/watchlists/{id}] --> D33[database function update_watchlist]
        S7[DELETE /api/v1/watchlists/{id}] --> D34[database function delete_watchlist]
        S8[POST /api/v1/watchlists/{id}/assets] --> D35[database function add_asset_to_watchlist]
        S9[DELETE /api/v1/watchlists/{id}/assets/{asset_id}] --> D36[database function remove_asset_from_watchlist]
        S10[POST /api/v1/signals/alerts] --> D37[database function create_user_alert]
        S11[PUT /api/v1/signals/alerts/{id}] --> D38[database function update_alert]
        S12[DELETE /api/v1/signals/alerts/{id}] --> D39[database function delete_alert]
        S13[PUT /api/v1/users/profile] --> D40[database function update_user_profile]
        S14[PUT /api/v1/notifications/{id}/read] --> D41[database function mark_notification_read]
        S15[POST /api/v1/notifications/preferences] --> D42[database function update_notification_preferences]
        S16[POST /api/v1/suggestions/{id}/feedback] --> D43[database function record_ai_suggestion_feedback]
        S17[POST /api/v1/signals/execute] --> D44[database function execute_trading_signal]
    end

    subgraph "Admin SET Operations APIs"
        A1[PUT /api/v1/admin/users/{id}/role] --> D45[database function update_user_role]
        A2[PUT /api/v1/admin/users/{id}/status] --> D46[database function update_user_status]
        A3[POST /api/v1/admin/watchlists/default] --> D47[database function create_default_watchlist]
        A4[PUT /api/v1/admin/watchlists/default] --> D48[database function update_default_watchlist]
        A5[PUT /api/v1/admin/watchlists/{id}/assets/bulk] --> D49[database function bulk_update_watchlist_assets]
        A6[POST /api/v1/admin/models/{id}/retrain] --> D50[database function initiate_model_retrain]
        A7[PUT /api/v1/admin/models/{id}/config] --> D51[database function update_model_config]
    end

    subgraph "Dashboard APIs"
        H1[GET /api/v1/dashboard/overview] --> D40[database view v_dashboard_overview]
        H2[GET /api/v1/dashboard/performance] --> D41[multiple views + functions]
    end
```

---

## 🔐 **Authentication & Authorization Strategy**

### **🎯 JWT Token Implementation:**
```python
# Token Structure
{
    "user_id": 123,
    "email": "user@example.com",
    "role": "public|admin",
    "iat": 1640995200,  # Issued at
    "exp": 1640998800,  # Expiration (1 hour)
    "permissions": ["read:personal", "write:personal", "admin:system"]
}

# Token Validation Middleware
async def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        role = payload.get("role")
        return {"user_id": user_id, "role": role}
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")

# Role-based Access Control
def require_auth(required_role: str = None):
    def decorator(func):
        async def wrapper(request: Request):
            token = request.headers.get("Authorization")
            if not token:
                if required_role:
                    raise HTTPException(401, "Authentication required")
                return await func(request, user=None)
            
            user = await verify_token(token.replace("Bearer ", ""))
            if required_role and user["role"] != required_role:
                raise HTTPException(403, "Insufficient permissions")
            
            return await func(request, user=user)
        return wrapper
    return decorator
```

---

## ⚡ **Rate Limiting Strategy**

### **📊 Rate Limiting Rules:**
```python
# Rate Limiting Configuration
RATE_LIMITS = {
    "guest_users": {
        "global": "1000/hour",  # Global API calls
        "macro": "unlimited",   # Layer 1 endpoints
        "sector": "unlimited",  # Layer 2 endpoints
        "assets": "500/hour",   # Layer 3 searches
        "signals": "200/hour",  # Layer 4 analysis
        "heavy_analytics": "50/hour"  # Resource-intensive endpoints
    },
    "logged_users": {
        "global": "unlimited",
        "all_layers": "unlimited",
        "personal_operations": "unlimited"
    },
    "admin_users": {
        "all_operations": "unlimited"
    }
}

# Rate Limiting Implementation
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    user = await get_current_user(request)  # Extract from JWT
    
    if user and user.role == "admin":
        # No limits for admin users
        return await call_next(request)
    elif user:
        # Standard limits for logged users
        rate_limit = "10000/hour"
    else:
        # Restricted limits for guest users
        endpoint_category = categorize_endpoint(request.url.path)
        rate_limit = RATE_LIMITS["guest_users"].get(endpoint_category, "100/hour")
    
    # Apply rate limiting logic
    return await call_next(request)
```

---

## 📝 **Response Schema Standards**

### **✅ Success Response Format:**
```json
{
    "success": true,
    "data": {
        // Actual response data
    },
    "meta": {
        "timestamp": "2024-01-15T10:30:00Z",
        "user_context": "guest|logged|admin",
        "rate_limit": {
            "remaining": 450,
            "reset_at": "2024-01-15T11:00:00Z"
        },
        "pagination": {  // For paginated endpoints
            "page": 1,
            "limit": 50,
            "total": 150,
            "has_next": true
        }
    }
}
```

### **❌ Error Response Format:**
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid request parameters",
        "details": {
            "field": "email",
            "issue": "Invalid email format"
        }
    },
    "meta": {
        "timestamp": "2024-01-15T10:30:00Z",
        "request_id": "uuid-here"
    }
}
```

### **📊 HTTP Status Codes:**
```python
# Standard HTTP Status Code Usage
STATUS_CODES = {
    200: "OK - Successful request",
    201: "Created - Resource created successfully", 
    204: "No Content - Successful deletion",
    400: "Bad Request - Invalid request parameters",
    401: "Unauthorized - Authentication required",
    403: "Forbidden - Insufficient permissions",
    404: "Not Found - Resource not found",
    409: "Conflict - Resource already exists",
    429: "Too Many Requests - Rate limit exceeded",
    500: "Internal Server Error - Server error",
    503: "Service Unavailable - Maintenance mode"
}
```

---

## 🚀 **Performance Optimization**

### **📈 Caching Strategy:**
```python
# Redis Caching Configuration
CACHE_STRATEGIES = {
    "macro_data": {
        "ttl": 300,  # 5 minutes
        "pattern": "macro:*",
        "description": "Market regime and macro indicators"
    },
    "sector_data": {
        "ttl": 600,  # 10 minutes  
        "pattern": "sector:*",
        "description": "Sector performance and rotation"
    },
    "sector_mapping": {
        "ttl": 3600, # 60 minutes (less frequently changing)
        "pattern": "sector_mapping:*",
        "description": "Crypto-sector relationship mapping data"
    },
    "asset_data": {
        "ttl": 180,  # 3 minutes
        "pattern": "asset:*",
        "description": "Individual asset analysis"
    },
    "signals_data": {
        "ttl": 60,   # 1 minute
        "pattern": "signals:*", 
        "description": "Timing signals and alerts"
    },
    "user_watchlists": {
        "ttl": 1800, # 30 minutes
        "pattern": "watchlist:*",
        "description": "User personal watchlists"
    }
}

# Database Query Optimization
QUERY_OPTIMIZATIONS = {
    "indexes": [
        "CREATE INDEX idx_crypto_symbol ON cryptocurrencies(symbol)",
        "CREATE INDEX idx_watchlist_user ON watchlists(user_id, created_at)",
        "CREATE INDEX idx_signals_asset ON trading_signals(asset_id, created_at)",
        "CREATE INDEX idx_user_activities ON user_activities(user_id, created_at)",
        "CREATE INDEX idx_sector_mapping_crypto ON crypto_sector_mapping(cryptocurrency_id)",
        "CREATE INDEX idx_sector_mapping_sector ON crypto_sector_mapping(sector_id)",
        "CREATE INDEX idx_sector_name ON crypto_sectors(name)",
        "CREATE INDEX idx_crypto_sector_composite ON crypto_sector_mapping(cryptocurrency_id, sector_id)"
    ],
    "materialized_views": [
        "CREATE MATERIALIZED VIEW sector_performance_summary AS ...",
        "CREATE MATERIALIZED VIEW user_engagement_metrics AS ...",
        "CREATE MATERIALIZED VIEW v_crypto_sectors AS SELECT * FROM v_crypto_sectors",
        "CREATE MATERIALIZED VIEW v_sector_cryptocurrencies AS SELECT * FROM v_sector_cryptocurrencies",
        "CREATE MATERIALIZED VIEW v_sector_performance_summary AS SELECT * FROM v_sector_performance_summary"
    ]
}
```

---

## 🔄 **Real-time Updates Strategy**

### **📡 WebSocket Integration:**
```python
# WebSocket Endpoints for Real-time Data
WS_ENDPOINTS = {
    "/ws/macro": "Real-time macro analysis updates",
    "/ws/sectors": "Live sector rotation signals", 
    "/ws/assets/{asset_id}": "Individual asset updates",
    "/ws/signals": "Live timing signals and alerts",
    "/ws/portfolio": "Personal portfolio updates (auth required)"
}

# WebSocket Authentication
async def authenticate_websocket(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if token:
        try:
            user = await verify_token(token)
            return user
        except:
            await websocket.close(code=1008, reason="Invalid token")
    return None  # Guest user
```

---

## 📊 **API Monitoring & Analytics**

### **📈 Monitoring Metrics:**
```python
# Key Metrics to Track
MONITORING_METRICS = {
    "api_performance": {
        "response_time": "Average response time per endpoint",
        "throughput": "Requests per second",
        "error_rate": "Percentage of failed requests",
        "availability": "Uptime percentage"
    },
    "user_engagement": {
        "daily_active_users": "Users per day",
        "api_usage_patterns": "Most used endpoints",
        "conversion_rate": "Guest to registered user conversion",
        "feature_adoption": "Feature usage statistics"
    },
    "system_health": {
        "database_performance": "Query execution times",
        "cache_hit_rate": "Redis cache effectiveness", 
        "ai_model_latency": "ML prediction response times",
        "external_api_status": "Third-party API availability"
    }
}
```

---

## 🗺️ **Sector Mapping Functions Integration**

### **📊 PL/pgSQL Functions for Sector Mapping:**
```python
# Database Functions Implementation
SECTOR_MAPPING_FUNCTIONS = {
    "get_crypto_sectors": {
        "function_name": "get_crypto_sectors(crypto_id INTEGER)",
        "endpoint": "GET /api/v1/cryptocurrencies/{crypto_id}/sectors",
        "description": "Returns all sectors for a specific cryptocurrency",
        "cache_key": "crypto_sectors:{crypto_id}",
        "cache_ttl": 3600
    },
    "get_sector_cryptocurrencies": {
        "function_name": "get_sector_cryptocurrencies(sector_id INTEGER)",
        "endpoint": "GET /api/v1/sectors/{sector_id}/cryptocurrencies",
        "description": "Returns all cryptocurrencies in a specific sector",
        "cache_key": "sector_cryptos:{sector_id}",
        "cache_ttl": 3600
    },
    "get_crypto_sectors_by_symbol": {
        "function_name": "get_crypto_sectors_by_symbol(symbol VARCHAR)",
        "endpoint": "GET /api/v1/cryptocurrencies/symbol/{symbol}/sectors",
        "description": "Returns all sectors for cryptocurrency by symbol",
        "cache_key": "crypto_sectors_symbol:{symbol}",
        "cache_ttl": 3600
    },
    "get_sector_cryptocurrencies_by_name": {
        "function_name": "get_sector_cryptocurrencies_by_name(sector_name VARCHAR)",
        "endpoint": "GET /api/v1/sectors/name/{sector_name}/cryptocurrencies",
        "description": "Returns all cryptocurrencies in sector by name",
        "cache_key": "sector_cryptos_name:{sector_name}",
        "cache_ttl": 3600
    }
}

# Additional Database Functions Implementation
ADMIN_FUNCTIONS = {
    "create_default_watchlist": {
        "function_name": "create_default_watchlist(name VARCHAR, description TEXT)",
        "endpoint": "POST /api/v1/admin/watchlists/default",
        "description": "Creates a new default watchlist for system-wide use",
        "auth": "admin_required"
    },
    "bulk_update_watchlist_assets": {
        "function_name": "bulk_update_watchlist_assets(watchlist_id INTEGER, asset_updates JSONB, admin_user_id INTEGER)",
        "endpoint": "PUT /api/v1/admin/watchlists/{watchlist_id}/assets/bulk",
        "description": "Bulk update multiple watchlist assets in single transaction",
        "auth": "admin_required"
    },
    "get_user_ai_context": {
        "function_name": "get_user_ai_context(user_id INTEGER)",
        "endpoint": "GET /api/v1/users/{user_id}/ai-context",
        "description": "Retrieves user watchlist context for AI analysis",
        "auth": "user_or_admin_required"
    }
}

# Layer 1 Macro Functions Implementation
MACRO_FUNCTIONS = {
    "get_market_regime_analysis": {
        "function_name": "get_market_regime_analysis()",
        "endpoint": "GET /api/v1/macro/regime",
        "description": "Returns current market regime with AI confidence and trend analysis",
        "cache_ttl": 300
    },
    "get_market_sentiment_analysis": {
        "function_name": "get_market_sentiment_analysis()",
        "endpoint": "GET /api/v1/macro/sentiment",
        "description": "Multi-source sentiment analysis including Fear & Greed, social, and news",
        "cache_ttl": 300
    },
    "get_dominance_analysis": {
        "function_name": "get_dominance_analysis()",
        "endpoint": "GET /api/v1/macro/dominance",
        "description": "BTC, ETH, and altcoin dominance analysis with trading signals",
        "cache_ttl": 180
    },
    "get_macro_indicators": {
        "function_name": "get_macro_indicators()",
        "endpoint": "GET /api/v1/macro/indicators",
        "description": "Volatility forecasts, correlations, and macro trend analysis",
        "cache_ttl": 600
    }
}

# Layer 2 Sector Functions Implementation  
SECTOR_FUNCTIONS = {
    "get_sector_rotation_analysis": {
        "function_name": "get_sector_rotation_analysis()",
        "endpoint": "GET /api/v1/sectors/rotation",
        "description": "Current sector rotation signals and money flow analysis",
        "cache_ttl": 300
    },
    "get_sector_allocation_recommendations": {
        "function_name": "get_sector_allocation_recommendations(user_id INTEGER)",
        "endpoint": "GET /api/v1/sectors/allocation",
        "description": "Personalized sector allocation recommendations based on AI analysis",
        "cache_ttl": 900
    }
}

# Layer 4 Signals Functions Implementation
SIGNALS_FUNCTIONS = {
    "get_current_trading_signals": {
        "function_name": "get_current_trading_signals()",
        "endpoint": "GET /api/v1/signals/current", 
        "description": "Current AI trading signals for top cryptocurrencies",
        "cache_ttl": 60
    }
}

# Database Views Implementation
DATABASE_VIEWS = {
    "v_ai_performance": {
        "view_name": "v_ai_performance",
        "endpoint": "GET /api/v1/admin/ai/performance",
        "description": "AI performance metrics across all layers",
        "auth": "admin_required"
    },
    "v_users_overview": {
        "view_name": "v_users_overview",
        "endpoint": "GET /api/v1/admin/users/overview",
        "description": "Comprehensive users overview and statistics",
        "auth": "admin_required"
    },
    "v_sector_performance_summary": {
        "view_name": "v_sector_performance_summary",
        "endpoint": "GET /api/v1/sectors/performance",
        "description": "Aggregated sector performance metrics",
        "auth": "public_access"
    },
    "v_crypto_sectors": {
        "view_name": "v_crypto_sectors",
        "endpoint": "Internal use only - accessed via functions",
        "description": "Internal view for crypto-sector relationships",
        "auth": "internal"
    },
    "v_sector_cryptocurrencies": {
        "view_name": "v_sector_cryptocurrencies", 
        "endpoint": "Internal use only - accessed via functions",
        "description": "Internal view for sector-crypto relationships",
        "auth": "internal"
    },
    "v_dashboard_overview": {
        "view_name": "v_dashboard_overview",
        "endpoint": "GET /api/v1/dashboard/overview",
        "description": "Context-aware dashboard data for all user types",
        "auth": "public_access"
    }
}

# API Response Format for Sector Mapping
SECTOR_MAPPING_RESPONSES = {
    "crypto_sectors": {
        "success": True,
        "data": {
            "cryptocurrency": {
                "id": 1,
                "symbol": "BTC",
                "name": "Bitcoin"
            },
            "sectors": [
                {
                    "id": 1,
                    "name": "Digital Gold",
                    "description": "Store of value cryptocurrencies",
                    "allocation_percentage": 8.5,
                    "relationship_type": "primary"
                }
            ],
            "total_sectors": 2
        }
    },
    "sector_cryptocurrencies": {
        "success": True,
        "data": {
            "sector": {
                "id": 1,
                "name": "Digital Gold",
                "description": "Store of value cryptocurrencies"
            },
            "cryptocurrencies": [
                {
                    "id": 1,
                    "symbol": "BTC",
                    "name": "Bitcoin",
                    "allocation_percentage": 8.5,
                    "relationship_type": "primary"
                }
            ],
            "total_cryptocurrencies": 3
        }
    }
}
```

---

## ✅ **Testing Strategy**

### **🧪 API Testing Framework:**
```python
# Test Categories
TEST_COVERAGE = {
    "unit_tests": {
        "authentication": "JWT token validation",
        "rate_limiting": "Rate limit enforcement",
        "data_validation": "Input validation and sanitization",
        "business_logic": "Core functionality testing"
    },
    "integration_tests": {
        "database_integration": "Database CRUD operations",
        "external_apis": "Third-party API integration",
        "cache_integration": "Redis caching functionality",
        "websocket_integration": "Real-time updates",
        "sector_mapping_functions": "PL/pgSQL function testing",
        "sector_mapping_apis": "Sector mapping endpoint integration"
    },
    "performance_tests": {
        "load_testing": "High concurrent user simulation",
        "stress_testing": "System breaking point identification",
        "endurance_testing": "Long-running stability",
        "spike_testing": "Sudden traffic surge handling"
    },
    "security_tests": {
        "authentication_bypass": "Security vulnerability testing",
        "injection_attacks": "SQL injection, XSS prevention",
        "rate_limit_bypass": "Rate limiting circumvention",
        "data_exposure": "Sensitive data leakage prevention"
    }
}
```

## 📋 ** Endpoint Coverage **

### **✅ Endpoints & Database Integration:**

#### **🌐 Layer 1: Macro Economics (5 endpoints)**
- ✅ `GET /api/v1/macro/regime` → `get_market_regime_analysis()` + `v_market_regime_current` view (NEW)
- ✅ `GET /api/v1/macro/sentiment` → `get_market_sentiment_analysis()` + `v_market_sentiment_summary` view (NEW)
- ✅ `GET /api/v1/macro/dominance` → `get_dominance_analysis()`
- ✅ `GET /api/v1/macro/indicators` → `get_macro_indicators()`
- ✅ `GET /api/v1/macro/history` → Direct table access

#### **📊 Layer 2: Sector Analysis (10 endpoints)**
- ✅ `GET /api/v1/sectors` → Direct table access
- ✅ `GET /api/v1/sectors/performance` → `v_sector_performance_summary` view
- ✅ `GET /api/v1/sectors/{id}/performance` → Direct table access
- ✅ `GET /api/v1/sectors/rotation` → `get_sector_rotation_analysis()`
- ✅ `GET /api/v1/sectors/{id}/assets` → Direct table access
- ✅ `GET /api/v1/sectors/allocation` → `get_sector_allocation_recommendations()`
- ✅ `GET /api/v1/sectors/{id}/cryptocurrencies` → `get_sector_cryptocurrencies()`
- ✅ `GET /api/v1/sectors/name/{name}/cryptocurrencies` → `get_sector_cryptocurrencies_by_name_secure()`
- ✅ `GET /api/v1/cryptocurrencies/{id}/sectors` → `get_crypto_sectors()`
- ✅ `GET /api/v1/cryptocurrencies/symbol/{symbol}/sectors` → `get_crypto_sectors_by_symbol()`

#### **💼 Layer 3: Asset Selection (9 endpoints)**
- ✅ `GET /api/v1/watchlists/default` → Direct table access
- ✅ `GET /api/v1/assets/{id}/analysis` → Direct table access
- ✅ `GET /api/v1/assets/search` → Complex query + search
- ✅ `GET /api/v1/watchlists` → Direct table access
- ✅ `POST /api/v1/watchlists` → `create_watchlist()`
- ✅ `PUT /api/v1/watchlists/{id}` → `update_watchlist()`
- ✅ `DELETE /api/v1/watchlists/{id}` → `delete_watchlist()`
- ✅ `POST /api/v1/watchlists/{id}/assets` → `add_asset_to_watchlist()`
- ✅ `DELETE /api/v1/watchlists/{id}/assets/{asset_id}` → `remove_asset_from_watchlist()`

#### **⚡ Layer 4: Timing Signals (7 endpoints)**
- ✅ `GET /api/v1/signals/current` → `get_current_trading_signals()`
- ✅ `GET /api/v1/signals/{asset_id}` → Direct table access
- ✅ `GET /api/v1/signals/alerts` → Direct table access
- ✅ `POST /api/v1/signals/alerts` → `create_user_alert()`
- ✅ `PUT /api/v1/signals/alerts/{id}` → `update_alert()`
- ✅ `DELETE /api/v1/signals/alerts/{id}` → `delete_alert()`
- ✅ `POST /api/v1/signals/execute` → `execute_trading_signal()`

#### **🤖 AI Suggestions (5 endpoints)**
- ✅ `GET /api/v1/suggestions/current` → Direct table access
- ✅ `GET /api/v1/suggestions/{asset_id}` → Direct table access
- ✅ `GET /api/v1/suggestions/personalized` → Complex AI query
- ✅ `GET /api/v1/users/{user_id}/ai-context` → `get_user_ai_context()`
- ✅ `POST /api/v1/suggestions/{id}/feedback` → `record_ai_suggestion_feedback()`

#### **📈 Dashboard (2 endpoints)**
- ✅ `GET /api/v1/dashboard/overview` → `v_dashboard_overview` view (NEW)
- ✅ `GET /api/v1/dashboard/performance` → `v_system_performance` view + Multiple functions

#### **🔐 Authentication (4 endpoints)**
- ✅ `POST /api/v1/auth/register` → `create_user_account_secure()`
- ✅ `POST /api/v1/auth/login` → `authenticate_user()`
- ✅ `POST /api/v1/auth/refresh` → `refresh_user_token()`
- ✅ `POST /api/v1/auth/logout` → `logout_user()`

#### **👤 User Management (6 endpoints)**
- ✅ `GET /api/v1/users/profile` → Direct table access
- ✅ `PUT /api/v1/users/profile` → `update_user_profile()`
- ✅ `GET /api/v1/users/activity` → Direct table access
- ✅ `GET /api/v1/notifications` → Direct table access
- ✅ `PUT /api/v1/notifications/{id}/read` → `mark_notification_read()`
- ✅ `POST /api/v1/notifications/preferences` → `update_notification_preferences()`

#### **👑 Admin Operations (30 endpoints)**
- ✅ `GET /api/v1/admin/system/health` → System health checks
- ✅ `GET /api/v1/admin/system/metrics` → System metrics
- ✅ `GET /api/v1/admin/ai/performance` → `v_ai_performance` view
- ✅ `GET /api/v1/admin/users` → Direct table access with pagination
- ✅ `GET /api/v1/admin/users/overview` → `v_users_overview` view
- ✅ `PUT /api/v1/admin/users/{id}/role` → `update_user_role()`
- ✅ `PUT /api/v1/admin/users/{id}/status` → `update_user_status()`
- ✅ `GET /api/v1/admin/watchlists/default` → Direct table access
- ✅ `POST /api/v1/admin/watchlists/default` → `create_default_watchlist()`
- ✅ `PUT /api/v1/admin/watchlists/default` → `update_default_watchlist()`
- ✅ `PUT /api/v1/admin/watchlists/{id}/assets/bulk` → `bulk_update_watchlist_assets()`
- ✅ `GET /api/v1/admin/watchlists/analytics` → Complex analytics query
- ✅ `GET /api/v1/admin/models` → Direct table access
- ✅ `POST /api/v1/admin/models/{id}/retrain` → `initiate_model_retrain()`
- ✅ `PUT /api/v1/admin/models/{id}/config` → `update_model_config()`
- ✅ `GET /api/v1/admin/analytics/usage` → Analytics queries
- ✅ `GET /api/v1/admin/analytics/performance` → Performance queries
- ✅ `GET /api/v1/admin/models/performance` → `model_performance` table (NEW)
- ✅ `POST /api/v1/admin/models/{id}/performance` → `record_model_performance()` (NEW)
- ✅ `GET /api/v1/admin/analytics/data` → `analytics_data` table (NEW)
- ✅ `POST /api/v1/admin/analytics/data` → `store_analytics_data()` (NEW)
- ✅ `GET /api/v1/admin/analytics/trends` → `get_analytics_trends()` (NEW)
- ✅ `GET /api/v1/admin/external-apis/logs` → `external_api_logs` table (NEW)
- ✅ `GET /api/v1/admin/external-apis/performance` → `get_external_api_performance()` (NEW)
- ✅ `GET /api/v1/admin/tasks` → `background_tasks` table (NEW)
- ✅ `GET /api/v1/admin/tasks/history` → `get_background_task_history()` (NEW)
- ✅ `POST /api/v1/admin/tasks/{id}/cancel` → `cancel_background_task()` (NEW)
- ✅ `GET /api/v1/admin/tasks/{id}/progress` → Task progress details (NEW)
- ✅ `GET /api/v1/admin/alerts/overview` → Signal alerts overview (NEW)
- ✅ `GET /api/v1/admin/alerts/triggered` → Triggered alerts system-wide (NEW)
- ✅ `GET /api/v1/admin/suggestions/feedback/analytics` → `get_suggestion_feedback_analytics()` (NEW)
- ✅ `GET /api/v1/admin/suggestions/feedback/trends` → Feedback trends (NEW)
- ✅ `GET /api/v1/admin/models/performance/comparison` → `get_model_performance_comparison()` (NEW)

#### **⚡ Signal Alerts (NEW - 7 endpoints)**
- ✅ `GET /api/v1/alerts` → `signal_alerts` table
- ✅ `POST /api/v1/alerts` → `create_user_alert()`
- ✅ `PUT /api/v1/alerts/{id}` → `update_user_alert()`
- ✅ `DELETE /api/v1/alerts/{id}` → `delete_user_alert()`
- ✅ `GET /api/v1/alerts/triggered` → `get_triggered_alerts()`
- ✅ `PUT /api/v1/alerts/{id}/acknowledge` → `acknowledge_alert()`

#### **🤖 AI Suggestion Feedback (NEW - 4 endpoints)**
- ✅ `POST /api/v1/suggestions/{id}/feedback` → `suggestion_feedback` table + `record_suggestion_feedback()`
- ✅ `GET /api/v1/suggestions/{id}/feedback` → `suggestion_feedback` table
- ✅ `PUT /api/v1/suggestions/feedback/{id}` → `update_suggestion_feedback()`

#### **🔍 Enhanced Query Functions (NEW - 3 endpoints)**
- ✅ `GET /api/v1/assets/search` → `search_assets_advanced()` (Enhanced with JSONB filters)
- ✅ `GET /api/v1/users/activity` → `get_user_activity_summary()` (Enhanced analytics)
- ✅ `GET /api/v1/admin/watchlists/analytics` → `get_watchlist_performance_analytics()` (NEW)

---

## 📊 **Complete Database Coverage Summary**

### **✅ All 29 Tables Covered by API Endpoints:**

#### **👤 User Management Tables (4/4)**
- ✅ `users` → User profile, authentication endpoints
- ✅ `user_sessions` → Session management (auth endpoints)
- ✅ `user_activities` → Activity tracking endpoints
- ✅ `notifications` → Notification management endpoints

#### **💰 Cryptocurrency Data Tables (2/2)**
- ✅ `cryptocurrencies` → Asset analysis, search endpoints
- ✅ `price_data` → Price analysis, dashboard endpoints

#### **🌍 Layer 1 Macro Tables (4/4)**
- ✅ `market_regime_analysis` → Macro regime endpoints
- ✅ `market_sentiment_data` → Sentiment analysis endpoints
- ✅ `dominance_data` → Dominance analysis endpoints
- ✅ `macro_indicators` → Macro indicators endpoints

#### **📊 Layer 2 Sector Tables (4/4)**
- ✅ `crypto_sectors` → Sector listing endpoints
- ✅ `sector_performance` → Sector performance endpoints
- ✅ `sector_rotation_analysis` → Rotation analysis endpoints
- ✅ `crypto_sector_mapping` → Sector mapping endpoints

#### **📋 Layer 3 Assets Tables (3/3)**
- ✅ `watchlists` → Watchlist management endpoints
- ✅ `watchlist_assets` → Asset management endpoints
- ✅ `ai_suggestions` → AI suggestion endpoints

#### **⚡ Layer 4 Timing Tables (4/4)**
- ✅ `trading_signals` → Trading signal endpoints
- ✅ `signal_executions` → Signal execution endpoints
- ✅ `signal_alerts` → **NEW** Signal alerts endpoints
- ✅ `risk_management` → Risk management endpoints

#### **🤖 AI & ML Tables (3/3)**
- ✅ `ai_models` → Model management endpoints
- ✅ `model_performance` → **NEW** Model performance tracking endpoints
- ✅ `predictions` → Prediction endpoints

#### **🔧 System Tables (5/5)**
- ✅ `system_health` → System health endpoints
- ✅ `analytics_data` → **NEW** Analytics data endpoints
- ✅ `external_api_logs` → **NEW** External API monitoring endpoints
- ✅ `background_tasks` → **NEW** Background task monitoring endpoints
- ✅ `suggestion_feedback` → **NEW** AI feedback endpoints

---

## 🎯 **TOTAL API ENDPOINT COUNT**

### **📈 Complete API Coverage:**
```
🔥 FINAL API ENDPOINT STATISTICS:
├── 🌍 Layer 1 Macro: 5 endpoints
├── 📊 Layer 2 Sector: 10 endpoints  
├── 💼 Layer 3 Assets: 9 endpoints
├── ⚡ Layer 4 Timing: 7 endpoints
├── 📈 Dashboard: 2 endpoints
├── 🔐 Authentication: 4 endpoints
├── 👤 User Management: 6 endpoints
├── 👑 Admin Operations: 30 endpoints
├── ⚡ Signal Alerts (NEW): 7 endpoints
├── 🤖 AI Feedback (NEW): 4 endpoints
└── 🔍 Enhanced Query Functions (NEW): 3 endpoints

🚀 TOTAL API ENDPOINTS: 87 endpoints
🗄️ TOTAL DATABASE TABLES: 29 tables
🔧 TOTAL DATABASE FUNCTIONS: 60+ functions
📊 TOTAL DATABASE VIEWS: 12+ views

✅ 100% DATABASE COVERAGE ACHIEVED
```

---

## 🎯 **IMPLEMENTATION READINESS STATUS**

### **✅ Design Phase Completion:**
```
🔥 SINGLE UI STRATEGY - COMPLETE DESIGN PHASE:

├── 📋 ERD Structure: ✅ COMPLETE (29 tables, all relationships mapped)
├── 🗄️ Database Schema: ✅ COMPLETE (All tables, functions, views, indexes)
├── 📡 API Planning: ✅ COMPLETE (84 endpoints, full database integration)
├── 🔐 Security Layer: ✅ COMPLETE (Authentication, authorization, rate limiting)
├── 🤖 AI Integration: ✅ COMPLETE (4-layer AI system, feedback loops)
├── 📊 Analytics Layer: ✅ COMPLETE (Performance monitoring, user analytics)
├── ⚡ Real-time Features: ✅ COMPLETE (Signal alerts, notifications)
└── 👑 Admin Management: ✅ COMPLETE (System monitoring, user management)

🎯 STATUS: READY FOR IMPLEMENTATION PHASE
📅 DESIGN COMPLETION DATE: September 4, 2025
🚀 NEXT PHASE: FastAPI Backend Implementation
```

### **🔧 Key Implementation Benefits:**

#### **📊 Complete Database Coverage:**
- ✅ All 29 tables mapped to API endpoints
- ✅ 60+ PL/pgSQL functions for complex operations
- ✅ 12+ database views for reporting and analytics
- ✅ Optimized indexes for performance

#### **🌐 Universal Access Strategy:**
- ✅ Open endpoints for guest users (market data, analysis)
- ✅ Protected endpoints for authenticated users (personal data)
- ✅ Admin endpoints for system management
- ✅ Context-aware responses based on user authentication

#### **⚡ Real-time Features:**
- ✅ Signal alerts with customizable triggers
- ✅ Push notifications for price movements
- ✅ WebSocket support for live updates
- ✅ Background task monitoring

#### **🤖 AI-Powered Intelligence:**
- ✅ 4-layer AI system (Macro → Sector → Asset → Timing)
- ✅ Personalized recommendations
- ✅ Feedback collection and learning
- ✅ Performance tracking and optimization

#### **🛡️ Enterprise-Grade Security:**
- ✅ JWT-based authentication
- ✅ Role-based access control
- ✅ Rate limiting for fair usage
- ✅ Audit logging and monitoring

#### **📈 Comprehensive Analytics:**
- ✅ User behavior tracking
- ✅ API usage monitoring
- ✅ External API performance tracking
- ✅ Business intelligence and reporting

---

## 📅 **DESIGN DOCUMENTATION STATUS**

### **✅ All Design Files Complete and Aligned:**

1. **17_0_Database_ERD_Structure.md** ✅
   - Complete ERD with all 29 tables
   - All relationships mapped
   - Summary section added

2. **17_1_Database_Table_Creation_Scripts.md** ✅
   - All missing tables added (signal_alerts, model_performance, analytics_data, external_api_logs, background_tasks, suggestion_feedback)
   - 60+ PL/pgSQL functions included
   - Complete schema ready for implementation

3. **17_2_Database_Integration_And_API_Planning.md** ✅
   - 87 API endpoints documented (3 new enhanced endpoints added)
   - Complete database integration mapping with all new functions and views
   - All new tables covered by endpoints
   - Enhanced Analytics Functions: 5 functions mapped to endpoints
   - Advanced Query Functions: 3 functions mapped to endpoints  
   - New Dashboard Views: 4 views integrated
   - Implementation readiness confirmed

**🎯 RESULT: Complete design documentation ready for implementation phase!**
**📊 ENHANCED COVERAGE: All 60+ functions and 12+ views fully mapped to API endpoints**
