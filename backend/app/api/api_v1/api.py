# File: ./backend/app/api/api_v1/api.py
# Main API router for CryptoPredict MVP
# Aggregates all API endpoints and provides version 1 routing

from fastapi import APIRouter

# Import endpoint routers (to be created)
# from app.api.api_v1.endpoints import auth, crypto, predictions, health

# Create main API router
api_router = APIRouter()

# Health check endpoint for basic API testing
@api_router.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring API status
    Returns basic API information and status
    """
    return {
        "status": "healthy",
        "service": "cryptopredict-api",
        "version": "1.0.0",
        "message": "CryptoPredict MVP API is running"
    }

# Basic info endpoint
@api_router.get("/info")
async def api_info():
    """
    API information endpoint
    Returns API metadata and available endpoints
    """
    return {
        "name": "CryptoPredict MVP API",
        "version": "1.0.0",
        "description": "AI-powered cryptocurrency price prediction API",
        "endpoints": {
            "health": "/api/v1/health",
            "info": "/api/v1/info",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

# Include other routers (uncomment when endpoints are created)
# api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
# api_router.include_router(crypto.router, prefix="/crypto", tags=["cryptocurrency"])
# api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
# api_router.include_router(health.router, prefix="/system", tags=["system"])