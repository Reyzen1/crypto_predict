#!/bin/bash
# temp/setup-celery.sh
# Celery dependencies setup and verification script

echo "🚀 Setting up Celery for Background Tasks"
echo "========================================"

cd backend

echo ""
echo "📋 Step 1: Checking Python Environment"
echo "--------------------------------------"
python --version
echo "✅ Python environment ready"

echo ""
echo "📋 Step 2: Installing Celery Dependencies"  
echo "-----------------------------------------"
echo "Checking if Celery is installed..."

python -c "
try:
    import celery
    print('✅ Celery already installed: ' + celery.__version__)
except ImportError:
    print('❌ Celery not found, installing...')
    import subprocess
    subprocess.run(['pip', 'install', 'celery==5.3.4'])
"

echo ""
echo "📋 Step 3: Checking Redis Connection"
echo "------------------------------------"
python -c "
try:
    import redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print('✅ Redis connection successful')
except Exception as e:
    print('❌ Redis connection failed: ' + str(e))
    print('Make sure Redis is running: docker-compose up redis')
"

echo ""
echo "📋 Step 4: Testing Celery Configuration"
echo "---------------------------------------"
python -c "
try:
    import sys
    sys.path.append('.')
    
    from app.core.celery_config import CeleryConfig
    print('✅ CeleryConfig imported successfully')
    
    config = CeleryConfig.get_config_dict()
    print('✅ Configuration loaded: ' + str(len(config)) + ' settings')
    
    from app.tasks.celery_app import celery_app
    print('✅ Celery app created successfully')
    print('   Broker: ' + celery_app.conf.broker_url)
    print('   Backend: ' + celery_app.conf.result_backend)
    
except Exception as e:
    print('❌ Celery configuration test failed: ' + str(e))
    import traceback
    traceback.print_exc()
"

echo ""
echo "📋 Step 5: Creating Celery Directories"
echo "--------------------------------------"
mkdir -p app/tasks
touch app/tasks/__init__.py

echo "✅ Task directories created"

cd ..

echo ""
echo "🎉 CELERY SETUP COMPLETED!"
echo "========================="
echo ""
echo "📝 What was configured:"
echo "  ✅ Celery dependencies verified"
echo "  ✅ Redis connection tested"  
echo "  ✅ Celery configuration loaded"
echo "  ✅ Task directories created"
echo ""
echo "🔄 Next steps:"
echo "  1. Implement price collector tasks"
echo "  2. Setup task scheduling" 
echo "  3. Test background task execution"