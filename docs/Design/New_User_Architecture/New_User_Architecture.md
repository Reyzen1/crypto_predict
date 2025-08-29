# docs\Design\New_User_Architecture.md
# 👥 معماری کاربری جدید CryptoPredict فاز دوم
## Single UI Design با Multi-Level Access

---

## 🎯 **تغییرات کلیدی از طراحی قبلی**

### **🔄 از 3 Persona به 2 User Type:**
```
❌ طراحی قبلی: 
├── Admin/System Manager
├── Professional Trader  
└── Casual Investor

✅ طراحی جدید:
├── 👑 Admin User
└── 👤 Regular User (با سطوح مختلف دسترسی)
```

### **🎨 Single UI Philosophy:**
- **یک interface واحد** برای همه کاربران
- **Progressive complexity** در خود UI تعبیه شده
- **Contextual help** برای سطوح مختلف
- **No separate views** - همه از یک طراحی استفاده می‌کنند

---

## 👥 **User Types و دسترسی‌ها**

### **🌐 Guest User (Anonymous)**
```
🔓 دسترسی آزاد:
├── ✅ تمام 4 لایه AI (Layer 1-4)
├── ✅ مشاهده Admin Watchlist (پیش‌فرض)
├── ✅ تمام تحلیل‌ها و charts
├── ✅ AI suggestions مربوط به Admin Watchlist
├── ✅ تمام امکانات عمومی سیستم
└── ❌ امکانات شخصی (watchlist, settings, history)

📊 Analytics:
├── ✅ General usage tracking (برای آمار کلی)
├── ✅ Personal behavior tracking
└── ❌ Detailed user profiling

🎯 تشویق به ثبت‌نام:
├── 💡 Gentle banner: "Create personal watchlist"
├── 🔔 Action-based prompts
└── 📈 Benefits highlighting
```

### **👤 Logged User (Regular)**
```
🔐 همه امکانات Guest +:
├── ✅ Personal Watchlist (اختیاری)
├── ✅ Personal AI Suggestions
├── ✅ Settings & Preferences
├── ✅ Performance History
├── ✅ Custom notifications
└── ✅ Progress tracking

📋 Watchlist Logic:
├── بدون Personal Watchlist → Admin Watchlist نمایش
├── با Personal Watchlist → Personal Watchlist نمایش
└── Toggle capability (اگر مورد نیاز باشد)

🤖 AI Features:
├── Personal context AI suggestions
├── Personalized risk assessment
├── Custom performance tracking
└── Tailored educational content
```

### **👑 Admin User**
```
🔧 همه امکانات Logged User +:
├── ✅ Admin Panel access (link در header)
├── ✅ Default Watchlist management
├── ✅ مشاهده تمام User Watchlists
├── ✅ ویرایش هر User Watchlist
├── ✅ User Management
├── ✅ System Performance monitoring
├── ✅ AI Parameters control
└── ✅ Complete audit access

🎛️ Watchlist Toggle System:
├── ○ Default Watchlist (15 items) [Edit]
├── ○ My Personal (8 items) [Edit] 
├── ○ User: john@example.com (12 items) [Edit]
├── ○ User: sarah@example.com (6 items) [Edit]
└── ○ User: mike@example.com (20 items) [Edit]

👁️ User Data Access:
├── Complete watchlist contents
├── User settings & preferences
├── Performance history & analytics
├── Personal AI suggestions
├── Activity patterns & engagement
└── All timestamps & metadata
```

---

## 🔐 **Authentication Strategy**

### **🎯 Just-in-Time Authentication:**
```
🚪 Login Triggers:
├── کلیک روی "Edit Watchlist" → Login prompt
├── کلیک روی "Add to Watchlist" → Login prompt
├── کلیک روی "Save Settings" → Login prompt  
├── کلیک روی "View History" → Login prompt
├── کلیک روی "Create Alert" → Login prompt
└── هر action شخصی دیگر → Login modal

💡 Gentle Encouragement:
┌─────────────────────────────────────────────────┐
│ 💎 Create your personal watchlist and get      │
│ custom AI recommendations - Login for better   │
│ experience                                      │
│ [Login] [Maybe Later] [×]                      │
└─────────────────────────────────────────────────┘

🔄 Post-Login Flow:
Login → Redirect to intended action → Complete action
```

### **📱 Login Modal vs Redirect:**
- **Modal**: برای سادگی و continuity
- **Same page**: حفظ context و user state
- **Quick process**: minimal friction

---

## 🧭 **Navigation & Interface Design**

### **🎯 Header Structure:**
```
Header Layout:
┌─────────────────────────────────────────────────┐
│ [Logo] [Navigation] ...              [Login]   │  ← Guest User
│ [Logo] [Navigation] ...              [User ▼]  │  ← Logged User
│ [Logo] [Navigation] ... [Admin Panel] [User ▼] │  ← Admin User
└─────────────────────────────────────────────────┘

Admin Panel Link:
├── فقط برای Admin نمایش داده می‌شود
├── نام: "Admin Panel"
├── مکان: قبل از User dropdown
└── Direct access به management interface
```

### **🎛️ Watchlist Management Interface:**

#### **برای Guest & New Users:**
```
📋 Watchlist Display:
┌─────────────────────────────────────┐
│ 📈 Default Watchlist (15 assets)   │
│ ┌─────────────────────────────────┐ │
│ │ 🟢 BTC  $43,250 +2.5%          │ │
│ │ 🟡 ETH  $2,680  +1.8%          │ │
│ │ 🔵 ADA  $0.52   -0.3%          │ │
│ │ ... more assets                 │ │
│ └─────────────────────────────────┘ │
│ [📝 Create Personal Watchlist]     │ ← Login trigger
└─────────────────────────────────────┘
```

#### **برای Logged Users:**
```
📋 Personal Watchlist:
┌─────────────────────────────────────┐
│ 📊 My Watchlist (8 assets) [Edit]  │
│ ┌─────────────────────────────────┐ │
│ │ Selected personal assets...     │ │
│ └─────────────────────────────────┘ │
│                                     │
│ 🔄 View Default Watchlist          │ ← Toggle option
└─────────────────────────────────────┘
```

#### **برای Admin:**
```
🔧 Admin Watchlist Control:
┌─────────────────────────────────────┐
│ 📋 Watchlist View: [Select ▼]      │
│ ├── ○ Default Watchlist [Edit]     │
│ ├── ○ My Personal [Edit]           │
│ ├── ○ User: john@example.com [Edit]│
│ ├── ○ User: sarah@example.com [Edit]│
│ └── ○ User: mike@example.com [Edit]│
│                                     │
│ Currently viewing: Default (15)     │
│ ┌─────────────────────────────────┐ │
│ │ Assets with full edit controls  │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

---

## 🤖 **AI Integration Strategy**

### **🧠 Context-Aware AI Suggestions:**
```
AI Suggestion Logic:
├── Guest Users → Admin Watchlist context
├── Logged Users (no personal) → Admin Watchlist context
├── Logged Users (with personal) → Personal Watchlist context
├── Admin viewing Default → Default context
├── Admin viewing User X → User X context
└── Admin viewing Personal → Personal context

🎯 AI Personalization Levels:
├── Level 0 (Guest): General market insights
├── Level 1 (Logged): Personal preferences applied
├── Level 2 (History): Historical behavior considered
├── Level 3 (Advanced): Full ML personalization
└── Level 4 (Admin): System-wide optimization insights
```

### **📊 4-Layer System Access:**
```
🌍 Layer 1 (Macro): همه کاربران - no restrictions
📊 Layer 2 (Sector): همه کاربران - no restrictions  
💰 Layer 3 (Asset): context-based suggestions
⚡ Layer 4 (Timing): context-based signals

Rate Limiting:
├── Guest Users: unlimited access
├── Logged Users: unlimited access
├── Admin Users: unlimited access
└── No API restrictions based on user type
```

---

## 🗄️ **Database Architecture Changes**
تغییری در دیتابیس نداریم فقط:
Table users:
 در جدول users مقادیر فیلد role عبارت خواهند بود از : 'admin', 'public' و دیفالت آن 'public' است.
Table watchlists:
در جدول watchlists مقادیر فیلد type عبارت خواهند بود از : 'default', 'personal' 

## 🛡️ **Security & Privacy**

### **🔒 Admin Permissions:**
```
👑 Admin Capabilities:
├── ✅ View any user watchlist (complete data)
├── ✅ Edit any user watchlist (add/remove/reorder)
├── ✅ Access user performance history
├── ✅ View user AI suggestions
├── ✅ Modify user settings (if needed)
├── ✅ User management (activate/deactivate)
└── ✅ System-wide configuration

🛡️ Security Measures:
├── IP address tracking
├── Timestamp recording
├── Action details stored
└── Audit trail maintenance
```

### **👁️ User Privacy:**
```
🔐 Privacy Settings:
├── Users NOT notified of admin viewing
├── Users NOT notified of admin edits
├── Admin activities silent to users
├── Audit logs admin-only accessible
└── User data access controlled by role

📊 Data Access Levels:
├── Guest: public data only
├── User: own data + public data
├── Admin: all data + system data
└── Audit: admin action history
```

---

## 🚀 **Implementation Priorities**

### **📋 Phase 1: Core User System (Week 1-2)**
```
🎯 Essential Features:
├── ✅ User registration/login system
├── ✅ Role-based authentication  
├── ✅ Guest access implementation
├── ✅ Basic watchlist CRUD
├── ✅ Admin panel access control
└── ✅ Audit logging system
```

### **📋 Phase 2: Watchlist Management (Week 3-4)**
```
🎯 Watchlist Features:
├── ✅ Default watchlist system
├── ✅ Personal watchlist creation
├── ✅ Admin toggle interface
├── ✅ Watchlist editing controls
├── ✅ Context-aware AI suggestions
└── ✅ Performance tracking
```

### **📋 Phase 3: Advanced Features (Week 5-6)**
```
🎯 Enhanced Capabilities:
├── ✅ Advanced admin controls
├── ✅ User management interface
├── ✅ System performance monitoring
├── ✅ AI parameter controls
├── ✅ Complete audit dashboard
└── ✅ Mobile responsiveness
```

---

## 🎯 **Success Metrics**

### **📊 User Engagement:**
```
🌐 Guest User Metrics:
├── Page views and session duration
├── Feature usage patterns
├── Conversion to registered users
└── Return visitor rates

👤 Logged User Metrics:
├── Watchlist creation rates
├── Personal feature adoption
├── Session frequency and duration
└── Feature utilization depth

👑 Admin Efficiency:
├── Time spent on management tasks
├── User support efficiency
├── System optimization effectiveness
└── Decision-making speed improvement
```

### **🎪 User Experience Goals:**
```
✅ Single UI serves all user types effectively
✅ Seamless transition from guest to logged user
✅ Intuitive admin controls without complexity
✅ No feature discovery friction
✅ Progressive enhancement working naturally
```

---

## 💡 **Key Design Principles**

### **🎨 Universal Design:**
- **One interface** serves beginner to expert
- **Progressive disclosure** shows complexity as needed
- **Contextual help** available throughout
- **No artificial barriers** to feature access

### **🔐 Privacy by Design:**
- **Minimal data collection** for guests  
- **Transparent permissions** for logged users
- **Silent admin operations** to avoid user concern
- **Complete audit trail** for accountability

### **⚡ Performance First:**
- **No rate limiting** based on user type
- **Full AI access** for all users
- **Optimized for guest users** (largest segment)
- **Scalable architecture** for growth

---

**📅 تاریخ تدوین:** نسخه 1.0 - بر اساس جلسات طراحی فاز دوم
**🎯 هدف:** معماری یکپارچه و قابل اجرا برای CryptoPredict Phase 2