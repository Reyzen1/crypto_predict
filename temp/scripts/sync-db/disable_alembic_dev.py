# File: scripts/sync-db/disable_alembic_dev.py
# Disable Alembic for development and use direct SQLAlchemy model creation

import os
import sys
from pathlib import Path

# Add backend to path
project_root = Path(__file__).parent.parent.parent
backend_dir = project_root / "backend"
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from app.core.config import get_settings
from app.core.database import Base

def disable_alembic_dev_mode():
    """
    Disable Alembic and use direct SQLAlchemy model creation for development
    """
    print("🔧 Setting up Development Mode (No Alembic)")
    print("=" * 50)
    
    try:
        # Find and start containers first
        print("🐳 Starting database containers...")
        
        # Find compose file
        project_root = Path(__file__).parent.parent.parent
        
        if (project_root / "docker-compose-backend.yml").exists():
            compose_file = "docker-compose-backend.yml"
        elif (project_root / "docker-compose.yml").exists():
            compose_file = "docker-compose.yml"
        else:
            print("❌ No docker-compose file found!")
            return False
        
        print(f"   Using: {compose_file}")
        
        # Start containers
        import subprocess
        os.chdir(project_root)
        
        # Start postgres and redis
        result = subprocess.run([
            "docker-compose", "-f", compose_file, "up", "-d", "postgres", "redis"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Failed to start containers: {result.stderr}")
            return False
        
        print("✅ Containers started")
        
        # Wait for PostgreSQL to be ready
        print("⏳ Waiting for PostgreSQL to be ready...")
        import time
        for i in range(30):
            try:
                result = subprocess.run([
                    "docker-compose", "-f", compose_file, "exec", "-T", "postgres", 
                    "pg_isready", "-U", "postgres"
                ], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    print("✅ PostgreSQL is ready")
                    break
                    
            except subprocess.TimeoutExpired:
                pass
            
            if i >= 29:
                print("⚠️  PostgreSQL may not be fully ready, but continuing...")
                break
                
            time.sleep(2)
        
        # Additional wait to be sure
        time.sleep(5)
        
        # Get database configuration
        settings = get_settings()
        engine = create_engine(settings.DATABASE_URL)
        
        print("📋 Development Mode Features:")
        print("   ✅ Direct model creation (no migrations)")
        print("   ✅ Easy schema changes")
        print("   ✅ No migration conflicts")
        print("   ✅ Perfect for rapid development")
        print()
        
        # Drop all tables and recreate from models
        print("🗑️ Dropping all existing tables...")
        Base.metadata.drop_all(bind=engine)
        
        print("🏗️ Creating tables from current models...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database recreated from models!")
        print()
        
        # Create a marker file to indicate dev mode
        dev_mode_file = backend_dir / ".dev_mode_no_alembic"
        with open(dev_mode_file, "w") as f:
            f.write("Development mode active - Alembic disabled\n")
            f.write("Tables created directly from SQLAlchemy models\n")
            f.write("To re-enable Alembic, delete this file and run: alembic stamp head\n")
        
        print("📝 Created development mode marker file")
        print(f"   File: {dev_mode_file}")
        print()
        
        print("💡 Development Mode Active!")
        print("   - Change models freely")
        print("   - Run this script again after model changes")
        print("   - No migration files needed")
        print()
        print("🔄 To re-enable Alembic later:")
        print("   1. Delete backend/.dev_mode_no_alembic")
        print("   2. Run: alembic stamp head")
        print("   3. Create migrations normally")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def update_main_py():
    """
    Update main.py to create tables directly in dev mode
    """
    print("🔧 Updating main.py for development mode...")
    
    main_py_path = Path(__file__).parent.parent.parent / "backend" / "app" / "main.py"
    
    if not main_py_path.exists():
        print("⚠️  main.py not found, skipping update")
        return
    
    # Read current content
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add dev mode check
    dev_mode_code = '''
# Development mode check - auto-create tables without Alembic
import os
from pathlib import Path

dev_mode_file = Path(__file__).parent.parent / ".dev_mode_no_alembic"
if dev_mode_file.exists():
    # Development mode: create tables directly
    print("🔧 Development Mode: Creating tables directly from models")
    Base.metadata.create_all(bind=engine)
else:
    # Production mode: would use Alembic migrations
    print("🏭 Production Mode: Using Alembic migrations")
'''
    
    # Replace the existing table creation line
    if "Base.metadata.create_all(bind=engine)" in content:
        content = content.replace("Base.metadata.create_all(bind=engine)", dev_mode_code)
    else:
        # Add before app = FastAPI
        content = content.replace("app = FastAPI(", dev_mode_code + "\napp = FastAPI(")
    
    # Write back
    with open(main_py_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ main.py updated for development mode")

def create_dev_workflow_script():
    """
    Create a simple script for development workflow
    """
    workflow_script = '''#!/bin/bash
# File: scripts/sync-db/dev_reset_db.sh
# Quick database reset for development

echo "🔄 Development Database Reset"
echo "============================"

# Stop containers
docker-compose -f docker-compose-backend.yml down

# Remove database volume
docker volume rm cryptopredict_postgres_data 2>/dev/null || true

# Create fresh volume
docker volume create cryptopredict_postgres_data

# Start containers
docker-compose -f docker-compose-backend.yml up -d postgres redis

# Wait for PostgreSQL
echo "⏳ Waiting for PostgreSQL..."
sleep 10

# Reset database from models
python scripts/sync-db/disable_alembic_dev.py

# Add seed data
python scripts/sync-db/seed_data.py

echo "✅ Development database reset complete!"
echo "🚀 Start backend: cd backend && uvicorn app.main:app --reload"
'''
    
    script_path = Path(__file__).parent / "dev_reset_db.sh"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(workflow_script)
    
    # Make executable
    os.chmod(script_path, 0o755)
    
    print(f"✅ Created development workflow script: {script_path}")

if __name__ == "__main__":
    print("🚀 CryptoPredict Development Mode Setup")
    print("=" * 50)
    print("⚠️  This will disable Alembic and use direct model creation")
    print("   Perfect for rapid development with frequent schema changes")
    print()
    
    response = input("Continue? (y/N): ")
    if response.lower() in ['y', 'yes']:
        if disable_alembic_dev_mode():
            create_dev_workflow_script()
            print()
            print("🎉 Development mode setup complete!")
        else:
            print("❌ Setup failed!")
    else:
        print("❌ Setup cancelled")