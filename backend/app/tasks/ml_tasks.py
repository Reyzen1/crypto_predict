# File: backend/app/tasks/ml_tasks.py
# Background tasks for ML operations - Based on price_collector.py pattern

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


def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get status of ML task - Similar to price_collector pattern
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


@celery_app.task(bind=True, name="ml_tasks.auto_train_models")
def auto_train_models(self, force_retrain: bool = False) -> Dict[str, Any]:
    """
    Automatically train models for all active cryptocurrencies
    
    Similar to sync_all_prices pattern but for ML training
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
            "models_failed": 0,
            "training_results": [],
            "errors": []
        }
        
        try:
            # Get all active cryptocurrencies
            cryptocurrencies = cryptocurrency_repository.get_all_active(db)
            total_cryptos = len(cryptocurrencies)
            
            logger.info(f"Found {total_cryptos} cryptocurrencies for auto training")
            
            for i, crypto in enumerate(cryptocurrencies):
                try:
                    # Update progress
                    progress = int((i / total_cryptos) * 100)
                    current_task.update_state(
                        state='PROGRESS',
                        meta={
                            'status': f'Training models for {crypto.symbol}',
                            'progress': progress,
                            'current_step': f'Processing {crypto.symbol} ({i+1}/{total_cryptos})',
                            'crypto_symbol': crypto.symbol
                        }
                    )
                    
                    # Check if training is needed
                    needs_training = await _check_if_training_needed(
                        db, crypto.symbol, force_retrain
                    )
                    
                    if needs_training:
                        logger.info(f"Training model for {crypto.symbol}")
                        
                        # Start training
                        training_result = await training_service.train_model(
                            crypto_symbol=crypto.symbol,
                            model_type="lstm",
                            training_config={
                                "epochs": 50,  # Reduced for background task
                                "batch_size": 32,
                                "sequence_length": 60,
                                "validation_split": 0.2
                            },
                            data_days_back=365,
                            force_retrain=force_retrain
                        )
                        
                        if training_result.get("success", False):
                            results["models_trained"] += 1
                            results["training_results"].append({
                                "crypto_symbol": crypto.symbol,
                                "status": "success",
                                "model_path": training_result.get("model_path"),
                                "training_metrics": training_result.get("training_metrics", {}),
                                "evaluation_metrics": training_result.get("evaluation_metrics", {})
                            })
                            logger.info(f"Successfully trained model for {crypto.symbol}")
                        else:
                            results["models_failed"] += 1
                            error_msg = training_result.get("error", "Unknown training error")
                            results["errors"].append({
                                "crypto_symbol": crypto.symbol,
                                "error": error_msg
                            })
                            logger.error(f"Failed to train model for {crypto.symbol}: {error_msg}")
                    else:
                        logger.info(f"Model for {crypto.symbol} is up to date, skipping")
                        results["training_results"].append({
                            "crypto_symbol": crypto.symbol,
                            "status": "skipped",
                            "reason": "Model is up to date"
                        })
                    
                    results["cryptocurrencies_processed"] += 1
                    
                except Exception as e:
                    results["models_failed"] += 1
                    error_msg = f"Error processing {crypto.symbol}: {str(e)}"
                    results["errors"].append({
                        "crypto_symbol": crypto.symbol,
                        "error": error_msg
                    })
                    logger.error(error_msg)
            
            # Final task completion
            results["completed_at"] = datetime.now(timezone.utc).isoformat()
            results["success"] = True
            results["summary"] = f"Processed {results['cryptocurrencies_processed']} cryptocurrencies, trained {results['models_trained']} models, {results['models_failed']} failed"
            
            current_task.update_state(
                state='SUCCESS',
                meta={
                    'status': 'Auto training completed',
                    'progress': 100,
                    'results': results
                }
            )
            
            logger.info(f"Auto train models task completed: {results['summary']}")
            return results
            
        finally:
            db.close()
            
    except Exception as e:
        error_msg = f"Auto train models task failed: {str(e)}"
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
    Generate predictions for cryptocurrencies on schedule
    
    Similar to sync_all_prices but for predictions
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
            "prediction_results": [],
            "errors": []
        }
        
        try:
            # Get cryptocurrencies to predict
            if crypto_symbols:
                cryptocurrencies = []
                for symbol in crypto_symbols:
                    crypto = cryptocurrency_repository.get_by_symbol(db, symbol)
                    if crypto:
                        cryptocurrencies.append(crypto)
            else:
                cryptocurrencies = cryptocurrency_repository.get_all_active(db)
            
            total_cryptos = len(cryptocurrencies)
            logger.info(f"Generating predictions for {total_cryptos} cryptocurrencies")
            
            # Prediction timeframes to generate
            timeframes = ["1h", "4h", "24h", "7d"]
            
            for i, crypto in enumerate(cryptocurrencies):
                try:
                    # Update progress
                    progress = int((i / total_cryptos) * 100)
                    current_task.update_state(
                        state='PROGRESS',
                        meta={
                            'status': f'Generating predictions for {crypto.symbol}',
                            'progress': progress,
                            'current_step': f'Processing {crypto.symbol} ({i+1}/{total_cryptos})',
                            'crypto_symbol': crypto.symbol
                        }
                    )
                    
                    crypto_predictions = []
                    
                    for timeframe in timeframes:
                        try:
                            # Generate prediction
                            prediction_result = await prediction_service.predict_price(
                                crypto_symbol=crypto.symbol,
                                timeframe=timeframe,
                                use_ensemble_models=True,
                                include_technical_indicators=True
                            )
                            
                            if prediction_result and prediction_result.get("success", False):
                                crypto_predictions.append({
                                    "timeframe": timeframe,
                                    "predicted_price": float(prediction_result["predicted_price"]),
                                    "confidence_score": prediction_result["confidence_score"],
                                    "model_used": prediction_result["model_used"]
                                })
                                results["predictions_generated"] += 1
                            else:
                                results["predictions_failed"] += 1
                                results["errors"].append({
                                    "crypto_symbol": crypto.symbol,
                                    "timeframe": timeframe,
                                    "error": prediction_result.get("error", "Unknown prediction error")
                                })
                        
                        except Exception as e:
                            results["predictions_failed"] += 1
                            results["errors"].append({
                                "crypto_symbol": crypto.symbol,
                                "timeframe": timeframe,
                                "error": str(e)
                            })
                    
                    if crypto_predictions:
                        results["prediction_results"].append({
                            "crypto_symbol": crypto.symbol,
                            "predictions": crypto_predictions,
                            "total_predictions": len(crypto_predictions)
                        })
                    
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
    
    Checks realized predictions vs actual prices
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
            "total_predictions_evaluated": 0,
            "performance_results": [],
            "errors": []
        }
        
        try:
            # Get cryptocurrencies to evaluate
            if crypto_symbol:
                crypto = cryptocurrency_repository.get_by_symbol(db, crypto_symbol)
                cryptocurrencies = [crypto] if crypto else []
            else:
                cryptocurrencies = cryptocurrency_repository.get_all_active(db)
            
            total_cryptos = len(cryptocurrencies)
            
            for i, crypto in enumerate(cryptocurrencies):
                try:
                    # Update progress
                    progress = int((i / total_cryptos) * 100)
                    current_task.update_state(
                        state='PROGRESS',
                        meta={
                            'status': f'Evaluating {crypto.symbol}',
                            'progress': progress,
                            'current_step': f'Processing {crypto.symbol} ({i+1}/{total_cryptos})',
                            'crypto_symbol': crypto.symbol
                        }
                    )
                    
                    # Get performance metrics
                    performance_metrics = await prediction_service.evaluate_model_accuracy(
                        crypto_symbol=crypto.symbol,
                        days_back=30
                    )
                    
                    if performance_metrics:
                        results["performance_results"].append({
                            "crypto_symbol": crypto.symbol,
                            "total_predictions": performance_metrics.get("total_predictions", 0),
                            "realized_predictions": performance_metrics.get("realized_predictions", 0),
                            "accuracy_percentage": performance_metrics.get("accuracy_percentage"),
                            "average_confidence": performance_metrics.get("average_confidence", 0.0),
                            "rmse": performance_metrics.get("rmse"),
                            "mae": performance_metrics.get("mae"),
                            "model_performance": performance_metrics.get("model_performance", {})
                        })
                        
                        results["total_predictions_evaluated"] += performance_metrics.get("total_predictions", 0)
                    
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
            results["summary"] = f"Evaluated {results['cryptocurrencies_evaluated']} cryptocurrencies, {results['total_predictions_evaluated']} predictions analyzed"
            
            current_task.update_state(
                state='SUCCESS',
                meta={
                    'status': 'Performance evaluation completed',
                    'progress': 100,
                    'results': results
                }
            )
            
            logger.info(f"Model performance evaluation completed: {results['summary']}")
            return results
            
        finally:
            db.close()
            
    except Exception as e:
        error_msg = f"Model performance evaluation failed: {str(e)}"
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
    Clean up old predictions to manage database size
    
    Similar to cleanup_old_data in price_collector
    """
    task_id = self.request.id
    logger.info(f"Starting prediction cleanup task {task_id} - keeping {days_to_keep} days")
    
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
            "predictions_kept": 0,
            "errors": []
        }
        
        try:
            # Calculate cutoff date
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
            
            current_task.update_state(
                state='PROGRESS',
                meta={
                    'status': 'Cleaning up old predictions',
                    'progress': 50,
                    'current_step': f'Removing predictions older than {cutoff_date.date()}'
                }
            )
            
            # Get cleanup stats
            cleanup_result = prediction_repository.cleanup_old_predictions(db, cutoff_date)
            
            results["predictions_deleted"] = cleanup_result.get("deleted_count", 0)
            results["predictions_kept"] = cleanup_result.get("remaining_count", 0)
            
            # Task completion
            results["completed_at"] = datetime.now(timezone.utc).isoformat()
            results["success"] = True
            results["summary"] = f"Deleted {results['predictions_deleted']} old predictions, kept {results['predictions_kept']} recent predictions"
            
            current_task.update_state(
                state='SUCCESS',
                meta={
                    'status': 'Prediction cleanup completed',
                    'progress': 100,
                    'results': results
                }
            )
            
            logger.info(f"Prediction cleanup completed: {results['summary']}")
            return results
            
        finally:
            db.close()
            
    except Exception as e:
        error_msg = f"Prediction cleanup failed: {str(e)}"
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


async def _check_if_training_needed(
    db: Session, 
    crypto_symbol: str, 
    force_retrain: bool = False
) -> bool:
    """
    Check if model training is needed for a cryptocurrency
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


# Convenience functions for manual task execution
def start_auto_training(force_retrain: bool = False) -> str:
    """Start auto training task manually"""
    task = auto_train_models.delay(force_retrain=force_retrain)
    return task.id


def start_prediction_generation(crypto_symbols: Optional[List[str]] = None) -> str:
    """Start prediction generation task manually"""
    task = generate_scheduled_predictions.delay(crypto_symbols=crypto_symbols)
    return task.id


def start_performance_evaluation(crypto_symbol: Optional[str] = None) -> str:
    """Start performance evaluation task manually"""
    task = evaluate_model_performance.delay(crypto_symbol=crypto_symbol)
    return task.id


def start_prediction_cleanup(days_to_keep: int = 90) -> str:
    """Start prediction cleanup task manually"""
    task = cleanup_old_predictions.delay(days_to_keep=days_to_keep)
    return task.id