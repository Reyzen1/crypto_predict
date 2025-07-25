# File: temp/sync_database_with_model.py
# Sync database structure with the Prediction model

import sys
import os

# Add backend path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

def sync_predictions_table():
    """Sync predictions table with the model definition"""
    
    try:
        print("🔧 Syncing predictions table with model...")
        
        from app.core.database import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        
        try:
            # List of columns that should exist based on the model
            required_columns = [
                # Basic columns (already exist)
                ('id', 'SERIAL PRIMARY KEY'),
                ('crypto_id', 'INTEGER NOT NULL'),
                ('user_id', 'INTEGER'),  # Made nullable
                ('model_name', 'VARCHAR(50) NOT NULL'),
                ('model_version', 'VARCHAR(20) NOT NULL DEFAULT \'1.0\''),  # Already added
                
                # Core prediction fields
                ('predicted_price', 'NUMERIC(20,8) NOT NULL'),
                ('confidence_score', 'NUMERIC(5,4)'),
                
                # Target date (need to rename from target_date to target_datetime)
                ('target_datetime', 'TIMESTAMP WITH TIME ZONE NOT NULL'),
                
                # Additional fields from model
                ('prediction_horizon', 'INTEGER'),
                ('features_used', 'JSON'),
                ('model_parameters', 'JSON'),
                ('input_price', 'NUMERIC(20,8)'),
                ('input_features', 'JSON'),
                ('actual_price', 'NUMERIC(20,8)'),
                ('accuracy_percentage', 'NUMERIC(5,2)'),
                ('absolute_error', 'NUMERIC(20,8)'),
                ('squared_error', 'NUMERIC(30,8)'),
                ('is_realized', 'BOOLEAN DEFAULT FALSE'),
                ('is_accurate', 'BOOLEAN'),
                ('accuracy_threshold', 'NUMERIC(5,2) DEFAULT 5.0'),
                ('training_data_end', 'TIMESTAMP WITH TIME ZONE'),
                ('market_conditions', 'VARCHAR(20)'),
                ('volatility_level', 'VARCHAR(10)'),
                ('model_training_time', 'NUMERIC(10,2)'),
                ('prediction_time', 'NUMERIC(10,6)'),
                ('notes', 'TEXT'),
                ('debug_info', 'JSON'),
                ('created_at', 'TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP'),
                ('updated_at', 'TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP'),
                ('evaluated_at', 'TIMESTAMP WITH TIME ZONE')
            ]
            
            # Get current columns
            result = db.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'predictions' 
                ORDER BY ordinal_position;
            """))
            
            existing_columns = {row[0]: row for row in result.fetchall()}
            
            changes_made = []
            
            # 1. First, rename target_date to target_datetime if needed
            if 'target_date' in existing_columns and 'target_datetime' not in existing_columns:
                print("🔄 Renaming target_date to target_datetime...")
                db.execute(text("""
                    ALTER TABLE predictions 
                    RENAME COLUMN target_date TO target_datetime;
                """))
                changes_made.append("Renamed target_date to target_datetime")
            
            # 2. Make user_id nullable (since it can be optional)
            if 'user_id' in existing_columns:
                current_nullable = existing_columns['user_id'][2]
                if current_nullable == 'NO':
                    print("🔄 Making user_id nullable...")
                    db.execute(text("""
                        ALTER TABLE predictions 
                        ALTER COLUMN user_id DROP NOT NULL;
                    """))
                    changes_made.append("Made user_id nullable")
            
            # 3. Add missing columns (only the essential ones for now)
            essential_columns = [
                ('prediction_horizon', 'INTEGER'),
                ('input_price', 'NUMERIC(20,8)'),
                ('actual_price', 'NUMERIC(20,8)'),
                ('accuracy_percentage', 'NUMERIC(5,2)'),
                ('is_realized', 'BOOLEAN DEFAULT FALSE'),
                ('is_accurate', 'BOOLEAN'),
                ('accuracy_threshold', 'NUMERIC(5,2) DEFAULT 5.0'),
                ('updated_at', 'TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP'),
                ('evaluated_at', 'TIMESTAMP WITH TIME ZONE')
            ]
            
            for col_name, col_definition in essential_columns:
                if col_name not in existing_columns:
                    print(f"➕ Adding column: {col_name}")
                    db.execute(text(f"""
                        ALTER TABLE predictions 
                        ADD COLUMN {col_name} {col_definition};
                    """))
                    changes_made.append(f"Added {col_name} column")
            
            # 4. Change features_used from TEXT to JSON if needed
            if 'features_used' in existing_columns:
                current_type = existing_columns['features_used'][1]
                if 'text' in current_type.lower():
                    print("🔄 Converting features_used from TEXT to JSON...")
                    try:
                        db.execute(text("""
                            ALTER TABLE predictions 
                            ALTER COLUMN features_used TYPE JSON USING features_used::JSON;
                        """))
                        changes_made.append("Converted features_used to JSON")
                    except Exception as e:
                        print(f"⚠️ Could not convert features_used to JSON: {e}")
                        changes_made.append("features_used conversion failed (kept as TEXT)")
            
            # Commit all changes
            db.commit()
            
            if changes_made:
                print(f"\n✅ Applied {len(changes_made)} changes:")
                for change in changes_made:
                    print(f"   - {change}")
            else:
                print("✅ No changes needed - table is already synchronized")
            
            return True
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error syncing table: {e}")
            return False
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def verify_final_structure():
    """Verify the final table structure"""
    
    try:
        print("\n🔍 Verifying final table structure...")
        
        from app.core.database import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        
        try:
            result = db.execute(text("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_name = 'predictions' 
                ORDER BY ordinal_position;
            """))
            
            columns = result.fetchall()
            
            print(f"📊 Final predictions table structure ({len(columns)} columns):")
            print("-" * 80)
            
            key_columns = ['target_datetime', 'model_version', 'prediction_horizon', 'is_realized']
            
            for i, (col_name, data_type, is_nullable, col_default) in enumerate(columns, 1):
                nullable_str = "nullable: YES" if is_nullable == "YES" else "nullable: NO"
                default_str = f"default: {col_default}" if col_default else "no default"
                
                # Highlight key columns
                if col_name in key_columns:
                    print(f"{i:3d}. {col_name:<25} | {data_type:<20} | {nullable_str} | {default_str} ✓")
                else:
                    print(f"{i:3d}. {col_name:<25} | {data_type:<20} | {nullable_str} | {default_str}")
            
            print("-" * 80)
            
            # Check for key columns
            existing_cols = [col[0] for col in columns]
            
            required_key_cols = ['target_datetime', 'model_version', 'prediction_horizon', 'is_realized']
            missing_cols = [col for col in required_key_cols if col not in existing_cols]
            
            if not missing_cols:
                print("✅ All key columns present")
                return True
            else:
                print(f"❌ Missing key columns: {missing_cols}")
                return False
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error verifying structure: {e}")
        return False

def test_prediction_insert():
    """Test inserting a prediction with the new structure"""
    
    try:
        print("\n🧪 Testing prediction insert...")
        
        from app.core.database import SessionLocal
        from app.models.prediction import Prediction
        from datetime import datetime, timezone, timedelta
        from decimal import Decimal
        
        db = SessionLocal()
        
        try:
            # Create a test prediction
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
            return False
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Syncing Database with Prediction Model")
    print("=" * 50)
    
    # Step 1: Sync table structure
    if sync_predictions_table():
        print("\n✅ Table sync completed!")
        
        # Step 2: Verify structure
        if verify_final_structure():
            print("\n✅ Structure verification passed!")
            
            # Step 3: Test insert
            if test_prediction_insert():
                print("\n🎉 Database sync successful!")
                print("\n🚀 Now test the complete pipeline:")
                print("cd backend && python ../temp/test_complete_ml_pipeline.py")
            else:
                print("\n⚠️ Insert test failed - check model compatibility")
        else:
            print("\n⚠️ Structure verification failed")
    else:
        print("\n❌ Table sync failed")
        print("\n📋 You may need to manually run SQL commands or recreate the table")