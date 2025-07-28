# File: backend/app/api/api_v1/endpoints/ml_training.py
# ML Training API endpoints - Wrapper around existing MLTrainingService

import asyncio
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

# Import existing services and components
from app.core.database import get_db
from app.core.deps import get_current_active_user, get_optional_current_user
from app.ml.training.training_service import training_service
from app.ml.config.ml_config import model_registry, ml_config
from app.repositories import cryptocurrency_repository
from app.models import User

# Import the schemas we just created
from app.schemas.ml_training import (
    TrainingRequest, TrainingResponse, TrainingStatusResponse,
    ModelInfo, ModelListResponse, ModelActivationRequest, 
    ModelActivationResponse, ModelPerformanceResponse,
    TrainingStatus, ModelType
)
from app.schemas.common import SuccessResponse

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for training jobs (in production, use Redis or database)
training_jobs: Dict[str, Dict[str, Any]] = {}


def generate_job_id(crypto_symbol: str, model_type: str) -> str:
    """Generate unique training job ID"""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"train_{crypto_symbol.lower()}_{model_type}_{timestamp}"


async def run_training_job(
    job_id: str,
    crypto_symbol: str,
    training_config: Optional[Dict[str, Any]] = None,
    data_days_back: int = 180
):
    """
    Background task to run the actual training
    Updates job status in training_jobs dictionary
    """
    try:
        # Update job status to running
        if job_id in training_jobs:
            training_jobs[job_id].update({
                "status": TrainingStatus.RUNNING,
                "message": "Training started",
                "current_epoch": 0
            })
        
        logger.info(f"Starting training job {job_id} for {crypto_symbol}")
        
        # Call existing training service
        result = await training_service.train_model_for_crypto(
            crypto_symbol=crypto_symbol,
            training_config=training_config,
            data_days_back=data_days_back
        )
        
        # Update job status based on result
        if job_id in training_jobs:
            if result.get("success", False):
                training_jobs[job_id].update({
                    "status": TrainingStatus.COMPLETED,
                    "message": "Training completed successfully",
                    "completed_at": datetime.now(timezone.utc),
                    "training_metrics": result.get("training_metrics", {}),
                    "validation_metrics": result.get("validation_metrics", {}),
                    "model_performance": result.get("evaluation_metrics", {}),
                    "model_path": result.get("model_path"),
                    "progress_percentage": 100.0
                })
                logger.info(f"Training job {job_id} completed successfully")
            else:
                training_jobs[job_id].update({
                    "status": TrainingStatus.FAILED,
                    "message": f"Training failed: {result.get('error', 'Unknown error')}",
                    "completed_at": datetime.now(timezone.utc),
                    "error_details": result.get("error", "Unknown error")
                })
                logger.error(f"Training job {job_id} failed: {result.get('error')}")
        
    except Exception as e:
        logger.error(f"Training job {job_id} failed with exception: {str(e)}")
        if job_id in training_jobs:
            training_jobs[job_id].update({
                "status": TrainingStatus.FAILED,
                "message": f"Training failed: {str(e)}",
                "completed_at": datetime.now(timezone.utc),
                "error_details": str(e)
            })


@router.post("/training/start", response_model=TrainingResponse)
async def start_training(
    request: TrainingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Start training a new ML model for cryptocurrency prediction
    
    Requires authentication. Starts a background training job.
    """
    try:
        # Validate cryptocurrency exists
        crypto = cryptocurrency_repository.get_by_symbol(db, request.crypto_symbol)
        if not crypto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cryptocurrency {request.crypto_symbol} not found"
            )
        
        # Check if there's already a recent training job running
        if not request.force_retrain:
            active_jobs = [
                job for job in training_jobs.values()
                if (job["crypto_symbol"] == request.crypto_symbol and 
                    job["status"] in [TrainingStatus.PENDING, TrainingStatus.RUNNING])
            ]
            if active_jobs:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Training job already running for {request.crypto_symbol}. Use force_retrain=true to override."
                )
        
        # Generate job ID
        job_id = generate_job_id(request.crypto_symbol, request.model_type.value)
        
        # Prepare training configuration
        training_config = None
        if request.training_config:
            training_config = request.training_config.dict()
        
        # Store job information
        training_jobs[job_id] = {
            "job_id": job_id,
            "crypto_symbol": request.crypto_symbol,
            "model_type": request.model_type.value,
            "status": TrainingStatus.PENDING,
            "message": "Training job queued",
            "started_at": datetime.now(timezone.utc),
            "user_id": current_user.id,
            "training_config": training_config,
            "data_days_back": request.data_days_back,
            "progress_percentage": 0.0
        }
        
        # Start background training task
        background_tasks.add_task(
            run_training_job,
            job_id,
            request.crypto_symbol,
            training_config,
            request.data_days_back
        )
        
        # Estimate duration based on configuration
        estimated_duration = 15  # Default 15 minutes
        if training_config and "epochs" in training_config:
            estimated_duration = max(5, min(60, training_config["epochs"] // 4))
        
        return TrainingResponse(
            job_id=job_id,
            crypto_symbol=request.crypto_symbol,
            model_type=request.model_type.value,
            status=TrainingStatus.PENDING,
            message="Training job started successfully",
            started_at=datetime.now(timezone.utc),
            estimated_duration_minutes=estimated_duration
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start training: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start training: {str(e)}"
        )


@router.get("/training/{job_id}/status", response_model=TrainingStatusResponse)
async def get_training_status(
    job_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get the status of a training job
    
    Requires authentication. Returns detailed training status.
    """
    if job_id not in training_jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training job {job_id} not found"
        )
    
    job = training_jobs[job_id]
    
    # Check if user has access to this job
    if job.get("user_id") != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this training job"
        )
    
    # Calculate duration
    duration_seconds = None
    if job.get("completed_at"):
        duration_seconds = int((job["completed_at"] - job["started_at"]).total_seconds())
    elif job["status"] == TrainingStatus.RUNNING:
        duration_seconds = int((datetime.now(timezone.utc) - job["started_at"]).total_seconds())
    
    return TrainingStatusResponse(
        job_id=job_id,
        crypto_symbol=job["crypto_symbol"],
        model_type=job["model_type"],
        status=job["status"],
        progress_percentage=job.get("progress_percentage"),
        current_epoch=job.get("current_epoch"),
        total_epochs=job.get("training_config", {}).get("epochs") if job.get("training_config") else None,
        started_at=job["started_at"],
        completed_at=job.get("completed_at"),
        duration_seconds=duration_seconds,
        message=job["message"],
        error_details=job.get("error_details"),
        training_metrics=job.get("training_metrics"),
        validation_metrics=job.get("validation_metrics"),
        model_performance=job.get("model_performance")
    )


@router.get("/models/list", response_model=ModelListResponse)
async def list_models(
    crypto_symbol: Optional[str] = None,
    model_type: Optional[ModelType] = None,
    active_only: bool = False,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    List available trained models
    
    Requires authentication. Can filter by crypto symbol, model type, or active status.
    """
    try:
        # Get models from model registry
        all_models = model_registry.list_models()
        
        # Apply filters
        filtered_models = all_models
        
        if crypto_symbol:
            filtered_models = [m for m in filtered_models if m.get("crypto_symbol", "").upper() == crypto_symbol.upper()]
        
        if model_type:
            filtered_models = [m for m in filtered_models if m.get("model_type") == model_type.value]
        
        if active_only:
            filtered_models = [m for m in filtered_models if m.get("is_active", False)]
        
        # Convert to response format
        model_infos = []
        for model in filtered_models:
            model_info = ModelInfo(
                model_id=model.get("model_id", "unknown"),
                crypto_symbol=model.get("crypto_symbol", "UNKNOWN"),
                model_type=model.get("model_type", "lstm"),
                version=model.get("version", "1.0"),
                is_active=model.get("is_active", False),
                created_at=model.get("created_at", datetime.now(timezone.utc)),
                training_duration_seconds=model.get("training_duration_seconds"),
                data_points_used=model.get("data_points_used"),
                performance_metrics=model.get("performance_metrics"),
                model_path=model.get("model_path")
            )
            model_infos.append(model_info)
        
        # Count active models
        active_models = len([m for m in filtered_models if m.get("is_active", False)])
        
        return ModelListResponse(
            models=model_infos,
            total=len(model_infos),
            active_models=active_models
        )
        
    except Exception as e:
        logger.error(f"Failed to list models: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {str(e)}"
        )


@router.post("/models/{model_id}/activate", response_model=ModelActivationResponse)
async def activate_model(
    model_id: str,
    request: ModelActivationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Activate a specific model for predictions
    
    Requires authentication. Sets the model as active for its cryptocurrency.
    """
    try:
        # Validate model exists
        model_info = model_registry.get_model_info(model_id)
        if not model_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_id} not found"
            )
        
        crypto_symbol = model_info.get("crypto_symbol")
        if not crypto_symbol:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Model does not have associated cryptocurrency symbol"
            )
        
        # Get previously active model
        previous_active = model_registry.get_active_model(crypto_symbol)
        previous_model_id = previous_active.get("model_id") if previous_active else None
        
        # Activate the model
        success = model_registry.set_active_model(crypto_symbol, model_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to activate model"
            )
        
        return ModelActivationResponse(
            model_id=model_id,
            crypto_symbol=crypto_symbol,
            previous_active_model=previous_model_id,
            activated_at=datetime.now(timezone.utc),
            message=f"Model {model_id} activated successfully for {crypto_symbol}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate model {model_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate model: {str(e)}"
        )


@router.get("/models/{model_id}/performance", response_model=ModelPerformanceResponse)
async def get_model_performance(
    model_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get detailed performance metrics for a specific model
    
    Requires authentication. Returns comprehensive model performance data.
    """
    try:
        # Get model information
        model_info = model_registry.get_model_info(model_id)
        if not model_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_id} not found"
            )
        
        # Extract performance metrics
        training_metrics = model_info.get("training_metrics", {})
        validation_metrics = model_info.get("validation_metrics", {})
        performance_metrics = model_info.get("performance_metrics", {})
        
        return ModelPerformanceResponse(
            model_id=model_id,
            crypto_symbol=model_info.get("crypto_symbol", "UNKNOWN"),
            model_type=model_info.get("model_type", "lstm"),
            training_metrics=training_metrics,
            validation_metrics=validation_metrics,
            rmse=performance_metrics.get("rmse", 0.0),
            mae=performance_metrics.get("mae", 0.0),
            r2_score=performance_metrics.get("r2_score", 0.0),
            mape=performance_metrics.get("mape"),
            created_at=model_info.get("created_at", datetime.now(timezone.utc)),
            data_points_used=model_info.get("data_points_used", 0),
            training_duration_seconds=model_info.get("training_duration_seconds", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model performance for {model_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model performance: {str(e)}"
        )


@router.delete("/training/{job_id}/cancel", response_model=SuccessResponse)
async def cancel_training(
    job_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Cancel a running training job
    
    Requires authentication. Can only cancel pending or running jobs.
    """
    if job_id not in training_jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training job {job_id} not found"
        )
    
    job = training_jobs[job_id]
    
    # Check if user has access to this job
    if job.get("user_id") != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this training job"
        )
    
    # Check if job can be cancelled
    if job["status"] not in [TrainingStatus.PENDING, TrainingStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job with status: {job['status']}"
        )
    
    # Update job status
    training_jobs[job_id].update({
        "status": TrainingStatus.CANCELLED,
        "message": "Training cancelled by user",
        "completed_at": datetime.now(timezone.utc)
    })
    
    return SuccessResponse(
        success=True,
        message=f"Training job {job_id} cancelled successfully"
    )


@router.get("/training/jobs", response_model=List[TrainingStatusResponse])
async def list_training_jobs(
    crypto_symbol: Optional[str] = None,
    status_filter: Optional[TrainingStatus] = None,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    List training jobs for the current user
    
    Requires authentication. Can filter by crypto symbol and status.
    """
    # Filter jobs by user (unless superuser)
    user_jobs = []
    for job_id, job in training_jobs.items():
        if current_user.is_superuser or job.get("user_id") == current_user.id:
            # Apply filters
            if crypto_symbol and job["crypto_symbol"].upper() != crypto_symbol.upper():
                continue
            if status_filter and job["status"] != status_filter:
                continue
                
            # Calculate duration
            duration_seconds = None
            if job.get("completed_at"):
                duration_seconds = int((job["completed_at"] - job["started_at"]).total_seconds())
            elif job["status"] == TrainingStatus.RUNNING:
                duration_seconds = int((datetime.now(timezone.utc) - job["started_at"]).total_seconds())
            
            job_status = TrainingStatusResponse(
                job_id=job_id,
                crypto_symbol=job["crypto_symbol"],
                model_type=job["model_type"],
                status=job["status"],
                progress_percentage=job.get("progress_percentage"),
                current_epoch=job.get("current_epoch"),
                total_epochs=job.get("training_config", {}).get("epochs") if job.get("training_config") else None,
                started_at=job["started_at"],
                completed_at=job.get("completed_at"),
                duration_seconds=duration_seconds,
                message=job["message"],
                error_details=job.get("error_details"),
                training_metrics=job.get("training_metrics"),
                validation_metrics=job.get("validation_metrics"),
                model_performance=job.get("model_performance")
            )
            user_jobs.append(job_status)
    
    return user_jobs