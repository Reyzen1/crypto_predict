#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
from pathlib import Path

def display_file_structure(python_files, base_path):
    """
    نمایش ساختار فایل‌های پیدا شده
    
    Args:
        python_files (list): لیست مسیر فایل‌های پایتون
        base_path (str): مسیر پایه
    """
    
    print("\n📋 فایل‌های پیدا شده:")
    print("-" * 40)
    
    # گروه‌بندی فایل‌ها بر اساس پوشه
    folders = {}
    for file_path in python_files:
        folder = os.path.dirname(file_path)
        relative_folder = os.path.relpath(folder, start=".")
        file_name = os.path.basename(file_path)
        
        if relative_folder not in folders:
            folders[relative_folder] = []
        folders[relative_folder].append(file_name)
    
    # نمایش ساختار
    for folder in sorted(folders.keys()):
        print(f"📁 {folder}/")
        for file_name in sorted(folders[folder]):
            print(f"   📄 {file_name}")
        print()

def add_comments_to_model_files(models_path="backend/app/models/"):
    """
    اضافه کردن توضیحات به ابتدای فایل‌های پایتون در مسیر models و تمام زیرپوشه‌ها
    
    Args:
        models_path (str): مسیر پوشه models
    """
    
    # بررسی وجود مسیر
    if not os.path.exists(models_path):
        print(f"❌ مسیر {models_path} وجود ندارد!")
        return
    
    # پیدا کردن تمام فایل‌های پایتون در تمام زیرپوشه‌ها
    python_files = []
    for root, dirs, files in os.walk(models_path):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    if not python_files:
        print(f"❌ هیچ فایل پایتونی در مسیر {models_path} و زیرپوشه‌هایش پیدا نشد!")
        return
    
    print(f"📁 {len(python_files)} فایل پایتون پیدا شد:")
    
    # نمایش ساختار پوشه‌ها
    display_file_structure(python_files, models_path)
    
    for file_path in python_files:
        process_file(file_path, models_path)
    
    print("\n✅ تمام فایل‌ها با موفقیت پردازش شدند!")

def process_file(file_path, base_path):
    """
    پردازش یک فایل و اضافه کردن توضیحات
    
    Args:
        file_path (str): مسیر کامل فایل
        base_path (str): مسیر پایه برای محاسبه مسیر نسبی
    """
    
    file_name = os.path.basename(file_path)
    
    print(f"\n🔍 در حال پردازش: {file_name}")
    print(f"   مسیر کامل: {file_path}")
    
    # خواندن محتوای فایل با encodingهای مختلف
    content = None
    for encoding in ['utf-8', 'cp1256', 'latin-1']:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            print(f"   ✅ فایل با encoding {encoding} خوانده شد")
            break
        except Exception as e:
            print(f"   ⚠️  خطا با encoding {encoding}: {e}")
            continue
    
    if content is None:
        print(f"❌ نمی‌توان فایل {file_name} را خواند")
        return
    
    print(f"   📄 طول محتوای فایل: {len(content)} کاراکتر")
    print(f"   🔤 اولین 100 کاراکتر: {repr(content[:100])}")
    
    # محاسبه مسیر نسبی
    relative_path = os.path.relpath(file_path, start=".")
    
    # ایجاد توضیحات
    comment_block = f"# File: {relative_path}\n# SQLAlchemy model for {get_model_description(file_name)}\n\n"
    
    print(f"   💭 توضیحات تولید شده:")
    print(f"      {comment_block.strip()}")
    
    # بررسی اینکه آیا توضیحات قبلاً اضافه شده‌اند یا نه
    if content.startswith("# File:"):
        print(f"⏭️  {file_name} - توضیحات قبلاً اضافه شده")
        return
    
    # بررسی اینکه آیا فایل خالی است یا نه
    if not content.strip():
        print(f"⚠️  {file_name} - فایل خالی است")
        new_content = comment_block
    else:
        # اضافه کردن توضیحات به ابتدای فایل
        new_content = comment_block + content
    
    print(f"   📝 طول محتوای جدید: {len(new_content)} کاراکتر")
    
    # نوشتن محتوای جدید
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ {file_name} - توضیحات با موفقیت اضافه شد")
        
        # تأیید نوشتن
        with open(file_path, 'r', encoding='utf-8') as f:
            verification_content = f.read()
        
        if verification_content.startswith("# File:"):
            print(f"   ✅ تأیید: توضیحات درست اضافه شده")
        else:
            print(f"   ❌ خطا: توضیحات اضافه نشده!")
            
    except Exception as e:
        print(f"❌ خطا در نوشتن فایل {file_path}: {e}")
        print(f"   نوع خطا: {type(e).__name__}")
        print(f"   جزئیات: {str(e)}")

def get_model_description(file_name):
    """
    تولید توضیح مناسب برای مدل بر اساس نام فایل
    
    Args:
        file_name (str): نام فایل
        
    Returns:
        str: توضیح مدل
    """
    
    # حذف پسوند .py
    model_name = file_name.replace('.py', '')
    
    # اگر فایل __init__.py باشد، توضیح خاص
    if model_name == '__init__':
        return 'module initialization'
    
    # تبدیل underscore به space و اضافه کردن data
    description = model_name.replace('_', ' ') + ' data'
    
    return description

def create_backup(models_path="backend/app/models/"):
    """
    ایجاد نسخه پشتیبان از فایل‌ها قبل از تغییر (شامل تمام زیرپوشه‌ها)
    
    Args:
        models_path (str): مسیر پوشه models
    """
    
    backup_path = f"{models_path.rstrip('/')}_backup"
    
    try:
        import shutil
        if os.path.exists(backup_path):
            shutil.rmtree(backup_path)
        shutil.copytree(models_path, backup_path)
        print(f"💾 نسخه پشتیبان در {backup_path} ایجاد شد (شامل تمام زیرپوشه‌ها)")
        return True
    except Exception as e:
        print(f"❌ خطا در ایجاد نسخه پشتیبان: {e}")
        return False

def main():
    """
    تابع اصلی اسکریپت
    """
    
    print("🚀 شروع پردازش فایل‌های مدل SQLAlchemy")
    print("=" * 50)
    
    models_path = "backend/app/models/"
    
    # سؤال از کاربر برای ایجاد نسخه پشتیبان
    backup_choice = input(f"آیا می‌خواهید نسخه پشتیبان از {models_path} ایجاد کنید؟ (y/n): ").lower()
    
    if backup_choice in ['y', 'yes', 'بله']:
        if not create_backup(models_path):
            continue_choice = input("آیا می‌خواهید بدون پشتیبان ادامه دهید؟ (y/n): ").lower()
            if continue_choice not in ['y', 'yes', 'بله']:
                print("❌ عملیات لغو شد")
                return
    
    # پردازش فایل‌ها
    add_comments_to_model_files(models_path)
    
    print("\n" + "=" * 50)
    print("🎉 پردازش کامل شد!")

if __name__ == "__main__":
    main()