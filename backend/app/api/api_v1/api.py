# File: ./backend/app/api/api_v1/api.py
# Main API router for CryptoPredict MVP - Updated with External API endpoints
# Aggregates all API endpoints and provides version 1 routing

from fastapi import APIRouter

# Import endpoint routers
from app.api.api_v1.endpoints import auth, users, crypto, prices, health, external
# from app.api.api_v1.endpoints import predictions  # To be created later

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
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "crypto": "/api/v1/crypto",
            "prices": "/api/v1/prices",
            "external": "/api/v1/external",
            "system": "/api/v1/system",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        "features": [
            "User authentication with JWT",
            "Cryptocurrency data management",
            "Price data tracking and analysis",
            "External API integration (CoinGecko)",
            "Background data synchronization",
            "System health monitoring",
            "RESTful API design",
            "Automatic API documentation"
        ]
    }

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

# Include system health router
api_router.include_router(health.router, prefix="/system", tags=["System Health"])

# Include other routers (uncomment when endpoints are created)
# api_router.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])