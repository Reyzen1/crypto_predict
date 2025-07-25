# File: temp/check_database_structure.py
# Check database structure to see if model_version column exists

import sys
import os

# Add backend path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

def check_predictions_table_structure():
    """Check the actual structure of predictions table in database"""
    
    try:
        print("🔍 Checking predictions table structure...")
        
        from app.core.database import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        
        try:
            # Get table structure
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
            
            print(f"📊 predictions table has {len(columns)} columns:")
            print("-" * 80)
            
            model_version_exists = False
            
            for i, (col_name, data_type, is_nullable, col_default) in enumerate(columns, 1):
                nullable_str = "nullable: YES" if is_nullable == "YES" else "nullable: NO"
                default_str = f"default: {col_default}" if col_default else "no default"
                
                print(f"{i:3d}. {col_name:<25} | {data_type:<20} | {nullable_str} | {default_str}")
                
                if col_name == 'model_version':
                    model_version_exists = True
            
            print("-" * 80)
            
            if model_version_exists:
                print("✅ model_version column EXISTS in database")
            else:
                print("❌ model_version column DOES NOT exist in database")
                print("\n🔧 Need to add model_version column:")
                print("ALTER TABLE predictions ADD COLUMN model_version VARCHAR(20) NOT NULL DEFAULT '1.0';")
            
            return model_version_exists
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error checking database structure: {e}")
        return False

def add_model_version_column():
    """Add model_version column if it doesn't exist"""
    
    try:
        print("\n🔧 Adding model_version column...")
        
        from app.core.database import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        
        try:
            # Add the column
            db.execute(text("""
                ALTER TABLE predictions 
                ADD COLUMN IF NOT EXISTS model_version VARCHAR(20) NOT NULL DEFAULT '1.0';
            """))
            
            db.commit()
            print("✅ model_version column added successfully")
            
            # Verify it was added
            result = db.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'predictions' 
                AND column_name = 'model_version';
            """))
            
            if result.fetchone():
                print("✅ Column verified in database")
                return True
            else:
                print("❌ Column not found after adding")
                return False
                
        except Exception as e:
            db.rollback()
            print(f"❌ Error adding column: {e}")
            return False
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def check_alembic_migration_status():
    """Check current alembic migration status"""
    
    try:
        print("\n📋 Checking Alembic migration status...")
        
        from app.core.database import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        
        try:
            # Check if alembic_version table exists
            result = db.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'alembic_version'
                );
            """))
            
            alembic_exists = result.scalar()
            
            if alembic_exists:
                # Get current version
                result = db.execute(text("SELECT version_num FROM alembic_version;"))
                current_version = result.scalar()
                print(f"✅ Alembic is initialized. Current version: {current_version}")
            else:
                print("⚠️ Alembic is not initialized")
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error checking Alembic status: {e}")

def run_quick_database_test():
    """Run a quick test to see what's working"""
    
    try:
        print("\n🧪 Quick database connection test...")
        
        from app.core.database import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        
        try:
            # Test basic connection
            result = db.execute(text("SELECT 1 as test;"))
            if result.scalar() == 1:
                print("✅ Database connection working")
            
            # Check what tables exist
            result = db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            
            tables = [row[0] for row in result.fetchall()]
            print(f"✅ Found {len(tables)} tables: {', '.join(tables)}")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Database Structure Check")
    print("=" * 50)
    
    # Step 1: Test basic database connection
    if not run_quick_database_test():
        print("❌ Database connection failed. Check your database setup.")
        exit(1)
    
    # Step 2: Check alembic status
    check_alembic_migration_status()
    
    # Step 3: Check predictions table structure
    model_version_exists = check_predictions_table_structure()
    
    # Step 4: Add column if it doesn't exist
    if not model_version_exists:
        print("\n🔧 model_version column is missing. Adding it...")
        if add_model_version_column():
            print("\n✅ Column added successfully!")
            # Check again to confirm
            check_predictions_table_structure()
        else:
            print("\n❌ Failed to add column")
            print("\n📋 Manual fix needed:")
            print("1. Connect to PostgreSQL:")
            print("   psql -h localhost -U postgres -d cryptopredict")
            print("2. Run this SQL:")
            print("   ALTER TABLE predictions ADD COLUMN model_version VARCHAR(20) NOT NULL DEFAULT '1.0';")
    else:
        print("\n✅ model_version column already exists!")
    
    print("\n🚀 After fixing, test again:")
    print("cd backend && python ../temp/test_complete_ml_pipeline.py")