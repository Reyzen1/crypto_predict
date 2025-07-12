# File: ./backend/app/core/config.py
# Application configuration settings for CryptoPredict MVP
# Manages environment variables and application settings

from typing import List, Optional
from pydantic import BaseModel
import os


class Settings(BaseModel):
    """Application settings with fixed values"""
    
    # Project Information
    PROJECT_NAME: str = "CryptoPredict MVP"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AI-powered cryptocurrency price prediction API"
    
    # Environment Configuration
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Security Configuration
    SECRET_KEY: str = "your-secret-key-change-this"
    JWT_SECRET_KEY: str = "your-jwt-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://postgres:postgres123@localhost:5432/cryptopredict"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379"
    
    # External API Configuration
    COINGECKO_API_KEY: Optional[str] = None
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_API_SECRET: Optional[str] = None
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",     # Next.js frontend
        "http://localhost:8000",     # FastAPI backend
        "http://127.0.0.1:3000",     # Alternative localhost
        "http://127.0.0.1:8000",     # Alternative localhost
    ]
    
    # Allowed Hosts
    ALLOWED_HOSTS: List[str] = [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
    ]
    
    # Rate Limiting Configuration
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # ML Model Configuration
    MODEL_PATH: str = "./models"
    MODEL_UPDATE_INTERVAL: int = 3600  # 1 hour
    
    # Data Collection Configuration
    DATA_COLLECTION_INTERVAL: int = 300  # 5 minutes


# Global settings instance
settings = Settings()