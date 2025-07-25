# File: temp/export_schema.py
# Purpose: Export database schema structure for migration to another system
# Usage: python temp/export_schema.py

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Add backend path to sys.path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

from app.core.config import get_settings

def export_database_schema():
    """
    Export PostgreSQL database schema using pg_dump
    Creates a SQL file with only table structures, no data
    """
    
    print("🔄 Starting database schema export...")
    
    # Get database configuration
    settings = get_settings()
    
    # Database connection parameters
    db_params = {
        'host': settings.DATABASE_HOST,
        'port': settings.DATABASE_PORT,
        'database': settings.DATABASE_NAME,
        'username': settings.DATABASE_USER,
        'password': settings.DATABASE_PASSWORD
    }
    
    # Create timestamp for backup file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    schema_file = f"temp/schema_backup_{timestamp}.sql"
    
    # Ensure temp directory exists
    os.makedirs("temp", exist_ok=True)
    
    # pg_dump command for schema only (no data)
    pg_dump_cmd = [
        "pg_dump",
        f"--host={db_params['host']}",
        f"--port={db_params['port']}",
        f"--username={db_params['username']}",
        "--no-password",  # Will use PGPASSWORD environment variable
        "--schema-only",  # Export only structure, no data
        "--no-owner",     # Don't include ownership commands
        "--no-privileges", # Don't include privilege commands
        "--clean",        # Include DROP commands
        "--create",       # Include CREATE DATABASE command
        "--if-exists",    # Use IF EXISTS for DROP commands
        f"--file={schema_file}",
        db_params['database']
    ]
    
    try:
        # Set password environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = db_params['password']
        
        print(f"📤 Exporting schema to: {schema_file}")
        print(f"🔗 Database: {db_params['database']}@{db_params['host']}:{db_params['port']}")
        
        # Execute pg_dump command
        result = subprocess.run(
            pg_dump_cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        print("✅ Schema export completed successfully!")
        print(f"📁 Schema file created: {schema_file}")
        
        # Get file size
        file_size = os.path.getsize(schema_file)
        print(f"📊 File size: {file_size / 1024:.2f} KB")
        
        # Create a simple schema info file
        create_schema_info(schema_file, db_params, timestamp)
        
        return schema_file
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error exporting schema: {e}")
        print(f"🔍 Error output: {e.stderr}")
        return None
    except FileNotFoundError:
        print("❌ pg_dump not found. Please ensure PostgreSQL client tools are installed.")
        print("💡 You can download from: https://www.postgresql.org/download/windows/")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def create_schema_info(schema_file, db_params, timestamp):
    """
    Create an info file with export details
    """
    info_file = schema_file.replace('.sql', '_info.txt')
    
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write("Database Schema Export Information\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Source Database: {db_params['database']}\n")
        f.write(f"Source Host: {db_params['host']}:{db_params['port']}\n")
        f.write(f"Schema File: {schema_file}\n")
        f.write(f"Export Type: Schema Only (No Data)\n\n")
        f.write("Files to transfer to new system:\n")
        f.write(f"1. {schema_file}\n")
        f.write(f"2. {info_file}\n")
        f.write("3. backend/alembic/versions/* (all migration files)\n")
        f.write("4. backend/alembic.ini\n\n")
        f.write("Next steps on target system:\n")
        f.write("1. Setup Docker and Docker Compose\n")
        f.write("2. Clone project from GitHub\n")
        f.write("3. Copy migration files to backend/alembic/versions/\n")
        f.write("4. Run: python temp/import_schema.py\n")
    
    print(f"📋 Info file created: {info_file}")

def check_prerequisites():
    """
    Check if required tools are available
    """
    print("🔍 Checking prerequisites...")
    
    # Check if pg_dump is available
    try:
        result = subprocess.run(['pg_dump', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ PostgreSQL client found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ pg_dump not found!")
        print("💡 Please install PostgreSQL client tools:")
        print("   - Download from: https://www.postgresql.org/download/windows/")
        print("   - Or install via chocolatey: choco install postgresql")
        return False

def export_alembic_migrations():
    """
    Copy Alembic migration files to temp directory for transfer
    """
    print("📁 Copying Alembic migration files...")
    
    migrations_source = "backend/alembic/versions"
    migrations_temp = "temp/alembic_migrations"
    
    try:
        # Create temp migrations directory
        os.makedirs(migrations_temp, exist_ok=True)
        
        # Copy all migration files
        if os.path.exists(migrations_source):
            import shutil
            for file in os.listdir(migrations_source):
                if file.endswith('.py'):
                    shutil.copy2(
                        os.path.join(migrations_source, file),
                        os.path.join(migrations_temp, file)
                    )
            
            # Copy alembic.ini
            if os.path.exists("backend/alembic.ini"):
                shutil.copy2("backend/alembic.ini", "temp/alembic.ini")
            
            print(f"✅ Migration files copied to: {migrations_temp}")
            return True
        else:
            print(f"⚠️  Migrations directory not found: {migrations_source}")
            return False
            
    except Exception as e:
        print(f"❌ Error copying migration files: {e}")
        return False

def main():
    """
    Main function to export database schema
    """
    print("🚀 Database Schema Export Tool")
    print("=" * 40)
    
    # Check prerequisites
    if not check_prerequisites():
        return False
        
    # Export schema
    schema_file = export_database_schema()
    if not schema_file:
        return False
        
    # Export migration files
    export_alembic_migrations()
    
    print("\n" + "=" * 50)
    print("✅ EXPORT COMPLETED SUCCESSFULLY!")
    print("=" * 50)
    print("📦 Files ready for transfer:")
    print(f"   - {schema_file}")
    print(f"   - {schema_file.replace('.sql', '_info.txt')}")
    print("   - temp/alembic_migrations/* (migration files)")
    print("   - temp/alembic.ini")
    print("\n💡 Copy these files to your target system")
    print("   Then run: python temp/import_schema.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)