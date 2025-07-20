# File: backend/app/core/config.py
# Application configuration settings for CryptoPredict MVP
# Updated with Authentication settings while preserving existing config

from typing import List, Optional, Union
from pydantic_settings import BaseSettings
from pydantic import field_validator
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Project Information (preserving your existing values)
    PROJECT_NAME: str = "CryptoPredict MVP"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AI-powered cryptocurrency price prediction API"
    
    # Environment Configuration
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Security Configuration (NEW for authentication)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Database Configuration (preserving your existing values)
    DATABASE_URL: str = "postgresql://postgres:postgres123@localhost:5432/cryptopredict"
    
    # Redis Configuration (preserving your existing values)
    REDIS_URL: str = "redis://localhost:6379"
    
    # External API Configuration (preserving your existing values)
    COINGECKO_API_KEY: Optional[str] = None
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_API_SECRET: Optional[str] = None
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    
    # CORS Configuration (preserving your existing approach)
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://127.0.0.1:3000"
    
    # Allowed Hosts (preserving your existing values)
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]
    
    # Rate Limiting Configuration (preserving your existing values)
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # ML Model Configuration (preserving your existing values)
    MODEL_PATH: str = "./models"
    MODEL_UPDATE_INTERVAL: int = 3600  # 1 hour
    
    # Data Collection Configuration (preserving your existing values)
    DATA_COLLECTION_INTERVAL: int = 300  # 5 minutes
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS origins from environment variable (preserving your logic)"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return v
        else:
            return ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()