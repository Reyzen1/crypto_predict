# File: backend/app/core/config.py
# Complete configuration with all required fields 

import os
from typing import List, Optional, Union
from pydantic_settings import BaseSettings
from pydantic import field_validator, ConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file
    """
    
    # Pydantic V2 configuration using ConfigDict (FIXED)
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Basic app settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PROJECT_NAME: str = "CryptoPredict MVP"
    DESCRIPTION: str = "AI-powered cryptocurrency price prediction API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security settings
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    JWT_SECRET_KEY: str = "your-jwt-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database settings
    DATABASE_URL: str = "postgresql://postgres:postgres123@localhost:5432/cryptopredict"
    
    # Redis settings
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # External API settings
    COINGECKO_API_KEY: Optional[str] = None
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_API_SECRET: Optional[str] = None
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Frontend settings
    NEXT_PUBLIC_API_URL: str = "http://localhost:8000"
    NEXT_PUBLIC_WS_URL: str = "ws://localhost:8000"
    
    # ML Model settings
    MODEL_PATH: str = "./models"
    MODEL_UPDATE_INTERVAL: int = 3600
    DATA_COLLECTION_INTERVAL: int = 300
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "./logs/app.log"
    
    # CORS and host settings
    ALLOWED_HOSTS: List[str] = ["*"]  # Allow all hosts for development
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000", 
        "http://localhost:8000",
        "http://testserver"
    ]
    
    @field_validator('BACKEND_CORS_ORIGINS', mode='before')
    @classmethod
    def assemble_cors_origins(cls, v) -> List[str]:
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return [str(origin) for origin in v]
        else:
            return [
                "http://localhost:3000",
                "http://127.0.0.1:3000", 
                "http://localhost:8000",
                "http://testserver"
            ]

    @field_validator('DEBUG', mode='before')
    @classmethod
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return bool(v)


def get_settings() -> Settings:
    """Create settings instance with environment loading"""
    env_files_to_try = [".env", "../.env"]
    
    for env_file in env_files_to_try:
        if os.path.exists(env_file):
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file, override=True)
                break
            except ImportError:
                pass
    
    return Settings()


# Create settings instance - CRITICAL: This was missing!
settings = get_settings()

# Export for backward compatibility
__all__ = ["settings", "Settings", "get_settings"]