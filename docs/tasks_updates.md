# تغییرات برای فایل: backend/app/api/api_v1/endpoints/tasks.py
# اضافه کردن ML tasks به task management endpoints

# =====================================
# 1. اضافه کردن imports در ابتدای فایل:
# =====================================

# بعد از existing imports، این خطوط را اضافه کنید:
from app.tasks.ml_tasks import (
    start_auto_training,
    start_prediction_generation,
    start_performance_evaluation,
    start_prediction_cleanup,
    get_task_status as get_ml_task_status
)

# =====================================
# 2. اضافه کردن ML task endpoints:
# =====================================

# این endpoints را در انتهای فایل قبل از آخرین endpoint اضافه کنید:

@router.post("/ml/auto-train", operation_id="start_ml_auto_training")
async def start_ml_auto_training(
    force_retrain: bool = False,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Start automatic model training for all cryptocurrencies
    
    Requires authentication. Trains ML models for all active cryptocurrencies.
    """
    try:
        logger.info(f"User {current_user.id} starting auto ML training (force_retrain: {force_retrain})")
        
        # Start the training task
        task_id = start_auto_training(force_retrain=force_retrain)
        
        return {
            "success": True,
            "message": "Auto training task started successfully",
            "task_id": task_id,
            "task_type": "auto_train_models",
            "force_retrain": force_retrain,
            "status_endpoint": f"/api/v1/tasks/ml/status/{task_id}",
            "estimated_duration": "30-120 minutes",
            "started_by": current_user.email,
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start auto training: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start auto training: {str(e)}"
        )


@router.post("/ml/predictions/generate", operation_id="start_ml_prediction_generation")
async def start_ml_prediction_generation(
    crypto_symbols: Optional[List[str]] = None,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Start scheduled prediction generation
    
    Requires authentication. Generates predictions for specified or all cryptocurrencies.
    """
    try:
        logger.info(f"User {current_user.id} starting prediction generation for: {crypto_symbols or 'all cryptocurrencies'}")
        
        # Start the prediction task
        task_id = start_prediction_generation(crypto_symbols=crypto_symbols)
        
        return {
            "success": True,
            "message": "Prediction generation task started successfully", 
            "task_id": task_id,
            "task_type": "generate_scheduled_predictions",
            "crypto_symbols": crypto_symbols or "all",
            "status_endpoint": f"/api/v1/tasks/ml/status/{task_id}",
            "estimated_duration": "5-15 minutes",
            "started_by": current_user.email,
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start prediction generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start prediction generation: {str(e)}"
        )


@router.post("/ml/performance/evaluate", operation_id="start_ml_performance_evaluation")
async def start_ml_performance_evaluation(
    crypto_symbol: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Start model performance evaluation
    
    Requires authentication. Evaluates model accuracy and performance metrics.
    """
    try:
        logger.info(f"User {current_user.id} starting performance evaluation for: {crypto_symbol or 'all cryptocurrencies'}")
        
        # Start the evaluation task
        task_id = start_performance_evaluation(crypto_symbol=crypto_symbol)
        
        return {
            "success": True,
            "message": "Performance evaluation task started successfully",
            "task_id": task_id,
            "task_type": "evaluate_model_performance",
            "crypto_symbol": crypto_symbol or "all",
            "status_endpoint": f"/api/v1/tasks/ml/status/{task_id}",
            "estimated_duration": "10-30 minutes",
            "started_by": current_user.email,
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start performance evaluation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start performance evaluation: {str(e)}"
        )


@router.post("/ml/cleanup", operation_id="start_ml_prediction_cleanup")
async def start_ml_prediction_cleanup(
    days_to_keep: int = 90,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Start prediction data cleanup
    
    Requires authentication. Cleans up old prediction data to manage database size.
    """
    try:
        if days_to_keep < 7 or days_to_keep > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="days_to_keep must be between 7 and 365"
            )
        
        logger.info(f"User {current_user.id} starting prediction cleanup (keeping {days_to_keep} days)")
        
        # Start the cleanup task
        task_id = start_prediction_cleanup(days_to_keep=days_to_keep)
        
        return {
            "success": True,
            "message": "Prediction cleanup task started successfully",
            "task_id": task_id,
            "task_type": "cleanup_old_predictions",
            "days_to_keep": days_to_keep,
            "status_endpoint": f"/api/v1/tasks/ml/status/{task_id}",
            "estimated_duration": "5-15 minutes",
            "started_by": current_user.email,
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start prediction cleanup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start prediction cleanup: {str(e)}"
        )


@router.get("/ml/status/{task_id}", operation_id="get_ml_task_status")
async def get_ml_task_status_endpoint(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get status of ML task
    
    Requires authentication. Returns detailed status of ML background tasks.
    """
    try:
        # Get task status
        task_status = get_ml_task_status(task_id)
        
        return {
            "success": True,
            "task_status": task_status,
            "requested_by": current_user.email,
            "requested_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get ML task status {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )


# =====================================
# 3. بروزرسانی get_task_info function:
# =====================================

# در function get_task_info، در قسمت management_endpoints، این خطوط را اضافه کنید:

            # بعد از existing endpoints:
            "ml_auto_train": "POST /api/v1/tasks/ml/auto-train",
            "ml_generate_predictions": "POST /api/v1/tasks/ml/predictions/generate", 
            "ml_evaluate_performance": "POST /api/v1/tasks/ml/performance/evaluate",
            "ml_cleanup_predictions": "POST /api/v1/tasks/ml/cleanup",
            "ml_task_status": "GET /api/v1/tasks/ml/status/{task_id}",

# =====================================
# 4. بروزرسانی available_tasks در get_task_info:
# =====================================

# در قسمت available_tasks، این items را اضافه کنید:

            # بعد از existing tasks:
            "auto_train_models": {
                "description": "Automatically train ML models for all cryptocurrencies",
                "endpoint": "/api/v1/tasks/ml/auto-train",
                "method": "POST",
                "schedule": "Weekly on Sunday at 1:00 AM",
                "type": "periodic/manual",
                "estimated_duration": "30-120 minutes",
                "dependencies": ["Database", "Model Storage", "Price Data"],
                "parameters": {
                    "force_retrain": "boolean - Force retrain even if models are recent"
                }
            },
            "generate_scheduled_predictions": {
                "description": "Generate predictions for all active cryptocurrencies",
                "endpoint": "/api/v1/tasks/ml/predictions/generate",
                "method": "POST", 
                "schedule": "Every 4 hours",
                "type": "periodic/manual",
                "estimated_duration": "5-15 minutes",
                "dependencies": ["Trained Models", "Database", "Price Data"],
                "parameters": {
                    "crypto_symbols": "array - Specific cryptocurrencies or null for all"
                }
            },
            "evaluate_model_performance": {
                "description": "Evaluate accuracy and performance of prediction models",
                "endpoint": "/api/v1/tasks/ml/performance/evaluate",
                "method": "POST",
                "schedule": "Daily at 6:00 AM", 
                "type": "periodic/manual",
                "estimated_duration": "10-30 minutes",
                "dependencies": ["Database", "Realized Predictions"],
                "parameters": {
                    "crypto_symbol": "string - Specific cryptocurrency or null for all"
                }
            },
            "cleanup_old_predictions": {
                "description": "Clean up old prediction data to manage database size",
                "endpoint": "/api/v1/tasks/ml/cleanup",
                "method": "POST",
                "schedule": "Weekly on Sunday at 4:00 AM",
                "type": "periodic/manual", 
                "estimated_duration": "5-15 minutes",
                "dependencies": ["Database"],
                "parameters": {
                    "days_to_keep": "integer - Days of data to retain (7-365)"
                }
            }