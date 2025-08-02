# File: backend/app/api/api_v1/endpoints/ml_prediction.py
# ML Prediction API endpoints - Based on ml_training.py pattern
# Fixed to use existing prediction schemas and follow training endpoint structure

import asyncio
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

# Import existing services and components
from app.core.database import get_db
from app.core.deps import get_current_active_user, get_optional_current_user
from app.ml.prediction.prediction_service import prediction_service
from app.ml.config.ml_config import model_registry, ml_config
from app.repositories import cryptocurrency_repository, prediction_repository
from app.models import User

# Import prediction schemas (using existing prediction.py schemas)
from app.schemas.ml_prediction import (
    PredictionRequest, PredictionResult, BatchPredictionRequest, BatchPredictionResponse,
    PredictionResponse, PredictionCreate, ModelPerformance, PredictionAnalytics
)
from app.schemas.common import SuccessResponse

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for prediction jobs (in production, use Redis or database)
prediction_jobs: Dict[str, Dict[str, Any]] = {}
prediction_cache: Dict[str, Dict[str, Any]] = {}


# =====================================
# HELPER FUNCTIONS (Following ml_training.py pattern)
# =====================================

def generate_prediction_id(crypto_symbol: str, timeframe: str) -> str:
    """
    Generate unique prediction ID
    
    Args:
        crypto_symbol: Cryptocurrency symbol
        timeframe: Prediction timeframe
        
    Returns:
        str: Unique prediction identifier
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"pred_{crypto_symbol.lower()}_{timeframe}_{timestamp}"


def generate_batch_id() -> str:
    """
    Generate unique batch prediction ID
    
    Returns:
        str: Unique batch identifier
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"batch_{timestamp}_{uuid.uuid4().hex[:8]}"


def get_cache_key(crypto_symbol: str, timeframe: str, model_version: Optional[str] = None) -> str:
    """
    Generate cache key for predictions
    
    Args:
        crypto_symbol: Cryptocurrency symbol
        timeframe: Prediction timeframe
        model_version: Model version (optional)
        
    Returns:
        str: Cache key
    """
    base_key = f"{crypto_symbol}_{timeframe}"
    if model_version:
        base_key += f"_{model_version}"
    return base_key


def create_safe_prediction_response(prediction_id: str, job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a safe prediction response without problematic data
    
    Args:
        prediction_id: Prediction identifier
        job: Job data dictionary
        
    Returns:
        dict: Safe response data
    """
    # Calculate duration
    duration_seconds = None
    if job.get("completed_at"):
        duration_seconds = int((job["completed_at"] - job["started_at"]).total_seconds())
    elif job.get("status") == "running":
        duration_seconds = int((datetime.now(timezone.utc) - job["started_at"]).total_seconds())
    
    return {
        "prediction_id": prediction_id,
        "crypto_symbol": job["crypto_symbol"],
        "status": job["status"],
        "message": job.get("message", "Prediction in progress"),
        "started_at": job["started_at"],
        "completed_at": job.get("completed_at"),
        "duration_seconds": duration_seconds,
        "error_details": job.get("error_details"),
        "prediction_result": job.get("prediction_result")
    }


async def run_prediction_task(
    prediction_id: str,
    crypto_symbol: str,
    prediction_horizon: int,
    model_type: str,
    include_confidence: bool
):
    """
    Background task to run prediction (following training pattern)
    
    Args:
        prediction_id: Prediction identifier
        crypto_symbol: Cryptocurrency symbol
        prediction_horizon: Hours ahead to predict
        model_type: Type of model to use
        include_confidence: Whether to include confidence score
    """
    try:
        # Update job status to running
        prediction_jobs[prediction_id]["status"] = "running"
        prediction_jobs[prediction_id]["message"] = "Prediction started"
        
        logger.info(f"Starting prediction job {prediction_id} for {crypto_symbol}")
        
        # Start actual prediction
        result = await prediction_service.predict_price(
            crypto_symbol=crypto_symbol,
            prediction_horizon=prediction_horizon
        )
        
        # Update job with results
        if result.get("success", False):
            prediction_jobs[prediction_id]["status"] = "completed"
            prediction_jobs[prediction_id]["message"] = "Prediction completed successfully"
            prediction_jobs[prediction_id]["completed_at"] = datetime.now(timezone.utc)
            prediction_jobs[prediction_id]["prediction_result"] = result
        else:
            prediction_jobs[prediction_id]["status"] = "failed"
            prediction_jobs[prediction_id]["message"] = "Prediction failed"
            prediction_jobs[prediction_id]["error_details"] = result.get("error", "Unknown error")
            prediction_jobs[prediction_id]["completed_at"] = datetime.now(timezone.utc)
            
        logger.info(f"Prediction job {prediction_id} completed with status: {prediction_jobs[prediction_id]['status']}")
        
    except Exception as e:
        logger.error(f"Prediction job {prediction_id} failed with exception: {str(e)}")
        prediction_jobs[prediction_id]["status"] = "failed"
        prediction_jobs[prediction_id]["message"] = "Prediction failed with exception"
        prediction_jobs[prediction_id]["error_details"] = str(e)
        prediction_jobs[prediction_id]["completed_at"] = datetime.now(timezone.utc)


# =====================================
# PREDICTION ENDPOINTS (Following ml_training.py pattern)
# =====================================

@router.post("/predict", operation_id="make_price_prediction")
async def make_prediction(
    request: PredictionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> PredictionResult:
    """
    Make a cryptocurrency price prediction
    
    Initiates prediction for specified cryptocurrency. Prediction runs
    asynchronously in the background and can be monitored via status endpoint.
    """
    try:
        logger.info(f"User {current_user.id} requesting prediction for crypto_id {request.crypto_id}")
        
        # Validate cryptocurrency exists
        crypto = cryptocurrency_repository.get_by_id(db, request.crypto_id)
        if not crypto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cryptocurrency with ID {request.crypto_id} not found"
            )
        
        # Generate prediction job ID
        prediction_id = generate_prediction_id(crypto.symbol, f"{request.prediction_horizon}h")
        
        # Check cache for recent predictions
        cache_key = get_cache_key(crypto.symbol, f"{request.prediction_horizon}h")
        cache_ttl_minutes = 30  # Cache for 30 minutes
        
        if cache_key in prediction_cache:
            cached_prediction = prediction_cache[cache_key]
            cached_time = cached_prediction.get("cached_at")
            if cached_time and (datetime.now(timezone.utc) - cached_time).total_seconds() < cache_ttl_minutes * 60:
                logger.info(f"Returning cached prediction for {crypto.symbol}")
                
                cached_result = cached_prediction["data"]
                return PredictionResult(
                    crypto_id=request.crypto_id,
                    crypto_symbol=crypto.symbol,
                    model_name=cached_result["model_name"],
                    predicted_price=cached_result["predicted_price"],
                    confidence_score=cached_result["confidence_score"],
                    target_datetime=cached_result["target_datetime"],
                    features_used=cached_result.get("features_used", []),
                    model_accuracy=cached_result.get("model_accuracy"),
                    prediction_id=None
                )
        
        # Create prediction job record
        prediction_jobs[prediction_id] = {
            "prediction_id": prediction_id,
            "crypto_symbol": crypto.symbol,
            "crypto_id": request.crypto_id,
            "status": "pending",
            "message": "Prediction job queued",
            "started_at": datetime.now(timezone.utc),
            "user_id": current_user.id,
            "prediction_horizon": request.prediction_horizon,
            "model_type": request.model_type,
            "include_confidence": request.include_confidence
        }
        
        # Try immediate prediction first (for quick results)
        try:
            result = await prediction_service.predict_price(
                crypto_symbol=crypto.symbol,
                prediction_horizon=request.prediction_horizon
            )
            
            if result.get("success", False):
                # Cache the result
                target_datetime = datetime.now(timezone.utc) + timedelta(hours=request.prediction_horizon)
                
                cached_data = {
                    "model_name": result.get("model_name", "unknown"),
                    "predicted_price": result["predicted_price"],
                    "confidence_score": result.get("confidence_score", 0.0),
                    "target_datetime": target_datetime,
                    "features_used": result.get("features_used", []),
                    "model_accuracy": result.get("model_accuracy")
                }
                
                prediction_cache[cache_key] = {
                    "data": cached_data,
                    "cached_at": datetime.now(timezone.utc)
                }
                
                # Update job status to completed
                prediction_jobs[prediction_id]["status"] = "completed"
                prediction_jobs[prediction_id]["prediction_result"] = result
                prediction_jobs[prediction_id]["completed_at"] = datetime.now(timezone.utc)
                
                logger.info(f"Immediate prediction completed for {crypto.symbol}")
                
                return PredictionResult(
                    crypto_id=request.crypto_id,
                    crypto_symbol=crypto.symbol,
                    model_name=cached_data["model_name"],
                    predicted_price=cached_data["predicted_price"],
                    confidence_score=cached_data["confidence_score"],
                    target_datetime=cached_data["target_datetime"],
                    features_used=cached_data["features_used"],
                    model_accuracy=cached_data["model_accuracy"],
                    prediction_id=None
                )
                
        except Exception as e:
            logger.warning(f"Immediate prediction failed for {crypto.symbol}: {str(e)}")
        
        # Start background prediction task
        background_tasks.add_task(
            run_prediction_task,
            prediction_id,
            crypto.symbol,
            request.prediction_horizon,
            request.model_type,
            request.include_confidence
        )
        
        # Wait briefly for quick predictions
        await asyncio.sleep(0.5)
        
        # Check if completed quickly
        if prediction_id in prediction_jobs:
            job = prediction_jobs[prediction_id]
            if job["status"] == "completed" and job.get("prediction_result"):
                result = job["prediction_result"]
                target_datetime = datetime.now(timezone.utc) + timedelta(hours=request.prediction_horizon)
                
                return PredictionResult(
                    crypto_id=request.crypto_id,
                    crypto_symbol=crypto.symbol,
                    model_name=result.get("model_name", "unknown"),
                    predicted_price=result["predicted_price"],
                    confidence_score=result.get("confidence_score", 0.0),
                    target_datetime=target_datetime,
                    features_used=result.get("features_used", []),
                    model_accuracy=result.get("model_accuracy"),
                    prediction_id=None
                )
        
        # Return pending response with job info
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail={
                "message": "Prediction is being processed",
                "prediction_id": prediction_id,
                "status_endpoint": f"/api/v1/ml/prediction/status/{prediction_id}",
                "estimated_completion": "2-5 minutes"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to make prediction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to make prediction: {str(e)}"
        )


@router.get("/status/{prediction_id}", operation_id="get_prediction_status")
async def get_prediction_status(
    prediction_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get prediction job status and progress
    
    Returns detailed information about a prediction job including progress,
    current status, and results if completed.
    """
    try:
        # Check if job exists
        if prediction_id not in prediction_jobs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prediction job {prediction_id} not found"
            )
        
        job = prediction_jobs[prediction_id]
        
        # Create safe response
        response = create_safe_prediction_response(prediction_id, job)
        
        logger.info(f"User {current_user.id} checked status of prediction job {prediction_id}")
        
        return {
            "success": True,
            "prediction_status": response,
            "requested_by": current_user.email,
            "requested_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prediction status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prediction status: {str(e)}"
        )


@router.post("/batch", operation_id="make_batch_predictions")
async def make_batch_predictions(
    request: BatchPredictionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> BatchPredictionResponse:
    """
    Make predictions for multiple cryptocurrencies
    
    Generates predictions for multiple cryptocurrencies simultaneously.
    Useful for portfolio analysis and comparison across different assets.
    """
    try:
        logger.info(f"User {current_user.id} requesting batch predictions for {len(request.crypto_ids)} cryptos")
        
        # Generate batch ID
        batch_id = generate_batch_id()
        
        # Validate all crypto IDs exist
        valid_cryptos = []
        errors = []
        
        for crypto_id in request.crypto_ids:
            crypto = cryptocurrency_repository.get_by_id(db, crypto_id)
            if crypto:
                valid_cryptos.append(crypto)
            else:
                errors.append({
                    "crypto_id": crypto_id,
                    "error": "Cryptocurrency not found",
                    "error_code": "CRYPTO_NOT_FOUND"
                })
        
        # Generate predictions for valid cryptos
        predictions = []
        
        async def predict_single(crypto) -> Optional[PredictionResult]:
            try:
                result = await prediction_service.predict_price(
                    crypto_symbol=crypto.symbol,
                    prediction_horizon=request.prediction_horizon
                )
                
                if result.get("success", False):
                    target_datetime = datetime.now(timezone.utc) + timedelta(hours=request.prediction_horizon)
                    
                    return PredictionResult(
                        crypto_id=crypto.id,
                        crypto_symbol=crypto.symbol,
                        model_name=result.get("model_name", "unknown"),
                        predicted_price=result["predicted_price"],
                        confidence_score=result.get("confidence_score", 0.0),
                        target_datetime=target_datetime,
                        features_used=result.get("features_used", []),
                        model_accuracy=result.get("model_accuracy"),
                        prediction_id=None
                    )
                else:
                    errors.append({
                        "crypto_id": crypto.id,
                        "crypto_symbol": crypto.symbol,
                        "error": result.get("error", "Prediction failed"),
                        "error_code": "PREDICTION_FAILED"
                    })
                    return None
                    
            except Exception as e:
                errors.append({
                    "crypto_id": crypto.id,
                    "crypto_symbol": crypto.symbol,
                    "error": str(e),
                    "error_code": "PREDICTION_ERROR"
                })
                return None
        
        # Execute predictions concurrently
        prediction_tasks = [predict_single(crypto) for crypto in valid_cryptos]
        prediction_results = await asyncio.gather(*prediction_tasks, return_exceptions=True)
        
        # Filter successful predictions
        for result in prediction_results:
            if isinstance(result, PredictionResult):
                predictions.append(result)
        
        return BatchPredictionResponse(
            predictions=predictions,
            total_requested=len(request.crypto_ids),
            successful_predictions=len(predictions),
            failed_predictions=len(request.crypto_ids) - len(predictions),
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Failed to make batch predictions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to make batch predictions: {str(e)}"
        )


@router.get("/history/{crypto_id}", operation_id="get_prediction_history")
async def get_prediction_history(
    crypto_id: int,
    days_back: int = 30,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[PredictionResponse]:
    """
    Get prediction history for a cryptocurrency
    
    Returns historical predictions for the specified cryptocurrency
    for analysis and accuracy tracking.
    """
    try:
        logger.info(f"User {current_user.id} requesting history for crypto_id {crypto_id}")
        
        # Validate cryptocurrency exists
        crypto = cryptocurrency_repository.get_by_id(db, crypto_id)
        if not crypto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cryptocurrency with ID {crypto_id} not found"
            )
        
        # Get historical predictions from database
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        predictions = prediction_repository.get_predictions_by_crypto_and_date(
            db, 
            crypto_id, 
            cutoff_date
        )
        
        # Convert to response format
        prediction_responses = []
        for pred in predictions:
            pred_response = PredictionResponse(
                id=pred.id,
                crypto_id=pred.crypto_id,
                model_name=pred.model_name,
                predicted_price=pred.predicted_price,
                confidence_score=pred.confidence_score,
                target_datetime=pred.target_datetime,
                features_used=pred.features_used,
                user_id=pred.user_id,
                created_at=pred.created_at
            )
            prediction_responses.append(pred_response)
        
        logger.info(f"Retrieved {len(prediction_responses)} historical predictions for {crypto.symbol}")
        
        return prediction_responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prediction history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prediction history: {str(e)}"
        )


@router.get("/performance/{crypto_id}", operation_id="get_prediction_performance")
async def get_prediction_performance(
    crypto_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ModelPerformance:
    """
    Get prediction performance metrics for a cryptocurrency
    
    Returns detailed performance information about prediction models
    including accuracy and error metrics.
    """
    try:
        logger.info(f"User {current_user.id} requesting performance for crypto_id {crypto_id}")
        
        # Validate cryptocurrency exists
        crypto = cryptocurrency_repository.get_by_id(db, crypto_id)
        if not crypto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cryptocurrency with ID {crypto_id} not found"
            )
        
        # Get performance data from prediction service
        performance_data = await prediction_service.get_model_performance(crypto.symbol)
        
        if not performance_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No performance data found for {crypto.symbol}"
            )
        
        return ModelPerformance(
            model_name=performance_data.get("model_name", "unknown"),
            crypto_id=crypto_id,
            total_predictions=performance_data.get("total_predictions", 0),
            accurate_predictions=performance_data.get("accurate_predictions", 0),
            accuracy_percentage=performance_data.get("accuracy_percentage", 0.0),
            average_error=performance_data.get("average_error", 0.0),
            rmse=performance_data.get("rmse", 0.0),
            mae=performance_data.get("mae", 0.0),
            last_trained=performance_data.get("last_trained", datetime.now(timezone.utc)),
            training_data_points=performance_data.get("training_data_points", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prediction performance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prediction performance: {str(e)}"
        )


@router.get("/analytics/{crypto_id}", operation_id="get_prediction_analytics")
async def get_prediction_analytics(
    crypto_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> PredictionAnalytics:
    """
    Get prediction analytics for a cryptocurrency
    
    Returns comprehensive analytics about predictions including
    accuracy trends and model performance comparisons.
    """
    try:
        logger.info(f"User {current_user.id} requesting analytics for crypto_id {crypto_id}")
        
        # Validate cryptocurrency exists
        crypto = cryptocurrency_repository.get_by_id(db, crypto_id)
        if not crypto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cryptocurrency with ID {crypto_id} not found"
            )
        
        # Get analytics data
        analytics_data = await prediction_service.get_prediction_analytics(crypto.symbol)
        
        if not analytics_data:
            # Return default analytics if no data available
            return PredictionAnalytics(
                crypto_id=crypto_id,
                crypto_symbol=crypto.symbol,
                total_predictions=0,
                average_confidence=0.0,
                accuracy_by_horizon={},
                best_performing_model="unknown",
                worst_performing_model="unknown",
                prediction_trends={}
            )
        
        return PredictionAnalytics(
            crypto_id=crypto_id,
            crypto_symbol=crypto.symbol,
            total_predictions=analytics_data.get("total_predictions", 0),
            average_confidence=analytics_data.get("average_confidence", 0.0),
            accuracy_by_horizon=analytics_data.get("accuracy_by_horizon", {}),
            best_performing_model=analytics_data.get("best_performing_model", "unknown"),
            worst_performing_model=analytics_data.get("worst_performing_model", "unknown"),
            prediction_trends=analytics_data.get("prediction_trends", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prediction analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prediction analytics: {str(e)}"
        )


@router.delete("/jobs/{prediction_id}", operation_id="cancel_prediction_job")
async def cancel_prediction_job(
    prediction_id: str,
    current_user: User = Depends(get_current_active_user)
) -> SuccessResponse:
    """
    Cancel a running prediction job
    
    Attempts to cancel a prediction job that is currently pending or running.
    Completed or failed jobs cannot be cancelled.
    """
    try:
        # Check if job exists
        if prediction_id not in prediction_jobs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prediction job {prediction_id} not found"
            )
        
        job = prediction_jobs[prediction_id]
        
        # Check if job can be cancelled
        if job["status"] in ["completed", "failed", "cancelled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel job with status: {job['status']}"
            )
        
        # Update job status
        prediction_jobs[prediction_id]["status"] = "cancelled"
        prediction_jobs[prediction_id]["message"] = f"Job cancelled by user {current_user.email}"
        prediction_jobs[prediction_id]["completed_at"] = datetime.now(timezone.utc)
        
        logger.info(f"User {current_user.id} cancelled prediction job {prediction_id}")
        
        return SuccessResponse(
            success=True,
            message=f"Prediction job {prediction_id} cancelled successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel prediction job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel prediction job: {str(e)}"
        )