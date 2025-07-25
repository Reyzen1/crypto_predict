# File: temp/database_reset.py
# Reset database and recreate from models

import sys
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.database import Base
from app.models.user import User
from app.models.cryptocurrency import Cryptocurrency
from app.models.prediction import Prediction
from passlib.context import CryptContext

def main():
    print("🔄 Database Reset & Recreate")
    print("=" * 30)
    
    try:
        # Create engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Drop all tables with CASCADE
        print("🗑️ Dropping all tables...")
        with engine.connect() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
            conn.commit()
        
        # Recreate all tables
        print("🏗️ Creating tables from models...")
        Base.metadata.create_all(bind=engine)
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Add seed data
        print("🌱 Adding seed data...")
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Create system user
        user = User(
            email="system@cryptopredict.local",
            hashed_password=pwd_context.hash("SystemPassword123!"),
            first_name="System",
            last_name="User",
            is_active=True,
            is_verified=True,
            is_superuser=True
        )
        db.add(user)
        
        # Create Bitcoin
        bitcoin = Cryptocurrency(
            symbol="BTC",
            name="Bitcoin",
            coingecko_id="bitcoin",
            is_active=True
        )
        db.add(bitcoin)
        
        db.commit()
        db.refresh(user)
        db.refresh(bitcoin)
        
        print(f"✅ Created user ID: {user.id}")
        print(f"✅ Created Bitcoin ID: {bitcoin.id}")
        
        # Test prediction
        test_prediction = Prediction(
            crypto_id=bitcoin.id,
            user_id=user.id,
            model_name="LSTM_test",
            model_version="1.0",
            predicted_price=Decimal("50000.00"),
            confidence_score=Decimal("0.85"),
            prediction_horizon=24,
            target_datetime=datetime.now(timezone.utc),
            input_price=Decimal("49000.00"),
            accuracy_threshold=Decimal("5.0"),
            is_realized=False
        )
        
        db.add(test_prediction)
        db.commit()
        print(f"✅ Test prediction ID: {test_prediction.id}")
        
        # Clean up test
        db.delete(test_prediction)
        db.commit()
        
        print(f"\n🎉 Database reset successful!")
        print(f"💡 Ready to use: user_id={user.id}, crypto_id={bitcoin.id}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)