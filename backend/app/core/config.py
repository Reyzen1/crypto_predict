# File: ./backend/app/core/config.py
# Configuration settings for CryptoPredict MVP
# Manages environment variables and application settings

from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import validator, AnyHttpUrl

class Settings(BaseSettings):
    """Application settings with validation"""

    # Application settings
    PROJECT_NAME: str = "CryptoPredict MVP"
    VERSION: str = "1.0.0"
    DEBUG: bool                                     # Enable debug mode

    # API settings
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str                                 # Main secret key
    ACCESS_TOKEN_EXPIRE_MINUTES: int                # Token expiration time
    REFRESH_TOKEN_EXPIRE_DAYS: int                  # Refresh token time

    # Database settings
    DATABASE_URL: str = "postgresql://cryptopredict:cryptopredict123@localhost:5432/cryptopredict_db"
    
    # Redis settings
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security settings
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",  # Next.js development server
        "http://localhost:8000",  # FastAPI development server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
    ALLOWED_HOSTS: List[str] = [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
    ]

    # External API settings
    COINGECKO_API_KEY: str                          # CoinGecko API key
    BINANCE_API_KEY: str                            # Binance API key
    BINANCE_API_SECRET: str                         # Binance API secret
    ALPHA_VANTAGE_API_KEY: str                      # Alpha Vantage API key
    JWT_SECRET_KEY: str                             # JWT token key
    ALGORITHM: str = "HS256"                        # JWT algorithm

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60                 # Requests per minute

    # ML Model settings
    MODEL_DATA_PATH: str = "./data/models"          # Path to ML models
    PREDICTION_CACHE_TTL: int = 300                 # Cache TTL in seconds

    # Logging
    LOG_LEVEL: str = "INFO"

    # Frontend-related config
    ENVIRONMENT: str                                # Environment type
    NEXT_PUBLIC_API_URL: str                        # Backend API URL
    NEXT_PUBLIC_WS_URL: str                         # WebSocket URL

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Validate and assemble CORS origins"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @validator("ALLOWED_HOSTS", pre=True)
    def assemble_allowed_hosts(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Validate and assemble allowed hosts"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    class Config:
        case_sensitive = True
        env_file = ".env"

# Create settings instance
settings = Settings()
