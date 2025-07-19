#!/bin/bash
# بررسی وضعیت فعلی پروژه و database

echo "🔍 بررسی وضعیت فعلی پروژه CryptoPredict"
echo "============================================"

# بررسی اینکه آیا در مسیر درست هستیم
if [ ! -d "backend" ]; then
    echo "❌ شما در مسیر اصلی پروژه نیستید!"
    echo "لطفا به مسیر cryptopredict-mvp برید"
    exit 1
fi

echo "✅ در مسیر درست هستیم"

# بررسی services که در حال اجرا هستند
echo ""
echo "📊 بررسی سرویس‌های در حال اجرا:"
echo "--------------------------------"

# بررسی PostgreSQL
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend (FastAPI) در حال اجرا است - http://localhost:8000"
else
    echo "❌ Backend در حال اجرا نیست"
fi

if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend (Next.js) در حال اجرا است - http://localhost:3000"
else
    echo "❌ Frontend در حال اجرا نیست"
fi

# بررسی database connection
echo ""
echo "🗄️ بررسی اتصال database:"
echo "--------------------------"
cd backend

# فعال کردن محیط مجازی
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "❌ محیط مجازی Python پیدا نشد!"
    exit 1
fi

# تست اتصال database
python -c "
import psycopg2
import sys

try:
    # تست اتصال به دیتابیس
    conn = psycopg2.connect('postgresql://postgres:postgres123@localhost:5432/cryptopredict')
    print('✅ اتصال به database cryptopredict موفق است')
    
    cursor = conn.cursor()
    
    # بررسی جداول موجود
    cursor.execute('''
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    ''')
    
    tables = cursor.fetchall()
    
    if tables:
        print('📋 جداول موجود در database:')
        for table in tables:
            print(f'   - {table[0]}')
    else:
        print('⚠️ هیچ جدولی در database موجود نیست')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'❌ خطا در اتصال به database: {e}')
    print('💡 احتمالا PostgreSQL در حال اجرا نیست یا database ایجاد نشده')
    sys.exit(1)
"

echo ""
echo "📁 بررسی فایل‌های مهم:"
echo "----------------------"

# بررسی فایل‌های کلیدی
if [ -f "app/models/__init__.py" ]; then
    echo "✅ Models file موجود است"
else
    echo "❌ Models file موجود نیست"
fi

if [ -f "app/core/database.py" ]; then
    echo "✅ Database configuration موجود است"
else
    echo "❌ Database configuration موجود نیست"
fi

if [ -f "app/core/config.py" ]; then
    echo "✅ App configuration موجود است"
else
    echo "❌ App configuration موجود نیست"
fi

cd ..

echo ""
echo "🎯 خلاصه وضعیت:"
echo "---------------"
echo "اگر همه چیز سبز باشد، آماده ادامه روز ۳ هستیم"
echo "اگر چیزهایی قرمز باشند، باید ابتدا آن‌ها را درست کنیم"