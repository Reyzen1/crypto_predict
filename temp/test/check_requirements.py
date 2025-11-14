#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requirements Check Script

Check if all required packages are installed for Bitcoin data testing.
This script verifies Python version, virtual environment, packages, and database connection.
"""

import sys
import importlib
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def check_requirements():
    """Check project requirements and dependencies"""
    
    print("🔍 Checking requirements...")
    print("=" * 40)
    
    # Check Python version
    python_version = sys.version_info
    print(f"🐍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print("❌ Python version must be 3.8 or higher")
        return False
    else:
        print("✅ Python version is suitable")
    
    # Check virtual environment
    venv_active = sys.prefix != sys.base_prefix
    print(f"🔧 Virtual environment: {'✅ Active' if venv_active else '❌ Inactive'}")
    
    if not venv_active:
        print("⚠️  Recommendation: Activate virtual environment")
        print("   Windows: backend\\venv\\Scripts\\activate")
        print("   Linux/Mac: source backend/venv/bin/activate")
    
    # Required packages
    required_packages = [
        ('sqlalchemy', 'SQLAlchemy'),
        ('psycopg2', 'PostgreSQL adapter'),
        ('httpx', 'HTTP client'),
        ('pydantic', 'Data validation'),
        ('fastapi', 'FastAPI framework'),
        ('alembic', 'Database migrations'),
    ]
    
    print("\n📦 Checking packages:")
    all_good = True
    
    for package, description in required_packages:
        try:
            importlib.import_module(package)
            print(f"   ✅ {package} ({description})")
        except ImportError:
            print(f"   ❌ {package} ({description}) - Not installed")
            all_good = False
    
    # Check project files
    print("\n📁 Checking project files:")
    
    project_files = [
        '../../backend/app/services/price_data_service.py',
        '../../backend/app/repositories/asset/asset_repository.py',
        '../../backend/app/core/database.py',
        '../../backend/requirements.txt'
    ]
    
    for file_path in project_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - File not found")
            all_good = False
    
    # Check database connection (if possible)
    print("\n🗄️  Checking database connection:")
    try:
        # Check if we can create a basic database URL and connection
        # This avoids importing the app's modules which may have circular dependencies
        from sqlalchemy import create_engine
        
        # Try to read database URL from environment or config
        import os
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            # Try to load from .env file
            env_path = Path('../../backend/.env')
            if env_path.exists():
                with open(env_path, 'r') as f:
                    for line in f:
                        if line.strip().startswith('DATABASE_URL='):
                            db_url = line.strip().split('=', 1)[1].strip('"\'')
                            break
        
        if db_url:
            print(f"   ✅ Database URL: {db_url[:50]}...")
            
            # Try to test connection
            engine = create_engine(db_url)
            with engine.connect() as conn:
                print("   ✅ Database connection successful")
            engine.dispose()
        else:
            print("   ⚠️  Database URL not found in environment")
            print("   💡 Make sure DATABASE_URL is set in .env file")
        
    except ImportError as e:
        print(f"   ❌ Missing dependencies for database connection: {e}")
        print("   💡 This is expected if packages are not installed yet")
        # Don't mark as failure since this is expected without venv
        
    except Exception as e:
        print(f"   ❌ Database connection issue: {e}")
        print(f"   💡 This might be due to database not running or incorrect credentials")
    
    print("\n" + "=" * 40)
    
    if all_good:
        print("🎉 All requirements are ready!")
        print("✅ You can run the test scripts")
        return True
    else:
        print("❌ Some requirements are incomplete")
        print("\n🔧 Suggested solutions:")
        print("1. Activate virtual environment")
        print("2. Install dependencies: pip install -r backend/requirements.txt")
        print("3. Check database settings")
        print("4. Check environment variables")
        return False

def main():
    """Main function to run requirements check"""
    print("Requirements Check Script")
    print("Bitcoin Data Testing Prerequisites")
    print("=" * 40)
    
    success = check_requirements()
    
    if success:
        print("\n🚀 Ready to run tests:")
        print("   python quick_bitcoin_test.py")
        print("   python test_bitcoin_update.py")
    else:
        print("\n⚠️  Please fix the issues first")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())