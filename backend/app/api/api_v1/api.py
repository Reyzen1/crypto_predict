# File: backend/app/api/api_v1/api.py
# Main API router updated to use new naming convention and prediction endpoints

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
    prediction,
    dashboard,        
    websocket         
)

# Create main API router
api_router = APIRouter()

# Include other routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["User Management"])
api_router.include_router(crypto.router, prefix="/crypto", tags=["Cryptocurrency"])
api_router.include_router(prices.router, prefix="/prices", tags=["Price Data"])
api_router.include_router(external.router, prefix="/external", tags=["External APIs"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Background Tasks"])
api_router.include_router(health.router, prefix="/system", tags=["System Health"])
api_router.include_router(ml_training.router, prefix="/ml", tags=["Machine Learning"])
api_router.include_router(prediction.router, prefix="/ml/predictions", tags=["Predictions"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
api_router.include_router(crypto.router, prefix="/crypto", tags=["Cryptocurrency"])

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
        "description": "Cryptocurrency Price Prediction API with ML",
        "features": [
            "Symbol-based predictions (BTC, ETH, etc.)",
            "Dashboard data aggregation",
            "Real-time WebSocket updates",
            "ML model training and serving",
            "User authentication and management"
        ],
        "endpoints": {
            "predictions": {
                "symbol_prediction": "POST /ml/predictions/{symbol}/predict",
                "legacy_prediction": "POST /predictions/predict"
            },
            "dashboard": {
                "summary": "GET /dashboard/summary",
                "crypto_details": "GET /dashboard/crypto/{symbol}",
                "quick_data": "GET /dashboard/quick/{symbol}",
                "prices": "GET /dashboard/prices"
            },
            "websocket": {
                "dashboard": "ws://host/ws/dashboard",
                "symbol_prices": "ws://host/ws/prices/{symbol}"
            },
            "authentication": {
                "register": "POST /auth/register",
                "login": "POST /auth/login"
            }
        },
        "supported_symbols": ["BTC", "ETH", "ADA", "DOT"],
        "ml_models": ["LSTM", "LINEAR_REGRESSION", "RANDOM_FOREST"],
        "system_status": "operational"
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