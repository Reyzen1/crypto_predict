# File: scripts/sync-db/create_sync_migration.py
# Create migration to sync database with current models

import subprocess
import sys
import os
from pathlib import Path

def create_sync_migration():
    """
    Create a migration to sync database with current models
    """
    print("🔄 Creating sync migration...")
    
    # Get project root directory (2 levels up from this script)
    project_root = Path(__file__).parent.parent.parent
    backend_dir = project_root / "backend"
    original_dir = Path.cwd()
    
    if not backend_dir.exists():
        print(f"❌ Backend directory not found: {backend_dir}")
        return False
    
    try:
        os.chdir(backend_dir)
        
        # Create migration
        print("📝 Generating migration...")
        result = subprocess.run([
            "alembic", "revision", "--autogenerate", 
            "-m", "sync_database_with_models"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migration created successfully!")
            print("📋 Migration output:")
            print(result.stdout)
            
            # Apply migration
            print("🚀 Applying migration...")
            apply_result = subprocess.run([
                "alembic", "upgrade", "head"
            ], capture_output=True, text=True)
            
            if apply_result.returncode == 0:
                print("✅ Migration applied successfully!")
                return True
            else:
                print(f"❌ Failed to apply migration: {apply_result.stderr}")
                return False
        else:
            print(f"❌ Failed to create migration: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        os.chdir(original_dir)

def create_seed_data_script():
    """
    Create script to add essential seed data
    """
    print("📝 Creating seed data script...")
    
    # Ensure directory exists
    script_dir = Path(__file__).parent
    script_dir.mkdir(parents=True, exist_ok=True)
    
    seed_script = '''# File: scripts/sync-db/seed_data.py
# Add essential seed data to database

import sys
from pathlib import Path

# Add backend to path (3 levels up from this script)
project_root = Path(__file__).parent.parent.parent
backend_dir = project_root / "backend"
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.models.core.user import User
from app.models.core.crypto import Cryptocurrency
from passlib.context import CryptContext

def create_seed_data():
    """Create essential seed data for the application"""
    print("🌱 Creating seed data...")
    
    try:
        settings = get_settings()
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        db = SessionLocal()
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Create test user if not exists
        test_user = db.query(User).filter(User.email == "test@cryptopredict.com").first()
        if not test_user:
            test_user = User(
                email="test@cryptopredict.com",
                password_hash=pwd_context.hash("test_password"),
                first_name="Test",
                last_name="User",
                is_active=True,
                is_verified=True,
                is_superuser=False
            )
            db.add(test_user)
            print("✅ Test user created")
        else:
            print("✅ Test user already exists")
        
        # Create Bitcoin if not exists
        btc_crypto = db.query(Cryptocurrency).filter(Cryptocurrency.symbol == "BTC").first()
        if not btc_crypto:
            btc_crypto = Cryptocurrency(
                symbol="BTC",
                name="Bitcoin",
                coingecko_id="bitcoin",
                is_active=True,
                is_supported=True
            )
            db.add(btc_crypto)
            print("✅ Bitcoin cryptocurrency created")
        else:
            print("✅ Bitcoin cryptocurrency already exists")
        
        # Create Ethereum if not exists
        eth_crypto = db.query(Cryptocurrency).filter(Cryptocurrency.symbol == "ETH").first()
        if not eth_crypto:
            eth_crypto = Cryptocurrency(
                symbol="ETH",
                name="Ethereum",
                coingecko_id="ethereum",
                is_active=True,
                is_supported=True
            )
            db.add(eth_crypto)
            print("✅ Ethereum cryptocurrency created")
        else:
            print("✅ Ethereum cryptocurrency already exists")
        
        db.commit()
        print("🎉 Seed data created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating seed data: {e}")
        if 'db' in locals():
            db.rollback()
        return False
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    create_seed_data()
'''
    
    seed_file = script_dir / "seed_data.py"
    with open(seed_file, "w", encoding="utf-8") as f:
        f.write(seed_script)
    
    print(f"✅ Seed data script created: {seed_file}")

if __name__ == "__main__":
    print("🚀 Database Sync Tool")
    print("=" * 30)
    
    # Create sync migration
    if create_sync_migration():
        print("\n📝 Creating seed data script...")
        create_seed_data_script()
        
        print("\n" + "=" * 50)
        print("✅ SYNC COMPLETED!")
        print("=" * 50)
        print("📋 What was done:")
        print("   1. ✅ Migration created and applied")
        print("   2. ✅ Database synced with models")
        print("   3. ✅ Seed data script created")
        print("\n💡 For future setups:")
        print("   Run: python scripts/sync-db/seed_data.py")
        print("   This will create test user and basic data")
        
    else:
        print("\n❌ Sync failed! Manual intervention needed.")