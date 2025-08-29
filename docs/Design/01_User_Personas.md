# docs\Design\01_User_Personas.md
# 👥 User Types - CryptoPredict فاز دوم
## Single UI Design with Progressive Access Levels

---

## 📋 **تحلیل کاربران فاز یک**

### **📊 بررسی User Feedback موجود:**
بر اساس گزارش فاز یک، insights کلیدی عبارتند از:

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

## 🎯 **معماری کاربری جدید**

### **🔄 Single UI Philosophy:**
- **یک رابط کاربری واحد** برای همه سطوح کاربران
- **Progressive complexity** در خود UI تعبیه شده
- **Contextual help** برای سطوح مختلف درک
- **No separate views** - همه از یک طراحی استفاده می‌کنند

---

## 👥 **User Types تعریف شده**

## 🌐 **Guest User (Anonymous)**
### **"کاربر بدون ثبت‌نام"**

**📋 Profile:**
- **وضعیت:** ناشناس، بدون ثبت‌نام
- **دسترسی:** کامل به تمام امکانات سیستم
- **تجربه:** از مبتدی تا پیشرفته
- **هدف:** کشف امکانات و ارزیابی سیستم

**🔓 دسترسی‌های آزاد:**
- ✅ **تمام 4 لایه AI** (Layer 1-4) بدون محدودیت
- ✅ **مشاهده Admin Watchlist** (15 کوین پیش‌فرض)
- ✅ **تمام تحلیل‌ها و charts** بدون rate limiting
- ✅ **AI suggestions** مربوط به Admin Watchlist
- ✅ **تمام امکانات عمومی سیستم**
- ❌ **امکانات شخصی** (watchlist, settings, history)

**💡 تشویق به ثبت‌نام:**
- **Gentle banners:** "Create personal watchlist for custom AI recommendations"
- **Action-based prompts:** هنگام کلیک روی عملیات شخصی
- **Benefits highlighting:** نمایش مزایای ثبت‌نام

**🎯 Goals & Needs:**
- **کشف سیستم:** درک امکانات و قابلیت‌ها
- **ارزیابی کیفیت:** صحت پیش‌بینی‌ها و تحلیل‌ها
- **آموزش:** درک مبانی تحلیل کریپتو
- **تصمیم‌گیری:** آیا ثبت‌نام کند یا خیر

**😤 Potential Friction Points:**
- **عدم دسترسی به تاریخچه شخصی**
- **نبود watchlist شخصی**
- **عدم ذخیره تنظیمات**
- **نبود notification شخصی**

---

## 👤 **Regular User (Logged In)**
### **"کاربر عادی ثبت‌نام شده"**

**📋 Profile:**
- **سن:** 25-55 سال
- **تجربه کریپتو:** از مبتدی تا متوسط
- **فعالیت:** روزانه تا هفتگی
- **هدف:** سرمایه‌گذاری هوشمند و آموزش

**🔐 همه امکانات Guest User + امکانات شخصی:**
- ✅ **Personal Watchlist** (اختیاری، تا 25 کوین)
- ✅ **Personal AI Suggestions** based on personal watchlist
- ✅ **Settings & Preferences** (theme, notifications, language)
- ✅ **Performance History** (track record شخصی)
- ✅ **Custom Notifications** (price alerts, signals)
- ✅ **Progress Tracking** (learning progress, accuracy)

**📋 Watchlist Logic:**
- **بدون Personal Watchlist:** Admin Watchlist نمایش داده می‌شود
- **با Personal Watchlist:** Personal Watchlist نمایش داده می‌شود
- **Toggle Capability:** امکان تعویض بین Default و Personal

**🤖 AI Features:**
- **Personal Context AI:** suggestions based on personal watchlist
- **Personalized Risk Assessment:** بر اساس تاریخچه کاربر
- **Custom Performance Tracking:** track record دقیق
- **Tailored Educational Content:** بر اساس سطح دانش

**🎯 Goals & Needs:**
- **سرمایه‌گذاری موثر:** بهبود performance شخصی
- **یادگیری مداوم:** توسعه مهارت‌های تحلیل
- **مدیریت ریسک:** حفظ سرمایه و رشد پایدار
- **Personalization:** سفارشی‌سازی تجربه کاربری

**💡 Needs & Requirements:**
- **Personal Dashboard:** نمای شخصی از دارایی‌ها
- **Watchlist Management:** ایجاد و مدیریت لیست شخصی
- **Historical Analysis:** بررسی عملکرد گذشته
- **Learning Tools:** ابزارهای آموزشی تعاملی
- **Mobile Optimization:** تجربه بهینه روی موبایل

---

## 👑 **Admin User (System Manager)**
### **"مدیر سیستم"**

**📋 Profile:**
- **سن:** 30-50 سال
- **تخصص:** مدیریت سیستم‌های مالی/AI
- **تجربه کریپتو:** 3+ سال
- **مسئولیت:** بهینه‌سازی سیستم و نظارت

**🔧 همه امکانات Regular User + قابلیت‌های مدیریتی:**
- ✅ **Admin Panel Access** (لینک در header)
- ✅ **Default Watchlist Management** (15 کوین اصلی)
- ✅ **مشاهده تمام User Watchlists** (complete data access)
- ✅ **ویرایش هر User Watchlist** (add/remove/reorder)
- ✅ **User Management** (activate/deactivate accounts)
- ✅ **System Performance Monitoring** (KPIs, metrics)
- ✅ **AI Parameters Control** (model tuning, thresholds)
- ✅ **Complete Audit Access** (all user actions)

**🎛️ Watchlist Toggle System:**
```
📋 Admin Watchlist Control:
├── ○ Default Watchlist (15 items) [Edit]
├── ○ My Personal (8 items) [Edit] 
├── ○ User: john@example.com (12 items) [Edit]
├── ○ User: sarah@example.com (6 items) [Edit]
└── ○ User: mike@example.com (20 items) [Edit]
```

**👁️ User Data Access:**
- **Complete Watchlist Contents:** تمام دارایی‌های کاربران
- **User Settings & Preferences:** تنظیمات شخصی
- **Performance History & Analytics:** عملکرد تاریخی
- **Personal AI Suggestions:** پیشنهادات شخصی کاربران
- **Activity Patterns:** الگوهای استفاده و engagement
- **All Metadata:** timestamps, IP addresses, actions

**🎯 Goals & Objectives:**
- **System Optimization:** بهبود accuracy و performance
- **User Experience Enhancement:** بهبود تجربه کاربری
- **Quality Control:** نظارت بر کیفیت پیشنهادات AI
- **Data-Driven Decisions:** تصمیم‌گیری بر اساس آمار
- **Fraud Prevention:** شناسایی فعالیت‌های مشکوک

**💡 Needs & Requirements:**
- **Comprehensive Dashboard:** KPIs کلیدی سیستم
- **Bulk Management Tools:** عملیات گروهی
- **Advanced Analytics:** تحلیل عمقی کاربران
- **Alert System:** هشدارهای فوری سیستم
- **Audit Trail:** ردیابی کامل اعمال

---

## 🔐 **Authentication Strategy**

### **🚪 Just-in-Time Authentication:**
```
Login Triggers (برای Guest Users):
├── کلیک روی "Create Personal Watchlist" → Login modal
├── کلیک روی "Save Settings" → Login prompt
├── کلیک روی "View My History" → Authentication required
├── کلیک روی "Set Alert" → Login modal
└── هر عمل شخصی دیگر → Gentle login prompt
```

**💡 Gentle Encouragement:**
```
┌─────────────────────────────────────────────────┐
│ 💎 Create your personal watchlist and get      │
│ custom AI recommendations tailored to you      │
│                                                 │
│ [Login/Register] [Continue as Guest] [×]       │
└─────────────────────────────────────────────────┘
```

---

## 📊 **Design Implications**

### **🎨 Single UI Considerations:**
- **Progressive Disclosure:** پیچیدگی بر اساس نیاز نمایش
- **Contextual Help:** راهنمایی مناسب برای هر سطح
- **Universal Navigation:** منو واحد برای همه کاربران
- **Adaptive Content:** محتوا بر اساس سطح کاربر

### **🔄 State Management:**
```
UI States:
├── Guest State: تمام امکانات عمومی + Login prompts
├── Logged State: امکانات شخصی + Personal controls
├── Admin State: Management controls + Admin panel link
└── Loading States: Progressive loading برای هر state
```

### **📱 Mobile Considerations:**
- **Touch-First Design:** برای همه سطوح کاربران
- **Responsive Navigation:** منو تطبیقی
- **Gesture Support:** عملیات لمسی بهینه
- **Performance Optimization:** سرعت بالا برای Guest users

---

## 🎯 **Success Metrics**

### **📈 User Engagement:**
```
🌐 Guest User Metrics:
├── Session Duration: 5+ minutes average
├── Page Views: 8+ pages per session
├── Feature Usage: 60%+ try major features
├── Conversion Rate: 25%+ to registered user
└── Return Rate: 40%+ return within 7 days

👤 Regular User Metrics:
├── Personal Watchlist Creation: 70%+ create within 30 days
├── Daily Active Users: 35%+ return daily
├── Feature Adoption: 80%+ use personal features
├── Retention: 60%+ active after 3 months
└── Satisfaction: 8/10+ average rating

👑 Admin Efficiency:
├── Management Time: 50%+ reduction in admin tasks
├── User Support: 60%+ faster issue resolution
├── System Optimization: 25%+ accuracy improvement
├── Decision Speed: 40%+ faster strategic decisions
└── User Growth: 30%+ increase in active users
```

### **🔄 Conversion Funnel:**
```
Guest → Logged Conversion:
├── Guest Session → 100%
├── Feature Interest → 80%
├── Login Prompt → 50%
├── Registration → 35%
├── Personal Setup → 25%
└── Active User → 20%

Success Rate Target: 20%+ Guest-to-Active conversion
```

---

**📅 آخرین بروزرسانی:** نسخه 2.0 - بر اساس معماری کاربری جدید فاز دوم
**🎯 هدف:** Single UI Design with Progressive Access Levels