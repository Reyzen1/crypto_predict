# Database Deployment Guide
## چگونه پروژه را روی سیستم دیگری راه‌اندازی کنم؟

## 🎯 **روش‌های مختلف برای سیستم جدید:**

### **1. 📋 روش Clean Setup (پیشنهادی برای سیستم جدید)**

```bash
# کلون کردن پروژه
git clone <repository-url>
cd crypto_predict

# تنظیم virtual environment
cd backend
python -m venv venv

# فعال کردن virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# نصب dependencies
pip install -r requirements.txt

# کپی کردن environment variables
cp .env.example .env
# ویرایش .env و تنظیم DATABASE_URL برای سیستم جدید

# ایجاد database جدید
createdb cryptopredict

# اجرای migrations
alembic upgrade head

# تست
python -c "from app.models import *; print('✅ Models loaded')"
```

---

### **2. 🔄 روش Migration-Based (برای update کردن سیستم موجود)**

```bash
# Pull کردن آخرین تغییرات
git pull origin main

# فعال کردن virtual environment
source venv/bin/activate  # Linux/Mac
# یا venv\Scripts\activate  # Windows

# بروزرسانی dependencies
pip install -r requirements.txt

# اعمال migrations جدید
alembic upgrade head

# چک کردن وضعیت
alembic current
```

---

### **3. 🗄️ روش Database Dump (برای انتقال داده‌ها)**

```bash
# در سیستم اصلی (export)
pg_dump -h localhost -U postgres -d cryptopredict > cryptopredict_backup.sql

# در سیستم جدید (import)
createdb cryptopredict
psql -h localhost -U postgres -d cryptopredict < cryptopredict_backup.sql
```

---

## 📋 **مراحل تفصیلی برای سیستم جدید:**

### **Step 1: Setup Environment**
```bash
# 1. کلون پروژه
git clone <your-repo-url>
cd crypto_predict

# 2. ایجاد Python environment
cd backend
python -m venv venv

# 3. فعال کردن environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. نصب dependencies
pip install -r requirements.txt
```

### **Step 2: Database Setup**
```bash
# 1. ایجاد .env file
cp .env.example .env

# 2. ویرایش .env file
nano .env  # یا editor دلخواه
# تنظیم:
# DATABASE_URL=postgresql://username:password@localhost:5432/cryptopredict
# REDIS_URL=redis://localhost:6379/0

# 3. ایجاد database
createdb cryptopredict
# یا از pgAdmin

# 4. اجرای migrations
alembic upgrade head
```

### **Step 3: Verification**
```bash
# 1. چک migration status
alembic current

# 2. تست database connection
python -c "
from app.core.database import engine
from app.models import *
print('✅ Database connection successful')
print('✅ All models loaded')
"

# 3. تست application
python -c "
import sys
sys.path.append('.')
from app.main import app
print('✅ FastAPI app loads successfully')
"
```

---

## 🏢 **برای Team Development:**

### **الف) Developer جدید:**
```bash
# 1. Clone repository
git clone <repo>
cd crypto_predict/backend

# 2. Setup environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Setup database
cp .env.example .env
# Edit DATABASE_URL to point to local database

# 4. Initialize database
createdb cryptopredict_dev
alembic upgrade head
```

### **ب) Update کردن environment موجود:**
```bash
# 1. Pull latest changes
git pull origin main

# 2. Update dependencies
pip install -r requirements.txt

# 3. Apply new migrations
alembic upgrade head

# 4. Check status
alembic current
```

---

## 🐳 **استفاده از Docker (آسان‌ترین روش):**

### **ایجاد docker-compose.yml:**
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/cryptopredict
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./backend:/app

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=cryptopredict
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### **راه‌اندازی با Docker:**
```bash
# در سیستم جدید:
git clone <repo>
cd crypto_predict

# راه‌اندازی کل stack
docker-compose up --build

# اجرای migrations
docker-compose exec backend alembic upgrade head
```

---

## ⚠️ **نکات مهم:**

### **1. Environment Variables:**
```bash
# هیچ‌وقت .env file را commit نکنید!
# همیشه .env.example بروزرسانی کنید
# در هر سیستم .env جداگانه داشته باشید
```

### **2. Database URLs:**
```bash
# Development:
DATABASE_URL=postgresql://user:pass@localhost:5432/cryptopredict_dev

# Production:
DATABASE_URL=postgresql://user:pass@production-server:5432/cryptopredict

# Docker:
DATABASE_URL=postgresql://postgres:postgres@db:5432/cryptopredict
```

### **3. Migration Best Practices:**
```bash
# همیشه backup بگیرید قبل از migration
pg_dump cryptopredict > backup_$(date +%Y%m%d).sql

# Migration را ابتدا روی staging test کنید
alembic upgrade head --sql  # نمایش SQL بدون اجرا

# در صورت مشکل، rollback کنید
alembic downgrade -1
```

---

## 🚀 **خلاصه پیشنهادات:**

### **برای سیستم جدید شخصی:**
1. ✅ **Git clone + Clean setup**
2. ✅ **Virtual environment جدید**
3. ✅ **Local database جدید**
4. ✅ **alembic upgrade head**

### **برای Production/Server:**
1. ✅ **Docker Compose** (آسان‌ترین)
2. ✅ **Automated deployment scripts**
3. ✅ **Database backup قبل از update**
4. ✅ **Staging environment برای test**

### **برای Team Collaboration:**
1. ✅ **Git-based workflow**
2. ✅ **Migration files در repository**
3. ✅ **Environment-specific .env files**
4. ✅ **Documentation کامل**