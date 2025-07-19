# File: ./backend/app/schemas/__init__.py
# Schemas package initialization - exports all schema classes

# Common schemas
from app.schemas.common import (
    BaseSchema,
    PaginationParams,
    PaginatedResponse,
    SuccessResponse,
    ErrorResponse,
    HealthCheck,
    SearchParams,
    DateRangeFilter,
    BulkOperation,
    BulkOperationResult
)

# User schemas
from app.schemas.user import (
    UserBase,
    UserRegister,
    UserLogin,
    UserUpdate,
    UserPasswordChange,
    UserResponse,
    UserSummary,
    UserWithStats,
    Token,
    TokenData,
    UserPreferences
)

# Cryptocurrency schemas
from app.schemas.cryptocurrency import (
    CryptocurrencyBase,
    CryptocurrencyCreate,
    CryptocurrencyUpdate,
    CryptocurrencyResponse,
    CryptocurrencyWithPrice,
    CryptocurrencyStats,
    CryptocurrencyList,
    CryptocurrencySearch,
    CryptocurrencyBulkUpdate,
    MarketData,
    CryptocurrencyRanking,
    SupportedCryptocurrencies
)

# Price data schemas
from app.schemas.price_data import (
    PriceDataBase,
    PriceDataCreate,
    PriceDataUpdate,
    PriceDataResponse,
    PriceDataWithCrypto,
    OHLCV,
    PriceHistoryRequest,
    PriceHistoryResponse,
    PriceStatistics,
    MLDataRequest,
    MLDataResponse,
    PriceAlert,
    PriceDataBulkInsert,
    PriceDataAnalytics,
    RealTimePriceUpdate
)

# Prediction schemas
from app.schemas.prediction import (
    PredictionBase,
    PredictionCreate,
    PredictionUpdate,
    PredictionResponse,
    PredictionWithDetails,
    PredictionRequest,
    PredictionResult,
    BatchPredictionRequest,
    BatchPredictionResponse,
    ModelPerformance,
    PredictionAnalytics,
    PredictionComparison,
    UserPredictionStats,
    PredictionAlert,
    ModelTrainingRequest,
    ModelTrainingResponse
)

# Export all schema classes for easy importing
__all__ = [
    # Common schemas
    "BaseSchema",
    "PaginationParams", 
    "PaginatedResponse",
    "SuccessResponse",
    "ErrorResponse", 
    "HealthCheck",
    "SearchParams",
    "DateRangeFilter",
    "BulkOperation",
    "BulkOperationResult",
    
    # User schemas
    "UserBase",
    "UserRegister",
    "UserLogin", 
    "UserUpdate",
    "UserPasswordChange",
    "UserResponse",
    "UserSummary",
    "UserWithStats", 
    "Token",
    "TokenData",
    "UserPreferences",
    
    # Cryptocurrency schemas
    "CryptocurrencyBase",
    "CryptocurrencyCreate",
    "CryptocurrencyUpdate",
    "CryptocurrencyResponse", 
    "CryptocurrencyWithPrice",
    "CryptocurrencyStats",
    "CryptocurrencyList",
    "CryptocurrencySearch",
    "CryptocurrencyBulkUpdate",
    "MarketData",
    "CryptocurrencyRanking", 
    "SupportedCryptocurrencies",
    
    # Price data schemas
    "PriceDataBase",
    "PriceDataCreate",
    "PriceDataUpdate",
    "PriceDataResponse",
    "PriceDataWithCrypto",
    "OHLCV",
    "PriceHistoryRequest", 
    "PriceHistoryResponse",
    "PriceStatistics",
    "MLDataRequest",
    "MLDataResponse", 
    "PriceAlert",
    "PriceDataBulkInsert",
    "PriceDataAnalytics",
    "RealTimePriceUpdate",
    
    # Prediction schemas
    "PredictionBase", 
    "PredictionCreate",
    "PredictionUpdate",
    "PredictionResponse",
    "PredictionWithDetails",
    "PredictionRequest",
    "PredictionResult",
    "BatchPredictionRequest",
    "BatchPredictionResponse",
    "ModelPerformance",
    "PredictionAnalytics", 
    "PredictionComparison",
    "UserPredictionStats",
    "PredictionAlert",
    "ModelTrainingRequest",
    "ModelTrainingResponse"
]