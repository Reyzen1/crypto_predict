# File: scripts/sync-db/seed_data.py
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
from app.models.user import User
from app.models.cryptocurrency import Cryptocurrency
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
                market_cap_rank=1,
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
                market_cap_rank=2,
                is_active=True,
                is_supported=True
            )
            db.add(eth_crypto)
            print("✅ Ethereum cryptocurrency created")
        else:
            print("✅ Ethereum cryptocurrency already exists")
        
        # Create Binance Coin if not exists
        bnb_crypto = db.query(Cryptocurrency).filter(Cryptocurrency.symbol == "BNB").first()
        if not bnb_crypto:
            bnb_crypto = Cryptocurrency(
                symbol="BNB",
                name="Binance Coin",
                coingecko_id="binancecoin",
                market_cap_rank=3,
                is_active=True,
                is_supported=True
            )
            db.add(bnb_crypto)
            print("✅ Binance Coin cryptocurrency created")
        else:
            print("✅ Binance Coin cryptocurrency already exists")
        
        # Create admin user if not exists
        admin_user = db.query(User).filter(User.email == "admin@cryptopredict.com").first()
        if not admin_user:
            admin_user = User(
                email="admin@cryptopredict.com",
                password_hash=pwd_context.hash("admin_password"),
                first_name="Admin",
                last_name="User",
                is_active=True,
                is_verified=True,
                is_superuser=True
            )
            db.add(admin_user)
            print("✅ Admin user created")
        else:
            print("✅ Admin user already exists")
        
        db.commit()
        print("🎉 Seed data created successfully!")
        
        # Show summary
        user_count = db.query(User).count()
        crypto_count = db.query(Cryptocurrency).count()
        print(f"📊 Summary: {user_count} users, {crypto_count} cryptocurrencies")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating seed data: {e}")
        if 'db' in locals():
            db.rollback()
        return False
    finally:
        if 'db' in locals():
            db.close()

def check_seed_data():
    """Check if seed data exists"""
    print("🔍 Checking existing seed data...")
    
    try:
        settings = get_settings()
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        db = SessionLocal()
        
        # Check users
        user_count = db.query(User).count()
        print(f"👥 Users in database: {user_count}")
        
        users = db.query(User).all()
        for user in users:
            role = "Admin" if user.is_superuser else "User"
            status = "Active" if user.is_active else "Inactive"
            print(f"   - {user.email} ({role}, {status})")
        
        # Check cryptocurrencies
        crypto_count = db.query(Cryptocurrency).count()
        print(f"💰 Cryptocurrencies in database: {crypto_count}")
        
        cryptos = db.query(Cryptocurrency).all()
        for crypto in cryptos:
            status = "Active" if crypto.is_active else "Inactive"
            print(f"   - {crypto.symbol} ({crypto.name}, {status})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking seed data: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def main():
    """Main function with options"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage seed data for CryptoPredict')
    parser.add_argument('--check', action='store_true', help='Check existing seed data')
    parser.add_argument('--create', action='store_true', help='Create seed data')
    
    args = parser.parse_args()
    
    if args.check:
        check_seed_data()
    elif args.create:
        create_seed_data()
    else:
        # Default: create seed data
        print("🚀 CryptoPredict Seed Data Tool")
        print("=" * 40)
        
        # Check existing data first
        check_seed_data()
        print()
        
        # Create seed data
        create_seed_data()

if __name__ == "__main__":
    main()