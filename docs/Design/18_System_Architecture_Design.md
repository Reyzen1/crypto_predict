# docs\Design\18_System_Architecture_Design.md
# 🏗️ System Architecture Design - CryptoPredict فاز دوم
## Single UI Serving Strategy با Simplified Role-Based Access Control

---

## 🎯 **System Architecture Overview - New Design**

### **🔄 Single UI Serving Strategy:**
```
Unified Architecture Approach:
├── 🎨 Single UI Application: One interface serves all user types
├── 🔐 Context-Based Authentication: Just-in-time auth triggers
├── 👤 Progressive User Experience: Guest → Logged → Admin progression
├── 🎛️ Admin Panel Integration: Separate admin interface when needed
└── 📱 Universal Responsive Design: Same experience across all devices
```

---

## 🏛️ **Overall System Architecture**

### **🌐 High-Level Architecture Diagram:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CRYPTOPREDICT SYSTEM ARCHITECTURE                 │
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   CLIENT LAYER   │    │  APPLICATION    │    │   DATA LAYER    │         │
│  │                 │    │     LAYER       │    │                 │         │
│  │ 🌐 Web App       │◄──►│ 🚀 Next.js 14   │◄──►│ 🗄️ PostgreSQL   │         │
│  │ 📱 Mobile PWA    │    │ ⚡ FastAPI       │    │ 📊 Redis Cache   │         │
│  │ 🎛️ Admin Panel   │    │ 🤖 AI Services   │    │ 🔄 Message Queue│         │
│  └─────────────────┘    │ 🔐 Auth Service  │    │ 📁 File Storage │         │
│                         │ 🎯 API Gateway   │    └─────────────────┘         │
│                         └─────────────────┘                                │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┤
│  │                        🔄 EXTERNAL INTEGRATIONS                        │
│  ├─────────────────┬─────────────────┬─────────────────┬─────────────────┤
│  │ 📊 CoinGecko API │ 📰 News APIs    │ 👥 Social APIs  │ 📈 Market Data  │
│  │ 💰 Binance API  │ 🔍 Google Trends│ 📱 Reddit API   │ ⚡ WebSocket     │
│  └─────────────────┴─────────────────┴─────────────────┴─────────────────┘
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔐 **Authentication System Architecture**

### **🎯 Simplified Authentication Strategy:**
```
Authentication Flow (Just-in-Time):

🌐 Guest User Flow:
├── Initial Access: No authentication required
├── Full Feature Access: All 4 layers, all analysis tools
├── Session Tracking: Anonymous session for preferences
├── Auth Triggers: Personal actions (create watchlist, save settings)
└── Gentle Encouragement: Benefits-focused login prompts

👤 Regular User Flow:  
├── Registration: Simple email + password
├── JWT Token: Secure token-based authentication
├── Session Management: Persistent login with refresh tokens
├── Context Switch: Personal watchlist + settings access
└── Cross-Device Sync: Settings and preferences synchronized

👑 Admin User Flow:
├── Enhanced Security: Multi-factor authentication
├── Role Verification: Database role field validation
├── Admin Panel Access: Separate admin interface token
├── Audit Logging: All admin actions tracked
└── Emergency Access: Override capabilities for crisis management
```

### **🏗️ Authentication Service Architecture:**
```python
# Authentication Service Components
class AuthenticationService:
    """
    Simplified authentication for single UI approach
    """
    
    def __init__(self):
        self.jwt_service = JWTService()
        self.session_manager = SessionManager()
        self.user_service = UserService()
        
    async def authenticate_guest(self, session_data: dict) -> GuestToken:
        """Create anonymous session for guest users"""
        return await self.session_manager.create_guest_session(session_data)
    
    async def authenticate_user(self, email: str, password: str) -> UserToken:
        """Standard user authentication"""
        user = await self.user_service.validate_credentials(email, password)
        if user and user.role in ['public', 'admin']:
            token = await self.jwt_service.create_user_token(user)
            await self.session_manager.create_user_session(user.id, token)
            return token
        raise AuthenticationError("Invalid credentials")
    
    async def verify_admin_access(self, token: str) -> bool:
        """Verify admin role for admin panel access"""
        user = await self.jwt_service.verify_token(token)
        return user.role == 'admin'
    
    async def get_user_context(self, token: str) -> UserContext:
        """Get user context for AI and personalization"""
        user = await self.jwt_service.verify_token(token)
        watchlists = await self.user_service.get_user_watchlists(user.id)
        return UserContext(user=user, watchlists=watchlists)

# Role-Based Access Control (Simplified)
class RoleBasedAccess:
    """
    Simplified RBAC for single UI architecture
    """
    
    GUEST_PERMISSIONS = [
        'read_all_layers', 'read_public_watchlist', 'read_analysis'
    ]
    
    USER_PERMISSIONS = GUEST_PERMISSIONS + [
        'create_personal_watchlist', 'update_personal_settings',
        'read_personal_history', 'create_alerts'
    ]
    
    ADMIN_PERMISSIONS = USER_PERMISSIONS + [
        'read_all_users', 'update_any_watchlist', 'admin_panel_access',
        'system_configuration', 'user_management', 'ai_parameter_control'
    ]
    
    @staticmethod
    def check_permission(user_role: str, permission: str) -> bool:
        permission_map = {
            'guest': RoleBasedAccess.GUEST_PERMISSIONS,
            'public': RoleBasedAccess.USER_PERMISSIONS, 
            'admin': RoleBasedAccess.ADMIN_PERMISSIONS
        }
        return permission in permission_map.get(user_role, [])
```

---

## 🎛️ **Admin Panel Integration Approach**

### **🚪 Admin Panel Access Strategy:**
```
Admin Panel Architecture:

🎯 Access Method:
├── Header Link: "Admin Panel" appears only for admin users
├── Separate Interface: Admin panel runs as separate Next.js app
├── Shared Authentication: Same JWT token, verified admin role
├── Context Preservation: Can switch back to main app seamlessly
└── Mobile Support: Essential admin functions available on mobile

🏗️ Admin Panel Structure:
├── 📊 Admin Dashboard: System overview and KPIs
├── 📋 Watchlist Management: Multi-user watchlist control
├── 👥 User Management: User accounts and permissions  
├── 📈 Analytics & Reports: System performance insights
├── ⚙️ System Settings: Configuration and maintenance
└── 🔙 Back to Main App: Seamless return to regular interface

🔐 Security Architecture:
├── Role Verification: Continuous admin role validation
├── Session Management: Separate admin session tracking
├── Audit Logging: Complete admin action history
├── IP Restriction: Optional IP-based access control
└── Emergency Lockdown: Crisis mode system controls
```

### **🎛️ Admin Integration Components:**
```python
# Admin Panel Integration Service
class AdminPanelService:
    """
    Handles admin panel integration with main application
    """
    
    def __init__(self):
        self.auth_service = AuthenticationService()
        self.watchlist_service = WatchlistService()
        self.user_service = UserService()
        self.audit_service = AuditService()
    
    async def verify_admin_access(self, token: str) -> AdminSession:
        """Verify admin access and create admin session"""
        user = await self.auth_service.verify_token(token)
        if user.role != 'admin':
            raise UnauthorizedError("Admin access required")
        
        admin_session = await self.create_admin_session(user)
        await self.audit_service.log_admin_access(user.id, admin_session.id)
        return admin_session
    
    async def get_system_overview(self, admin_id: int) -> SystemOverview:
        """Get system overview data for admin dashboard"""
        return SystemOverview(
            total_users=await self.user_service.count_users(),
            active_users=await self.user_service.count_active_users(),
            system_health=await self.get_system_health(),
            ai_performance=await self.get_ai_performance_summary()
        )
    
    async def manage_user_watchlist(
        self, admin_id: int, user_id: int, action: str, data: dict
    ) -> WatchlistResult:
        """Admin management of user watchlists"""
        await self.audit_service.log_admin_action(
            admin_id, 'watchlist_management', {'user_id': user_id, 'action': action}
        )
        return await self.watchlist_service.admin_update(user_id, action, data)

# Watchlist Toggle System for Admins
class AdminWatchlistToggle:
    """
    Allows admins to switch between different user contexts
    """
    
    async def get_available_contexts(self, admin_id: int) -> List[WatchlistContext]:
        """Get all available watchlist contexts for admin"""
        contexts = []
        
        # Default watchlist
        default_watchlist = await self.get_default_watchlist()
        contexts.append(WatchlistContext(
            id=default_watchlist.id,
            type='default',
            name='Default Watchlist',
            user_email=None,
            asset_count=await self.count_assets(default_watchlist.id)
        ))
        
        # Admin's personal watchlist
        admin_personal = await self.get_user_personal_watchlist(admin_id)
        if admin_personal:
            contexts.append(WatchlistContext(
                id=admin_personal.id,
                type='personal',
                name='My Personal',
                user_email=None,
                asset_count=await self.count_assets(admin_personal.id)
            ))
        
        # All user watchlists
        user_watchlists = await self.get_all_user_watchlists()
        for watchlist in user_watchlists:
            contexts.append(WatchlistContext(
                id=watchlist.id,
                type='personal',
                name=f'User: {watchlist.user.email}',
                user_email=watchlist.user.email,
                asset_count=await self.count_assets(watchlist.id)
            ))
        
        return contexts
    
    async def switch_context(
        self, admin_id: int, target_watchlist_id: int
    ) -> WatchlistContext:
        """Switch admin to different watchlist context"""
        # Verify admin can access this watchlist
        await self.verify_watchlist_access(admin_id, target_watchlist_id)
        
        # Log the context switch
        await self.audit_service.log_admin_action(
            admin_id, 'context_switch', {'target_watchlist_id': target_watchlist_id}
        )
        
        # Return new context
        return await self.get_watchlist_context(target_watchlist_id)
```

---

## 🌐 **Single UI Serving Strategy**

### **📱 Universal Frontend Architecture:**
```
Next.js 14 Application Structure:

app/
├── (auth)/                    # Authentication pages
│   ├── login/
│   └── register/
├── (dashboard)/               # Main application
│   ├── page.tsx              # Universal dashboard
│   ├── macro/                # Layer 1 pages
│   ├── sector/               # Layer 2 pages  
│   ├── assets/               # Layer 3 pages
│   ├── timing/               # Layer 4 pages
│   └── settings/             # User settings
├── admin/                     # Admin panel (separate app)
│   ├── dashboard/
│   ├── watchlists/
│   ├── users/
│   └── system/
└── components/
    ├── ui/                   # Shared UI components
    ├── auth/                 # Authentication components
    ├── admin/                # Admin-specific components
    └── dashboard/            # Dashboard components

Key Architecture Principles:
├── 🎨 Component Reusability: Same components for all user types
├── 🔐 Progressive Enhancement: Features unlock based on auth state
├── 📱 Responsive Design: Universal mobile/desktop experience
├── ⚡ Performance: Single bundle, efficient code splitting
└── 🎛️ Context-Aware: UI adapts to user permissions dynamically
```

### **🎯 Context-Aware Rendering:**
```typescript
// Universal Dashboard Component
interface UniversalDashboardProps {
  userContext: UserContext | null; // null for guest users
  watchlistContext: WatchlistContext;
}

export function UniversalDashboard({ userContext, watchlistContext }: UniversalDashboardProps) {
  // Determine user type
  const userType = getUserType(userContext);
  
  return (
    <div className="dashboard-container">
      {/* Universal Header - adapts based on user type */}
      <Header userContext={userContext} />
      
      {/* Main Content - same layout, different data context */}
      <main className="dashboard-main">
        {/* 4-Layer Navigation - universal for all users */}
        <LayerNavigation />
        
        {/* Dashboard Content - context-aware */}
        <DashboardContent 
          userType={userType}
          watchlistContext={watchlistContext}
        />
        
        {/* Admin Controls - only visible to admins */}
        {userType === 'admin' && (
          <AdminWatchlistToggle 
            currentContext={watchlistContext}
            onContextChange={handleContextSwitch}
          />
        )}
      </main>
      
      {/* Guest User Prompts - contextual login encouragement */}
      {userType === 'guest' && (
        <GuestUserPrompts onAuthTrigger={handleAuthModal} />
      )}
    </div>
  );
}

// User Type Detection
function getUserType(userContext: UserContext | null): 'guest' | 'user' | 'admin' {
  if (!userContext) return 'guest';
  if (userContext.user.role === 'admin') return 'admin';
  return 'user';
}

// Context-Aware API Calls
class APIService {
  async getDashboardData(watchlistContext: WatchlistContext) {
    // Same API endpoint, different context parameter
    return await fetch('/api/dashboard', {
      method: 'POST',
      body: JSON.stringify({
        watchlist_id: watchlistContext.id,
        context_type: watchlistContext.type
      })
    });
  }
}
```

---

## 🤖 **4-Layer AI System Architecture (Preserved)**

### **🧠 AI System Components (Unchanged):**
```python
# Complete 4-Layer AI Architecture (Preserved from original design)
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Any
import asyncio
from datetime import datetime

class LayerType(Enum):
    LAYER1_MACRO = "layer1_macro"
    LAYER2_SECTOR = "layer2_sector"  
    LAYER3_ASSET = "layer3_asset"
    LAYER4_TIMING = "layer4_timing"

class ModelStatus(Enum):
    ACTIVE = "active"
    TRAINING = "training"
    INACTIVE = "inactive"
    ERROR = "error"

@dataclass
class AnalysisContext:
    """Context passed between AI layers for cascade analysis"""
    
    market_regime: str
    confidence_score: float
    risk_level: str
    sector_allocation: Dict[str, float]
    active_assets: List[Dict[str, Any]]
    timestamp: datetime
    
class LayeredAIOrchestrator:
    """
    🎯 Central AI Orchestrator
    Coordinates all 4 AI layers in cascade fashion
    Ensures context flows from macro to micro analysis
    """
    
    def __init__(self):
        self.models = {
            LayerType.LAYER1_MACRO: MacroRegimeDetector(),
            LayerType.LAYER2_SECTOR: SectorRotationPredictor(),
            LayerType.LAYER3_ASSET: SmartAssetSelector(),
            LayerType.LAYER4_TIMING: PrecisionTimingEngine()
        }
        
        self.model_status = {layer: ModelStatus.ACTIVE for layer in LayerType}
        self.last_analysis = {}
        self.context_cache = {}
        
    async def run_cascade_analysis(self, watchlist_context: WatchlistContext) -> Dict[str, Any]:
        """
        🔄 Run complete 4-layer cascade analysis with context awareness
        Each layer uses context from previous layers + watchlist context
        """
        
        logger.info(f"Starting cascade analysis for context: {watchlist_context.type}")
        
        try:
            # Layer 1: Macro Market Analysis (Universal)
            layer1_result = await self.run_layer1_analysis()
            
            # Create analysis context for downstream layers
            context = AnalysisContext(
                market_regime=layer1_result["regime"],
                confidence_score=layer1_result["confidence"], 
                risk_level=layer1_result["risk_level"],
                sector_allocation={},
                active_assets=[],
                timestamp=datetime.utcnow()
            )
            
            # Layer 2: Sector Analysis (using Layer 1 context)
            layer2_result = await self.run_layer2_analysis(context)
            context.sector_allocation = layer2_result["recommended_allocation"]
            
            # Layer 3: Asset Selection (using Layer 1 & 2 context + watchlist context)
            layer3_result = await self.run_layer3_analysis(context, watchlist_context)
            context.active_assets = layer3_result["selected_assets"]
            
            # Layer 4: Timing Signals (using all previous context + watchlist context)
            layer4_result = await self.run_layer4_analysis(context, watchlist_context)
            
            # Combine all results with context awareness
            return {
                "layer1_macro": layer1_result,
                "layer2_sector": layer2_result, 
                "layer3_assets": layer3_result,
                "layer4_timing": layer4_result,
                "analysis_context": context,
                "watchlist_context": watchlist_context,
                "timestamp": datetime.utcnow(),
                "cascade_confidence": self.calculate_cascade_confidence([
                    layer1_result["confidence"],
                    layer2_result["confidence"], 
                    layer3_result["confidence"],
                    layer4_result["confidence"]
                ])
            }
            
        except Exception as e:
            logger.error(f"Cascade analysis failed: {str(e)}")
            await self.handle_analysis_failure(e)
            raise

    async def run_layer3_analysis(self, context: AnalysisContext, watchlist_context: WatchlistContext):
        """Layer 3 with watchlist context awareness"""
        
        # Get assets from the current watchlist context
        watchlist_assets = await self.get_watchlist_assets(watchlist_context.id)
        
        # Run analysis based on context type
        if watchlist_context.type == 'default':
            # Admin watchlist - full system optimization
            return await self.models[LayerType.LAYER3_ASSET].analyze_system_watchlist(
                context, watchlist_assets
            )
        else:
            # Personal watchlist - personalized optimization
            return await self.models[LayerType.LAYER3_ASSET].analyze_personal_watchlist(
                context, watchlist_assets, watchlist_context.user_preferences
            )
    
    async def run_layer4_analysis(self, context: AnalysisContext, watchlist_context: WatchlistContext):
        """Layer 4 with watchlist context awareness"""
        
        # Get current positions from watchlist context
        current_positions = await self.get_current_positions(watchlist_context.id)
        
        # Generate timing signals based on context
        return await self.models[LayerType.LAYER4_TIMING].generate_signals(
            context, current_positions, watchlist_context
        )

# Individual AI Layer Models (Complete preservation of original architecture)
class MacroRegimeDetector:
    """Layer 1: Macro Market Analysis - Unchanged from original"""
    # ... (Complete original implementation preserved)

class SectorRotationPredictor:
    """Layer 2: Sector Analysis - Unchanged from original"""
    # ... (Complete original implementation preserved)

class SmartAssetSelector:
    """Layer 3: Asset Selection - Enhanced with context awareness"""
    # ... (Original implementation + watchlist context integration)

class PrecisionTimingEngine:
    """Layer 4: Timing Signals - Enhanced with context awareness"""
    # ... (Original implementation + watchlist context integration)
```

---

## 📊 **Session Management Architecture**

### **🔄 Session Handling Strategy:**
```python
# Session Management Service
class SessionManager:
    """
    Handles all session types: guest, user, admin
    """
    
    def __init__(self):
        self.redis_client = RedisClient()
        self.session_store = SessionStore()
    
    async def create_guest_session(self, session_data: dict) -> GuestSession:
        """Create anonymous session for guest users"""
        session_id = generate_session_id()
        guest_session = GuestSession(
            id=session_id,
            preferences=session_data.get('preferences', {}),
            analytics_data=session_data.get('analytics', {}),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        # Store in Redis for fast access
        await self.redis_client.setex(
            f"guest_session:{session_id}", 
            86400,  # 24 hours
            guest_session.to_json()
        )
        
        return guest_session
    
    async def create_user_session(self, user_id: int, token: str) -> UserSession:
        """Create authenticated user session"""
        session_id = generate_session_id()
        user_session = UserSession(
            id=session_id,
            user_id=user_id,
            token=token,
            watchlist_context=await self.get_user_default_context(user_id),
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        # Store in Redis and Database
        await self.redis_client.setex(
            f"user_session:{session_id}",
            604800,  # 7 days
            user_session.to_json()
        )
        
        await self.session_store.save_user_session(user_session)
        return user_session
    
    async def upgrade_guest_to_user(
        self, guest_session_id: str, user_session: UserSession
    ) -> UserSession:
        """Upgrade guest session to user session, preserving data"""
        # Get guest session data
        guest_data = await self.redis_client.get(f"guest_session:{guest_session_id}")
        
        if guest_data:
            guest_session = GuestSession.from_json(guest_data)
            
            # Merge guest preferences with user session
            user_session.migrated_preferences = guest_session.preferences
            user_session.previous_analytics = guest_session.analytics_data
            
            # Update user session
            await self.redis_client.setex(
                f"user_session:{user_session.id}",
                604800,
                user_session.to_json()
            )
            
            # Clean up guest session
            await self.redis_client.delete(f"guest_session:{guest_session_id}")
        
        return user_session

# Cross-Device Synchronization
class CrossDeviceSyncService:
    """
    Synchronize user state across devices
    """
    
    async def sync_user_state(self, user_id: int) -> UserState:
        """Sync user state across all active sessions"""
        active_sessions = await self.get_active_user_sessions(user_id)
        
        # Get latest state from most recent session
        latest_session = max(active_sessions, key=lambda s: s.last_used_at)
        latest_state = await self.get_session_state(latest_session.id)
        
        # Broadcast state to all other active sessions
        for session in active_sessions:
            if session.id != latest_session.id:
                await self.update_session_state(session.id, latest_state)
        
        return latest_state
```

---

## 🌐 **API Gateway & Routing Architecture**

### **⚡ API Gateway Strategy:**
```python
# API Gateway for Single UI Architecture
class APIGateway:
    """
    Unified API gateway serving single UI with context awareness
    """
    
    def __init__(self):
        self.auth_service = AuthenticationService()
        self.rate_limiter = RateLimiter()
        self.context_resolver = ContextResolver()
    
    async def route_request(self, request: APIRequest) -> APIResponse:
        """Route requests with context awareness"""
        
        # Resolve user context (guest/user/admin)
        user_context = await self.context_resolver.resolve(request)
        
        # Apply rate limiting (no user-type discrimination)
        await self.rate_limiter.check_rate_limit(request.ip_address)
        
        # Route to appropriate service based on endpoint
        if request.path.startswith('/api/layers/'):
            return await self.route_layer_request(request, user_context)
        elif request.path.startswith('/api/admin/'):
            return await self.route_admin_request(request, user_context)
        elif request.path.startswith('/api/watchlists/'):
            return await self.route_watchlist_request(request, user_context)
        else:
            return await self.route_general_request(request, user_context)
    
    async def route_layer_request(self, request: APIRequest, user_context: UserContext):
        """Route 4-layer AI requests with context"""
        
        # All users get full access to 4-layer AI
        watchlist_context = await self.resolve_watchlist_context(user_context)
        
        layer_service = LayerService()
        return await layer_service.process_request(request, watchlist_context)
    
    async def route_admin_request(self, request: APIRequest, user_context: UserContext):
        """Route admin requests with permission check"""
        
        # Verify admin permissions
        if not user_context or user_context.user.role != 'admin':
            return APIResponse(status=403, message="Admin access required")
        
        admin_service = AdminService()
        return await admin_service.process_request(request, user_context)

# Context Resolution Service
class ContextResolver:
    """
    Resolves user and watchlist context for API requests
    """
    
    async def resolve(self, request: APIRequest) -> UserContext:
        """Resolve user context from request"""
        
        # Try to get auth token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            # Guest user context
            return self.create_guest_context(request)
        
        try:
            # Verify token and get user
            user = await self.auth_service.verify_token(token)
            watchlists = await self.get_user_watchlists(user.id)
            
            return UserContext(
                user=user,
                watchlists=watchlists,
                session_id=request.headers.get('Session-ID'),
                device_info=request.headers.get('User-Agent')
            )
        except:
            # Invalid token, treat as guest
            return self.create_guest_context(request)
    
    async def resolve_watchlist_context(self, user_context: UserContext) -> WatchlistContext:
        """Resolve active watchlist context for user"""
        
        if not user_context.user:
            # Guest user - return default watchlist
            return await self.get_default_watchlist_context()
        
        if user_context.user.role == 'admin':
            # Admin - check for context override in request
            admin_context = request.headers.get('Admin-Watchlist-Context')
            if admin_context:
                return await self.get_watchlist_context(admin_context)
        
        # Regular user - return personal or default
        personal_watchlist = await self.get_user_personal_watchlist(user_context.user.id)
        if personal_watchlist:
            return WatchlistContext.from_watchlist(personal_watchlist)
        else:
            return await self.get_default_watchlist_context()
```

---

## 🚀 **Performance & Scalability Architecture**

### **⚡ Caching Strategy:**
```python
# Multi-Level Caching Architecture
class CachingService:
    """
    Multi-level caching for optimal performance
    """
    
    def __init__(self):
        self.redis_client = RedisClient()  # L1 Cache - Fast access
        self.memory_cache = MemoryCache()   # L2 Cache - Ultra fast
        self.cdn_cache = CDNCache()         # L3 Cache - Global distribution
    
    async def get_layer_analysis(self, layer: int, context_key: str) -> Any:
        """Get cached layer analysis with fallback strategy"""
        
        cache_key = f"layer_{layer}:{context_key}"
        
        # L2: Check memory cache first (fastest)
        if result := self.memory_cache.get(cache_key):
            return result
        
        # L1: Check Redis cache 
        if result := await self.redis_client.get(cache_key):
            # Store in memory cache for next time
            self.memory_cache.set(cache_key, result, ttl=300)  # 5 minutes
            return result
        
        # Cache miss - generate new analysis
        return None
    
    async def set_layer_analysis(
        self, layer: int, context_key: str, data: Any, ttl: int = 1800
    ):
        """Cache layer analysis at multiple levels"""
        
        cache_key = f"layer_{layer}:{context_key}"
        
        # Store at all cache levels
        self.memory_cache.set(cache_key, data, ttl=min(ttl, 300))
        await self.redis_client.setex(cache_key, ttl, data)
        
        # Store static data in CDN for global access
        if layer in [1, 2]:  # Macro and Sector data can be globally cached
            await self.cdn_cache.set(cache_key, data, ttl)

# Load Balancing Strategy
class LoadBalancer:
    """
    Intelligent load balancing for AI services
    """
    
    def __init__(self):
        self.ai_service_pool = AIServicePool()
        self.health_monitor = ServiceHealthMonitor()
    
    async def route_ai_request(self, layer: int, context: WatchlistContext) -> AIService:
        """Route AI requests to optimal service instance"""
        
        # Get healthy service instances for this layer
        healthy_services = await self.health_monitor.get_healthy_services(f"layer_{layer}")
        
        if not healthy_services:
            raise ServiceUnavailableError(f"No healthy services for layer {layer}")
        
        # Use round-robin for Layer 1 & 2 (stateless)
        if layer in [1, 2]:
            return self.round_robin_select(healthy_services)
        
        # Use consistent hashing for Layer 3 & 4 (context-dependent)
        else:
            context_hash = hash(f"{context.id}:{context.type}")
            return self.consistent_hash_select(healthy_services, context_hash)
```

---

## 📊 **Monitoring & Logging Architecture**

### **📈 System Monitoring:**
```python
# Comprehensive Monitoring Service
class MonitoringService:
    """
    System-wide monitoring and alerting
    """
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.dashboard_service = DashboardService()
    
    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect comprehensive system metrics"""
        
        return SystemMetrics(
            # User Metrics
            total_users=await self.count_total_users(),
            active_users_24h=await self.count_active_users(24),
            guest_sessions=await self.count_guest_sessions(),
            
            # AI Performance Metrics  
            ai_layer_accuracy={
                layer: await self.get_layer_accuracy(layer) 
                for layer in [1, 2, 3, 4]
            },
            ai_response_times=await self.get_ai_response_times(),
            
            # System Performance Metrics
            api_response_time=await self.get_avg_response_time(),
            system_uptime=await self.get_system_uptime(),
            error_rate=await self.get_error_rate(),
            
            # Watchlist Metrics
            default_watchlist_performance=await self.get_watchlist_performance('default'),
            avg_personal_watchlist_performance=await self.get_avg_personal_performance(),
            
            timestamp=datetime.utcnow()
        )
    
    async def check_system_health(self) -> HealthStatus:
        """Comprehensive system health check"""
        
        health_checks = {
            'database': await self.check_database_health(),
            'redis': await self.check_redis_health(),
            'ai_services': await self.check_ai_services_health(),
            'external_apis': await self.check_external_apis_health(),
            'file_storage': await self.check_storage_health()
        }
        
        overall_status = all(health_checks.values())
        
        if not overall_status:
            await self.alert_manager.send_critical_alert(
                "System health check failed", health_checks
            )
        
        return HealthStatus(
            overall_healthy=overall_status,
            component_health=health_checks,
            last_check=datetime.utcnow()
        )

# Admin Audit Logging
class AuditLogger:
    """
    Complete audit logging for admin actions
    """
    
    async def log_admin_action(
        self, admin_id: int, action: str, entity_type: str, 
        entity_id: int, details: dict, ip_address: str
    ):
        """Log admin action with full context"""
        
        audit_log = AuditLog(
            admin_id=admin_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
            timestamp=datetime.utcnow(),
            session_id=await self.get_current_session_id(admin_id)
        )
        
        # Store in database for permanent record
        await self.audit_store.save_audit_log(audit_log)
        
        # Store in search index for quick querying
        await self.search_service.index_audit_log(audit_log)
        
        # Send to real-time monitoring if critical action
        if action in ['user_delete', 'system_config_change', 'emergency_override']:
            await self.real_time_monitor.notify_critical_action(audit_log)
```

---

## 🔒 **Security Architecture**

### **🛡️ Security Layers:**
```python
# Comprehensive Security Service
class SecurityService:
    """
    Multi-layered security for single UI architecture
    """
    
    def __init__(self):
        self.encryption_service = EncryptionService()
        self.intrusion_detection = IntrusionDetectionService()
        self.data_protection = DataProtectionService()
    
    async def secure_api_request(self, request: APIRequest) -> SecurityResult:
        """Apply security layers to API requests"""
        
        security_checks = []
        
        # 1. Rate limiting (DDoS protection)
        rate_limit_result = await self.check_rate_limit(request)
        security_checks.append(rate_limit_result)
        
        # 2. Input validation and sanitization
        input_validation_result = await self.validate_input(request)
        security_checks.append(input_validation_result)
        
        # 3. Authentication verification
        auth_result = await self.verify_authentication(request)
        security_checks.append(auth_result)
        
        # 4. Authorization check
        authz_result = await self.check_authorization(request, auth_result.user)
        security_checks.append(authz_result)
        
        # 5. Intrusion detection
        intrusion_result = await self.intrusion_detection.analyze_request(request)
        security_checks.append(intrusion_result)
        
        # Return combined security result
        return SecurityResult(
            passed=all(check.passed for check in security_checks),
            checks=security_checks,
            risk_score=sum(check.risk_score for check in security_checks) / len(security_checks)
        )
    
    async def protect_admin_access(self, request: AdminRequest) -> bool:
        """Enhanced security for admin operations"""
        
        # Multi-factor authentication required
        if not await self.verify_mfa(request.admin_id):
            return False
        
        # IP whitelist check (optional)
        if self.ip_whitelist_enabled:
            if not await self.check_ip_whitelist(request.ip_address):
                await self.log_security_incident("admin_ip_violation", request)
                return False
        
        # Time-based access restrictions
        if not await self.check_time_restrictions(request.admin_id):
            return False
        
        # Concurrent session limits
        if not await self.check_session_limits(request.admin_id):
            return False
        
        return True
```

---

**📅 آخرین بروزرسانی:** نسخه 2.0 - بر اساس معماری کاربری جدید فاز دوم  
**🎯 هدف:** Single UI Serving Strategy with Simplified Authentication & Comprehensive Admin Integration