# File: temp/import_schema.py
# Purpose: Import database schema structure from exported SQL file
# Usage: python temp/import_schema.py

import os
import sys
import subprocess
import glob
from datetime import datetime
from pathlib import Path
import shutil

# Add backend path to sys.path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

from app.core.config import get_settings

def find_schema_file():
    """
    Find the most recent schema backup file in temp directory
    """
    schema_files = glob.glob("temp/schema_backup_*.sql")
    if not schema_files:
        print("❌ No schema backup files found in temp/ directory")
        print("💡 Please ensure you have copied the schema file from source system")
        return None
    
    # Get the most recent file
    latest_file = max(schema_files, key=os.path.getctime)
    print(f"📁 Found schema file: {latest_file}")
    return latest_file

def check_prerequisites():
    """
    Check if required tools and environment are ready
    """
    print("🔍 Checking prerequisites...")
    
    # Check if psql is available
    try:
        result = subprocess.run(['psql', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ PostgreSQL client found: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ psql not found!")
        print("💡 Please install PostgreSQL client tools")
        return False
    
    # Check if Docker is running
    try:
        result = subprocess.run(['docker', 'ps'], 
                              capture_output=True, text=True, check=True)
        print("✅ Docker is running")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker is not running or not installed")
        print("💡 Please start Docker Desktop")
        return False
    
    return True

def setup_database_container():
    """
    Ensure database container is running
    """
    print("🐳 Setting up database container...")
    
    try:
        # Check if containers are already running
        result = subprocess.run(['docker-compose', 'ps', 'db'], 
                              capture_output=True, text=True)
        
        if 'Up' not in result.stdout:
            print("🚀 Starting database container...")
            subprocess.run(['docker-compose', 'up', '-d', 'db'], check=True)
            
            # Wait a moment for database to be ready
            import time
            print("⏳ Waiting for database to be ready...")
            time.sleep(10)
        else:
            print("✅ Database container is already running")
            
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error setting up database container: {e}")
        return False

def import_database_schema(schema_file):
    """
    Import database schema using psql
    """
    print(f"📥 Importing schema from: {schema_file}")
    
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
    
    # psql command to import schema
    psql_cmd = [
        "psql",
        f"--host={db_params['host']}",
        f"--port={db_params['port']}",
        f"--username={db_params['username']}",
        "--no-password",  # Will use PGPASSWORD environment variable
        f"--dbname={db_params['database']}",
        "--file=" + schema_file
    ]
    
    try:
        # Set password environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = db_params['password']
        
        print(f"🔗 Connecting to: {db_params['database']}@{db_params['host']}:{db_params['port']}")
        
        # Execute psql command
        result = subprocess.run(
            psql_cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        print("✅ Schema import completed successfully!")
        
        # Show any warnings or notices
        if result.stderr:
            print("📋 Import messages:")
            print(result.stderr)
            
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error importing schema: {e}")
        print(f"🔍 Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def restore_alembic_migrations():
    """
    Restore Alembic migration files from temp directory
    """
    print("📁 Restoring Alembic migration files...")
    
    migrations_temp = "temp/alembic_migrations"
    migrations_target = "backend/alembic/versions"
    
    try:
        # Ensure target directory exists
        os.makedirs(migrations_target, exist_ok=True)
        
        # Copy migration files
        if os.path.exists(migrations_temp):
            for file in os.listdir(migrations_temp):
                if file.endswith('.py'):
                    shutil.copy2(
                        os.path.join(migrations_temp, file),
                        os.path.join(migrations_target, file)
                    )
            print(f"✅ Migration files restored to: {migrations_target}")
        else:
            print(f"⚠️  No migration files found in: {migrations_temp}")
        
        # Copy alembic.ini if exists
        if os.path.exists("temp/alembic.ini"):
            shutil.copy2("temp/alembic.ini", "backend/alembic.ini")
            print("✅ alembic.ini restored")
            
        return True
        
    except Exception as e:
        print(f"❌ Error restoring migration files: {e}")
        return False

def update_alembic_head():
    """
    Update Alembic to mark current state as up-to-date
    """
    print("🔄 Updating Alembic revision state...")
    
    try:
        # Change to backend directory
        original_dir = os.getcwd()
        os.chdir("backend")
        
        # Get current head revision
        result = subprocess.run(
            ["alembic", "current"],
            capture_output=True,
            text=True
        )
        
        if "Current revision" not in result.stdout:
            # No current revision, stamp with head
            print("📌 Stamping database with current head revision...")
            subprocess.run(["alembic", "stamp", "head"], check=True)
            print("✅ Alembic state updated successfully")
        else:
            print("✅ Alembic is already up-to-date")
            
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error updating Alembic: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        # Return to original directory
        os.chdir(original_dir)

def verify_import():
    """
    Verify that the import was successful
    """
    print("🔍 Verifying import...")
    
    # Get database configuration
    settings = get_settings()
    
    db_params = {
        'host': settings.DATABASE_HOST,
        'port': settings.DATABASE_PORT,
        'database': settings.DATABASE_NAME,
        'username': settings.DATABASE_USER,
        'password': settings.DATABASE_PASSWORD
    }
    
    # Check tables command
    psql_cmd = [
        "psql",
        f"--host={db_params['host']}",
        f"--port={db_params['port']}",
        f"--username={db_params['username']}",
        "--no-password",
        f"--dbname={db_params['database']}",
        "--command=\\dt"
    ]
    
    try:
        env = os.environ.copy()
        env['PGPASSWORD'] = db_params['password']
        
        result = subprocess.run(
            psql_cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.stdout:
            print("✅ Database tables found:")
            print(result.stdout)
            return True
        else:
            print("⚠️  No tables found in database")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying import: {e}")
        return False

def main():
    """
    Main function to import database schema
    """
    print("🚀 Database Schema Import Tool")
    print("=" * 40)
    
    # Check prerequisites
    if not check_prerequisites():
        return False
    
    # Find schema file
    schema_file = find_schema_file()
    if not schema_file:
        return False
    
    # Setup database container
    if not setup_database_container():
        return False
    
    # Import schema
    if not import_database_schema(schema_file):
        return False
    
    # Restore migration files
    if not restore_alembic_migrations():
        return False
    
    # Update Alembic state
    if not update_alembic_head():
        return False
    
    # Verify import
    if not verify_import():
        print("⚠️  Import completed but verification failed")
        print("💡 You may need to run migrations manually")
    
    print("\n" + "=" * 50)
    print("✅ IMPORT COMPLETED SUCCESSFULLY!")
    print("=" * 50)
    print("🎉 Your database schema has been imported")
    print("🔄 Alembic migrations are ready")
    print("🚀 You can now start developing!")
    print("\n💡 Next steps:")
    print("   - Run: docker-compose up -d")
    print("   - Test: python -m pytest backend/tests/")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)