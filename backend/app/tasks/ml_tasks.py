# File: backend/app/tasks/ml_tasks.py
# Background tasks for ML operations - Fixed async/await issues
# Based on price_collector.py pattern with Celery compatibility

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from celery import current_task

# Import existing infrastructure
from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.config import settings

# Import ML services and repositories
from app.ml.training.training_service import training_service
from app.ml.prediction.prediction_service import prediction_service
from app.ml.config.ml_config import model_registry, ml_config
from app.repositories import (
    cryptocurrency_repository,
    price_data_repository,
    prediction_repository
)

# Setup logging
logger = logging.getLogger(__name__)


# =====================================
# HELPER FUNCTIONS FOR ASYNC OPERATIONS
# =====================================

def run_async_task(coro):
    """
    Helper function to run async operations in Celery tasks
    
    Since Celery tasks cannot be async, we use this helper to run
    async operations synchronously within Celery workers.
    """
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, create a new one
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            # If no loop is running, use asyncio.run
            return asyncio.run(coro)
    except RuntimeError:
        # If no event loop exists, create one
        return asyncio.run(coro)


async def _async_check_training_needed(crypto_symbol: str, force_retrain: bool = False) -> bool:
    """
    Async helper to check if model training is needed for a cryptocurrency
    
    Args:
        crypto_symbol: Cryptocurrency symbol to check
        force_retrain: Force retrain even if model exists
        
    Returns:
        bool: True if training is needed, False otherwise
    """
    if force_retrain:
        return True
    
    try:
        # Check if active model exists
        active_model = model_registry.get_active_model(crypto_symbol)
        if not active_model:
            logger.info(f"No active model found for {crypto_symbol}, training needed")
            return True
        
        # Check model age (retrain if older than 7 days)
        model_created = active_model.get("created_at")
        if model_created:
            if isinstance(model_created, str):
                model_created = datetime.fromisoformat(model_created.replace('Z', '+00:00'))
            
            age_days = (datetime.now(timezone.utc) - model_created).days
            if age_days > 7:
                logger.info(f"Model for {crypto_symbol} is {age_days} days old, training needed")
                return True
        
        # Check model performance (retrain if accuracy < 70%)
        performance = await prediction_service.get_model_performance(crypto_symbol)
        if performance:
            accuracy = performance.get("accuracy_percentage", 0)
            if accuracy < 70:
                logger.info(f"Model for {crypto_symbol} has low accuracy ({accuracy}%), training needed")
                return True
        
        logger.info(f"Model for {crypto_symbol} is up to date")
        return False
        
    except Exception as e:
        logger.error(f"Error checking training need for {crypto_symbol}: {str(e)}")
        return True  # Default to training if uncertain


def check_training_needed(crypto_symbol: str, force_retrain: bool = False) -> bool:
    """
    Synchronous wrapper for checking if training is needed
    
    Args:
        crypto_symbol: Cryptocurrency symbol to check
        force_retrain: Force retrain even if model exists
        
    Returns:
        bool: True if training is needed, False otherwise
    """
    return run_async_task(_async_check_training_needed(crypto_symbol, force_retrain))


# =====================================
# TASK STATUS MANAGEMENT
# =====================================

def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get status of ML task - Similar to price_collector pattern
    
    Args:
        task_id: Celery task identifier
        
    Returns:
        Dict containing task status information
    """
    try:
        # Check if task exists in Celery
        task_result = celery_app.AsyncResult(task_id)
        
        return {
            "task_id": task_id,
            "status": task_result.status,
            "result": task_result.result if task_result.ready() else None,
            "info": task_result.info,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting task status {task_id}: {str(e)}")
        return {
            "task_id": task_id,
            "status": "ERROR",
            "result": None,
            "info": f"Error: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# =====================================
# CELERY TASKS (SYNCHRONOUS IMPLEMENTATIONS)
# =====================================

@celery_app.task(bind=True, name="ml_tasks.auto_train_models")
def auto_train_models(self, force_retrain: bool = False) -> Dict[str, Any]:
    """
    Automatically train models for all active cryptocurrencies
    
    Similar to sync_all_prices pattern but for ML training.
    This function runs synchronously in Celery worker process.
    
    Args:
        force_retrain: Force retrain even if recent models exist
        
    Returns:
        Dict containing task results and statistics
    """
    task_id = self.request.id
    logger.info(f"Starting auto train models task {task_id}")
    
    try:
        # Update task progress
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Starting auto training',
                'progress': 0,
                'current_step': 'Initializing'
            }
        )
        
        db = SessionLocal()
        results = {
            "task_id": task_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "cryptocurrencies_processed": 0,
            "models_trained": 0,
            "training_skipped": 0,
            "errors": [],
            "success": False
        }
        
        try:
            # Get all active cryptocurrencies
            cryptocurrencies = cryptocurrency_repository.get_active_cryptocurrencies(db)
            total_cryptos = len(cryptocurrencies)
            
            if total_cryptos == 0:
                results["completed_at"] = datetime.now(timezone.utc).isoformat()
                results["success"] = True
                results["summary"] = "No active cryptocurrencies found"
                return results
            
            current_task.update_state(
                state='PROGRESS',
                meta={
                    'status': f'Found {total_cryptos} cryptocurrencies to process',
                    'progress': 5,
                    'current_step': 'Processing cryptocurrencies'
                }
            )
            
            # Process each cryptocurrency
            for i, crypto in enumerate(cryptocurrencies):
                try:
                    progress = int((i / total_cryptos) * 90) + 5  # 5-95%
                    current_task.update_state(
                        state='PROGRESS',
                        meta={
                            'status': f'Processing {crypto.symbol}',
                            'progress': progress,
                            'current_step': f'Crypto {i+1}/{total_cryptos}',
                            'current_crypto': crypto.symbol
                        }
                    )
                    
                    # Check if training is needed (using sync wrapper)
                    if check_training_needed(crypto.symbol, force_retrain):
                        logger.info(f"Training model for {crypto.symbol}")
                        
                        # Start training using async wrapper
                        async def _train_model():
                            return await training_service.train_model(
                                crypto_symbol=crypto.symbol,
                                model_type="lstm",
                                force_retrain=force_retrain
                            )
                        
                        training_result = run_async_task(_train_model())
                        
                        if training_result.get("success", False):
                            results["models_trained"] += 1
                            logger.info(f"Successfully trained model for {crypto.symbol}")
                        else:
                            error_msg = f"Training failed for {crypto.symbol}: {training_result.get('error', 'Unknown error')}"
                            results["errors"].append({
                                "crypto_symbol": crypto.symbol,
                                "error": error_msg
                            })
                            logger.error(error_msg)
                    else:
                        results["training_skipped"] += 1
                        logger.info(f"Training skipped for {crypto.symbol} - model is up to date")
                    
                    results["cryptocurrencies_processed"] += 1
                    
                except Exception as e:
                    error_msg = f"Error processing {crypto.symbol}: {str(e)}"
                    results["errors"].append({
                        "crypto_symbol": crypto.symbol,
                        "error": error_msg
                    })
                    logger.error(error_msg)
            
            # Task completion
            results["completed_at"] = datetime.now(timezone.utc).isoformat()
            results["success"] = True
            results["summary"] = f"Processed {results['cryptocurrencies_processed']} cryptocurrencies, trained {results['models_trained']} models, skipped {results['training_skipped']}"
            
            current_task.update_state(
                state='SUCCESS',
                meta={
                    'status': 'Auto training completed',
                    'progress': 100,
                    'results': results
                }
            )
            
            logger.info(f"Auto training task completed: {results['summary']}")
            return results
            
        finally:
            db.close()
            
    except Exception as e:
        error_msg = f"Auto training task failed: {str(e)}"
        logger.error(error_msg)
        
        current_task.update_state(
            state='FAILURE',
            meta={
                'status': 'Auto training failed',
                'error': error_msg,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )
        
        return {
            "task_id": task_id,
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@celery_app.task(bind=True, name="ml_tasks.generate_scheduled_predictions")
def generate_scheduled_predictions(self, crypto_symbols: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Generate scheduled predictions for cryptocurrencies
    
    Synchronous Celery task that generates predictions for specified
    or all active cryptocurrencies using available trained models.
    
    Args:
        crypto_symbols: Optional list of symbols to generate predictions for
        
    Returns:
        Dict containing prediction generation results
    """
    task_id = self.request.id
    logger.info(f"Starting scheduled predictions task {task_id}")
    
    try:
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Starting prediction generation',
                'progress': 0,
                'current_step': 'Initializing'
            }
        )
        
        db = SessionLocal()
        results = {
            "task_id": task_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "cryptocurrencies_processed": 0,
            "predictions_generated": 0,
            "predictions_failed": 0,
            "errors": [],
            "success": False
        }
        
        try:
            # Get cryptocurrencies to process
            if crypto_symbols:
                cryptocurrencies = [
                    cryptocurrency_repository.get_by_symbol(db, symbol) 
                    for symbol in crypto_symbols
                ]
                cryptocurrencies = [c for c in cryptocurrencies if c]  # Filter None values
            else:
                cryptocurrencies = cryptocurrency_repository.get_active_cryptocurrencies(db)
            
            total_cryptos = len(cryptocurrencies)
            
            if total_cryptos == 0:
                results["completed_at"] = datetime.now(timezone.utc).isoformat()
                results["success"] = True
                results["summary"] = "No cryptocurrencies found for prediction"
                return results
            
            current_task.update_state(
                state='PROGRESS',
                meta={
                    'status': f'Generating predictions for {total_cryptos} cryptocurrencies',
                    'progress': 5,
                    'current_step': 'Processing predictions'
                }
            )
            
            # Generate predictions for each cryptocurrency
            for i, crypto in enumerate(cryptocurrencies):
                try:
                    progress = int((i / total_cryptos) * 90) + 5  # 5-95%
                    current_task.update_state(
                        state='PROGRESS',
                        meta={
                            'status': f'Generating predictions for {crypto.symbol}',
                            'progress': progress,
                            'current_step': f'Crypto {i+1}/{total_cryptos}',
                            'current_crypto': crypto.symbol
                        }
                    )
                    
                    # Generate predictions using async wrapper
                    async def _generate_predictions():
                        return await prediction_service.predict_price(
                            crypto_symbol=crypto.symbol,
                            prediction_horizon=24  # 24 hours
                        )
                    
                    prediction_result = run_async_task(_generate_predictions())
                    
                    if prediction_result.get("success", False):
                        results["predictions_generated"] += 1
                        logger.info(f"Generated prediction for {crypto.symbol}")
                    else:
                        results["predictions_failed"] += 1
                        error_msg = f"Prediction failed for {crypto.symbol}: {prediction_result.get('error', 'Unknown error')}"
                        results["errors"].append({
                            "crypto_symbol": crypto.symbol,
                            "error": error_msg
                        })
                        logger.error(error_msg)
                    
                    results["cryptocurrencies_processed"] += 1
                    
                except Exception as e:
                    error_msg = f"Error processing {crypto.symbol}: {str(e)}"
                    results["errors"].append({
                        "crypto_symbol": crypto.symbol,
                        "error": error_msg
                    })
                    logger.error(error_msg)
            
            # Task completion
            results["completed_at"] = datetime.now(timezone.utc).isoformat()
            results["success"] = True
            results["summary"] = f"Generated {results['predictions_generated']} predictions for {results['cryptocurrencies_processed']} cryptocurrencies, {results['predictions_failed']} failed"
            
            current_task.update_state(
                state='SUCCESS',
                meta={
                    'status': 'Prediction generation completed',
                    'progress': 100,
                    'results': results
                }
            )
            
            logger.info(f"Scheduled predictions task completed: {results['summary']}")
            return results
            
        finally:
            db.close()
            
    except Exception as e:
        error_msg = f"Scheduled predictions task failed: {str(e)}"
        logger.error(error_msg)
        
        current_task.update_state(
            state='FAILURE',
            meta={
                'status': 'Prediction generation failed',
                'error': error_msg,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )
        
        return {
            "task_id": task_id,
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@celery_app.task(bind=True, name="ml_tasks.evaluate_model_performance")
def evaluate_model_performance(self, crypto_symbol: Optional[str] = None) -> Dict[str, Any]:
    """
    Evaluate model performance and accuracy
    
    Synchronous Celery task that evaluates prediction accuracy
    by comparing predictions with actual market prices.
    
    Args:
        crypto_symbol: Optional specific cryptocurrency to evaluate
        
    Returns:
        Dict containing performance evaluation results
    """
    task_id = self.request.id
    logger.info(f"Starting model performance evaluation task {task_id}")
    
    try:
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Starting performance evaluation',
                'progress': 0,
                'current_step': 'Initializing'
            }
        )
        
        db = SessionLocal()
        results = {
            "task_id": task_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "cryptocurrencies_evaluated": 0,
            "performance_updates": 0,
            "evaluation_errors": 0,
            "errors": [],
            "success": False
        }
        
        try:
            # Get cryptocurrencies to evaluate
            if crypto_symbol:
                crypto = cryptocurrency_repository.get_by_symbol(db, crypto_symbol)
                cryptocurrencies = [crypto] if crypto else []
            else:
                cryptocurrencies = cryptocurrency_repository.get_active_cryptocurrencies(db)
            
            total_cryptos = len(cryptocurrencies)
            
            if total_cryptos == 0:
                results["completed_at"] = datetime.now(timezone.utc).isoformat()
                results["success"] = True
                results["summary"] = "No cryptocurrencies found for evaluation"
                return results
            
            current_task.update_state(
                state='PROGRESS',
                meta={
                    'status': f'Evaluating {total_cryptos} cryptocurrencies',
                    'progress': 5,
                    'current_step': 'Processing evaluations'
                }
            )
            
            # Evaluate each cryptocurrency
            for i, crypto in enumerate(cryptocurrencies):
                try:
                    progress = int((i / total_cryptos) * 90) + 5  # 5-95%
                    current_task.update_state(
                        state='PROGRESS',
                        meta={
                            'status': f'Evaluating {crypto.symbol}',
                            'progress': progress,
                            'current_step': f'Crypto {i+1}/{total_cryptos}',
                            'current_crypto': crypto.symbol
                        }
                    )
                    
                    # Evaluate performance using async wrapper
                    async def _evaluate_performance():
                        return await prediction_service.evaluate_model_accuracy(
                            crypto_symbol=crypto.symbol,
                            days_back=30  # Evaluate last 30 days
                        )
                    
                    evaluation_result = run_async_task(_evaluate_performance())
                    
                    if evaluation_result.get("success", False):
                        results["performance_updates"] += 1
                        logger.info(f"Updated performance metrics for {crypto.symbol}")
                    else:
                        results["evaluation_errors"] += 1
                        error_msg = f"Evaluation failed for {crypto.symbol}: {evaluation_result.get('error', 'Unknown error')}"
                        results["errors"].append({
                            "crypto_symbol": crypto.symbol,
                            "error": error_msg
                        })
                        logger.error(error_msg)
                    
                    results["cryptocurrencies_evaluated"] += 1
                    
                except Exception as e:
                    error_msg = f"Error evaluating {crypto.symbol}: {str(e)}"
                    results["errors"].append({
                        "crypto_symbol": crypto.symbol,
                        "error": error_msg
                    })
                    logger.error(error_msg)
            
            # Task completion
            results["completed_at"] = datetime.now(timezone.utc).isoformat()
            results["success"] = True
            results["summary"] = f"Evaluated {results['cryptocurrencies_evaluated']} cryptocurrencies, updated {results['performance_updates']} performance records"
            
            current_task.update_state(
                state='SUCCESS',
                meta={
                    'status': 'Performance evaluation completed',
                    'progress': 100,
                    'results': results
                }
            )
            
            logger.info(f"Performance evaluation task completed: {results['summary']}")
            return results
            
        finally:
            db.close()
            
    except Exception as e:
        error_msg = f"Performance evaluation task failed: {str(e)}"
        logger.error(error_msg)
        
        current_task.update_state(
            state='FAILURE',
            meta={
                'status': 'Performance evaluation failed',
                'error': error_msg,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )
        
        return {
            "task_id": task_id,
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@celery_app.task(bind=True, name="ml_tasks.cleanup_old_predictions")
def cleanup_old_predictions(self, days_to_keep: int = 90) -> Dict[str, Any]:
    """
    Clean up old prediction data to manage database size
    
    Synchronous Celery task that removes old prediction records
    while preserving recent data and important analytics.
    
    Args:
        days_to_keep: Number of days of prediction data to retain
        
    Returns:
        Dict containing cleanup results
    """
    task_id = self.request.id
    logger.info(f"Starting prediction cleanup task {task_id}")
    
    try:
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Starting prediction cleanup',
                'progress': 0,
                'current_step': 'Initializing'
            }
        )
        
        db = SessionLocal()
        results = {
            "task_id": task_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "days_to_keep": days_to_keep,
            "predictions_deleted": 0,
            "success": False
        }
        
        try:
            # Calculate cutoff date
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
            
            current_task.update_state(
                state='PROGRESS',
                meta={
                    'status': f'Cleaning predictions older than {cutoff_date.strftime("%Y-%m-%d")}',
                    'progress': 10,
                    'current_step': 'Identifying old records'
                }
            )
            
            # Delete old predictions
            deleted_count = prediction_repository.delete_old_predictions(db, cutoff_date)
            results["predictions_deleted"] = deleted_count
            
            current_task.update_state(
                state='PROGRESS',
                meta={
                    'status': f'Deleted {deleted_count} old predictions',
                    'progress': 90,
                    'current_step': 'Finalizing cleanup'
                }
            )
            
            # Commit the transaction
            db.commit()
            
            # Task completion
            results["completed_at"] = datetime.now(timezone.utc).isoformat()
            results["success"] = True
            results["summary"] = f"Deleted {deleted_count} predictions older than {days_to_keep} days"
            
            current_task.update_state(
                state='SUCCESS',
                meta={
                    'status': 'Prediction cleanup completed',
                    'progress': 100,
                    'results': results
                }
            )
            
            logger.info(f"Prediction cleanup task completed: {results['summary']}")
            return results
            
        finally:
            db.close()
            
    except Exception as e:
        error_msg = f"Prediction cleanup task failed: {str(e)}"
        logger.error(error_msg)
        
        current_task.update_state(
            state='FAILURE',
            meta={
                'status': 'Prediction cleanup failed',
                'error': error_msg,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )
        
        return {
            "task_id": task_id,
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# =====================================
# CONVENIENCE FUNCTIONS FOR MANUAL EXECUTION
# =====================================

def start_auto_training(force_retrain: bool = False) -> str:
    """
    Start auto training task manually
    
    Args:
        force_retrain: Force retrain even if models are recent
        
    Returns:
        str: Task ID for monitoring
    """
    task = auto_train_models.delay(force_retrain=force_retrain)
    return task.id


def start_prediction_generation(crypto_symbols: Optional[List[str]] = None) -> str:
    """
    Start prediction generation task manually
    
    Args:
        crypto_symbols: Optional list of specific cryptocurrencies
        
    Returns:
        str: Task ID for monitoring
    """
    task = generate_scheduled_predictions.delay(crypto_symbols=crypto_symbols)
    return task.id


def start_performance_evaluation(crypto_symbol: Optional[str] = None) -> str:
    """
    Start performance evaluation task manually
    
    Args:
        crypto_symbol: Optional specific cryptocurrency to evaluate
        
    Returns:
        str: Task ID for monitoring
    """
    task = evaluate_model_performance.delay(crypto_symbol=crypto_symbol)
    return task.id


def start_prediction_cleanup(days_to_keep: int = 90) -> str:
    """
    Start prediction cleanup task manually
    
    Args:
        days_to_keep: Number of days of data to retain
        
    Returns:
        str: Task ID for monitoring
    """
    task = cleanup_old_predictions.delay(days_to_keep=days_to_keep)
    return task.id