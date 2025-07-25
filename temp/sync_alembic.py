# File: temp/sync_alembic.py
# Sync Alembic after manual database reset

import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.config import settings

def main():
    print("🔄 Syncing Alembic After Database Reset")
    print("=" * 40)
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            # Create alembic_version table
            print("📋 Creating alembic_version table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num VARCHAR(32) NOT NULL,
                    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                )
            """))
            
            # Clear any existing version
            conn.execute(text("DELETE FROM alembic_version"))
            
            # Get the latest migration file to use as head
            alembic_dir = backend_dir / "alembic" / "versions"
            if alembic_dir.exists():
                migration_files = list(alembic_dir.glob("*.py"))
                if migration_files:
                    # Get the latest migration file name (without .py)
                    latest_migration = migration_files[-1].stem
                    version_id = latest_migration.split('_')[0]  # Get version ID part
                    print(f"📍 Using migration version: {version_id}")
                    conn.execute(text(f"INSERT INTO alembic_version (version_num) VALUES ('{version_id}')"))
                else:
                    print("⚠️ No migration files found, using 'head'")
                    conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('head')"))
            else:
                print("⚠️ Alembic versions directory not found, using 'head'")
                conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('head')"))
            
            conn.commit()
        
        print("🎉 Alembic sync completed!")
        print("💡 Database is now in sync with current models")
        print("💡 Run 'cd backend && alembic current' to verify")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)