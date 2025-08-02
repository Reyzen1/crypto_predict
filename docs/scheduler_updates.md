# تغییرات برای فایل: backend/app/tasks/scheduler.py
# اضافه کردن ML tasks به scheduler

# =====================================
# 1. اضافه کردن imports در ابتدای فایل:
# =====================================

# بعد از خط:
from app.tasks.price_collector import (
    sync_all_prices,
    sync_historical_data,
    discover_new_cryptocurrencies,
    cleanup_old_data
)

# این خطوط را اضافه کنید:
# Import ML tasks
from app.tasks.ml_tasks import (
    auto_train_models,
    generate_scheduled_predictions,
    evaluate_model_performance,
    cleanup_old_predictions
)

# =====================================
# 2. بروزرسانی task_scheduler.conf در setup_periodic_tasks:
# =====================================

# بعد از block موجود cleanup_old_data، این block را اضافه کنید:

    # ============= ML TASKS =============
    
    # Auto train models - Weekly on Sunday at 1:00 AM
    task_scheduler.add_periodic_task(
        crontab(hour=1, minute=0, day_of_week=0),  # Sunday 1:00 AM
        auto_train_models.s(force_retrain=False),
        name='auto-train-models-weekly',
    )
    
    # Generate scheduled predictions - Every 4 hours
    task_scheduler.add_periodic_task(
        crontab(minute=0, hour='*/4'),  # Every 4 hours at minute 0
        generate_scheduled_predictions.s(),
        name='generate-predictions-4hourly',
    )
    
    # Evaluate model performance - Daily at 6:00 AM
    task_scheduler.add_periodic_task(
        crontab(hour=6, minute=0),  # Every day at 6:00 AM
        evaluate_model_performance.s(),
        name='evaluate-model-performance-daily',
    )
    
    # Cleanup old predictions - Weekly on Sunday at 4:00 AM
    task_scheduler.add_periodic_task(
        crontab(hour=4, minute=0, day_of_week=0),  # Sunday 4:00 AM
        cleanup_old_predictions.s(days_to_keep=90),
        name='cleanup-old-predictions-weekly',
    )

# =====================================
# 3. بروزرسانی get_next_run_times function:
# =====================================

# در function get_next_run_times، بعد از block موجود، این خطوط را اضافه کنید:

        # ML Tasks
        "auto-train-models-weekly": _get_next_cron_run(1, 0, day_of_week=0),
        "generate-predictions-4hourly": _get_next_cron_run(minute=0, hour_interval=4),
        "evaluate-model-performance-daily": _get_next_cron_run(6, 0),
        "cleanup-old-predictions-weekly": _get_next_cron_run(4, 0, day_of_week=0),

# =====================================
# 4. اضافه کردن helper function برای hour intervals:
# =====================================

# بعد از function _get_next_cron_run موجود، این function را اضافه کنید:

def _get_next_cron_run_interval(hour_interval: int, minute: int = 0) -> str:
    """
    Calculate next run time for interval-based cron jobs
    """
    try:
        now = datetime.now(timezone.utc)
        
        # Find the next hour that's divisible by the interval
        next_hour = ((now.hour // hour_interval) + 1) * hour_interval
        
        if next_hour >= 24:
            # Next day
            next_run = now.replace(hour=0, minute=minute, second=0, microsecond=0) + timedelta(days=1)
        else:
            next_run = now.replace(hour=next_hour, minute=minute, second=0, microsecond=0)
        
        return next_run.isoformat()
    except Exception as e:
        logger.error(f"Error calculating next interval run time: {str(e)}")
        return "Unknown"

# =====================================
# 5. بروزرسانی task documentation:
# =====================================

# در function get_task_info، در قسمت available_tasks، این items را اضافه کنید:

            # بعد از cleanup_old_data block:
            "auto_train_models": {
                "description": "Automatically train ML models for all cryptocurrencies",
                "schedule": "Weekly on Sunday at 1:00 AM",
                "type": "periodic",
                "estimated_duration": "30-120 minutes",
                "dependencies": ["Database", "Model Storage", "Price Data"]
            },
            "generate_scheduled_predictions": {
                "description": "Generate predictions for all active cryptocurrencies",
                "schedule": "Every 4 hours",
                "type": "periodic", 
                "estimated_duration": "5-15 minutes",
                "dependencies": ["Trained Models", "Database", "Price Data"]
            },
            "evaluate_model_performance": {
                "description": "Evaluate accuracy and performance of prediction models",
                "schedule": "Daily at 6:00 AM",
                "type": "periodic",
                "estimated_duration": "10-30 minutes", 
                "dependencies": ["Database", "Realized Predictions"]
            },
            "cleanup_old_predictions": {
                "description": "Clean up old prediction data to manage database size",
                "schedule": "Weekly on Sunday at 4:00 AM",
                "type": "periodic",
                "estimated_duration": "5-15 minutes",
                "dependencies": ["Database"]
            }

# =====================================
# 6. بروزرسانی startup_commands:
# =====================================

# در قسمت startup_commands، بعد از flower_monitoring، این خطوط را اضافه کنید:

            "ml_worker_only": "celery -A app.tasks.celery_app worker --loglevel=info --queues=ml_tasks",
            "combined_worker": "celery -A app.tasks.celery_app worker --loglevel=info --queues=price_data,ml_tasks"