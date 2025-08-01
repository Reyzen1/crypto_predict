# File: temp/fix-deps-logger.py
# Fix deps.py logger issue and authentication schema

import os
import re

def fix_deps_logger():
    """Fix logger import in deps.py"""
    
    deps_file = "backend/app/core/deps.py"
    
    if not os.path.exists(deps_file):
        print("❌ deps.py file not found")
        return False
    
    print("🔧 Fixing logger import in deps.py...")
    
    with open(deps_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add logger import if not present
    if 'import logging' not in content:
        # Add import after other imports
        import_section = content.split('\n')
        new_imports = []
        
        for i, line in enumerate(import_section):
            new_imports.append(line)
            # Add logging import after jose import
            if 'from jose import' in line:
                new_imports.append('import logging')
                break
        
        # Reconstruct file
        remaining_lines = import_section[i+1:]
        content = '\n'.join(new_imports + remaining_lines)
    
    # Add logger definition if not present
    if 'logger = logging.getLogger(__name__)' not in content:
        # Find where to add logger
        lines = content.split('\n')
        new_lines = []
        
        for i, line in enumerate(lines):
            if 'security = HTTPBearer(auto_error=False)' in line:
                new_lines.append(line)
                new_lines.append('')
                new_lines.append('# Logger for authentication')
                new_lines.append('logger = logging.getLogger(__name__)')
            else:
                new_lines.append(line)
        
        content = '\n'.join(new_lines)
    
    # Write back the fixed content
    with open(deps_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed logger import in deps.py")
    return True

def check_auth_schemas():
    """Check authentication schemas"""
    
    auth_endpoints = "backend/app/api/api_v1/endpoints/auth.py"
    user_schemas = "backend/app/schemas/user.py"
    
    print("\n🔍 Checking authentication schemas...")
    
    issues = []
    
    # Check if files exist
    if not os.path.exists(auth_endpoints):
        issues.append("auth.py endpoint file missing")
    if not os.path.exists(user_schemas):
        issues.append("user.py schema file missing")
    
    if issues:
        print("❌ Schema issues found:")
        for issue in issues:
            print(f"   • {issue}")
        return False
    
    # Check auth.py for login endpoint
    with open(auth_endpoints, 'r', encoding='utf-8') as f:
        auth_content = f.read()
    
    # Check for common issues
    if 'username' in auth_content and 'email' in auth_content:
        print("⚠️  Mixed username/email fields detected in auth.py")
        issues.append("Mixed username/email fields")
    
    # Check user schemas
    with open(user_schemas, 'r', encoding='utf-8') as f:
        schema_content = f.read()
    
    if 'class UserLogin' not in schema_content:
        print("⚠️  UserLogin schema not found")
        issues.append("UserLogin schema missing")
    
    if issues:
        return False
    
    print("✅ Authentication schemas look good")
    return True

def fix_auth_login_schema():
    """Fix login schema to use email instead of username"""
    
    print("\n🔧 Checking login schema...")
    
    # Check current UserLogin schema
    schema_file = "backend/app/schemas/user.py"
    
    if not os.path.exists(schema_file):
        print("❌ user.py schema file not found")
        return False
    
    with open(schema_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for UserLogin class
    if 'class UserLogin' in content:
        print("✅ UserLogin schema found")
        
        # Check if it uses email or username
        if 'username:' in content and 'email:' not in content:
            print("⚠️  UserLogin uses 'username' field")
            print("🔧 Schema should use 'email' field for consistency")
            
            # Show current schema
            lines = content.split('\n')
            in_userlogin = False
            for line in lines:
                if 'class UserLogin' in line:
                    in_userlogin = True
                    print(f"Found: {line}")
                elif in_userlogin and line.strip().startswith('class '):
                    break
                elif in_userlogin and line.strip():
                    print(f"  {line}")
            
            return False
        else:
            print("✅ UserLogin schema uses email field")
            return True
    else:
        print("❌ UserLogin schema not found")
        return False

def show_swagger_login_help():
    """Show help for using Swagger UI login"""
    
    print("\n💡 How to use Swagger UI for login:")
    print("=" * 40)
    print("1. Start backend: ./start-backend-local.sh")
    print("2. Go to: http://localhost:8000/docs")
    print("3. First register a user:")
    print("   • Find 'POST /api/v1/auth/register'")
    print("   • Click 'Try it out'")
    print("   • Enter user data:")
    print("     {")
    print('       "email": "testuser2@example.com",')
    print('       "password": "password123",')
    print('       "first_name": "Test",')
    print('       "last_name": "User"')
    print("     }")
    print("   • Execute")
    print()
    print("4. Then login:")
    print("   • Find 'POST /api/v1/auth/login'")
    print("   • Click 'Try it out'")
    print("   • Enter credentials:")
    print("     {")
    print('       "email": "testuser2@example.com",')
    print('       "password": "password123"')
    print("     }")
    print("   • Execute")
    print("   • Copy the 'access_token' from response")
    print()
    print("5. Authorize for other endpoints:")
    print("   • Click 'Authorize' button at top")
    print("   • Enter: Bearer YOUR_ACCESS_TOKEN")
    print("   • Click 'Authorize'")
    print()
    print("6. Now you can use protected endpoints like:")
    print("   • POST /api/v1/external/sync/prices")

def main():
    """Main fix function"""
    
    print("🔧 Authentication & Logger Fixer")
    print("===============================")
    
    # Fix 1: Logger import
    logger_fixed = fix_deps_logger()
    
    # Fix 2: Check schemas
    schemas_ok = check_auth_schemas()
    
    # Fix 3: Check login schema specifically
    login_schema_ok = fix_auth_login_schema()
    
    print("\n📊 Fix Results:")
    print("===============")
    print(f"   {'✅' if logger_fixed else '❌'} Logger import fixed")
    print(f"   {'✅' if schemas_ok else '❌'} Auth schemas checked")
    print(f"   {'✅' if login_schema_ok else '❌'} Login schema correct")
    
    if logger_fixed and schemas_ok and login_schema_ok:
        print("\n🎉 All fixes applied successfully!")
        print("\nNext steps:")
        print("1. Restart backend: ./start-backend-local.sh")
        print("2. Test authentication in Swagger UI")
        print("3. Sync price data for BTC")
        
        show_swagger_login_help()
    else:
        print("\n⚠️  Some issues need manual attention:")
        if not logger_fixed:
            print("   • Check backend/app/core/deps.py manually")
        if not schemas_ok or not login_schema_ok:
            print("   • Check authentication schema files")
            print("   • Ensure UserLogin uses 'email' not 'username'")

if __name__ == "__main__":
    main()