# File: backend/app/api/api_v1/endpoints/ml_prediction.py
# ML Prediction API endpoints - Based on ml_training.py pattern

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

# Import the schemas we just created
from app.schemas.ml_prediction import (
    PredictionRequest, PredictionResponse, BatchPredictionRequest, BatchPredictionResponse,
    PredictionHistoryRequest, PredictionHistoryResponse, PredictionHistoryItem,
    ModelPerformanceResponse, ModelPerformanceMetrics, PredictionStatsResponse,
    PredictionStatus, PredictionTimeframe
)
from app.schemas.common import SuccessResponse

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for prediction jobs (in production, use Redis or database)
prediction_jobs: Dict[str, Dict[str, Any]] = {}
prediction_cache: Dict[str, Dict[str, Any]] = {}


def generate_prediction_id(crypto_symbol: str, timeframe: str) -> str:
    """Generate unique prediction ID"""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"pred_{crypto_symbol.lower()}_{timeframe}_{timestamp}"


def generate_batch_id() -> str:
    """Generate unique batch prediction ID"""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"batch_{timestamp}_{uuid.uuid4().hex[:8]}"


def get_cache_key(crypto_symbol: str, timeframe: str, model_version: Optional[str] = None) -> str:
    """Generate cache key for predictions"""
    model_part = f"_{model_version}" if model_version else ""
    return f"pred_{crypto_symbol.lower()}_{timeframe}{model_part}"


def is_prediction_fresh(cached_prediction: Dict[str, Any], timeframe: str) -> bool:
    """Check if cached prediction is still fresh"""
    if not cached_prediction or "prediction_timestamp" not in cached_prediction:
        return False
    
    prediction_time = cached_prediction["prediction_timestamp"]
    if isinstance(prediction_time, str):
        prediction_time = datetime.fromisoformat(prediction_time.replace('Z', '+00:00'))
    
    now = datetime.now(timezone.utc)
    
    # Define freshness based on timeframe
    freshness_rules = {
        "15m": timedelta(minutes=5),
        "30m": timedelta(minutes=10), 
        "1h": timedelta(minutes=20),
        "4h": timedelta(hours=1),
        "24h": timedelta(hours=4),
        "7d": timedelta(hours=12),
        "30d": timedelta(days=1)
    }
    
    max_age = freshness_rules.get(timeframe, timedelta(hours=1))
    return (now - prediction_time) < max_age


async def run_prediction_task(
    prediction_id: str,
    crypto_symbol: str,
    prediction_config: Optional[dict] = None,
    model_version: Optional[str] = None,
    include_historical_context: bool = True
):
    """Background task for running predictions - similar to training task pattern"""
    try:
        logger.info(f"Starting prediction task {prediction_id} for {crypto_symbol}")
        
        if prediction_id not in prediction_jobs:
            logger.error(f"Prediction job {prediction_id} not found in jobs registry")
            return
        
        # Update status to running
        prediction_jobs[prediction_id].update({
            "status": PredictionStatus.RUNNING,
            "message": "Generating prediction...",
            "started_processing_at": datetime.now(timezone.utc)
        })
        
        # Get database session
        db = SessionLocal()
        try:
            # Validate cryptocurrency exists
            crypto = cryptocurrency_repository.get_by_symbol(db, crypto_symbol)
            if not crypto:
                raise Exception(f"Cryptocurrency {crypto_symbol} not found")
            
            # Prepare prediction configuration
            config = prediction_config or {}
            timeframe = config.get("timeframe", "24h")
            confidence_threshold = config.get("confidence_threshold", 0.7)
            use_ensemble = config.get("use_ensemble_models", True)
            
            # Run prediction using prediction service
            prediction_result = await prediction_service.predict_price(
                crypto_symbol=crypto_symbol,
                timeframe=timeframe,
                model_version=model_version,
                use_ensemble_models=use_ensemble,
                include_technical_indicators=config.get("include_technical_indicators", True),
                include_market_sentiment=config.get("include_market_sentiment", False)
            )
            
            if prediction_result and prediction_result.get("success", False):
                # Calculate prediction validity
                valid_until = datetime.now(timezone.utc)
                if timeframe == "15m":
                    valid_until += timedelta(minutes=15)
                elif timeframe == "30m":
                    valid_until += timedelta(minutes=30)
                elif timeframe == "1h":
                    valid_until += timedelta(hours=1)
                elif timeframe == "4h":
                    valid_until += timedelta(hours=4)
                elif timeframe == "24h":
                    valid_until += timedelta(hours=24)
                elif timeframe == "7d":
                    valid_until += timedelta(days=7)
                elif timeframe == "30d":
                    valid_until += timedelta(days=30)
                
                # Update job with successful result
                prediction_jobs[prediction_id].update({
                    "status": PredictionStatus.COMPLETED,
                    "message": "Prediction completed successfully",
                    "completed_at": datetime.now(timezone.utc),
                    "prediction_result": prediction_result,
                    "valid_until": valid_until,
                    "confidence_score": prediction_result.get("confidence_score", 0.0)
                })
                
                # Cache the result
                cache_key = get_cache_key(crypto_symbol, timeframe, model_version)
                prediction_cache[cache_key] = {
                    "prediction_result": prediction_result,
                    "prediction_timestamp": datetime.now(timezone.utc),
                    "valid_until": valid_until,
                    "timeframe": timeframe
                }
                
                logger.info(f"Prediction job {prediction_id} completed successfully")
            else:
                raise Exception(f"Prediction failed: {prediction_result.get('error', 'Unknown error')}")
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Prediction job {prediction_id} failed with exception: {str(e)}")
        if prediction_id in prediction_jobs:
            prediction_jobs[prediction_id].update({
                "status": PredictionStatus.FAILED,
                "message": f"Prediction failed: {str(e)}",
                "completed_at": datetime.now(timezone.utc),
                "error_details": str(e)
            })


@router.post("/predictions/predict", response_model=PredictionResponse)
async def make_prediction(
    request: PredictionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Make a price prediction for cryptocurrency
    
    Requires authentication. Generates AI-powered price predictions.
    """
    try:
        # Validate cryptocurrency exists
        crypto = cryptocurrency_repository.get_by_symbol(db, request.crypto_symbol)
        if not crypto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cryptocurrency {request.crypto_symbol} not found"
            )
        
        config = request.prediction_config.dict() if request.prediction_config else {}
        timeframe = config.get("timeframe", "24h")
        
        # Check cache first (unless force_refresh is True)
        if not request.force_refresh:
            cache_key = get_cache_key(request.crypto_symbol, timeframe, request.model_version)
            cached_prediction = prediction_cache.get(cache_key)
            
            if cached_prediction and is_prediction_fresh(cached_prediction, timeframe):
                logger.info(f"Returning cached prediction for {request.crypto_symbol}")
                result = cached_prediction["prediction_result"]
                
                return PredictionResponse(
                    prediction_id=f"cached_{cache_key}",
                    crypto_symbol=request.crypto_symbol,
                    current_price=result["current_price"],
                    predicted_price=result["predicted_price"],
                    price_change=result["price_change"],
                    price_change_percentage=result["price_change_percentage"],
                    confidence_score=result["confidence_score"],
                    timeframe=timeframe,
                    model_used=result["model_used"],
                    model_version=result["model_version"],
                    prediction_timestamp=cached_prediction["prediction_timestamp"],
                    valid_until=cached_prediction["valid_until"],
                    technical_indicators=result.get("technical_indicators"),
                    market_sentiment=result.get("market_sentiment"),
                    historical_accuracy=result.get("historical_accuracy"),
                    risk_assessment=result.get("risk_assessment")
                )
        
        # Generate prediction ID and create job
        prediction_id = generate_prediction_id(request.crypto_symbol, timeframe)
        
        prediction_jobs[prediction_id] = {
            "prediction_id": prediction_id,
            "crypto_symbol": request.crypto_symbol,
            "timeframe": timeframe,
            "model_version": request.model_version,
            "status": PredictionStatus.PENDING,
            "message": "Prediction request queued",
            "created_at": datetime.now(timezone.utc),
            "user_id": current_user.id,
            "config": config
        }
        
        # Start background task
        background_tasks.add_task(
            run_prediction_task,
            prediction_id,
            request.crypto_symbol,
            config,
            request.model_version,
            request.include_historical_context
        )
        
        # Wait briefly for quick predictions
        await asyncio.sleep(0.5)
        
        # Check if completed quickly
        if prediction_id in prediction_jobs:
            job = prediction_jobs[prediction_id]
            if job["status"] == PredictionStatus.COMPLETED:
                result = job["prediction_result"]
                return PredictionResponse(
                    prediction_id=prediction_id,
                    crypto_symbol=request.crypto_symbol,
                    current_price=result["current_price"],
                    predicted_price=result["predicted_price"],
                    price_change=result["price_change"],
                    price_change_percentage=result["price_change_percentage"],
                    confidence_score=result["confidence_score"],
                    timeframe=timeframe,
                    model_used=result["model_used"],
                    model_version=result["model_version"],
                    prediction_timestamp=job["completed_at"],
                    valid_until=job["valid_until"],
                    technical_indicators=result.get("technical_indicators"),
                    market_sentiment=result.get("market_sentiment"),
                    historical_accuracy=result.get("historical_accuracy"),
                    risk_assessment=result.get("risk_assessment")
                )
        
        # Return async response for longer predictions
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail={
                "message": "Prediction is being processed",
                "prediction_id": prediction_id,
                "status_endpoint": f"/api/v1/ml/predictions/status/{prediction_id}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction request failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction request failed: {str(e)}"
        )


@router.get("/predictions/status/{prediction_id}")
async def get_prediction_status(
    prediction_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get status of a prediction job
    
    Similar to training status endpoint pattern.
    """
    if prediction_id not in prediction_jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction job {prediction_id} not found"
        )
    
    job = prediction_jobs[prediction_id]
    
    # Verify user owns this prediction job
    if job.get("user_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this prediction job"
        )
    
    # If completed, return full result
    if job["status"] == PredictionStatus.COMPLETED:
        result = job["prediction_result"]
        return {
            "prediction_id": prediction_id,
            "status": job["status"],
            "message": job["message"],
            "prediction": PredictionResponse(
                prediction_id=prediction_id,
                crypto_symbol=job["crypto_symbol"],
                current_price=result["current_price"],
                predicted_price=result["predicted_price"],
                price_change=result["price_change"],
                price_change_percentage=result["price_change_percentage"],
                confidence_score=result["confidence_score"],
                timeframe=job["timeframe"],
                model_used=result["model_used"],
                model_version=result["model_version"],
                prediction_timestamp=job["completed_at"],
                valid_until=job["valid_until"],
                technical_indicators=result.get("technical_indicators"),
                market_sentiment=result.get("market_sentiment"),
                historical_accuracy=result.get("historical_accuracy"),
                risk_assessment=result.get("risk_assessment")
            )
        }
    
    # Return status for pending/running jobs
    return {
        "prediction_id": prediction_id,
        "status": job["status"],
        "message": job["message"],
        "crypto_symbol": job["crypto_symbol"],
        "timeframe": job["timeframe"],
        "created_at": job["created_at"],
        "started_processing_at": job.get("started_processing_at"),
        "error_details": job.get("error_details")
    }


@router.post("/predictions/batch", response_model=BatchPredictionResponse)
async def batch_predictions(
    request: BatchPredictionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Make batch predictions for multiple cryptocurrencies
    
    Requires authentication. Processes multiple predictions efficiently.
    """
    try:
        batch_id = generate_batch_id()
        start_time = datetime.now(timezone.utc)
        
        predictions = []
        successful_count = 0
        failed_count = 0
        
        for crypto_symbol in request.crypto_symbols:
            try:
                # Validate cryptocurrency exists
                crypto = cryptocurrency_repository.get_by_symbol(db, crypto_symbol)
                if not crypto:
                    logger.warning(f"Cryptocurrency {crypto_symbol} not found, skipping")
                    failed_count += 1
                    continue
                
                # Create individual prediction request
                config = request.prediction_config.dict() if request.prediction_config else {}
                timeframe = config.get("timeframe", "24h")
                
                # Check cache first
                cache_key = get_cache_key(crypto_symbol, timeframe, request.model_version)
                cached_prediction = prediction_cache.get(cache_key)
                
                if cached_prediction and is_prediction_fresh(cached_prediction, timeframe):
                    result = cached_prediction["prediction_result"]
                    predictions.append(PredictionResponse(
                        prediction_id=f"batch_{batch_id}_{crypto_symbol.lower()}",
                        crypto_symbol=crypto_symbol,
                        current_price=result["current_price"],
                        predicted_price=result["predicted_price"],
                        price_change=result["price_change"],
                        price_change_percentage=result["price_change_percentage"],
                        confidence_score=result["confidence_score"],
                        timeframe=timeframe,
                        model_used=result["model_used"],
                        model_version=result["model_version"],
                        prediction_timestamp=cached_prediction["prediction_timestamp"],
                        valid_until=cached_prediction["valid_until"],
                        technical_indicators=result.get("technical_indicators"),
                        market_sentiment=result.get("market_sentiment"),
                        historical_accuracy=result.get("historical_accuracy"),
                        risk_assessment=result.get("risk_assessment")
                    ))
                    successful_count += 1
                else:
                    # Generate new prediction
                    prediction_result = await prediction_service.predict_price(
                        crypto_symbol=crypto_symbol,
                        timeframe=timeframe,
                        model_version=request.model_version,
                        use_ensemble_models=config.get("use_ensemble_models", True)
                    )
                    
                    if prediction_result and prediction_result.get("success", False):
                        valid_until = datetime.now(timezone.utc) + timedelta(hours=24)  # Default validity
                        
                        predictions.append(PredictionResponse(
                            prediction_id=f"batch_{batch_id}_{crypto_symbol.lower()}",
                            crypto_symbol=crypto_symbol,
                            current_price=prediction_result["current_price"],
                            predicted_price=prediction_result["predicted_price"],
                            price_change=prediction_result["price_change"],
                            price_change_percentage=prediction_result["price_change_percentage"],
                            confidence_score=prediction_result["confidence_score"],
                            timeframe=timeframe,
                            model_used=prediction_result["model_used"],
                            model_version=prediction_result["model_version"],
                            prediction_timestamp=datetime.now(timezone.utc),
                            valid_until=valid_until,
                            technical_indicators=prediction_result.get("technical_indicators"),
                            market_sentiment=prediction_result.get("market_sentiment"),
                            historical_accuracy=prediction_result.get("historical_accuracy"),
                            risk_assessment=prediction_result.get("risk_assessment")
                        ))
                        successful_count += 1
                        
                        # Cache the result
                        prediction_cache[cache_key] = {
                            "prediction_result": prediction_result,
                            "prediction_timestamp": datetime.now(timezone.utc),
                            "valid_until": valid_until,
                            "timeframe": timeframe
                        }
                    else:
                        failed_count += 1
                        
            except Exception as e:
                logger.error(f"Failed to predict {crypto_symbol}: {str(e)}")
                failed_count += 1
        
        end_time = datetime.now(timezone.utc)
        processing_time = (end_time - start_time).total_seconds()
        
        return BatchPredictionResponse(
            batch_id=batch_id,
            total_requested=len(request.crypto_symbols),
            successful_predictions=successful_count,
            failed_predictions=failed_count,
            predictions=predictions,
            processing_time_seconds=processing_time
        )
        
    except Exception as e:
        logger.error(f"Batch prediction failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction failed: {str(e)}"
        )


@router.get("/predictions/history/{crypto_symbol}", response_model=PredictionHistoryResponse)
async def get_prediction_history(
    crypto_symbol: str,
    days_back: Optional[int] = 7,
    model_version: Optional[str] = None,
    min_confidence: Optional[float] = None,
    limit: Optional[int] = 50,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Any:
    """
    Get prediction history for a cryptocurrency
    
    Optional authentication. Returns historical predictions and their accuracy.
    """
    try:
        # Validate parameters
        if days_back < 1 or days_back > 90:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="days_back must be between 1 and 90"
            )
        
        if limit < 1 or limit > 500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="limit must be between 1 and 500"
            )
        
        # Validate cryptocurrency exists
        crypto = cryptocurrency_repository.get_by_symbol(db, crypto_symbol)
        if not crypto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cryptocurrency {crypto_symbol} not found"
            )
        
        # Get prediction history from repository
        predictions = prediction_repository.get_by_crypto_and_timerange(
            db=db,
            crypto_id=crypto.id,
            days_back=days_back,
            model_name=model_version,
            limit=limit
        )
        
        # Filter by confidence if specified
        if min_confidence:
            predictions = [p for p in predictions if p.confidence_score >= min_confidence]
        
        # Convert to response format
        prediction_items = []
        realized_count = 0
        total_accuracy = 0.0
        
        for pred in predictions:
            is_realized = pred.is_realized or False
            accuracy = None
            
            if is_realized and pred.actual_price:
                accuracy = 1.0 - abs(float(pred.predicted_price - pred.actual_price)) / float(pred.actual_price)
                accuracy = max(0.0, accuracy)  # Ensure non-negative
                total_accuracy += accuracy
                realized_count += 1
            
            prediction_items.append(PredictionHistoryItem(
                prediction_id=f"hist_{pred.id}",
                predicted_price=pred.predicted_price,
                actual_price=pred.actual_price,
                accuracy=accuracy,
                confidence_score=float(pred.confidence_score or 0.0),
                model_used=pred.model_name or "unknown",
                prediction_timestamp=pred.created_at,
                is_realized=is_realized
            ))
        
        average_accuracy = (total_accuracy / realized_count) if realized_count > 0 else None
        
        return PredictionHistoryResponse(
            crypto_symbol=crypto_symbol,
            total_predictions=len(prediction_items),
            realized_predictions=realized_count,
            average_accuracy=average_accuracy,
            predictions=prediction_items
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get prediction history failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prediction history: {str(e)}"
        )


@router.get("/predictions/performance/{crypto_symbol}", response_model=ModelPerformanceResponse)
async def get_model_performance(
    crypto_symbol: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Any:
    """
    Get model performance metrics for a cryptocurrency
    
    Optional authentication. Returns detailed performance statistics.
    """
    try:
        # Validate cryptocurrency exists
        crypto = cryptocurrency_repository.get_by_symbol(db, crypto_symbol)
        if not crypto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cryptocurrency {crypto_symbol} not found"
            )
        
        # Get active model info
        active_model = model_registry.get_active_model(crypto_symbol)
        if not active_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active model found for {crypto_symbol}"
            )
        
        # Get performance metrics from prediction service
        performance_metrics = await prediction_service.get_model_performance(crypto_symbol)
        
        active_model_metrics = ModelPerformanceMetrics(
            model_name=active_model["name"],
            model_version=active_model["version"],
            total_predictions=performance_metrics.get("total_predictions", 0),
            realized_predictions=performance_metrics.get("realized_predictions", 0),
            accuracy_percentage=performance_metrics.get("accuracy_percentage"),
            average_confidence=performance_metrics.get("average_confidence", 0.0),
            rmse=performance_metrics.get("rmse"),
            mae=performance_metrics.get("mae"),
            last_updated=datetime.now(timezone.utc)
        )
        
        # Get alternative models (if any)
        alternative_models = []
        all_models = model_registry.list_models(crypto_symbol)
        
        for model_info in all_models:
            if model_info["name"] != active_model["name"]:
                # Get performance for alternative model
                alt_performance = await prediction_service.get_model_performance(
                    crypto_symbol, model_name=model_info["name"]
                )
                
                alternative_models.append(ModelPerformanceMetrics(
                    model_name=model_info["name"],
                    model_version=model_info["version"],
                    total_predictions=alt_performance.get("total_predictions", 0),
                    realized_predictions=alt_performance.get("realized_predictions", 0),
                    accuracy_percentage=alt_performance.get("accuracy_percentage"),
                    average_confidence=alt_performance.get("average_confidence", 0.0),
                    rmse=alt_performance.get("rmse"),
                    mae=alt_performance.get("mae"),
                    last_updated=datetime.now(timezone.utc)
                ))
        
        # Get performance trend
        performance_trend = performance_metrics.get("performance_trend", {})
        
        return ModelPerformanceResponse(
            crypto_symbol=crypto_symbol,
            active_model=active_model_metrics,
            alternative_models=alternative_models if alternative_models else None,
            performance_trend=performance_trend if performance_trend else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get model performance failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model performance: {str(e)}"
        )


@router.get("/predictions/stats", response_model=PredictionStatsResponse)
async def get_prediction_stats(
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Any:
    """
    Get overall prediction statistics
    
    Optional authentication. Returns system-wide prediction metrics.
    """
    try:
        # Get stats from prediction service
        stats = await prediction_service.get_system_stats()
        
        return PredictionStatsResponse(
            total_predictions_today=stats.get("predictions_today", 0),
            total_predictions_week=stats.get("predictions_week", 0),
            total_predictions_all_time=stats.get("predictions_all_time", 0),
            active_cryptocurrencies=stats.get("active_cryptocurrencies", 0),
            active_models=stats.get("active_models", 0),
            average_confidence=stats.get("average_confidence", 0.0),
            cache_hit_rate=stats.get("cache_hit_rate", 0.0),
            average_response_time_ms=stats.get("average_response_time_ms", 0.0)
        )
        
    except Exception as e:
        logger.error(f"Get prediction stats failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prediction statistics: {str(e)}"
        )


@router.delete("/predictions/cache/clear")
async def clear_prediction_cache(
    crypto_symbol: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
) -> SuccessResponse:
    """
    Clear prediction cache
    
    Requires authentication. Clears cached predictions.
    """
    try:
        if crypto_symbol:
            # Clear cache for specific cryptocurrency
            keys_to_remove = [key for key in prediction_cache.keys() if crypto_symbol.lower() in key]
            for key in keys_to_remove:
                del prediction_cache[key]
            message = f"Cleared prediction cache for {crypto_symbol}"
        else:
            # Clear all cache
            prediction_cache.clear()
            message = "Cleared all prediction cache"
        
        logger.info(f"Cache cleared by user {current_user.id}: {message}")
        
        return SuccessResponse(
            success=True,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Clear prediction cache failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear prediction cache: {str(e)}"
        )