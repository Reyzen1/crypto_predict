# File: temp/create_system_user.py
# اسکریپت ایجاد system user برای training

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

def create_system_user():
    """Create system user with ID=1 for training purposes"""
    
    try:
        from app.core.database import SessionLocal
        from app.models import User
        from passlib.context import CryptContext
        
        print("🔧 Creating System User...")
        print("=" * 30)
        
        # Create password context
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        db = SessionLocal()
        
        try:
            # Check if user ID=1 already exists
            existing_user = db.query(User).filter(User.id == 1).first()
            
            if existing_user:
                print(f"✅ System user already exists:")
                print(f"   ID: {existing_user.id}")
                print(f"   Email: {existing_user.email}")
                print(f"   Name: {existing_user.first_name} {existing_user.last_name}")
                return True
            
            # Create system user
            system_user = User(
                email="system@cryptopredict.local",
                password_hash=pwd_context.hash("SystemPass123!"),
                first_name="System",
                last_name="User",
                is_active=True,
                is_verified=True,
                is_superuser=False
            )
            
            db.add(system_user)
            db.commit()
            db.refresh(system_user)
            
            print(f"✅ System user created successfully:")
            print(f"   ID: {system_user.id}")
            print(f"   Email: {system_user.email}")
            print(f"   Name: {system_user.first_name} {system_user.last_name}")
            print(f"   Password: SystemPass123! (for testing only)")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Failed to create system user: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_and_create_btc():
    """Ensure BTC cryptocurrency exists"""
    
    try:
        from app.core.database import SessionLocal
        from app.models import Cryptocurrency
        
        print("\n🪙 Checking BTC Cryptocurrency...")
        print("=" * 35)
        
        db = SessionLocal()
        
        try:
            # Check if BTC exists
            btc_crypto = db.query(Cryptocurrency).filter(Cryptocurrency.symbol == "BTC").first()
            
            if btc_crypto:
                print(f"✅ BTC already exists:")
                print(f"   ID: {btc_crypto.id}")
                print(f"   Symbol: {btc_crypto.symbol}")
                print(f"   Name: {btc_crypto.name}")
                return True
            
            # Create BTC
            btc_crypto = Cryptocurrency(
                symbol="BTC",
                name="Bitcoin",
                coingecko_id="bitcoin",
                is_active=True
            )
            
            db.add(btc_crypto)
            db.commit()
            db.refresh(btc_crypto)
            
            print(f"✅ BTC created successfully:")
            print(f"   ID: {btc_crypto.id}")
            print(f"   Symbol: {btc_crypto.symbol}")
            print(f"   Name: {btc_crypto.name}")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Failed to create BTC: {str(e)}")
        return False

def main():
    """Main function"""
    
    print("🚀 System Setup Script")
    print("=" * 25)
    
    success1 = create_system_user()
    success2 = check_and_create_btc()
    
    if success1 and success2:
        print("\n🎉 Setup Complete!")
        print("✅ System user created (ID=1)")
        print("✅ BTC cryptocurrency ready")
        print("\n🚀 You can now run training without foreign key errors!")
        return True
    else:
        print("\n❌ Setup failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)