# File: backend/app/main.py
# UPDATED: FastAPI application with Graceful Shutdown and Persistent Model Registry

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import Response, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn
import uvicorn.config
import os
import logging
import signal
import sys
from datetime import datetime
import asyncio

from app.core.config import settings
from app.api.api_v1.api import api_router
from app.core.database import engine, Base

# Import models to ensure they're registered with SQLAlchemy
from app.models import Base, User, Cryptocurrency, PriceData, Prediction

# NEW: Import persistent model registry
from app.ml.config.ml_config import model_registry, ml_config

logger = logging.getLogger(__name__)

# Create all database tables on startup
Base.metadata.create_all(bind=engine)

# Development mode check - auto-create tables without Alembic
from pathlib import Path

dev_mode_file = Path(__file__).parent.parent / ".dev_mode_no_alembic"
if dev_mode_file.exists():
    logger.info("🔧 Development Mode: Creating tables directly from models")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tables created from models (Development Mode)")
    except Exception as e:
        logger.error(f"❌ Error creating tables: {str(e)}")

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="CryptoPredict API - Bitcoin Price Prediction with ML",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0"]
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Custom HTTPException handler to show e.detail
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom HTTPException handler that includes detailed error information
    """
    error_response = {
        "status_code": exc.status_code,
        "message": exc.detail,
        "timestamp": datetime.now().isoformat(),
        "path": str(request.url.path)
    }
    
    # Log the error with details
    logger.error(f"HTTPException {exc.status_code}: {exc.detail} - Path: {request.url.path}")
    
    # If there's additional detail in the exception, include it
    if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
        error_response.update(exc.detail)
    elif hasattr(exc, 'detail') and exc.detail:
        error_response["detail"] = exc.detail
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )

# Custom general exception handler for unexpected errors
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    General exception handler for unexpected errors
    """
    error_message = str(exc)
    error_type = type(exc).__name__
    
    # Log the full error
    logger.error(f"Unhandled exception {error_type}: {error_message} - Path: {request.url.path}", exc_info=True)
    
    error_response = {
        "status_code": 500,
        "message": "Internal server error",
        "error_type": error_type,
        "detail": error_message,
        "timestamp": datetime.now().isoformat(),
        "path": str(request.url.path)
    }
    
    # In development mode, include more details
    if settings.DEBUG:
        import traceback
        error_response["traceback"] = traceback.format_exc()
    
    return JSONResponse(
        status_code=500,
        content=error_response
    )

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Global flag for graceful shutdown
shutdown_flag = False

@app.on_event("startup")
async def startup_event():
    """
    Startup event handler
    The persistent model registry automatically loads existing models during initialization
    """
    logger.info("🚀 Starting CryptoPredict backend...")
    
    logger.info(f"Check historical data for {settings.major_cryptos_list}")
    await startup_data_check()

    # Log model registry status
    total_models = len(model_registry.models)
    active_models = len(model_registry.active_models)
    
    logger.info(f"📊 Model Registry Status:")
    logger.info(f"   Total models: {total_models}")
    logger.info(f"   Active models: {active_models}")
    logger.info(f"   Models directory: {ml_config.models_storage_path}")
    
    if total_models > 0:
        logger.info("📋 Available models:")
        for crypto_symbol, model_id in model_registry.active_models.items():
            model_info = model_registry.get_model_info(model_id)
            if model_info:
                model_path = model_info.get('model_path', 'Unknown')
                logger.info(f"   {crypto_symbol}: {model_id} ({model_path})")
    else:
        logger.info("📝 No models found. Models will be available after training.")
    
    logger.info("✅ Backend startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Graceful shutdown event handler"""
    global shutdown_flag
    shutdown_flag = True
    
    logger.info("🛑 Shutting down CryptoPredict backend...")
    
    # Save model registry state before shutdown
    try:
        if hasattr(model_registry, 'save_registry'):
            model_registry.save_registry()
            logger.info("💾 Model registry saved before shutdown")
    except Exception as e:
        logger.error(f"❌ Failed to save registry on shutdown: {str(e)}")
    
    # Additional cleanup can be added here
    logger.info("✅ Graceful shutdown complete")


@app.get("/")
async def root():
    """Root endpoint with model information"""
    total_models = len(model_registry.models)
    active_models = len(model_registry.active_models)
    
    # Get active models info
    active_models_info = {}
    for crypto_symbol, model_id in model_registry.active_models.items():
        model_info = model_registry.get_model_info(model_id)
        if model_info:
            active_models_info[crypto_symbol] = {
                "model_id": model_id,
                "registered_at": model_info.get('registered_at'),
                "model_type": model_info.get('model_type', 'unknown')
            }
    
    return {
        "message": "CryptoPredict API with Persistent Model Registry",
        "version": settings.VERSION,
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "models": {
            "total": total_models,
            "active": active_models,
            "active_models": active_models_info
        },
        "registry": {
            "type": "persistent",
            "auto_load": True,
            "storage": ml_config.models_storage_path
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint with model registry status"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "api": "running",
            "database": "connected",
            "model_registry": {
                "status": "operational",
                "models_loaded": len(model_registry.models),
                "active_models": len(model_registry.active_models),
                "registry_type": "persistent"
            }
        }
    }


@app.get("/models/status")
async def models_status():
    """Detailed model registry status endpoint"""
    models_info = []
    
    for model_id, model_data in model_registry.models.items():
        model_info = {
            "model_id": model_id,
            "crypto_symbol": model_data.get('crypto_symbol'),
            "model_type": model_data.get('model_type'),
            "is_active": model_data.get('is_active', False),
            "registered_at": model_data.get('registered_at'),
            "file_exists": os.path.exists(model_data.get('model_path', ''))
        }
        models_info.append(model_info)
    
    return {
        "registry_type": "persistent",
        "models_directory": ml_config.models_storage_path,
        "total_models": len(model_registry.models),
        "active_models": len(model_registry.active_models),
        "models": models_info,
        "active_models_by_crypto": model_registry.active_models
    }


async def startup_data_check():
    """Check and ensure basic data on startup using settings"""
    
    try:
        from app.services.data_sync import data_sync_service
        
        # Use settings for crypto list and min records
        for crypto in settings.major_cryptos_list:
            try:
                await data_sync_service.check_and_ensure_historical_data(
                    crypto_symbol=crypto,
                    min_records=settings.ML_STARTUP_MIN_RECORDS,  # 30 for faster startup
                    max_age_hours=settings.ML_MAX_DATA_AGE_HOURS
                )
                logger.info(f"✅ Startup data check passed for {crypto}")
            except Exception as e:
                logger.warning(f"⚠️ Startup data check failed for {crypto}: {e}")
    
    except Exception as e:
        logger.error(f"Startup data check error: {e}")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_flag
    shutdown_flag = True
    
    signal_name = signal.Signals(signum).name if hasattr(signal, 'Signals') else str(signum)
    logger.info(f"📡 Received signal {signal_name} ({signum})")
    logger.info("🛑 Initiating graceful shutdown...")
    
    # Set the flag and let the main loop handle the shutdown
    sys.exit(0)


async def main():
    """Main async function with proper shutdown handling"""
    try:
        logger.info("🔧 Starting server with graceful shutdown support...")
        
        config = uvicorn.Config(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            access_log=True,
            use_colors=True
        )
        server = uvicorn.Server(config)
        
        # Setup signal handlers
        def handle_signal():
            logger.info("🔴 Shutdown signal received - shutting down gracefully")
            server.should_exit = True
        
        # Handle different signals
        for sig in [signal.SIGINT, signal.SIGTERM]:
            signal.signal(sig, lambda s, f: handle_signal())
        
        await server.serve()
        
    except KeyboardInterrupt:
        logger.info("🔴 KeyboardInterrupt received - shutting down gracefully")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
    finally:
        logger.info("👋 Server shutdown complete")


if __name__ == "__main__":
    # Run the async main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # This should now be handled more gracefully
        print("\n🔴 Application terminated by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)