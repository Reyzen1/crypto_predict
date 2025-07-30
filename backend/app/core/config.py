# File: backend/app/core/config.py
# Simple and stable configuration with proper environment variable loading

import os
from typing import List, Optional, Union
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import field_validator, ConfigDict


def load_env_file():
    """Load environment variables from .env file"""
    try:
        from dotenv import load_dotenv
        
        # Look for .env file in project root (parent of backend)
        current_dir = Path(__file__).parent.parent.parent
        env_path = current_dir / '.env'
        
        if env_path.exists():
            load_dotenv(env_path, override=True)
            return True
        
        return False
        
    except ImportError:
        # dotenv not available, continue without it
        return False


# Load environment variables ONCE at module level
load_env_file()


class Settings(BaseSettings):
    """
    Application settings with automatic environment variable loading
    """
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Basic app settings
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes", "on")
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "CryptoPredict MVP")
    DESCRIPTION: str = os.getenv("DESCRIPTION", "AI-powered cryptocurrency price prediction API")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-12345678")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key-change-in-production-87654321")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 
                                                     os.getenv("TOKEN_EXPIRE_MINUTES", "30")))
    
    # Database settings - AUTO-DETECT from environment
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:admin123@localhost:5433/cryptopredict")
    
    # Redis settings - AUTO-DETECT from environment
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # External API settings
    COINGECKO_API_KEY: Optional[str] = os.getenv("COINGECKO_API_KEY")
    BINANCE_API_KEY: Optional[str] = os.getenv("BINANCE_API_KEY")
    BINANCE_API_SECRET: Optional[str] = os.getenv("BINANCE_API_SECRET")
    ALPHA_VANTAGE_API_KEY: Optional[str] = os.getenv("ALPHA_VANTAGE_API_KEY")
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", 
                                              os.getenv("RATE_LIMIT_MINUTE", "60")))
    RATE_LIMIT_PER_HOUR: int = int(os.getenv("RATE_LIMIT_PER_HOUR", 
                                            os.getenv("RATE_LIMIT_HOUR", "1000")))
    
    # Frontend settings
    NEXT_PUBLIC_API_URL: str = os.getenv("NEXT_PUBLIC_API_URL", 
                                        os.getenv("API_URL", "http://localhost:8000"))
    NEXT_PUBLIC_WS_URL: str = os.getenv("NEXT_PUBLIC_WS_URL", 
                                       os.getenv("WS_URL", "ws://localhost:8000"))
    
    # ML Model settings
    MODEL_PATH: str = os.getenv("MODEL_PATH", "./models")
    MODEL_UPDATE_INTERVAL: int = int(os.getenv("MODEL_UPDATE_INTERVAL", "3600"))
    DATA_COLLECTION_INTERVAL: int = int(os.getenv("DATA_COLLECTION_INTERVAL", "300"))
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "./logs/app.log")
    
    # CORS and host settings
    ALLOWED_HOSTS: List[str] = ["*"]
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = os.getenv(
        "BACKEND_CORS_ORIGINS", 
        os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://testserver")
    )
    
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


# Create settings instance
settings = Settings()

# Export for backward compatibility
__all__ = ["settings", "Settings"]