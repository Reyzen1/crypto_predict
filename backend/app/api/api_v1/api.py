# File: backend/app/api/api_v1/api.py
# Main API router with fixed imports and enhanced endpoints
# Updated to use new naming convention and prediction endpoints

from fastapi import APIRouter

# Import all endpoint modules with corrected names
from app.api.api_v1.endpoints import (
    auth,
    users, 
    crypto,
    prices,
    external,
    tasks,
    health,
    ml_training,      
    prediction     
)

# Create main API router
api_router = APIRouter()

# Include authentication router
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Include user management router  
api_router.include_router(users.router, prefix="/users", tags=["User Management"])

# Include cryptocurrency router
api_router.include_router(crypto.router, prefix="/crypto", tags=["Cryptocurrency"])

# Include price data router
api_router.include_router(prices.router, prefix="/prices", tags=["Price Data"])

# Include external API router
api_router.include_router(external.router, prefix="/external", tags=["External APIs"])

# Include background tasks router
api_router.include_router(tasks.router, prefix="/tasks", tags=["Background Tasks"])

# Include system health router
api_router.include_router(health.router, prefix="/system", tags=["System Health"])

# Include ML training router
api_router.include_router(ml_training.router, prefix="/ml", tags=["Machine Learning"])

# Include other routers (
api_router.include_router(prediction.router, prefix="/predictions", tags=["Predictions"])

# =====================================
# API INFORMATION ENDPOINT
# =====================================

@api_router.get("/", tags=["API Info"])
async def api_info():
    """
    Get API information and available endpoints
    
    Returns comprehensive information about the CryptoPredict API
    including available endpoints, features, and system capabilities.
    """
    return {
        "name": "CryptoPredict API",
        "version": "1.0.0",
        "description": "Cryptocurrency price prediction and analysis platform",
        "status": "active",
        "environment": "development",
        
        "features": [
            "Real-time cryptocurrency price tracking",
            "Historical data analysis and storage", 
            "LSTM neural network price predictions",
            "Model training and evaluation",
            "Batch predictions and history",          
            "Model performance analytics",            
            "User authentication and authorization",
            "Background task management",
            "External API integrations",
            "System health monitoring"
        ],
        
        "endpoints": {
            "authentication": "/api/v1/auth",
            "users": "/api/v1/users",
            "cryptocurrencies": "/api/v1/crypto", 
            "prices": "/api/v1/prices",
            "external_apis": "/api/v1/external",
            "background_tasks": "/api/v1/tasks",
            "system_health": "/api/v1/system",
            "ml_training": "/api/v1/ml/training",      
            "ml_predictions": "/api/v1/ml/predictions" 
        },
        
        "ml_capabilities": {
            "models": ["LSTM", "Linear Regression", "Random Forest", "ARIMA", "Ensemble"],
            "prediction_timeframes": ["1h", "24h", "7d", "30d"],
            "supported_cryptocurrencies": "Dynamic (auto-discovery)",
            "training_frequency": "Weekly automatic + on-demand",
            "prediction_frequency": "Every 4 hours + on-demand"
        },
        
        "data_sources": [
            "CoinGecko API",
            "Binance API", 
            "Alpha Vantage API"
        ],
        
        "documentation": {
            "interactive_docs": "/docs",
            "openapi_schema": "/openapi.json",
            "redoc": "/redoc"
        },
        
        "support": {
            "contact": "support@cryptopredict.com",
            "documentation": "https://docs.cryptopredict.com",
            "github": "https://github.com/cryptopredict/api"
        }
    }


# =====================================
# HEALTH CHECK ENDPOINT
# =====================================

@api_router.get("/health", tags=["API Health"])
async def api_health():
    """
    Quick API health check
    
    Returns basic health status of the API service.
    For detailed system health, use /api/v1/system/health
    """
    return {
        "status": "healthy",
        "service": "CryptoPredict API",
        "version": "1.0.0",
        "timestamp": "2024-01-28T14:30:22Z"
    }