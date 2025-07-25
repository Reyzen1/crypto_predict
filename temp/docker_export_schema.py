# File: temp/docker_export_schema.py
# Purpose: Export database schema using Docker container (no local pg_dump needed)
# Usage: python temp/docker_export_schema.py

import os
import sys
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

# Add backend path to sys.path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

from app.core.config import get_settings

def check_docker_prerequisites():
    """
    Check if Docker is available and database container is running
    """
    print("🔍 Checking Docker prerequisites...")
    
    # Check if Docker is available
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Docker found: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker not found! Please install Docker Desktop")
        return False
    
    # Check if docker-compose is available
    try:
        result = subprocess.run(['docker-compose', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Docker Compose found: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker Compose not found!")
        return False
    
    return True

def ensure_database_running():
    """
    Ensure database container is running
    """
    print("🐳 Checking database container status...")
    
    try:
        # First try to check which docker-compose file exists and use appropriate service name
        compose_files = [
            ('docker-compose-backend.yml', 'postgres'),
            ('docker-compose.yml', 'postgres'),
            ('docker-compose.yml', 'db')  # fallback
        ]
        
        compose_file = None
        service_name = None
        
        for file_name, svc_name in compose_files:
            if os.path.exists(file_name):
                compose_file = file_name
                service_name = svc_name
                print(f"📁 Using compose file: {compose_file}")
                break
        
        if not compose_file:
            print("❌ No docker-compose file found!")
            return False
        
        # Check if database container is running
        cmd = ['docker-compose', '-f', compose_file, 'ps', service_name]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if 'Up' in result.stdout:
            print("✅ Database container is running")
            return True
        else:
            print("🚀 Starting database container...")
            start_cmd = ['docker-compose', '-f', compose_file, 'up', '-d', service_name]
            subprocess.run(start_cmd, check=True)
            
            # Wait for database to be ready
            import time
            print("⏳ Waiting for database to be ready...")
            
            # Try to check if database is ready using health check
            max_attempts = 15
            for attempt in range(max_attempts):
                try:
                    # Check container status
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if 'Up' in result.stdout:
                        # Try to ping database
                        ping_cmd = ['docker-compose', '-f', compose_file, 'exec', '-T', service_name, 
                                   'pg_isready', '-U', 'postgres']
                        ping_result = subprocess.run(ping_cmd, capture_output=True, text=True, timeout=5)
                        
                        if ping_result.returncode == 0:
                            print("✅ Database container is ready!")
                            return True
                    
                    print(f"⏳ Attempt {attempt + 1}/{max_attempts} - waiting...")
                    time.sleep(2)
                    
                except subprocess.TimeoutExpired:
                    continue
                except Exception:
                    continue
            
            print("⚠️  Database may not be fully ready, but continuing...")
            return True
                
    except subprocess.CalledProcessError as e:
        print(f"❌ Error with database container: {e}")
        print("💡 Make sure Docker Desktop is running")
        return False

def export_schema_with_docker():
    """
    Export database schema using Docker container's pg_dump
    """
    print("📤 Exporting schema using Docker...")
    
    # Get database configuration
    settings = get_settings()
    
    # Parse DATABASE_URL to get connection details
    # Format: postgresql://user:password@host:port/database
    import urllib.parse
    
    try:
        parsed_url = urllib.parse.urlparse(settings.DATABASE_URL)
        db_user = parsed_url.username or 'postgres'
        db_password = parsed_url.password or 'postgres123'
        db_host = parsed_url.hostname or 'localhost'
        db_port = parsed_url.port or 5432
        db_name = parsed_url.path.lstrip('/') or 'cryptopredict'
        
        print(f"🔗 Parsed database connection:")
        print(f"   User: {db_user}")
        print(f"   Host: {db_host}:{db_port}")
        print(f"   Database: {db_name}")
        
    except Exception as e:
        print(f"❌ Error parsing DATABASE_URL: {e}")
        print(f"DATABASE_URL: {settings.DATABASE_URL}")
        return None
    
    # Create timestamp for backup file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    schema_file = f"temp/schema_backup_{timestamp}.sql"
    
    # Ensure temp directory exists
    os.makedirs("temp", exist_ok=True)
    
    # Find the appropriate docker-compose file and service name
    compose_files = [
        ('docker-compose-backend.yml', 'postgres'),
        ('docker-compose.yml', 'postgres')
    ]
    
    compose_file = None
    service_name = None
    
    for file_name, svc_name in compose_files:
        if os.path.exists(file_name):
            compose_file = file_name
            service_name = svc_name
            break
    
    if not compose_file:
        print("❌ No suitable docker-compose file found!")
        return None
    
    # Docker command to run pg_dump inside the database container
    docker_cmd = [
        'docker-compose', '-f', compose_file, 'exec', '-T', service_name,
        'pg_dump',
        '-U', db_user,
        '--schema-only',      # Export only structure, no data
        '--no-owner',         # Don't include ownership commands
        '--no-privileges',    # Don't include privilege commands
        '--clean',            # Include DROP commands
        '--if-exists',        # Use IF EXISTS for DROP commands
        db_name
    ]
    
    try:
        print(f"🔗 Using compose file: {compose_file}")
        print(f"🐳 Using service: {service_name}")
        print(f"🔗 Exporting from database: {db_name}")
        print(f"📁 Output file: {schema_file}")
        
        # Execute docker command and save output to file
        with open(schema_file, 'w', encoding='utf-8') as f:
            result = subprocess.run(
                docker_cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
        
        # Check if file was created and has content
        if os.path.exists(schema_file) and os.path.getsize(schema_file) > 0:
            file_size = os.path.getsize(schema_file)
            print("✅ Schema export completed successfully!")
            print(f"📊 File size: {file_size / 1024:.2f} KB")
            
            # Create schema info file with parsed details
            create_schema_info_parsed(schema_file, db_user, db_host, db_port, db_name, timestamp)
            return schema_file
        else:
            print("❌ Export file is empty or not created")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error exporting schema: {e}")
        if e.stderr:
            print(f"🔍 Error details: {e.stderr}")
        
        # Try to get more information about the error
        if "database" in str(e.stderr).lower() and "does not exist" in str(e.stderr).lower():
            print("💡 The database might not exist yet. Try running:")
            print(f"   docker-compose -f {compose_file} exec {service_name} createdb -U {db_user} {db_name}")
        
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def create_schema_info_parsed(schema_file, db_user, db_host, db_port, db_name, timestamp):
    """
    Create an info file with export details using parsed database info
    """
    info_file = schema_file.replace('.sql', '_info.txt')
    
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write("Database Schema Export Information\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Export Method: Docker Container pg_dump\n")
        f.write(f"Source Database: {db_name}\n")
        f.write(f"Source Host: {db_host}:{db_port}\n")
        f.write(f"Source User: {db_user}\n")
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
        f.write("   OR: python temp/setup_new_database.py\n")
    
    print(f"📋 Info file created: {info_file}")

def create_schema_info(schema_file, settings, timestamp):
    """
    Create an info file with export details
    """
    info_file = schema_file.replace('.sql', '_info.txt')
    
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write("Database Schema Export Information\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Export Method: Docker Container pg_dump\n")
        f.write(f"Source Database: {settings.DATABASE_NAME}\n")
        f.write(f"Source Host: {settings.DATABASE_HOST}:{settings.DATABASE_PORT}\n")
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
        f.write("   OR: python temp/setup_new_database.py\n")
    
    print(f"📋 Info file created: {info_file}")

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
            migration_count = 0
            for file in os.listdir(migrations_source):
                if file.endswith('.py'):
                    shutil.copy2(
                        os.path.join(migrations_source, file),
                        os.path.join(migrations_temp, file)
                    )
                    migration_count += 1
            
            # Copy alembic.ini
            if os.path.exists("backend/alembic.ini"):
                shutil.copy2("backend/alembic.ini", "temp/alembic.ini")
                print("✅ alembic.ini copied")
            
            print(f"✅ {migration_count} migration files copied to: {migrations_temp}")
            return True
        else:
            print(f"⚠️  Migrations directory not found: {migrations_source}")
            print("💡 This might be normal if no migrations exist yet")
            return True  # Not a critical error
            
    except Exception as e:
        print(f"❌ Error copying migration files: {e}")
        return False

def test_exported_schema(schema_file):
    """
    Basic validation of exported schema file
    """
    print("🔍 Testing exported schema file...")
    
    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for common SQL elements
        checks = {
            'CREATE TABLE': content.count('CREATE TABLE'),
            'CREATE INDEX': content.count('CREATE INDEX'),
            'ALTER TABLE': content.count('ALTER TABLE'),
            'PRIMARY KEY': content.count('PRIMARY KEY')
        }
        
        print("📊 Schema content analysis:")
        for item, count in checks.items():
            if count > 0:
                print(f"   ✅ {item}: {count}")
            else:
                print(f"   ⚠️  {item}: {count}")
        
        # Check for expected tables (based on your project)
        expected_tables = ['users', 'cryptocurrencies', 'price_data', 'predictions']
        found_tables = []
        
        for table in expected_tables:
            if f'CREATE TABLE public.{table}' in content or f'CREATE TABLE {table}' in content:
                found_tables.append(table)
        
        print(f"🗃️  Expected tables found: {len(found_tables)}/{len(expected_tables)}")
        for table in found_tables:
            print(f"   ✅ {table}")
        
        missing_tables = [t for t in expected_tables if t not in found_tables]
        if missing_tables:
            print("⚠️  Missing tables (might be normal if not created yet):")
            for table in missing_tables:
                print(f"   ⚠️  {table}")
        
        return len(found_tables) > 0  # At least some tables should exist
        
    except Exception as e:
        print(f"❌ Error testing schema file: {e}")
        return False

def main():
    """
    Main function to export database schema using Docker
    """
    print("🚀 Docker-based Database Schema Export Tool")
    print("=" * 50)
    print("💡 This tool uses Docker container to export schema")
    print("   No need to install PostgreSQL client tools locally!")
    print("=" * 50)
    
    # Check Docker prerequisites
    if not check_docker_prerequisites():
        return False
    
    # Ensure database is running
    if not ensure_database_running():
        return False
    
    # Export schema
    schema_file = export_schema_with_docker()
    if not schema_file:
        return False
    
    # Test exported schema
    if not test_exported_schema(schema_file):
        print("⚠️  Schema file seems incomplete, but continuing...")
    
    # Export migration files
    export_alembic_migrations()
    
    print("\n" + "=" * 60)
    print("✅ DOCKER EXPORT COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("📦 Files ready for transfer:")
    print(f"   - {schema_file}")
    print(f"   - {schema_file.replace('.sql', '_info.txt')}")
    print("   - temp/alembic_migrations/* (migration files)")
    print("   - temp/alembic.ini")
    print("\n💡 Transfer these files to your target system")
    print("   Then run: python temp/setup_new_database.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)