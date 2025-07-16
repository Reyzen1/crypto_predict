# File: ./backend/app/core/config.py
# Application configuration settings for CryptoPredict MVP
# Fixed version to handle environment variables properly

from typing import List, Optional, Union
from pydantic_settings import BaseSettings
from pydantic import field_validator
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
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
    
    # CORS Configuration - Fixed to handle string input properly
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://127.0.0.1:3000"
    
    # Allowed Hosts
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]
    
    # Rate Limiting Configuration
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # ML Model Configuration
    MODEL_PATH: str = "./models"
    MODEL_UPDATE_INTERVAL: int = 3600  # 1 hour
    
    # Data Collection Configuration
    DATA_COLLECTION_INTERVAL: int = 300  # 5 minutes
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS origins from environment variable"""
        if isinstance(v, str):
            # Split by comma and clean up
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return v
        else:
            # Default fallback
            return ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()