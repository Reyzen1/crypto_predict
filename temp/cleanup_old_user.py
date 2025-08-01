# File: temp/cleanup_old_user.py
# حذف user قدیمی برای testing

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

def cleanup_test_user():
    """حذف test user قدیمی"""
    try:
        from app.core.database import SessionLocal
        from app.models import User
        
        db = SessionLocal()
        
        # پیدا کردن user قدیمی
        old_user = db.query(User).filter(User.email == "testuser2@example.com").first()
        
        if old_user:
            print(f"🗑️ Found old test user: {old_user.email}")
            db.delete(old_user)
            db.commit()
            print("✅ Old test user deleted successfully")
        else:
            print("✅ No old test user found")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error cleaning up user: {str(e)}")
        return False

def main():
    print("🧹 Cleanup Old Test User")
    print("=" * 30)
    
    success = cleanup_test_user()
    
    if success:
        print("\n✅ Cleanup completed. You can now use testuser2@example.com again.")
    else:
        print("\n❌ Cleanup failed. Use testuser2@example.com instead.")

if __name__ == "__main__":
    main()