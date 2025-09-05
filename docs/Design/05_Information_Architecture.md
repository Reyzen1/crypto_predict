# docs\Design\05_Information_Architecture.md
# 🏗️ Information Architecture - CryptoPredict فاز دوم
## Single UI Navigation Structure & Universal Content Hierarchy

---

## 🗺️ **Site Architecture Design - New Architecture**

### **🎯 Single UI Navigation Philosophy:**
- **Universal Navigation:** یک منو برای همه سطوح کاربری
- **Progressive Disclosure:** قابلیت‌ها بر اساس نیاز نمایش داده می‌شود
- **Context-Aware Adaptation:** منو بر اساس وضعیت کاربر تطبیق می‌یابد
- **Just-in-Time Controls:** کنترل‌های admin فقط هنگام نیاز نمایش

---

## 📐 **Primary Navigation Structure**

### **🎛️ Main Navigation Menu (Universal Header)**
```
CryptoPredict Universal Navigation:

┌─────────────────────────────────────────────────────────────────────────────┐
│ [Logo] [Nav Menu...] [Search] [Theme] [Admin Panel?] [Login/User ▼]       │
└─────────────────────────────────────────────────────────────────────────────┘

Navigation Menu Items (All User Types):
🏠 Dashboard     🌍 Macro (L1)    📊 Sector (L2)    💰 Assets (L3)    ⚡ Timing (L4)

Additional Header Elements (Context-Based):
├── 🔍 Search: Universal search for all content
├── 🌙 Theme Toggle: Dark/Light mode for all users
├── 👑 Admin Panel: Only visible for Admin users
└── 🔐 Login/User: Guest→Login button, Logged→User dropdown, Admin→Extended menu
```

### **🔍 Navigation Context Adaptation**
```
🌐 Guest User Navigation:
Header: [Logo] [Dashboard] [Macro] [Sector] [Assets] [Timing] [🔍] [🌙] [Login]

👤 Logged User Navigation:
Header: [Logo] [Dashboard] [Macro] [Sector] [Assets] [Timing] [🔍] [🌙] [User ▼]

👑 Admin User Navigation:
Header: [Logo] [Dashboard] [Macro] [Sector] [Assets] [Timing] [🔍] [🌙] [Admin Panel] [User ▼]

🔄 State Transitions:
├── Guest → Logged: [Login] button becomes [User ▼] dropdown
├── Logged → Admin: [Admin Panel] link appears
├── Admin → Logged: [Admin Panel] link disappears (if role changed)
└── Universal: Core navigation always consistent
```

### **🎛️ Admin Panel Access Integration**
```
👑 Admin Panel Navigation (Separate Interface):

Access Method: "Admin Panel" link in main header (admin users only)

Admin Panel Structure:
┌─────────────────────────────────────────────────────────┐
│ 🎛️ CryptoPredict Admin Panel                          │
│                                                         │
│ [Dashboard] [Watchlist Mgmt] [Users] [Analytics] [System] [Back to App] │
└─────────────────────────────────────────────────────────┘

Admin Panel Navigation:
├── 🏠 Admin Dashboard: System overview & KPIs
├── 📋 Watchlist Management: Default & user watchlists
├── 👥 User Management: User accounts & permissions
├── 📊 Analytics & Reports: System performance & insights
├── ⚙️ System Settings: Configuration & maintenance
└── 🔙 Back to Main App: Return to regular interface
```

## 📊 **4-Layer Content Structure (Universal)**

### **🌍 Layer 1 (Macro) - All Users**
```
Navigation Path: /macro

Content Access (Universal):
├── 🔓 Market Regime Detection: Bull/Bear/Neutral/Volatile
├── 🔓 Dominance Analysis: BTC.D, ETH.D, Alt.D tracking
├── 🔓 Sentiment Analysis: Fear & Greed + social sentiment
├── 🔓 DeFi Metrics: DeFi dominance & ecosystem health
├── 🔓 Volatility Forecasting: VIX-style crypto volatility
└── 🔓 Correlation Analysis: Cross-market relationships

User Experience Adaptation:
├── 🌐 Guest: Full access + educational tooltips
├── 👤 Logged: Full access + personal context notes
└── 👑 Admin: Full access + system impact indicators
```

### **📊 Layer 2 (Sector) - All Users**
```
Navigation Path: /sector

Content Access (Universal):
├── 🔓 Sector Rotation Analysis: Flow between sectors
├── 🔓 Performance Comparison: Sector-by-sector metrics
├── 🔓 Money Flow Tracking: Capital allocation patterns
├── 🔓 Leadership Identification: Leading & lagging sectors
├── 🔓 Allocation Recommendations: Sector balance suggestions
└── 🔓 Narrative Analysis: Sector theme & trend tracking

User Experience Adaptation:
├── 🌐 Guest: Full analysis + sector education
├── 👤 Logged: Full analysis + personal sector preferences
└── 👑 Admin: Full analysis + system optimization insights
```

### **💰 Layer 3 (Assets) - All Users**
```
Navigation Path: /assets

Content Structure (Universal Access):
├── 🔓 Admin Watchlist (15 selected cryptocurrencies)
├── 🔓 Crypto Analysis Pages (deep dive for each asset)
├── 👤 Personal Watchlist (logged users only)
├── 🔓 Performance Metrics: 7d/30d/90d returns
├── 🔓 Technical Analysis: RSI, MACD, Moving Averages
├── 🔓 Fundamental Data: Network stats, development activity
├── 🔓 Social Sentiment: Reddit, Twitter, News sentiment
├── 🔓 Correlation Matrix: Asset pair relationships
└── 🔓 Historical Patterns: Price pattern recognition

Individual Crypto Analysis Structure:
┌─────────────────────────────────────────────────────────┐
│ 📊 BITCOIN (BTC) - Complete Analysis                   │
├─────────────────────────────────────────────────────────┤
│ 💰 Price & Market Data                                 │
│ 📈 Interactive Technical Chart                         │
│ 🤖 AI Predictions & Confidence                         │
│ 📊 Technical Indicators                                │
│ 📰 News & Sentiment Analysis                           │
│ 🔍 Fundamental Analysis                                │
│ 💼 Institutional Data                                  │
│ 🎯 Trading Opportunities                               │
│ ⚠️ Risk Factors                                        │
│ 🔄 Quick Actions (Trade/Alert/Save)                    │
└─────────────────────────────────────────────────────────┘

Navigation Access:
├── From Watchlist: Direct click on any crypto
├── From Search: Type crypto name in search
├── From Layer 4: Click on asset in timing signals
├── Direct URL: /assets/[crypto-symbol]
└── Mobile: Swipeable sections for touch navigation

User Experience Adaptation:
├── 🌐 Guest: Full analysis access + conversion CTAs
├── 👤 Logged: Full access + personal notes + alerts
└── 👑 Admin: Full access + system performance data
```
Navigation Path: /assets

Content Access Strategy:
├── 🌐 Guest Users: Admin Watchlist context (15 assets)
├── 👤 Logged Users (No Personal): Admin Watchlist context
├── 👤 Logged Users (Personal): Personal Watchlist context
├── 👑 Admin (Default View): Admin Watchlist context
├── 👑 Admin (Personal View): Personal Watchlist context
└── 👑 Admin (User View): Selected User Watchlist context

Watchlist Toggle Interface (Admin Only):
┌─────────────────────────────────────────────────────────┐
│ 📋 Viewing: [Select Watchlist ▼]                      │
│ ├── ○ Default Watchlist (15 assets) [Edit]            │
│ ├── ○ My Personal (8 assets) [Edit]                   │
│ ├── ○ User: john@example.com (12 assets) [View/Edit]   │
│ └── ○ User: sarah@example.com (6 assets) [View/Edit]   │
└─────────────────────────────────────────────────────────┘

Content Features:
├── 🔓 Asset Analysis: Technical & fundamental analysis
├── 🔓 AI Recommendations: Context-based suggestions
├── 🔓 Performance Tracking: Historical & predictive metrics
├── 🔓 Research Tools: Comprehensive analysis suite
├── 🔒 Personal Actions: Add/remove from watchlist (login required)
└── 👑 Admin Actions: Manage any watchlist (admin only)
```

### **⚡ Layer 4 (Timing Signals) - Context-Based**
```
Navigation Path: /timing

Content Access Strategy:
├── Same context logic as Layer 3
├── Signals based on active watchlist context
├── Entry/exit recommendations for context assets
└── Risk management for context portfolio

Signal Types (All Users):
├── 🔓 Entry Signals: Buy/Long opportunities
├── 🔓 Exit Signals: Sell/Short/Hold recommendations
├── 🔓 Risk Signals: Portfolio protection alerts
├── 🔓 Performance Tracking: Signal accuracy & results
├── 🔒 Personal Alerts: Custom notifications (login required)
└── 👑 Admin Monitoring: System-wide signal performance
```

## 🔐 **Authentication & State Management**

### **🚪 Login/Logout State Integration**
```
Authentication States in Navigation:

🌐 Guest State:
├── Header: [Login] button (right side)
├── No personal menu options
├── Access to all content with educational prompts
├── Gentle encouragement for personal features
└── "Create Account" call-to-actions in appropriate contexts

👤 Logged State:
├── Header: [User ▼] dropdown replaces [Login] button
├── User Dropdown Menu:
│   ├── 👤 Profile & Settings
│   ├── 📋 My Watchlist
│   ├── 📊 My Performance
│   ├── 🔔 Notifications
│   ├── 📚 Learning Progress
│   └── 🚪 Logout
├── Personal features accessible throughout app
└── Context-aware AI suggestions

👑 Admin State:
├── Header: [Admin Panel] link + [User ▼] dropdown
├── Admin-specific dropdown additions:
│   ├── 🎛️ Admin Dashboard (shortcut)
│   ├── 👥 User Management (shortcut)
│   ├── 📊 System Analytics (shortcut)
│   └── 🔧 System Settings (shortcut)
├── Extended permissions throughout app
└── Watchlist toggle capabilities
```

### **🔄 Seamless State Transitions**
```
State Change Animations:
├── Guest → Logged: Smooth header transformation
├── Login → Redirect: Preserve navigation context
├── Feature Unlock: Progressive disclosure animation
└── Admin Toggle: Contextual controls slide in/out

Context Preservation:
├── Maintain current page during login
├── Preserve analysis state across authentication
├── Keep filters & preferences during transitions
└── Seamless watchlist context switching
```

---

## 🗂️ **URL Structure Design**

### **🌐 Universal URL Architecture**
```
Base Structure: https://cryptopredict.app

Core Routes (All Users):
├── / (Dashboard - context-aware default)
├── /macro (Layer 1 - Universal access)
├── /sector (Layer 2 - Universal access)
├── /assets (Layer 3 - Context-based content)
├── /timing (Layer 4 - Context-based signals)
├── /settings (User preferences)
├── /help (Support & learning)
└── /about (Company information)

Authentication Routes:
├── /login (Login page)
├── /register (Registration page)
├── /forgot-password (Password recovery)
└── /logout (Logout redirect)

Admin-Only Routes:
├── /admin (Admin panel gateway)
├── /admin/dashboard (Admin overview)
├── /admin/watchlists (Watchlist management)
├── /admin/users (User management)
├── /admin/analytics (System analytics)
└── /admin/settings (System configuration)
```

### **📱 Mobile & API Routes**
```
Mobile-Optimized Routes:
├── /m/* (Mobile-specific layouts)
├── /pwa (Progressive Web App resources)
└── /offline (Offline functionality)

API Routes:
├── /api/v1/auth/* (Authentication endpoints)
├── /api/v1/layers/* (4-Layer AI endpoints)
├── /api/v1/watchlists/* (Watchlist management)
├── /api/v1/admin/* (Admin-only endpoints)
└── /api/v1/public/* (Public data endpoints)
```

---

## 📋 **Content Hierarchy & Prioritization**

### **🎯 Universal Content Priority Framework**
```
Priority Level 1 (Critical - Always Visible):
├── Navigation menu & user status
├── System health & performance indicators
├── Active alerts & notifications
├── Primary action recommendations
└── Core dashboard metrics

Priority Level 2 (Important - Prominent):
├── AI insights & predictions
├── Performance summaries
├── Market context information
├── Trending opportunities
└── Recent activity summaries

Priority Level 3 (Useful - On-Demand):
├── Detailed analytics & charts
├── Historical data & comparisons
├── Advanced settings & configurations
├── Educational content & tutorials
└── Support & help resources

Priority Level 4 (Archive - Deep Access):
├── Complete historical records
├── Advanced system configurations
├── Developer tools & APIs
├── Comprehensive reports
└── Audit logs & system data
```

### **🌐 Guest User Content Strategy**
```
Guest Content Prioritization:
├── 🔥 Immediate Value Demonstration (Priority 1)
├── ⚡ Feature Discovery & Exploration (Priority 2)
├── 💡 Educational Content & Guidance (Priority 2)
├── 📊 Historical Performance Evidence (Priority 3)
├── 🎯 Conversion Encouragement (Contextual)
└── 📚 Learning Resources (Priority 3)

Content Adaptation:
├── Simplified language & explanations
├── Interactive tooltips & help
├── Clear value propositions
├── Social proof & testimonials
└── Easy conversion paths
```

### **👤 Logged User Content Strategy**
```
Logged Content Prioritization:
├── 🔥 Personal Performance & Portfolio (Priority 1)
├── ⚡ Personalized AI Recommendations (Priority 1)
├── 📊 Context-Based Analysis (Priority 1)
├── 💡 Learning Progress & Achievements (Priority 2)
├── 🔔 Custom Alerts & Notifications (Priority 2)
└── ⚙️ Personalization & Settings (Priority 3)

Content Adaptation:
├── Personalized insights & recommendations
├── Historical performance tracking
├── Custom notification preferences
├── Learning path continuation
└── Advanced feature access
```

### **👑 Admin Content Strategy**
```
Admin Content Prioritization:
├── 🔥 System Health & Performance (Priority 1)
├── ⚡ Critical Issues & Alerts (Priority 1)
├── 📊 User Activity & Engagement (Priority 1)
├── 💡 Optimization Opportunities (Priority 2)
├── 🛠️ Management Tools & Controls (Priority 2)
└── 📈 Strategic Analytics & Reports (Priority 3)

Content Adaptation:
├── Data-rich dashboards & metrics
├── Bulk operation capabilities
├── System oversight & control panels
├── User management interfaces
└── Strategic planning tools
```

---

## 📱 **Mobile Navigation Patterns**

### **📲 Mobile-First Navigation Design**
```
Mobile Navigation Strategy:
├── 🍔 Hamburger Menu: Primary navigation
├── 🎯 Bottom Tab Bar: Quick access to 4 layers
├── 🔍 Search: Persistent search functionality
├── 👤 Profile: User status & quick actions
└── 🚀 Floating Action Button: Primary actions

Mobile Header (Responsive):
┌─────────────────────────────────┐
│ [☰] CryptoPredict [🔍] [👤] │
└─────────────────────────────────┘

Bottom Tab Bar (4-Layer Access):
┌─────────────────────────────────┐
│ [🏠] [🌍] [📊] [💰] [⚡]     │
│ Dash Macro Sector Assets Timing │
└─────────────────────────────────┘
```

### **📱 Mobile Context Adaptation**
```
Mobile Guest Experience:
├── Simplified navigation with exploration hints
├── Swipe tutorials for feature discovery
├── Touch-friendly educational overlays
└── Easy access to login/registration

Mobile Logged Experience:
├── Personal shortcuts in navigation
├── Quick action gestures
├── Push notification integration
└── Cross-device synchronization

Mobile Admin Experience:
├── Essential admin controls accessible
├── Touch-optimized management interfaces
├── Mobile-friendly bulk operations
└── Emergency system controls
```

---

## 🔍 **Search & Filtering Architecture**

### **🔍 Universal Search System**
```
Search Functionality (All Users):
├── 🔍 Global Search: Assets, analysis, features
├── 🎯 Contextual Search: Within current section
├── 📊 Smart Suggestions: AI-powered recommendations
├── 📱 Voice Search: Mobile voice input
└── 🔄 Search History: Recent searches (logged users)

Search Categories:
├── 💰 Assets: Cryptocurrencies & tokens
├── 📊 Analysis: Reports & insights
├── 🎓 Learning: Educational content
├── ⚙️ Settings: Configuration options
└── 👑 Admin: System management (admin only)
```

### **🎛️ Filtering & Customization**
```
Filter Options (Context-Aware):
├── ⏰ Time Range: 1h, 4h, 1d, 1w, 1m, all time
├── 📊 Performance: Top performers, underperformers
├── 🎯 Confidence: High, medium, low AI confidence
├── 💰 Market Cap: Large, mid, small cap
├── 📈 Trends: Trending up, down, sideways
└── 👤 Personalized: Based on user preferences (logged users)

Advanced Filters (Progressive Disclosure):
├── Technical Indicators: RSI, MACD, Bollinger Bands
├── Fundamental Metrics: Volume, market cap, supply
├── Sentiment Filters: Bullish, bearish, neutral
├── Sector Filters: DeFi, Gaming, Infrastructure, etc.
└── Custom Filters: User-defined criteria (logged users)
```

---

## 📊 **Content Organization Best Practices**

### **🎯 Information Architecture Principles**
```
✅ Universal Design Principles:
├── 🧠 Cognitive Load Management: Progressive complexity
├── 📱 Mobile-First: Essential content prioritized
├── 🔍 Discoverability: Clear navigation paths
├── ⚡ Performance: Fast access to critical info
├── 🎯 Task-Oriented: Support user goals efficiently
├── 📊 Visual Hierarchy: Clear importance indicators
└── 🔄 Consistency: Predictable interaction patterns

✅ Accessibility & Inclusion:
├── ♿ WCAG 2.1 AA Compliance: Screen reader friendly
├── ⌨️ Keyboard Navigation: Full keyboard accessibility
├── 🎨 High Contrast: Visual accessibility options
├── 📝 Clear Language: Plain language principles
├── 🌍 Internationalization: Multi-language support
└── 📱 Touch Accessibility: Large touch targets
```

### **🔄 Adaptive Content Strategy**
```
Content Adaptation Framework:
├── 🌐 Guest Focus: Discovery & value demonstration
├── 👤 Logged Focus: Personalization & progress tracking
├── 👑 Admin Focus: System oversight & optimization
├── 📱 Mobile Focus: Touch-friendly & simplified
├── 🌙 Theme Focus: Dark/light mode optimization
└── 🎯 Context Focus: Situational content relevance

Cross-User Consistency:
├── 🎨 Visual Design Language: Consistent across all users
├── 🔄 Interaction Patterns: Predictable behaviors
├── 📊 Data Presentation: Standardized formats
├── 🎯 Navigation Logic: Intuitive path structures
└── 💡 Help System: Contextual assistance available
```

---

**📅 آخرین بروزرسانی:** نسخه 2.0 - بر اساس معماری کاربری جدید فاز دوم
**🎯 هدف:** Single UI Navigation with Universal Access & Progressive Enhancement