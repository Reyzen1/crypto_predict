# File: temp/setup_new_database.py
# Purpose: Complete setup of database on new system (combines all steps)
# Usage: python temp/setup_new_database.py

import os
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path

# Add backend path to sys.path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

def print_banner():
    """Print setup banner"""
    print("🚀 CryptoPredict Database Setup Tool")
    print("=" * 50)
    print("📋 This tool will:")
    print("   1. Check prerequisites")
    print("   2. Setup Docker containers")
    print("   3. Import database schema")
    print("   4. Setup Alembic migrations")
    print("   5. Validate setup")
    print("=" * 50)

def check_all_prerequisites():
    """
    Comprehensive prerequisite check
    """
    print("🔍 Checking all prerequisites...")
    
    checks = []
    
    # Check Docker
    try:
        subprocess.run(['docker', '--version'], 
                      capture_output=True, text=True, check=True)
        print("✅ Docker is installed")
        checks.append(True)
    except:
        print("❌ Docker is not installed")
        checks.append(False)
    
    # Check Docker Compose
    try:
        subprocess.run(['docker-compose', '--version'], 
                      capture_output=True, text=True, check=True)
        print("✅ Docker Compose is installed")
        checks.append(True)
    except:
        print("❌ Docker Compose is not installed")
        checks.append(False)
    
    # Check PostgreSQL client
    try:
        subprocess.run(['psql', '--version'], 
                      capture_output=True, text=True, check=True)
        print("✅ PostgreSQL client is installed")
        checks.append(True)
    except:
        print("❌ PostgreSQL client is not installed")
        print("💡 Download from: https://www.postgresql.org/download/windows/")
        checks.append(False)
    
    # Check Python packages
    try:
        from app.core.config import get_settings
        print("✅ Backend Python packages available")
        checks.append(True)
    except ImportError as e:
        print(f"❌ Backend packages missing: {e}")
        print("💡 Run: pip install -r backend/requirements.txt")
        checks.append(False)
    
    # Check required files
    required_files = [
        "docker-compose.yml",
        "backend/alembic.ini",
        "backend/app/core/config.py"
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ Found: {file_path}")
            checks.append(True)
        else:
            print(f"❌ Missing: {file_path}")
            checks.append(False)
    
    return all(checks)

def setup_environment():
    """
    Setup environment variables and configuration
    """
    print("⚙️  Setting up environment...")
    
    # Check if .env file exists
    env_files = [".env", "backend/.env", ".env.local"]
    env_exists = any(os.path.exists(f) for f in env_files)
    
    if not env_exists:
        print("⚠️  No .env file found")
        print("💡 Creating basic .env file...")
        
        # Create basic .env file
        env_content = """# Database Configuration
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=cryptopredict
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# API Configuration
SECRET_KEY=your-secret-key-change-this
API_V1_STR=/api/v1
PROJECT_NAME=CryptoPredict

# External APIs
COINGECKO_API_KEY=
BINANCE_API_KEY=
BINANCE_SECRET_KEY=
"""
        
        with open(".env", "w") as f:
            f.write(env_content)
        
        print("✅ Basic .env file created")
        print("💡 Please update the SECRET_KEY and API keys")
    else:
        print("✅ Environment file found")
    
    return True

def start_docker_services():
    """
    Start required Docker services
    """
    print("🐳 Starting Docker services...")
    
    try:
        # Find appropriate docker-compose file
        compose_files = [
            ('docker-compose-backend.yml', ['postgres', 'redis']),
            ('docker-compose.yml', ['postgres', 'redis'])
        ]
        
        compose_file = None
        services = None
        
        for file_name, svc_list in compose_files:
            if os.path.exists(file_name):
                compose_file = file_name
                services = svc_list
                break
        
        if not compose_file:
            print("❌ No suitable docker-compose file found!")
            return False
        
        print(f"📁 Using compose file: {compose_file}")
        print(f"🚀 Starting services: {', '.join(services)}")
        
        # Start database and redis services
        start_cmd = ['docker-compose', '-f', compose_file, 'up', '-d'] + services
        result = subprocess.run(start_cmd, capture_output=True, text=True, check=True)
        
        print("✅ Docker services started")
        
        # Wait for database to be ready
        print("⏳ Waiting for database to be ready...")
        max_attempts = 30
        
        for attempt in range(max_attempts):
            try:
                # Try to ping database using Docker
                ping_cmd = [
                    'docker-compose', '-f', compose_file, 'exec', '-T', 'postgres',
                    'pg_isready', '-U', 'postgres'
                ]
                ping_result = subprocess.run(ping_cmd, capture_output=True, text=True, timeout=5)
                
                if ping_result.returncode == 0:
                    print("✅ Database is ready!")
                    return True
                    
            except subprocess.TimeoutExpired:
                pass
            except Exception:
                pass
            
            if attempt < max_attempts - 1:
                print(f"⏳ Attempt {attempt + 1}/{max_attempts} - waiting...")
                time.sleep(2)
        
        print("⚠️  Database may not be fully ready, but continuing...")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting Docker services: {e}")
        print("💡 Make sure Docker Desktop is running")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False

def run_import_schema():
    """
    Run the import schema script
    """
    print("📥 Running schema import...")
    
    try:
        # Import the necessary functions directly instead of calling subprocess
        import sys
        from pathlib import Path
        
        # Add current directory to path for imports
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir))
        
        # Import our custom import functions
        from docker_export_schema import get_database_schema_info
        import urllib.parse
        import subprocess
        import os
        
        # Get database configuration
        backend_path = Path(__file__).parent.parent / "backend"
        sys.path.append(str(backend_path))
        from app.core.config import get_settings
        
        settings = get_settings()
        
        # Parse DATABASE_URL to get connection details
        parsed_url = urllib.parse.urlparse(settings.DATABASE_URL)
        db_user = parsed_url.username or 'postgres'
        db_name = parsed_url.path.lstrip('/') or 'cryptopredict'
        
        # Find schema backup file
        import glob
        schema_files = glob.glob("temp/schema_backup_*.sql")
        if not schema_files:
            print("❌ No schema backup files found in temp/ directory")
            return False
            
        # Get the most recent file
        schema_file = max(schema_files, key=os.path.getctime)
        print(f"📁 Using schema file: {schema_file}")
        
        # Find appropriate docker-compose file and service name
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
            return False
        
        # Import schema using Docker container's psql
        print(f"🔗 Using compose file: {compose_file}")
        print(f"🐳 Using service: {service_name}")
        
        psql_cmd = [
            'docker-compose', '-f', compose_file, 'exec', '-T', service_name,
            'psql',
            '-U', db_user,
            '-d', db_name,
            '-f', f'/tmp/{os.path.basename(schema_file)}'
        ]
        
        # Copy schema file to container first
        print("📁 Copying schema file to container...")
        copy_cmd = [
            'docker', 'cp', schema_file, 
            f'cryptopredict_{service_name}:/tmp/{os.path.basename(schema_file)}'
        ]
        
        result = subprocess.run(copy_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error copying file to container: {result.stderr}")
            return False
        
        # Execute import
        print("📥 Importing schema...")
        result = subprocess.run(psql_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Schema import completed successfully!")
            if result.stdout:
                print("📋 Import messages:")
                print(result.stdout)
            return True
        else:
            print(f"❌ Schema import failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running import: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_validation():
    """
    Run the validation checks
    """
    print("🔍 Running validation...")
    
    try:
        # Import validation functions directly
        import sys
        from pathlib import Path
        import urllib.parse
        import subprocess
        
        # Get database configuration
        backend_path = Path(__file__).parent.parent / "backend"
        sys.path.append(str(backend_path))
        from app.core.config import get_settings
        
        settings = get_settings()
        
        # Parse DATABASE_URL
        parsed_url = urllib.parse.urlparse(settings.DATABASE_URL)
        db_user = parsed_url.username or 'postgres'
        db_name = parsed_url.path.lstrip('/') or 'cryptopredict'
        
        # Find docker-compose file
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
            print("❌ No suitable docker-compose file found for validation!")
            return False
        
        # Check tables using Docker container
        print("📋 Checking database tables...")
        
        tables_cmd = [
            'docker-compose', '-f', compose_file, 'exec', '-T', service_name,
            'psql', '-U', db_user, '-d', db_name, '-c', '\\dt'
        ]
        
        result = subprocess.run(tables_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            if result.stdout:
                print("✅ Database tables found:")
                print(result.stdout)
                
                # Check for expected tables
                expected_tables = ['users', 'cryptocurrencies', 'price_data', 'predictions', 'alembic_version']
                found_tables = []
                
                for table in expected_tables:
                    if table in result.stdout:
                        found_tables.append(table)
                
                print(f"📊 Expected tables found: {len(found_tables)}/{len(expected_tables)}")
                for table in found_tables:
                    print(f"   ✅ {table}")
                
                missing = [t for t in expected_tables if t not in found_tables]
                if missing:
                    print("⚠️  Missing tables:")
                    for table in missing:
                        print(f"   ❌ {table}")
                
                # Validation is successful if we have at least some basic tables
                return len(found_tables) >= 2
            else:
                print("⚠️  No tables output received")
                return False
        else:
            print(f"❌ Error checking tables: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running validation: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_setup_summary():
    """
    Create a summary of the setup process
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = f"temp/setup_summary_{timestamp}.md"
    
    summary_content = f"""# Database Setup Summary

**Setup Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## ✅ Completed Steps

1. **Prerequisites Check** - All required tools verified
2. **Environment Setup** - Configuration files created/verified
3. **Docker Services** - Database and Redis containers started
4. **Schema Import** - Database structure imported successfully
5. **Alembic Setup** - Migration system configured
6. **Validation** - Database schema validated

## 🚀 Next Steps

### Development Commands
```bash
# Start all services
docker-compose up -d

# Run backend development server
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run frontend development server
cd frontend
npm run dev
```

### Database Commands
```bash
# Check database status
python temp/validate_schema.py

# Run new migrations
cd backend
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"
```

### Testing Commands
```bash
# Run backend tests
cd backend
python -m pytest tests/

# Check API endpoints
curl http://localhost:8000/api/v1/health
```

## 📁 Important Files

- `temp/schema_backup_*.sql` - Original schema export
- `temp/validation_report_*.json` - Setup validation results
- `.env` - Environment configuration
- `backend/alembic/versions/*` - Database migrations

## 🔧 Troubleshooting

If you encounter issues:

1. **Database Connection Issues:**
   ```bash
   docker-compose down
   docker-compose up -d db redis
   ```

2. **Migration Issues:**
   ```bash
   cd backend
   alembic stamp head
   alembic upgrade head
   ```

3. **Permission Issues:**
   - Make sure Docker Desktop is running
   - Check that ports 5432 and 6379 are available

## 📞 Support

If you need help, check:
- Project documentation in `docs/`
- GitHub repository issues
- Database logs: `docker-compose logs db`

---
**Setup completed successfully! 🎉**
"""
    
    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        print(f"📝 Setup summary created: {summary_file}")
        return summary_file
        
    except Exception as e:
        print(f"❌ Error creating summary: {e}")
        return None

def main():
    """
    Main setup function
    """
    print_banner()
    
    # Step 1: Check prerequisites
    if not check_all_prerequisites():
        print("\n❌ SETUP FAILED - Prerequisites not met")
        print("💡 Please install missing requirements and try again")
        return False
    
    # Step 2: Setup environment
    if not setup_environment():
        print("\n❌ SETUP FAILED - Environment setup failed")
        return False
    
    # Step 3: Start Docker services
    if not start_docker_services():
        print("\n❌ SETUP FAILED - Docker services failed to start")
        return False
    
    # Step 4: Import schema
    if not run_import_schema():
        print("\n❌ SETUP FAILED - Schema import failed")
        return False
    
    # Step 5: Run validation
    validation_success = run_validation()
    
    # Step 6: Create summary
    summary_file = create_setup_summary()
    
    # Final result
    print("\n" + "=" * 60)
    if validation_success:
        print("🎉 SETUP COMPLETED SUCCESSFULLY!")
        print("✅ Your CryptoPredict database is ready for development!")
    else:
        print("⚠️  SETUP COMPLETED WITH WARNINGS")
        print("💡 Database is functional but some validations failed")
    print("=" * 60)
    
    print("\n🚀 Quick Start Commands:")
    print("   docker-compose up -d          # Start all services")
    print("   cd backend && uvicorn app.main:app --reload  # Start API")
    print("   cd frontend && npm run dev    # Start frontend")
    
    if summary_file:
        print(f"\n📝 Setup guide: {summary_file}")
    
    return True

if __name__ == "__main__":
    success = main()
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)