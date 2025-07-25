# File: temp/add_remaining_columns.py
# Add the remaining missing columns to predictions table

import sys
import os

# Add backend path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

def add_missing_columns():
    """Add the remaining missing columns"""
    
    try:
        print("🔧 Adding remaining missing columns...")
        
        from app.core.database import engine
        from sqlalchemy import text
        
        # Use engine directly for DDL operations
        with engine.connect() as connection:
            with connection.begin():
                
                # Missing columns from the error
                missing_columns = [
                    "absolute_error NUMERIC(20,8)",
                    "squared_error NUMERIC(30,8)",
                    "training_data_end TIMESTAMP WITH TIME ZONE",
                    "market_conditions VARCHAR(20)",
                    "volatility_level VARCHAR(10)",
                    "model_training_time NUMERIC(10,2)",
                    "prediction_time NUMERIC(10,6)",
                    "notes TEXT",
                    "debug_info JSON",
                    "model_parameters JSON",
                    "input_features JSON"
                ]
                
                added_count = 0
                
                for column_def in missing_columns:
                    try:
                        column_name = column_def.split()[0]
                        connection.execute(text(f"""
                            ALTER TABLE predictions 
                            ADD COLUMN IF NOT EXISTS {column_def};
                        """))
                        print(f"✅ Added {column_name}")
                        added_count += 1
                    except Exception as e:
                        print(f"⚠️ {column_name}: {e}")
                
                print(f"\n✅ Successfully added {added_count} additional columns!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding columns: {e}")
        return False

def verify_complete_structure():
    """Verify that all columns are now present"""
    
    try:
        print("\n🔍 Verifying complete table structure...")
        
        from app.core.database import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        
        try:
            result = db.execute(text("""
                SELECT column_name
                FROM information_schema.columns 
                WHERE table_name = 'predictions' 
                ORDER BY ordinal_position;
            """))
            
            columns = [row[0] for row in result.fetchall()]
            
            print(f"📊 Total columns: {len(columns)}")
            
            # Check for all required columns from the model
            required_columns = [
                'id', 'crypto_id', 'user_id', 'model_name', 'model_version',
                'predicted_price', 'confidence_score', 'prediction_horizon',
                'target_datetime', 'features_used', 'model_parameters',
                'input_price', 'input_features', 'actual_price', 
                'accuracy_percentage', 'absolute_error', 'squared_error',
                'is_realized', 'is_accurate', 'accuracy_threshold',
                'training_data_end', 'market_conditions', 'volatility_level',
                'model_training_time', 'prediction_time', 'notes', 'debug_info',
                'created_at', 'updated_at', 'evaluated_at'
            ]
            
            missing = [col for col in required_columns if col not in columns]
            
            if missing:
                print(f"❌ Still missing columns: {missing}")
                return False
            else:
                print("✅ All required columns are present!")
                print(f"   Current columns: {', '.join(sorted(columns))}")
                return True
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

def test_prediction_insert_again():
    """Test inserting a prediction with all columns"""
    
    try:
        print("\n🧪 Testing prediction insert with complete structure...")
        
        from app.core.database import SessionLocal
        from app.models.prediction import Prediction
        from datetime import datetime, timezone, timedelta
        from decimal import Decimal
        
        db = SessionLocal()
        
        try:
            # Create a test prediction with minimal required fields
            test_prediction = Prediction(
                crypto_id=1,
                user_id=1,
                model_name="LSTM_test",
                model_version="1.0",
                predicted_price=Decimal("50000.00"),
                confidence_score=Decimal("0.85"),
                target_datetime=datetime.now(timezone.utc) + timedelta(hours=24),
                prediction_horizon=24,
                input_price=Decimal("49000.00"),
                is_realized=False,
                accuracy_threshold=Decimal("5.0")
            )
            
            db.add(test_prediction)
            db.commit()
            
            print("✅ Test prediction inserted successfully!")
            print(f"   - ID: {test_prediction.id}")
            print(f"   - target_datetime: {test_prediction.target_datetime}")
            print(f"   - model_version: {test_prediction.model_version}")
            
            # Clean up - delete the test prediction
            db.delete(test_prediction)
            db.commit()
            print("✅ Test prediction cleaned up")
            
            return True
            
        except Exception as e:
            db.rollback()
            print(f"❌ Test prediction failed: {e}")
            
            # If it still fails, show which columns are causing issues
            import traceback
            error_details = str(e)
            if 'column' in error_details and 'does not exist' in error_details:
                # Extract column name from error
                import re
                match = re.search(r'column "([^"]+)" of relation', error_details)
                if match:
                    missing_col = match.group(1)
                    print(f"❌ Missing column: {missing_col}")
            
            return False
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Adding Remaining Missing Columns")
    print("=" * 50)
    
    # Step 1: Add missing columns
    if add_missing_columns():
        
        # Step 2: Verify structure
        if verify_complete_structure():
            
            # Step 3: Test insert
            if test_prediction_insert_again():
                print("\n🎉 Database structure is now complete!")
                print("\n🚀 Ready to test:")
                print("cd backend && python ../temp/test_complete_ml_pipeline.py")
            else:
                print("\n⚠️ Insert test failed - there may still be missing columns")
                print("Check the error details above")
        else:
            print("\n⚠️ Structure verification failed")
            print("Some columns may still be missing")
    else:
        print("\n❌ Failed to add missing columns")