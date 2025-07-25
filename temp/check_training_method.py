# File: temp/check_training_method.py
# Check which training method was used (MLTrainingService or fallback)

import sys
from pathlib import Path
import logging
from datetime import datetime, timezone

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.core.config import settings
from app.models.cryptocurrency import Cryptocurrency
from app.models.prediction import Prediction

# Configure logging to capture training messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def check_recent_training_logs():
    """Check recent training activity and methods used"""
    print("🔍 Checking Training Method Usage")
    print("=" * 40)
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Get recent training records from predictions table
        recent_training = db.query(Prediction).filter(
            Prediction.model_name.like('%training%')
        ).order_by(Prediction.created_at.desc()).limit(5).all()
        
        print(f"📊 Found {len(recent_training)} recent training records:")
        print()
        
        for i, record in enumerate(recent_training, 1):
            print(f"🔬 Training Record #{i}:")
            print(f"   Model Name: {record.model_name}")
            print(f"   Model Version: {record.model_version}")
            print(f"   Created At: {record.created_at}")
            print(f"   Confidence Score: {record.confidence_score}")
            
            # Check features_used for training method indicators
            if record.features_used:
                features = str(record.features_used)
                if 'MLTrainingService' in features:
                    print("   ✅ Method: MLTrainingService (Advanced)")
                elif 'simple' in features.lower() or 'fallback' in features.lower():
                    print("   🔄 Method: Fallback (Simple)")
                else:
                    print("   ❓ Method: Unknown - checking content...")
                    if 'training_metrics' in features:
                        print("   📈 Contains training metrics (likely MLTrainingService)")
                    else:
                        print("   📉 Basic metrics (likely fallback)")
            else:
                print("   ❓ Method: Unknown (no features_used data)")
            
            print()
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def run_training_test_with_logging():
    """Run a training test with detailed logging to see which method is used"""
    print("🧪 Running Training Test with Detailed Logging")
    print("=" * 50)
    
    try:
        # Import training modules
        from app.ml.training.training_service import MLTrainingService
        from app.ml.simple_models.simple_training import train_model_for_crypto_simple
        from app.core.database import get_db
        
        # Get database session
        db = next(get_db())
        crypto = db.query(Cryptocurrency).filter(Cryptocurrency.symbol == "BTC").first()
        
        if not crypto:
            print("❌ Bitcoin not found in database")
            return False
        
        print(f"🪙 Testing training for Bitcoin (ID: {crypto.id})")
        print()
        
        # Test 1: Try MLTrainingService directly
        print("📋 Test 1: MLTrainingService (Direct)")
        print("-" * 30)
        try:
            ml_service = MLTrainingService()
            result = ml_service.train_model(crypto.id)
            print("✅ MLTrainingService: SUCCESS")
            print(f"   Model ID: {result.get('model_id', 'Unknown')}")
            print(f"   Training Duration: {result.get('training_duration_seconds', 'Unknown')} seconds")
        except Exception as e:
            print(f"❌ MLTrainingService: FAILED - {e}")
        
        print()
        
        # Test 2: Try simple training directly
        print("📋 Test 2: Simple Training (Direct)")
        print("-" * 30)
        try:
            result = train_model_for_crypto_simple(crypto.id)
            print("✅ Simple Training: SUCCESS")
            print(f"   Result: {type(result)}")
        except Exception as e:
            print(f"❌ Simple Training: FAILED - {e}")
        
        print()
        
        # Test 3: Check which method your current system uses
        print("📋 Test 3: Current System Method")
        print("-" * 30)
        
        # Try to find your training endpoint or service
        try:
            # This will depend on your actual implementation
            # Let's check if there's a training service or endpoint
            from app.ml.training import training_service
            
            # Check if there's a train method that uses fallback
            if hasattr(training_service, 'train_model'):
                print("🔍 Found training_service.train_model")
                # You can add more specific checks here
            
        except ImportError as e:
            print(f"📝 Training service import info: {e}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def analyze_log_files():
    """Analyze log files for training method indicators"""
    print("📄 Analyzing Log Files")
    print("=" * 25)
    
    # Check common log locations
    log_paths = [
        Path("logs/app.log"),
        Path("backend/logs/app.log"),
        Path("app.log"),
        Path("backend/app.log")
    ]
    
    found_logs = False
    
    for log_path in log_paths:
        if log_path.exists():
            found_logs = True
            print(f"📋 Found log: {log_path}")
            
            try:
                with open(log_path, 'r') as f:
                    lines = f.readlines()[-50:]  # Last 50 lines
                
                training_lines = [line for line in lines if 'train' in line.lower()]
                
                if training_lines:
                    print(f"   🔍 Recent training activity:")
                    for line in training_lines[-5:]:  # Last 5 training lines
                        line = line.strip()
                        if 'fallback' in line.lower():
                            print(f"      🔄 FALLBACK: {line}")
                        elif 'MLTrainingService' in line:
                            print(f"      ✅ ADVANCED: {line}")
                        else:
                            print(f"      📝 GENERAL: {line}")
                else:
                    print("   ℹ️ No recent training activity in logs")
                    
            except Exception as e:
                print(f"   ❌ Error reading log: {e}")
    
    if not found_logs:
        print("📝 No log files found in common locations")
        print("💡 Check your logging configuration in app/core/config.py")

def main():
    print("🔍 Training Method Detection Report")
    print("=" * 50)
    print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Method 1: Check database records
    check_recent_training_logs()
    print()
    
    # Method 2: Run training tests
    run_training_test_with_logging()
    print()
    
    # Method 3: Analyze log files
    analyze_log_files()
    print()
    
    print("💡 Summary:")
    print("   - Check the database records above for training method indicators")
    print("   - Look for 'MLTrainingService' vs 'fallback' in the output")
    print("   - Recent training features will show which method was used")

if __name__ == "__main__":
    main()