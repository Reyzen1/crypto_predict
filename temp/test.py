#!/usr/bin/env python3
"""
اسکریپت تست اتصال Redis
"""
import redis
import sys
import time

def test_redis_connection():
    """تست اتصال به Redis"""
    print("🔍 در حال تست اتصال به Redis...")
    
    try:
        # ایجاد اتصال به Redis
        r = redis.Redis(
            host='localhost', 
            port=6379, 
            db=0,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # تست ping
        response = r.ping()
        if response:
            print("✅ اتصال به Redis موفقیت‌آمیز بود!")
            
            # تست نوشتن و خواندن
            test_key = "test_connection"
            test_value = f"test_value_{int(time.time())}"
            
            r.set(test_key, test_value, ex=10)  # expire in 10 seconds
            retrieved_value = r.get(test_key)
            
            if retrieved_value and retrieved_value.decode() == test_value:
                print("✅ تست نوشتن/خواندن موفقیت‌آمیز بود!")
                
                # نمایش اطلاعات Redis
                info = r.info()
                print(f"📊 نسخه Redis: {info.get('redis_version', 'نامعلوم')}")
                print(f"📊 حافظه استفاده شده: {info.get('used_memory_human', 'نامعلوم')}")
                print(f"📊 تعداد کلیدها: {r.dbsize()}")
                
                return True
            else:
                print("❌ تست نوشتن/خواندن ناموفق بود!")
                return False
        else:
            print("❌ Redis پاسخ ping را نداد!")
            return False
            
    except redis.ConnectionError as e:
        print("❌ خطا در اتصال به Redis:")
        print(f"   {str(e)}")
        print("\n💡 راه‌حل‌های پیشنهادی:")
        print("   1. Redis سرور را راه‌اندازی کنید")
        print("   2. بررسی کنید که پورت 6379 آزاد باشد")
        print("   3. Firewall را بررسی کنید")
        return False
        
    except redis.TimeoutError as e:
        print("❌ Timeout در اتصال به Redis:")
        print(f"   {str(e)}")
        return False
        
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {str(e)}")
        return False

def check_redis_installation():
    """بررسی نصب Redis"""
    print("🔍 در حال بررسی نصب Redis...")
    
    import subprocess
    
    try:
        # تست redis-cli
        result = subprocess.run(['redis-cli', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ Redis CLI نصب شده: {result.stdout.strip()}")
            return True
        else:
            print("❌ Redis CLI یافت نشد")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Timeout در بررسی Redis CLI")
        return False
    except FileNotFoundError:
        print("❌ Redis CLI یافت نشد در PATH")
        return False
    except Exception as e:
        print(f"❌ خطا در بررسی Redis CLI: {str(e)}")
        return False

def check_redis_server():
    """بررسی اجرای Redis سرور"""
    print("🔍 در حال بررسی Redis سرور...")
    
    import socket
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5)
            result = sock.connect_ex(('localhost', 6379))
            if result == 0:
                print("✅ Redis سرور در پورت 6379 در حال اجرا است")
                return True
            else:
                print("❌ Redis سرور در پورت 6379 در حال اجرا نیست")
                return False
    except Exception as e:
        print(f"❌ خطا در بررسی Redis سرور: {str(e)}")
        return False

def main():
    """تابع اصلی"""
    print("🚀 شروع تست Redis")
    print("=" * 50)
    
    # بررسی نصب
    redis_installed = check_redis_installation()
    
    # بررسی سرور
    server_running = check_redis_server()
    
    # تست اتصال
    connection_ok = False
    if server_running:
        connection_ok = test_redis_connection()
    
    # خلاصه نتایج
    print("\n📋 خلاصه نتایج:")
    print(f"   Redis نصب شده: {'✅' if redis_installed else '❌'}")
    print(f"   Redis سرور اجرا: {'✅' if server_running else '❌'}")
    print(f"   اتصال موفق: {'✅' if connection_ok else '❌'}")
    
    if not server_running:
        print("\n💡 برای راه‌اندازی Redis:")
        print("   Windows: redis-server.exe")
        print("   Linux/Mac: redis-server")
        print("   Docker: docker run -d -p 6379:6379 redis:alpine")
    
    return connection_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)