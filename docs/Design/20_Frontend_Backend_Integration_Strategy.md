# docs\Design\20_Frontend_Backend_Integration_Strategy.md
# 🌐 Frontend-Backend Integration Strategy - فاز دوم
## تمرکز روی Frontend Implementation، API Consumption و Real-time Integration

---

## 🎯 **Frontend Integration Overview**

### **🔄 Frontend-Specific Integration Strategy:**
```
Next.js 14 Frontend ←→ FastAPI Backend Integration:
├── 📱 Component-Based Architecture: Universal components for all user types
├── � API Consumption Patterns: Efficient data fetching and caching
├── ⚡ Real-time Integration: WebSocket for live updates and alerts
├── � State Management: Context + SWR for optimal performance
├── 🎨 Progressive Enhancement: Features unlock based on auth state
├── 📱 Mobile-First PWA: Offline support and native-like experience
├── � Crypto Analysis Integration: Deep analysis page routing
└── 🎛️ Admin Interface Integration: Separate admin panel routing

� Integration Focus Areas:
- API endpoint consumption (84 endpoints)
- Real-time data synchronization
- Authentication state management
- Component reusability across user types
- Mobile-optimized crypto analysis pages
- Progressive loading and caching strategies
```

---

## 🏗️ **Frontend Architecture Integration**

### **📁 Next.js 14 App Structure (به‌روزرسانی شده):**
```typescript
// app/ directory structure aligned with 84 backend APIs
app/
├── (auth)/                     // Authentication routes
│   ├── login/
│   │   └── page.tsx           // → POST /api/v1/auth/login
│   ├── register/
│   │   └── page.tsx           // → POST /api/v1/auth/register
│   └── layout.tsx             // Auth layout wrapper
├── (dashboard)/                // Main application
│   ├── page.tsx               // Universal dashboard → GET /api/v1/dashboard/overview
│   ├── macro/                 // Layer 1 routes (5 endpoints)
│   │   ├── page.tsx           // → GET /api/v1/macro/regime
│   │   ├── sentiment/
│   │   │   └── page.tsx       // → GET /api/v1/macro/sentiment
│   │   ├── dominance/
│   │   │   └── page.tsx       // → GET /api/v1/macro/dominance
│   │   ├── indicators/
│   │   │   └── page.tsx       // → GET /api/v1/macro/indicators
│   │   └── history/
│   │       └── page.tsx       // → GET /api/v1/macro/history
│   ├── sectors/               // Layer 2 routes (10 endpoints)
│   │   ├── page.tsx           // → GET /api/v1/sectors
│   │   ├── performance/
│   │   │   └── page.tsx       // → GET /api/v1/sectors/performance
│   │   ├── rotation/
│   │   │   └── page.tsx       // → GET /api/v1/sectors/rotation
│   │   ├── allocation/
│   │   │   └── page.tsx       // → GET /api/v1/sectors/allocation
│   │   └── [sector]/
│   │       ├── page.tsx       // → GET /api/v1/sectors/{id}/cryptocurrencies
│   │       └── performance/
│   │           └── page.tsx   // → GET /api/v1/sectors/{id}/performance
│   ├── watchlists/            // Layer 3 routes (10 endpoints)
│   │   ├── page.tsx           // → GET /api/v1/watchlists
│   │   ├── default/
│   │   │   └── page.tsx       // → GET /api/v1/watchlists/default
│   │   ├── create/
│   │   │   └── page.tsx       // → POST /api/v1/watchlists
│   │   └── [id]/
│   │       ├── page.tsx       // → GET /api/v1/watchlists/{id}
│   │       └── edit/
│   │           └── page.tsx   // → PUT /api/v1/watchlists/{id}
│   ├── signals/               // Layer 4 routes (10 endpoints)
│   │   ├── page.tsx           // → GET /api/v1/signals/current
│   │   ├── alerts/            // NEW: Signal Alerts Integration
│   │   │   ├── page.tsx       // → GET /api/v1/alerts
│   │   │   ├── create/
│   │   │   │   └── page.tsx   // → POST /api/v1/alerts
│   │   │   ├── [id]/
│   │   │   │   ├── page.tsx   // → GET /api/v1/alerts/{id}
│   │   │   │   └── edit/
│   │   │   │       └── page.tsx // → PUT /api/v1/alerts/{id}
│   │   │   └── triggered/
│   │   │       └── page.tsx   // → GET /api/v1/alerts/triggered
│   │   └── [asset]/
│   │       └── page.tsx       // → GET /api/v1/signals/{asset_id}
│   ├── suggestions/           // AI Suggestions routes (5 endpoints)
│   │   ├── page.tsx           // → GET /api/v1/suggestions/current
│   │   ├── personalized/
│   │   │   └── page.tsx       // → GET /api/v1/suggestions/personalized
│   │   ├── [asset]/
│   │   │   └── page.tsx       // → GET /api/v1/suggestions/{asset_id}
│   │   └── feedback/          // NEW: AI Feedback Integration
│   │       └── [id]/
│   │           └── page.tsx   // → POST /api/v1/suggestions/{id}/feedback
│   ├── assets/                // Asset Analysis routes
│   │   ├── search/
│   │   │   └── page.tsx       // → GET /api/v1/assets/search
│   │   └── [id]/
│   │       ├── page.tsx       // → GET /api/v1/assets/{id}/analysis
│   │       ├── analysis/      // NEW: Deep Crypto Analysis
│   │       │   └── page.tsx   // Individual crypto analysis page
│   │       └── sectors/
│   │           └── page.tsx   // → GET /api/v1/cryptocurrencies/{id}/sectors
│   ├── profile/               // User Management routes
│   │   ├── page.tsx           // → GET /api/v1/users/profile
│   │   ├── edit/
│   │   │   └── page.tsx       // → PUT /api/v1/users/profile
│   │   ├── activity/
│   │   │   └── page.tsx       // → GET /api/v1/users/activity
│   │   └── notifications/
│   │       ├── page.tsx       // → GET /api/v1/notifications
│   │       └── preferences/
│   │           └── page.tsx   // → POST /api/v1/notifications/preferences
│   └── (admin)/               // Admin Panel routes (30 endpoints)
│       ├── dashboard/
│       │   └── page.tsx       // → GET /api/v1/admin/system/health
│       ├── users/
│       │   ├── page.tsx       // → GET /api/v1/admin/users
│       │   ├── overview/
│       │   │   └── page.tsx   // → GET /api/v1/admin/users/overview
│       │   └── [id]/
│       │       ├── page.tsx   // → GET /api/v1/admin/users/{id}
│       │       └── edit/
│       │           └── page.tsx // → PUT /api/v1/admin/users/{id}/role
│       ├── models/            // NEW: AI Model Management
│       │   ├── page.tsx       // → GET /api/v1/admin/models
│       │   ├── performance/
│       │   │   └── page.tsx   // → GET /api/v1/admin/models/performance
│       │   └── [id]/
│       │       ├── page.tsx   // → GET /api/v1/admin/models/{id}
│       │       ├── retrain/
│       │       │   └── page.tsx // → POST /api/v1/admin/models/{id}/retrain
│       │       └── config/
│       │           └── page.tsx // → PUT /api/v1/admin/models/{id}/config
│       ├── analytics/         // NEW: Analytics Dashboard
│       │   ├── page.tsx       // → GET /api/v1/admin/analytics/usage
│       │   ├── data/
│       │   │   └── page.tsx   // → GET /api/v1/admin/analytics/data
│       │   ├── performance/
│       │   │   └── page.tsx   // → GET /api/v1/admin/analytics/performance
│       │   └── feedback/
│       │       └── page.tsx   // → GET /api/v1/admin/suggestions/feedback/analytics
│       ├── external-apis/     // NEW: External API Monitoring
│       │   ├── page.tsx       // → GET /api/v1/admin/external-apis/logs
│       │   ├── performance/
│       │   │   └── page.tsx   // → GET /api/v1/admin/external-apis/performance
│       │   └── health/
│       │       └── page.tsx   // → GET /api/v1/admin/external-apis/health
│       ├── tasks/             // NEW: Background Tasks Management
│       │   ├── page.tsx       // → GET /api/v1/admin/tasks
│       │   ├── [id]/
│       │   │   ├── page.tsx   // → GET /api/v1/admin/tasks/{id}/progress
│       │   │   └── cancel/
│       │   │       └── page.tsx // → POST /api/v1/admin/tasks/{id}/cancel
│       │   └── history/
│       │       └── page.tsx   // → GET /api/v1/admin/tasks/history
│       ├── alerts/            // NEW: Signal Alerts Admin
│       │   ├── page.tsx       // → GET /api/v1/admin/alerts/overview
│       │   └── triggered/
│       │       └── page.tsx   // → GET /api/v1/admin/alerts/triggered
│       └── watchlists/
│           ├── page.tsx       // → GET /api/v1/admin/watchlists/analytics
│           ├── default/
│           │   ├── page.tsx   // → GET /api/v1/admin/watchlists/default
│           │   └── edit/
│           │       └── page.tsx // → PUT /api/v1/admin/watchlists/default
│           └── [id]/
│               └── bulk-edit/
│                   └── page.tsx // → PUT /api/v1/admin/watchlists/{id}/assets/bulk
├── api/                       // API routes (if needed for client-side processing)
└── globals.css               // Global styles
```
│   │   └── [sectorId]/
│   │       └── page.tsx       // → GET /api/v1/sectors/{id}/cryptocurrencies
│   ├── assets/                // Layer 3 routes
│   │   ├── page.tsx           // Asset overview
│   │   ├── search/
│   │   │   └── page.tsx       // → GET /api/v1/assets/search
│   │   ├── watchlists/
│   │   │   ├── page.tsx       // → GET /api/v1/watchlists
│   │   │   ├── default/
│   │   │   │   └── page.tsx   // → GET /api/v1/watchlists/default
│   │   │   └── [watchlistId]/
│   │   │       └── page.tsx   // → GET /api/v1/watchlists/{id}
│   │   └── [assetId]/
│   │       ├── page.tsx       // → GET /api/v1/assets/{id}/analysis
│   │       └── sectors/
│   │           └── page.tsx   // → GET /api/v1/cryptocurrencies/{id}/sectors
│   ├── signals/               // Layer 4 routes
│   │   ├── page.tsx           // → GET /api/v1/signals/current
│   │   ├── alerts/
│   │   │   └── page.tsx       // → GET /api/v1/signals/alerts
│   │   └── [assetId]/
│   │       └── page.tsx       // → GET /api/v1/signals/{assetId}
│   ├── suggestions/           // AI suggestions
│   │   ├── page.tsx           // → GET /api/v1/suggestions/current
│   │   ├── personalized/
│   │   │   └── page.tsx       // → GET /api/v1/suggestions/personalized
│   │   └── [assetId]/
│   │       └── page.tsx       // → GET /api/v1/suggestions/{assetId}
│   ├── profile/               // User management
│   │   ├── page.tsx           // → GET /api/v1/users/profile
│   │   ├── activity/
│   │   │   └── page.tsx       // → GET /api/v1/users/activity
│   │   ├── notifications/
│   │   │   └── page.tsx       // → GET /api/v1/notifications
│   │   └── preferences/
│   │       └── page.tsx       // → PUT /api/v1/users/profile
│   └── layout.tsx             // Main app layout
├── admin/                     // Admin panel (separate app)
│   ├── dashboard/
│   │   └── page.tsx           // → GET /api/v1/admin/system/health
│   ├── users/
│   │   ├── page.tsx           // → GET /api/v1/admin/users
│   │   ├── overview/
│   │   │   └── page.tsx       // → GET /api/v1/admin/users/overview
│   │   └── [userId]/
│   │       └── page.tsx       // → PUT /api/v1/admin/users/{id}/role
│   ├── watchlists/
│   │   ├── page.tsx           // → GET /api/v1/admin/watchlists/analytics
│   │   ├── default/
│   │   │   └── page.tsx       // → GET /api/v1/admin/watchlists/default
│   │   └── [watchlistId]/
│   │       └── page.tsx       // → PUT /api/v1/admin/watchlists/{id}/assets/bulk
│   ├── ai/
│   │   ├── performance/
│   │   │   └── page.tsx       // → GET /api/v1/admin/ai/performance
│   │   └── models/
│   │       ├── page.tsx       // → GET /api/v1/admin/models
│   │       └── [modelId]/
│   │           └── page.tsx   // → PUT /api/v1/admin/models/{id}/config
│   ├── analytics/
│   │   ├── usage/
│   │   │   └── page.tsx       // → GET /api/v1/admin/analytics/usage
│   │   └── performance/
│   │       └── page.tsx       // → GET /api/v1/admin/analytics/performance
│   └── layout.tsx             // Admin layout
└── components/                // Shared components
    ├── ui/                    // Base UI components
    ├── auth/                  // Authentication components
    ├── layers/                // 4-Layer specific components
    ├── admin/                 // Admin-specific components
    └── charts/                // Data visualization components
```

---

## 🔗 **Frontend API Consumption Strategy**

### **🌐 API Client Architecture (Frontend-Focused):**
```typescript
// lib/api/frontend-client.ts - Frontend-optimized API client
import { AuthContext } from '@/contexts/AuthContext';

interface FrontendAPIClientConfig {
  baseURL: string;
  timeout: number;
  retries: number;
  cacheStrategy: 'swr' | 'react-query' | 'custom';
}

class FrontendAPIClient {
  private config: FrontendAPIClientConfig;
  private userContext: UserContext;
  
  constructor(config: FrontendAPIClientConfig) {
    this.config = config;
    this.userContext = this.getUserContext();
  }

  // Frontend-specific request method with caching
  async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<APIResponse<T>> {
    // Add frontend-specific headers
    const headers = {
      'Content-Type': 'application/json',
      'User-Agent': 'CryptoPredict-Frontend/1.0',
      'Client-Type': 'web',
      ...options.headers,
    };

    // Add authentication if available
    if (this.userContext.token) {
      headers['Authorization'] = `Bearer ${this.userContext.token}`;
    }

    // Add user context for analytics
    headers['User-Context'] = this.userContext.role;
    headers['Session-ID'] = this.getSessionId();
    headers['Frontend-Version'] = process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0';

    return this.makeRequest(endpoint, { ...options, headers });
  }

  // Crypto Analysis specific methods (Frontend)
  async getCryptoAnalysis(
    symbol: string, 
    timeframe?: string
  ): Promise<CryptoAnalysisData> {
    const params = timeframe ? `?timeframe=${timeframe}` : '';
    return this.request<CryptoAnalysisData>(
      `/api/v1/assets/${symbol}/analysis${params}`
    );
  }

  async getCryptoChart(
    symbol: string, 
    interval: string = '1h',
    limit: number = 100
  ): Promise<ChartData> {
    return this.request<ChartData>(
      `/api/v1/assets/${symbol}/chart?interval=${interval}&limit=${limit}`
    );
  }

  async getCryptoNews(symbol: string): Promise<NewsData[]> {
    return this.request<NewsData[]>(`/api/v1/assets/${symbol}/news`);
  }

  async getCryptoSentiment(symbol: string): Promise<SentimentData> {
    return this.request<SentimentData>(`/api/v1/assets/${symbol}/sentiment`);
  }

  // Real-time subscription methods
  async subscribeToRealTimeUpdates(symbols: string[]): Promise<WebSocket> {
    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}/ws/crypto`;
    const params = `?symbols=${symbols.join(',')}`;
    const token = this.userContext.token ? `&token=${this.userContext.token}` : '';
    
    return new WebSocket(`${wsUrl}${params}${token}`);
  }
}

---

## 📊 **Crypto Analysis Frontend Components**

### **🔍 Individual Crypto Analysis Page:**
```typescript
// app/assets/[id]/analysis/page.tsx - Deep crypto analysis page
'use client';

interface CryptoAnalysisPageProps {
  params: { id: string };
}

export default function CryptoAnalysisPage({ params }: CryptoAnalysisPageProps) {
  const { id: symbol } = params;
  const { role, isAuthenticated } = useAuth();
  
  // Data fetching with SWR
  const { data: analysis, isLoading, error } = useCryptoAnalysis(symbol);
  const { data: chartData } = useCryptoChart(symbol, '1h');
  const { data: news } = useCryptoNews(symbol);
  const { data: sentiment } = useCryptoSentiment(symbol);
  
  // Real-time updates
  const { isConnected } = useWebSocket({
    onMessage: (data) => {
      if (data.type === 'crypto_update' && data.symbol === symbol) {
        mutate(`/api/v1/assets/${symbol}/analysis`);
      }
    },
  });

  if (isLoading) return <CryptoAnalysisSkeleton />;
  if (error) return <CryptoAnalysisError error={error} />;

  return (
    <div className="crypto-analysis-page">
      {/* Header with breadcrumb and actions */}
      <CryptoAnalysisHeader 
        symbol={symbol}
        price={analysis?.currentPrice}
        change={analysis?.priceChange24h}
        isLive={isConnected}
      />

      {/* Main analysis content */}
      <div className="analysis-content">
        {/* Price and Market Data */}
        <CryptoPriceSection 
          data={analysis?.priceData}
          marketCap={analysis?.marketCap}
          volume={analysis?.volume24h}
        />

        {/* Interactive Chart */}
        <CryptoChartSection 
          symbol={symbol}
          chartData={chartData}
          timeframes={['1h', '4h', '1d', '1w', '1m']}
          onTimeframeChange={(tf) => mutateCryptoChart(symbol, tf)}
        />

        {/* AI Predictions */}
        <CryptoAIPredictions 
          predictions={analysis?.aiPredictions}
          confidence={analysis?.confidence}
          modelAccuracy={analysis?.modelAccuracy}
        />

        {/* Technical Indicators */}
        <CryptoTechnicalIndicators 
          indicators={analysis?.technicalIndicators}
          signals={analysis?.tradingSignals}
        />

        {/* News and Sentiment */}
        <CryptoNewsAndSentiment 
          news={news}
          sentiment={sentiment}
          socialMetrics={analysis?.socialMetrics}
        />

        {/* Trading Opportunities */}
        <CryptoTradingOpportunities 
          opportunities={analysis?.tradingOpportunities}
          riskAssessment={analysis?.riskAssessment}
          userRole={role}
          isAuthenticated={isAuthenticated}
        />

        {/* Risk Factors */}
        <CryptoRiskFactors 
          risks={analysis?.riskFactors}
          riskScore={analysis?.riskScore}
        />
      </div>

      {/* Quick Actions Sidebar */}
      <CryptoQuickActions 
        symbol={symbol}
        currentPrice={analysis?.currentPrice}
        isAuthenticated={isAuthenticated}
        onAddToWatchlist={handleAddToWatchlist}
        onCreateAlert={handleCreateAlert}
        onShare={handleShare}
      />

      {/* Mobile-specific bottom actions */}
      <MobileCryptoActions 
        symbol={symbol}
        isAuthenticated={isAuthenticated}
        className="md:hidden"
      />
    </div>
  );
}

// Custom hooks for crypto analysis
function useCryptoAnalysis(symbol: string) {
  return useAPIData<CryptoAnalysisData>(`/api/v1/assets/${symbol}/analysis`, {
    refreshInterval: 30 * 1000, // 30 seconds
    revalidateOnFocus: true,
  });
}

function useCryptoChart(symbol: string, timeframe: string = '1h') {
  return useAPIData<ChartData>(`/api/v1/assets/${symbol}/chart?interval=${timeframe}`, {
    refreshInterval: 15 * 1000, // 15 seconds
  });
}

function useCryptoNews(symbol: string) {
  return useAPIData<NewsData[]>(`/api/v1/assets/${symbol}/news`, {
    refreshInterval: 5 * 60 * 1000, // 5 minutes
  });
}

function useCryptoSentiment(symbol: string) {
  return useAPIData<SentimentData>(`/api/v1/assets/${symbol}/sentiment`, {
    refreshInterval: 10 * 60 * 1000, // 10 minutes
  });
}
```

### **📱 Mobile Crypto Analysis Components:**
```typescript
// components/crypto/mobile/MobileCryptoAnalysis.tsx
export function MobileCryptoAnalysis({ symbol, analysis }: MobileCryptoAnalysisProps) {
  const [activeTab, setActiveTab] = useState('overview');
  
  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'chart', label: 'Chart', icon: TrendingUp },
    { id: 'ai', label: 'AI', icon: Brain },
    { id: 'news', label: 'News', icon: Newspaper },
    { id: 'trade', label: 'Trade', icon: Target },
  ];

  return (
    <div className="mobile-crypto-analysis">
      {/* Mobile Header */}
      <MobileAnalysisHeader 
        symbol={symbol}
        price={analysis.currentPrice}
        change={analysis.priceChange24h}
      />

      {/* Tab Navigation */}
      <div className="mobile-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "tab-button",
              activeTab === tab.id && "active"
            )}
          >
            <tab.icon className="w-4 h-4" />
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'overview' && (
          <MobileOverviewTab analysis={analysis} />
        )}
        {activeTab === 'chart' && (
          <MobileChartTab symbol={symbol} />
        )}
        {activeTab === 'ai' && (
          <MobileAITab predictions={analysis.aiPredictions} />
        )}
        {activeTab === 'news' && (
          <MobileNewsTab symbol={symbol} />
        )}
        {activeTab === 'trade' && (
          <MobileTradeTab 
            symbol={symbol}
            opportunities={analysis.tradingOpportunities}
          />
        )}
      </div>

      {/* Floating Action Button */}
      <MobileFloatingActions symbol={symbol} />
    </div>
  );
}

// Swipeable chart component for mobile
export function MobileSwipeableChart({ symbol }: { symbol: string }) {
  const [currentTimeframe, setCurrentTimeframe] = useState('1h');
  const timeframes = ['1h', '4h', '1d', '1w', '1m'];
  
  const swipeHandlers = useSwipeable({
    onSwipedLeft: () => {
      const currentIndex = timeframes.indexOf(currentTimeframe);
      if (currentIndex < timeframes.length - 1) {
        setCurrentTimeframe(timeframes[currentIndex + 1]);
      }
    },
    onSwipedRight: () => {
      const currentIndex = timeframes.indexOf(currentTimeframe);
      if (currentIndex > 0) {
        setCurrentTimeframe(timeframes[currentIndex - 1]);
      }
    },
  });

  return (
    <div {...swipeHandlers} className="mobile-chart-container">
      <div className="timeframe-indicator">
        {timeframes.map((tf, index) => (
          <div
            key={tf}
            className={cn(
              "indicator-dot",
              tf === currentTimeframe && "active"
            )}
          />
        ))}
      </div>
      
      <InteractiveCryptoChart 
        symbol={symbol}
        timeframe={currentTimeframe}
        height={300}
        touchOptimized
      />
      
      <div className="swipe-hint">
        ← Swipe to change timeframe →
      </div>
    </div>
  );
}
```

---

## 🔐 **Authentication Integration (Frontend)**
```typescript
// lib/api/client.ts - Universal API client for all user types
import { AuthContext } from '@/contexts/AuthContext';

interface APIClientConfig {
  baseURL: string;
  timeout: number;
  retries: number;
}

interface UserContext {
  user: User | null;
  token: string | null;
  role: 'guest' | 'user' | 'admin';
}

class UniversalAPIClient {
  private config: APIClientConfig;
  private userContext: UserContext;

  constructor(config: APIClientConfig) {
    this.config = config;
    this.userContext = this.getUserContext();
  }

  // Context-aware request method
  async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<APIResponse<T>> {
    const url = `${this.config.baseURL}${endpoint}`;
    
    // Add authentication headers if available
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.userContext.token) {
      headers['Authorization'] = `Bearer ${this.userContext.token}`;
    }

    // Add user context for analytics
    headers['User-Context'] = this.userContext.role;
    headers['Session-ID'] = this.getSessionId();

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        signal: AbortSignal.timeout(this.config.timeout),
      });

      if (!response.ok) {
        throw new APIError(response.status, await response.text());
      }

      const data = await response.json();
      return this.processResponse<T>(data);
    } catch (error) {
      return this.handleError(error);
    }
  }

  // Layer-specific methods (به‌روزرسانی شده)
  async getMacroRegime(): Promise<MacroRegimeData> {
    return this.request<MacroRegimeData>('/api/v1/macro/regime');
  }

  async getSectorPerformance(): Promise<SectorPerformanceData> {
    return this.request<SectorPerformanceData>('/api/v1/sectors/performance');
  }

  async getWatchlists(): Promise<WatchlistData[]> {
    if (this.userContext.role === 'guest') {
      // Guest users get default watchlist
      return this.request<WatchlistData[]>('/api/v1/watchlists/default');
    }
    // Logged users get personal watchlists
    return this.request<WatchlistData[]>('/api/v1/watchlists');
  }

  async getCurrentSignals(): Promise<TradingSignalData[]> {
    return this.request<TradingSignalData[]>('/api/v1/signals/current');
  }

  // NEW: Signal Alerts methods
  async getUserAlerts(): Promise<SignalAlertData[]> {
    this.requireAuth();
    return this.request<SignalAlertData[]>('/api/v1/alerts');
  }

  async createAlert(alertData: CreateAlertData): Promise<SignalAlertData> {
    this.requireAuth();
    return this.request<SignalAlertData>('/api/v1/alerts', {
      method: 'POST',
      body: JSON.stringify(alertData),
    });
  }

  async updateAlert(alertId: number, updates: UpdateAlertData): Promise<SignalAlertData> {
    this.requireAuth();
    return this.request<SignalAlertData>(`/api/v1/alerts/${alertId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteAlert(alertId: number): Promise<void> {
    this.requireAuth();
    return this.request<void>(`/api/v1/alerts/${alertId}`, {
      method: 'DELETE',
    });
  }

  async getTriggeredAlerts(days?: number): Promise<TriggeredAlertData[]> {
    this.requireAuth();
    const params = days ? `?days=${days}` : '';
    return this.request<TriggeredAlertData[]>(`/api/v1/alerts/triggered${params}`);
  }

  async acknowledgeAlert(alertId: number): Promise<void> {
    this.requireAuth();
    return this.request<void>(`/api/v1/alerts/${alertId}/acknowledge`, {
      method: 'PUT',
    });
  }

  // NEW: AI Suggestion Feedback methods
  async submitSuggestionFeedback(
    suggestionId: number, 
    feedback: SuggestionFeedbackData
  ): Promise<void> {
    this.requireAuth();
    return this.request<void>(`/api/v1/suggestions/${suggestionId}/feedback`, {
      method: 'POST',
      body: JSON.stringify(feedback),
    });
  }

  async getSuggestionFeedback(suggestionId: number): Promise<SuggestionFeedbackData> {
    this.requireAuth();
    return this.request<SuggestionFeedbackData>(`/api/v1/suggestions/${suggestionId}/feedback`);
  }

  async updateSuggestionFeedback(
    feedbackId: number, 
    updates: UpdateFeedbackData
  ): Promise<SuggestionFeedbackData> {
    this.requireAuth();
    return this.request<SuggestionFeedbackData>(`/api/v1/suggestions/feedback/${feedbackId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  // Context-aware dashboard data
  async getDashboardData(symbols?: string[]): Promise<DashboardData> {
    const params = symbols ? `?symbols=${symbols.join(',')}` : '';
    return this.request<DashboardData>(`/api/v1/dashboard/overview${params}`);
  }

  // Admin-specific methods (with role check)
  async getAdminSystemHealth(): Promise<SystemHealthData> {
    this.requireAdminAuth();
    return this.request<SystemHealthData>('/api/v1/admin/system/health');
  }

  // NEW: Admin Model Performance methods
  async getAdminModelPerformance(params?: ModelPerformanceParams): Promise<ModelPerformanceData[]> {
    this.requireAdminAuth();
    const queryParams = params ? `?${new URLSearchParams(params).toString()}` : '';
    return this.request<ModelPerformanceData[]>(`/api/v1/admin/models/performance${queryParams}`);
  }

  async recordModelPerformance(
    modelId: number, 
    performanceData: RecordPerformanceData
  ): Promise<void> {
    this.requireAdminAuth();
    return this.request<void>(`/api/v1/admin/models/${modelId}/performance`, {
      method: 'POST',
      body: JSON.stringify(performanceData),
    });
  }

  // NEW: Admin Analytics Data methods
  async getAdminAnalyticsData(params?: AnalyticsDataParams): Promise<AnalyticsDataResponse> {
    this.requireAdminAuth();
    const queryParams = params ? `?${new URLSearchParams(params).toString()}` : '';
    return this.request<AnalyticsDataResponse>(`/api/v1/admin/analytics/data${queryParams}`);
  }

  async storeAnalyticsData(analyticsData: StoreAnalyticsData): Promise<void> {
    this.requireAdminAuth();
    return this.request<void>('/api/v1/admin/analytics/data', {
      method: 'POST',
      body: JSON.stringify(analyticsData),
    });
  }

  // NEW: Admin External API Monitoring methods
  async getExternalAPILogs(params?: ExternalAPIParams): Promise<ExternalAPILogData[]> {
    this.requireAdminAuth();
    const queryParams = params ? `?${new URLSearchParams(params).toString()}` : '';
    return this.request<ExternalAPILogData[]>(`/api/v1/admin/external-apis/logs${queryParams}`);
  }

  async getExternalAPIPerformance(): Promise<ExternalAPIPerformanceData> {
    this.requireAdminAuth();
    return this.request<ExternalAPIPerformanceData>('/api/v1/admin/external-apis/performance');
  }

  // NEW: Admin Background Tasks methods
  async getAdminBackgroundTasks(params?: BackgroundTaskParams): Promise<BackgroundTaskData[]> {
    this.requireAdminAuth();
    const queryParams = params ? `?${new URLSearchParams(params).toString()}` : '';
    return this.request<BackgroundTaskData[]>(`/api/v1/admin/tasks${queryParams}`);
  }

  async cancelBackgroundTask(taskId: number): Promise<void> {
    this.requireAdminAuth();
    return this.request<void>(`/api/v1/admin/tasks/${taskId}/cancel`, {
      method: 'POST',
    });
  }

  async getTaskProgress(taskId: number): Promise<TaskProgressData> {
    this.requireAdminAuth();
    return this.request<TaskProgressData>(`/api/v1/admin/tasks/${taskId}/progress`);
  }

  // NEW: Admin Signal Alerts methods
  async getAdminAlertsOverview(): Promise<AdminAlertsOverviewData> {
    this.requireAdminAuth();
    return this.request<AdminAlertsOverviewData>('/api/v1/admin/alerts/overview');
  }

  async getAdminTriggeredAlerts(params?: AdminAlertsParams): Promise<AdminTriggeredAlertsData[]> {
    this.requireAdminAuth();
    const queryParams = params ? `?${new URLSearchParams(params).toString()}` : '';
    return this.request<AdminTriggeredAlertsData[]>(`/api/v1/admin/alerts/triggered${queryParams}`);
  }

  // NEW: Admin Suggestion Feedback Analytics methods
  async getSuggestionFeedbackAnalytics(params?: FeedbackAnalyticsParams): Promise<FeedbackAnalyticsData> {
    this.requireAdminAuth();
    const queryParams = params ? `?${new URLSearchParams(params).toString()}` : '';
    return this.request<FeedbackAnalyticsData>(`/api/v1/admin/suggestions/feedback/analytics${queryParams}`);
  }

  async getSuggestionFeedbackTrends(): Promise<FeedbackTrendsData> {
    this.requireAdminAuth();
    return this.request<FeedbackTrendsData>('/api/v1/admin/suggestions/feedback/trends');
  }

  // Helper methods
  private requireAuth(): void {
    if (this.userContext.role === 'guest') {
      throw new Error('Authentication required');
    }
  }

  private requireAdminAuth(): void {
    if (this.userContext.role !== 'admin') {
      throw new Error('Admin access required');
    }
  }
    this.requireAdminRole();
    return this.request<SystemHealthData>('/api/v1/admin/system/health');
  }

  async updateUserRole(userId: number, role: string): Promise<void> {
    this.requireAdminRole();
    return this.request('/api/v1/admin/users/${userId}/role', {
      method: 'PUT',
      body: JSON.stringify({ role }),
    });
  }

  // Watchlist management
  async createWatchlist(data: CreateWatchlistData): Promise<WatchlistData> {
    this.requireAuthentication();
    return this.request<WatchlistData>('/api/v1/watchlists', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateWatchlist(
    watchlistId: number, 
    data: UpdateWatchlistData
  ): Promise<WatchlistData> {
    this.requireAuthentication();
    return this.request<WatchlistData>(`/api/v1/watchlists/${watchlistId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async addAssetToWatchlist(
    watchlistId: number, 
    assetData: AddAssetData
  ): Promise<void> {
    this.requireAuthentication();
    return this.request(`/api/v1/watchlists/${watchlistId}/assets`, {
      method: 'POST',
      body: JSON.stringify(assetData),
    });
  }

  // Signal management
  async createAlert(alertData: CreateAlertData): Promise<AlertData> {
    this.requireAuthentication();
    return this.request<AlertData>('/api/v1/signals/alerts', {
      method: 'POST',
      body: JSON.stringify(alertData),
    });
  }

  async updateAlert(alertId: number, data: UpdateAlertData): Promise<AlertData> {
    this.requireAuthentication();
    return this.request<AlertData>(`/api/v1/signals/alerts/${alertId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // AI suggestions
  async recordSuggestionFeedback(
    suggestionId: number, 
    feedback: SuggestionFeedback
  ): Promise<void> {
    this.requireAuthentication();
    return this.request(`/api/v1/suggestions/${suggestionId}/feedback`, {
      method: 'POST',
      body: JSON.stringify(feedback),
    });
  }

  // Helper methods
  private getUserContext(): UserContext {
    // Get user context from React Context or localStorage
    const user = this.getStoredUser();
    const token = this.getStoredToken();
    
    return {
      user,
      token,
      role: user ? (user.role === 'admin' ? 'admin' : 'user') : 'guest'
    };
  }

  private requireAuthentication(): void {
    if (!this.userContext.token) {
      throw new AuthenticationError('Authentication required');
    }
  }

  private requireAdminRole(): void {
    if (this.userContext.role !== 'admin') {
      throw new AuthorizationError('Admin access required');
    }
  }

  private processResponse<T>(data: any): APIResponse<T> {
    return {
      success: data.success || true,
      data: data.data || data,
      meta: data.meta || {},
      timestamp: data.timestamp || new Date().toISOString(),
    };
  }

  private handleError(error: any): APIResponse<never> {
    console.error('API Error:', error);
    throw error;
  }
}

// Export singleton instance
export const apiClient = new UniversalAPIClient({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000,
  retries: 3,
});
```

---

## 🔐 **Authentication Integration**

### **👤 Context-Aware Auth System:**
### **👤 Frontend Authentication Context:**
```typescript
// contexts/AuthContext.tsx - Frontend-focused authentication
'use client';

interface FrontendAuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  role: 'guest' | 'user' | 'admin';
  sessionId: string;
}

interface FrontendAuthContextType extends FrontendAuthState {
  login: (email: string, password: string) => Promise<void>;
  register: (userData: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  switchToGuestMode: () => void;
  // Frontend-specific methods
  persistSession: () => void;
  clearSession: () => void;
  updateUserPreferences: (prefs: UserPreferences) => Promise<void>;
}

export function FrontendAuthProvider({ children }: { children: React.ReactNode }) {
  const [authState, setAuthState] = useState<FrontendAuthState>({
    user: null,
    token: null,
    isLoading: true,
    isAuthenticated: false,
    role: 'guest',
    sessionId: generateSessionId(),
  });

  // Frontend-specific initialization
  useEffect(() => {
    initializeFrontendAuth();
  }, []);

  // Auto-save user preferences
  useEffect(() => {
    if (authState.user) {
      localStorage.setItem('user_preferences', JSON.stringify(authState.user.preferences));
    }
  }, [authState.user?.preferences]);

  const initializeFrontendAuth = async () => {
    try {
      // Check for stored session
      const storedSession = localStorage.getItem('crypto_predict_session');
      if (storedSession) {
        const session = JSON.parse(storedSession);
        await validateStoredSession(session);
      } else {
        // Initialize guest session
        initializeGuestSession();
      }
    } catch (error) {
      console.error('Frontend auth initialization failed:', error);
      initializeGuestSession();
    }
  };

  const initializeGuestSession = () => {
    const guestSession = {
      sessionId: generateSessionId(),
      timestamp: Date.now(),
      preferences: getDefaultPreferences(),
    };
    
    localStorage.setItem('guest_session', JSON.stringify(guestSession));
    setAuthState(prev => ({
      ...prev,
      isLoading: false,
      role: 'guest',
      sessionId: guestSession.sessionId,
    }));
  };

  // Frontend-specific login with session management
  const login = async (email: string, password: string) => {
    try {
      const response = await apiClient.request('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });

      const { user, access_token, refresh_token } = response.data;

      // Frontend session management
      const sessionData = {
        user,
        access_token,
        refresh_token,
        sessionId: generateSessionId(),
        loginTime: Date.now(),
        lastActivity: Date.now(),
      };

      // Store in localStorage with encryption
      localStorage.setItem('crypto_predict_session', JSON.stringify(sessionData));
      localStorage.removeItem('guest_session'); // Clear guest session

      setAuthState({
        user,
        token: access_token,
        isLoading: false,
        isAuthenticated: true,
        role: user.role === 'admin' ? 'admin' : 'user',
        sessionId: sessionData.sessionId,
      });

      // Track login analytics
      trackUserLogin(user.id, user.role);
    } catch (error) {
      console.error('Frontend login error:', error);
      throw error;
    }
  };

  // Frontend-specific logout with cleanup
  const logout = async () => {
    try {
      if (authState.token) {
        // Notify backend of logout
        await apiClient.request('/api/v1/auth/logout', {
          method: 'POST',
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Frontend cleanup
      localStorage.removeItem('crypto_predict_session');
      localStorage.removeItem('user_preferences');
      
      // Initialize new guest session
      initializeGuestSession();
    }
  };

  // Frontend-specific helper methods
  const persistSession = () => {
    if (authState.isAuthenticated) {
      const currentSession = JSON.parse(
        localStorage.getItem('crypto_predict_session') || '{}'
      );
      currentSession.lastActivity = Date.now();
      localStorage.setItem('crypto_predict_session', JSON.stringify(currentSession));
    }
  };

  const updateUserPreferences = async (prefs: UserPreferences) => {
    if (!authState.isAuthenticated) return;

    try {
      await apiClient.request('/api/v1/users/preferences', {
        method: 'PUT',
        body: JSON.stringify(prefs),
      });

      setAuthState(prev => ({
        ...prev,
        user: prev.user ? { ...prev.user, preferences: prefs } : null,
      }));
    } catch (error) {
      console.error('Failed to update preferences:', error);
      throw error;
    }
  };

  return (
    <AuthContext.Provider value={{
      ...authState,
      login,
      register,
      logout,
      refreshToken,
      switchToGuestMode: initializeGuestSession,
      persistSession,
      clearSession: () => localStorage.clear(),
      updateUserPreferences,
    }}>
      {children}
    </AuthContext.Provider>
  );
}
```

---

## 📊 **Frontend Data Management**

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  role: 'guest' | 'user' | 'admin';
}

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  register: (userData: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  switchToGuestMode: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    token: null,
    isLoading: true,
    isAuthenticated: false,
    role: 'guest',
  });

  // Initialize auth state from localStorage
  useEffect(() => {
    initializeAuth();
  }, []);

  // Auto token refresh
  useEffect(() => {
    if (authState.token) {
      const interval = setInterval(refreshToken, 50 * 60 * 1000); // 50 minutes
      return () => clearInterval(interval);
    }
  }, [authState.token]);

  const initializeAuth = async () => {
    try {
      const storedToken = localStorage.getItem('auth_token');
      const storedUser = localStorage.getItem('user_data');

      if (storedToken && storedUser) {
        const user = JSON.parse(storedUser);
        setAuthState({
          user,
          token: storedToken,
          isLoading: false,
          isAuthenticated: true,
          role: user.role === 'admin' ? 'admin' : 'user',
        });

        // Verify token is still valid
        await verifyToken(storedToken);
      } else {
        // Guest mode
        setAuthState(prev => ({
          ...prev,
          isLoading: false,
          role: 'guest',
        }));
      }
    } catch (error) {
      console.error('Auth initialization failed:', error);
      switchToGuestMode();
    }
  };

  const login = async (email: string, password: string) => {
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const data = await response.json();
      const { user, access_token, refresh_token } = data.data;

      // Store tokens
      localStorage.setItem('auth_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('user_data', JSON.stringify(user));

      setAuthState({
        user,
        token: access_token,
        isLoading: false,
        isAuthenticated: true,
        role: user.role === 'admin' ? 'admin' : 'user',
      });
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const register = async (userData: RegisterData) => {
    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData),
      });

      if (!response.ok) {
        throw new Error('Registration failed');
      }

      const data = await response.json();
      const { user, access_token, refresh_token } = data.data;

      // Store tokens
      localStorage.setItem('auth_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('user_data', JSON.stringify(user));

      setAuthState({
        user,
        token: access_token,
        isLoading: false,
        isAuthenticated: true,
        role: user.role === 'admin' ? 'admin' : 'user',
      });
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      if (authState.token) {
        await fetch('/api/v1/auth/logout', {
          method: 'POST',
          headers: { 
            'Authorization': `Bearer ${authState.token}`,
            'Content-Type': 'application/json',
          },
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear stored data
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_data');

      // Switch to guest mode
      switchToGuestMode();
    }
  };

  const refreshToken = async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data = await response.json();
      const { access_token } = data.data;

      localStorage.setItem('auth_token', access_token);
      setAuthState(prev => ({
        ...prev,
        token: access_token,
      }));
    } catch (error) {
      console.error('Token refresh failed:', error);
      switchToGuestMode();
    }
  };

  const switchToGuestMode = () => {
    setAuthState({
      user: null,
      token: null,
      isLoading: false,
      isAuthenticated: false,
      role: 'guest',
    });
  };

  const verifyToken = async (token: string) => {
    try {
      const response = await fetch('/api/v1/auth/me', {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (!response.ok) {
        throw new Error('Token verification failed');
      }
    } catch (error) {
      console.error('Token verification failed:', error);
      switchToGuestMode();
    }
  };

  const value: AuthContextType = {
    ...authState,
    login,
    register,
    logout,
    refreshToken,
    switchToGuestMode,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
```

### **🔄 Frontend State Management with SWR:**
```typescript
// hooks/useFrontendData.ts - Frontend-optimized data fetching
import useSWR from 'swr';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api/frontend-client';

interface FrontendDataOptions {
  refreshInterval?: number;
  revalidateOnFocus?: boolean;
  fallbackData?: any;
  onError?: (error: any) => void;
  // Frontend-specific options
  cacheKey?: string;
  backgroundUpdate?: boolean;
  optimisticUpdate?: boolean;
}

export function useFrontendData<T>(
  endpoint: string,
  options: FrontendDataOptions = {}
) {
  const { role, isAuthenticated, sessionId } = useAuth();
  
  // Frontend-specific cache key generation
  const cacheKey = options.cacheKey || `${endpoint}:${role}:${sessionId}`;
  
  const fetcher = async (url: string) => {
    const response = await apiClient.request<T>(url);
    
    // Frontend analytics
    trackDataFetch(url, role, Date.now());
    
    return response.data;
  };

  const {
    data,
    error,
    isLoading,
    isValidating,
    mutate,
  } = useSWR(
    cacheKey,
    () => fetcher(endpoint),
    {
      refreshInterval: options.refreshInterval || 0,
      revalidateOnFocus: options.revalidateOnFocus !== false,
      fallbackData: options.fallbackData,
      onError: (error) => {
        // Frontend error handling
        console.error(`Frontend data fetch error for ${endpoint}:`, error);
        options.onError?.(error);
        
        // Track error for analytics
        trackDataError(endpoint, error, role);
      },
      // Frontend-specific optimizations
      dedupingInterval: 2000, // Prevent duplicate requests
      errorRetryCount: 3,
      errorRetryInterval: 1000,
    }
  );

  // Frontend-specific optimistic updates
  const optimisticUpdate = (newData: T) => {
    if (options.optimisticUpdate) {
      mutate(newData, false); // Update immediately without revalidation
    }
  };

  return {
    data,
    error,
    isLoading,
    isValidating,
    mutate,
    refresh: () => mutate(),
    optimisticUpdate,
    cacheKey,
  };
}

// Specialized frontend hooks for crypto analysis
export function useCryptoAnalysisData(symbol: string) {
  const { data: analysis, ...rest } = useFrontendData<CryptoAnalysisData>(
    `/api/v1/assets/${symbol}/analysis`,
    {
      refreshInterval: 30 * 1000, // 30 seconds
      cacheKey: `crypto-analysis:${symbol}`,
      backgroundUpdate: true,
    }
  );

  // Frontend-specific derived data
  const derivedData = useMemo(() => {
    if (!analysis) return null;
    
    return {
      ...analysis,
      // Frontend calculations
      priceChangePercent: ((analysis.currentPrice - analysis.previousPrice) / analysis.previousPrice) * 100,
      marketCapFormatted: formatCurrency(analysis.marketCap),
      volumeFormatted: formatCurrency(analysis.volume24h),
      // Frontend display helpers
      displayName: `${analysis.name} (${symbol.toUpperCase()})`,
      chartConfig: generateChartConfig(analysis),
    };
  }, [analysis, symbol]);

  return {
    analysis: derivedData,
    ...rest,
  };
}

export function useCryptoChartData(symbol: string, timeframe: string = '1h') {
  return useFrontendData<ChartData>(
    `/api/v1/assets/${symbol}/chart?interval=${timeframe}`,
    {
      refreshInterval: timeframe === '1h' ? 15000 : 60000, // Dynamic refresh based on timeframe
      cacheKey: `crypto-chart:${symbol}:${timeframe}`,
      revalidateOnFocus: true,
    }
  );
}

export function useCryptoRealtimePrice(symbol: string) {
  const [realtimePrice, setRealtimePrice] = useState<number | null>(null);
  
  useEffect(() => {
    const ws = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL}/ws/price/${symbol}`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setRealtimePrice(data.price);
    };

    return () => ws.close();
  }, [symbol]);

  return realtimePrice;
}

// Frontend-specific watchlist management
export function useFrontendWatchlist() {
  const { isAuthenticated, role } = useAuth();
  
  const endpoint = isAuthenticated ? '/api/v1/watchlists' : '/api/v1/watchlists/default';
  
  const { data: watchlists, mutate, ...rest } = useFrontendData<WatchlistData[]>(
    endpoint,
    {
      refreshInterval: 2 * 60 * 1000,
      cacheKey: `watchlist:${role}`,
    }
  );

  // Frontend watchlist operations
  const addToWatchlist = async (watchlistId: number, assetId: string) => {
    if (!isAuthenticated) {
      throw new Error('Authentication required');
    }

    // Optimistic update
    const updatedWatchlists = watchlists?.map(wl => 
      wl.id === watchlistId 
        ? { ...wl, assets: [...wl.assets, { id: assetId }] }
        : wl
    );
    
    mutate(updatedWatchlists, false);

    try {
      await apiClient.request(`/api/v1/watchlists/${watchlistId}/assets`, {
        method: 'POST',
        body: JSON.stringify({ asset_id: assetId }),
      });
    } catch (error) {
      // Revert optimistic update
      mutate();
      throw error;
    }
  };

  const removeFromWatchlist = async (watchlistId: number, assetId: string) => {
    if (!isAuthenticated) {
      throw new Error('Authentication required');
    }

    // Optimistic update
    const updatedWatchlists = watchlists?.map(wl => 
      wl.id === watchlistId 
        ? { ...wl, assets: wl.assets.filter(a => a.id !== assetId) }
        : wl
    );
    
    mutate(updatedWatchlists, false);

    try {
      await apiClient.request(`/api/v1/watchlists/${watchlistId}/assets/${assetId}`, {
        method: 'DELETE',
      });
    } catch (error) {
      // Revert optimistic update
      mutate();
      throw error;
    }
  };

  return {
    watchlists,
    addToWatchlist,
    removeFromWatchlist,
    mutate,
    ...rest,
  };
}

// Frontend helper functions
function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

function generateChartConfig(analysis: CryptoAnalysisData) {
  return {
    responsive: true,
    scales: {
      x: { type: 'time' },
      y: { beginAtZero: false },
    },
    plugins: {
      legend: { display: true },
      tooltip: { mode: 'index' },
    },
  };
}

function trackDataFetch(url: string, userRole: string, timestamp: number) {
  // Frontend analytics tracking
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', 'data_fetch', {
      endpoint: url,
      user_role: userRole,
      timestamp,
    });
  }
}

function trackDataError(url: string, error: any, userRole: string) {
  // Frontend error tracking
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', 'data_error', {
      endpoint: url,
      error_message: error.message,
      user_role: userRole,
    });
  }
}
```

---

## ⚡ **Frontend Real-time Integration**

### **🔄 State Management with Context + SWR:**
```typescript
// hooks/useAPIData.ts - Universal data fetching hook
import useSWR from 'swr';
import { apiClient } from '@/lib/api/client';
import { useAuth } from '@/contexts/AuthContext';

interface UseAPIDataOptions {
  refreshInterval?: number;
  revalidateOnFocus?: boolean;
  fallbackData?: any;
  onError?: (error: any) => void;
}

export function useAPIData<T>(
  endpoint: string,
  options: UseAPIDataOptions = {}
) {
  const { role, isAuthenticated } = useAuth();
  
  const fetcher = async (url: string) => {
    const response = await apiClient.request<T>(url);
    return response.data;
  };

  const {
    data,
    error,
    isLoading,
    isValidating,
    mutate,
  } = useSWR(
    endpoint,
    fetcher,
    {
      refreshInterval: options.refreshInterval || 0,
      revalidateOnFocus: options.revalidateOnFocus || true,
      fallbackData: options.fallbackData,
      onError: options.onError,
      // Conditional fetching based on auth state
      shouldRetryOnError: (error) => {
        // Don't retry 401/403 for guest users on protected endpoints
        if (!isAuthenticated && (error.status === 401 || error.status === 403)) {
          return false;
        }
        return true;
      },
    }
  );

  return {
    data,
    error,
    isLoading,
    isValidating,
    mutate, // For manual revalidation
    refresh: () => mutate(), // Alias for convenience
  };
}

// Specialized hooks for each layer
export function useMacroData() {
  return {
    regime: useAPIData<MacroRegimeData>('/api/v1/macro/regime', {
      refreshInterval: 5 * 60 * 1000, // 5 minutes
    }),
    sentiment: useAPIData<SentimentData>('/api/v1/macro/sentiment', {
      refreshInterval: 5 * 60 * 1000,
    }),
    dominance: useAPIData<DominanceData>('/api/v1/macro/dominance', {
      refreshInterval: 3 * 60 * 1000, // 3 minutes
    }),
    indicators: useAPIData<MacroIndicatorData>('/api/v1/macro/indicators', {
      refreshInterval: 10 * 60 * 1000, // 10 minutes
    }),
  };
}

export function useSectorData() {
  return {
    sectors: useAPIData<SectorData[]>('/api/v1/sectors'),
    performance: useAPIData<SectorPerformanceData>('/api/v1/sectors/performance', {
      refreshInterval: 5 * 60 * 1000,
    }),
    rotation: useAPIData<SectorRotationData>('/api/v1/sectors/rotation', {
      refreshInterval: 10 * 60 * 1000,
    }),
    allocation: useAPIData<SectorAllocationData>('/api/v1/sectors/allocation', {
      refreshInterval: 15 * 60 * 1000,
    }),
  };
}

export function useWatchlistData() {
  const { isAuthenticated } = useAuth();
  
  const endpoint = isAuthenticated ? '/api/v1/watchlists' : '/api/v1/watchlists/default';
  
  return useAPIData<WatchlistData[]>(endpoint, {
    refreshInterval: 2 * 60 * 1000, // 2 minutes
  });
}

export function useSignalsData() {
  return {
    current: useAPIData<TradingSignalData[]>('/api/v1/signals/current', {
      refreshInterval: 1 * 60 * 1000, // 1 minute
    }),
    alerts: useAPIData<AlertData[]>('/api/v1/signals/alerts'),
  };
}

export function useDashboardData(symbols?: string[]) {
  const endpoint = symbols 
    ? `/api/v1/dashboard/overview?symbols=${symbols.join(',')}`
    : '/api/v1/dashboard/overview';
    
  return useAPIData<DashboardData>(endpoint, {
    refreshInterval: 2 * 60 * 1000,
  });
}

// Admin-specific hooks
export function useAdminData() {
  const { role } = useAuth();
  
  if (role !== 'admin') {
    return {
      systemHealth: { data: null, error: new Error('Admin access required') },
      users: { data: null, error: new Error('Admin access required') },
      analytics: { data: null, error: new Error('Admin access required') },
    };
  }

  return {
    systemHealth: useAPIData<SystemHealthData>('/api/v1/admin/system/health', {
      refreshInterval: 30 * 1000, // 30 seconds
    }),
    users: useAPIData<UserOverviewData>('/api/v1/admin/users/overview'),
    analytics: useAPIData<AnalyticsData>('/api/v1/admin/analytics/usage'),
  };
}
```

---

## 🎨 **UI Component Integration**

### **🌐 Universal Components:**
```typescript
// components/layers/UniversalDashboard.tsx
interface UniversalDashboardProps {
  className?: string;
}

export function UniversalDashboard({ className }: UniversalDashboardProps) {
  const { role, isAuthenticated, user } = useAuth();
  const { data: dashboardData, isLoading } = useDashboardData();
  const { data: watchlists } = useWatchlistData();

  return (
    <div className={cn("dashboard-container", className)}>
      {/* Universal Header - adapts based on user type */}
      <DashboardHeader 
        userRole={role}
        isAuthenticated={isAuthenticated}
        user={user}
      />

      {/* 4-Layer Navigation - universal for all users */}
      <LayerNavigation currentLayer={1} />

      {/* Main Dashboard Content */}
      <div className="dashboard-content">
        {isLoading ? (
          <DashboardSkeleton />
        ) : (
          <>
            {/* Layer 1: Macro Overview - Universal Access */}
            <MacroOverviewCard data={dashboardData?.macro} />

            {/* Layer 2: Sector Performance - Universal Access */}
            <SectorPerformanceCard data={dashboardData?.sectors} />

            {/* Layer 3: Watchlist - Context-aware */}
            <WatchlistCard 
              data={watchlists}
              userRole={role}
              isAuthenticated={isAuthenticated}
            />

            {/* Layer 4: Trading Signals - Universal Access */}
            <TradingSignalsCard data={dashboardData?.signals} />
          </>
        )}
      </div>

      {/* Context-specific sidebars */}
      {role === 'admin' && (
        <AdminSidebar />
      )}

      {role === 'guest' && (
        <GuestPromptSidebar />
      )}
    </div>
  );
}

// components/layers/LayerNavigation.tsx
interface LayerNavigationProps {
  currentLayer: number;
}

export function LayerNavigation({ currentLayer }: LayerNavigationProps) {
  const layers = [
    { id: 1, name: 'Macro', href: '/macro', icon: Globe },
    { id: 2, name: 'Sectors', href: '/sectors', icon: BarChart3 },
    { id: 3, name: 'Assets', href: '/assets', icon: Coins },
    { id: 4, name: 'Signals', href: '/signals', icon: Zap },
  ];

  return (
    <nav className="layer-navigation">
      {layers.map((layer) => (
        <Link
          key={layer.id}
          href={layer.href}
          className={cn(
            "layer-nav-item",
            currentLayer === layer.id && "active"
          )}
        >
          <layer.icon className="w-4 h-4" />
          <span>{layer.name}</span>
        </Link>
      ))}
    </nav>
  );
}

// components/watchlists/WatchlistCard.tsx
interface WatchlistCardProps {
  data: WatchlistData[] | null;
  userRole: 'guest' | 'user' | 'admin';
  isAuthenticated: boolean;
}

export function WatchlistCard({ data, userRole, isAuthenticated }: WatchlistCardProps) {
  const [selectedWatchlist, setSelectedWatchlist] = useState<WatchlistData | null>(
    data?.[0] || null
  );

  return (
    <Card className="watchlist-card">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>
            {userRole === 'guest' ? 'Default Watchlist' : 'My Watchlists'}
          </CardTitle>
          
          {isAuthenticated && (
            <div className="flex gap-2">
              <WatchlistSelector 
                watchlists={data}
                selected={selectedWatchlist}
                onSelect={setSelectedWatchlist}
              />
              <CreateWatchlistButton />
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent>
        {selectedWatchlist ? (
          <WatchlistAssetList 
            watchlist={selectedWatchlist}
            canEdit={isAuthenticated}
          />
        ) : (
          <EmptyWatchlistState userRole={userRole} />
        )}
      </CardContent>

      {userRole === 'guest' && (
        <CardFooter>
          <GuestWatchlistPrompt />
        </CardFooter>
      )}
    </Card>
  );
}

// components/admin/AdminWatchlistToggle.tsx
export function AdminWatchlistToggle() {
  const { role } = useAuth();
  const [selectedContext, setSelectedContext] = useState<WatchlistContext | null>(null);
  
  if (role !== 'admin') return null;

  return (
    <div className="admin-watchlist-toggle">
      <Label>Admin Context Switch:</Label>
      <Select value={selectedContext?.id.toString()} onValueChange={handleContextChange}>
        <SelectTrigger>
          <SelectValue placeholder="Select watchlist context" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="default">Default Watchlist</SelectItem>
          <SelectItem value="personal">My Personal</SelectItem>
          {/* Dynamic user watchlists */}
        </SelectContent>
      </Select>
    </div>
  );
}
```

---

## ⚡ **Real-time Updates Integration**

### **🔄 Frontend WebSocket Management:**
```typescript
// hooks/useFrontendWebSocket.ts - Frontend-optimized WebSocket management
import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';

interface FrontendWebSocketOptions {
  reconnectAttempts?: number;
  reconnectInterval?: number;
  onMessage?: (data: any) => void;
  onError?: (error: Event) => void;
  onOpen?: () => void;
  onClose?: () => void;
  // Frontend-specific options
  autoReconnect?: boolean;
  bufferMessages?: boolean;
  heartbeatInterval?: number;
}

export function useFrontendWebSocket(
  endpoint: string,
  options: FrontendWebSocketOptions = {}
) {
  const { token, role, sessionId } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const [lastMessage, setLastMessage] = useState<any>(null);
  const [messageBuffer, setMessageBuffer] = useState<any[]>([]);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    try {
      setConnectionStatus('connecting');
      
      const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}${endpoint}`;
      const params = new URLSearchParams({
        session_id: sessionId,
        user_role: role,
      });
      
      if (token) {
        params.append('token', token);
      }
      
      const url = `${wsUrl}?${params.toString()}`;
      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = () => {
        setIsConnected(true);
        setConnectionStatus('connected');
        reconnectAttemptsRef.current = 0;
        
        // Start heartbeat
        if (options.heartbeatInterval) {
          heartbeatIntervalRef.current = setInterval(() => {
            if (wsRef.current?.readyState === WebSocket.OPEN) {
              wsRef.current.send(JSON.stringify({ type: 'ping' }));
            }
          }, options.heartbeatInterval);
        }

        // Send buffered messages
        if (options.bufferMessages && messageBuffer.length > 0) {
          messageBuffer.forEach(msg => {
            wsRef.current?.send(JSON.stringify(msg));
          });
          setMessageBuffer([]);
        }

        options.onOpen?.();
        console.log('Frontend WebSocket connected:', endpoint);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Handle heartbeat
          if (data.type === 'pong') return;
          
          setLastMessage(data);
          options.onMessage?.(data);
          
          // Frontend-specific message handling
          handleFrontendMessage(data);
        } catch (error) {
          console.error('Frontend WebSocket message parsing error:', error);
        }
      };

      wsRef.current.onclose = (event) => {
        setIsConnected(false);
        setConnectionStatus('disconnected');
        
        // Clear heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
          heartbeatIntervalRef.current = null;
        }

        console.log('Frontend WebSocket disconnected:', endpoint, event.code);
        
        // Auto-reconnect logic
        if (options.autoReconnect !== false && 
            reconnectAttemptsRef.current < (options.reconnectAttempts || 5)) {
          setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, options.reconnectInterval || 3000);
        }

        options.onClose?.();
      };

      wsRef.current.onerror = (error) => {
        setConnectionStatus('error');
        console.error('Frontend WebSocket error:', endpoint, error);
        options.onError?.(error);
      };

    } catch (error) {
      setConnectionStatus('error');
      console.error('Frontend WebSocket connection failed:', error);
    }
  }, [endpoint, token, role, sessionId, options, messageBuffer]);

  useEffect(() => {
    connect();
    
    return () => {
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
      }
      wsRef.current?.close();
    };
  }, [connect]);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else if (options.bufferMessages) {
      setMessageBuffer(prev => [...prev, message]);
    } else {
      console.warn('Frontend WebSocket not connected, message not sent:', message);
    }
  }, [options.bufferMessages]);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
  }, []);

  // Frontend-specific message handler
  const handleFrontendMessage = (data: any) => {
    switch (data.type) {
      case 'crypto_price_update':
        // Update price in all relevant components
        window.dispatchEvent(new CustomEvent('crypto-price-update', { detail: data }));
        break;
      case 'crypto_analysis_update':
        // Trigger SWR revalidation for analysis data
        window.dispatchEvent(new CustomEvent('crypto-analysis-update', { detail: data }));
        break;
      case 'user_notification':
        // Show notification to user
        showFrontendNotification(data.message, data.type);
        break;
      case 'market_alert':
        // Handle market alerts
        handleMarketAlert(data);
        break;
    }
  };

  return {
    isConnected,
    connectionStatus,
    lastMessage,
    sendMessage,
    disconnect,
    reconnect: connect,
    messageBuffer: messageBuffer.length,
  };
}

// Specialized WebSocket hooks for different features
export function useCryptoRealtimeUpdates(symbols: string[]) {
  const [priceUpdates, setPriceUpdates] = useState<Record<string, number>>({});
  
  const { isConnected, sendMessage } = useFrontendWebSocket('/ws/crypto', {
    onMessage: (data) => {
      if (data.type === 'price_update') {
        setPriceUpdates(prev => ({
          ...prev,
          [data.symbol]: data.price,
        }));
      }
    },
    autoReconnect: true,
    heartbeatInterval: 30000, // 30 seconds
  });

  useEffect(() => {
    if (isConnected && symbols.length > 0) {
      sendMessage({
        type: 'subscribe',
        symbols,
      });
    }
  }, [isConnected, symbols, sendMessage]);

  return {
    priceUpdates,
    isConnected,
  };
}

export function useSignalAlerts() {
  const [alerts, setAlerts] = useState<SignalAlert[]>([]);
  
  useFrontendWebSocket('/ws/alerts', {
    onMessage: (data) => {
      if (data.type === 'signal_alert') {
        setAlerts(prev => [data.alert, ...prev.slice(0, 49)]); // Keep last 50 alerts
        showFrontendNotification(data.alert.message, 'signal');
      }
    },
    autoReconnect: true,
  });

  return { alerts };
}

// Frontend notification system
function showFrontendNotification(message: string, type: string) {
  // Create toast notification
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.remove();
  }, 5000);
}

function handleMarketAlert(data: any) {
  // Frontend-specific market alert handling
  console.log('Market Alert:', data);
  
  // Update UI components that depend on market conditions
  window.dispatchEvent(new CustomEvent('market-alert', { detail: data }));
}
```

### **📱 Frontend Mobile PWA Integration:**
```typescript
// hooks/useFrontendPWA.ts - Progressive Web App features
import { useEffect, useState } from 'react';

export function useFrontendPWA() {
  const [isInstallable, setIsInstallable] = useState(false);
  const [isInstalled, setIsInstalled] = useState(false);
  const [isOnline, setIsOnline] = useState(true);
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);

  useEffect(() => {
    // Check if already installed
    setIsInstalled(window.matchMedia('(display-mode: standalone)').matches);

    // Listen for install prompt
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setIsInstallable(true);
    };

    // Listen for successful install
    const handleAppInstalled = () => {
      setIsInstalled(true);
      setIsInstallable(false);
      setDeferredPrompt(null);
    };

    // Listen for online/offline
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const installApp = async () => {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      
      if (outcome === 'accepted') {
        setIsInstallable(false);
        setDeferredPrompt(null);
      }
    }
  };

  return {
    isInstallable,
    isInstalled,
    isOnline,
    installApp,
  };
}

// Frontend offline data management
export function useFrontendOfflineData() {
  const [offlineData, setOfflineData] = useState<any>(null);
  const [isOfflineMode, setIsOfflineMode] = useState(false);

  useEffect(() => {
    const handleOffline = () => {
      setIsOfflineMode(true);
      // Load cached data from IndexedDB
      loadOfflineData();
    };

    const handleOnline = () => {
      setIsOfflineMode(false);
      // Sync with server when back online
      syncOfflineData();
    };

    window.addEventListener('offline', handleOffline);
    window.addEventListener('online', handleOnline);

    return () => {
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('online', handleOnline);
    };
  }, []);

  const loadOfflineData = async () => {
    try {
      // Load from IndexedDB
      const cachedData = await getCachedData();
      setOfflineData(cachedData);
    } catch (error) {
      console.error('Failed to load offline data:', error);
    }
  };

  const syncOfflineData = async () => {
    try {
      // Sync offline changes with server
      await syncWithServer();
    } catch (error) {
      console.error('Failed to sync offline data:', error);
    }
  };

  return {
    offlineData,
    isOfflineMode,
  };
}

// Frontend performance monitoring
export function useFrontendPerformance() {
  const [performanceMetrics, setPerformanceMetrics] = useState<any>(null);

  useEffect(() => {
    // Monitor Core Web Vitals
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach((entry) => {
        if (entry.entryType === 'navigation') {
          setPerformanceMetrics(prev => ({
            ...prev,
            loadTime: entry.loadEventEnd - entry.loadEventStart,
            domContentLoaded: entry.domContentLoadedEventEnd - entry.domContentLoadedEventStart,
          }));
        }
      });
    });

    observer.observe({ entryTypes: ['navigation', 'paint'] });

    return () => observer.disconnect();
  }, []);

  return { performanceMetrics };
}
```

---

## ⚡ **Frontend Performance & Security**

### **🚀 Frontend Performance Optimization:**
```typescript
// hooks/useFrontendOptimization.ts - Client-side performance
import { useCallback, useEffect, useMemo, useState } from 'react';
import { debounce, throttle } from 'lodash';

// Frontend caching strategy
export function useFrontendCache<T>(key: string, data: T, ttl = 300000) { // 5 min default
  const [cachedData, setCachedData] = useState<T | null>(null);
  
  useEffect(() => {
    // Check localStorage cache
    const cached = localStorage.getItem(key);
    if (cached) {
      try {
        const { data: cachedData, timestamp } = JSON.parse(cached);
        if (Date.now() - timestamp < ttl) {
          setCachedData(cachedData);
          return;
        }
      } catch (error) {
        console.warn('Frontend cache error:', error);
      }
    }
    
    // Cache new data
    if (data) {
      localStorage.setItem(key, JSON.stringify({
        data,
        timestamp: Date.now(),
      }));
      setCachedData(data);
    }
  }, [key, data, ttl]);

  const clearCache = useCallback(() => {
    localStorage.removeItem(key);
    setCachedData(null);
  }, [key]);

  return { cachedData, clearCache };
}

// Frontend lazy loading for crypto data
export function useFrontendLazyLoad() {
  const [visibleItems, setVisibleItems] = useState(20);
  const [isLoading, setIsLoading] = useState(false);

  const loadMoreItems = useCallback(
    throttle(() => {
      if (!isLoading) {
        setIsLoading(true);
        setTimeout(() => {
          setVisibleItems(prev => prev + 20);
          setIsLoading(false);
        }, 200);
      }
    }, 1000),
    [isLoading]
  );

  return {
    visibleItems,
    isLoading,
    loadMoreItems,
  };
}

// Frontend search optimization
export function useFrontendSearch(items: any[], searchFields: string[]) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredItems, setFilteredItems] = useState(items);

  const debouncedSearch = useMemo(
    () => debounce((term: string) => {
      if (!term.trim()) {
        setFilteredItems(items);
        return;
      }

      const filtered = items.filter(item => 
        searchFields.some(field => 
          item[field]?.toString().toLowerCase().includes(term.toLowerCase())
        )
      );
      setFilteredItems(filtered);
    }, 300),
    [items, searchFields]
  );

  useEffect(() => {
    debouncedSearch(searchTerm);
  }, [searchTerm, debouncedSearch]);

  return {
    searchTerm,
    setSearchTerm,
    filteredItems,
  };
}

// Frontend image optimization
export function useFrontendImageOptimization() {
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);

  const handleImageLoad = useCallback(() => {
    setIsLoaded(true);
    setHasError(false);
  }, []);

  const handleImageError = useCallback(() => {
    setHasError(true);
    setIsLoaded(false);
  }, []);

  return {
    isLoaded,
    hasError,
    handleImageLoad,
    handleImageError,
  };
}
```

### **🔐 Frontend Security Implementation:**
```typescript
// utils/frontendSecurity.ts - Client-side security measures
export class FrontendSecurity {
  
  // Sanitize user inputs
  static sanitizeInput(input: string): string {
    return input
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
      .replace(/javascript:/gi, '')
      .replace(/on\w+\s*=/gi, '');
  }

  // Validate crypto symbols
  static validateSymbol(symbol: string): boolean {
    const validPattern = /^[A-Z]{2,10}$/;
    return validPattern.test(symbol);
  }

  // Secure localStorage wrapper
  static secureStorage = {
    set(key: string, value: any, encrypt = true): void {
      try {
        const data = encrypt ? btoa(JSON.stringify(value)) : JSON.stringify(value);
        localStorage.setItem(`crypto_${key}`, data);
      } catch (error) {
        console.error('Frontend storage error:', error);
      }
    },

    get(key: string, decrypt = true): any {
      try {
        const data = localStorage.getItem(`crypto_${key}`);
        if (!data) return null;
        
        return decrypt ? JSON.parse(atob(data)) : JSON.parse(data);
      } catch (error) {
        console.error('Frontend retrieval error:', error);
        return null;
      }
    },

    remove(key: string): void {
      localStorage.removeItem(`crypto_${key}`);
    },

    clear(): void {
      Object.keys(localStorage)
        .filter(key => key.startsWith('crypto_'))
        .forEach(key => localStorage.removeItem(key));
    }
  };

  // Rate limiting for frontend requests
  static createRateLimiter(maxRequests: number, windowMs: number) {
    const requests: number[] = [];

    return function rateLimiter(): boolean {
      const now = Date.now();
      
      // Remove old requests outside the window
      while (requests.length > 0 && requests[0] <= now - windowMs) {
        requests.shift();
      }

      if (requests.length >= maxRequests) {
        return false; // Rate limit exceeded
      }

      requests.push(now);
      return true;
    };
  }

  // Frontend token validation
  static validateToken(token: string): boolean {
    if (!token) return false;
    
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp * 1000 > Date.now();
    } catch {
      return false;
    }
  }

  // Secure API request headers
  static getSecureHeaders(token?: string): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
      'Cache-Control': 'no-cache',
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }
}

// Frontend error boundary for crypto components
export class CryptoErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback?: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Crypto component error:', error, errorInfo);
    
    // Log to frontend monitoring service
    this.logErrorToService(error, errorInfo);
  }

  logErrorToService(error: Error, errorInfo: React.ErrorInfo) {
    // Send error to monitoring service
    fetch('/api/frontend-errors', {
      method: 'POST',
      headers: FrontendSecurity.getSecureHeaders(),
      body: JSON.stringify({
        error: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
      }),
    }).catch(console.error);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="crypto-error-boundary">
          <h3>خطا در بارگذاری اطلاعات کریپتو</h3>
          <p>لطفاً صفحه را مجدداً بارگذاری کنید</p>
          <button 
            onClick={() => window.location.reload()}
            className="btn btn-primary"
          >
            بارگذاری مجدد
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// Frontend monitoring hooks
export function useFrontendMonitoring() {
  const [performanceMetrics, setPerformanceMetrics] = useState<any>({});
  
  useEffect(() => {
    // Monitor page load times
    const navigationEntry = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    
    if (navigationEntry) {
      setPerformanceMetrics({
        pageLoadTime: navigationEntry.loadEventEnd - navigationEntry.loadEventStart,
        domContentLoaded: navigationEntry.domContentLoadedEventEnd - navigationEntry.loadEventStart,
        firstContentfulPaint: 0, // Will be updated by PerformanceObserver
      });
    }

    // Monitor Core Web Vitals
    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        if (entry.entryType === 'paint' && entry.name === 'first-contentful-paint') {
          setPerformanceMetrics(prev => ({
            ...prev,
            firstContentfulPaint: entry.startTime,
          }));
        }
      });
    });

    observer.observe({ entryTypes: ['paint'] });

    return () => observer.disconnect();
  }, []);

  const logUserAction = useCallback((action: string, details?: any) => {
    // Log user interactions for frontend analytics
    console.log('User Action:', action, details);
    
    // Send to analytics service if needed
    fetch('/api/frontend-analytics', {
      method: 'POST',
      headers: FrontendSecurity.getSecureHeaders(),
      body: JSON.stringify({
        action,
        details,
        timestamp: new Date().toISOString(),
        url: window.location.href,
      }),
    }).catch(console.error);
  }, []);

  return {
    performanceMetrics,
    logUserAction,
  };
}
```

---

**📊 Frontend Performance Targets:**
- **First Contentful Paint:** < 1.5s
- **Largest Contentful Paint:** < 2.5s  
- **Cumulative Layout Shift:** < 0.1
- **First Input Delay:** < 100ms
- **Time to Interactive:** < 3.5s

**🔐 Frontend Security Checklist:**
- ✅ Input sanitization and validation
- ✅ Secure token storage and validation  
- ✅ Rate limiting on client requests
- ✅ Error boundary implementation
- ✅ Performance monitoring
- ✅ User action logging
```

---

**📅 Frontend Integration Timeline:**  
**🎯 Focus:** React Components, API Consumption, Real-time Updates, Mobile PWA  
**🔗 Dependencies:** Backend APIs (84 endpoints) must be ready  
**⏱️ Implementation:** 10-15 days after backend completion
