# File: scripts/seed-cryptocurrencies.py
# Seed cryptocurrencies table with initial data

import sys
import os
from pathlib import Path
from datetime import datetime

# Add backend to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

def seed_cryptocurrencies():
    """Seed cryptocurrencies table with initial data"""
    
    try:
        from app.core.database import SessionLocal, engine, Base
        from app.models import Cryptocurrency
        from sqlalchemy.orm import Session
        from sqlalchemy import text
        
        print("🌱 Cryptocurrency Seeder")
        print("========================")
        
        # Create session
        db: Session = SessionLocal()
        
        try:
            # Test database connection
            db.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            
            # Check if cryptocurrencies table exists
            result = db.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'cryptocurrencies'
                );
            """))
            
            table_exists = result.scalar()
            
            if not table_exists:
                print("⚠️  Cryptocurrencies table not found, creating tables...")
                Base.metadata.create_all(bind=engine)
                print("✅ Tables created")
            
            # Check existing cryptocurrencies
            existing_cryptos = db.query(Cryptocurrency).all()
            print(f"📊 Found {len(existing_cryptos)} existing cryptocurrencies")
            
            if existing_cryptos:
                print("Existing cryptocurrencies:")
                for crypto in existing_cryptos:
                    print(f"   • {crypto.symbol}: {crypto.name} (ID: {crypto.id})")
            
            # Define initial cryptocurrency data
            initial_cryptos = [
                {
                    "symbol": "BTC",
                    "name": "Bitcoin",
                    "coingecko_id": "bitcoin",
                    "is_active": True
                },
                {
                    "symbol": "ETH", 
                    "name": "Ethereum",
                    "coingecko_id": "ethereum",
                    "is_active": True
                },
                {
                    "symbol": "ADA",
                    "name": "Cardano", 
                    "coingecko_id": "cardano",
                    "is_active": False  # Not active by default
                },
                {
                    "symbol": "DOT",
                    "name": "Polkadot",
                    "coingecko_id": "polkadot", 
                    "is_active": False  # Not active by default
                },
                {
                    "symbol": "SOL",
                    "name": "Solana",
                    "coingecko_id": "solana",
                    "is_active": False  # Not active by default
                }
            ]
            
            # Add cryptocurrencies
            added_count = 0
            updated_count = 0
            
            for crypto_data in initial_cryptos:
                symbol = crypto_data["symbol"]
                
                # Check if cryptocurrency already exists
                existing_crypto = db.query(Cryptocurrency).filter(
                    Cryptocurrency.symbol == symbol
                ).first()
                
                if existing_crypto:
                    # Update existing cryptocurrency
                    existing_crypto.name = crypto_data["name"]
                    if hasattr(existing_crypto, 'coingecko_id'):
                        existing_crypto.coingecko_id = crypto_data.get("coingecko_id")
                    if hasattr(existing_crypto, 'is_active'):
                        existing_crypto.is_active = crypto_data.get("is_active", True)
                    existing_crypto.updated_at = datetime.utcnow()
                    
                    updated_count += 1
                    print(f"📝 Updated: {symbol} - {crypto_data['name']}")
                else:
                    # Create new cryptocurrency
                    new_crypto = Cryptocurrency(
                        symbol=symbol,
                        name=crypto_data["name"],
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    
                    # Add optional fields if they exist in the model
                    if hasattr(Cryptocurrency, 'coingecko_id'):
                        new_crypto.coingecko_id = crypto_data.get("coingecko_id")
                    if hasattr(Cryptocurrency, 'is_active'):
                        new_crypto.is_active = crypto_data.get("is_active", True)
                    
                    db.add(new_crypto)
                    added_count += 1
                    print(f"➕ Added: {symbol} - {crypto_data['name']}")
            
            # Commit changes
            db.commit()
            
            # Verify data
            all_cryptos = db.query(Cryptocurrency).all()
            
            print(f"\n📊 Seeding Summary:")
            print(f"   • Added: {added_count} cryptocurrencies")
            print(f"   • Updated: {updated_count} cryptocurrencies") 
            print(f"   • Total: {len(all_cryptos)} cryptocurrencies")
            
            print(f"\n✅ Current Cryptocurrencies:")
            for crypto in all_cryptos:
                status = "🟢 Active" if getattr(crypto, 'is_active', True) else "🔴 Inactive"
                coingecko_id = getattr(crypto, 'coingecko_id', 'N/A')
                print(f"   • {crypto.symbol}: {crypto.name} ({status}) - CoinGecko: {coingecko_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ Database operation failed: {e}")
            db.rollback()
            return False
            
        finally:
            db.close()
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("Make sure you're running from the project root directory")
        print("and the backend virtual environment is activated")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_cryptocurrency_model():
    """Check the structure of Cryptocurrency model"""
    
    try:
        from app.models import Cryptocurrency
        from sqlalchemy import inspect
        
        print("\n🔍 Cryptocurrency Model Analysis:")
        print("==================================")
        
        # Get model attributes
        model_attrs = dir(Cryptocurrency)
        db_columns = [attr for attr in model_attrs if not attr.startswith('_') and not callable(getattr(Cryptocurrency, attr))]
        
        print("Database columns:")
        for col in db_columns:
            print(f"   • {col}")
        
        # Check specific important columns
        important_cols = ['symbol', 'name', 'coingecko_id', 'is_active', 'created_at', 'updated_at']
        
        print("\nColumn availability:")
        for col in important_cols:
            exists = hasattr(Cryptocurrency, col)
            status = "✅ Available" if exists else "❌ Missing"
            print(f"   • {col}: {status}")
            
        return True
        
    except Exception as e:
        print(f"❌ Model analysis failed: {e}")
        return False

def main():
    """Main function"""
    
    print("🌱 CryptoPredict Cryptocurrency Seeder")
    print("======================================")
    
    # Check if we're in the right directory
    if not os.path.exists("backend/app/models"):
        print("❌ Please run this script from the project root directory")
        print("Expected structure: backend/app/models/")
        return
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        if os.path.exists('.env'):
            load_dotenv()
            print("✅ Environment variables loaded")
    except ImportError:
        print("⚠️  python-dotenv not available, using system environment")
    
    # Check model structure
    if not check_cryptocurrency_model():
        return
    
    # Seed cryptocurrencies
    if seed_cryptocurrencies():
        print("\n🎉 Seeding completed successfully!")
        print("\nNext steps:")
        print("1. Start the backend: ./start-backend-local.sh")
        print("2. Test API: http://localhost:8000/docs")
        print("3. Check cryptocurrencies: GET /api/v1/crypto/list")
    else:
        print("\n❌ Seeding failed!")
        print("\nTroubleshooting:")
        print("1. Ensure PostgreSQL is running")
        print("2. Check database connection in .env")
        print("3. Verify virtual environment is activated")
        print("4. Run from project root directory")

if __name__ == "__main__":
    main()