# docs\Design\01_User_Personas.md
# 👥 User Personas - CryptoPredict فاز دوم
## Primary User Types & Behavioral Analysis

---

## 📋 **تحلیل کاربران فاز یک (1 ساعت)**

### **📊 بررسی User Feedback موجود:**
بر اساس گزارش فاز یک، کاربران اصلی سیستم عبارتند از:

**✅ فاز یک Insights:**
- **80% کاربران:** از basic prediction استفاده کرده‌اند
- **15% کاربران:** از admin features استفاده کرده‌اند  
- **60% درخواست:** برای multi-asset prediction
- **70% نیاز:** به simplified interface
- **90% تقاضا:** برای real-time signals

**⚠️ شناسایی شده Pain Points:**
- پیچیدگی interface برای کاربران مبتدی
- کمبود guidance در تصمیم‌گیری
- نیاز به personalization بیشتر
- کمبود mobile optimization

---

## 🎯 **Primary Personas (3 شخصیت اصلی)**

## 👨‍💼 **Persona 1: Admin/System Manager**
### **"محمدرضا - مدیر سیستم"**

**📋 Profile:**
- **سن:** 35-45 سال
- **تخصص:** مدیریت سیستم‌های مالی
- **تجربه کریپتو:** 5+ سال
- **تکنولوژی:** Expert level
- **ساعات کاری:** 8+ ساعت/روز

**🎯 Goals & Objectives:**
- **Primary Goal:** مدیریت کارآمد watchlist و بهینه‌سازی عملکرد سیستم
- **Secondary Goal:** نظارت بر auto-suggestions و quality control
- **Business Goal:** افزایش accuracy کل سیستم
- **Personal Goal:** کاهش workload manual و automation بیشتر

**😤 Pain Points:**
- **وقت‌گیر بودن:** بررسی manual تمام suggestions
- **عدم شفافیت:** در دلایل پیشنهادات AI
- **کنترل محدود:** بر prioritization الگوریتم‌ها
- **گزارش‌گیری:** کمبود dashboard جامع برای تصمیم‌گیری

**💡 Needs & Requirements:**
- **Dashboard جامع:** با KPIs کلیدی و performance metrics (Bull/Bear)
- **Bulk Actions:** برای مدیریت watchlist (bulk add/remove/tier change)
- **AI Explanation:** دلایل هر suggestion با confidence score (Buy/Sell/Hold)
- **Historical Analysis:** track record accuracy برای decision support
- **Alert System:** برای موارد نیازمند توجه فوری (Market regime changes)
- **Permission Management:** سطوح دسترسی مختلف
- **Bear Market Tools:** Defensive asset management و risk-off strategies
- **Two-Sided Analytics:** Bull/Bear performance tracking و strategy effectiveness

**⚡ User Journey Highlights:**
1. **صبح:** بررسی overnight suggestions و market changes
2. **روز:** monitoring system performance و user activities
3. **عصر:** بررسی و approval/rejection suggestions
4. **تحلیل:** weekly performance analysis و system tuning

**📱 Device Usage:**
- **Desktop:** 80% (primary work environment)
- **Mobile:** 20% (monitoring on-the-go)

**🎨 UI/UX Preferences:**
- **Information Dense:** بیشترین اطلاعات در کمترین فضا
- **Quick Actions:** دسترسی سریع به frequent actions
- **Data Visualization:** charts و graphs برای trend analysis
- **Professional Look:** clean, corporate design

---

## 💼 **Persona 2: Professional Trader**
### **"علیرضا - معامله‌گر حرفه‌ای"**

**📋 Profile:**
- **سن:** 28-40 سال
- **تخصص:** Technical Analysis & Trading
- **تجربه کریپتو:** 3+ سال
- **سرمایه:** $50K+ portfolio
- **ساعات کاری:** 6+ ساعت/روز
- **تکنولوژی:** Advanced level

**🎯 Goals & Objectives:**
- **Primary Goal:** maximum profit با managed risk
- **Secondary Goal:** دسترسی به high-quality signals
- **Trading Goal:** beat market performance consistently
- **Learning Goal:** درک بهتر market dynamics از طریق AI insights

**😤 Pain Points:**
- **Information Overload:** زیاد بودن منابع اطلاعاتی
- **Timing Issues:** دیر رسیدن signals یا missed opportunities
- **False Signals:** پیش‌بینی‌های اشتباه که منجر به loss می‌شود
- **Context Missing:** کمبود توضیح macro context برای signals

**💡 Needs & Requirements:**
- **Real-time Signals:** with precise entry/exit points (Long/Short)
- **Risk Management:** automatic stop-loss/take-profit suggestions
- **Multi-layer Analysis:** درک comprehensive از market dynamics (Bull/Bear)
- **Backtesting:** historical performance data برای validation
- **Customization:** تنظیم risk tolerance و investment horizon
- **Integration:** با trading platforms (API connections)
- **Bear Market Tools:** Short selling opportunities و defensive strategies
- **Market Regime Adaptation:** Strategy adjustment based on Bull/Bear/Neutral phases
- **Portfolio Hedging:** Risk management در volatile markets
- **Two-Sided Execution:** Long و Short position management tools

**🔧 Feature Priorities:**
1. **Layer 4 Timing Signals** (Critical) - Buy/Sell/Short
2. **Layer 1 Macro Context** (High) - Bull/Bear regime detection
3. **Risk Management Tools** (High) - Long/Short position management
4. **Bear Market Strategies** (High) - Defensive positioning
5. **Performance Tracking** (Medium) - Bull/Bear performance
6. **Portfolio Integration** (Medium) - Two-sided exposure

**⚡ User Journey Highlights:**
1. **Pre-market:** بررسی overnight developments و macro context
2. **Market Hours:** active monitoring signals و quick decision making
3. **Post-market:** analysis performance و adjustment strategies

**📱 Device Usage:**
- **Desktop:** 70% (primary trading setup)
- **Mobile:** 30% (monitoring during travel)

**🎨 UI/UX Preferences:**
- **Speed First:** minimal loading times
- **Information Hierarchy:** most important data prominently displayed
- **Customizable Dashboard:** arrange widgets based on preference
- **Dark Theme:** easier on eyes during long sessions

---

## 🌱 **Persona 3: Casual Investor**
### **"سارا - سرمایه‌گذار مبتدی"**

**📋 Profile:**
- **سن:** 25-35 سال
- **تخصص:** غیرمالی (مهندس، پزشک، معلم)
- **تجربه کریپتو:** 1-2 سال
- **سرمایه:** $5K-20K portfolio
- **زمان:** 1-2 ساعت/روز
- **تکنولوژی:** Beginner to Intermediate

**🎯 Goals & Objectives:**
- **Primary Goal:** رشد تدریجی سرمایه با ریسک کم
- **Secondary Goal:** یادگیری درباره crypto markets
- **Investment Goal:** long-term wealth building
- **Personal Goal:** financial security و independence

**😤 Pain Points:**
- **Complexity:** پیچیدگی technical analysis
- **Uncertainty:** عدم اطمینان در decision making
- **FOMO/Fear:** ترس از دست دادن opportunities یا losses
- **Information Gap:** نفهمیدن market trends و patterns

**💡 Needs & Requirements:**
- **Simple Interface:** clear و easy-to-understand
- **Guided Decisions:** step-by-step recommendations (Buy/Sell/Hold)
- **Educational Content:** explanation پشت هر پیشنهاد
- **Risk Warnings:** clear indication of risk levels
- **Dollar Cost Averaging:** support برای DCA strategies
- **Portfolio Overview:** simple performance tracking
- **Bear Market Education:** How to handle market downturns
- **Defensive Strategies:** Safe haven assets و capital preservation
- **Sell Timing Guidance:** When and how to take profits or cut losses
- **Market Cycle Understanding:** Bull/Bear cycle education

**🎓 Learning Needs:**
- **Market Basics:** understanding market cycles
- **Layer Explanation:** simple explanation of 4-layer approach
- **Terminology:** crypto terms dictionary
- **Risk Management:** basic principles

**⚡ User Journey Highlights:**
1. **Weekly Check:** بررسی portfolio performance
2. **Decision Time:** following guided recommendations
3. **Learning:** reading explanations و educational content

**📱 Device Usage:**
- **Mobile:** 60% (convenience و on-the-go)
- **Desktop:** 40% (detailed analysis)

**🎨 UI/UX Preferences:**
- **Simplicity:** clean, uncluttered interface
- **Visual Guidance:** icons, colors, progress indicators
- **Explanatory Text:** tooltips و help sections
- **Light Theme:** friendly و welcoming appearance

---

## 📊 **Cross-Persona Analysis**

### **🎯 Common Needs:**
- **Reliability:** accurate predictions و stable system
- **Performance:** fast loading و responsive interface
- **Trust:** transparent methodology و proven results
- **Support:** help documentation و customer service

### **⚖️ Conflicting Requirements:**
- **Information Density:** Admin wants dense, Casual wants simple
- **Customization:** Pro wants full control, Casual wants guided
- **Frequency:** Pro needs real-time, Casual prefers periodic

### **🎨 Design Implications:**
- **Adaptive Interface:** different views based on user type
- **Progressive Disclosure:** show complexity gradually
- **Role-based Features:** feature access based on user level
- **Contextual Help:** assistance where needed

---

## 📋 **Layer-wise User Needs Matrix**

### **🌍 Layer 1 (Macro Market):**

| Persona | Need Level | Use Case | Frequency |
|---------|------------|----------|-----------|
| **Admin** | **Critical** | System optimization based on market regime | Daily |
| **Professional** | **High** | Trading strategy adjustment | Multiple/day |
| **Casual** | **Medium** | General market understanding | Weekly |

### **📊 Layer 2 (Sector Analysis):**

| Persona | Need Level | Use Case | Frequency |
|---------|------------|----------|-----------|
| **Admin** | **High** | Watchlist sector balancing | Weekly |
| **Professional** | **Critical** | Sector rotation strategies | Daily |
| **Casual** | **Low** | Diversification guidance | Monthly |

### **💰 Layer 3 (Asset Selection):**

| Persona | Need Level | Use Case | Frequency |
|---------|------------|----------|-----------|
| **Admin** | **Critical** | Watchlist management | Daily |
| **Professional** | **Critical** | Trading opportunities | Multiple/day |
| **Casual** | **High** | Investment choices | Weekly |

### **⚡ Layer 4 (Timing):**

| Persona | Need Level | Use Case | Frequency |
|---------|------------|----------|-----------|
| **Admin** | **Medium** | Signal quality monitoring (Bull/Bear) | Daily |
| **Professional** | **Critical** | Entry/exit timing (Long/Short) | Multiple/day |
| **Casual** | **Medium** | Buy/sell guidance (Market cycle aware) | Weekly |

---

## 🎯 **Two-Sided Market Feature Priority Matrix**

### **🔥 High Priority (All Personas):**
- Main Dashboard با layer overview (Bull/Bear context)
- Asset Selection (Layer 3) interface (Long/Short opportunities)
- Basic Performance Tracking (Market regime aware)
- Mobile Responsive Design
- **Bear Market Dashboard** (Risk-off strategies)
- **Sell Signal Interface** (Exit optimization)

### **⚡ Medium Priority:**
- Admin Watchlist Management
- Layer 1 Macro Analysis (Bull/Bear regime detection)
- Educational Content (Market cycle education)
- Risk Management Tools (Long/Short position management)
- **Defensive Asset Selection** (Bear market assets)
- **Short Selling Tools** (Professional traders)

### **💡 Low Priority:**
- Advanced Customization
- API Integration
- Advanced Analytics
- White-label Options

---

## 📈 **Success Metrics per Persona**

### **👨‍💼 Admin Success:**
- **Efficiency:** 50% reduction in manual review time
- **Accuracy:** 80%+ auto-suggestion acceptance rate (Buy/Sell combined)
- **Coverage:** 95%+ watchlist optimization
- **Satisfaction:** 4.5/5 dashboard usability
- **Market Adaptation:** 90%+ regime change detection accuracy

### **💼 Professional Success:**
- **Performance:** 15%+ improvement in trading results (Bull/Bear markets)
- **Speed:** <2 sec signal delivery (Long/Short)
- **Accuracy:** 75%+ signal success rate (Both directions)
- **Retention:** 90%+ monthly active usage
- **Risk Management:** 80%+ proper position sizing adherence

### **🌱 Casual Success:**
- **Understanding:** 80% feature comprehension rate (Market cycles)
- **Engagement:** 70%+ weekly active usage
- **Growth:** 10%+ improvement in investment decisions
- **Learning:** completion of educational content
- **Risk Awareness:** 85% proper risk assessment in decisions

---

**📤 Output:** User Personas Document Complete 