# File: scripts/sync-db/update_main_dev.py
# Update main.py to support development mode without Alembic

from pathlib import Path
import shutil

def update_main_py():
    """
    Update main.py to check for development mode and create tables directly
    """
    print("🔧 Updating main.py for development mode support...")
    
    project_root = Path(__file__).parent.parent.parent
    main_py_path = project_root / "backend" / "app" / "main.py"
    
    if not main_py_path.exists():
        print("❌ main.py not found!")
        return False
    
    # Create backup
    backup_path = main_py_path.with_suffix('.py.backup')
    shutil.copy2(main_py_path, backup_path)
    print(f"📋 Backup created: {backup_path}")
    
    # Read current content
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already updated
    if "dev_mode_no_alembic" in content:
        print("✅ main.py already supports development mode")
        return True
    
    # Find the imports section
    if "from app.core.database import engine, Base" in content:
        # Add the development mode logic
        dev_mode_code = '''
# Development mode check - auto-create tables without Alembic
from pathlib import Path
import os

# Check if development mode is enabled
dev_mode_file = Path(__file__).parent.parent / ".dev_mode_no_alembic"
if dev_mode_file.exists():
    print("🔧 Development Mode: Creating tables directly from models")
    try:
        # Import all models to ensure they're registered with SQLAlchemy
        from app.models import Base, User, Cryptocurrency, PriceData, Prediction
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created from models (Development Mode)")
    except Exception as e:
        print(f"⚠️  Error creating tables in dev mode: {e}")
else:
    print("🏭 Production Mode: Alembic should handle migrations")

'''
        
        # Find the place to insert the code (after imports, before app creation)
        if "# Import all models to ensure they're registered with SQLAlchemy" in content:
            # Replace existing model import block
            import_start = content.find("# Import all models to ensure they're registered with SQLAlchemy")
            import_end = content.find("Base.metadata.create_all(bind=engine)", import_start)
            if import_end != -1:
                import_end = content.find("\n", import_end) + 1
                content = content[:import_start] + dev_mode_code + content[import_end:]
            else:
                # Just replace the comment
                content = content.replace("# Import all models to ensure they're registered with SQLAlchemy", dev_mode_code)
        else:
            # Find a good place to insert (before app = FastAPI)
            if "app = FastAPI(" in content:
                insertion_point = content.find("app = FastAPI(")
                content = content[:insertion_point] + dev_mode_code + "\n" + content[insertion_point:]
            else:
                print("⚠️  Could not find insertion point in main.py")
                return False
    
        # Write back
        with open(main_py_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ main.py updated successfully")
        print("   - Checks for .dev_mode_no_alembic file")
        print("   - Creates tables directly in development mode") 
        print("   - Falls back to Alembic in production mode")
        
        return True
    else:
        print("❌ Could not find database import in main.py")
        return False

def update_complete_setup():
    """
    Update complete_setup.sh to handle development mode
    """
    print("🔧 Updating complete_setup.sh for development mode...")
    
    project_root = Path(__file__).parent.parent.parent
    setup_script = project_root / "scripts" / "sync-db" / "complete_setup.sh"
    
    if not setup_script.exists():
        print("⚠️  complete_setup.sh not found, skipping")
        return False
    
    # Read current content
    with open(setup_script, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already updated
    if "dev_mode_no_alembic" in content:
        print("✅ complete_setup.sh already supports development mode")
        return True
    
    # Add development mode check
    dev_check = '''
# Check for development mode
check_dev_mode() {
    if [ -f "backend/.dev_mode_no_alembic" ]; then
        echo "development"
    else
        echo "production"
    fi
}

'''
    
    # Insert after the existing functions
    if "check_setup_type()" in content:
        insertion_point = content.find("check_setup_type() {")
        content = content[:insertion_point] + dev_check + content[insertion_point:]
    else:
        # Insert near the beginning
        content = dev_check + content
    
    # Update existing_setup function to handle dev mode
    existing_setup_addition = '''
    # Check for development mode
    dev_mode=$(check_dev_mode)
    if [ "$dev_mode" = "development" ]; then
        print_status "Development mode detected - skipping Alembic"
        print_success "Development mode uses direct model creation"
    else
        # Original Alembic logic here
'''
    
    # Add this check to existing_setup function
    if "# Check current vs head" in content:
        content = content.replace("# Check current vs head", existing_setup_addition + "        # Check current vs head")
    
    # Write back
    with open(setup_script, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ complete_setup.sh updated for development mode")
    return True

def main():
    print("🚀 Development Mode Integration")
    print("=" * 40)
    print("This will update main.py and setup scripts to support development mode")
    print()
    
    response = input("Continue? (y/N): ")
    if response.lower() in ['y', 'yes']:
        success = True
        
        if not update_main_py():
            success = False
        
        if not update_complete_setup():
            success = False
        
        if success:
            print()
            print("✅ Development mode integration complete!")
            print()
            print("🎯 How it works:")
            print("   - If backend/.dev_mode_no_alembic exists → Development Mode")
            print("   - If file doesn't exist → Production Mode (uses Alembic)")
            print()
            print("🔄 Usage:")
            print("   python scripts/sync-db/disable_alembic_dev.py  # Enable dev mode")
            print("   rm backend/.dev_mode_no_alembic               # Disable dev mode")
        else:
            print("❌ Some updates failed!")
    else:
        print("❌ Update cancelled")

if __name__ == "__main__":
    main()