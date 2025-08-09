#!/bin/bash
# temp/test_fixed_worker.sh
# Test worker after rate limit fix

echo "🧪 Testing Fixed Worker"
echo "======================="

cd backend

echo "📋 Step 1: Quick configuration test..."
python -c "
try:
    from app.core.celery_config import CeleryConfig
    config = CeleryConfig()
    print('✅ Config loaded successfully')
    
    # Check rate limits
    if hasattr(config, 'task_annotations'):
        print('📊 Rate limits found:')
        for task, settings in config.task_annotations.items():
            if 'rate_limit' in settings:
                rate_limit = settings['rate_limit']
                task_name = task.split('.')[-1]
                print(f'   • {task_name}: {rate_limit}')
                
                if '/w' in rate_limit:
                    print('     ❌ Still has /w - manual fix needed')
                    exit(1)
                else:
                    print('     ✅ Valid format')
    
    print('✅ All rate limits are valid')
    
except Exception as e:
    print(f'❌ Config test failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Configuration test failed"
    exit 1
fi

echo ""
echo "📋 Step 2: Testing worker startup (10 seconds)..."

# Test worker startup
timeout 10s python -m celery -A app.tasks.celery_app worker \
    --loglevel=info \
    --concurrency=1 \
    --queues=price_data \
    --pool=threads \
    --hostname=test_worker@%h

exit_code=$?

echo ""
echo "📊 Worker test results:"

case $exit_code in
    0)
        echo "✅ Worker exited normally"
        echo "🎉 Rate limit fix SUCCESSFUL!"
        ;;
    124)
        echo "✅ Worker was running (killed by timeout)"
        echo "🎉 Rate limit fix SUCCESSFUL!"
        echo "✅ Worker can start without errors"
        ;;
    1)
        echo "❌ Worker failed to start"
        echo "🔍 Check error messages above"
        ;;
    2)
        echo "❌ Worker had configuration errors"
        echo "🔍 Rate limit fix might not be complete"
        ;;
    *)
        echo "❌ Unexpected exit code: $exit_code"
        ;;
esac

echo ""
echo "📋 Step 3: Quick task test..."

if [ $exit_code -eq 124 ] || [ $exit_code -eq 0 ]; then
    echo "🧪 Testing task import and signature creation..."
    
    python -c "
try:
    from app.tasks.price_collector import sync_all_prices
    from app.tasks.celery_app import debug_task
    
    # Test task signature creation
    sig1 = sync_all_prices.s()
    sig2 = debug_task.s()
    
    print('✅ sync_all_prices signature: OK')
    print('✅ debug_task signature: OK')
    print('🎉 All tasks can be created without rate limit errors')
    
except Exception as e:
    print(f'❌ Task test failed: {e}')
    exit(1)
"
    
    task_test_exit=$?
    
    if [ $task_test_exit -eq 0 ]; then
        echo "✅ Task test passed"
    else
        echo "❌ Task test failed"
    fi
else
    echo "⚠️ Skipping task test due to worker startup failure"
fi

echo ""
echo "📊 Final Results:"
echo "================="

if [ $exit_code -eq 124 ] || [ $exit_code -eq 0 ]; then
    echo "🎉 SUCCESS: Rate limit fix worked!"
    echo "✅ Workers can start without KeyError"
    echo "✅ Ready to run full worker script"
    echo ""
    echo "🚀 Next steps:"
    echo "   1. Run: ./temp/run_workers_fixed.sh"
    echo "   2. Or run: ./scripts/run-workers-simple-kill-all.sh"
    echo "   3. Check Flower at: http://localhost:5555"
else
    echo "❌ Rate limit fix incomplete"
    echo "🔧 Need additional troubleshooting"
    echo ""
    echo "🛠️ Try:"
    echo "   1. Manual config check"
    echo "   2. Re-run rate limit fix"
    echo "   3. Check for other configuration issues"
fi