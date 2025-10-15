# **timestamp_strategy**

## **استانداردسازی Timestamp Fields:**

  همه جداول استاندارد `created_at` و `updated_at` داشته باشند و فیلدهای مشابه با نام‌های مختلف حذف شوند.

### **📋 لیست کامل فیلدهای timestamp که باید استاندارد شوند:**

#### **✅ جداولی که فعلاً استاندارد هستند:**
- `users`: `created_at`, `updated_at` ✅
- `cryptocurrencies`: `created_at`, `updated_at` ✅  
- `watchlists`: `created_at`, `updated_at` ✅

#### **❌ جداولی که نیاز به تغییر دارند:**

```sql
-- 1. price_data
-- فعلی: created_at فقط
-- باید باشد: created_at, updated_at

-- 2. watchlist_assets  
-- فعلی: added_at
-- باید باشد: created_at, updated_at
-- حذف: added_at

-- 3. regime_analysis
-- فعلی: analysis_time, created_at, updated_at
-- باید باشد: created_at, updated_at
-- حذف: analysis_time

-- 4. sector_performance
-- فعلی: analysis_time, created_at  
-- باید باشد: created_at, updated_at
-- حذف: analysis_time

-- 5. trading_signals
-- فعلی: generated_at, expires_at, updated_at
-- باید باشد: created_at, updated_at, expires_at
-- حذف: generated_at

-- 6. signal_executions
-- فعلی: executed_at, updated_at
-- باید باشد: created_at, updated_at
-- حذف: executed_at

-- 7. ai_suggestions
-- فعلی: created_at, expires_at, reviewed_at, implemented_at
-- باید باشد: created_at, updated_at, expires_at
-- حذف: reviewed_at, implemented_at

-- 8. system_health
-- فعلی: check_time, created_at
-- باید باشد: created_at, updated_at
-- حذف: check_time

-- و ادامه برای سایر جداول...
```

### **🎯 استراتژی پیشنهادی:**

1. **همه جداول استاندارد داشته باشند:**
   ```sql
   created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
   updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   ```

2. **فیلدهای خاص فقط برای موارد ضروری:**
   ```sql
   expires_at    -- برای چیزهایی که منقضی می‌شوند
   last_login    -- برای کاربران
   last_trained  -- برای مدل‌های AI
   ```

3. **حذف فیلدهای تکراری:**
   - `added_at` → `created_at`
   - `generated_at` → `created_at`
   - `analysis_time` → `created_at`
   - `executed_at` → `created_at`
   - `check_time` → `created_at`
