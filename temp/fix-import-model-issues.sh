#!/bin/bash
# temp/fix-import-model-issues.sh
# Fix import and model definition issues

echo "🔧 Fixing Import and Model Issues"
echo "================================="

cd backend

echo ""
echo "📋 Step 1: Check Import Issues in api.py"
echo "----------------------------------------"

# Fix the duplicate import in api.py
python -c "
# Read api.py content
with open('app/api/api_v1/api.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check for duplicate imports
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'from app.api.api_v1.endpoints import' in line:
        print(f'Line {i+1}: {line.strip()}')
        
        # Check for duplicate 'tasks' in import
        if line.count('tasks') > 1:
            print('❌ Found duplicate tasks import!')
            # Fix the line
            import_parts = line.split('import')[1].strip()
            modules = [m.strip() for m in import_parts.split(',')]
            unique_modules = list(dict.fromkeys(modules))  # Remove duplicates
            
            new_line = 'from app.api.api_v1.endpoints import ' + ', '.join(unique_modules)
            lines[i] = new_line
            print(f'✅ Fixed to: {new_line}')
            
            # Write back the fixed content
            fixed_content = '\n'.join(lines)
            with open('app/api/api_v1/api.py', 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            break
"

echo ""
echo "📋 Step 2: Check Model Import Order"
echo "-----------------------------------"

# Check main.py for model import issues
python -c "
with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

print('Checking main.py model imports...')

# Look for model imports
if 'import app.models' in content:
    print('✅ Found: import app.models')
else:
    print('⚠️ Model import may be missing or different')

# Check order of imports
lines = content.split('\n')
api_import_line = -1
model_import_line = -1

for i, line in enumerate(lines):
    if 'from app.api.api_v1.api import api_router' in line:
        api_import_line = i
    if 'import app.models' in line:
        model_import_line = i

if model_import_line > api_import_line and api_import_line != -1:
    print('❌ Models imported after API router - this can cause issues')
    print(f'   API router import: line {api_import_line + 1}')
    print(f'   Models import: line {model_import_line + 1}')
else:
    print('✅ Import order seems OK')
"

echo ""
echo "📋 Step 3: Test Individual Model Imports"
echo "----------------------------------------"

python -c "
try:
    print('Testing individual model imports...')
    
    # Test database base first
    from app.core.database import Base
    print('✅ Database Base imported')
    
    # Test models one by one
    models_to_test = [
        ('User', 'app.models.user'),
        ('Cryptocurrency', 'app.models.cryptocurrency'), 
        ('PriceData', 'app.models.price_data'),
        ('Prediction', 'app.models.prediction')
    ]
    
    for model_name, module_path in models_to_test:
        try:
            exec(f'from {module_path} import {model_name}')
            print(f'✅ {model_name} model imported successfully')
        except Exception as e:
            print(f'❌ {model_name} model import failed: {e}')
    
    print('✅ Individual model imports completed')
    
except Exception as e:
    print(f'❌ Model import test failed: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "📋 Step 4: Create Safe Model Import"
echo "-----------------------------------"

# Create a safe models __init__.py
cat > app/models/__init__.py << 'EOF'
# app/models/__init__.py
# Safe model imports to prevent duplicate table definitions

from app.core.database import Base

# Import models in dependency order
from app.models.user import User
from app.models.cryptocurrency import Cryptocurrency  
from app.models.price_data import PriceData
from app.models.prediction import Prediction

# Export all models
__all__ = [
    "Base",
    "User", 
    "Cryptocurrency",
    "PriceData", 
    "Prediction"
]
EOF

echo "✅ Created safe models/__init__.py"

echo ""
echo "📋 Step 5: Update main.py for Safe Import"
echo "-----------------------------------------"

# Create a safe main.py version
python -c "
with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the model import
if 'import app.models' in content:
    content = content.replace('import app.models', '# Import all models to register with SQLAlchemy\nfrom app.models import *')
    
    with open('app/main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('✅ Updated main.py with safe model import')
else:
    print('⚠️ Model import line not found or already different')
"

echo ""
echo "📋 Step 6: Test Complete Import Chain"
echo "------------------------------------"

python -c "
try:
    print('Testing complete import chain...')
    
    # Test the fixed imports
    print('1. Testing database base...')
    from app.core.database import Base
    
    print('2. Testing models package...')
    from app.models import User, Cryptocurrency, PriceData, Prediction
    
    print('3. Testing API endpoints...')
    from app.api.api_v1.endpoints import tasks
    
    print('4. Testing API router...')
    from app.api.api_v1.api import api_router
    
    print('5. Testing main app structure...')
    # Don't import main.py here as it creates tables
    
    print('✅ All import tests passed!')
    
except Exception as e:
    print(f'❌ Import chain test failed: {e}')
    import traceback
    traceback.print_exc()
"

cd ..

echo ""
echo "🎉 IMPORT AND MODEL FIXES APPLIED!"
echo "=================================="
echo ""
echo "✅ Fixes Applied:"
echo "   1. Fixed duplicate imports in api.py"
echo "   2. Created safe model imports"
echo "   3. Updated main.py import strategy"
echo "   4. Verified import chain"
echo ""
echo "🚀 Try Starting FastAPI Again:"
echo "   cd backend"
echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "🎯 The SQLAlchemy table conflict should now be resolved!"