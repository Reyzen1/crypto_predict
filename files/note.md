# 📊 لیست کامل داده‌های جمع‌آوری‌شده

## ✅ داده‌های دریافت‌شده (Rایگان)

### 1. داده‌های قیمت BTC/ETH
- ✓ `btc_price` → CoinGecko
- ✓ `eth_price` → CoinGecko
- ✓ `btc_volume` → CoinGecko
- ✓ `eth_volume` → CoinGecko
- ✓ `btc_market_cap` → CoinGecko
- ✓ `eth_market_cap` → CoinGecko

### 2. داده‌های دمینانس و بازار
- ✓ `btc_dominance` → CoinGecko
- ✓ `eth_dominance` → CoinGecko
- ✓ `altcoin_dominance` → CoinGecko (محاسبه‌شده)
- ✓ `total_market_cap` → CoinGecko

### 3. داده‌های Futures
- ✓ `open_interest_btc` → CoinGlass
- ✓ `funding_rate_btc` → CoinGlass
- ✓ `liquidations_long` → CoinGlass
- ✓ `liquidations_short` → CoinGlass

### 4. داده‌های محاسبه‌شده
- ✓ `weekly_return` → محاسبه‌شده (7 روزه)
- ✓ `monthly_return` → محاسبه‌شده (30 روزه)
- ✓ `btc_eth_correlation_30d` → محاسبه‌شده
- ✓ `liquidity_score` → محاسبه‌شده
- ✓ `momentum_index` → محاسبه‌شده (RSI)

### 5. داده‌های بازار
- ✓ `new_highs_24h` → محاسبه‌شده
- ✓ `new_lows_24h` → محاسبه‌شده
- ✓ `crypto_market_breadth` → محاسبه‌شده

### 6. داده‌های Macro (Alpha Vantage)
- ✓ `sp500` → Alpha Vantage (SPY)
- ✓ `gold` → Alpha Vantage (GLD)
- ✓ `vix_index` → Alpha Vantage

### 7. داده‌های Macro (FRED)
- ✓ `dxy` → FRED (US Dollar Index)
- ✓ `us_10y_yield` → FRED (10-Year Treasury Yield)

### 8. داده‌های خاص
- ✓ `halving_countdown_days` → محاسبه‌شده
- ✓ `btc_sp500_correlation_30d` → محاسبه‌شده

---

## ❌ داده‌های غیرممکن رایگان (0 ثابت)

| داده | دلیل | منبع پولی |
|-----|------|---------|
| `whale_netflow_24h` | نیاز به API پولی | CryptoQuant ($99/ماه) |
| `active_addresses_btc` | نیاز به API پولی | Glassnode ($199/ماه) |
| `usdt_dominance` | داده دقیق نیست | CoinGecko |
| `liquidation_zones` | محاسبه پیچیده | CoinGlass Pro |

---

## 📋 منابع و API Keys مورد نیاز

### CoinGecko
- ✓ **رایگان**: بدون API Key
- 📍 **Rate Limit**: 10-50 درخواست/دقیقه
- 🔗 URL: `https://api.coingecko.com/api/v3`
- ℹ️ **توضیح**: بهترین برای داده‌های کریپتو

### CoinGlass
- ✓ **رایگان**: بدون API Key
- 📍 **Rate Limit**: 50 درخواست/دقیقه
- 🔗 URL: `https://api.coinglass.com`
- ℹ️ **توضیح**: بهترین برای Futures و Liquidations

### Alpha Vantage
- ✓ **رایگان**: 5 درخواست/دقیقه
- ⚠️ **محدودیت**: فقط 5 درخواست/دقیقه (بسیار محدود)
- 📍 **API Key**: `demo` (رایگان) یا ثبت‌نام برای بیشتر
- 🔗 URL: `https://www.alphavantage.co`
- 🔑 **ثبت‌نام**: https://www.alphavantage.co/

### FRED (Federal Reserve)
- ✓ **رایگان**: بدون محدودیت
- 📍 **API Key**: `demo` (رایگان) یا ثبت‌نام برای API Key اختصاصی
- 🔗 URL: `https://api.stlouisfed.org/fred`
- 🔑 **ثبت‌نام**: https://fredaccount.stlouisfed.org/login/secure/

---

## 🚀 نحوه راه‌اندازی

### 1. نصب بسته‌های مورد نیاز
```bash
pip install requests pandas numpy
```

### 2. دریافت API Keys رایگان (اختیاری)
```python
# Alpha Vantage
# ثبت‌نام در: https://www.alphavantage.co/
# API Key را کپی کنید

# FRED
# ثبت‌نام در: https://fredaccount.stlouisfed.org/login/secure/
# API Key را کپی کنید
```

### 3. جایگزین کردن API Keys در کد
```python
# کد اصلی
self.alpha_vantage_key = "YOUR_API_KEY"  # API Key خود
self.fred_key = "YOUR_API_KEY"  # API Key خود
```

### 4. اجرا
```bash
python collector.py
```

### 5. خروجی
- `crypto_data_365d.csv` - فایل CSV
- `crypto_data_365d.json` - فایل JSON

---

## 📊 تعداد کل داده‌های جمع‌آوری‌شده

| گروه | تعداد | منبع |
|------|------|------|
| **قیمت و حجم** | 6 | CoinGecko |
| **دمینانس** | 4 | CoinGecko |
| **Futures** | 4 | CoinGlass |
| **محاسبه‌شده** | 8 | Custom |
| **Macro (Alpha)** | 3 | Alpha Vantage |
| **Macro (FRED)** | 2 | FRED |
| **خاص** | 2 | Custom |
| **غیرممکن** | 4 | - |
| **جمع کل** | **33** | - |

---

## 💡 نکات مهم

### اگر بخواهید داده‌های دقیق‌تر:

| داده | سناریو | هزینه |
|-----|--------|------|
| `whale_netflow_24h` | تحلیل حرکات وال | $99/ماه |
| `active_addresses_btc` | تحلیل on-chain | $199/ماه |
| بهتر `alpha_vantage` | بیشتر از 5/دقیقه | $20/ماه |
| بهتر `sp500` | داده‌های دقیق | Polygon/Alpaca |

### Rate Limiting
- **CoinGecko**: 10-50/دقیقه (رایگان)
- **CoinGlass**: 50/دقیقه (رایگان)
- **Alpha Vantage**: 5/دقیقه (رایگان)
- **FRED**: بدون محدودیت

### تاخیر توصیه‌شده
```python
time.sleep(1)  # 1 ثانیه بین درخواست‌ها
```

---

## 🎯 استراتژی بهترین استفاده

### برای تحلیل تکنیکال
✓ استفاده از: `btc_price`, `weekly_return`, `momentum_index`

### برای تحلیل احساسات
✓ استفاده از: `funding_rate_btc`, `liquidations`, `open_interest`

### برای تحلیل Macro
✓ استفاده از: `sp500`, `dxy`, `vix_index`, `us_10y_yield`

### برای تحلیل کریپتو
✓ استفاده از: `btc_dominance`, `altcoin_dominance`, `market_breadth`

### برای شناسایی فرصت‌ها
✓ استفاده از: `btc_eth_correlation`, `liquidity_score`, `new_highs/lows`

---

## 📞 حل مشکلات

### مشکل: API محدود است
```
⚠️ حل: API Key خود را دریافت کنید (رایگان)
```

### مشکل: Rate Limit شده‌اید
```
⚠️ حل: تاخیر بیشتری بگذارید (2-3 ثانیه)
```

### مشکل: داده‌ها ناقص هستند
```
⚠️ حل: منتظر بمانید تا API جواب دهد
```

### مشکل: هیچ داده دریافت نشد
```
⚠️ حل: اتصال اینترنت را بررسی کنید
```