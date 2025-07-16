# CryptoPredict MVP - Quick Start Guide

## 🚀 سریع‌ترین راه راه‌اندازی

### پیش‌نیازها:
- Docker Desktop نصب و اجرا شده
- Python 3.12 (یا Python 3.x)
- Node.js و npm
- Git Bash (برای Windows)

### 📋 مراحل:

#### 1. راه‌اندازی اولیه (یکبار):
```bash
# اجازه اجرا به اسکریپت‌ها
chmod +x scripts/*.sh

# راه‌اندازی کامل
./scripts/quick-setup.sh
```

#### 2. شروع سرویس‌ها:

**Terminal 1 - Backend:**
```bash
./scripts/start-backend.sh
```

**Terminal 2 - Frontend:**
```bash
./scripts/start-frontend.sh
```

#### 3. دسترسی به برنامه:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

#### 4. متوقف کردن:
```bash
# متوقف کردن دیتابیس‌ها
./scripts/stop-db.sh

# Backend و Frontend با Ctrl+C متوقف می‌شوند
```

---

## 📁 فایل‌های مورد نیاز

این فایل‌ها را در پوشه `scripts/` ایجاد کنید:

### 1. `scripts/quick-setup.sh`
```bash
#!/bin/bash
# محتویات artifact بالا
```

### 2. `scripts/start-backend.sh`
```bash
#!/bin/bash
# محتویات artifact بالا
```

### 3. `scripts/start-frontend.sh`
```bash
#!/bin/bash
# محتویات artifact بالا
```

### 4. `scripts/stop-db.sh`
```bash
#!/bin/bash
# محتویات artifact بالا
```

### 5. `docker-compose-backend.yml`
```yaml
# محتویات artifact بالا (بدون خط version)
```

---

## 🔧 عیب‌یابی

### مشکل: اسکریپت اجرا نمی‌شود
```bash
chmod +x scripts/*.sh
```

### مشکل: Virtual Environment یافت نمی‌شود
```bash
cd backend
python -m venv venv
# یا
py -3.12 -m venv venv
```

### مشکل: Docker در دسترس نیست
```bash
# Docker Desktop را شروع کنید
docker info
```

### مشکل: نصب packages Python
```bash
cd backend
source venv/Scripts/activate
pip install --upgrade pip
pip install fastapi uvicorn sqlalchemy psycopg2-binary redis pydantic
```

---

## 🎯 بعد از راه‌اندازی موفق

شما آماده هستید برای:
- ✅ Backend API در http://localhost:8000
- ✅ Frontend در http://localhost:3000
- ✅ Database PostgreSQL و Redis
- ✅ ادامه توسعه طبق Phase 1

### گام بعدی:
- تنظیم SQLAlchemy و Alembic
- ایجاد مدل‌های دیتابیس
- تنظیم CORS و Security middleware

---

## 📞 کمک

اگر مشکلی داشتید:
1. اطمینان حاصل کنید که Docker اجرا شده است
2. Python 3.12 یا بالاتر نصب باشد
3. Node.js و npm نصب باشد
4. از Git Bash استفاده کنید (برای Windows)

### Reset کامل:
```bash
./scripts/stop-db.sh
docker system prune -f
./scripts/quick-setup.sh
```