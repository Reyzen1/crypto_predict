# File: ./backend/app/core/config.py
# Application configuration settings for CryptoPredict MVP
# Manages environment variables and application settings

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator
import os
from decouple import config


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Project Information
    PROJECT_NAME: str = "CryptoPredict MVP"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AI-powered cryptocurrency price prediction API"
    
    # Environment Configuration
    ENVIRONMENT: str = config("ENVIRONMENT", default="development")
    DEBUG: bool = config("DEBUG", default=True, cast=bool)
    
    # Security Configuration
    SECRET_KEY: str = config("SECRET_KEY", default="your-secret-key-change-this")
    JWT_SECRET_KEY: str = config("JWT_SECRET_KEY", default="your-jwt-secret-key")
    ALGORITHM: str = config("ALGORITHM", default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=30, cast=int)
    
    # Database Configuration
    DATABASE_URL: str = config(
        "DATABASE_URL", 
        default="postgresql://postgres:postgres123@localhost:5432/cryptopredict"
    )
    
    # Redis Configuration
    REDIS_URL: str = config("REDIS_URL", default="redis://localhost:6379")
    
    # External API Configuration
    COINGECKO_API_KEY: Optional[str] = config("COINGECKO_API_KEY", default=None)
    BINANCE_API_KEY: Optional[str] = config("BINANCE_API_KEY", default=None)
    BINANCE_API_SECRET: Optional[str] = config("BINANCE_API_SECRET", default=None)
    ALPHA_VANTAGE_API_KEY: Optional[str] = config("ALPHA_VANTAGE_API_KEY", default=None)
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
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
    MODEL_PATH: str = config("MODEL_PATH", default="./models")
    MODEL_UPDATE_INTERVAL: int = config("MODEL_UPDATE_INTERVAL", default=3600, cast=int)  # 1 hour
    
    # Data Collection Configuration
    DATA_COLLECTION_INTERVAL: int = config("DATA_COLLECTION_INTERVAL", default=300, cast=int)  # 5 minutes
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str) -> List[str]:
        """Parse CORS origins from environment variable"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()