# File: temp/create_test_user.py
# Fixed script to create a test user for API testing

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

def create_test_user_simple():
    """Create a test user using direct database approach"""
    print("🔧 Creating Test User for API Testing")
    print("=" * 40)
    
    try:
        from app.core.database import SessionLocal
        from app.models import User
        from passlib.context import CryptContext
        
        # Create database session
        db = SessionLocal()
        
        # Test user data
        test_email = "test@example.com"
        test_password = "testpassword123"
        test_name = "Test User"
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == test_email).first()
        
        if existing_user:
            print(f"✅ Test user already exists: {test_email}")
            print(f"   User ID: {existing_user.id}")
            print(f"   Email: {existing_user.email}")
            print(f"   Active: {existing_user.is_active}")
            
            # Test password verification
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            password_valid = pwd_context.verify(test_password, existing_user.password_hash)
            
            if password_valid:
                print(f"✅ Password verification works")
            else:
                print(f"⚠️ Password might be different")
                
            db.close()
            return True
        
        # Create password hash
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        password_hash = pwd_context.hash(test_password)
        
        # Create new user directly
        new_user = User(
            email=test_email,
            password_hash=password_hash,
            first_name="Test",
            last_name="User",
            is_active=True,
            is_verified=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"✅ Test user created successfully!")
        print(f"   Email: {new_user.email}")
        print(f"   ID: {new_user.id}")
        print(f"   Name: {new_user.first_name} {new_user.last_name}")
        
        # Test password verification
        password_valid = pwd_context.verify(test_password, new_user.password_hash)
        
        if password_valid:
            print(f"✅ Password verification works")
        else:
            print(f"❌ Password verification failed")
            db.close()
            return False
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to create test user: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_cryptocurrency_data():
    """Check if BTC exists in database and create if needed"""
    print("\n📋 Checking Cryptocurrency Data...")
    
    try:
        from app.core.database import SessionLocal
        from app.models import Cryptocurrency
        
        db = SessionLocal()
        
        # Check if BTC exists
        btc_crypto = db.query(Cryptocurrency).filter(Cryptocurrency.symbol == "BTC").first()
        
        if btc_crypto:
            print(f"✅ BTC cryptocurrency exists: {btc_crypto.name}")
            print(f"   ID: {btc_crypto.id}")
            print(f"   Symbol: {btc_crypto.symbol}")
        else:
            print("⚠️ BTC cryptocurrency not found")
            print("💡 Creating BTC entry...")
            
            # Create BTC entry
            btc_crypto = Cryptocurrency(
                symbol="BTC",
                name="Bitcoin",
                coingecko_id="bitcoin",
                is_active=True
            )
            
            db.add(btc_crypto)
            db.commit()
            db.refresh(btc_crypto)
            
            print(f"✅ BTC cryptocurrency created!")
            print(f"   ID: {btc_crypto.id}")
            print(f"   Symbol: {btc_crypto.symbol}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to check cryptocurrency data: {str(e)}")
        return False

def check_database_connection():
    """Check if database connection is working"""
    try:
        from app.core.database import engine
        from sqlalchemy import text
        
        # Test connection with proper text() wrapper
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
            
        print("✅ Database connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

def check_imports():
    """Check if required imports work"""
    try:
        # Test basic imports
        from app.core.database import SessionLocal, engine
        from app.models import User, Cryptocurrency
        from passlib.context import CryptContext
        
        print("✅ Required imports successful")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {str(e)}")
        print("💡 Make sure you're in the right directory and backend is properly set up")
        return False

def check_database_tables():
    """Check if required tables exist"""
    try:
        from app.core.database import engine
        from sqlalchemy import inspect
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        required_tables = ['users', 'cryptocurrencies']
        missing_tables = []
        
        for table in required_tables:
            if table in tables:
                print(f"✅ Table '{table}' exists")
            else:
                missing_tables.append(table)
                print(f"❌ Table '{table}' missing")
        
        if missing_tables:
            print(f"\n💡 Missing tables: {missing_tables}")
            print("   Run database migrations or create tables")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to check tables: {str(e)}")
        return False

def main():
    """Main function to set up test environment"""
    print("🔧 API Test Environment Setup - Fixed Version")
    print("=" * 50)
    
    # Check imports
    print("\n📋 Checking Imports...")
    if not check_imports():
        print("💡 Make sure backend dependencies are installed")
        return
    
    # Check database connection
    print("\n📋 Checking Database Connection...")
    if not check_database_connection():
        print("💡 Make sure PostgreSQL is running and database exists")
        return
    
    # Check database tables
    print("\n📋 Checking Database Tables...")
    if not check_database_tables():
        print("💡 Make sure database tables are created")
        return
    
    # Create test user
    print("\n📋 Creating Test User...")
    if not create_test_user_simple():
        print("💡 Check the errors above and fix them")
        return
    
    # Check cryptocurrency data
    if not check_cryptocurrency_data():
        print("💡 Cryptocurrency data check failed")
        return
    
    print("\n🎉 Test environment setup complete!")
    print("\nYou can now run:")
    print("  python temp/test_ml_training_api_fixed.py")
    print("\nTest credentials:")
    print("  Email: test@example.com")
    print("  Password: testpassword123")
    print("\nAvailable data:")
    print("  • Test user account")
    print("  • BTC cryptocurrency entry")

if __name__ == "__main__":
    main()