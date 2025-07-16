# File: ./backend/app/main.py
# Main FastAPI application entry point for CryptoPredict MVP
# Updated with favicon and well-known endpoints

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn
import os

from app.core.config import settings
from app.api.api_v1.api import api_router
from app.core.database import engine, Base

# Import models to ensure they're registered with SQLAlchemy
import app.models

# Create all database tables on startup
Base.metadata.create_all(bind=engine)

# Initialize FastAPI application with metadata
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",                       # Swagger UI documentation
    redoc_url="/redoc"                      # ReDoc documentation
)

# Initialize rate limiter for API protection
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,  # Allowed origins
    allow_credentials=True,                        # Allow cookies
    allow_methods=["*"],                           # Allow all HTTP methods
    allow_headers=["*"],                           # Allow all headers
)

# Configure trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS          # Allowed hostnames
)

# Include API routes with version prefix
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "message": f"{settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy", 
        "service": "cryptopredict-backend",
        "version": settings.VERSION
    }

# Handle favicon requests to avoid 404 logs
@app.get("/favicon.ico")
async def get_favicon():
    """Return empty response for favicon requests"""
    return Response(content="", media_type="image/x-icon")

# Handle Chrome DevTools well-known requests
@app.get("/.well-known/appspecific/com.chrome.devtools.json")
async def get_chrome_devtools():
    """Return empty JSON for Chrome DevTools requests"""
    return {}

# Development server configuration
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",                           # Listen on all interfaces
        port=8000,                                # Default port
        reload=True,                              # Auto-reload on code changes
        log_level="info"                          # Logging level
    )